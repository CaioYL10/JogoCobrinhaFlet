"""Cada modo muda o mundo de um jeito diferente."""

import random
import unittest
from collections import deque

from jogo import modos
from jogo.estado import EstadoJogo
from jogo.grade import ALTURA, LARGURA, Direcao, Ponto


class TestParedes(unittest.TestCase):
    def _cobra_na_borda_direita(self, modo) -> EstadoJogo:
        estado = EstadoJogo(modo, semente=1)
        estado.fruta = Ponto(0, 0)
        estado.cobra = deque([Ponto(23, 5), Ponto(22, 5), Ponto(21, 5)])
        return estado

    def test_classico_mata_na_parede(self):
        estado = self._cobra_na_borda_direita(modos.CLASSICO)

        estado.passo()

        self.assertFalse(estado.viva)

    def test_sem_paredes_da_a_volta(self):
        estado = self._cobra_na_borda_direita(modos.SEM_PAREDES)

        estado.passo()

        self.assertTrue(estado.viva)
        self.assertEqual(estado.cabeca, Ponto(0, 5))


class TestLabirinto(unittest.TestCase):
    def test_tem_blocos_no_mapa(self):
        estado = EstadoJogo(modos.LABIRINTO, semente=1)

        self.assertGreater(len(estado.obstaculos), 0)

    def test_nenhum_bloco_em_cima_da_cobra(self):
        for semente in range(10):
            estado = EstadoJogo(modos.LABIRINTO, semente=semente)
            self.assertEqual(estado.obstaculos & set(estado.cobra), set())

    def test_a_cobra_tem_caminho_livre_no_comeco(self):
        # Ela nasce indo para a direita: as células logo à frente precisam
        # estar livres, senão a partida acaba antes de o jogador reagir.
        for semente in range(10):
            estado = EstadoJogo(modos.LABIRINTO, semente=semente)
            frente = {
                Ponto(estado.cabeca.x + i, estado.cabeca.y) for i in range(1, 5)
            }
            self.assertEqual(estado.obstaculos & frente, set())

    def test_morre_ao_bater_num_bloco(self):
        estado = EstadoJogo(modos.LABIRINTO, semente=1)
        estado.fruta = Ponto(0, 0)
        estado.obstaculos.add(Ponto(estado.cabeca.x + 1, estado.cabeca.y))

        resultado = estado.passo()

        self.assertTrue(resultado.morreu)

    def test_a_fruta_nunca_nasce_dentro_de_um_bloco(self):
        for semente in range(10):
            estado = EstadoJogo(modos.LABIRINTO, semente=semente)
            self.assertNotIn(estado.fruta, estado.obstaculos)

    def test_classico_nao_tem_blocos(self):
        estado = EstadoJogo(modos.CLASSICO, semente=1)

        self.assertEqual(estado.obstaculos, set())


class TestNuvens(unittest.TestCase):
    def test_o_modo_comeca_com_quatro_nuvens(self):
        estado = EstadoJogo(modos.NUVENS, semente=1)

        self.assertEqual(len(estado.nuvens), 4)

    def test_a_nuvem_ricocheteia_em_vez_de_sair_do_mapa(self):
        nuvem = modos.Nuvem(canto=Ponto(0, 0), direcao=Direcao(-1, -1))

        nuvem.mover()

        self.assertEqual(nuvem.direcao, Direcao(1, 1))
        self.assertTrue(all(0 <= c.x < LARGURA and 0 <= c.y < ALTURA for c in nuvem.celulas()))

    def test_a_nuvem_fica_sempre_dentro_do_mapa(self):
        rng = random.Random(5)
        nuvens = modos.NUVENS.criar_nuvens(rng)

        for _ in range(200):
            for nuvem in nuvens:
                nuvem.mover()
                for celula in nuvem.celulas():
                    self.assertTrue(0 <= celula.x < LARGURA)
                    self.assertTrue(0 <= celula.y < ALTURA)

    def test_morre_ao_bater_numa_nuvem(self):
        estado = EstadoJogo(modos.NUVENS, semente=1)
        estado.fruta = Ponto(0, 0)
        estado.nuvens = []
        alvo = Ponto(estado.cabeca.x + 1, estado.cabeca.y)
        # Nuvem parada em cima do destino: direção zero não a move do lugar.
        estado.nuvens = [modos.Nuvem(canto=alvo, direcao=Direcao(0, 0))]

        resultado = estado.passo()

        self.assertTrue(resultado.morreu)

    def test_nenhuma_nuvem_nasce_em_cima_da_cobra(self):
        for semente in range(40):
            estado = EstadoJogo(modos.NUVENS, semente=semente)
            sobreposicao = estado.celulas_das_nuvens() & set(estado.cobra)
            self.assertEqual(
                sobreposicao, set(), f"semente {semente}: nuvem em cima da cobra"
            )

    def test_a_cobra_tem_caminho_livre_no_comeco_com_nuvens(self):
        # Nascer colado numa nuvem mata antes de o jogador encostar no teclado.
        for semente in range(40):
            estado = EstadoJogo(modos.NUVENS, semente=semente)
            frente = {
                Ponto(estado.cabeca.x + i, estado.cabeca.y) for i in range(1, 6)
            }
            self.assertEqual(
                estado.celulas_das_nuvens() & frente,
                set(),
                f"semente {semente}: nuvem bloqueando a saída",
            )

    def test_a_fruta_nunca_nasce_dentro_de_uma_nuvem(self):
        for semente in range(20):
            estado = EstadoJogo(modos.NUVENS, semente=semente)
            self.assertNotIn(estado.fruta, estado.celulas_das_nuvens())

    def test_modos_todos_tem_id_unico(self):
        ids = [modo.id for modo in modos.TODOS]

        self.assertEqual(len(ids), len(set(ids)))


if __name__ == "__main__":
    unittest.main()
