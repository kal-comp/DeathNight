"""Itens com silhuetas distintas e coleta que não desperdiça recursos cheios."""
import random
from PPlay.sprite import Sprite
from PPlay.ui import Imagem
from PPlay.camera import Camera
from game_objects.colisao_utils import colidiu

CORES = {'cura': (115, 222, 170), 'municao': (237, 193, 112),
         'adrenalina': (106, 207, 238), 'rapido': (219, 148, 237)}
NOMES = {'cura': 'Vida +25', 'municao': 'Munição +16',
         'adrenalina': 'Adrenalina · 6s', 'rapido': 'Disparo rápido · 8s'}


def ciclo_suprimentos():
    """Mesmos pesos 5/3/1/1; benefícios aparecem no 3º e no 6º item aleatório."""
    recursos = ['municao']*5 + ['cura']*3
    random.shuffle(recursos)
    beneficios = random.sample(['adrenalina', 'rapido'], 2)
    return [recursos.pop(), recursos.pop(), beneficios[0],
            recursos.pop(), recursos.pop(), beneficios[1], *recursos]


class ArteSuprimento(Imagem):
    """Recorte e escala do PNG fornecido pelo autor, por componentes PPlay."""
    ESPECIFICACOES = {
        'cura': ((296, 151, 944, 681), (30, 22)),
        'municao': ((109, 61, 1130, 1013), (28, 25)),
        'adrenalina': ((322, 65, 1528, 565), (36, 14)),
        'rapido': ((154, 77, 1071, 960), (28, 25)),
    }

    def __init__(self, tipo):
        recorte, tamanho = self.ESPECIFICACOES[tipo]
        super().__init__(f'assets/images/suprimentos/{tipo}.png', *tamanho)
        self.figura.image = self.figura.image.subsurface(recorte)


class Suprimento:
    width = height = 22

    def __init__(self, tipo, x, y, tempo):
        self.tipo, self.x, self.y, self.criado_em = tipo, x, y, tempo
        self.ativo = True
        if tipo in ArteSuprimento.ESPECIFICACOES:
            self.sprite = ArteSuprimento(tipo)
            self.sombra = Sprite('assets/images/power21/sombra.png')
        else:
            self.sprite = Sprite(f"assets/images/power21/{tipo}.png")

    def collided(self, alvo):
        return colidiu(self, alvo)

    def expirou(self, tempo):
        return tempo-self.criado_em >= 14000

    def aplicar(self, player, tempo):
        if self.tipo == 'cura':
            if player.vida >= player.vida_maxima:
                return False
            player.vida = min(player.vida_maxima, player.vida+25)
        elif self.tipo == 'municao':
            if player.municao >= player.municao_maxima:
                return False
            player.municao = min(player.municao_maxima, player.municao+16)
        elif self.tipo == 'adrenalina':
            player.adrenalina_ate = tempo+6000
        else:
            player.rapido_ate = tempo+8000
        self.ativo = False
        return True

    def draw(self, tela, tempo):
        if tempo-self.criado_em > 11000 and int(tempo/160) % 2:
            return
        if isinstance(self.sprite, ArteSuprimento):
            # A arte fica centrada na área de coleta existente (22 x 22).
            cx, cy = self.x+self.width/2, self.y+self.height/2
            self.sombra.set_position(cx-12, cy+6)
            self.sombra.draw()  # Sprite aplica a câmera automaticamente.
            camera = Camera.get_instance()
            self.sprite.set_position(cx-self.sprite.width/2-(camera.x if camera else 0),
                                     cy-self.sprite.height/2-(camera.y if camera else 0))
        else:
            self.sprite.set_position(self.x-11, self.y-11)
        self.sprite.draw()
