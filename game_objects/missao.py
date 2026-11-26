"""Objetivo da primeira fase: reunir fusíveis, energizar o portão e escapar."""
import math

from game_objects.arena import Bloco
from game_objects.bairro import FUSIVEIS, PORTAO, PAINEL


class MissaoFusiveis:
    POSICOES = FUSIVEIS

    def __init__(self):
        self.fusiveis = [dict(x=x, y=y, coletado=False) for x, y in self.POSICOES]
        self.portao = Bloco(PORTAO)
        self.painel = PAINEL
        self.aberto = False
        self.instalados = False
        self.chefe = None
        self.chefe_derrotado = False

    @property
    def quantidade(self):
        return sum(f['coletado'] for f in self.fusiveis)

    @staticmethod
    def perto(player, posicao):
        return math.dist((player.x+player.width/2, player.y+player.height/2), posicao) <= 66

    def alvo(self, player):
        if not self.aberto and self.perto(player, self.painel):
            return 'painel'
        disponiveis = [i for i, f in enumerate(self.fusiveis)
                       if not f['coletado'] and self.perto(player, (f['x'], f['y']))]
        return min(disponiveis, key=lambda i: math.dist(
            (player.x+player.width/2, player.y+player.height/2),
            (self.fusiveis[i]['x'], self.fusiveis[i]['y']))) if disponiveis else None

    def interagir(self, player):
        if not player.esta_vivo():
            return None
        alvo = self.alvo(player)
        if alvo == 'painel':
            if self.instalados:
                return 'em_combate'
            if self.quantidade < 3:
                return 'faltam'
            self.instalados = True
            return 'instalou'
        if isinstance(alvo, int):
            self.fusiveis[alvo]['coletado'] = True
            return 'coletou'
        return None

    def liberar_portao(self):
        # Só a morte do chefe vinculado a esta missão autoriza a abertura.
        if (not self.instalados or self.chefe is None or self.chefe.ativo
                or self.chefe_derrotado):
            return False
        self.chefe_derrotado = True
        self.aberto = True
        self.portao.bloqueia_movimento = False
        self.portao.bloqueia_tiro = False
        return True

    def escapou(self, player):
        centro_x = player.x+player.width/2
        return (self.aberto and player.esta_vivo() and
                self.portao.x+8 <= centro_x <= self.portao.x+self.portao.width-8 and
                player.y+player.height >= self.portao.y+50)

    def objetivo(self):
        if self.aberto:
            return 'PORTÃO ABERTO · Atravesse a saída ao sul'
        if self.instalados:
            return 'CONFRONTO FINAL · Derrote o guardião do portão'
        if self.quantidade == 3:
            return 'FUSÍVEIS 3/3 · Leve-os ao painel do portão'
        return f'FUSÍVEIS {self.quantidade}/3 · Encontre os três pelo bairro'

    def instrucao(self, player):
        alvo = self.alvo(player)
        if alvo == 'painel':
            if self.instalados:
                return 'PORTÃO BLOQUEADO · Derrote o guardião'
            return 'E · Instalar os 3 fusíveis' if self.quantidade == 3 else 'E · Verificar painel (precisa de 3 fusíveis)'
        if isinstance(alvo, int):
            return 'E · Coletar fusível'
        return ''

    def draw(self, interface, texto, player):
        """Objetos no asfalto, desenhados antes dos personagens."""
        for i, f in enumerate(self.fusiveis):
            if f['coletado']:
                continue
            x, y = f['x'], f['y']
            interface.imagem('sombra', x-12, y+3)
            interface.objetivo('fusivel', (x-16, y-6, 32, 12))
            if self.perto(player, (x, y)):
                texto(f'E · FUSÍVEL {i+1}', x, y-28, 10, (229, 189, 116), centro=True, bold=True)
        if self.aberto:
            texto('SAÍDA', self.portao.x+56, self.portao.y+35, 12,
                   (112, 208, 169), centro=True, bold=True)

    def draw_estrutura(self, interface, texto):
        """Portão em pé e caixa sobre o muro: a base deles fica à frente do jogador."""
        cor = (112, 208, 169) if self.aberto else ((229, 189, 116) if self.instalados else (235, 95, 91))
        x, y = self.portao.x, self.portao.y
        # Reutiliza as duas folhas do PNG original. Abertas, ficam sobre os muros
        # laterais, deixando livre exatamente o vão que a missão desbloqueia.
        deslocamento = 55 if self.aberto else 0
        interface.objetivo('folha_esquerda', (x+1-deslocamento, y-13, 55, 33))
        interface.objetivo('folha_direita', (x+56+deslocamento, y-13, 55, 33))
        interface.objetivo('poste_esquerdo', (x-8, y-22, 10, 46))
        interface.objetivo('poste_direito', (x+110, y-22, 10, 46))
        interface.caixa((x+115, y-3, 2, 3), cor)

        px, _ = self.painel
        # A arte ocupa a face do muro; a zona de interação permanece na calçada.
        # Reserva espaço para a folha direita recolhida, sem cobrir a caixa.
        cx, cy = px+4, y+3
        interface.objetivo('painel', (cx, cy, 40, 60))
        if self.instalados:
            for altura in (18, 31, 44):
                interface.objetivo('fusivel', (cx+9, cy+altura-4, 22, 8))
        interface.caixa((cx+12, cy+8, 3, 4), cor)
        texto('PAINEL', cx+20, y-23, 10, cor, centro=True, bold=True)
