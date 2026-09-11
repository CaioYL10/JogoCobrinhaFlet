"""Cada poder faz o que promete — e deixa de fazer quando acaba."""

import unittest
from collections import deque

from jogo import modos
from jogo.estado import DISTANCIA_DO_RAIO, EstadoJogo
from jogo.grade import Ponto, distancia_manhattan
from jogo.poderes import ATE_USAR, DEFINICOES, PoderAtivo, TipoPoder


def com_poder(estado: EstadoJogo, tipo: TipoPoder) -> None:
    estado.poderes[tipo] = PoderAtivo(tipo=tipo, restante=DEFINICOES[tipo].duracao)


def fruta_na_frente(estado: EstadoJogo) -> None:
    estado.fruta = Ponto(estado.cabeca.x + 1, estado.cabeca.y)


class TestEscudo(unittest.TestCase):
    def _cobra_encarando_a_parede(self) -> EstadoJogo:
        estado = EstadoJogo(modos.CLASSICO, semente=1)
        estado.fruta = Ponto(0, 0)
        estado.cobra = deque([Ponto(23, 5), Ponto(22, 5), Ponto(21, 5)])
        return estado

    def test_absorve_a_colisao_e_se_gasta(self):
        estado = self._cobra_encarando_a_parede()
        estado.poderes[TipoPoder.ESCUDO] = PoderAtivo(TipoPoder.ESCUDO, ATE_USAR)

        resultado = estado.passo()

        self.assertTrue(resultado.escudo_salvou)
        self.assertTrue(estado.viva)
        self.assertNotIn(TipoPoder.ESCUDO, estado.poderes)

    def test_salva_uma_vez_so(self):
        estado = self._cobra_encarando_a_parede()
        estado.poderes[TipoPoder.ESCUDO] = PoderAtivo(TipoPoder.ESCUDO, ATE_USAR)

        estado.passo()
        segundo = estado.passo()

        self.assertTrue(segundo.morreu)

    def test_nao_envelhece_com_o_tempo(self):
        estado = EstadoJogo(modos.SEM_PAREDES, semente=1)
        estado.fruta = Ponto(0, 0)
        estado.poderes[TipoPoder.ESCUDO] = PoderAtivo(TipoPoder.ESCUDO, ATE_USAR)

        for _ in range(30):
            estado.passo()

        self.assertIn(TipoPoder.ESCUDO, estado.poderes)


class TestPontosEmDobro(unittest.TestCase):
    def test_fruta_vale_dois(self):
        estado = EstadoJogo(modos.CLASSICO, semente=1)
        com_poder(estado, TipoPoder.DOBRO)
        fruta_na_frente(estado)

        estado.passo()

        self.assertEqual(estado.pontos, 2)

    def test_volta_a_valer_um_quando_acaba(self):
        estado = EstadoJogo(modos.SEM_PAREDES, semente=1)
        estado.fruta = Ponto(0, 0)
        estado.poderes[TipoPoder.DOBRO] = PoderAtivo(TipoPoder.DOBRO, 2)

        estado.passo()
        estado.passo()
        self.assertNotIn(TipoPoder.DOBRO, estado.poderes)

        fruta_na_frente(estado)
        estado.passo()

        self.assertEqual(estado.pontos, 1)


class TestCameraLenta(unittest.TestCase):
    def test_dobra_o_intervalo_entre_passos(self):
        estado = EstadoJogo(modos.CLASSICO, semente=1)
        normal = estado.intervalo_ms()

        com_poder(estado, TipoPoder.LENTIDAO)

        self.assertEqual(estado.intervalo_ms(), normal * 2)


class TestIma(unittest.TestCase):
    def test_puxa_a_fruta_uma_celula_por_passo(self):
        estado = EstadoJogo(modos.SEM_PAREDES, semente=1)
        com_poder(estado, TipoPoder.IMA)
        estado.fruta = Ponto(estado.cabeca.x + 8, estado.cabeca.y)
        x_antes = estado.fruta.x

        estado.passo()

        self.assertEqual(estado.fruta.x, x_antes - 1)

    def test_sem_ima_a_fruta_fica_parada(self):
        estado = EstadoJogo(modos.SEM_PAREDES, semente=1)
        estado.fruta = Ponto(estado.cabeca.x + 8, estado.cabeca.y)
        antes = estado.fruta

        estado.passo()

        self.assertEqual(estado.fruta, antes)


class TestRaio(unittest.TestCase):
    def test_manda_a_fruta_para_longe(self):
        estado = EstadoJogo(modos.CLASSICO, semente=1)
        estado.fruta = Ponto(estado.cabeca.x + 1, estado.cabeca.y)

        estado._ativar(TipoPoder.RAIO)

        self.assertGreaterEqual(
            distancia_manhattan(estado.fruta, estado.cabeca), DISTANCIA_DO_RAIO
        )

    def test_e_instantaneo_nao_fica_ativo(self):
        estado = EstadoJogo(modos.CLASSICO, semente=1)

        estado._ativar(TipoPoder.RAIO)

        self.assertNotIn(TipoPoder.RAIO, estado.poderes)


class TestEncolher(unittest.TestCase):
    def _cobra_de_dez(self) -> EstadoJogo:
        estado = EstadoJogo(modos.SEM_PAREDES, semente=1)
        estado.fruta = Ponto(0, 0)
        estado.cobra = deque(Ponto(12 - i, 12) for i in range(10))
        return estado

    def test_corta_metade_do_corpo(self):
        estado = self._cobra_de_dez()

        estado._ativar(TipoPoder.ENCOLHER)

        self.assertEqual(len(estado.cobra), 5)

    def test_o_rabo_volta_quando_o_poder_acaba(self):
        estado = self._cobra_de_dez()
        estado._ativar(TipoPoder.ENCOLHER)

        for _ in range(DEFINICOES[TipoPoder.ENCOLHER].duracao + 10):
            estado.passo()

        self.assertTrue(estado.viva)
        self.assertEqual(len(estado.cobra), 10)

    def test_a_pontuacao_nao_muda_ao_encolher(self):
        estado = self._cobra_de_dez()
        estado.pontos = 42

        estado._ativar(TipoPoder.ENCOLHER)

        self.assertEqual(estado.pontos, 42)

    def test_nunca_encolhe_abaixo_do_minimo(self):
        estado = EstadoJogo(modos.SEM_PAREDES, semente=1)
        estado.fruta = Ponto(0, 0)

        estado._ativar(TipoPoder.ENCOLHER)

        self.assertGreaterEqual(len(estado.cobra), 3)


class TestItensNoTabuleiro(unittest.TestCase):
    def test_nasce_um_item_a_cada_quatro_frutas(self):
        estado = EstadoJogo(modos.SEM_PAREDES, semente=3)

        for _ in range(4):
            estado.fruta = Ponto(estado.cabeca.x + 1, estado.cabeca.y)
            estado.passo()

        self.assertIsNotNone(estado.item_poder)


if __name__ == "__main__":
    unittest.main()
