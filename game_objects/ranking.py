"""Persistência simples do ranking (top pontuações) em um arquivo JSON
local. Não depende de servidor nem de internet — funciona offline."""
import json
import os

CAMINHO_RANKING = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "ranking.json")
MAX_ENTRADAS = 10


def carregar_ranking():
    if not os.path.exists(CAMINHO_RANKING):
        return []
    try:
        with open(CAMINHO_RANKING, "r", encoding="utf-8") as arquivo:
            return json.load(arquivo)
    except (json.JSONDecodeError, OSError):
        return []


def salvar_pontuacao(pontos, onda, nome_dificuldade):
    """Adiciona uma nova pontuação, reordena e mantém só o top 10."""
    ranking = carregar_ranking()
    ranking.append({"pontos": pontos, "onda": onda, "dificuldade": nome_dificuldade})
    ranking.sort(key=lambda entrada: entrada["pontos"], reverse=True)
    ranking = ranking[:MAX_ENTRADAS]

    os.makedirs(os.path.dirname(CAMINHO_RANKING), exist_ok=True)
    with open(CAMINHO_RANKING, "w", encoding="utf-8") as arquivo:
        json.dump(ranking, arquivo, ensure_ascii=False, indent=2)

    return ranking

