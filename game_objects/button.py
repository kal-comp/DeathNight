from PPlay.sprite import *


class Botao:
    """Botão clicável com o mouse, usando duas imagens (normal/hover) do
    pacote de UI. Pode receber um texto opcional desenhado por cima —
    útil pro botão "Blank", que não tem rótulo na própria imagem."""

    def __init__(self, imagem_normal, imagem_pressionado, x, y, texto=None, cor_texto=(40, 28, 18)):
        self.normal = Sprite(imagem_normal)
        self.hover = Sprite(imagem_pressionado)
        self.x = x
        self.y = y
        self.texto = texto
        self.cor_texto = cor_texto
        self.width = self.normal.width
        self.height = self.normal.height

    def mouse_sobre(self, mouse):
        return mouse.is_over_area((self.x, self.y), (self.x + self.width, self.y + self.height))

    def foi_clicado(self, mouse, clique_esquerdo_agora):
        return clique_esquerdo_agora and self.mouse_sobre(mouse)

    def draw(self, janela, mouse):
        em_hover = self.mouse_sobre(mouse)
        sprite = self.hover if em_hover else self.normal
        sprite.x = self.x
        sprite.y = self.y + (self.height - sprite.height)  # mantém a base alinhada
        sprite.draw()

        if self.texto:
            largura_aprox = len(self.texto) * 9  # estimativa simples pra centralizar o texto
            tx = self.x + (self.width - largura_aprox) / 2
            ty = self.y + (self.height / 2) - 11
            janela.draw_text(self.texto, tx, ty, size=18, color=self.cor_texto, bold=True)

