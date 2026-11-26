def colidiu(objeto, alvo):
    """Checagem de colisão AABB simples (mesma lógica usada internamente
    pelo PPlay), pra objetos que não herdam de Sprite diretamente (como
    o Player e o Zumbi animados, que têm várias imagens por direção)."""
    min1_x, min1_y = objeto.x, objeto.y
    max1_x, max1_y = objeto.x + objeto.width, objeto.y + objeto.height

    min2_x, min2_y = alvo.x, alvo.y
    max2_x, max2_y = alvo.x + alvo.width, alvo.y + alvo.height

    if min1_x >= max2_x or max1_x <= min2_x:
        return False
    if min1_y >= max2_y or max1_y <= min2_y:
        return False
    return True


def mover_com_colisao(objeto, deslocamento_x, deslocamento_y, obstaculos):
    """Move o objeto no eixo X e no eixo Y separadamente, cancelando o
    deslocamento em cada eixo se colidir com algum obstáculo que bloqueia
    movimento. Isso permite 'deslizar' pela lateral do obstáculo em vez
    de travar completamente ao encostar nele."""

    if deslocamento_x != 0:
        objeto.x += deslocamento_x
        for obstaculo in obstaculos:
            if obstaculo.bloqueia_movimento and objeto.collided(obstaculo):
                objeto.x -= deslocamento_x
                break

    if deslocamento_y != 0:
        objeto.y += deslocamento_y
        for obstaculo in obstaculos:
            if obstaculo.bloqueia_movimento and objeto.collided(obstaculo):
                objeto.y -= deslocamento_y
                break

