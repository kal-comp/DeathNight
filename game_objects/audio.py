"""Efeitos e trilhas do autor reproduzidos pelo Power PPlay 2.1."""
import math
import random
from pathlib import Path
from PPlay.sound import Sound, Music, SoundManager
from PPlay.window import Window


class Audio:
    ARQUIVOS = {
        'tiro': 'acao/pistola.wav', 'tiro_escopeta': 'acao/escopeta.wav',
        'impacto': 'acao/impacto.wav', 'parede': 'acao/parede.wav',
        'coleta': 'coleta.wav', 'cura': 'acao/cura.wav', 'municao': 'acao/municao.wav',
        'beneficio': 'acao/beneficio.wav', 'onda': 'acao/onda.wav',
        'dano': 'dano.wav', 'clique': 'clique.wav', 'vazio': 'acao/vazio.wav',
        'troca': 'acao/troca.wav', 'fusivel': 'acao/fusivel.wav',
        'painel': 'acao/painel.wav', 'portao': 'acao/portao.wav',
        'nivel': 'acao/nivel.wav', 'melhoria': 'acao/melhoria.wav',
        'vitoria': 'acao/vitoria.wav', 'derrota': 'acao/derrota.wav',
        'chefe': 'acao/chefe.wav', 'morte_zumbi': 'acao/morte_zumbi.wav',
        **{f'zumbi_{i}': f'acao/zumbi_{i}.wav' for i in (1, 2, 3)},
    }
    GANHOS = {'tiro': .65, 'tiro_escopeta': .72, 'impacto': .38, 'parede': .28,
              'clique': .45, 'dano': .65, 'chefe': .55, 'morte_zumbi': .25,
              'portao': .48, 'zumbi_1': .3, 'zumbi_2': .3, 'zumbi_3': .3}
    INTERVALOS = {'impacto': 45, 'parede': 65, 'morte_zumbi': 100, 'vazio': 500}

    def __init__(self, caminho_musica=None, caminho_menu=None):
        self.sons = {}
        self.volume = .5
        self.volume_musica = .35
        self.trilhas = {}
        self.musica = None
        self.modo = None
        self.faixa_atual = self.destino = None
        self.ganho_musica = 0.
        self.reiniciar_musica = False
        self.musica_iniciada = self.musica_pausada = False
        self.ultimos = {}
        self.rng = random.Random(7013)  # O áudio não muda os sorteios da partida.
        self.proxima_voz = 2400
        try:
            for nome, arquivo in self.ARQUIVOS.items():
                apelido = {'tiro': 'pistola', 'tiro_escopeta': 'escopeta'}.get(nome, nome)
                escolhido = next((str(p) for base in dict.fromkeys((nome, apelido))
                    for ext in ('wav', 'ogg')
                    if (p := Path(f'assets/sounds/importados/{base}.{ext}')).is_file()), None)
                self.sons[nome] = Sound(escolhido or f'assets/sounds/{arquivo}')
            # Somente músicas escolhidas pelo autor; nunca a prévia sintética.
            for nome, caminho, base, pronto in (
                    ('jogo', caminho_musica, 'musica', 'partida'),
                    ('menu', caminho_menu, 'menu', 'menu')):
                if caminho is None:
                    candidatos = [Path(f'assets/sounds/importados/{base}.{ext}')
                                  for ext in ('ogg', 'mp3', 'wav')]
                    candidatos.append(Path(f'assets/music/{pronto}.ogg'))
                    caminho = next((str(p) for p in candidatos if p.is_file()), None)
                if caminho is not None:
                    self.trilhas[nome] = Music(str(caminho))
            self.ajustar_efeitos(self.volume)
        except RuntimeError:
            self.sons = {}
            self.trilhas = {}
            self.musica = None

    def ajustar_volume(self, valor):
        """Compatibilidade com o antigo controle único."""
        self.ajustar_efeitos(valor)
        self.ajustar_musica(valor)

    def ajustar_efeitos(self, valor):
        self.volume = max(0, min(1, valor))
        for nome, som in self.sons.items():
            som.set_volume(self.volume*100*self.GANHOS.get(nome, .55))

    def ajustar_musica(self, valor):
        self.volume_musica = max(0, min(1, valor))
        self._volume_trilha()

    def _volume_trilha(self):
        if self.musica is not None:
            SoundManager.set_music_volume(self.volume_musica*100*self.ganho_musica)

    def tocar(self, nome, ganho=1):
        if nome in self.sons:
            agora = Window.get_instance().time_elapsed()
            if agora-self.ultimos.get(nome, -10000) < self.INTERVALOS.get(nome, 0):
                return
            self.ultimos[nome] = agora
            self.sons[nome].set_volume(self.volume*100*self.GANHOS.get(nome, .55)*ganho)
            self.sons[nome].play()

    def contexto(self, estado, em_partida=False):
        modo = ('jogo' if estado == 'jogando' else 'fim' if estado in ('fim', 'vitoria') else
                'pausa' if estado in ('pausa', 'melhoria') or (estado == 'opcoes' and em_partida) else 'menu')
        self.modo = modo
        self.destino = 'jogo' if modo in ('jogo', 'pausa') else 'menu' if modo == 'menu' else None
        if self.destino not in self.trilhas:
            self.destino = None
        trocar = self._precisa_trocar()
        if modo == 'pausa':
            # Pausar durante uma transição também deve silenciar o menu e
            # preparar a faixa da partida, que ficará parada no mesmo ponto.
            if trocar:
                self._trocar_trilha()
            if self.musica_iniciada and not self.musica_pausada:
                self.musica.pause()
                self.musica_pausada = True
        elif trocar and (self.musica is None or self.musica_pausada):
            self._trocar_trilha()
        elif self.musica_pausada and self.musica is not None:
            self.ganho_musica = 0.
            self._volume_trilha()
            self.musica.unpause()
            self.musica_pausada = False

    def _precisa_trocar(self):
        return (self.faixa_atual != self.destino or
                (self.reiniciar_musica and self.destino == 'jogo'))

    def _trocar_trilha(self):
        if self.musica is not None:
            # O fade do mixer pode bloquear. A rampa acontece quadro a quadro.
            self.musica.stop(fade_out_ms=0)
        self.faixa_atual = self.destino
        self.musica = self.trilhas.get(self.destino)
        self.musica_iniciada = self.musica_pausada = False
        self.ganho_musica = 0.
        if self.destino == 'jogo':
            self.reiniciar_musica = False
        if self.musica is not None:
            self._volume_trilha()
            self.musica.play(loops=-1, fade_in_ms=0)
            self.musica_iniciada = True

    def atualizar_musica(self, dt):
        """Transição não bloqueante, inclusive nas telas sem tempo de partida."""
        if self.modo == 'pausa':
            return
        restante = max(0., dt)
        if self._precisa_trocar():
            gasto = min(restante, self.ganho_musica*.28)
            self.ganho_musica = max(0., self.ganho_musica-gasto/.28)
            restante -= gasto
            self._volume_trilha()
            if self.ganho_musica <= 1e-8:
                self._trocar_trilha()
        else:
            restante = max(0., dt)
        if not self._precisa_trocar() and self.musica is not None:
            self.ganho_musica = min(1., self.ganho_musica+restante/.65)
            self._volume_trilha()

    def reiniciar_partida(self):
        self.reiniciar_musica = True
        self.proxima_voz = 2400
        self.ultimos.clear()
        for som in self.sons.values():
            som.stop()

    def atualizar(self, tempo, player, zumbis, chefe=None):
        if tempo < self.proxima_voz:
            return
        self.proxima_voz = tempo+self.rng.uniform(2200, 3500)
        proximos = [(math.dist((z.x, z.y), (player.x, player.y)), z)
                    for z in zumbis if z.ativo]
        if not proximos:
            return
        distancia, z = min(proximos, key=lambda par: par[0])
        if distancia <= 500:
            nome = 'chefe' if z is chefe else f'zumbi_{self.rng.randint(1, 3)}'
            self.tocar(nome, max(.18, 1-distancia/600))

    def encerrar(self):
        if self.musica is not None:
            self.musica.stop(fade_out_ms=0)
        for som in self.sons.values():
            som.stop()
        self.musica_iniciada = self.musica_pausada = False
        self.modo = None
        self.musica = self.faixa_atual = self.destino = None
        self.ganho_musica = 0.
