"""Integração das novas folhas com a animação nativa do PPlay."""
import os
os.environ['SDL_VIDEODRIVER'] = 'dummy'
os.environ['SDL_AUDIODRIVER'] = 'dummy'

from pathlib import Path
import unittest
from unittest.mock import patch
import pygame
from PPlay.window import Window
from PPlay.camera import Camera
from PPlay.sprite import Sprite
from game_objects.player import Player


class PersonagemPistola(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        os.chdir(Path(__file__).resolve().parents[1])
        cls.janela = Window(960, 640, 'Teste de animações', intro=False)
        cls.camera = Camera(960, 640)

    def setUp(self):
        self.player = Player(440, 1010)

    def test_quatro_direcoes_com_altura_64_transparencia_e_poses_distintas(self):
        for direcao in ('down', 'up', 'side', 'side-left'):
            with self.subTest(direcao=direcao):
                self.player.direcao_atual_sprite = direcao
                self.player.estado_atual = 'run'
                sprite = self.player._sprite_ativo()
                self.assertIsInstance(sprite, Sprite)
                self.assertEqual((sprite.width, sprite.height, sprite.total_frames), (64, 64, 6))
                poses = set()
                alturas = []
                for i in range(6):
                    sprite.set_curr_frame(i)
                    frame = sprite._recorte_atual()
                    self.assertEqual(frame.get_at((0, 0)).a, 0)
                    caixa = frame.get_bounding_rect(min_alpha=128)
                    self.assertGreater(caixa.width, 15)
                    self.assertEqual(caixa.bottom, 64)
                    alturas.append(caixa.height)
                    poses.add(pygame.image.tobytes(frame, 'RGBA'))
                self.assertEqual(max(alturas), 64)
                self.assertGreaterEqual(len(poses), 5)

    def test_andar_avanca_seis_quadros_parado_e_pausa_nao_caminham(self):
        p = self.player
        p.estado_atual = 'run'
        sprite = p._sprite_ativo()
        with patch.object(self.janela, 'delta_time', return_value=.12):
            for i in range(1, 7):
                p.draw()
                self.assertEqual(sprite.get_curr_frame(), i % 6)
            sprite.set_curr_frame(3)
            p.draw(animar=False)
            self.assertEqual(sprite.get_curr_frame(), 3)
            p.estado_atual = 'idle'
            for _ in range(10):
                p.draw()
            self.assertEqual(p._sprite_ativo().get_curr_frame(), 0)

    def test_esquerda_espelha_quadro_sem_inverter_ordem_da_caminhada(self):
        direito = self.player.animacoes_pistola['side']['run']
        esquerdo = self.player.animacoes_pistola['side-left']['run']
        for i in range(6):
            esperado = pygame.transform.flip(direito.image.subsurface((i*64, 0, 64, 64)), True, False)
            real = esquerdo._superficie(6, 1).subsurface((i*64, 0, 64, 64))
            self.assertEqual(pygame.image.tobytes(real, 'RGBA'), pygame.image.tobytes(esperado, 'RGBA'))

    def test_desbloqueio_equipa_nova_escopeta_e_q_alterna_sem_mudar_colisor(self):
        p = self.player
        tamanho = p.width, p.height
        posicao = p.x, p.y
        p.trocar_arma()
        self.assertEqual(p.arma, 'pistola')  # Q só alterna depois do desbloqueio.
        for direcao in p.animacoes_pistola:
            p.direcao_atual_sprite = direcao
            self.assertEqual((p.width, p.height), tamanho)
            self.assertIn('/pistola/', p._sprite_ativo().caminho)
        p.melhorar('escopeta')
        self.assertIn('/escopeta/', p._sprite_ativo().caminho)
        self.assertEqual(len(p.disparar(0)), 5)
        for direcao in p.animacoes_escopeta:
            p.direcao_atual_sprite = direcao
            for _ in range(4):
                p.trocar_arma()
                self.assertIn(f'/{p.arma}/', p._sprite_ativo().caminho)
                self.assertEqual((p.width, p.height), tamanho)
                self.assertEqual((p.x, p.y), posicao)

    def test_escopeta_tem_quatro_direcoes_transparentes_e_cano_sem_corte(self):
        p = self.player
        p.melhorar('escopeta')
        p.estado_atual = 'run'
        for direcao in p.animacoes_escopeta:
            p.direcao_atual_sprite = direcao
            sprite = p._sprite_ativo()
            self.assertIsInstance(sprite, Sprite)
            self.assertEqual((sprite.width, sprite.height, sprite.total_frames), (96, 80, 6))
            poses = set()
            for i in range(6):
                sprite.set_curr_frame(i)
                frame = sprite._recorte_atual()
                caixa = frame.get_bounding_rect(min_alpha=128)
                self.assertEqual(caixa.bottom, 80)
                self.assertGreater(caixa.left, 0)
                self.assertLess(caixa.right, 96)
                self.assertEqual(frame.get_at((0, 0)).a, 0)
                poses.add(pygame.image.tobytes(frame, 'RGBA'))
            self.assertGreaterEqual(len(poses), 5)

    def test_escopeta_anima_pelo_pplay_e_congela_na_pausa_e_parado(self):
        p = self.player
        p.melhorar('escopeta')
        p.estado_atual = 'run'
        sprite = p._sprite_ativo()
        with patch.object(self.janela, 'delta_time', return_value=.12):
            for i in range(1, 7):
                p.draw()
                self.assertEqual(sprite.get_curr_frame(), i % 6)
            sprite.set_curr_frame(4)
            for _ in range(5):
                p.draw(animar=False)
            self.assertEqual(sprite.get_curr_frame(), 4)
            p.estado_atual = 'idle'
            for _ in range(10):
                p.draw()
            self.assertEqual(p._sprite_ativo().get_curr_frame(), 0)

    def test_esquerda_da_escopeta_espelha_quadros_sem_inverter_ordem(self):
        direito = self.player.animacoes_escopeta['side']['run']
        esquerdo = self.player.animacoes_escopeta['side-left']['run']
        for i in range(6):
            esperado = pygame.transform.flip(direito.image.subsurface((i*96, 0, 96, 80)), True, False)
            real = esquerdo._superficie(6, 1).subsurface((i*96, 0, 96, 80))
            self.assertEqual(pygame.image.tobytes(real, 'RGBA'), pygame.image.tobytes(esperado, 'RGBA'))

    def test_cinco_pellets_e_clarao_partem_do_cano_da_escopeta(self):
        p = self.player
        p.melhorar('escopeta')
        for direcao, vetor in [('side', (1, 0)), ('side-left', (-1, 0)),
                               ('down', (0, 1)), ('up', (0, -1))]:
            p.direcao_atual_sprite, p.direcao_atual = direcao, vetor
            antes = p.municao
            tiros = p.disparar(1000)
            self.assertEqual(len(tiros), 5)
            self.assertEqual(p.municao, antes-1)
            _, ponta = p.pontos_arma()
            self.assertEqual(p.origem_ultimo_tiro, ponta)
            p.tempo_jogo = 1020
            with patch.object(p.clarao, 'desenhar_centro') as clarao:
                p.draw(animar=False)
                clarao.assert_called_once_with(ponta[0]+vetor[0]*3, ponta[1]+vetor[1]*3, vetor)
            p.tempo_ultimo_tiro = -99999

    def test_clarao_da_pistola_acompanha_ponta_visivel_em_todas_as_direcoes(self):
        p = self.player
        for direcao, vetor in [('side', (1, 0)), ('side-left', (-1, 0)),
                               ('down', (0, 1)), ('up', (0, -1))]:
            p.direcao_atual_sprite, p.direcao_atual = direcao, vetor
            tiro = p.disparar(1000)
            self.assertEqual(len(tiro), 1)
            _, ponta = p.pontos_arma()
            self.assertEqual(p.origem_ultimo_tiro, ponta)
            p.tempo_jogo = 1020
            with patch.object(p.clarao, 'desenhar_centro') as clarao:
                p.draw(animar=False)
                clarao.assert_called_once_with(ponta[0]+vetor[0]*3, ponta[1]+vetor[1]*3, vetor)
            p.tempo_ultimo_tiro = -99999


if __name__ == '__main__':
    unittest.main()
