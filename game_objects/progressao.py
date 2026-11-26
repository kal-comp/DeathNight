"""Catálogo das escolhas de nível; os efeitos pertencem ao jogador."""
import random
MELHORIAS = {
    'dano': ('MUNIÇÃO REFORÇADA', '+0,5 de dano por projétil', 'Mais força contra os chefes.', 3),
    'vida': ('RESISTÊNCIA', '+25 de vida máxima e cura', 'Mais espaço para sobreviver.', 3),
    'municao': ('SUPRIMENTOS', '+8 de capacidade e munição', 'Mais tempo no combate.', 3),
    'cadencia': ('CADÊNCIA DE TIRO', 'Reduz o intervalo em 12%', 'Afeta as duas armas.', 3),
    'velocidade': ('PASSOS LEVES', '+8% de velocidade base', 'Abra espaço entre a horda.', 3),
    'escopeta': ('ESCOPETA', '5 projéteis em leque', 'Desbloqueia e equipa. Q troca.', 1),
    'cura': ('PRIMEIROS SOCORROS', 'Recupera até 40 de vida', 'Recompensa imediata.', None),
    'reserva': ('RESERVA DE MUNIÇÃO', 'Reabastece toda a munição', 'Recompensa imediata.', None),
    'impulso': ('SEGUNDO FÔLEGO', 'Adrenalina e tiro rápido', 'Benefícios por 10 segundos.', None),
}


def opcoes_disponiveis(player):
    permanentes = [k for k, m in MELHORIAS.items()
                  if m[3] is not None and player.melhorias[k] < m[3]]
    # Três escolhas distintas continuam disponíveis depois dos limites.
    return permanentes + ['cura', 'reserva', 'impulso'][:max(0, 3-len(permanentes))]


def sortear_opcoes(player, fila):
    """Percorre as opções elegíveis antes de repetir; três escolhas distintas."""
    disponiveis = opcoes_disponiveis(player)
    fila[:] = [chave for chave in fila if chave in disponiveis]
    escolhas = []
    while len(escolhas) < 3:
        if not fila:
            restantes = [chave for chave in disponiveis if chave not in escolhas]
            fila.extend(random.sample(restantes, len(restantes)))
        chave = fila.pop(0)
        if chave not in escolhas:
            escolhas.append(chave)
    return escolhas
