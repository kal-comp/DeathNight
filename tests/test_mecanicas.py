"""Regressões das mecânicas. Execute: python -m unittest discover -s tests -v."""
import os
os.environ['SDL_VIDEODRIVER'] = 'dummy'
os.environ['SDL_AUDIODRIVER'] = 'dummy'

import math
import random
import unittest
from unittest.mock import patch
from pathlib import Path

import pygame
from main import Jogo
from game_objects.arena import AREA
from game_objects.colisao_utils import colidiu, mover_com_colisao
from game_objects.suprimento import Suprimento
from game_objects.zombie import ZumbiCaminhante, ZumbiChefe, ZumbiCorredor, ZumbiChefeFinal
from game_objects.projectile import Projetil
from game_objects.dificuldade import DIFICULDADES


class SemTeclas:
    def key_pressed(self, nome):
        return False


class Mecanicas(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.jogo = Jogo()
        cls.sem_teclas = SemTeclas()

    def setUp(self):
        random.seed(12)
        self.jogo.nova_partida()
        self.jogo.janela.eventos = []
        self.jogo.rodando = True
        self.p = self.jogo.partida
        self.player = self.p['player']

    def avancar(self, segundos, atirar=False, mira=(800, 300)):
        for _ in range(round(segundos*60)):
            self.jogo.atualizar(1/60, mira=mira, atirar=atirar, teclado=self.sem_teclas)

    def test_pausa_congela_tempo_itens_e_beneficios(self):
        self.player.adrenalina_ate = 6000
        self.player.rapido_ate = 8000
        item = self.p['itens'][0]
        self.jogo.mudar('pausa')
        self.avancar(20)
        self.assertEqual(self.p['tempo'], 0)
        self.assertFalse(item.expirou(self.p['tempo']))
        self.jogo.mudar('jogando')
        self.avancar(1)
        self.assertAlmostEqual(self.p['tempo'], 1000)
        self.assertGreater(self.player.adrenalina_ate, self.p['tempo'])

    def test_mansao_bloqueia_jogador(self):
        predio = self.jogo.arena.obstaculos[0]
        self.player.x, self.player.y = predio.x+80, predio.y+predio.height+1
        for _ in range(30):
            mover_com_colisao(self.player, 0, -8, self.jogo.arena.obstaculos)
        self.assertGreaterEqual(self.player.y, predio.y+predio.height)
        self.assertFalse(colidiu(self.player, self.jogo.arena.obstaculos[0]))

    def test_mansao_bloqueia_tiro(self):
        predio = self.jogo.arena.obstaculos[0]
        self.p['projeteis'] = [Projetil(predio.x+80,predio.y+predio.height+30,(0,-1))]
        self.avancar(.3)
        self.assertEqual(len(self.p['projeteis']), 0)

    def test_tiro_atinge_um_inimigo_e_pontua(self):
        z = ZumbiCaminhante(550, 280)
        z.velocidade = 0
        z.vida = 1
        self.p['zumbis'] = [z]
        self.p['projeteis'] = [Projetil(535, 280+z.height/2, (1, 0))]
        self.avancar(.1)
        self.assertEqual(self.p['pontos'], z.PONTOS)
        self.assertFalse(z.ativo)
        self.assertEqual(self.player.xp, z.XP)
        self.assertEqual(len(self.p['projeteis']), 0)

    def test_spawns_de_itens_validos(self):
        for _ in range(600):
            posicao = self.jogo.arena.posicao_livre(22, 22)
            self.assertIsNotNone(posicao)
            self.assertTrue(self.jogo.arena.livre(pygame.Rect(*posicao, 22, 22)))

    def test_entradas_comportam_todos_os_inimigos(self):
        for classe in (ZumbiCaminhante, ZumbiCorredor, ZumbiChefe):
            z = classe(0, 0)
            for _ in range(80):
                posicao = self.jogo.arena.spawn()
                self.assertTrue(self.jogo.arena.livre(pygame.Rect(*posicao, z.width, z.height)))

    def test_cura_e_municao_nao_desperdicadas(self):
        for tipo in ('cura', 'municao'):
            item = Suprimento(tipo, 0, 0, 0)
            self.assertFalse(item.aplicar(self.player, 100))
            self.assertTrue(item.ativo)
        self.player.vida = 90
        item = Suprimento('cura', 0, 0, 0)
        self.assertTrue(item.aplicar(self.player, 0))
        self.assertEqual(self.player.vida, 100)

    def test_beneficios_expiram_e_coleta_renova_sem_acumular(self):
        Suprimento('adrenalina', 0, 0, 0).aplicar(self.player, 100)
        self.assertEqual(self.player.adrenalina_ate, 6100)
        Suprimento('adrenalina', 0, 0, 0).aplicar(self.player, 200)
        self.assertEqual(self.player.adrenalina_ate, 6200)
        Suprimento('rapido', 0, 0, 0).aplicar(self.player, 0)
        self.player.tempo_ultimo_tiro = 0
        self.assertTrue(self.player.pode_atirar(180))
        self.player.tempo_ultimo_tiro = 7990
        self.assertFalse(self.player.pode_atirar(8190))

    def test_melhorias_limite_e_reinicio(self):
        for tipo in ('dano', 'vida', 'municao'):
            for _ in range(3):
                self.assertTrue(self.player.melhorar(tipo))
            self.assertFalse(self.player.melhorar(tipo))
        self.assertEqual(self.player.vida_maxima, 175)
        self.assertEqual(self.player.municao_maxima, 64)
        self.assertEqual(self.player.atirar(100).dano, 2.5)
        self.jogo.nova_partida()
        self.assertEqual(self.jogo.partida['player'].dano_tiro, 1)

    def test_xp_excedente_e_escolhas_em_sequencia(self):
        self.player.ganhar_xp(115)  # 40 + 60: dois níveis e 15 restantes.
        self.avancar(.1)
        self.assertEqual((self.player.nivel, self.player.xp), (3, 15))
        self.assertEqual(self.jogo.estado, 'melhoria')
        tempo = self.p['tempo']
        escolhas = self.p['opcoes_melhoria'][:]
        self.avancar(10)
        self.assertEqual(self.p['tempo'], tempo)
        self.assertEqual(self.p['opcoes_melhoria'], escolhas)
        self.assertEqual(len(set(escolhas)), 3)
        for _ in range(2):
            self.jogo.agir('melhorar:'+self.p['opcoes_melhoria'][0])
        self.assertEqual(self.player.escolhas_pendentes, 0)
        self.assertEqual(self.jogo.estado, 'jogando')

    def test_ondas_nao_concedem_melhoria(self):
        self.p['gerenciador'].onda_atual = 3
        self.avancar(3.2)
        self.assertEqual(self.jogo.estado, 'jogando')
        self.assertEqual(self.player.nivel, 1)
        self.assertEqual(self.p['gerenciador'].onda_atual, 4)

    def test_primeiras_duas_escolhas_oferecem_cadencia_e_escopeta(self):
        for semente in range(30):
            random.seed(semente)
            self.jogo.nova_partida()
            p = self.jogo.partida
            p['player'].ganhar_xp(100)
            self.jogo.abrir_melhoria()
            primeira = p['opcoes_melhoria'][:]
            self.jogo.agir('melhorar:'+primeira[0])
            segunda = p['opcoes_melhoria'][:]
            self.assertEqual(len(set(primeira+segunda)), 6)
            self.assertIn('cadencia', primeira+segunda)
            self.assertIn('escopeta', primeira+segunda)

    def test_ciclo_de_itens_inclui_ambos_beneficios_sem_aumentar_drops(self):
        for semente in range(20):
            random.seed(semente)
            self.jogo.nova_partida()
            p = self.jogo.partida
            tipos = []
            for _ in range(10):
                p['itens'].clear()
                self.jogo.gerar_item()
                self.assertEqual(len(p['itens']), 1)
                tipos.append(p['itens'][0].tipo)
            self.assertEqual({tipos[2], tipos[5]}, {'adrenalina', 'rapido'})
            self.assertEqual(tipos.count('municao'), 5)
            self.assertEqual(tipos.count('cura'), 3)

    def test_filas_de_sorteios_reiniciam_e_cota_cheia_nao_consume_beneficio(self):
        self.p['fila_suprimentos'] = ['adrenalina']
        self.p['itens'] = [Suprimento('cura', 0, 0, 0), Suprimento('rapido', 0, 0, 0)]
        self.jogo.gerar_item()
        self.assertEqual(self.p['fila_suprimentos'], ['adrenalina'])
        self.p['itens'].clear()
        self.jogo.gerar_item()
        self.assertEqual(self.p['itens'][0].tipo, 'adrenalina')
        self.jogo.nova_partida()
        self.assertFalse(self.jogo.partida['fila_melhorias'])
        self.assertFalse(self.jogo.partida['fila_suprimentos'])

    def test_limites_e_recompensas_alternativas(self):
        from game_objects.progressao import MELHORIAS
        for chave in self.player.melhorias:
            for _ in range(MELHORIAS[chave][3]):
                self.assertTrue(self.player.melhorar(chave))
        self.player.ganhar_xp(40)
        self.avancar(.1)
        self.assertEqual(set(self.p['opcoes_melhoria']), {'cura', 'reserva', 'impulso'})
        self.jogo.agir('melhorar:reserva')
        self.assertEqual(self.jogo.estado, 'jogando')

    def test_escopeta_leque_municao_alcance_e_troca(self):
        self.assertEqual(self.player.arma, 'pistola')
        self.player.trocar_arma()
        self.assertEqual(self.player.arma, 'pistola')
        self.assertTrue(self.player.melhorar('escopeta'))
        municao = self.player.municao
        tiros = self.player.disparar(0)
        self.assertEqual(len(tiros), 5)
        self.assertEqual(self.player.municao, municao-1)
        self.assertEqual(len({t.direcao for t in tiros}), 5)
        self.assertEqual(self.player.disparar(100), [])
        for tiro in tiros:
            self.assertAlmostEqual(math.hypot(*tiro.direcao), 1)
            tiro.atualizar(.7)
            self.assertFalse(tiro.ativo)
        self.player.trocar_arma()
        self.assertEqual(self.player.arma, 'pistola')
        self.assertEqual(len(self.player.disparar(1000)), 1)
        self.assertFalse(self.player.melhorar('escopeta'))

    def test_cadencia_e_velocidade(self):
        self.player.melhorar('cadencia')
        self.player.melhorar('velocidade')
        self.assertAlmostEqual(self.player.cooldown_tiro, 308)
        self.assertAlmostEqual(self.player.velocidade, 237.6)
        self.player.tempo_ultimo_tiro = 0
        self.assertFalse(self.player.pode_atirar(300))
        self.assertTrue(self.player.pode_atirar(310))

    def test_zumbis_resistem_e_melhoria_de_dano_reduz_tiros(self):
        z=ZumbiCaminhante(550,280)
        z.levar_dano(self.player.dano_tiro)
        self.assertTrue(z.ativo)
        self.assertEqual(z.vida,2)
        self.player.melhorar('dano')
        melhorado=ZumbiCaminhante(550,280)
        melhorado.levar_dano(self.player.dano_tiro)
        self.assertTrue(melhorado.ativo)
        melhorado.levar_dano(self.player.dano_tiro)
        self.assertFalse(melhorado.ativo)
        corredor=ZumbiCorredor(550,280)
        corredor.levar_dano(1)
        self.assertTrue(corredor.ativo)

    def test_dificuldade_aumenta_vida_quantidade_e_ritmo(self):
        from game_objects.wave_manager import GerenciadorDeOndas
        g=GerenciadorDeOndas(lambda:(440,500),'normal')
        h=GerenciadorDeOndas(lambda:(440,500),'dificil')
        self.assertEqual(g._zumbis_da_onda(1),16)
        self.assertGreater(h._zumbis_da_onda(1),g._zumbis_da_onda(1))
        self.assertLess(h._intervalo_spawn_da_onda(1),g._intervalo_spawn_da_onda(1))
        g.iniciar_proxima_onda(0);h.iniciar_proxima_onda(0)
        normal=g.atualizar(1000,0);dificil=h.atualizar(1000,0)
        self.assertGreater(dificil.vida,normal.vida)
        self.assertGreater(normal.vida,1)
        g.iniciar_proxima_onda(6_000)
        proximo=g.atualizar(8_000,0)
        self.assertGreater(proximo.vida,normal.vida)
        pendentes=h.zumbis_restantes_para_spawnar
        self.assertIsNone(h.atualizar(5000,60))
        self.assertEqual(h.zumbis_restantes_para_spawnar,pendentes)

    def test_escopeta_credita_xp_uma_vez_por_zumbi(self):
        z = ZumbiCaminhante(550, 280)
        z.velocidade = 0
        z.vida = 1
        self.p['zumbis'] = [z]
        self.p['projeteis'] = [Projetil(535, 280+z.height/2, (1, 0)) for _ in range(5)]
        self.avancar(.1)
        self.assertEqual(self.p['pontos'], z.PONTOS)
        self.assertEqual(self.player.xp, z.XP)

    def test_eliminacao_abre_nivel_durante_onda(self):
        self.player.ganhar_xp(30)
        z = ZumbiCaminhante(550, 280)
        z.velocidade = 0
        z.vida = 1
        self.p['zumbis'] = [z, ZumbiCaminhante(50, 230)]
        self.p['projeteis'] = [Projetil(535, 280+z.height/2, (1, 0))]
        self.avancar(.1)
        self.assertEqual(self.jogo.estado, 'melhoria')
        self.assertEqual(self.player.nivel, 2)
        self.assertEqual(len(self.p['zumbis']), 1)

    def test_morte_tem_prioridade_e_reinicio_limpa_progressao(self):
        self.player.ganhar_xp(100)
        self.player.melhorar('escopeta')
        self.player.melhorar('cadencia')
        self.player.vida = 0
        with patch('main.salvar_pontuacao', return_value=[]):
            self.avancar(.1)
        self.assertEqual(self.jogo.estado, 'fim')
        self.jogo.agir('iniciar')
        player = self.jogo.partida['player']
        self.assertEqual((player.nivel, player.xp, player.escolhas_pendentes), (1, 0, 0))
        self.assertEqual(player.arma, 'pistola')
        self.assertEqual(player.cooldown_tiro, 350)
        self.assertTrue(all(n == 0 for n in player.melhorias.values()))
        self.assertEqual(self.jogo.partida['opcoes_melhoria'], [])

    def test_escolha_invalida_nao_aplica_e_recompensa_nao_duplica(self):
        self.player.ganhar_xp(40)
        self.avancar(.1)
        self.jogo.agir('melhorar:inexistente')
        self.assertEqual(self.player.escolhas_pendentes, 1)
        acao = 'melhorar:'+self.p['opcoes_melhoria'][0]
        self.jogo.agir(acao)
        valores = self.player.melhorias.copy()
        self.jogo.agir(acao)
        self.assertEqual(valores, self.player.melhorias)

    def test_melhoria_nao_aceita_tiro_durante_transicao(self):
        with patch.object(self.jogo.janela, 'time_elapsed', return_value=1000) as relogio:
            self.player.ganhar_xp(40)
            self.jogo.abrir_melhoria()
            posicao = self.jogo.botoes()[0][0].center
            clique = pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=posicao)
            with patch.object(self.jogo.controle_mouse, 'get_position', return_value=posicao), \
                 patch.object(self.jogo.controle_mouse, 'button_pressed', return_value=True) as segurado:
                relogio.return_value = 1200
                self.jogo.eventos([clique])  # Clique dentro dos 350 ms.
                self.assertEqual(self.player.escolhas_pendentes, 1)
                relogio.return_value = 2500
                self.jogo.eventos([clique])  # Continuar segurando não libera.
                self.assertEqual(self.player.escolhas_pendentes, 1)
                segurado.return_value = False
                self.jogo.eventos([])  # Soltou: apenas arma a confirmação.
                self.assertEqual(self.player.escolhas_pendentes, 1)
                self.jogo.eventos([clique])  # Novo clique intencional.
                self.assertEqual(self.player.escolhas_pendentes, 0)
                self.assertEqual(self.jogo.estado, 'jogando')

    def test_espaco_nao_confirma_melhoria_enter_precisa_ser_solto(self):
        with patch.object(self.jogo.janela, 'time_elapsed', return_value=1000) as relogio:
            self.player.ganhar_xp(40)
            self.jogo.abrir_melhoria()
            relogio.return_value = 1500
            enter = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN)
            for _ in range(3):
                self.jogo.eventos([enter])  # Repetição de Enter durante a entrada.
            self.assertEqual(self.player.escolhas_pendentes, 1)
            self.jogo.eventos([])
            self.jogo.eventos([pygame.event.Event(pygame.KEYDOWN, key=pygame.K_SPACE)])
            self.assertEqual(self.player.escolhas_pendentes, 1)
            self.jogo.eventos([enter])
            self.assertEqual(self.player.escolhas_pendentes, 0)

    def test_melhorias_em_sequencia_exigem_nova_confirmacao(self):
        with patch.object(self.jogo.janela, 'time_elapsed', return_value=1000) as relogio:
            self.player.ganhar_xp(100)
            self.jogo.abrir_melhoria()
            relogio.return_value = 1400
            self.jogo.eventos([])
            enter = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN)
            self.jogo.eventos([enter])
            self.assertEqual(self.player.escolhas_pendentes, 1)
            self.jogo.eventos([enter])
            self.assertEqual(self.player.escolhas_pendentes, 1)
            relogio.return_value = 1800
            self.jogo.eventos([])
            self.jogo.eventos([enter])
            self.assertEqual(self.player.escolhas_pendentes, 0)
            self.assertEqual(self.jogo.estado, 'jogando')

    def test_inimigos_contornam_barreira(self):
        for classe in (ZumbiCaminhante, ZumbiCorredor, ZumbiChefe):
            self.jogo.nova_partida()
            self.p = self.jogo.partida
            player = self.p['player']
            player.x, player.y = 930, 520
            z = classe(650, 520)
            self.p['zumbis'] = [z]
            for _ in range(900):
                self.jogo.atualizar(1/60, teclado=self.sem_teclas)
                self.assertFalse(any(colidiu(z, o) for o in self.jogo.arena.obstaculos))
                if z.x > 875:
                    break
            self.assertGreater(z.x, 875, classe.__name__)

    def test_mira_independente_do_movimento(self):
        class Esquerda:
            def key_pressed(self, nome):
                return nome == 'A'
        x = self.player.x
        self.jogo.atualizar(.02, mira=(900, 320), atirar=True, teclado=Esquerda())
        self.assertLess(self.player.x, x)
        self.assertGreater(self.p['projeteis'][0].direcao[0], .9)

    def test_reposicao_mais_rapida_sem_municao_em_cada_dificuldade(self):
        for dificuldade in ('facil', 'normal', 'dificil'):
            with self.subTest(dificuldade=dificuldade):
                self.jogo.dificuldade = dificuldade
                self.jogo.nova_partida()
                p = self.jogo.partida
                p['player'].municao = 0
                p['itens'].clear()
                intervalo = DIFICULDADES[dificuldade]['intervalo_municao']/2
                self.assertLess(intervalo, DIFICULDADES[dificuldade]['intervalo_item'])
                p['tempo'] = intervalo-100
                self.jogo.atualizar(.04, teclado=self.sem_teclas)
                self.assertEqual(p['itens'], [])  # Nem a primeira onda dá caixa grátis.
                p['tempo'] = intervalo
                self.jogo.atualizar(.01, teclado=self.sem_teclas)
                self.assertEqual([i.tipo for i in p['itens']], ['municao'])
        self.jogo.dificuldade = 'normal'

    def test_reforco_so_com_reserva_baixa_sem_consumir_fila_de_beneficios(self):
        self.p['itens'].clear()
        self.p['fila_suprimentos'] = ['adrenalina', 'rapido']
        intervalo = DIFICULDADES[self.jogo.dificuldade]['intervalo_municao']
        self.p['tempo'] = intervalo
        self.player.municao = self.player.municao_maxima//2
        self.jogo.atualizar(.01, teclado=self.sem_teclas)
        self.assertFalse(self.p['itens'])
        self.player.municao = self.player.municao_maxima//4
        self.jogo.atualizar(.01, teclado=self.sem_teclas)
        self.assertEqual([i.tipo for i in self.p['itens']], ['municao'])
        self.assertEqual(self.p['fila_suprimentos'], ['adrenalina', 'rapido'])
        for _ in range(10):
            self.jogo.atualizar(.01, teclado=self.sem_teclas)
        self.assertEqual(len(self.p['itens']), 1)

    def test_reforco_bloqueado_pela_cota_tenta_novamente_sem_nova_espera(self):
        self.p['itens'].clear()
        self.p['tempo'] = DIFICULDADES[self.jogo.dificuldade]['intervalo_municao']
        self.player.municao = 1
        for _ in range(DIFICULDADES[self.jogo.dificuldade]['limite_itens']):
            self.assertTrue(self.jogo.gerar_item('cura'))
        self.jogo.atualizar(.01, teclado=self.sem_teclas)
        self.assertEqual(self.p['ultimo_reforco_municao'], 0)
        self.p['itens'].pop()
        self.jogo.atualizar(.01, teclado=self.sem_teclas)
        self.assertIn('municao', [i.tipo for i in self.p['itens']])
        self.assertGreater(self.p['ultimo_reforco_municao'], 0)

    def test_municao_de_reposicao_aparece_mais_perto_do_jogador(self):
        self.p['itens'].clear()
        for semente in range(10):
            random.seed(semente)
            self.assertTrue(self.jogo.gerar_item('municao'))
            item = self.p['itens'].pop()
            self.assertLessEqual(abs(item.x-self.player.x), 160)
            self.assertLessEqual(abs(item.y-self.player.y), 160)
            self.assertTrue(self.jogo.arena.livre(pygame.Rect(item.x, item.y, 22, 22)))

    def test_suprimentos_limitados_sem_acumular_municao(self):
        self.p['itens'].clear()
        for _ in range(8):
            self.jogo.gerar_item('municao')
        self.assertEqual(len(self.p['itens']), 1)
        for _ in range(8):
            self.jogo.gerar_item('cura')
        self.assertEqual(len(self.p['itens']), 2)
        self.p['tempo'] = 14001
        self.jogo.gerar_item('rapido')
        self.assertEqual([i.tipo for i in self.p['itens']], ['rapido'])

    def test_drop_raro_no_combate_e_menor_no_dificil(self):
        for dificuldade, sorteio, esperado in [('facil', .08, 1), ('normal', .08, 0),
                                               ('normal', .05, 1), ('dificil', .05, 0),
                                               ('dificil', .02, 1), ('facil', .20, 0)]:
            with self.subTest(dificuldade=dificuldade, sorteio=sorteio):
                self.jogo.dificuldade = dificuldade
                self.jogo.nova_partida()
                p = self.jogo.partida
                p['itens'].clear()
                z = ZumbiCaminhante(550, 280)
                z.vida = 1
                z.velocidade = 0
                p['zumbis'] = [z]
                p['projeteis'] = [Projetil(535, 280+z.height/2, (1, 0))]
                with patch('main.random.random', return_value=sorteio):
                    self.avancar(.1)
                self.assertFalse(z.ativo)
                self.assertEqual(len(p['itens']), esperado)
        self.jogo.dificuldade = 'normal'

    def test_morte_salva_ranking_uma_vez(self):
        with patch('main.salvar_pontuacao', return_value=[]) as salvar:
            self.player.vida = 0
            self.avancar(1)
            self.assertEqual(self.jogo.estado, 'fim')
            salvar.assert_called_once()

    def test_navegacao_e_pausa_por_teclado(self):
        self.jogo.mudar('menu')
        enter = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN)
        self.jogo.eventos([enter])
        self.assertEqual(self.jogo.estado, 'preparar')
        self.jogo.foco = 3
        self.jogo.eventos([enter])
        self.assertEqual(self.jogo.estado, 'jogando')
        self.jogo.eventos([pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE)])
        self.assertEqual(self.jogo.estado, 'pausa')
        self.jogo.eventos([enter])
        self.assertEqual(self.jogo.estado, 'jogando')

    def test_telas_renderizam(self):
        Path('output/previews').mkdir(parents=True, exist_ok=True)
        for estado in ('menu', 'preparar', 'jogando', 'pausa', 'opcoes', 'ranking', 'melhoria', 'fim', 'vitoria'):
            if estado == 'melhoria':
                self.player.ganhar_xp(40)
                self.jogo.abrir_melhoria()
            else:
                if estado == 'vitoria':
                    missao = self.p['missao']
                    for f in missao.fusiveis:
                        f['coletado'] = True
                    self.perto_de(missao.painel)
                    missao.interagir(self.player)
                    missao.chefe = ZumbiChefeFinal(1336,1000)
                    missao.chefe.levar_dano(missao.chefe.vida)
                    missao.liberar_portao()
                self.jogo.mudar(estado)
            self.jogo.desenhar()
            pygame.image.save(self.jogo.tela, f'output/previews/{estado}.png')

    def perto_de(self, posicao):
        self.player.x = posicao[0]-self.player.width/2
        self.player.y = posicao[1]-self.player.height/2

    def coletar_fusiveis(self):
        missao = self.p['missao']
        for posicao in missao.POSICOES:
            self.perto_de(posicao)
            self.jogo.atualizar(1/60, teclado=self.sem_teclas, interagir=True)
        self.assertEqual(missao.quantidade, 3)

    def derrotar_chefe(self):
        chefe = self.p['missao'].chefe
        self.assertIsInstance(chefe,ZumbiChefeFinal)
        chefe.velocidade_base = 0
        tiro = Projetil(chefe.x+chefe.width/2,chefe.y+chefe.height/2,(1,0))
        tiro.dano = chefe.vida
        self.p['projeteis'].append(tiro)
        self.jogo.atualizar(1/60,teclado=self.sem_teclas)
        while self.jogo.estado == 'melhoria':
            self.jogo.agir('melhorar:'+self.p['opcoes_melhoria'][0])
        self.assertFalse(chefe.ativo)
        self.assertTrue(self.p['missao'].aberto)

    def test_fusiveis_precisam_proximidade_e_interacao(self):
        missao = self.p['missao']
        self.jogo.atualizar(1/60, teclado=self.sem_teclas, interagir=True)
        self.assertEqual(missao.quantidade, 0)
        self.perto_de(missao.POSICOES[0])
        self.avancar(.1)
        self.assertEqual(missao.quantidade, 0)
        self.jogo.eventos([pygame.event.Event(pygame.KEYDOWN, key=pygame.K_e)])
        self.jogo.atualizar(1/60, teclado=self.sem_teclas)
        self.assertEqual(missao.quantidade, 1)
        self.jogo.atualizar(1/60, teclado=self.sem_teclas, interagir=True)
        self.assertEqual(missao.quantidade, 1)

    def test_portao_fechado_bloqueia_movimento_e_tiro(self):
        portao = self.p['missao'].portao
        self.player.x, self.player.y = self.p['missao'].portao.x+26, self.p['missao'].portao.y-self.player.height-4
        mover_com_colisao(self.player, 0, 10, self.jogo.arena.obstaculos)
        self.assertEqual(self.player.y, portao.y-self.player.height-4)
        self.p['projeteis'] = [Projetil(portao.x+56,portao.y-13,(0,1))]
        self.avancar(.1)
        self.assertEqual(len(self.p['projeteis']), 0)
        self.assertTrue(portao.bloqueia_movimento)

    def test_portao_aberto_permite_projeteis_atravessarem_o_vao(self):
        portao = self.p['missao'].portao
        portao.bloqueia_tiro = False
        portao.bloqueia_movimento = False
        tiro = Projetil(portao.x+56, portao.y-13, (0, 1))
        self.p['projeteis'] = [tiro]
        self.avancar(.1)
        self.assertTrue(tiro.ativo)
        self.assertGreater(tiro.y, portao.y+portao.height)

    def test_cano_da_escopeta_nao_cria_tiro_do_outro_lado_da_parede(self):
        from game_objects.arena import Bloco
        self.player.melhorar('escopeta')
        self.player.direcao_atual = (1, 0)
        bloco = Bloco((self.player.x+self.player.width+2, self.player.y-20, 24, 110))
        self.jogo.arena.obstaculos.append(bloco)
        tiros = self.player.disparar(0, self.jogo.arena.obstaculos)
        corpo = (self.player.x+self.player.width/2, self.player.y+self.player.height/2)
        self.assertEqual(self.player.origem_ultimo_tiro, corpo)
        self.p['projeteis'] = tiros
        self.avancar(.1)
        self.assertFalse(self.p['projeteis'])

    def test_painel_so_abre_com_tres_e_nao_vence_ao_instalar(self):
        missao = self.p['missao']
        self.perto_de(missao.painel)
        self.jogo.atualizar(1/60, teclado=self.sem_teclas, interagir=True)
        self.assertFalse(missao.aberto)
        self.coletar_fusiveis()
        self.assertFalse(missao.aberto)
        self.perto_de(missao.painel)
        self.jogo.atualizar(1/60, teclado=self.sem_teclas, interagir=True)
        self.assertFalse(missao.aberto)
        self.assertIsInstance(missao.chefe,ZumbiChefeFinal)
        self.derrotar_chefe()
        self.assertTrue(missao.aberto)
        self.assertEqual(self.jogo.estado, 'jogando')
        self.assertFalse(missao.portao.bloqueia_tiro)
        self.player.x, self.player.y = self.p['missao'].portao.x+26, self.p['missao'].portao.y-self.player.height-4
        mover_com_colisao(self.player, 0, 10, self.jogo.arena.obstaculos)
        self.assertEqual(self.player.y, missao.portao.y-self.player.height+6)
        a=(missao.portao.x+26,missao.portao.y-self.player.height-4)
        b=(a[0],a[1]+40)
        self.assertEqual(self.jogo.arena.rota(a,b,self.player.width,self.player.height),[b])

    def test_vitoria_congela_partida_salva_uma_vez_e_reinicia(self):
        self.coletar_fusiveis()
        missao = self.p['missao']
        self.perto_de(missao.painel)
        self.jogo.atualizar(1/60, teclado=self.sem_teclas, interagir=True)
        self.derrotar_chefe()
        self.player.melhorar('escopeta')
        self.player.ganhar_xp(30)
        portao = self.p['missao'].portao
        self.player.x, self.player.y = portao.x+26,portao.y+52-self.player.height
        with patch('main.salvar_pontuacao', return_value=[]) as salvar:
            self.avancar(.1)
            self.assertEqual(self.jogo.estado, 'vitoria')
            tempo = self.p['tempo']
            self.avancar(2)
            self.assertEqual(self.p['tempo'], tempo)
            salvar.assert_called_once()
        self.jogo.agir('iniciar')
        nova = self.jogo.partida
        self.assertFalse(nova['missao'].aberto)
        self.assertEqual(nova['missao'].quantidade, 0)
        self.assertEqual(nova['player'].nivel, 1)
        self.assertEqual(nova['player'].xp, 0)
        self.assertEqual(nova['player'].arma, 'pistola')
        self.assertTrue(nova['missao'].portao.bloqueia_movimento)

    def test_missao_pausada_e_morte_tem_prioridade(self):
        self.perto_de(self.p['missao'].POSICOES[0])
        self.jogo.mudar('pausa')
        self.jogo.atualizar(.02, interagir=True)
        self.assertEqual(self.p['missao'].quantidade, 0)

        self.jogo.mudar('jogando')
        self.player.vida = 0
        with patch('main.salvar_pontuacao', return_value=[]):
            self.jogo.atualizar(.02, teclado=self.sem_teclas, interagir=True)
        self.assertEqual(self.jogo.estado, 'fim')
        self.assertEqual(self.p['missao'].quantidade, 0)

    def test_saida_fechada_nao_permite_vitoria(self):
        portao = self.p['missao'].portao
        self.player.x, self.player.y = portao.x+26,portao.y+52-self.player.height
        self.avancar(.1)
        self.assertEqual(self.jogo.estado, 'jogando')
        self.assertFalse(self.p['missao'].escapou(self.player))

    def test_um_ou_dois_fusiveis_nao_abrem_portao(self):
        missao = self.p['missao']
        for i in range(2):
            self.perto_de(missao.POSICOES[i])
            self.jogo.atualizar(1/60, teclado=self.sem_teclas, interagir=True)
            self.perto_de(missao.painel)
            self.jogo.atualizar(1/60, teclado=self.sem_teclas, interagir=True)
            self.assertEqual(missao.quantidade, i+1)
            self.assertFalse(missao.aberto)
            self.assertTrue(missao.portao.bloqueia_movimento)

    def iniciar_chefe(self):
        self.coletar_fusiveis()
        self.perto_de(self.p['missao'].painel)
        self.jogo.atualizar(1/60,teclado=self.sem_teclas,interagir=True)
        return self.p['missao'].chefe

    def test_chefe_final_unico_painel_repetido_e_spawn_seguro(self):
        chefe = self.iniciar_chefe()
        missao = self.p['missao']
        self.assertTrue(missao.instalados)
        self.assertFalse(missao.aberto)
        self.assertTrue(missao.portao.bloqueia_movimento)
        self.assertTrue(self.jogo.arena.livre(pygame.Rect(chefe.x,chefe.y,chefe.width,chefe.height)))
        self.assertGreaterEqual(math.dist((chefe.x,chefe.y),(self.player.x,self.player.y)),180)
        for _ in range(5):
            self.jogo.atualizar(1/60,teclado=self.sem_teclas,interagir=True)
        self.assertEqual(sum(isinstance(z,ZumbiChefeFinal) for z in self.p['zumbis']),1)
        self.assertIs(missao.chefe,chefe)
        self.assertFalse(missao.liberar_portao())

    def test_chefe_de_onda_nao_abre_portao(self):
        chefe = self.iniciar_chefe()
        comum = ZumbiChefe(100,500)
        comum.levar_dano(comum.vida)
        self.p['zumbis'].append(comum)
        self.avancar(.02)
        self.assertTrue(chefe.ativo)
        self.assertFalse(self.p['missao'].aberto)

    def test_final_pausa_ondas_preserva_inimigos_e_xp(self):
        chefe = self.iniciar_chefe()
        zumbi = ZumbiCaminhante(900,1010)
        self.p['zumbis'].append(zumbi)
        with patch.object(self.p['gerenciador'],'atualizar') as atualizar:
            self.avancar(.1)
            atualizar.assert_not_called()
        self.assertIn(zumbi,self.p['zumbis'])
        self.jogo.mudar('pausa')
        posicao=(chefe.x,chefe.y,chefe.vida)
        self.avancar(3)
        self.assertEqual((chefe.x,chefe.y,chefe.vida),posicao)
        self.jogo.mudar('jogando')
        self.derrotar_chefe()
        self.assertEqual(self.p['pontos'],chefe.PONTOS)
        self.assertEqual(self.p['eliminacoes'],1)
        self.assertEqual((self.player.nivel,self.player.xp),(3,20))
        self.assertEqual(self.player.escolhas_pendentes,0)

    def test_furia_e_morte_no_combate_reinicia_missao(self):
        chefe=self.iniciar_chefe()
        chefe.levar_dano(chefe.vida_maxima/2)
        self.avancar(.02)
        self.assertTrue(chefe.enfurecido)
        self.assertAlmostEqual(chefe.velocidade,chefe.velocidade_base*1.3)
        self.player.vida=0
        with patch('main.salvar_pontuacao',return_value=[]):
            self.avancar(.02)
        self.assertEqual(self.jogo.estado,'fim')
        self.assertFalse(self.p['missao'].aberto)
        self.jogo.agir('iniciar')
        missao=self.jogo.partida['missao']
        self.assertFalse(missao.instalados)
        self.assertFalse(missao.chefe_derrotado)
        self.assertIsNone(missao.chefe)
        self.assertFalse(missao.aberto)

    def test_escopeta_derrota_chefe_e_libera_portao(self):
        chefe=self.iniciar_chefe()
        chefe.velocidade_base=0
        self.player.x,self.player.y=chefe.x-120,chefe.y+14
        self.player.melhorar('escopeta')
        self.player.municao=100
        for _ in range(1000):
            if not chefe.ativo:
                break
            mira=(chefe.x+chefe.width/2-self.jogo.camera.x,
                  chefe.y+chefe.height/2-self.jogo.camera.y)
            self.jogo.atualizar(1/60,mira=mira,atirar=True,teclado=self.sem_teclas)
        self.assertFalse(chefe.ativo)
        self.assertTrue(self.p['missao'].aberto)
        self.assertEqual(self.p['pontos'],chefe.PONTOS)
        self.assertLess(self.player.municao,100)

    def test_objetivos_tem_acesso_sem_colisao(self):
        missao = self.p['missao']
        inicio = (self.player.x, self.player.y)
        for posicao in (*missao.POSICOES, missao.painel):
            self.perto_de(posicao)
            rect = pygame.Rect(self.player.x, self.player.y, self.player.width, self.player.height)
            self.assertTrue(AREA.contains(rect))
            self.assertFalse(any(colidiu(self.player, o) for o in self.jogo.arena.obstaculos))
            self.assertTrue(self.jogo.arena.rota(inicio, (self.player.x,self.player.y), self.player.width,self.player.height))

    def test_biblioteca_oficial_e_audio_pplay(self):
        from PPlay.window import Window
        from PPlay.sound import Sound
        from PPlay.gameimage import GameImage
        self.assertIsInstance(self.jogo.janela, Window)
        self.assertIsInstance(self.jogo.arena.fundo, GameImage)
        self.assertTrue(self.jogo.audio.sons)
        self.assertTrue(all(isinstance(s, Sound) for s in self.jogo.audio.sons.values()))
        self.assertEqual(self.player._sprite_ativo().total_frames, 6)

    def test_sem_audio_importado_nao_carrega_trilha_sintetica(self):
        from game_objects.audio import Audio
        with patch('game_objects.audio.Path.is_file', return_value=False), \
             patch('game_objects.audio.Music') as carregar:
            audio = Audio()
            audio.contexto('menu')
            audio.contexto('jogando')
            self.assertIsNone(audio.musica)
            carregar.assert_not_called()
        self.jogo.audio.ajustar_volume(self.jogo.audio.volume)

    def test_audio_importado_substitui_pistola_e_habilita_musica(self):
        from game_objects.audio import Audio
        with patch('game_objects.audio.Path.is_file', lambda p: p.name in ('pistola.wav', 'musica.mp3')), \
             patch('game_objects.audio.Sound') as carregar_som, \
             patch('game_objects.audio.Music') as carregar_musica:
            audio = Audio()
            caminhos = [Path(chamada.args[0]) for chamada in carregar_som.call_args_list]
            self.assertIn(Path('assets/sounds/importados/pistola.wav'), caminhos)
            self.assertNotIn(Path('assets/sounds/acao/pistola.wav'), caminhos)
            carregar_musica.assert_called_once_with(str(Path('assets/sounds/importados/musica.mp3')))
            audio.contexto('jogando')
            carregar_musica.return_value.play.assert_called_once()
        self.jogo.audio.ajustar_volume(self.jogo.audio.volume)

    def test_audio_distingue_pistola_escopeta_e_arma_vazia(self):
        with patch.object(self.jogo.audio, 'tocar') as tocar:
            self.jogo.atualizar(.01, atirar=True, teclado=self.sem_teclas)
            self.assertIn(unittest.mock.call('tiro'), tocar.call_args_list)
            self.player.melhorar('escopeta')
            self.player.tempo_ultimo_tiro = -99999
            self.jogo.atualizar(.01, atirar=True, teclado=self.sem_teclas)
            self.assertIn(unittest.mock.call('tiro_escopeta'), tocar.call_args_list)
            tocar.reset_mock()
            self.player.municao = 0
            for _ in range(8):
                self.jogo.atualizar(.01, atirar=True, teclado=self.sem_teclas)
            self.assertEqual(tocar.call_args_list.count(unittest.mock.call('vazio')), 1)

    def test_musica_pausa_retorna_sem_reiniciar_e_volume_zero_silencia(self):
        audio = self.jogo.audio
        audio.atualizar_musica(2)
        self.assertTrue(audio.musica.caminho.endswith('partida.ogg'))
        volume, volume_musica = audio.volume, audio.volume_musica
        with patch.object(audio.musica, 'pause', wraps=audio.musica.pause) as pausar, \
             patch.object(audio.musica, 'unpause', wraps=audio.musica.unpause) as retomar, \
             patch.object(audio.musica, 'play', wraps=audio.musica.play) as iniciar:
            self.jogo.mudar('pausa')
            self.jogo.agir('opcoes')
            self.jogo.mudar('pausa')
            self.jogo.mudar('jogando')
            pausar.assert_called_once()
            retomar.assert_called_once()
            iniciar.assert_not_called()
        try:
            audio.ajustar_volume(0)
            self.assertTrue(all(s.sound.get_volume()==0 for s in audio.sons.values()))
            self.assertEqual(pygame.mixer.music.get_volume(), 0)
        finally:
            audio.ajustar_efeitos(volume)
            audio.ajustar_musica(volume_musica)

    def test_vozes_so_perto_com_intervalo_e_sem_mudar_sorteio_do_jogo(self):
        audio = self.jogo.audio
        audio.proxima_voz = 0
        z = ZumbiCaminhante(10000, 10000)
        estado_sorteio = random.getstate()
        with patch.object(audio, 'tocar') as tocar:
            audio.atualizar(0, self.player, [z])
            tocar.assert_not_called()
            z.x,z.y = self.player.x+100,self.player.y
            audio.atualizar(5000, self.player, [z])
            tocar.assert_called_once()
            self.assertTrue(tocar.call_args.args[0].startswith('zumbi_'))
            audio.atualizar(5100, self.player, [z])
            tocar.assert_called_once()
        self.assertEqual(random.getstate(), estado_sorteio)

    def test_camera_limites_congelamento_e_reinicio(self):
        from game_objects.bairro import LARGURA_MUNDO, ALTURA_MUNDO, INICIO
        c = self.jogo.camera
        self.player.x,self.player.y = 1680,1040
        self.avancar(1)
        self.assertGreater(c.x, 500)
        self.assertGreater(c.y, 400)
        self.assertLessEqual(c.x,LARGURA_MUNDO-960)
        self.assertLessEqual(c.y,ALTURA_MUNDO-640)
        posicao = (c.x,c.y)
        self.jogo.mudar('pausa')
        self.avancar(1)
        self.assertEqual((c.x,c.y),posicao)
        self.jogo.nova_partida()
        self.assertEqual((self.jogo.partida['player'].x,self.jogo.partida['player'].y),INICIO)
        self.assertNotEqual((c.x,c.y),posicao)

    def test_mira_convertida_para_mundo_e_tiro_fora_da_tela(self):
        self.player.x,self.player.y = 900,1040
        self.jogo.camera.x,self.jogo.camera.y = 500,700
        alvo_tela = (self.player.x+self.player.width/2-500+100,
                     self.player.y+self.player.height/2-700)
        self.jogo.atualizar(.02,mira=alvo_tela,atirar=True,teclado=self.sem_teclas)
        self.assertAlmostEqual(self.p['projeteis'][0].direcao[0],1)
        self.assertAlmostEqual(self.p['projeteis'][0].direcao[1],0)
        tiro = Projetil(1750,600,(1,0))
        self.p['projeteis'] = [tiro]
        self.avancar(.02)
        self.assertIn(tiro,self.p['projeteis'])

    def test_colisao_nao_muda_ao_virar(self):
        for ator in (self.player,ZumbiCorredor(0,0),ZumbiChefe(0,0)):
            tamanho = (ator.width,ator.height)
            for dx,dy in [(1,0),(-1,0),(0,1),(0,-1)]:
                ator.atualizar_direcao_sprite(dx,dy)
                self.assertEqual((ator.width,ator.height),tamanho)

    def test_rota_recupera_ator_na_folga_da_esquina_sem_atravessar_obstaculo(self):
        # Entre a oficina e o carro: livre fisicamente, dentro da margem de 3 px.
        for ator in (self.player, ZumbiCaminhante(0,0)):
            ator.x, ator.y = 325, 764
            self.assertFalse(any(colidiu(ator,o) for o in self.jogo.arena.obstaculos))
            rota = self.jogo.arena.rota((ator.x,ator.y),(1694,558),ator.width,ator.height)
            self.assertTrue(rota)
            for ponto in rota:
                for _ in range(2000):
                    dx,dy = ponto[0]-ator.x,ponto[1]-ator.y
                    distancia = math.hypot(dx,dy)
                    if distancia < .01:
                        break
                    passo = min(1,distancia)
                    antes = ator.x,ator.y
                    mover_com_colisao(ator,dx/distancia*passo,dy/distancia*passo,self.jogo.arena.obstaculos)
                    self.assertNotEqual((ator.x,ator.y),antes)
                    self.assertFalse(any(colidiu(ator,o) for o in self.jogo.arena.obstaculos if o.bloqueia_movimento))
                self.assertLess(math.dist((ator.x,ator.y),ponto),.02)

    def test_explorar_bairro_coletar_e_escapar_sem_atravessar_paredes(self):
        def caminhar(destino):
            rota = self.jogo.arena.rota((self.player.x,self.player.y),destino,
                                        self.player.width,self.player.height)
            self.assertTrue(rota)
            for ponto in rota:
                for _ in range(2000):
                    dx,dy = ponto[0]-self.player.x,ponto[1]-self.player.y
                    distancia = math.hypot(dx,dy)
                    if distancia < .01:
                        break
                    passo = min(3,distancia)
                    antes = (self.player.x,self.player.y)
                    mover_com_colisao(self.player,dx/distancia*passo,dy/distancia*passo,self.jogo.arena.obstaculos)
                    self.assertNotEqual((self.player.x,self.player.y),antes)
                    self.assertFalse(any(colidiu(self.player,o) for o in self.jogo.arena.obstaculos if o.bloqueia_movimento))
                    self.jogo.atualizar(1/60,teclado=self.sem_teclas)
                self.assertLess(math.dist((self.player.x,self.player.y),ponto),.02)
        missao=self.p['missao']
        with patch.object(self.p['gerenciador'],'atualizar',return_value=None), patch('main.salvar_pontuacao',return_value=[]):
            for x,y in (*missao.POSICOES,missao.painel):
                caminhar((x-self.player.width/2,y-self.player.height/2))
                self.jogo.atualizar(1/60,teclado=self.sem_teclas,interagir=True)
            self.assertFalse(missao.aberto)
            self.derrotar_chefe()
            self.assertTrue(missao.aberto)
            caminhar((missao.portao.x+28,missao.portao.y+55-self.player.height))
            self.assertEqual(self.jogo.estado,'vitoria')

    def test_desenho_movel_nao_acumula_cache_de_interface(self):
        self.jogo.desenhar()
        self.jogo.camera.x,self.jogo.camera.y=500,500
        self.jogo.desenhar()
        antes=len(self.jogo.interface.cache)
        for i in range(25):
            self.jogo.camera.x,self.jogo.camera.y=500+i,500+i
            self.jogo.desenhar()
        self.assertEqual(len(self.jogo.interface.cache),antes)

    def test_mouse_em_janela_redimensionada(self):
        # Simula a área real dobrada; mira e clique usam coordenadas virtuais.
        original = self.jogo.janela.real_screen
        try:
            self.jogo.janela.real_screen = pygame.Surface((1920, 1280))
            self.jogo.mudar('menu')
            centro=self.jogo.botoes()[0][0].center
            posicao_real=(centro[0]*2,centro[1]*2)
            with patch('pygame.mouse.get_pos', return_value=posicao_real):
                self.assertEqual(self.jogo.controle_mouse.get_position(), centro)
                self.jogo.eventos([pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=posicao_real)])
                self.assertEqual(self.jogo.estado, 'preparar')
        finally:
            self.jogo.janela.real_screen = original

    def test_loop_real_pplay_processa_eventos_tempo_e_desenho(self):
        janela = self.jogo.janela
        original_update = janela.update
        quadros = []
        self.jogo.mudar('menu')
        def update():
            original_update()
            quadros.append(self.jogo.estado)
            if len(quadros) == 1:
                # O primeiro Enter entra na preparação pelo Keyboard do PPlay.
                janela.eventos = [pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN)]
            elif len(quadros) == 2:
                self.jogo.foco = 3
                janela.eventos = [pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN)]
            elif len(quadros) == 3:
                self.jogo.partida['player'].melhorar('escopeta')
                janela.eventos = [pygame.event.Event(pygame.KEYDOWN, key=pygame.K_q)]
            elif len(quadros) == 5:
                self.jogo.rodando = False
        with patch.object(janela, 'update', side_effect=update), patch.object(janela, 'close') as fechar:
            self.jogo.executar()
            fechar.assert_called_once()
        self.assertEqual(quadros[:3], ['menu', 'preparar', 'jogando'])
        self.assertGreater(janela.delta_time(), 0)
        self.assertGreater(self.jogo.partida['tempo'], 0)
        self.assertEqual(self.jogo.partida['player'].arma, 'pistola')


if __name__ == '__main__':
    unittest.main()
