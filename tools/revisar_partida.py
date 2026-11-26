"""Partida automatizada de revisão, com lógica e desenho reais do PPlay.

Simula somente comandos e relógio a 60 Hz, sem invencibilidade, teleporte,
munição extra, dano artificial ou bloqueio dos inimigos. Usa ranking temporário.
Não representa uma avaliação humana de dificuldade ou de áudio.
Execute: python tools/revisar_partida.py --dificuldade normal --semente 12
"""
import argparse
from collections import Counter
import json
import math
import os
from pathlib import Path
import random
import sys
import tempfile
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def revisar(dificuldade='normal', semente=12, limite=240):
    os.environ['SDL_VIDEODRIVER'] = 'dummy'
    os.environ['SDL_AUDIODRIVER'] = 'dummy'
    os.chdir(ROOT)
    import pygame
    from main import Jogo
    from game_objects.arena import AREA
    from game_objects import ranking

    random.seed(semente)
    pasta = ROOT/'output/revisao'/f'{dificuldade}_{semente}'
    pasta.mkdir(parents=True, exist_ok=True)
    dt, relogio, teclas = 1/60, [0.], set()
    eventos, sons, capturas, escolhas = [], Counter(), [], []
    rota, destino_anterior, recalcular_em = [], None, 0
    anteriores_z = {}
    vazia_total = 0.

    def centro(ator):
        return ator.x+ator.width/2, ator.y+ator.height/2

    with tempfile.TemporaryDirectory(prefix='deathnight-revisao-') as temporaria, \
            patch.object(ranking, 'CAMINHO_RANKING', str(Path(temporaria)/'ranking.json')):
        j = Jogo()
        tocar = j.audio.tocar

        def som(nome, ganho=1):
            sons[nome] += 1
            tocar(nome, ganho)

        def tecla(nome):
            codigo = j.teclado._get_code(nome)
            j.eventos([pygame.event.Event(pygame.KEYDOWN, key=codigo)])

        def captura(nome):
            j.desenhar()
            arquivo = f'{len(capturas):02d}_{nome}.png'
            pygame.image.save(j.tela, str(pasta/arquivo))
            capturas.append(arquivo)

        def livre(xy):
            return j.arena.livre(pygame.Rect(*xy, player.width, player.height))

        def objetivo():
            p, m = j.partida, j.partida['missao']
            pc = centro(player)
            itens = [i for i in p['itens'] if
                     (i.tipo == 'municao' and player.municao <= player.municao_maxima*.5) or
                     (i.tipo == 'cura' and player.vida <= player.vida_maxima*.7) or
                     (i.tipo in ('adrenalina', 'rapido') and math.dist(pc, centro(i)) < 130)]
            if itens:
                i = min(itens, key=lambda a: math.dist(pc, centro(a)))
                return i.x+i.width/2-player.width/2, i.y+i.height/2-player.height/2
            if m.aberto:
                return m.portao.x+28, m.portao.y+55-player.height
            if m.chefe and m.chefe.ativo:
                c = centro(m.chefe)
                if 180 <= math.dist(pc, c) <= 255:
                    return player.x, player.y
                opcoes = [(c[0]+220*math.cos(a)-player.width/2,
                           c[1]+220*math.sin(a)-player.height/2) for a in [i*math.tau/16 for i in range(16)]]
                return min((xy for xy in opcoes if livre(xy)),
                           key=lambda xy: math.dist((player.x, player.y), xy),
                           default=(player.x, player.y))
            if player.nivel < 3:
                return 440, 1010  # Combate inicial para verificar XP e melhorias.
            fusiveis = [f for f in m.fusiveis if not f['coletado']]
            alvo = min(fusiveis, key=lambda f: math.dist(pc, (f['x'], f['y']))) if fusiveis else None
            x, y = (alvo['x'], alvo['y']) if alvo else m.painel
            return x-player.width/2, y-player.height/2

        def escolher_movimento(destino):
            nonlocal rota, destino_anterior, recalcular_em
            p = j.partida
            pc = centro(player)
            proximos = [z for z in p['zumbis'] if math.dist(pc, centro(z)) < 150]
            if proximos:
                candidatos = [(player.x+155*math.cos(i*math.tau/16),
                               player.y+155*math.sin(i*math.tau/16)) for i in range(16)]
                seguros = [xy for xy in candidatos if livre(xy)]
                if seguros:
                    def custo(xy):
                        c = xy[0]+player.width/2, xy[1]+player.height/2
                        return sum(max(0, 240-math.dist(c, centro(z)))**2/20 for z in proximos)+math.dist(xy,destino)*.2
                    destino = min(seguros, key=custo)
            if (destino_anterior is None or math.dist(destino, destino_anterior) > 20 or
                    p['tempo'] >= recalcular_em):
                rota = j.arena.rota((player.x, player.y), destino, player.width, player.height)
                destino_anterior, recalcular_em = destino, p['tempo']+250
            while rota and math.dist((player.x, player.y), rota[0]) < 3:
                rota.pop(0)
            if not rota:
                return
            alvo = rota[0]
            velocidade = player.velocidade*(1.35 if p['tempo'] < player.adrenalina_ate else 1)
            opcoes = []
            for dx, dy in ((0,0),(1,0),(-1,0),(0,1),(0,-1),(1,1),(1,-1),(-1,1),(-1,-1)):
                mag = math.hypot(dx, dy) or 1
                xy = player.x+dx/mag*velocidade*dt, player.y+dy/mag*velocidade*dt
                rect = pygame.Rect(*xy, player.width, player.height)
                if AREA.contains(rect) and not any(rect.colliderect(o.rect) for o in j.arena.obstaculos if o.bloqueia_movimento):
                    opcoes.append((math.dist(xy, alvo), dx, dy))
            if opcoes:
                _, dx, dy = min(opcoes)
                teclas.update((['D'] if dx>0 else ['A'] if dx<0 else [])+
                              (['S'] if dy>0 else ['W'] if dy<0 else []))

        with patch.object(j.audio, 'tocar', side_effect=som), \
                patch.object(j.janela, 'time_elapsed', side_effect=lambda: relogio[0]), \
                patch.object(j.janela, 'delta_time', return_value=dt), \
                patch.object(j.teclado, 'key_pressed', side_effect=lambda k: k.upper() in teclas), \
                patch.object(j.controle_mouse, 'get_position', return_value=(0,0)), \
                patch.object(j.controle_mouse, 'button_pressed', return_value=False):
            captura('menu')
            tecla('ENTER')
            j.foco = ('facil','normal','dificil').index(dificuldade)
            tecla('ENTER')
            j.foco = 3
            tecla('ENTER')
            player = j.partida['player']
            captura('inicio')
            ultimo = (1, 0, False, False)
            pausa_testada = False
            for frame in range(round(limite/dt)):
                relogio[0] += dt*1000
                teclas.clear()
                j.janela.eventos = []
                p, m = j.partida, j.partida['missao']
                if j.estado in ('fim','vitoria'):
                    break
                if j.estado == 'melhoria':
                    opcoes = p['opcoes_melhoria']
                    prioridade = ['escopeta','dano','municao','vida','cadencia','velocidade','reserva','cura','impulso']
                    escolha = min(opcoes, key=lambda k: prioridade.index(k))
                    if player.vida < player.vida_maxima*.55 and 'vida' in opcoes:
                        escolha = 'vida'
                    j.foco = opcoes.index(escolha)
                    if j.confirmacao_melhoria_pronta():
                        tecla('ENTER')
                        escolhas.append(escolha)
                        eventos.append({'t':round(p['tempo']/1000,2),'melhoria':escolha})
                    else:
                        j.eventos([])
                    j.audio.atualizar_musica(dt)
                    j.desenhar()
                    continue
                if not pausa_testada and p['tempo'] > 6000:
                    tempo_antes = p['tempo']
                    tecla('ESC')
                    j.atualizar(1)
                    assert p['tempo'] == tempo_antes and j.estado == 'pausa'
                    assert j.audio.musica_pausada
                    captura('pausa')
                    j.foco = 2
                    tecla('ENTER')
                    assert j.estado == 'opcoes'
                    j.atualizar(1)
                    assert p['tempo'] == tempo_antes and j.audio.musica_pausada
                    captura('opcoes_pela_pausa')
                    j.foco = 4
                    tecla('ENTER')
                    assert j.estado == 'pausa'
                    tecla('ESC')
                    pausa_testada = True
                escolher_movimento(objetivo())
                pc = centro(player)
                alvos = [z for z in p['zumbis'] if
                         0 < math.dist(pc,centro(z)) < 460 and
                         5 < centro(z)[0]-j.camera.x < 955 and 82 < centro(z)[1]-j.camera.y < 580 and
                         not any(o.bloqueia_tiro and o.rect.clipline(pc,centro(z)) for o in j.arena.obstaculos)]
                alvo = min(alvos, key=lambda z: math.dist(pc,centro(z)), default=None)
                mira = (700,320)
                atirar = False
                if alvo:
                    c = centro(alvo)
                    distancia = math.dist(pc,c)
                    anterior = anteriores_z.get(id(alvo), c)
                    vx, vy = (c[0]-anterior[0])/dt, (c[1]-anterior[1])/dt
                    antecipar = min(.5,distancia/480)
                    mira = c[0]+vx*antecipar-j.camera.x, c[1]+vy*antecipar-j.camera.y
                    preferida = 'escopeta' if player.melhorias['escopeta'] and distancia < 245 else 'pistola'
                    if player.arma != preferida:
                        tecla('Q')
                    atirar = player.arma == 'pistola' or distancia < 275
                anteriores_z = {id(z): centro(z) for z in p['zumbis']}
                if m.alvo(player) is not None and not m.instalados:
                    tecla('E')
                j.atualizar(dt,mira=mira,atirar=atirar)
                j.audio.atualizar_musica(dt)
                j.desenhar()
                if player.municao == 0:
                    vazia_total += dt
                atual = player.nivel, m.quantidade, m.instalados, m.aberto
                if atual != ultimo:
                    eventos.append({'t':round(p['tempo']/1000,2),'nivel':player.nivel,'fusiveis':m.quantidade,
                                    'instalados':m.instalados,'portao':m.aberto,'vida':player.vida,'municao':player.municao})
                    captura(f'nivel{player.nivel}_fusiveis{m.quantidade}_portao{int(m.aberto)}')
                    ultimo = atual
                if frame % 1200 == 0:
                    print(json.dumps({'t':round(p['tempo']/1000,1),'estado':j.estado,'hp':player.vida,
                        'ammo':player.municao,'kills':p['eliminacoes'],'fusiveis':m.quantidade,'xy':[round(player.x),round(player.y)]}),flush=True)
            captura(j.estado)
            resumo = {'dificuldade':dificuldade,'semente':semente,'estado_final':j.estado,
                      'tempo_ativo_s':round(p['tempo']/1000,2),'vida':player.vida,'municao':player.municao,
                      'nivel':player.nivel,'xp':player.xp,'eliminacoes':p['eliminacoes'],'pontos':p['pontos'],
                      'fusiveis':m.quantidade,'boss_derrotado':m.chefe_derrotado,'portao_aberto':m.aberto,
                      'melhorias_escolhidas':escolhas,'eventos_audio':dict(sons),
                      'tempo_total_sem_municao_s':round(vazia_total,2),'pausa_verificada':pausa_testada,
                      'ranking_temporario':j.ranking,'eventos':eventos,'capturas':capturas,
                      'metodo':'Comandos simulados e relógio acelerado a 60 Hz. Lógica e desenho PPlay reais, sem alterar atributos ou inimigos.'}
            if j.estado == 'vitoria':
                assert m.quantidade == 3 and m.chefe_derrotado and m.aberto
                assert player.nivel >= 3 and 'escopeta' in escolhas
                assert sons['tiro'] > 0 and sons['tiro_escopeta'] > 0
                assert len(j.ranking) == 1
                tecla('ENTER')  # Primeiro botão do resultado: nova tentativa.
                novo = j.partida
                assert (novo['player'].nivel,novo['player'].xp,novo['player'].arma) == (1,0,'pistola')
                assert novo['missao'].quantidade == 0 and not novo['missao'].aberto
                resumo['reinicio_verificado'] = True
                captura('reinicio')
                # Nova tentativa sem mover/atirar: derrota por contato real,
                # sem escrever na vida nem chamar finalizar diretamente.
                teclas.clear()
                for _ in range(90*60):
                    relogio[0] += dt*1000
                    j.eventos([])
                    j.atualizar(dt)
                    j.audio.atualizar_musica(dt)
                    j.desenhar()
                    if j.estado == 'fim':
                        break
                assert j.estado == 'fim' and novo['player'].vida <= 0
                resumo['derrota_por_contato_verificada'] = True
                assert len(j.ranking) == 2
                captura('derrota_por_contato')
                tecla('ENTER')
                novo = j.partida
                assert (novo['player'].nivel,novo['player'].xp,novo['player'].arma) == (1,0,'pistola')
                assert novo['player'].vida == novo['player'].vida_maxima
                resumo['reinicio_apos_derrota_verificado'] = True
                captura('reinicio_apos_derrota')
            elif j.estado == 'fim':
                assert player.vida <= 0 and sons['dano'] > 0
                assert len(j.ranking) == 1
                resumo['derrota_por_contato_verificada'] = True
                tecla('ENTER')
                novo = j.partida
                assert (novo['player'].nivel,novo['player'].xp,novo['player'].arma) == (1,0,'pistola')
                assert novo['player'].vida == novo['player'].vida_maxima
                assert novo['missao'].quantidade == 0 and not novo['missao'].aberto
                resumo['reinicio_apos_derrota_verificado'] = True
                captura('reinicio_apos_derrota')
            (pasta/'resultado.json').write_text(json.dumps(resumo,ensure_ascii=False,indent=2),encoding='utf-8')
            print(json.dumps({k:v for k,v in resumo.items() if k not in ('eventos','capturas')},ensure_ascii=False),flush=True)
        j.audio.encerrar()
        pygame.quit()
        return resumo


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dificuldade',choices=('facil','normal','dificil'),default='normal')
    parser.add_argument('--semente',type=int,default=12)
    parser.add_argument('--limite',type=int,default=240)
    args = parser.parse_args()
    resultado = revisar(args.dificuldade,args.semente,args.limite)
    sys.exit(0 if resultado['estado_final'] == 'vitoria' else 1)
