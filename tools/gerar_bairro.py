"""Arte pixelada do bairro e sprites individuais; ferramenta offline (Pillow).

Os retângulos de bairro.py determinam o tamanho da arte e das colisões.
Execute a partir de qualquer pasta: python tools/gerar_bairro.py.
A partida apenas carrega o PNG resultante usando PPlay.gameimage.GameImage.
"""
from pathlib import Path
import random
import sys

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from game_objects.bairro import (LARGURA_MUNDO, ALTURA_MUNDO, PREDIOS, CARROS,
                                 MUROS, RUAS, FUSIVEIS, PORTAO, PAINEL)

SAIDA = ROOT/'assets/images/cenario'
SAIDA.mkdir(parents=True, exist_ok=True)
RNG = random.Random(32)
ESCALA = 2
TAMANHO = (LARGURA_MUNDO//2, ALTURA_MUNDO//2)
FONT = ImageFont.load_default(size=8)
FONT_PEQUENA = ImageFont.load_default(size=6)


def cor_somada(cor, delta):
    return tuple(max(0, min(255, v+delta)) for v in cor[:3])


def legenda(d, texto, x, y, fonte=FONT, cor=(207, 199, 160)):
    d.fontmode = '1'
    d.text((x, y), texto, font=fonte, fill=cor)


def escalar(imagem):
    return imagem.resize((imagem.width*2, imagem.height*2), Image.Resampling.NEAREST)


def predio(w, h, indice):
    """Telhado de cima e fachada curta: seis silhuetas com a mesma planta física."""
    img = Image.new('RGBA', (w, h))
    d = ImageDraw.Draw(img)
    rng = random.Random(220+indice)
    paletas = [((71, 72, 70), (95, 80, 67), (147, 109, 62)),
               ((57, 70, 78), (91, 94, 86), (107, 129, 123)),
               ((63, 78, 78), (83, 98, 91), (90, 153, 127)),
               ((75, 69, 68), (102, 84, 71), (155, 120, 70)),
               ((59, 75, 73), (92, 101, 87), (77, 134, 125)),
               ((73, 73, 78), (91, 90, 88), (136, 111, 84))]
    roof,wall,accent = paletas[indice]
    frente = h-25
    d.rectangle((0,0,w-1,h-1), fill=(23,31,36))
    d.rectangle((1,2,w-2,frente), fill=roof)
    d.rectangle((4,6,w-6,frente-4), fill=cor_somada(roof,-9))
    # Juntas do telhado, manchas de umidade e remendos.
    for y in range(8,frente-3,11):
        d.line((5,y,w-6,y),fill=cor_somada(roof,-15))
        d.line((5,y+1,w-6,y+1),fill=cor_somada(roof,0))
    for _ in range(max(20,w*h//40)):
        x,y = rng.randrange(6,w-7), rng.randrange(7,frente-4)
        d.line((x,y,min(x+rng.randrange(1,5),w-7),y),fill=cor_somada(roof,rng.choice([-16,-9,5])))
    d.rectangle((1,1,w-2,3),fill=cor_somada(roof,40))
    d.rectangle((1,4,3,frente),fill=cor_somada(roof,20))
    d.rectangle((w-5,4,w-2,frente),fill=cor_somada(roof,-23))
    # Dutos, ventiladores e unidades de ar-condicionado no telhado.
    for x in range(15,w-32,58):
        y = 18 if (x//58)%2 == 0 else 31
        y = min(y,frente-25)
        d.rectangle((x+3,y+4,x+26,y+21),fill=(24,36,41))
        d.rectangle((x,y,x+23,y+16),fill=(101,112,109),outline=(132,140,127))
        d.rectangle((x+2,y+2,x+21,y+14),fill=(58,72,76))
        d.ellipse((x+3,y+3,x+13,y+13),fill=(30,43,48),outline=(122,133,123))
        d.line((x+8,y+4,x+8,y+12),fill=(82,99,99))
        d.line((x+4,y+8,x+12,y+8),fill=(82,99,99))
        for yy in range(y+3,y+14,3):d.line((x+16,yy,x+20,yy),fill=(126,135,123))
        d.line((x+23,y+9,min(w-8,x+35),y+9),fill=(126,132,117),width=2)
    # Uma claraboia com vidro quebrado.
    if w>200:
        d.rectangle((w-72,18,w-34,39),fill=(118,128,120))
        d.rectangle((w-70,20,w-36,37),fill=(37,61,69))
        for xx in range(w-69,w-35,9):d.line((xx,20,xx,37),fill=(104,129,126))
        d.line((w-65,22,w-51,35,w-43,27),fill=(160,177,154))
    # Fachada com fiadas de tijolos, friso, soleira e pilares.
    d.rectangle((1,frente,w-2,h-3),fill=wall)
    for y in range(frente+2,h-4,4):
        d.line((2,y,w-3,y),fill=cor_somada(wall,-15))
        for x in range(4+(y%8),w-3,13):
            d.line((x,y,x,y+3),fill=cor_somada(wall,-13))
    d.rectangle((0,frente-2,w-1,frente+1),fill=cor_somada(wall,32))
    d.line((0,frente+2,w-1,frente+2),fill=(28,39,43))
    d.rectangle((0,h-3,w-1,h-1),fill=(35,44,45))
    for x in range(3,w-8,34):
        d.rectangle((x,frente+5,x+21,h-6),fill=(24,36,42),outline=(136,137,115))
        d.rectangle((x+2,frente+7,x+19,h-8),fill=(37,63,68))
        d.line((x+11,frente+6,x+11,h-7),fill=(102,118,111))
        d.line((x+2,frente+10,x+18,frente+7),fill=(77,106,108))
        if (x//34+indice)%3==0:
            d.line((x+1,frente+9,x+20,h-8),fill=(126,100,68),width=3)
            d.line((x+2,frente+8,x+19,h-9),fill=(161,129,85))
        else:
            d.line((x+6,frente+7,x+10,frente+12,x+7,frente+16),fill=(153,169,146))
    porta = w//2
    if indice in (0,3,5):
        d.rectangle((porta-15,frente+3,porta+15,h-3),fill=(34,43,47),outline=(130,131,109))
        for yy in range(frente+5,h-3,3):
            d.line((porta-13,yy,porta+13,yy),fill=(87,96,92))
        d.line((porta-7,h-9,porta+8,h-9),fill=(178,146,94))
    else:
        d.rectangle((porta-9,frente+4,porta+9,h-3),fill=(20,34,40),outline=(134,143,122))
        d.rectangle((porta-7,frente+6,porta+7,h-13),fill=(50,76,77))
        d.point((porta+5,h-9),fill=(218,180,104))
    nomes = ['OFICINA 24H','DEPOSITO 07','FARMACIA','AUTO PECAS','MERCADO','ARMAZEM']
    nome=nomes[indice]
    box=d.textbbox((0,0),nome,font=FONT)
    largura=box[2]-box[0]+10
    x=(w-largura)//2
    d.rectangle((x,frente-15,x+largura,frente-5),fill=(23,38,43),outline=accent)
    legenda(d,nome,x+5,frente-15,cor=cor_somada(accent,65))
    # Toldos listrados, balcões e símbolos diferenciam os comércios.
    if indice in (2,4):
        y=frente+1
        d.rectangle((3,y,w-4,y+5),fill=accent)
        for xx in range(5,w-5,8):d.rectangle((xx,y,xx+3,y+4),fill=cor_somada(accent,35))
        if indice==2:
            d.rectangle((w-17,frente-16,w-6,frente-5),fill=(18,49,43),outline=(72,159,127))
            d.rectangle((w-13,frente-14,w-10,frente-7),fill=(140,222,159))
            d.rectangle((w-15,frente-12,w-8,frente-9),fill=(140,222,159))
    for x in (5,w-7):
        d.rectangle((x,frente+1,x+2,h-3),fill=cor_somada(wall,24))
    # Vegetação cresce nos cantos do prédio, fora das rotas centrais.
    for x in (7,w-16):
        for j in range(7):
            xx=x+rng.randrange(-3,8); yy=h-5-rng.randrange(0,8)
            d.line((xx,yy+3,xx+1,yy),fill=rng.choice([(51,76,61),(72,94,65),(87,105,71)]))
    return img


def carro(w,h,indice):
    horizontal = w>=h
    a,b = (w,h) if horizontal else (h,w)
    img=Image.new('RGBA',(a,b))
    d=ImageDraw.Draw(img)
    rng=random.Random(81+indice)
    body=[(137,83,64),(81,108,118),(111,122,87),(123,99,105)][indice]
    # Pneus, para-choques, carroceria e riscos de lataria.
    for x in (7,a-15):
        d.rectangle((x,0,x+7,4),fill=(13,21,26))
        d.rectangle((x,b-5,x+7,b-1),fill=(13,21,26))
        d.line((x+1,1,x+6,1),fill=(54,62,63))
    d.polygon([(2,6),(6,3),(a-7,3),(a-3,6),(a-2,b-7),(a-6,b-4),(6,b-4),(2,b-7)],fill=body,outline=cor_somada(body,-35))
    d.line((6,4,a-8,4),fill=cor_somada(body,38))
    d.line((5,b-5,a-7,b-5),fill=cor_somada(body,-35))
    d.rectangle((1,8,3,b-9),fill=(138,143,125))
    d.rectangle((a-4,7,a-2,b-8),fill=(100,113,110))
    # Capô amassado e grade do motor.
    d.rectangle((5,6,14,b-7),fill=cor_somada(body,-6))
    d.line((6,7,10,10,8,b-8,13,b-7),fill=(66,60,53))
    for y in range(8,b-7,3):d.point((4,y),fill=(31,39,40))
    # Para-brisa e vidro traseiro com moldura e rachaduras.
    d.polygon([(15,5),(19,7),(19,b-8),(15,b-6)],fill=(41,68,77),outline=(159,171,150))
    d.line((16,7,18,11,16,14,18,b-8),fill=(193,199,170))
    d.rectangle((20,7,a-17,b-8),fill=cor_somada(body,7))
    d.line((21,8,a-18,8),fill=cor_somada(body,34))
    d.polygon([(a-16,7),(a-12,5),(a-12,b-6),(a-16,b-8)],fill=(33,59,68),outline=(119,143,140))
    d.line((a-14,7,a-15,b-9),fill=(155,173,162))
    for x in (19,a-17):
        d.line((x,5,x,b-6),fill=cor_somada(body,-28))
        d.rectangle((x+2,3,x+5,4),fill=(190,182,146))
        d.rectangle((x+2,b-5,x+5,b-4),fill=(73,76,68))
    for _ in range(12):
        x,y=rng.randrange(5,a-5),rng.randrange(6,b-6)
        d.line((x,y,x+1,y),fill=rng.choice([(79,57,43),(155,113,66),(70,72,63)]))
    # Faróis ainda reconhecíveis e lanternas quebradas.
    for y in (6,b-9):
        d.rectangle((3,y,5,y+2),fill=(201,184,118))
        d.rectangle((a-6,y,a-4,y+2),fill=(143,69,53))
    if indice==1:
        d.rectangle((22,9,24,b-10),fill=(166,174,146))
        d.rectangle((25,9,27,b-10),fill=(91,128,159))
    if not horizontal:
        img=img.transpose(Image.Transpose.ROTATE_90)
    return img


def gerar():
    img=Image.new('RGB',TAMANHO,(27,40,40))
    d=ImageDraw.Draw(img)
    # Solo discreto, sem cobrir os pontos importantes com decoração.
    for _ in range(2800):
        x,y=RNG.randrange(16,944),RNG.randrange(56,632)
        d.point((x,y),fill=RNG.choice([(33,47,44),(38,51,46),(23,35,36)]))
    # Primeiro a malha de calçadas, depois o asfalto: cruzamentos ficam conectados.
    for x,y,w,h in RUAS:
        x,y,w,h=x//2,y//2,w//2,h//2
        d.rectangle((x-14,y-14,x+w+14,y+h+14),fill=(75,84,79))
    for y in range(57,632,8):
        d.line((16,y,943,y),fill=(58,70,67))
    for x in range(17,944,16):
        d.line((x,56,x,632),fill=(60,72,68))
    for x,y,w,h in RUAS:
        x,y,w,h=x//2,y//2,w//2,h//2
        d.rectangle((x-2,y-2,x+w+2,y+h+2),fill=(126,132,115))
        d.rectangle((x,y,x+w,y+h),fill=(37,48,53))
    # Ruas novamente por cima das bordas para remover linhas nos cruzamentos.
    for x,y,w,h in RUAS:
        x,y,w,h=x//2,y//2,w//2,h//2
        d.rectangle((x,y,x+w,y+h),fill=(37,48,53))
    def asfalto(x,y):
        return any(a//2<=x<=(a+w)//2 and b//2<=y<=(b+h)//2 for a,b,w,h in RUAS)
    for _ in range(8500):
        x,y=RNG.randrange(16,944),RNG.randrange(56,596)
        if asfalto(x,y):
            d.line((x,y,x+RNG.randrange(1,3),y),fill=RNG.choice([(41,52,57),(32,43,48),(46,56,58)]))
    # Faixas gastas e travessias de pedestres.
    for y in range(66,595,34):
        for x in (240,696):
            if not 215<y<375 and y<475:
                d.rectangle((x,y,x+1,y+15),fill=(161,147,97))
    for y in (298,543):
        for x in range(30,925,34):
            if not 157<x<315 and not 611<x<781:
                d.rectangle((x,y,x+15,y+1),fill=(161,147,97))
    for x in (176,294,624,756):
        for y in (237,352,491):
            for i in range(6):
                d.rectangle((x,y+i*4,x+12,y+i*4+1),fill=(158,170,155))
                if i%2==0:d.point((x+3,y+i*4),fill=(57,65,60))
    # Rachaduras, manchas de óleo e tampas de bueiro, esparsas.
    for x,y in [(240,380),(490,270),(650,490),(850,340),(390,560),(710,180)]:
        d.ellipse((x-12,y-5,x+11,y+6),fill=(28,39,44))
        d.line((x-18,y+12,x-13,y+9,x-5,y+11,x+1,y+17,x+8,y+16),fill=(22,34,39))
        d.line((x-5,y+11,x-6,y+6),fill=(22,34,39))
    for x,y in [(260,290),(680,540),(890,315)]:
        d.ellipse((x-7,y-5,x+7,y+5),fill=(27,39,43),outline=(94,106,98))
        for i in range(-4,5,2):d.line((x+i,y-3,x+i,y+3),fill=(69,84,82))
    # Vagas de estacionamento próximas às fachadas.
    for x0,y0 in [(330,224),(802,370)]:
        for i in range(4):
            x=x0+i*26
            d.line((x,y0,x,y0+12),fill=(110,125,115))
            d.line((x,y0+12,x+23,y0+12),fill=(110,125,115))
    nomes=['oficina','deposito','farmacia','garagem','mercado','armazem']
    for i,(x,y,w,h) in enumerate(PREDIOS):
        x,y,w,h=x//2,y//2,w//2,h//2
        d.rectangle((x+4,y+6,x+w+5,y+h+6),fill=(14,26,31))
        sprite=predio(w,h,i)
        escalar(sprite).save(SAIDA/f'predio_{nomes[i]}.png')
        img.paste(sprite,(x,y),sprite)
    for i,(x,y,w,h) in enumerate(CARROS):
        x,y,w,h=x//2,y//2,w//2,h//2
        d.rounded_rectangle((x+2,y+3,x+w+3,y+h+3),3,fill=(16,28,33))
        sprite=carro(w,h,i)
        escalar(sprite).save(SAIDA/f'carro_abandonado_{i+1}.png')
        img.paste(sprite,(x,y),sprite)
        # Fragmentos junto ao carro, sem sugerir um obstáculo novo.
        for _ in range(7):
            xx,yy=x+RNG.randrange(-5,w+5),y+RNG.randrange(-4,h+5)
            d.point((xx,yy),fill=(103,135,128))
    for x,y,w,h in MUROS:
        x,y,w,h=x//2,y//2,w//2,h//2
        d.rectangle((x,y,x+w-1,y+h),fill=(55,67,65))
        for yy in range(y+2,y+h,5):
            d.line((x,yy,x+w-1,yy),fill=(33,48,49))
            for xx in range(x+(yy%10),x+w,12):d.line((xx,yy,xx,yy+4),fill=(35,49,49))
        d.rectangle((x,y,x+w-1,y+2),fill=(128,135,114))
        for xx in range(x+7,x+w-3,20):
            d.line((xx,y+4,xx,y+15),fill=(22,36,40))
    # Poste curto e vegetação na borda das calçadas; não acrescentam colisões.
    for x,y in [(165,221),(307,377),(612,222),(778,478)]:
        d.ellipse((x-6,y-3,x+9,y+4),fill=(21,34,37))
        d.line((x,y,x,y-14),fill=(121,128,111),width=2)
        d.rectangle((x-3,y-17,x+3,y-13),fill=(234,206,130),outline=(125,137,117))
    for x,y in [(25,218),(161,207),(322,475),(928,217),(795,474),(27,471)]:
        for _ in range(12):
            xx,yy=x+RNG.randrange(-5,6),y+RNG.randrange(-4,4)
            d.line((xx,yy,xx+1,yy-3),fill=RNG.choice([(62,87,66),(79,101,71),(101,115,74)]))
    # Sinalização no solo; os fusíveis e o portão reais são desenhados pelo PPlay.
    legenda(d,'RUA DO MERCADO',390,367,FONT_PEQUENA,(123,139,133))
    legenda(d,'ACESSO OESTE',193,570,FONT_PEQUENA,(136,151,139))
    legenda(d,'SAIDA >',642,567,FONT,(183,166,112))
    d.line((680,578,700,578,695,574),fill=(183,166,112),width=2)
    d.rectangle((0,0,TAMANHO[0]-1,TAMANHO[1]-1),outline=(13,24,29),width=14)
    resultado=escalar(img)
    resultado.save(ROOT/'assets/images/power21/bairro.png')
    print('Bairro atualizado e 10 sprites individuais exportados para',SAIDA)


if __name__=='__main__':
    gerar()
