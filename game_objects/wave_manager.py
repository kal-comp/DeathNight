import random

from game_objects.zombie import ZumbiCaminhante, ZumbiCorredor, ZumbiChefe
from game_objects.dificuldade import DIFICULDADES


class GerenciadorDeOndas:
    """Controla o spawn de zumbis e a progressão de dificuldade por ondas.

    Uso no loop principal:
        novo_zumbi = gerenciador.atualizar(tempo_atual, len(zumbis))
        if novo_zumbi:
            zumbis.append(novo_zumbi)
    """

    def __init__(self, pontos_de_spawn_callback, dificuldade="normal", intervalo_entre_ondas=2000):
        self.onda_atual = 0
        self.zumbis_restantes_para_spawnar = 0
        self.intervalo_spawn = 1200  # ms, diminui a cada onda
        self.tempo_ultimo_spawn = 0

        self.pontos_de_spawn_callback = pontos_de_spawn_callback  # função -> (x, y) na borda
        self.dificuldade_chave = dificuldade if dificuldade in DIFICULDADES else "normal"
        self.dificuldade = DIFICULDADES[self.dificuldade_chave]

        self.aguardando_proxima_onda = False
        self.tempo_inicio_intervalo = 0
        self.intervalo_entre_ondas = intervalo_entre_ondas

        self.chefe_ja_spawnado_nesta_onda = False

    def _zumbis_da_onda(self, onda):
        base = 12 + onda * 4
        return max(1, round(base * self.dificuldade["multiplicador_zumbis"]))

    def _intervalo_spawn_da_onda(self, onda):
        return max(180, round((560 - onda * 35)/self.dificuldade['multiplicador_zumbis']))

    def _eh_onda_de_chefe(self):
        return self.onda_atual > 0 and self.onda_atual % 5 == 0

    def _sortear_tipo(self):
        if self._eh_onda_de_chefe() and not self.chefe_ja_spawnado_nesta_onda:
            self.chefe_ja_spawnado_nesta_onda = True
            return ZumbiChefe

        chance_corredor = min(0.15 + 0.05 * self.onda_atual, 0.6)
        if self.onda_atual >= 3 and random.random() < chance_corredor:
            return ZumbiCorredor
        return ZumbiCaminhante

    def iniciar_proxima_onda(self, tempo_atual):
        self.onda_atual += 1
        self.zumbis_restantes_para_spawnar = self._zumbis_da_onda(self.onda_atual)
        self.intervalo_spawn = self._intervalo_spawn_da_onda(self.onda_atual)
        self.tempo_ultimo_spawn = tempo_atual
        self.aguardando_proxima_onda = False
        self.chefe_ja_spawnado_nesta_onda = False

    def reiniciar(self):
        """Chamado ao reiniciar a partida (Game Over -> novo jogo)."""
        self.__init__(self.pontos_de_spawn_callback, self.dificuldade_chave, self.intervalo_entre_ondas)

    def atualizar(self, tempo_atual, zumbis_vivos):
        """Deve ser chamado a cada frame. Retorna um novo Zumbi para
        adicionar à lista do jogo, ou None se não for a hora de nascer."""

        onda_concluida = self.zumbis_restantes_para_spawnar == 0 and zumbis_vivos == 0

        if onda_concluida:
            if not self.aguardando_proxima_onda:
                self.aguardando_proxima_onda = True
                self.tempo_inicio_intervalo = tempo_atual
                return None

            if tempo_atual - self.tempo_inicio_intervalo >= self.intervalo_entre_ondas:
                self.iniciar_proxima_onda(tempo_atual)
            return None

        if self.zumbis_restantes_para_spawnar > 0:
            if zumbis_vivos >= 60:
                return None
            if tempo_atual - self.tempo_ultimo_spawn >= self.intervalo_spawn:
                self.tempo_ultimo_spawn = tempo_atual
                self.zumbis_restantes_para_spawnar -= 1
                classe_zumbi = self._sortear_tipo()
                x, y = self.pontos_de_spawn_callback()
                zumbi = classe_zumbi(x, y)
                resistencia = self.dificuldade['multiplicador_vida'] * min(2.0, 1+max(0,self.onda_atual-1)*.10)
                zumbi.vida_maxima = zumbi.vida = round(zumbi.VIDA*resistencia,2)
                zumbi.velocidade *= self.dificuldade["multiplicador_velocidade"]
                zumbi.dano_contato = max(1, round(zumbi.dano_contato * self.dificuldade["multiplicador_dano"]))
                return zumbi

        return None

