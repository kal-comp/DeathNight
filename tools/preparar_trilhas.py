"""Prepara emendas das trilhas do autor. FFmpeg e NumPy somente offline.

Os MP3s originais são preservados; o jogo usa os OGGs prontos pelo PPlay.
Execute: python tools/preparar_trilhas.py
"""
from pathlib import Path
import json
import shutil
import subprocess
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
PASTA = ROOT/'assets/music'
SR = 44100


def preparar(nome, arquivo):
    ffmpeg = shutil.which('ffmpeg')
    if not ffmpeg:
        raise RuntimeError('FFmpeg é necessário apenas para preparar as trilhas.')
    fonte = PASTA/'originais'/arquivo
    bruto = subprocess.run([ffmpeg, '-v', 'error', '-i', str(fonte), '-f', 'f32le',
                            '-ac', '2', '-ar', str(SR), 'pipe:1'],
                           capture_output=True, check=True).stdout
    audio = np.frombuffer(bruto, dtype='<f4').reshape(-1, 2).copy()
    janela = round(.02*SR)
    rms = np.array([np.sqrt(np.mean(audio[i:i+janela]**2))
                    for i in range(0, len(audio), janela)])
    audivel = np.flatnonzero(rms > 10**(-48/20))
    if not len(audivel):
        raise RuntimeError(f'Não foi encontrado áudio em {fonte}')
    inicio = max(0, audivel[0]*janela-round(.04*SR))
    fim = min(len(audio), (audivel[-1]+1)*janela+round(.04*SR))
    trecho = audio[inicio:fim]
    n = min(round(.35*SR), len(trecho)//8)
    # A emenda chega ao início do trecho já usado no primeiro frame do loop.
    fase = np.linspace(0, np.pi/2, n)[:, None]
    emenda = trecho[-n:]*np.cos(fase)+trecho[:n]*np.sin(fase)
    loop = np.concatenate((trecho[n:-n], emenda))
    ganho = min(1, .89/max(float(np.max(np.abs(loop))), 1e-9))
    loop = (loop*ganho).astype('<f4')
    saida = PASTA/(nome+'.ogg')
    subprocess.run([ffmpeg, '-v', 'error', '-y', '-f', 'f32le', '-ar', str(SR),
                    '-ac', '2', '-i', 'pipe:0', '-c:a', 'libvorbis', '-q:a', '6',
                    '-metadata', f'title=Death Night - {nome}', str(saida)],
                   input=loop.tobytes(), capture_output=True, check=True)
    return {'original': arquivo, 'arquivo': saida.name,
            'duracao_original_s': round(len(audio)/SR, 3),
            'duracao_loop_s': round(len(loop)/SR, 3),
            'inicio_aparado_s': round(inicio/SR, 3),
            'fim_aparado_s': round((len(audio)-fim)/SR, 3),
            'emenda_s': n/SR, 'ganho': round(ganho, 4)}


if __name__ == '__main__':
    relatorio = {nome: preparar(nome, arquivo) for nome, arquivo in (
        ('menu', 'DEATH NIGHT - Main Menu.mp3'),
        ('partida', 'DEATH NIGHT - Survival Loop.mp3'))}
    (PASTA/'preparacao.json').write_text(json.dumps(relatorio, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(relatorio, ensure_ascii=False, indent=2))
