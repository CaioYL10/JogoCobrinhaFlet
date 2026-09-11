"""A interpolação que faz o movimento deslizar.

Este é o único teste que importa a pasta `ui` — ele não abre janela nenhuma,
só confere a conta que decide onde cada segmento é desenhado.
"""

import unittest

from jogo import modos, skins
from jogo.estado import EstadoJogo
from jogo.grade import Ponto
from ui.desenho import _entre, formas_moveis


class TestPosicaoIntermediaria(unittest.TestCase):
    def test_no_comeco_do_passo_fica_na_posicao_antiga(self):
        self.assertEqual(_entre(Ponto(5, 5), Ponto(6, 5), 0.0), (5.0, 5.0))

    def test_no_meio_do_passo_fica_na_metade(self):
        self.assertEqual(_entre(Ponto(5, 5), Ponto(6, 5), 0.5), (5.5, 5.0))

    def test_no_fim_do_passo_chega_na_posicao_nova(self):
        self.assertEqual(_entre(Ponto(5, 5), Ponto(6, 5), 1.0), (6.0, 5.0))

    def test_desliza_tambem_na_vertical(self):
        self.assertEqual(_entre(Ponto(5, 5), Ponto(5, 4), 0.25), (5.0, 4.75))

    def test_segmento_novo_nao_desliza(self):
        # Segmento que acabou de nascer no rabo não tem posição anterior.
        self.assertEqual(_entre(None, Ponto(7, 3), 0.5), (7.0, 3.0))

    def test_volta_pela_borda_nao_atravessa_a_tela(self):
        # Da coluna 23 para a 0: deslizar faria a cobra varrer o tabuleiro
        # inteiro no meio do passo. Tem que aparecer direto no destino.
        self.assertEqual(_entre(Ponto(23, 5), Ponto(0, 5), 0.5), (0.0, 5.0))

    def test_volta_pela_borda_vertical_tambem(self):
        self.assertEqual(_entre(Ponto(5, 0), Ponto(5, 23), 0.5), (5.0, 23.0))


class TestDesenhoAnimado(unittest.TestCase):
    def test_a_cobra_ocupa_posicoes_diferentes_durante_o_passo(self):
        estado = EstadoJogo(modos.SEM_PAREDES, semente=1)
        estado.fruta = Ponto(0, 0)
        estado.passo()

        inicio = formas_moveis(estado, skins.PADRAO, 0.0)
        meio = formas_moveis(estado, skins.PADRAO, 0.5)
        fim = formas_moveis(estado, skins.PADRAO, 1.0)

        self.assertEqual(len(inicio), len(meio), "o número de formas não pode variar")
        xs = [formas[-3].x for formas in (inicio, meio, fim)]
        self.assertLess(xs[0], xs[1])
        self.assertLess(xs[1], xs[2])

    def test_antes_do_primeiro_passo_a_cobra_ja_aparece(self):
        estado = EstadoJogo(modos.CLASSICO, semente=1)

        formas = formas_moveis(estado, skins.PADRAO, 0.0)

        self.assertGreater(len(formas), 0)


if __name__ == "__main__":
    unittest.main()
