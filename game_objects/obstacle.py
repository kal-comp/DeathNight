from PPlay.sprite import *


class Obstaculo(Sprite):
    """Objeto estático do cenário (barril, container...) que impede a
    passagem de jogador e zumbis, e opcionalmente também bloqueia
    projéteis."""

    def __init__(self, imagem, x, y, bloqueia_tiro=True):
        super().__init__(imagem)
        self.x = x
        self.y = y
        self.bloqueia_movimento = True
        self.bloqueia_tiro = bloqueia_tiro


class BarrilVermelho(Obstaculo):
    def __init__(self, x, y):
        super().__init__("assets/images/obstacles/barrel_red.png", x, y, bloqueia_tiro=True)


class BarrilAzul(Obstaculo):
    def __init__(self, x, y):
        super().__init__("assets/images/obstacles/barrel_blue.png", x, y, bloqueia_tiro=True)


class Container(Obstaculo):
    def __init__(self, x, y):
        super().__init__("assets/images/obstacles/container.png", x, y, bloqueia_tiro=True)

