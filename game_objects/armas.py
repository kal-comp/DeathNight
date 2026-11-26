"""Artes direcionais do autor. O desenho usa PPlay.ui.Imagem e PPlay.Camera.

Apoio de pygame.transform somente para rotação/espelhamento, que o Imagem do
Power PPlay 2.1 não expõe. PNGs originais e colisores não são modificados.
"""
import math
from pygame.transform import rotate, flip
from PPlay.ui import Imagem
from PPlay.camera import Camera


class ArteDirecional(Imagem):
    ESPECIFICACOES = {
        'pistola': ((256, 153, 1052, 674), (24, 16)),
        'escopeta': ((111, 173, 1944, 424), (38, 10)),
        'projetil': ((459, 172, 1254, 357), (14, 4)),
        'clarao': ((182, 213, 1018, 745), (16, 12)),
    }
    _direcoes = {}

    def __init__(self, nome, tamanho=None):
        self.nome = nome
        recorte, padrao = self.ESPECIFICACOES[nome]
        super().__init__(f'assets/images/armas/{nome}.png', *(tamanho or padrao))
        self.figura.image = self.figura.image.subsurface(recorte)
        self.angulo = 0
        self.inverter = False

    def _superficie(self):
        chave = (self.nome, self.width, self.height, self.angulo, self.inverter)
        if chave not in self._direcoes:
            base = super()._superficie()
            if self.inverter:
                base = flip(base, False, True)
            self._direcoes[chave] = rotate(base, self.angulo) if self.angulo else base
        return self._direcoes[chave]

    def desenhar_centro(self, x, y, direcao=(1, 0), mundo=True):
        dx, dy = direcao
        self.angulo = (round(-math.degrees(math.atan2(dy, dx))/5)*5) % 360
        self.inverter = self.nome in ('pistola', 'escopeta') and dx < 0
        superficie = self._superficie()
        camera = Camera.get_instance() if mundo else None
        self.set_position(x-(camera.x if camera else 0)-superficie.get_width()/2,
                          y-(camera.y if camera else 0)-superficie.get_height()/2)
        self.draw()
