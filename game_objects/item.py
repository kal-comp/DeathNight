from PPlay.sprite import *


class ItemColetavel(Sprite):
    """Classe base para itens que o jogador pode coletar no pátio.
    Não deve ser instanciada diretamente — use ItemMunicao ou ItemCura."""

    def __init__(self, imagem, x, y, tipo, valor, tempo_atual, tempo_de_vida=8000):
        super().__init__(imagem)
        self.x = x
        self.y = y
        self.tipo = tipo
        self.valor = valor
        self.tempo_de_vida = tempo_de_vida
        self.criado_em = tempo_atual
        self.ativo = True

    def expirou(self, tempo_atual):
        """Item some do pátio se não for coletado a tempo (risco/recompensa)."""
        return (tempo_atual - self.criado_em) >= self.tempo_de_vida

    def aplicar_efeito(self, player):
        raise NotImplementedError("Subclasses devem implementar aplicar_efeito()")


class ItemMunicao(ItemColetavel):
    def __init__(self, x, y, tempo_atual):
        super().__init__("assets/images/items/bullet_box.png", x, y, "municao", valor=8, tempo_atual=tempo_atual)

    def aplicar_efeito(self, player):
        player.municao = min(player.municao_maxima, player.municao + self.valor)


class ItemCura(ItemColetavel):
    def __init__(self, x, y, tempo_atual):
        super().__init__("assets/images/items/bandage.png", x, y, "cura", valor=25, tempo_atual=tempo_atual)

    def aplicar_efeito(self, player):
        player.vida = min(player.vida_maxima, player.vida + self.valor)

