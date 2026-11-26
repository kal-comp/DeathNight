from PPlay.sprite import *
from game_objects.armas import ArteDirecional


class Projetil(Sprite):
    """Tiro disparado pelo jogador na direção em que ele está olhando."""

    def __init__(self, x, y, direcao):
        super().__init__("assets/images/bullet.png")
        self.x = x - self.width / 2
        self.y = y - self.height / 2
        self.direcao = direcao  # tupla (dx, dy) normalizada
        self.velocidade = 480  # pixels por segundo
        self.dano = 1
        self.ativo = True
        self.alcance = float('inf')
        self.distancia = 0
        # A colisão continua 10 x 10; o rastro visual tem tamanho independente.
        self.arte = ArteDirecional('projetil')

    def definir_escopeta(self):
        self.arte = ArteDirecional('projetil', (10, 3))

    def draw(self):
        self.arte.desenhar_centro(self.x+self.width/2, self.y+self.height/2, self.direcao)

    def atualizar(self, dt):
        self.x += self.direcao[0] * self.velocidade * dt
        self.y += self.direcao[1] * self.velocidade * dt
        self.distancia += self.velocidade*dt
        if self.distancia >= self.alcance:
            self.ativo = False

    def fora_da_area(self, largura_janela, altura_janela):
        margem = 20
        return (
            self.x < -margem
            or self.x > largura_janela + margem
            or self.y < -margem
            or self.y > altura_janela + margem
        )

