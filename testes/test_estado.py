"""Regras básicas: andar, comer, morrer e virar."""

import unittest
from collections import deque

from jogo import modos
from jogo.estado import EstadoJogo
from jogo.grade import BAIXO, CIMA, ESQUERDA, Ponto


def longe(estado: EstadoJogo) -> None:
    """Tira a fruta do caminho para o teste tratar só do movimento."""
    estado.fruta = Ponto(0, 0)


class TestMovimento(unittest.TestCase):
    def test_andar_nao_faz_a_cobra_crescer(self):
        estado = EstadoJogo(modos.CLASSICO, semente=1)
        longe(estado)
        tamanho = len(estado.cobra)

        estado.passo()

        self.assertEqual(len(estado.cobra), tamanho)

    def test_cabeca_anda_na_direcao_escolhida(self):
        estado = EstadoJogo(modos.CLASSICO, semente=1)
        longe(estado)
        antes = estado.cabeca

        estado.girar(BAIXO)
        estado.passo()

        self.assertEqual(estado.cabeca, Ponto(antes.x, antes.y + 1))

    def test_virar_180_graus_e_ignorado(self):
        estado = EstadoJogo(modos.CLASSICO, semente=1)
        longe(estado)
        antes = estado.cabeca

        estado.girar(ESQUERDA)  # está indo para a direita
        estado.passo()

        self.assertEqual(estado.cabeca, Ponto(antes.x + 1, antes.y))

    def test_duas_viradas_no_mesmo_passo_nao_matam_a_cobra(self):
        # O bug clássico: cima e depois esquerda antes do passo acontecer
        # fariam a cobra entrar no próprio pescoço se a comparação fosse com
        # a tecla anterior em vez da direção de fato aplicada.
        estado = EstadoJogo(modos.CLASSICO, semente=1)
        longe(estado)

        estado.girar(CIMA)
        estado.girar(ESQUERDA)
        estado.passo()

        self.assertTrue(estado.viva)


class TestComer(unittest.TestCase):
    def test_comer_cresce_e_pontua(self):
        estado = EstadoJogo(modos.CLASSICO, semente=1)
        tamanho = len(estado.cobra)
        estado.fruta = Ponto(estado.cabeca.x + 1, estado.cabeca.y)

        resultado = estado.passo()

        self.assertTrue(resultado.comeu)
        self.assertEqual(estado.pontos, 1)
        self.assertEqual(len(estado.cobra), tamanho + 1)

    def test_fruta_nova_nunca_nasce_em_cima_da_cobra(self):
        estado = EstadoJogo(modos.CLASSICO, semente=7)
        for _ in range(20):
            estado.fruta = Ponto(estado.cabeca.x + 1, estado.cabeca.y)
            if not estado.viva:
                break
            estado.passo()
            self.assertNotIn(estado.fruta, set(estado.cobra))


class TestMorte(unittest.TestCase):
    def test_morre_ao_bater_na_parede_no_classico(self):
        estado = EstadoJogo(modos.CLASSICO, semente=1)
        longe(estado)
        estado.cobra = deque([Ponto(23, 5), Ponto(22, 5), Ponto(21, 5)])

        resultado = estado.passo()

        self.assertTrue(resultado.morreu)
        self.assertFalse(estado.viva)

    def test_morre_ao_entrar_no_proprio_corpo(self):
        estado = EstadoJogo(modos.CLASSICO, semente=1)
        longe(estado)
        # Cobra em forma de laço: indo para a direita, a cabeça bate no
        # segmento do meio (6,5) — que não é o rabo, então não sai a tempo.
        estado.cobra = deque(
            [
                Ponto(5, 5),
                Ponto(4, 5),
                Ponto(4, 6),
                Ponto(5, 6),
                Ponto(6, 6),
                Ponto(6, 5),
                Ponto(7, 5),
            ]
        )

        resultado = estado.passo()

        self.assertTrue(resultado.morreu)

    def test_cabeca_pode_ocupar_a_celula_do_rabo(self):
        # O rabo sai no mesmo passo, então aquela célula está livre.
        estado = EstadoJogo(modos.CLASSICO, semente=1)
        longe(estado)
        estado.cobra = deque(
            [Ponto(5, 5), Ponto(4, 5), Ponto(4, 6), Ponto(5, 6), Ponto(6, 6), Ponto(6, 5)]
        )

        resultado = estado.passo()

        self.assertFalse(resultado.morreu)


class TestVelocidade(unittest.TestCase):
    def test_fica_mais_rapido_conforme_come(self):
        estado = EstadoJogo(modos.CLASSICO, semente=1)
        inicial = estado.intervalo_ms()

        estado.frutas_comidas = 10

        self.assertLess(estado.intervalo_ms(), inicial)

    def test_velocidade_tem_piso(self):
        estado = EstadoJogo(modos.CLASSICO, semente=1)
        estado.frutas_comidas = 10_000

        self.assertGreaterEqual(estado.intervalo_ms(), 1)


if __name__ == "__main__":
    unittest.main()
