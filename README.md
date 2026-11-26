# Death Night

**Death Night** é um jogo de ação e sobrevivência em 2D desenvolvido em Python como projeto da disciplina **Laboratório de Programação de Jogos**, da **Universidade Federal Fluminense (UFF)**. Utiliza **Power PPlay 2.1**, com apoio do Pygame.

## Sobre o jogo

Preso em um bairro tomado por zumbis, o jogador precisa encontrar três fusíveis, instalá-los no painel elétrico e enfrentar o Guardião do Portão para abrir a saída. Enquanto explora as ruas, enfrenta ondas de inimigos, administra vida e munição e escolhe melhorias ao subir de nível.

O jogo possui:

- Uma fase com ruas, prédios, carros e obstáculos com colisão.
- Câmera acompanhando o personagem pelo bairro.
- Pistola e escopeta desbloqueável, com troca de arma durante a partida.
- XP por eliminações e três opções de melhoria a cada nível.
- Zumbis com diferentes características e um confronto final.
- Kits de vida, munição, adrenalina e disparo rápido temporário.
- Três dificuldades: Fácil, Normal e Difícil.
- Menus, pausa, opções de áudio, telas de vitória e derrota e recordes locais.

Cada nova tentativa começa no nível 1, com a pistola e os objetivos reiniciados.

## Controles

| Ação | Controle |
| --- | --- |
| Mover | WASD ou setas |
| Mirar | Mouse |
| Atirar | Botão esquerdo do mouse ou espaço |
| Trocar entre as armas desbloqueadas | Q |
| Coletar fusível ou instalar no painel | E, próximo ao objeto |
| Pausar ou voltar | Esc |
| Navegar pelos menus | Mouse, setas ou Tab |
| Confirmar uma opção | Enter ou clique |

Na escolha de melhorias, espaço não confirma a seleção. A tela aguarda a soltura do botão de disparo antes de aceitar uma nova escolha.

## Como executar

Requisitos: Python e Pygame. O projeto foi testado com Python 3.13 e Pygame 2.6.1. A biblioteca **PPlay** já está incluída no repositório.

Abra um terminal na pasta que contém `main.py` e execute:

```powershell
python -m pip install -r requirements.txt
python main.py
```

O jogo abre em uma janela de 960 × 640. Para preservar a aparência dos pixels, use o tamanho original da janela.

## Organização do projeto

```text
DeathNight/
├── PPlay/             # Biblioteca Power PPlay 2.1
├── assets/            # Imagens, fontes, músicas e efeitos sonoros
├── game_objects/      # Jogador, inimigos, cenário, missão e interface
├── data/              # Recordes e configurações locais
├── tests/             # Testes das mecânicas, animações e áudio
├── tools/             # Utilitários de desenvolvimento
├── main.py            # Inicialização e estados do jogo
├── requirements.txt   # Dependências
├── CREDITOS.txt       # Créditos e origem dos recursos
└── README.md
```

Os arquivos de recordes e configurações são criados quando necessários. Cada jogador mantém seus próprios dados na pasta `data/`.

## Testes

```powershell
python -m unittest discover -s tests
```

## Créditos e uso dos recursos

- Projeto e integração: **Kalebe Barreto**.
- Biblioteca: **Power PPlay 2.1**, distribuída pelo site da UFF; licença em [PPlay/LICENSE](PPlay/LICENSE).
- Sprites de terceiros: **TheLazyStone**, pacote [Post-Apocalypse Pixel Art](https://thelazystone.itch.io/post-apocalypse-pixel-art-asset-pack). As condições de uso estão em [assets/LICENSE_ASSETS.txt](assets/LICENSE_ASSETS.txt).
- Fonte **Bebas Neue**, da Dharma Type, com licença em [assets/fonts/OFL.txt](assets/fonts/OFL.txt).

Informações complementares sobre os recursos estão em [CREDITOS.txt](CREDITOS.txt). As licenças dos componentes e recursos de terceiros continuam aplicáveis ao projeto.
