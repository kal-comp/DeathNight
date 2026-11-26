"""Folhas do autor para pistola e escopeta. Animação e desenho: PPlay.Sprite.

Somente a normalização de escala/alinhamento ocorre em memória com Surface e
transform.scale, pois Sprite não expõe escala por quadro. Nenhum PNG é alterado.
"""
from pygame import Surface, SRCALPHA
from pygame.transform import scale
from PPlay.sprite import Sprite


ALTURA = 64
QUADROS = 6
_folhas = {}
# Escopeta tem espaço para o cano, inclusive acima da cabeça. Os pontos
# medidos nas folhas são o centro horizontal do corpo e o topo do cabelo;
# assim a arma maior não reduz o personagem nem desloca seu corpo ao trocar.
PIVOS_ESCOPETA = {'side': (196, 47), 'down': (254, 36), 'up': (252, 80)}


def _sprite(direcao, parado=False, espelhado=False, arma='pistola'):
    caminho = f'assets/images/player/{arma}/{direcao}.png'
    largura, altura = (96, 80) if arma == 'escopeta' else (64, 64)
    sprite = Sprite(caminho, total_frames=QUADROS, linhas=2)
    if caminho not in _folhas:
        fonte = sprite.image
        w, h = fonte.get_width()//3, fonte.get_height()//2
        quadros = [fonte.subsurface((i % 3*w, i//3*h, w, h)) for i in range(QUADROS)]
        # Ignora apenas resíduos quase transparentes na margem ao medir a arte.
        caixas = [q.get_bounding_rect(min_alpha=128) for q in quadros]
        if any(c.height == 0 for c in caixas):
            raise ValueError(f'Quadro vazio na animação {caminho}')
        pivo_x = w/2
        fator = ALTURA/max(c.height for c in caixas)
        if arma == 'escopeta':
            pivo_x, topo_cabeca = PIVOS_ESCOPETA[direcao]
            fator = ALTURA/(max(c.bottom for c in caixas)-topo_cabeca)
        folha = Surface((largura*QUADROS, altura), SRCALPHA)
        for i, (quadro, caixa) in enumerate(zip(quadros, caixas)):
            tamanho = (max(1, round(caixa.width*fator)), max(1, round(caixa.height*fator)))
            figura = scale(quadro.subsurface(caixa), tamanho)
            x = largura//2+round((caixa.x-pivo_x)*fator)
            if x < 0 or x+tamanho[0] > largura or tamanho[1] > altura:
                raise ValueError(f'Arte excede o quadro: {caminho}')
            folha.blit(figura, (i*largura+x, altura-tamanho[1]))
        _folhas[caminho] = folha
    sprite.image = _folhas[caminho]
    sprite.width, sprite.height = largura, altura
    sprite.rect.size = (largura, altura)
    sprite.colunas, sprite.linhas = QUADROS, 1
    sprite.set_total_duration(660)
    sprite.set_espelhado(espelhado)
    if parado:
        sprite.set_intervalo_frames(0, 0)
    return sprite


def carregar_animacoes_arma(arma):
    return {direcao: {'idle': _sprite(folha, parado=True, espelhado=espelho, arma=arma),
                      'run': _sprite(folha, espelhado=espelho, arma=arma)}
            for direcao, folha, espelho in (
                ('down', 'down', False), ('up', 'up', False),
                ('side', 'side', False), ('side-left', 'side', True))}


def carregar_animacoes_pistola():
    return carregar_animacoes_arma('pistola')
