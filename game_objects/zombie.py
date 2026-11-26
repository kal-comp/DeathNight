from PPlay.sprite import *
from game_objects.animated_character import PersonagemAnimado
from game_objects.colisao_utils import mover_com_colisao


class Zumbi(PersonagemAnimado):
    """Classe base para os zumbis. Não deve ser instanciada diretamente —
    use ZumbiCaminhante, ZumbiCorredor ou ZumbiChefe."""

    PASTA_SPRITES = "assets/images/zombies/small"
    FRAMES = 6
    DURACAO_FRAME_MS = 140
    VELOCIDADE = 70
    DANO_CONTATO = 10
    VIDA = 1
    PONTOS = 10
    XP = 10

    def __init__(self, x, y):
        animacoes = {
            "down": Sprite(f"{self.PASTA_SPRITES}/down_walk.png", total_frames=self.FRAMES),
            "up": Sprite(f"{self.PASTA_SPRITES}/up_walk.png", total_frames=self.FRAMES),
            "side": Sprite(f"{self.PASTA_SPRITES}/side_walk.png", total_frames=self.FRAMES),
            "side-left": Sprite(f"{self.PASTA_SPRITES}/side_left_walk.png", total_frames=self.FRAMES),
        }
        super().__init__(x, y, animacoes, direcao_inicial="down", duracao_frame_ms=self.DURACAO_FRAME_MS)

        self.vida_maxima = self.VIDA
        self.vida = self.VIDA
        self.dano_contato = self.DANO_CONTATO
        self.velocidade = self.VELOCIDADE
        self.ativo = True

    def seguir(self, alvo, dt, obstaculos=None):
        """Move o zumbi em direção ao centro do alvo (o jogador),
        trocando a animação conforme a direção do movimento."""
        obstaculos = obstaculos or []

        centro_x = self.x + self.width / 2
        centro_y = self.y + self.height / 2
        alvo_x = alvo.x + alvo.width / 2
        alvo_y = alvo.y + alvo.height / 2

        dx = alvo_x - centro_x
        dy = alvo_y - centro_y
        distancia = (dx ** 2 + dy ** 2) ** 0.5

        if distancia != 0:
            dx, dy = dx / distancia, dy / distancia

        self.atualizar_direcao_sprite(dx, dy)

        deslocamento_x = dx * self.velocidade * dt
        deslocamento_y = dy * self.velocidade * dt
        mover_com_colisao(self, deslocamento_x, deslocamento_y, obstaculos)

    def levar_dano(self, dano):
        self.vida -= dano
        if self.vida <= 0:
            self.ativo = False


class ZumbiCaminhante(Zumbi):
    """Zumbi comum: lento, mas constante. Disponível desde a onda 1."""
    PASTA_SPRITES = "assets/images/zombies/small"
    FRAMES = 6
    DURACAO_FRAME_MS = 150
    VELOCIDADE = 70
    DANO_CONTATO = 10
    VIDA = 3
    PONTOS = 10


class ZumbiCorredor(Zumbi):
    """Zumbi rápido, introduzido a partir da onda 3. Exige reação mais ágil."""
    PASTA_SPRITES = "assets/images/zombies/axe"
    FRAMES = 8
    DURACAO_FRAME_MS = 90
    VELOCIDADE = 150
    DANO_CONTATO = 10
    VIDA = 2.5
    PONTOS = 15
    XP = 15


class ZumbiChefe(Zumbi):
    """Zumbi chefe: muito mais resistente e mais forte, aparece a cada
    5 ondas. Mais lento que os comuns, mas difícil de derrubar."""
    PASTA_SPRITES = "assets/images/zombies/big"
    FRAMES = 8
    DURACAO_FRAME_MS = 160
    VELOCIDADE = 50
    DANO_CONTATO = 25
    VIDA = 15
    PONTOS = 60
    XP = 60


class ZumbiChefeFinal(ZumbiChefe):
    """Guardião do portão: confronto único disparado pela instalação dos fusíveis."""
    VIDA = 40
    VELOCIDADE = 65
    DANO_CONTATO = 20
    PONTOS = 250
    XP = 120
    NOME = 'GUARDIÃO DO PORTÃO'

    def seguir(self, alvo, dt, obstaculos=None):
        self.enfurecido = self.vida <= self.vida_maxima/2
        self.velocidade = self.velocidade_base * (1.3 if self.enfurecido else 1)
        super().seguir(alvo, dt, obstaculos)

    def __init__(self, x, y):
        super().__init__(x, y)
        self.velocidade_base = self.VELOCIDADE
        self.enfurecido = False

