"""Cenário vetorial, colisores e rotas de contorno compartilhadas."""
import heapq
import math
import random

from pygame import Rect  # Somente geometria das rotas; desenho e janela usam PPlay.
from PPlay.gameimage import GameImage
from game_objects.bairro import LARGURA_MUNDO, ALTURA_MUNDO, INICIO, PREDIOS, CARROS, MUROS


LARGURA, ALTURA = 960, 640
AREA = Rect(32, 112, 1856, 1152)


class Bloco:
    bloqueia_movimento = True
    bloqueia_tiro = True

    def __init__(self, rect):
        self.rect = Rect(rect)
        self.x, self.y, self.width, self.height = self.rect


class Arena:
    def __init__(self):
        self.obstaculos = [Bloco(r) for r in (*PREDIOS, *CARROS, *MUROS)]
        self.fundo = GameImage("assets/images/power21/bairro.png")
        self.alvo_spawn = INICIO

    def desenhar(self, camera):
        # GameImage usa coordenadas de tela; os Sprites já usam Camera internamente.
        self.fundo.set_position(-camera.x, -camera.y)
        self.fundo.draw()

    def livre(self, rect):
        return AREA.contains(rect) and not any(rect.colliderect(o.rect.inflate(8, 8)) for o in self.obstaculos if o.bloqueia_movimento)

    def posicao_livre(self, largura, altura, rng=random, perto=None, raio=None):
        # A varredura garante uma posição válida mesmo se os sorteios falharem.
        for _ in range(60):
            x0,x1,y0,y1 = AREA.left,AREA.right-int(largura),AREA.top,1192-int(altura)
            if perto is not None:
                rx, ry = (320, 260) if raio is None else (raio, raio)
                x0,x1 = max(x0,int(perto[0]-rx)),min(x1,int(perto[0]+rx))
                y0,y1 = max(y0,int(perto[1]-ry)),min(y1,int(perto[1]+ry))
            rect = Rect(rng.randint(x0,x1),rng.randint(y0,y1),largura,altura)
            if self.livre(rect):
                return rect.topleft
        for y in range(AREA.top, 1192-int(altura), 8):
            for x in range(AREA.left, AREA.right-int(largura), 8):
                if self.livre(Rect(x, y, largura, altura)):
                    return x, y
        return None

    def spawn(self):
        # Nasce nos acessos ao redor do jogador, nunca dentro de uma construção.
        candidatos = []
        x, y = self.alvo_spawn
        for _ in range(100):
            angulo = random.random()*math.tau
            distancia = random.uniform(510, 720)
            px, py = x+math.cos(angulo)*distancia, y+math.sin(angulo)*distancia
            rect = Rect(px, py, 96, 96)  # Comporta corredor e chefe em todas as direções.
            if self.livre(rect):
                candidatos.append((int(px), int(py)))
        if candidatos:
            return random.choice(candidatos)
        return self.posicao_livre(96, 96)

    def rota(self, inicio, destino, largura, altura):
        # Grafo de visibilidade para o canto superior esquerdo do personagem.
        caixas = [Rect(o.x-largura-3, o.y-altura-3,
                             o.width+largura+6, o.height+altura+6) for o in self.obstaculos if o.bloqueia_movimento]
        # A folga do planejador é maior que a colisão real. Ao recalcular uma
        # rota perto da parede, sair primeiro dessa margem evita ficar preso
        # num ponto de partida que o próprio grafo considera bloqueado.
        if any(c.collidepoint(inicio) for c in caixas):
            def corpo_livre(x, y):
                return (AREA.left <= x <= AREA.right-largura and
                        AREA.top <= y <= AREA.bottom-altura and not any(
                            x < o.x+o.width and x+largura > o.x and
                            y < o.y+o.height and y+altura > o.y
                            for o in self.obstaculos if o.bloqueia_movimento))
            if not corpo_livre(*inicio):
                return []
            for raio in (2, 4, 8, 12, 20):
                candidatos = [(inicio[0]+raio*math.cos(i*math.tau/16),
                               inicio[1]+raio*math.sin(i*math.tau/16)) for i in range(16)]
                candidatos.sort(key=lambda p: math.dist(p, destino))
                for p in candidatos:
                    if any(c.collidepoint(p) for c in caixas):
                        continue
                    # A pequena saída também respeita colisores reais em todo
                    # o segmento; a correção não atravessa nem teleporta o ator.
                    if not all(corpo_livre(inicio[0]+(p[0]-inicio[0])*s/raio,
                                          inicio[1]+(p[1]-inicio[1])*s/raio)
                               for s in range(1, raio+1)):
                        continue
                    restante = self.rota(p, destino, largura, altura)
                    if restante:
                        return [p]+restante
            return []
        # O chefe é maior que o jogador: aproxima o alvo a uma posição que caiba.
        destino = (max(AREA.left, min(destino[0], AREA.right-largura)),
                   max(AREA.top, min(destino[1], AREA.bottom-altura)))
        for caixa in caixas:
            if caixa.collidepoint(destino):
                candidatos = [(caixa.left-2, destino[1]), (caixa.right+2, destino[1]),
                              (destino[0], caixa.top-2), (destino[0], caixa.bottom+2)]
                candidatos = [p for p in candidatos if AREA.contains(Rect(*p, largura, altura))
                              and not any(c.collidepoint(p) for c in caixas)]
                if candidatos:
                    destino = min(candidatos, key=lambda p: math.dist(p, destino))
        def visivel(a, b):
            return not any(r.clipline(a, b) for r in caixas)
        if visivel(inicio, destino):
            return [destino]
        pontos = [inicio, destino]
        for r in caixas:
            for p in [(r.left-2, r.top-2), (r.right+2, r.top-2),
                      (r.left-2, r.bottom+2), (r.right+2, r.bottom+2)]:
                if AREA.contains(Rect(*p, largura, altura)) and not any(c.collidepoint(p) for c in caixas):
                    pontos.append(p)
        fila = [(0, 0, [])]
        visitados = set()
        while fila:
            custo, i, caminho = heapq.heappop(fila)
            if i in visitados:
                continue
            if i == 1:
                return [pontos[j] for j in caminho]
            visitados.add(i)
            for j, p in enumerate(pontos):
                if j not in visitados and visivel(pontos[i], p):
                    heapq.heappush(fila, (custo+math.dist(pontos[i], p), j, caminho+[j]))
        return []

