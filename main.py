"""Death Night — sobrevivência em ondas, Python/PPlay/Pygame."""
import math
import os
import json
from pathlib import Path
import random
from types import SimpleNamespace

from game_objects.janela_windows import preparar_escala_windows

# Precisa ocorrer antes de o PPlay/SDL criar qualquer janela do processo.
preparar_escala_windows()

from pygame import Rect, WINDOWFOCUSLOST  # Apenas geometria e aviso de perda de foco.
from PPlay.window import Window
from game_objects.interface import Interface, InterfaceMundo
from PPlay.camera import Camera
from game_objects.bairro import LARGURA_MUNDO, ALTURA_MUNDO, INICIO

from game_objects.arena import Arena, AREA, LARGURA, ALTURA
from game_objects.audio import Audio
from game_objects.player import Player
from game_objects.missao import MissaoFusiveis
from game_objects.wave_manager import GerenciadorDeOndas
from game_objects.zombie import ZumbiChefeFinal
from game_objects.suprimento import Suprimento, CORES, NOMES, ciclo_suprimentos
from game_objects.colisao_utils import colidiu
from game_objects.dificuldade import DIFICULDADES, ORDEM_DIFICULDADES
from game_objects.ranking import carregar_ranking, salvar_pontuacao

ROOT = Path(__file__).resolve().parent
BRANCO = (229, 235, 226)
CINZA = (145, 166, 165)
OURO = (229, 189, 116)
VERDE = (112, 208, 169)
ATRASO_CONFIRMACAO_MELHORIA = 350  # ms reais; o tempo da partida fica congelado.
from game_objects.progressao import MELHORIAS, sortear_opcoes


class Jogo:
    def __init__(self):
        os.chdir(ROOT)
        self.janela = Window(LARGURA, ALTURA, 'Death Night • Até o amanhecer', intro=False)
        self.janela.set_title('Death Night • Até o amanhecer')
        self.tela = self.janela.screen
        self.arena = Arena()
        self.camera = Camera(LARGURA, ALTURA)
        self.camera.set_world_bounds(LARGURA_MUNDO, ALTURA_MUNDO)
        self.audio = Audio()
        self.teclado = self.janela.get_keyboard()
        self.controle_mouse = self.janela.get_mouse()
        self.interface = Interface()
        self.interface_mundo = InterfaceMundo(self.interface,self.camera)
        self.estado = 'menu'
        self.retorno_opcoes = 'menu'
        self.dificuldade = 'normal'
        self.rodando = True
        self.foco = 0
        self.mouse = (0, 0)
        self.ranking = carregar_ranking()
        self.partida = None
        self.erro_salvar = False
        self.interacao_pendente = False
        self.carregar_configuracao()
        self.controle_mouse.unhide()
        self.audio.contexto('menu')

    def carregar_configuracao(self):
        try:
            config = json.loads((ROOT / 'data' / 'configuracoes.json').read_text(encoding='utf-8'))
            self.audio.ajustar_efeitos(float(config.get('volume_efeitos', config.get('volume', .5))))
            self.audio.ajustar_musica(float(config.get('volume_musica', .35)))
        except (OSError, ValueError, TypeError, AttributeError):
            pass

    def texto(self, texto, x, y, tamanho=18, cor=BRANCO, centro=False, bold=False):
        return self.interface.texto(texto, x, y, tamanho, cor, centro, bold)

    def mudar(self, estado):
        self.estado = estado
        self.foco = 0
        if estado == 'melhoria':
            self.melhoria_liberar_em = self.janela.time_elapsed()+ATRASO_CONFIRMACAO_MELHORIA
            self.melhoria_aguarda_soltura = True
        if estado == 'jogando':
            self.controle_mouse.hide()
        else:
            self.controle_mouse.unhide()
        self.audio.contexto(estado, em_partida=bool(self.partida and self.retorno_opcoes == 'pausa'))

    def nova_partida(self):
        # Cada tentativa recria os colisores e o objetivo, inclusive o portão fechado.
        self.arena = Arena()
        missao = MissaoFusiveis()
        self.arena.obstaculos.append(missao.portao)
        self.interacao_pendente = False
        player = Player(*INICIO)
        self.camera.x = self.camera.y = 0
        self.camera.follow(player, suavizacao=1)
        player.municao_maxima += DIFICULDADES[self.dificuldade]['ajuste_municao']
        player.municao = player.municao_maxima
        self.partida = dict(player=player, zumbis=[], projeteis=[], itens=[], efeitos=[],
                            tempo=0., ultimo_item=0., ultimo_reforco_municao=0., pontos=0, opcoes_melhoria=[],
                            fila_melhorias=[], fila_suprimentos=[], audio_vazio_ate=0,
                            aviso='ENCONTRE OS 3 FUSÍVEIS · E PARA COLETAR', aviso_ate=3800,
                            missao=missao, eliminacoes=0, pontuacao_salva=False,
                            gerenciador=GerenciadorDeOndas(self.arena.spawn, self.dificuldade))
        self.erro_salvar = False
        self.gerar_item('municao')
        self.audio.reiniciar_partida()
        self.mudar('jogando')

    def avisar(self, texto, duracao=2000):
        self.partida['aviso'] = texto
        self.partida['aviso_ate'] = self.partida['tempo'] + duracao

    def gerar_item(self, tipo=None, posicao=None):
        p = self.partida
        # Itens vencidos não ocupam a cota antes da limpeza do fim do frame.
        p['itens'][:] = [i for i in p['itens'] if i.ativo and not i.expirou(p['tempo'])]
        if len(p['itens']) >= DIFICULDADES[self.dificuldade]['limite_itens']:
            return False
        aleatorio = tipo is None
        if aleatorio:
            if not p['fila_suprimentos']:
                p['fila_suprimentos'] = ciclo_suprimentos()
            tipo = p['fila_suprimentos'][0]
            if tipo == 'municao' and any(i.tipo == 'municao' for i in p['itens']):
                tipo = 'cura'  # Não desperdiçar a oportunidade com uma caixa duplicada.
        if tipo == 'municao' and any(i.tipo == 'municao' for i in p['itens']):
            return False  # Uma reserva disponível basta; não empilhar caixas pelo bairro.
        if posicao is None or not self.arena.livre(Rect(*posicao, 22, 22)):
            posicao = self.arena.posicao_livre(22, 22, perto=(p["player"].x,p["player"].y),
                                              raio=160 if tipo == 'municao' else None)
        if posicao is not None:
            p['itens'].append(Suprimento(tipo, *posicao, p['tempo']))
            if aleatorio:
                p['fila_suprimentos'].pop(0)
            return True
        return False

    def efeito(self, x, y, cor, quantidade=7):
        for _ in range(quantidade):
            angulo = random.random()*math.tau
            velocidade = random.uniform(25, 95)
            self.partida['efeitos'].append([x, y, math.cos(angulo)*velocidade,
                                             math.sin(angulo)*velocidade, .35, cor])

    def atualizar(self, dt, mira=None, atirar=False, teclado=None, interagir=False):
        if self.estado != 'jogando':
            return
        dt = min(dt, .04)
        p = self.partida
        interagir = interagir or self.interacao_pendente
        self.interacao_pendente = False
        p['tempo'] += dt*1000
        tempo, player, g = p['tempo'], p['player'], p['gerenciador']
        player.tempo_jogo = tempo
        player.mover(teclado or self.teclado, dt,
                     (AREA.left, AREA.right, AREA.top, AREA.bottom), self.arena.obstaculos)
        mira_tela = mira if mira is not None else self.mouse
        player.mirar((mira_tela[0]+self.camera.x, mira_tela[1]+self.camera.y))
        self.arena.alvo_spawn = (player.x,player.y)
        if atirar and player.pode_atirar(tempo):
            p['projeteis'].extend(player.disparar(tempo, self.arena.obstaculos))
            self.audio.tocar('tiro_escopeta' if player.arma == 'escopeta' else 'tiro')
            self.efeito(*player.origem_ultimo_tiro, OURO, 3)
        elif atirar and player.municao == 0 and tempo >= p['audio_vazio_ate']:
            self.audio.tocar('vazio')
            p['audio_vazio_ate'] = tempo+900

        onda_anterior = g.onda_atual
        # A instalação encerra a progressão de ondas; os inimigos presentes continuam.
        zumbi = None if p['missao'].instalados else g.atualizar(tempo, len(p['zumbis']))
        if zumbi:
            p['zumbis'].append(zumbi)
        if g.onda_atual != onda_anterior:
            self.avisar(f'ONDA {g.onda_atual}' + (' · CHEFE À VISTA' if g.onda_atual % 5 == 0 else ''))
            self.audio.tocar('onda')

        ajuste = DIFICULDADES[self.dificuldade]
        intervalo_municao = ajuste['intervalo_municao']*(.5 if player.municao == 0 else 1)
        if (player.municao <= player.municao_maxima*.25 and
                tempo-p['ultimo_reforco_municao'] >= intervalo_municao):
            # Uma tentativa bloqueada pela cota não reinicia toda a espera.
            # Não consome a fila dos benefícios nem permite caixas duplicadas.
            if self.gerar_item('municao'):
                p['ultimo_reforco_municao'] = tempo
        if tempo-p['ultimo_item'] >= ajuste['intervalo_item']:
            # Sem balas, esta reposição lenta prioriza munição para permitir a fuga.
            # Segue o mesmo intervalo e limite de itens da dificuldade escolhida.
            tipo = 'municao' if player.municao == 0 else None
            self.gerar_item(tipo)
            p['ultimo_item'] = tempo

        for z in p['zumbis']:
            if tempo >= getattr(z, 'recalcular_em', 0):
                z.rota = self.arena.rota((z.x, z.y), (player.x, player.y), z.width, z.height)
                z.recalcular_em = tempo+450
            while z.rota and math.dist((z.x, z.y), z.rota[0]) < .5:
                z.rota.pop(0)
            if z.rota:
                tx, ty = z.rota[0]
                alvo = SimpleNamespace(x=tx, y=ty, width=z.width, height=z.height)
                distancia = math.dist((z.x, z.y), (tx, ty))
                z.seguir(alvo, min(dt, distancia/max(z.velocidade, 1)), self.arena.obstaculos)
            if colidiu(z, player):
                vida_anterior = player.vida
                player.levar_dano(z.dano_contato, tempo)
                if player.vida != vida_anterior:
                    self.audio.tocar('dano')
                    self.efeito(player.x+player.width/2, player.y+player.height/2, (239, 113, 111))

        for tiro in p['projeteis']:
            # Subpassos evitam atravessar alvos pequenos durante um frame lento.
            passos = max(1, math.ceil(tiro.velocidade*dt/5))
            for _ in range(passos):
                tiro.atualizar(dt/passos)
                if not tiro.ativo:
                    break
                if any(o.bloqueia_tiro and colidiu(tiro, o) for o in self.arena.obstaculos):
                    tiro.ativo = False
                    self.audio.tocar('parede')
                    self.efeito(tiro.x, tiro.y, CINZA, 3)
                    break
                atingido = next((z for z in p['zumbis'] if z.ativo and colidiu(tiro, z)), None)
                if atingido:
                    atingido.levar_dano(tiro.dano)
                    tiro.ativo = False
                    self.audio.tocar('impacto')
                    self.efeito(tiro.x, tiro.y, VERDE)
                    if not atingido.ativo:
                        self.audio.tocar('morte_zumbi')
                        p['pontos'] += atingido.PONTOS
                        p['eliminacoes'] += 1
                        player.ganhar_xp(atingido.XP)
                        if random.random() < DIFICULDADES[self.dificuldade]['chance_drop']:
                            self.gerar_item(posicao=(atingido.x, atingido.y))
                    break
        p['projeteis'][:] = [t for t in p['projeteis'] if t.ativo and not t.fora_da_area(LARGURA_MUNDO, ALTURA_MUNDO)]
        p['zumbis'][:] = [z for z in p['zumbis'] if z.ativo]
        for item in p['itens']:
            if not item.expirou(tempo) and item.collided(player) and item.aplicar(player, tempo):
                self.audio.tocar(item.tipo if item.tipo in ('cura', 'municao') else 'beneficio')
                self.avisar(NOMES[item.tipo], 1200)
                self.efeito(item.x+11, item.y+11, CORES[item.tipo])
        p['itens'][:] = [i for i in p['itens'] if i.ativo and not i.expirou(tempo)]
        for e in p['efeitos']:
            e[0] += e[2]*dt
            e[1] += e[3]*dt
            e[4] -= dt
        p['efeitos'][:] = [e for e in p['efeitos'] if e[4] > 0]
        self.audio.atualizar(tempo, player, p['zumbis'], p['missao'].chefe)
        self.camera.follow(player, suavizacao=1-math.exp(-9*dt), zona_morta_x=45, zona_morta_y=30)
        if not player.esta_vivo():
            self.finalizar('fim')
            return
        missao = p['missao']
        if interagir:
            resultado = missao.interagir(player)
            if resultado == 'coletou':
                self.audio.tocar('fusivel')
                self.avisar(f'FUSÍVEL COLETADO · {missao.quantidade}/3')
            elif resultado == 'faltam':
                self.avisar(f'FALTAM {3-missao.quantidade} FUSÍVEIS')
            elif resultado == 'instalou':
                self.audio.tocar('painel')
                self.iniciar_confronto_final()
            elif resultado == 'em_combate':
                self.avisar('PORTÃO BLOQUEADO · DERROTE O GUARDIÃO')
        if missao.liberar_portao():
            self.audio.tocar('portao')
            self.avisar('GUARDIÃO DERROTADO · PORTÃO ABERTO', 3000)
            for z in p['zumbis']:
                z.recalcular_em = 0
        if missao.escapou(player):
            self.finalizar('vitoria')
        elif player.escolhas_pendentes:
            self.abrir_melhoria()

    def iniciar_confronto_final(self):
        p = self.partida
        missao, player = p['missao'], p['player']
        if not missao.instalados or missao.chefe is not None:
            return
        chefe = ZumbiChefeFinal(0, 0)
        candidatos = [(1336,1000), (1468,1000), (1160,1010), (1610,1010)]
        livres = [xy for xy in candidatos if self.arena.livre(Rect(*xy,chefe.width,chefe.height))]
        seguros = [xy for xy in livres if math.dist(xy,(player.x,player.y)) >= 180]
        chefe.x, chefe.y = min(seguros or livres, key=lambda xy: math.dist(xy,(player.x,player.y)))
        ajuste = DIFICULDADES[self.dificuldade]
        chefe.vida_maxima = chefe.vida = round(chefe.VIDA*ajuste['multiplicador_vida'])
        chefe.velocidade_base *= ajuste['multiplicador_velocidade']
        chefe.dano_contato = round(chefe.DANO_CONTATO*ajuste['multiplicador_dano'])
        missao.chefe = chefe
        p['zumbis'].append(chefe)
        player.municao = player.municao_maxima
        self.audio.tocar('chefe')
        self.avisar('GUARDIÃO DESPERTOU · DERROTE-O PARA SAIR', 3200)

    def finalizar(self, estado):
        p = self.partida
        if not p['pontuacao_salva']:
            try:
                self.ranking = salvar_pontuacao(p['pontos'], p['gerenciador'].onda_atual,
                                                DIFICULDADES[self.dificuldade]['nome'])
            except OSError:
                self.erro_salvar = True
            p['pontuacao_salva'] = True
        self.interacao_pendente = False
        self.mudar(estado)
        self.audio.tocar('vitoria' if estado == 'vitoria' else 'derrota')

    def abrir_melhoria(self):
        self.partida['opcoes_melhoria'] = sortear_opcoes(self.partida['player'], self.partida['fila_melhorias'])
        self.audio.tocar('nivel')
        self.mudar('melhoria')

    def botoes(self):
        def coluna(itens, y=252):
            return [(Rect(330, y+i*58, 300, 46), rotulo, acao, True) for i, (rotulo, acao) in enumerate(itens)]
        if self.estado == 'menu':
            return [(Rect(60,310+i*56,300,46),rotulo,acao,True)
                    for i,(rotulo,acao) in enumerate([('JOGAR','preparar'),('RECORDES','ranking'),
                                                     ('OPÇÕES','opcoes'),('SAIR','sair')])]
        if self.estado == 'preparar':
            itens = []
            for i, chave in enumerate(ORDEM_DIFICULDADES):
                rotulo = DIFICULDADES[chave]['nome'].upper()
                itens.append((Rect(132+i*238, 202, 220, 198), rotulo, 'dificuldade:'+chave, True))
            return itens + [(Rect(220, 489, 240, 46), 'COMEÇAR', 'iniciar', True),
                            (Rect(500, 489, 240, 46), 'VOLTAR', 'menu', True)]
        if self.estado == 'pausa':
            return coluna([('CONTINUAR', 'jogando'), ('REINICIAR', 'iniciar'), ('OPÇÕES', 'opcoes'), ('MENU PRINCIPAL', 'menu')], 235)
        if self.estado in ('fim', 'vitoria'):
            rotulo = 'JOGAR NOVAMENTE' if self.estado == 'vitoria' else 'TENTAR NOVAMENTE'
            return [(Rect(220, 489, 240, 46), rotulo, 'iniciar', True),
                    (Rect(500, 489, 240, 46), 'MENU PRINCIPAL', 'menu', True)]
        if self.estado == 'ranking':
            return coluna([('VOLTAR', 'menu')], 495)
        if self.estado == 'opcoes':
            return [(Rect(390, 204, 64, 44), '−', 'menos', True),
                    (Rect(724, 204, 64, 44), '+', 'mais', True),
                    (Rect(390, 266, 64, 44), '−', 'menos_musica', True),
                    (Rect(724, 266, 64, 44), '+', 'mais_musica', True),
                    (Rect(330, 505, 300, 40), 'VOLTAR', self.retorno_opcoes, True)]
        if self.estado == 'melhoria':
            return [(Rect(132+i*238, 208, 220, 230), MELHORIAS[chave][0], 'melhorar:'+chave, True)
                    for i, chave in enumerate(self.partida['opcoes_melhoria'])]
        return []

    def agir(self, acao):
        self.audio.tocar('clique')
        if acao == 'sair':
            self.rodando = False
        elif acao == 'iniciar':
            self.nova_partida()
        elif acao.startswith('dificuldade:'):
            self.dificuldade = acao.split(':')[1]
        elif acao in ('mais', 'menos', 'mais_musica', 'menos_musica'):
            passo = .1 if acao.startswith('mais') else -.1
            if acao.endswith('_musica'):
                self.audio.ajustar_musica(round(self.audio.volume_musica+passo, 2))
            else:
                self.audio.ajustar_efeitos(round(self.audio.volume+passo, 2))
            try:
                (ROOT / 'data').mkdir(exist_ok=True)
                (ROOT / 'data' / 'configuracoes.json').write_text(json.dumps({
                    'volume_efeitos': self.audio.volume,
                    'volume_musica': self.audio.volume_musica}), encoding='utf-8')
            except OSError:
                pass  # O volume ainda funciona durante a sessão sem acesso à pasta.
        elif acao.startswith('melhorar:'):
            player = self.partida['player']
            tipo = acao.split(':')[1]
            if self.estado != 'melhoria' or not player.escolhas_pendentes or tipo not in self.partida['opcoes_melhoria']:
                return
            if player.melhorar(tipo):
                self.audio.tocar('melhoria')
                player.escolhas_pendentes -= 1
                self.partida['opcoes_melhoria'] = []
                self.avisar('MELHORIA EQUIPADA')
                if player.escolhas_pendentes:
                    self.abrir_melhoria()
                else:
                    self.mudar('jogando')
        else:
            if acao == 'opcoes':
                self.retorno_opcoes = self.estado
            self.mudar(acao)

    def eventos(self, eventos=None):
        # A janela coleta os eventos; Keyboard/Mouse fazem a leitura pelo PPlay.
        if eventos is not None:
            self.janela.eventos = eventos
        if any(e.type == WINDOWFOCUSLOST for e in self.janela.eventos) and self.estado == 'jogando':
            self.mudar('pausa')
        teclado = self.teclado
        if teclado.key_down('ESC'):
            destino = {'jogando': 'pausa', 'pausa': 'jogando', 'opcoes': self.retorno_opcoes,
                       'ranking': 'menu', 'preparar': 'menu', 'fim': 'menu', 'vitoria': 'menu'}.get(self.estado)
            if destino:
                self.mudar(destino)
            return
        if self.estado == 'jogando' and teclado.key_down('E'):
            self.interacao_pendente = True
        if self.estado == 'jogando' and teclado.key_down('Q'):
            player = self.partida['player']
            arma_anterior = player.arma
            player.trocar_arma()
            if player.arma != arma_anterior:
                self.audio.tocar('troca')
        botoes = self.botoes()
        habilitados = [i for i, b in enumerate(botoes) if b[3]]
        if not habilitados:
            return
        if self.foco not in habilitados:
            self.foco = habilitados[0]
        mouse = self.controle_mouse.get_position()
        if mouse != getattr(self, '_ultimo_mouse', None):
            for i in habilitados:
                if botoes[i][0].collidepoint(mouse):
                    self.foco = i
            self._ultimo_mouse = mouse
        if any(teclado.key_down(k) for k in ('DOWN', 'RIGHT', 'TAB', 'UP', 'LEFT')):
            passo = -1 if teclado.key_down('UP') or teclado.key_down('LEFT') else 1
            self.foco = habilitados[(habilitados.index(self.foco)+passo) % len(habilitados)]
        if self.estado == 'melhoria' and not self.confirmacao_melhoria_pronta():
            return
        # Espaço continua atirando, mas não pode escolher uma melhoria por engano.
        if teclado.key_down('ENTER') or (self.estado != 'melhoria' and teclado.key_down('SPACE')):
            self.agir(botoes[self.foco][2])
        elif self.controle_mouse.button_down(1):
            for i in habilitados:
                if botoes[i][0].collidepoint(mouse):
                    self.agir(botoes[i][2])
                    break

    def confirmacao_melhoria_pronta(self):
        """Espera a transição e um frame sem os comandos de tiro/confirmação."""
        if self.janela.time_elapsed() < self.melhoria_liberar_em:
            self.melhoria_aguarda_soltura = True
            return False
        if self.melhoria_aguarda_soltura:
            pressionado = (self.controle_mouse.button_pressed(1) or
                           self.controle_mouse.button_down(1) or
                           any(self.teclado.key_pressed(k) or self.teclado.key_down(k)
                               for k in ('SPACE', 'ENTER')))
            if not pressionado:
                self.melhoria_aguarda_soltura = False
            return False  # Este frame só libera: a escolha exige uma nova ação.
        return True

    def painel(self, rect, alpha=225):
        self.interface.painel(rect, alpha)

    def desenhar_jogo(self):
        p = self.partida
        player, tempo, g = p['player'], p['tempo'], p['gerenciador']
        p['missao'].draw(self.interface_mundo, self.interface_mundo.texto, player)
        for i in p['itens']:
            i.draw(self.tela, tempo)
        for ator in sorted([player]+p['zumbis'], key=lambda a: a.y+a.height):
            centro = (int(ator.x+ator.width/2), int(ator.y+ator.height-3))
            self.interface.imagem('sombra', centro[0]-12, centro[1]-4)
            if ator is player and tempo < player.invulneravel_ate and int(tempo/85) % 2:
                continue
            ator.draw(animar=self.estado == 'jogando')
        p['missao'].draw_estrutura(self.interface_mundo, self.interface_mundo.texto)
        for t in p['projeteis']:
            t.draw()
        for x, y, vx, vy, vida, cor in p['efeitos']:
            self.interface.particula(x, y, cor)
        if self.estado != 'jogando':
            return  # O mundo fica visível; os avisos não disputam espaço com os menus.
        self.painel((0, 0, LARGURA, 80), 250)
        self.texto('VIDA', 26, 5, 11, CINZA, bold=True)
        self.interface.barra_hud('vida', (18, 22, 220, 48), player.vida,
                                 player.vida_maxima, (184, 47, 57))
        self.texto(f'{max(0, player.vida):.0f} / {player.vida_maxima}',
                   128, 35, 13, centro=True, bold=True)
        arma = player.arma.upper()
        self.interface.moldura_hud('municao', (260, 7, 144, 67))
        self.interface.icone_arma(player.arma, 288, 23)
        self.texto(arma, 350, 18, 10, CINZA, centro=True, bold=True)
        self.texto(f'{player.municao:02d} / {player.municao_maxima}', 332, 32, 20,
                   OURO if player.municao > 3 else (242, 124, 105), centro=True, bold=True)
        if player.melhorias['escopeta']:
            self.texto('Q · TROCAR', 332, 56, 9, CINZA, centro=True)
        self.texto(f'ONDA {g.onda_atual:02d}', 548, 12, 23, centro=True, bold=True)
        restantes = len(p['zumbis'])+g.zumbis_restantes_para_spawnar
        status = f'{len(p["zumbis"])} no bairro · {g.zumbis_restantes_para_spawnar if not p["missao"].instalados else 0} chegando' if restantes else 'Prepare-se para a próxima onda'
        self.texto(status, 548, 46, 12, CINZA, centro=True)
        self.texto('PONTOS', 739, 12, 11, CINZA, bold=True)
        self.texto(f'{p["pontos"]:05d}', 739, 32, 24, bold=True)
        self.texto('ESC · PAUSA', 840, 30, 12, CINZA)
        self.painel((0, 588, LARGURA, 52), 245)
        self.texto(f'NÍVEL {player.nivel}  ·  XP {player.xp}/{player.xp_proximo_nivel}', 24, 592, 12, (163, 211, 103), bold=True)
        self.interface.barra_hud('xp', (260, 589, 672, 22), player.xp,
                                 player.xp_proximo_nivel, (135, 181, 67))
        self.texto('WASD mover · MOUSE mirar · CLIQUE atirar · E interagir · Q arma', 24, 614, 12, CINZA)
        self.texto(DIFICULDADES[self.dificuldade]['nome'].upper(), 840, 614, 12, OURO)
        for indice, (fim, tipo, nome) in enumerate([(player.adrenalina_ate, 'adrenalina', 'ADRENALINA'), (player.rapido_ate, 'rapido', 'DISPARO RÁPIDO')]):
            if tempo < fim:
                self.painel((24, 142+indice*34, 205, 28))
                self.interface.particula(37, 156+indice*34, CORES[tipo])
                self.texto(f'{nome}  {(fim-tempo)/1000:.1f}s', 49, 146+indice*34, 13, CORES[tipo])
        self.painel((236, 86, 488, 32), 245)
        self.texto(p['missao'].objetivo(), 480, 92, 14, OURO, centro=True, bold=True)
        missao = p['missao']
        destinos = [(f['x'],f['y'],'FUSÍVEL') for f in missao.fusiveis if not f['coletado']]
        if missao.instalados and not missao.chefe_derrotado and missao.chefe is not None:
            destinos = [(missao.chefe.x+missao.chefe.width/2,missao.chefe.y+missao.chefe.height/2,'GUARDIÃO')]
        if not destinos:
            destinos = [(*missao.painel,'PAINEL')] if not missao.aberto else [(missao.portao.x+56,missao.portao.y+45,'SAÍDA')]
        alvo = min(destinos,key=lambda a: math.dist((player.x,player.y),a[:2]))
        dx,dy = alvo[0]-(player.x+player.width/2),alvo[1]-(player.y+player.height/2)
        direcao = ('LESTE' if dx>0 else 'OESTE') if abs(dx)>abs(dy) else ('SUL' if dy>0 else 'NORTE')
        self.texto(f'{alvo[2]} · {direcao} · {int(math.hypot(dx,dy)/32)} m', 480, 121, 12, CINZA, centro=True)
        if missao.chefe is not None and missao.chefe.ativo:
            chefe = missao.chefe
            cor_chefe = (239,113,111) if chefe.enfurecido else OURO
            self.painel((250,146,460,48),245)
            self.texto(chefe.NOME+(' · FÚRIA' if chefe.enfurecido else ''),480,150,14,cor_chefe,centro=True,bold=True)
            self.interface.barra((270,176,420,10),chefe.vida,chefe.vida_maxima,cor_chefe,(57,38,41))
        instrucao = p['missao'].instrucao(player)
        if instrucao and self.estado == 'jogando':
            self.painel((236, 452, 488, 34), 245)
            self.texto(instrucao, 480, 459, 16, VERDE, centro=True, bold=True)
        if tempo < p['aviso_ate']:
            self.painel((218, 228, 524, 42), 205)
            self.texto(p['aviso'], 480, 238, 16, OURO, centro=True, bold=True)
        if self.estado == 'jogando':
            self.interface.imagem('mira', self.mouse[0]-16, self.mouse[1]-16, camera_tela=self.camera)

    def desenhar_menu(self):
        self.interface.capa_menu((0,0,LARGURA,ALTURA))
        self.interface.arte('logotipo',(18,28,430,240))
        for i,(rect,rotulo,acao,habilitado) in enumerate(self.botoes()):
            selecionado = i == self.foco
            self.interface.botao_menu(rect,selecionado)
            self.texto(rotulo,rect.centerx,rect.y+10,18,
                       (247,213,194) if selecionado else BRANCO,centro=True,bold=True)

    def fundo_painel(self, titulo, subtitulo, cor=BRANCO):
        """Uma moldura comum, com o mundo congelado ou a capa ao fundo."""
        em_partida = self.partida and (self.estado in ('pausa', 'melhoria', 'fim', 'vitoria') or
                                      (self.estado == 'opcoes' and self.retorno_opcoes == 'pausa'))
        if em_partida:
            self.arena.desenhar(self.camera)
            self.desenhar_jogo()
        else:
            self.interface.capa_menu((0, 0, LARGURA, ALTURA))
        self.painel((0, 0, LARGURA, ALTURA), 170)
        self.interface.painel_menu((60, 38, 840, 564))
        self.interface.titulo_painel(titulo, 480, 97, cor)
        self.texto(subtitulo, 480, 145, 14, CINZA, centro=True)
        self.interface.caixa((132, 177, 696, 1), (96, 39, 43))

    def botoes_painel(self):
        for i, (rect, rotulo, _, habilitado) in enumerate(self.botoes()):
            focado = habilitado and i == self.foco
            self.interface.botao_menu(rect, focado)
            self.texto(rotulo, rect.centerx, rect.y+(rect.height-22)//2, 17,
                       (247, 213, 194) if focado else BRANCO, centro=True, bold=True)

    def desenhar_configuracao(self):
        self.fundo_painel('DIFICULDADE' if self.estado == 'preparar' else 'OPÇÕES',
                          'Escolha como enfrentar a noite.' if self.estado == 'preparar' else
                          'Ajuste o áudio e confira os controles.')
        if self.estado == 'preparar':
            descricoes = [('Horda reduzida', 'Menor resistência', 'Recursos escassos'),
                          ('Horda intensa', 'Resistência padrão', 'Poucos recursos'),
                          ('Horda agressiva', 'Zumbis resistentes', 'Recursos muito raros')]
            for i, (rect, _, acao, _) in enumerate(self.botoes()[:3]):
                escolhida = self.dificuldade == acao.split(':')[1]
                self.interface.caixa(rect, (41, 24, 28) if escolhida else (23, 26, 30),
                                     (166, 58, 63) if escolhida else (55, 57, 61))
                for linha, descricao in enumerate(descricoes[i]):
                    self.texto(descricao, rect.centerx, 280+linha*29, 13, CINZA, centro=True)
                if escolhida:
                    self.texto('SELECIONADO', rect.centerx, 374, 10, (235, 133, 127), centro=True, bold=True)
            self.texto('Encontre 3 fusíveis. Ative o painel. Derrote o guardião.',
                       480, 435, 14, CINZA, centro=True)
        else:
            for y, rotulo, descricao, volume in (
                    (204, 'EFEITOS', 'Tiros, monstros e interface', self.audio.volume),
                    (266, 'MÚSICA', 'Menu e partida', self.audio.volume_musica)):
                self.texto(rotulo, 146, y, 13, BRANCO, bold=True)
                self.texto(descricao, 146, y+23, 11, CINZA)
                self.interface.barra((474, y+16, 178, 9), volume, 1,
                                     (185, 60, 65), (36, 36, 40))
                self.texto(f'{round(volume*100)}%', 686, y+10, 18, OURO, centro=True, bold=True)
            self.interface.caixa((146, 327, 668, 1), (51, 48, 50))
            self.texto('CONTROLES', 146, 343, 11, CINZA, bold=True)
            linhas = [('WASD / SETAS', 'Mover pelo bairro'), ('MOUSE', 'Mirar'),
                      ('CLIQUE / ESPAÇO', 'Atirar'), ('Q', 'Trocar de arma'),
                      ('E', 'Coletar fusível / ativar painel'), ('ESC', 'Pausar / voltar')]
            for i, (tecla, uso) in enumerate(linhas):
                self.texto(tecla, 146, 369+i*21, 13, (217, 173, 149), bold=True)
                self.texto(uso, 376, 369+i*21, 13)
            if not self.audio.sons:
                self.texto('Dispositivo de áudio indisponível.', 480, 161, 11, CINZA, centro=True)

        for i, (rect, rotulo, acao, habilitado) in enumerate(self.botoes()):
            focado = habilitado and i == self.foco
            dificuldade = self.estado == 'preparar' and acao.startswith('dificuldade:')
            escolhida = dificuldade and self.dificuldade == acao.split(':')[1]
            desenho = Rect(rect.x+10, rect.y+12, rect.width-20, 48) if dificuldade else rect
            self.interface.botao_menu(desenho, focado or escolhida)
            self.texto(rotulo, desenho.centerx, desenho.y+(desenho.height-22)//2, 17,
                       (247, 213, 194) if focado or escolhida else BRANCO, centro=True, bold=True)

    def desenhar_pausa(self):
        self.fundo_painel('PAUSA', 'A noite espera. Continue quando estiver pronto.')
        p = self.partida
        self.texto(f'NÍVEL {p["player"].nivel}  ·  ONDA {p["gerenciador"].onda_atual}  ·  {p["pontos"]} PONTOS',
                   480, 198, 13, CINZA, centro=True)
        self.botoes_painel()

    def desenhar_ranking(self):
        self.fundo_painel('RECORDES DA NOITE', 'Suas 10 melhores tentativas.')
        for texto, x in [('POSIÇÃO', 146), ('PONTOS', 344), ('ONDA', 490), ('DIFICULDADE', 648)]:
            self.texto(texto, x, 199, 11, CINZA, bold=True)
        if not self.ranking:
            self.texto('Sua primeira história ainda está por ser escrita.', 480, 310, 17, centro=True)
            self.texto('Sobreviva à noite e registre sua pontuação.', 480, 344, 13, CINZA, centro=True)
        for i, r in enumerate(self.ranking[:10]):
            y = 230+i*24
            self.interface.caixa((132, y-2, 696, 23), (43, 30, 27) if i == 0 else
                                 ((25, 28, 31) if i % 2 == 0 else (19, 22, 25)))
            for valor, x in [(f'{i+1:02d}', 146), (r['pontos'], 344),
                             (r['onda'], 490), (r['dificuldade'], 648)]:
                self.texto(valor, x, y, 13, OURO if i == 0 else BRANCO)
        self.botoes_painel()

    def desenhar_resultado(self):
        venceu = self.estado == 'vitoria'
        self.fundo_painel('VOCÊ ESCAPOU!' if venceu else 'A NOITE VENCEU.',
                          'Energia restaurada. O portão está para trás.' if venceu else
                          'Cada tentativa deixa você mais preparado.', VERDE if venceu else (235, 135, 117))
        p = self.partida
        segundos = int(p['tempo']/1000)
        self.texto('PONTUAÇÃO', 480, 196, 11, CINZA, centro=True, bold=True)
        self.interface.titulo_painel(f'{p["pontos"]:05d}', 480, 214, OURO, 42)
        estatisticas = [('TEMPO', f'{segundos//60:02d}:{segundos%60:02d}'),
                        ('NÍVEL', p['player'].nivel), ('ONDA', p['gerenciador'].onda_atual),
                        ('ELIMINAÇÕES', p['eliminacoes'])]
        for i, (rotulo, valor) in enumerate(estatisticas):
            x = 138+i*174
            self.interface.caixa((x, 294, 162, 76), (23, 26, 30), (55, 57, 61))
            self.texto(rotulo, x+81, 307, 11, CINZA, centro=True, bold=True)
            self.texto(valor, x+81, 330, 24, centro=True, bold=True)
        if venceu:
            self.texto('3/3 FUSÍVEIS INSTALADOS · GUARDIÃO DERROTADO', 480, 401, 13, VERDE, centro=True)
        else:
            self.texto(f'FUSÍVEIS {p["missao"].quantidade}/3  ·  {DIFICULDADES[self.dificuldade]["nome"].upper()}',
                       480, 401, 13, CINZA, centro=True)
        if self.erro_salvar:
            self.texto('Não foi possível salvar o recorde neste dispositivo.', 480, 445, 12, OURO, centro=True)
        self.botoes_painel()

    def desenhar_melhorias(self):
        p = self.partida
        self.fundo_painel(f'NÍVEL {p["player"].nivel} · MELHORIAS', 'Escolha um benefício para esta tentativa.')
        for i, (rect, rotulo, _, habilitado) in enumerate(self.botoes()):
            focado = habilitado and i == self.foco
            chave = p['opcoes_melhoria'][i]
            m = MELHORIAS[chave]
            nivel = p['player'].melhorias.get(chave, 0)
            self.interface.caixa(rect, (41, 24, 28) if focado else (23, 26, 30),
                                 (166, 58, 63) if focado else (55, 57, 61))
            self.texto(f'0{i+1} / MELHORIA', rect.centerx, rect.y+15, 11, CINZA, centro=True)
            self.interface.botao_menu((rect.x+10, rect.y+42, rect.width-20, 48), focado)
            self.texto(rotulo, rect.centerx, rect.y+56, 14,
                       (247, 213, 194) if focado else BRANCO, centro=True, bold=True)
            self.texto(m[1], rect.centerx, rect.y+112, 13, VERDE, centro=True)
            self.texto(m[2], rect.centerx, rect.y+146, 12, CINZA, centro=True)
            self.texto(f'NÍVEL {nivel+1} / {m[3]}' if m[3] else 'USO IMEDIATO',
                       rect.centerx, rect.y+191, 11, OURO, centro=True, bold=True)
        instrucao = ('Solte o botão de tiro antes de escolher.' if self.melhoria_aguarda_soltura else
                     'SETAS para escolher · ENTER ou NOVO CLIQUE para aplicar')
        self.texto(instrucao, 480, 477, 12, CINZA, centro=True)
        pendentes = p['player'].escolhas_pendentes
        self.texto('1 escolha disponível' if pendentes == 1 else f'{pendentes} escolhas disponíveis',
                   480, 505, 12, CINZA, centro=True)

    def desenhar(self):
        if self.estado == 'menu':
            self.desenhar_menu()
        elif self.estado in ('preparar', 'opcoes'):
            self.desenhar_configuracao()
        elif self.estado == 'pausa':
            self.desenhar_pausa()
        elif self.estado == 'ranking':
            self.desenhar_ranking()
        elif self.estado in ('fim', 'vitoria'):
            self.desenhar_resultado()
        elif self.estado == 'melhoria':
            self.desenhar_melhorias()
        elif self.estado == 'jogando':
            self.arena.desenhar(self.camera)
            self.desenhar_jogo()

    def executar(self):
        while self.rodando:
            dt = self.janela.delta_time()
            self.mouse = self.controle_mouse.get_position()
            estado_anterior = self.estado
            self.eventos()
            atirar = estado_anterior == self.estado == 'jogando' and (
                self.controle_mouse.button_pressed(1) or self.teclado.key_pressed('SPACE'))
            self.atualizar(dt, atirar=atirar)
            self.audio.atualizar_musica(dt)
            self.desenhar()
            self.janela.update()
        self.audio.encerrar()
        self.janela.close()


if __name__ == '__main__':
    Jogo().executar()
