from game_objects.animated_character import PersonagemAnimado
from game_objects.colisao_utils import mover_com_colisao
from game_objects.projectile import Projetil
from game_objects.progressao import MELHORIAS
from game_objects.armas import ArteDirecional
from game_objects.personagem_pistola import carregar_animacoes_arma
import math


class Player(PersonagemAnimado):
    """Sobrevivente controlado pelo jogador."""

    def __init__(self, x, y):
        self.animacoes_pistola = carregar_animacoes_arma('pistola')
        self.animacoes_escopeta = carregar_animacoes_arma('escopeta')
        super().__init__(x, y, self.animacoes_pistola, direcao_inicial="down", duracao_frame_ms=110)
        # A arte de 64 px usa o mesmo centro e linha dos pés. A caixa lógica
        # anterior continua estável para movimento, câmera e colisão.
        self.largura_corpo, self.altura_corpo = 52, 64
        self.estado_atual = "idle"

        self.vida_maxima = 100
        self.vida = self.vida_maxima

        self.municao_maxima = 40
        self.municao = self.municao_maxima

        self.velocidade = 220  # pixels por segundo
        self.direcao_atual = (0, -1)  # direção de mira, usada pro disparo

        self.cooldown_tiro = 350  # ms entre disparos
        self.tempo_ultimo_tiro = -99999

        self.duracao_invulneravel = 800  # ms de invencibilidade após tomar dano
        self.invulneravel_ate = 0
        self.dano_tiro = 1
        self.adrenalina_ate = 0
        self.rapido_ate = 0
        self.tempo_jogo = 0
        self.melhorias = {k: 0 for k, m in MELHORIAS.items() if m[3] is not None}
        self.nivel = 1
        self.xp = 0
        self.escolhas_pendentes = 0
        self.arma = 'pistola'
        self.clarao = ArteDirecional('clarao')
        self.origem_ultimo_tiro = None

    def _sprite_ativo(self):
        animacoes = self.animacoes_pistola if self.arma == 'pistola' else self.animacoes_escopeta
        return animacoes[self.direcao_atual_sprite][self.estado_atual]

    def pontos_arma(self):
        # Pontas visíveis das armas integradas, sem sobrepor uma segunda arma.
        # Usa o vetor de mira também quando o disparo é chamado diretamente.
        dx, dy = self.direcao_atual
        direcao = ('side' if dx >= 0 else 'side-left') if abs(dx) >= abs(dy) else ('down' if dy > 0 else 'up')
        pontas = ({'side': (52, 20), 'side-left': (0, 20),
                   'down': (26, 41), 'up': (38, 7)} if self.arma == 'pistola' else
                  {'side': (61, 22), 'side-left': (-9, 22),
                   'down': (30, 37), 'up': (26, -9)})
        x, y = pontas[direcao]
        return (self.x+26, self.y+32), (self.x+x, self.y+y)

    def origem_tiro(self, obstaculos=()):
        _, ponta = self.pontos_arma()
        corpo = (self.x+self.width/2, self.y+self.height/2)
        # Cano perto de parede não permite criar um projétil do outro lado dela.
        if any(o.bloqueia_tiro and o.rect.inflate(10, 10).clipline(corpo, ponta)
               for o in obstaculos):
            return corpo
        return ponta

    def draw(self, animar=True):
        dx, dy = self.direcao_atual
        _, ponta = self.pontos_arma()
        desde_tiro = self.tempo_jogo-self.tempo_ultimo_tiro
        super().draw(animar)
        if 0 <= desde_tiro < 60:
            self.clarao.desenhar_centro(ponta[0]+dx*3, ponta[1]+dy*3, self.direcao_atual)

    @property
    def xp_proximo_nivel(self):
        return 40 + (self.nivel-1)*20

    def ganhar_xp(self, quantidade):
        if quantidade <= 0 or not self.esta_vivo():
            return
        self.xp += quantidade
        while self.xp >= self.xp_proximo_nivel:
            self.xp -= self.xp_proximo_nivel
            self.nivel += 1
            self.escolhas_pendentes += 1

    def trocar_arma(self):
        if self.melhorias['escopeta']:
            self.arma = 'escopeta' if self.arma == 'pistola' else 'pistola'

    def mirar(self, posicao):
        dx = posicao[0] - (self.x + self.width / 2)
        dy = posicao[1] - (self.y + self.height / 2)
        distancia = (dx*dx + dy*dy) ** .5
        if distancia > 1:
            self.direcao_atual = (dx/distancia, dy/distancia)
            self.atualizar_direcao_sprite(dx, dy)

    def melhorar(self, tipo):
        if tipo not in MELHORIAS:
            return False
        limite = MELHORIAS[tipo][3]
        if limite is not None:
            if self.melhorias[tipo] >= limite:
                return False
            self.melhorias[tipo] += 1
        if tipo == "dano":
            self.dano_tiro += .5
        elif tipo == "vida":
            self.vida_maxima += 25
            self.vida = min(self.vida_maxima, self.vida + 25)
        elif tipo == 'municao':
            self.municao_maxima += 8
            self.municao = min(self.municao_maxima, self.municao + 8)
        elif tipo == 'escopeta':
            self.arma = 'escopeta'
            self.municao = min(self.municao_maxima, self.municao+8)
        elif tipo == 'velocidade':
            self.velocidade = 220*(1+.08*self.melhorias[tipo])
        elif tipo == 'cadencia':
            self.cooldown_tiro = 350*.88**self.melhorias[tipo]
        elif tipo == 'cura':
            self.vida = min(self.vida_maxima, self.vida+40)
        elif tipo == 'reserva':
            self.municao = self.municao_maxima
        elif tipo == 'impulso':
            self.adrenalina_ate = max(self.adrenalina_ate, self.tempo_jogo+10000)
            self.rapido_ate = max(self.rapido_ate, self.tempo_jogo+10000)
        return True

    def mover(self, teclado, dt, limites, obstaculos=None):
        """Move o jogador com WASD/setas, troca a animação (parado/
        andando, direção) e guarda a direção de mira pro disparo."""
        obstaculos = obstaculos or []

        dx, dy = 0, 0
        if teclado.key_pressed("W") or teclado.key_pressed("UP"):
            dy -= 1
        if teclado.key_pressed("S") or teclado.key_pressed("DOWN"):
            dy += 1
        if teclado.key_pressed("A") or teclado.key_pressed("LEFT"):
            dx -= 1
        if teclado.key_pressed("D") or teclado.key_pressed("RIGHT"):
            dx += 1

        esta_andando = dx != 0 or dy != 0

        if esta_andando:
            magnitude = (dx ** 2 + dy ** 2) ** 0.5
            dx_n, dy_n = dx / magnitude, dy / magnitude
            self.direcao_atual = (dx_n, dy_n)
            self.atualizar_direcao_sprite(dx, dy)

            bonus = 1.35 if self.tempo_jogo < self.adrenalina_ate else 1
            deslocamento_x = dx_n * self.velocidade * bonus * dt
            deslocamento_y = dy_n * self.velocidade * bonus * dt
            mover_com_colisao(self, deslocamento_x, deslocamento_y, obstaculos)

        self.estado_atual = "run" if esta_andando else "idle"

        # limita o jogador dentro da área jogável do pátio
        min_x, max_x, min_y, max_y = limites
        self.x = max(min_x, min(self.x, max_x - self.width))
        self.y = max(min_y, min(self.y, max_y - self.height))

    def pode_atirar(self, tempo_atual):
        intervalo = self.cooldown_tiro * (.5 if tempo_atual < self.rapido_ate else 1)
        if self.arma == 'escopeta':
            intervalo *= 2.2
        return self.municao > 0 and (tempo_atual - self.tempo_ultimo_tiro) >= intervalo

    def disparar(self, tempo_atual, obstaculos=()):
        """Uma unidade de munição por disparo; a escopeta lança cinco projéteis."""
        if not self.pode_atirar(tempo_atual):
            return []
        central = self.atirar(tempo_atual, obstaculos)
        if self.arma == 'pistola':
            return [central]
        angulo = math.atan2(self.direcao_atual[1], self.direcao_atual[0])
        tiros = [central]
        central.alcance = 300
        central.definir_escopeta()
        for graus in (-16, -8, 8, 16):
            a = angulo+math.radians(graus)
            tiro = Projetil(*self.origem_ultimo_tiro, (math.cos(a), math.sin(a)))
            tiro.definir_escopeta()
            tiro.dano = self.dano_tiro
            tiro.alcance = 300
            tiros.append(tiro)
        return tiros

    def atirar(self, tempo_atual, obstaculos=()):
        """Cria e retorna um novo Projetil na direção atual do jogador."""
        self.tempo_ultimo_tiro = tempo_atual
        self.municao -= 1
        centro_x, centro_y = self.origem_tiro(obstaculos)
        self.origem_ultimo_tiro = (centro_x, centro_y)
        projetil = Projetil(centro_x, centro_y, self.direcao_atual)
        projetil.dano = self.dano_tiro
        return projetil

    def levar_dano(self, dano, tempo_atual):
        """Aplica dano ao jogador, respeitando a janela de invencibilidade."""
        if tempo_atual < self.invulneravel_ate:
            return
        self.vida -= dano
        self.invulneravel_ate = tempo_atual + self.duracao_invulneravel

    def esta_vivo(self):
        return self.vida > 0

