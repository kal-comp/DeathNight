from game_objects.colisao_utils import colidiu


class PersonagemAnimado:
    """Base para personagens com sprites diferentes por direção (baixo,
    cima, lado-direito, lado-esquerdo), usando animações reais
    (spritesheets do PPlay) em vez de uma imagem única e estática.

    `animacoes` pode ter duas formas:
      - {"down": Sprite(...), "up": Sprite(...), ...}  (um único estado,
        usado pelos zumbis, que estão sempre "andando")
      - {"down": {"idle": Sprite(...), "run": Sprite(...)}, ...}  (vários
        estados por direção, usado pelo Player)
    """

    def __init__(self, x, y, animacoes, direcao_inicial="down", duracao_frame_ms=120):
        self.x = x
        self.y = y
        self.animacoes = animacoes
        self.direcao_atual_sprite = direcao_inicial
        self.estado_atual = "run"  # subclasses sem estados múltiplos ignoram isso
        todos = [s for entrada in animacoes.values()
                 for s in (entrada.values() if isinstance(entrada, dict) else [entrada])]
        self.largura_corpo = max(s.width for s in todos)
        self.altura_corpo = max(s.height for s in todos)

        # configura a duração de cada frame em todas as animações cadastradas
        for entrada in self.animacoes.values():
            sprites = entrada.values() if isinstance(entrada, dict) else [entrada]
            for sprite in sprites:
                sprite.set_total_duration(duracao_frame_ms * sprite.total_frames)

    def _sprite_ativo(self):
        entrada = self.animacoes[self.direcao_atual_sprite]
        if isinstance(entrada, dict):
            return entrada.get(self.estado_atual) or next(iter(entrada.values()))
        return entrada

    @property
    def width(self):
        return self.largura_corpo

    @property
    def height(self):
        return self.altura_corpo

    def atualizar_direcao_sprite(self, dx, dy):
        """Escolhe qual das 4 animações mostrar com base no vetor de
        movimento. Se dx=dy=0, mantém a última direção (personagem
        continua "olhando" pra onde estava indo)."""
        if dx == 0 and dy == 0:
            return
        if abs(dx) >= abs(dy):
            self.direcao_atual_sprite = "side" if dx > 0 else "side-left"
        else:
            self.direcao_atual_sprite = "down" if dy > 0 else "up"

    def draw(self, animar=True):
        sprite = self._sprite_ativo()
        sprite.x = self.x+(self.width-sprite.width)/2
        sprite.y = self.y+self.height-sprite.height
        if animar:
            sprite.update()
        sprite.draw()

    def collided(self, alvo):
        return colidiu(self, alvo)

