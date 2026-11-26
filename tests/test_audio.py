"""Transições e configurações do áudio, sem depender de uma saída física."""
import json
import unittest
from unittest.mock import Mock, patch

from game_objects.audio import Audio
from main import Jogo


class Trilhas(unittest.TestCase):
    def setUp(self):
        self.patches = [patch('game_objects.audio.Sound'),
                        patch('game_objects.audio.Music', side_effect=lambda p: Mock(caminho=p)),
                        patch('game_objects.audio.SoundManager.set_music_volume')]
        for p in self.patches:
            p.start()
            self.addCleanup(p.stop)
        self.audio = Audio(caminho_musica='partida.ogg', caminho_menu='menu.ogg')
        self.menu = self.audio.trilhas['menu']
        self.partida = self.audio.trilhas['jogo']

    def ir(self, estado, **kwargs):
        self.audio.contexto(estado, **kwargs)
        self.audio.atualizar_musica(2)

    def test_navegacao_preserva_menu_e_troca_gradualmente_para_jogo(self):
        for estado in ('menu', 'opcoes', 'ranking', 'preparar'):
            self.ir(estado)
        self.menu.play.assert_called_once_with(loops=-1, fade_in_ms=0)
        self.audio.contexto('jogando')
        self.partida.play.assert_not_called()
        self.audio.atualizar_musica(.14)
        self.assertAlmostEqual(self.audio.ganho_musica, .5)
        self.partida.play.assert_not_called()
        self.audio.atualizar_musica(2)
        self.menu.stop.assert_called_once_with(fade_out_ms=0)
        self.partida.play.assert_called_once_with(loops=-1, fade_in_ms=0)
        self.assertEqual(self.audio.ganho_musica, 1)

    def test_pausa_opcoes_e_melhoria_preservam_ponto_da_partida(self):
        self.ir('jogando')
        self.ir('pausa')
        self.ir('opcoes', em_partida=True)
        self.ir('pausa')
        self.ir('jogando')
        self.ir('melhoria')
        self.ir('jogando')
        self.partida.play.assert_called_once()
        self.assertEqual(self.partida.pause.call_count, 2)
        self.assertEqual(self.partida.unpause.call_count, 2)
        self.menu.play.assert_not_called()

    def test_pausa_durante_transicao_nao_deixa_menu_tocando(self):
        self.ir('menu')
        self.audio.contexto('jogando')
        self.ir('pausa')
        self.menu.stop.assert_called_once_with(fade_out_ms=0)
        self.partida.pause.assert_called_once()
        self.ir('jogando')
        self.partida.play.assert_called_once()
        self.partida.unpause.assert_called_once()

    def test_reiniciar_partida_recomeca_faixa_e_sair_da_pausa_retorna_menu(self):
        self.ir('jogando')
        self.audio.reiniciar_partida()
        self.ir('jogando')
        self.assertEqual(self.partida.play.call_count, 2)
        self.ir('pausa')
        self.ir('menu')
        self.assertFalse(self.audio.musica_pausada)
        self.menu.play.assert_called_once()

    def test_resultados_silenciam_musica_sem_fade_bloqueante(self):
        for resultado in ('fim', 'vitoria'):
            with self.subTest(resultado=resultado):
                self.ir('jogando')
                self.partida.stop.reset_mock()
                self.audio.contexto(resultado)
                self.partida.stop.assert_not_called()
                self.audio.atualizar_musica(2)
                self.partida.stop.assert_called_once_with(fade_out_ms=0)
                self.assertIsNone(self.audio.musica)
        self.ir('menu')
        self.menu.play.assert_called_once()

    def test_volumes_independentes_com_limites_e_mudo(self):
        self.ir('jogando')
        som = self.audio.sons['tiro']
        som.set_volume.reset_mock()
        self.audio.ajustar_musica(0)
        som.set_volume.assert_not_called()
        self.assertEqual(self.audio.volume, .5)
        self.audio.ajustar_musica(2)
        self.audio.ajustar_efeitos(0)
        self.assertEqual(self.audio.volume_musica, 1)
        som.set_volume.assert_called_with(0)
        self.audio.ajustar_musica(-1)
        self.assertEqual(self.audio.volume_musica, 0)
        self.audio.ajustar_efeitos(2)
        self.assertEqual(self.audio.volume, 1)

    def test_configuracao_migra_volume_antigo_e_salva_controles_separados(self):
        jogo = Jogo.__new__(Jogo)
        jogo.audio = self.audio
        with patch('main.Path.read_text', return_value='{"volume": 0.4}'):
            jogo.carregar_configuracao()
        self.assertEqual(self.audio.volume, .4)
        self.assertEqual(self.audio.volume_musica, .35)
        with patch.object(self.audio, 'tocar'), patch('main.Path.mkdir'), \
                patch('main.Path.write_text') as salvar:
            jogo.agir('mais_musica')
            jogo.agir('menos')
        config = json.loads(salvar.call_args.args[0])
        self.assertEqual(config, {'volume_efeitos': .3, 'volume_musica': .45})
        with patch('main.Path.read_text', return_value=json.dumps(config)):
            jogo.carregar_configuracao()
        self.assertEqual(self.audio.volume, .3)
        self.assertEqual(self.audio.volume_musica, .45)


if __name__ == '__main__':
    unittest.main()
