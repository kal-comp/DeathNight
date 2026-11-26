"""Desenho do jogo por componentes oficiais do Power PPlay 2.1."""
from PPlay.ui import Caixa, Label, ProgressBar, Button, Imagem, UITheme
from PPlay.sprite import Sprite
from PPlay.fontes import Fontes
from game_objects.armas import ArteDirecional


class Interface:
    def __init__(self):
        Fontes.registrar('DeathTitle','assets/fonts/BebasNeue-Regular.ttf')
        UITheme.fonte_nome = 'segoeui'
        UITheme.fonte_tam = 17
        UITheme.raio = 4
        UITheme.borda = (58, 77, 78)
        UITheme.destaque = (229, 189, 116)
        UITheme.fundo_alt = (42, 59, 62)
        self.cache = {}
        self.cores = {(229,189,116): 'ouro', (145,166,165): 'cinza',
                      (112,208,169): 'verde', (239,113,111): 'vermelho',
                      (115,222,170): 'cura', (237,193,112): 'municao',
                      (106,207,238): 'adrenalina', (219,148,237): 'rapido'}

    def obter(self, chave, criar):
        if chave not in self.cache:
            self.cache[chave] = criar()
        return self.cache[chave]

    def texto(self, texto, x, y, tamanho, cor, centro, bold, chave=None):
        # Cache por posição/estilo: pontuação variável não acumula objetos.
        w = self.obter(('texto', chave or (x, y), tamanho, centro, bold),
                       lambda: Label('', tamanho=tamanho, cor=cor, negrito=bold,
                                     fonte='DeathTitle' if tamanho>=28 else None))
        w.cor = cor
        w.set_texto(str(texto))
        w.set_position(x-w.width/2 if centro else x, y)
        w.draw()
        return w

    def caixa(self, rect, cor, borda=None, espessura=1, chave=None):
        x, y, largura, altura = rect
        w = self.obter(('caixa', chave or tuple(rect)), lambda: Caixa(largura, altura))
        w.set_position(x, y)
        w.cor, w.cor_borda, w.espessura = cor, borda, espessura
        w.draw()

    def painel(self, rect, alpha):
        x, y, largura, altura = rect
        w = self.obter(('painel', tuple(rect), alpha), lambda: Imagem(
            f'assets/images/power21/painel_{alpha}.png', largura, altura))
        w.set_position(x, y)
        w.draw()

    def arte(self,nome,rect):
        x,y,w,h=rect
        img=self.obter(('arte',nome,w,h),lambda: Imagem(f'assets/images/marca/{nome}.png',w,h))
        img.set_position(x,y)
        img.draw()

    def objetivo(self, nome, rect):
        x, y, largura, altura = rect
        img = self.obter(('objetivo', nome, largura, altura),
                         lambda: ArteObjetivo(nome, largura, altura))
        img.set_position(x, y)
        img.draw()

    def icone_arma(self, nome, x, y):
        tamanho = (22, 14) if nome == 'pistola' else (32, 9)
        arte = self.obter(('icone_arma', nome), lambda: ArteDirecional(nome, tamanho))
        arte.desenhar_centro(x, y, mundo=False)

    def capa_menu(self,rect):
        """Preenche a janela sem deformar a ilustração; mantém sua borda direita."""
        x,y,w,h=rect
        img=self.obter(('capa_menu',w,h),lambda: Imagem('assets/images/marca/ilustracao_menu.jpg'))
        escala=max(w/img.figura.width,h/img.figura.height)
        img.width=round(img.figura.width*escala)
        img.height=round(img.figura.height*escala)
        img.set_position(x+w-img.width,y+(h-img.height)/2)
        img.draw()

    def barra(self, rect, valor, maximo, cor, fundo):
        x, y, largura, altura = rect
        w = self.obter(('barra', largura, altura), lambda: ProgressBar(largura, altura, mostrar_texto=False))
        w.set_position(x, y)
        w.valor_max = maximo
        w.set_valor(valor)
        w.cor, w.cor_fundo = cor, fundo
        w.draw()
        return w

    def moldura_hud(self, nome, rect):
        x, y, largura, altura = rect
        img = self.obter(('moldura_hud', nome, largura, altura),
                         lambda: MolduraHUD(nome, largura, altura))
        img.set_position(x, y)
        img.draw()

    def barra_hud(self, nome, rect, valor, maximo, cor):
        """Preenchimento nativo sob a abertura transparente da arte da HUD."""
        x, y, largura, altura = rect
        aberturas = {'vida': (.09, .25, .82, .54),
                     'xp': (.04, .17, .924, .68)}
        esquerda, topo, w, h = aberturas[nome]
        barra = self.barra((round(x+largura*esquerda), round(y+altura*topo),
                            round(largura*w), round(altura*h)),
                           valor, maximo, cor, (23, 26, 28))
        self.moldura_hud(nome, rect)
        return barra

    def imagem(self, nome, x, y, camera_tela=None):
        if camera_tela is not None:
            x, y = x+camera_tela.x, y+camera_tela.y
        w = self.obter(('sprite', nome), lambda: Sprite(f'assets/images/power21/{nome}.png'))
        w.set_position(x, y)
        w.draw()

    def particula(self, x, y, cor):
        self.imagem('particula_'+self.cores.get(cor, 'ouro'), x-3, y-3)

    def botao(self, rect, selecionado):
        x, y, largura, altura = rect
        w = self.obter(('botao', tuple(rect)), lambda: Button('', largura, altura, cor=(20,34,42)))
        w.set_position(x, y)
        w.focado = selecionado
        w.hover = False
        w.draw()

    def botao_menu(self,rect,selecionado):
        x,y,w,h=rect
        nome='botao_selecionado' if selecionado else 'botao_normal'
        img=self.obter(('moldura_menu',nome,w,h),lambda: MolduraMenu(nome,w,h))
        img.set_position(x,y)
        img.draw()

    def painel_menu(self, rect):
        x, y, largura, altura = rect
        self.caixa((x+28, y+32, largura-56, altura-64), (15, 18, 21))
        img = self.obter(('painel_menu', largura, altura),
                         lambda: MolduraPainel(largura, altura))
        img.set_position(x, y)
        img.draw()

    def titulo_painel(self, texto, x, y, cor=(229, 235, 226), tamanho=30):
        # A fonte de leitura evita o negrito sintético da fonte condensada.
        titulo = self.obter(('titulo_painel', x, y, tamanho), lambda: Label(
            '', tamanho=tamanho, cor=cor, negrito=True, fonte='segoeui'))
        titulo.cor = cor
        titulo.set_texto(texto)
        titulo.set_position(x-titulo.width/2, y)
        titulo.draw()


class ArteObjetivo(Imagem):
    """Sprites dos objetivos recortados e desenhados pelo PPlay.ui.Imagem."""
    RECORTES = {
        'fusivel': ('fusivel', (453, 140, 1243, 478)),
        'painel': ('painel', (107, 96, 827, 1237)),
        'poste_esquerdo': ('portao', (45, 65, 135, 646)),
        'poste_direito': ('portao', (1717, 65, 135, 646)),
        'folha_esquerda': ('portao', (180, 188, 768, 460)),
        'folha_direita': ('portao', (957, 188, 760, 460)),
    }

    def __init__(self, nome, largura, altura):
        arquivo, recorte = self.RECORTES[nome]
        super().__init__(f'assets/images/objetivos/{arquivo}.png', largura, altura)
        self.figura.image = self.figura.image.subsurface(recorte)


class MolduraPainel(Imagem):
    """Moldura fornecida pelo autor, com centro transparente e margem recortada."""
    def __init__(self, largura, altura):
        super().__init__('assets/images/marca/moldura_painel.png', largura, altura)
        self.figura.image = self.figura.image.subsurface((46, 43, 1588, 850))


class MolduraMenu(Imagem):
    """Texturas de botão fornecidas pelo autor, desenhadas por PPlay.ui.Imagem."""
    def __init__(self,nome,largura,altura):
        super().__init__(f'assets/images/marca/{nome}.png',largura,altura)
        # Recorte COMUM das duas texturas, sem margens transparentes ou resíduos.
        # A view é local a esta GameImage: não altera o PNG nem o cache da engine.
        self.figura.image=self.figura.image.subsurface((24,168,1798,516))


class MolduraHUD(Imagem):
    """Recorta somente a margem transparente; a arte original fica preservada."""
    RECORTES = {'vida': (16, 13, 2140, 697),
                'municao': (29, 14, 1615, 894),
                'xp': (25, 194, 2123, 342)}

    def __init__(self, nome, largura, altura):
        super().__init__(f'assets/images/hud/{nome}.png', largura, altura)
        self.figura.image = self.figura.image.subsurface(self.RECORTES[nome])


class InterfaceMundo:
    """Componentes de UI posicionados no mundo, com cache independente da câmera."""
    def __init__(self, interface, camera):
        self.interface, self.camera = interface, camera

    def caixa(self, rect, cor, borda=None, espessura=1):
        x,y,w,h = rect
        self.interface.caixa((x-self.camera.x,y-self.camera.y,w,h), cor, borda,
                             espessura, chave=('mundo',tuple(rect)))

    def objetivo(self, nome, rect):
        x, y, w, h = rect
        self.interface.objetivo(nome, (x-self.camera.x, y-self.camera.y, w, h))

    def imagem(self, nome, x, y):
        # Sprite já aplica a câmera internamente; aqui as coordenadas são do mundo.
        self.interface.imagem(nome, x, y)

    def texto(self, texto, x, y, tamanho=18, cor=(229,235,226), centro=False, bold=False):
        return self.interface.texto(texto, x-self.camera.x, y-self.camera.y,
                                    tamanho,cor,centro,bold,chave=('mundo',x,y))

