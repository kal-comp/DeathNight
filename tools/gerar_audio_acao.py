"""Áudio original sintetizado offline. Requer NumPy somente para reconstruir.

Nenhuma amostra de terceiros. O jogo toca os WAVs pelo PPlay, sem NumPy.
Execute: python tools/gerar_audio_acao.py
"""
from pathlib import Path
import wave
import numpy as np

PASTA = Path(__file__).resolve().parents[1]/'assets/sounds/acao'
SR = 44100
RNG = np.random.default_rng(8312026)


def eixo(segundos):
    return np.arange(round(segundos*SR), dtype=np.float64)/SR


def envelope(t, ataque=.003, queda=12):
    return np.minimum(t/max(ataque, .0001), 1)*np.exp(-t*queda)


def ruido(t, grave=False):
    n = RNG.uniform(-1, 1, len(t))
    if grave:
        n = np.convolve(n, np.ones(31)/31, mode='same')*3
    return n


def tom(t, frequencia, queda=12):
    return np.sin(2*np.pi*frequencia*t)*envelope(t, queda=queda)


def gravar(nome, sinal, pico=.86):
    sinal = np.asarray(sinal)
    if sinal.ndim == 1:
        sinal = np.column_stack((sinal, sinal))
    maximo = np.max(np.abs(sinal))
    if maximo:
        sinal = sinal/maximo*pico
    borda = min(220, len(sinal)//4)
    sinal[:borda] *= np.linspace(0, 1, borda)[:, None]
    sinal[-borda:] *= np.linspace(1, 0, borda)[:, None]
    PASTA.mkdir(parents=True, exist_ok=True)
    with wave.open(str(PASTA/(nome+'.wav')), 'wb') as arq:
        arq.setnchannels(2)
        arq.setsampwidth(2)
        arq.setframerate(SR)
        arq.writeframes((np.clip(sinal, -1, 1)*32767).astype('<i2').tobytes())


def acorde(notas, duracao=.6, queda=8):
    t = eixo(duracao)
    return sum(tom(t, f, queda) for f in notas)/len(notas)


def motivo(notas, passo=.10, duracao=.8):
    y = np.zeros(len(eixo(duracao)))
    for i, f in enumerate(notas):
        inserir(y, tom(eixo(.28), f, 17), i*passo)
    return y


def inserir(destino, trecho, inicio, ganho=1):
    inicio = round(inicio*SR)
    fim = min(len(destino), inicio+len(trecho))
    if fim > inicio:
        destino[inicio:fim] += trecho[:fim-inicio]*ganho


def efeitos():
    for nome, duracao, grave, forca in [('pistola', .25, 95, .62), ('escopeta', .46, 55, .95)]:
        t = eixo(duracao)
        corpo = np.sin(2*np.pi*(grave*t+2.1*(1-np.exp(-t*48))))
        estampido = ruido(t)*np.exp(-t*(54 if nome=='pistola' else 32))
        cauda = ruido(t, True)*np.exp(-t*14)
        gravar(nome, (estampido+corpo*forca*np.exp(-t*30)+.18*cauda)*np.minimum(t/.0004, 1))
    for i, f in enumerate((54, 67, 46), 1):
        t = eixo(.85+i*.06)
        fase = 2*np.pi*(f*t+1.1*np.sin(t*7))
        voz = (np.sin(fase)+.32*np.sin(fase*2)+.17*np.sin(fase*5))
        aspereza = ruido(t, True)*.6
        mod = .62+.38*np.sin(t*25)**2
        forma = np.minimum(t/.08, 1)*np.minimum((t[-1]-t)/.22, 1)
        gravar(f'zumbi_{i}', (voz*.5+aspereza)*mod*forma, .72)
    t = eixo(1.3)
    gravar('chefe', (np.sin(2*np.pi*(38*t+1.5*np.sin(t*4)))+.7*ruido(t, True))*
           np.minimum(t/.05, 1)*np.exp(-t*2.5))
    t = eixo(.5)
    gravar('morte_zumbi', (ruido(t, True)+tom(t, 54, 7)) * np.minimum(t/.01, 1)*np.exp(-t*6))
    t = eixo(.16)
    gravar('impacto', ruido(t, True)*envelope(t, queda=38)+tom(t, 95, 45)*.2)
    gravar('parede', ruido(t)*envelope(t, queda=65)+tom(t, 1500, 60)*.15)
    gravar('vazio', motivo([1700, 900], .025, .13), .5)
    gravar('troca', motivo([420, 740, 330], .06, .3), .6)
    gravar('cura', motivo([440, 554.37, 659.25], .07, .5), .6)
    gravar('municao', motivo([380, 570], .055, .35), .65)
    gravar('beneficio', motivo([523.25, 783.99, 1046.5, 1318.51], .065, .65), .62)
    gravar('fusivel', motivo([660, 880, 1320], .07, .55), .65)
    t = eixo(.9)
    gravar('painel', motivo([220, 330, 440, 660], .11, .9)+ruido(t)*envelope(t, queda=9)*.1)
    t = eixo(1.1)
    motor = (np.sin(t*2*np.pi*72)+.5*np.sin(t*2*np.pi*144)+ruido(t, True)*.5)
    motor *= np.minimum(t/.08, 1)*np.minimum((t[-1]-t)/.15, 1)
    gravar('portao', motor*(.18+.08*np.sin(t*43)**2), .8)
    gravar('nivel', motivo([329.63, 392, 493.88, 659.25], .1, .9), .65)
    gravar('melhoria', motivo([659.25, 987.77], .07, .5), .55)
    gravar('onda', motivo([164.81, 164.81, 246.94], .2, 1.1), .7)
    gravar('vitoria', motivo([329.63, 392, 493.88, 659.25, 783.99], .15, 1.7), .7)
    gravar('derrota', motivo([329.63, 293.66, 246.94, 164.81], .22, 1.8), .7)


def frequencia(midi):
    return 440*2**((midi-69)/12)


def trilha():
    """32 compassos, 128 BPM, baixo pulsante, bateria e arpejos em mi menor."""
    batida = 60/128
    duracao = 32*4*batida
    y = np.zeros(len(eixo(duracao)))
    tk = eixo(.32)
    kick = np.sin(2*np.pi*(45*tk+2.8*(1-np.exp(-tk*32))))*envelope(tk, queda=18)
    ts = eixo(.2)
    snare = (ruido(ts)*.75+np.sin(ts*2*np.pi*185)*.25)*envelope(ts, queda=27)
    th = eixo(.065)
    n = ruido(th)
    hat = (n-np.roll(n, 1))*envelope(th, queda=70)
    raizes = (40, 36, 43, 38)  # Em, C, G, D.
    notas_acorde = ((0, 3, 7), (0, 4, 7), (0, 4, 7), (0, 4, 7))
    for compasso in range(32):
        inicio = compasso*4*batida
        parte = compasso//8
        raiz = raizes[compasso % 4]
        intervalos = notas_acorde[compasso % 4]
        for b in range(4):
            inserir(y, kick, inicio+b*batida, .6)
            if b in (1, 3):
                inserir(y, snare, inicio+b*batida, .24)
        for subdivisao in range(8):
            inserir(y, hat, inicio+subdivisao*batida/2, .052 if subdivisao % 2 else .035)
            tb = eixo(batida*.40)
            f = frequencia(raiz+(12 if subdivisao==7 else 0))
            baixo = np.tanh(2.1*(np.sin(2*np.pi*f*tb)+.2*np.sin(2*np.pi*f*2*tb)))
            inserir(y, baixo*envelope(tb, queda=16), inicio+subdivisao*batida/2, .24)
        tp = eixo(4*batida)
        pad = sum(np.sin(2*np.pi*frequencia(raiz+12+i)*tp) for i in intervalos)/3
        pad *= np.sin(np.pi*np.linspace(0, 1, len(tp)))**2
        inserir(y, pad, inicio, .11)
        if parte != 2 or compasso % 2:
            for passo in range(8):
                ta = eixo(batida*.40)
                nota = raiz+24+intervalos[(passo+compasso) % 3]
                if passo in (3, 7):
                    nota += 12
                f = frequencia(nota)
                arp = (np.sin(ta*2*np.pi*f)+.17*np.sin(ta*2*np.pi*f*2))*envelope(ta, queda=19)
                inserir(y, arp, inicio+passo*batida/2, .10 if parte==0 else .15)
    # Uma reflexão curta e discreta abre espaço estéreo sem alterar o ritmo.
    atraso = round(.017*SR)
    esquerda = y*.93
    direita = y*.87
    direita[atraso:] += y[:-atraso]*.06
    gravar('noite_em_alerta', np.column_stack((esquerda, direita)), .78)


if __name__ == '__main__':
    efeitos()
    trilha()
    print(f'{len(list(PASTA.glob("*.wav")))} WAVs originais em {PASTA}')
