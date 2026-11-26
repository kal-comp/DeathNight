"""Identidade visual editável: fonte OFL, logotipo SVG/PNG e peças de divulgação."""
from pathlib import Path
import base64
import math
import random
from PIL import Image,ImageDraw,ImageFont,ImageFilter
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'assets/images/marca'
OUT.mkdir(parents=True,exist_ok=True)
EXPORT=ROOT/'output/identidade'
EXPORT.mkdir(parents=True,exist_ok=True)
FONT=ROOT/'assets/fonts/BebasNeue-Regular.ttf'
PAPEL=(230,232,215)
AMBAR=(226,166,90)
VERMELHO=(161,57,46)


def fonte(tamanho):return ImageFont.truetype(str(FONT),tamanho)


def logo():
    img=Image.new('RGBA',(1280,280))
    d=ImageDraw.Draw(img)
    # Fusível vertical: símbolo da missão, legível também sem o nome.
    d.polygon([(55,75),(78,52),(166,52),(189,75),(189,199),(166,222),(78,222),(55,199)],fill=(19,34,39),outline=AMBAR,width=3)
    d.rectangle((105,72,139,203),fill=(29,53,58),outline=PAPEL,width=3)
    d.rectangle((99,72,145,93),fill=AMBAR)
    d.rectangle((99,183,145,203),fill=AMBAR)
    d.line((122,99,115,119,130,140,115,162,122,178),fill=PAPEL,width=4)
    d.line((18,137,54,137),fill=AMBAR,width=3)
    d.line((189,137,224,137),fill=AMBAR,width=3)
    f=fonte(210)
    x=235
    for i,ch in enumerate('DEATH NIGHT'):
        cor=PAPEL if i<6 else AMBAR
        d.text((x,47),ch,font=f,fill=cor,anchor='lt')
        x+=f.getlength(ch)+6
    # Cortes finos no letreiro, sem prejudicar leitura em thumbnail.
    mask=img.getchannel('A');md=ImageDraw.Draw(mask)
    for pts in [[(247,123),(1108,113),(1108,117),(247,127)],[(736,177),(1032,169),(1032,171),(736,179)]]:
        md.polygon(pts,fill=0)
    img.putalpha(mask)
    d=ImageDraw.Draw(img)
    d.line((238,227,1118,227),fill=VERMELHO,width=5)
    for x in range(1142,1200,18):d.line((x,217,x-8,236),fill=AMBAR,width=4)
    img.save(OUT/'logo.png');img.save(EXPORT/'logo_transparente.png')
    enc=base64.b64encode(FONT.read_bytes()).decode()
    svg=f'''<svg xmlns="http://www.w3.org/2000/svg" width="1280" height="280" viewBox="0 0 1280 280">
<title>Death Night — logotipo com fusível</title>
<style>@font-face{{font-family:DeathTitle;src:url(data:font/ttf;base64,{enc})}}text{{font-family:DeathTitle,sans-serif;letter-spacing:6px}}</style>
<defs><mask id="desgaste"><rect width="1280" height="280" fill="white"/><path d="M247 123L1108 113V117L247 127Z M736 177L1032 169V171L736 179Z" fill="black"/></mask></defs>
<path d="M55 75L78 52H166L189 75V199L166 222H78L55 199Z" fill="#132227" stroke="#e2a65a" stroke-width="3"/>
<path d="M18 137H54M189 137H224" stroke="#e2a65a" stroke-width="3"/>
<rect x="105" y="72" width="34" height="131" fill="#1d353a" stroke="#e6e8d7" stroke-width="3"/>
<path d="M99 72H145V93H99ZM99 183H145V203H99Z" fill="#e2a65a"/>
<path d="M122 99L115 119L130 140L115 162L122 178" fill="none" stroke="#e6e8d7" stroke-width="4"/>
<text x="235" y="47" font-size="210" dominant-baseline="text-before-edge" fill="#e6e8d7" mask="url(#desgaste)">DEATH <tspan fill="#e2a65a">NIGHT</tspan></text>
<path d="M238 227H1118" stroke="#a1392e" stroke-width="5"/><path d="M1142 217l-8 19m26-19l-8 19m26-19l-8 19m26-19l-8 19" stroke="#e2a65a" stroke-width="4"/>
</svg>'''
    (EXPORT/'logo_editavel.svg').write_text(svg,encoding='utf-8')
    return img


def fundo(w,h):
    mapa=Image.open(ROOT/'assets/images/power21/bairro.png').convert('RGB')
    # O próprio bairro fornece a arte-base, sem capturas de HUD nem recursos externos.
    cena=mapa.crop((520,350,1480,1050)).resize((w,h),Image.Resampling.NEAREST).convert('RGBA')
    wash=Image.new('RGBA',(w,h),(8,20,27,105));cena=Image.alpha_composite(cena,wash)
    sombra=Image.new('RGBA',(w,h));p=sombra.load()
    for y in range(h):
        for x in range(w):
            vinheta=(abs(x-w*.48)/(w*.65))**2+(abs(y-h*.50)/(h*.8))**2
            alpha=min(225,int(42+100*vinheta+55*(1-x/w)))
            p[x,y]=(7,15,22,alpha)
    cena=Image.alpha_composite(cena,sombra)
    d=ImageDraw.Draw(cena)
    for i in range(4):
        x=int(w*.71)+i*19
        d.line((x,0,x-int(h*.35),h),fill=(78,66,48,50),width=3)
    return cena


def personagem(caminho,frames,escala):
    img=Image.open(ROOT/caminho).convert('RGBA')
    img=img.crop((0,0,img.width//frames,img.height))
    return img.resize((img.width*escala,img.height*escala),Image.Resampling.NEAREST)


def gerar():
    marca=logo()
    menu=fundo(960,640);menu.save(OUT/'fundo_menu.png')
    for nome,w,h in [('thumbnail',1920,1080),('capa',1260,1000)]:
        img=fundo(w,h)
        z=personagem('assets/images/zombies/big/down_walk.png',8,5 if w>1300 else 4)
        img.alpha_composite(z,(w-z.width-20,h-z.height-100))
        hero=personagem('assets/images/player/down_idle.png',6,7 if w>1300 else 5)
        img.alpha_composite(hero,(int(w*.64),h-hero.height-80))
        larg=int(w*.82)
        m=marca.resize((larg,int(larg*280/1280)),Image.Resampling.LANCZOS)
        img.alpha_composite(m,(int(w*.055),int(h*.14)))
        d=ImageDraw.Draw(img)
        d.text((int(w*.08),int(h*.48)),'A ENERGIA ACABOU. A NOITE NÃO.',font=fonte(int(w*.027)),fill=PAPEL)
        d.line((int(w*.08),int(h*.61),int(w*.44),int(h*.61)),fill=AMBAR,width=3)
        d.text((int(w*.08),int(h*.65)),'ENCONTRE OS FUSÍVEIS\nENFRENTE A HORDA\nABRA O PORTÃO',font=fonte(int(w*.028)),fill=AMBAR,spacing=8)
        d.text((int(w*.08),h-int(h*.10)),'SOBREVIVÊNCIA 2D  /  BAIRRO EM QUARENTENA',font=fonte(int(w*.017)),fill=PAPEL)
        img.convert('RGB').save(EXPORT/f'{nome}.png')
    print('Logotipo SVG/PNG, capa, thumbnail e fundo do menu gerados.')


if __name__=='__main__':gerar()
