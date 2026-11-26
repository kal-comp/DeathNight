"""Configurações de dificuldade do Death Night.

Cada nível ajusta: quantos zumbis nascem por onda, a velocidade e o dano
de contato deles, a munição inicial e a escassez dos suprimentos.
"""

DIFICULDADES = {
    "facil": {
        "nome": "Fácil",
        "multiplicador_zumbis": 0.7,
        "multiplicador_velocidade": 0.85,
        "multiplicador_dano": 0.7,
        "multiplicador_vida": 0.8,
        "ajuste_municao": 10,
        "chance_drop": .10,
        "intervalo_item": 18000,
        "intervalo_municao": 14000,
        "limite_itens": 3,
    },
    "normal": {
        "nome": "Normal",
        "multiplicador_zumbis": 1.0,
        "multiplicador_velocidade": 1.0,
        "multiplicador_dano": 1.0,
        "multiplicador_vida": 1.0,
        "ajuste_municao": 0,
        "chance_drop": .07,
        "intervalo_item": 24000,
        "intervalo_municao": 18000,
        "limite_itens": 2,
    },
    "dificil": {
        "nome": "Difícil",
        "multiplicador_zumbis": 1.4,
        "multiplicador_velocidade": 1.15,
        "multiplicador_dano": 1.3,
        "multiplicador_vida": 1.5,
        "ajuste_municao": -5,
        "chance_drop": .04,
        "intervalo_item": 30000,
        "intervalo_municao": 22000,
        "limite_itens": 2,
    },
}

ORDEM_DIFICULDADES = ["facil", "normal", "dificil"]

