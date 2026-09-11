"""Desbloqueio de skins e o arquivo de progresso."""

import json
import tempfile
import unittest
from pathlib import Path

from jogo import progresso as prog
from jogo import skins


class TestDesbloqueio(unittest.TestCase):
    def test_comeca_com_duas_skins(self):
        self.assertEqual(len(skins.liberadas(0)), 2)

    def test_recorde_alto_libera_todas(self):
        self.assertEqual(len(skins.liberadas(9999)), len(skins.TODAS))

    def test_skin_so_libera_no_valor_exato(self):
        fogo = skins.obter("fogo")

        self.assertFalse(fogo.liberada_com(fogo.pontos_para_liberar - 1))
        self.assertTrue(fogo.liberada_com(fogo.pontos_para_liberar))

    def test_a_proxima_meta_e_a_mais_barata(self):
        proxima = skins.proxima_a_liberar(0)

        self.assertIsNotNone(proxima)
        self.assertEqual(proxima.id, "fogo")

    def test_sem_meta_quando_tudo_liberado(self):
        self.assertIsNone(skins.proxima_a_liberar(9999))

    def test_id_desconhecido_cai_na_skin_padrao(self):
        self.assertEqual(skins.obter("nao_existe"), skins.PADRAO)

    def test_arco_iris_muda_de_cor_ao_longo_do_corpo(self):
        arco = skins.obter("arco_iris")

        self.assertNotEqual(arco.cor_do_segmento(0), arco.cor_do_segmento(1))

    def test_todas_as_skins_tem_id_unico(self):
        ids = [skin.id for skin in skins.TODAS]

        self.assertEqual(len(ids), len(set(ids)))


class TestProgresso(unittest.TestCase):
    def setUp(self):
        self.pasta = tempfile.TemporaryDirectory()
        self.arquivo = Path(self.pasta.name) / "progresso.json"

    def tearDown(self):
        self.pasta.cleanup()

    def test_arquivo_inexistente_devolve_progresso_zerado(self):
        carregado = prog.carregar(self.arquivo)

        self.assertEqual(carregado.recorde, 0)
        self.assertEqual(carregado.partidas, 0)

    def test_arquivo_corrompido_nao_derruba_o_jogo(self):
        self.arquivo.write_text("isto não é json {{{", encoding="utf-8")

        carregado = prog.carregar(self.arquivo)

        self.assertEqual(carregado.recorde, 0)

    def test_campo_com_tipo_errado_vira_zero(self):
        self.arquivo.write_text(json.dumps({"recorde": "muito"}), encoding="utf-8")

        carregado = prog.carregar(self.arquivo)

        self.assertEqual(carregado.recorde, 0)

    def test_salvar_e_carregar_preserva_tudo(self):
        original = prog.Progresso(
            recorde=120,
            recordes_por_modo={"classico": 120, "labirinto": 40},
            partidas=9,
            skin_escolhida="neon",
            modo_escolhido="labirinto",
        )

        prog.salvar(original, self.arquivo)
        carregado = prog.carregar(self.arquivo)

        self.assertEqual(carregado, original)

    def test_registrar_partida_avisa_quando_bate_o_recorde(self):
        p = prog.Progresso()

        self.assertTrue(p.registrar_partida("classico", 30))
        self.assertFalse(p.registrar_partida("classico", 10))
        self.assertEqual(p.recorde, 30)
        self.assertEqual(p.partidas, 2)

    def test_cada_modo_guarda_o_proprio_recorde(self):
        p = prog.Progresso()

        p.registrar_partida("classico", 30)
        p.registrar_partida("labirinto", 12)

        self.assertEqual(p.recorde_do_modo("classico"), 30)
        self.assertEqual(p.recorde_do_modo("labirinto"), 12)
        self.assertEqual(p.recorde_do_modo("nuvens"), 0)


if __name__ == "__main__":
    unittest.main()
