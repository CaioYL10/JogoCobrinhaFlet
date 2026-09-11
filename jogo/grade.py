"""Tabuleiro, coordenadas e direções."""

from typing import NamedTuple

LARGURA = 24
ALTURA = 24
CELULA = 22

INTERVALO_INICIAL_MS = 150
INTERVALO_MINIMO_MS = 70
ACELERACAO_POR_FRUTA_MS = 4


class Ponto(NamedTuple):
    x: int
    y: int

    def somar(self, direcao: "Direcao") -> "Ponto":
        return Ponto(self.x + direcao.dx, self.y + direcao.dy)


class Direcao(NamedTuple):
    dx: int
    dy: int


CIMA = Direcao(0, -1)
BAIXO = Direcao(0, 1)
ESQUERDA = Direcao(-1, 0)
DIREITA = Direcao(1, 0)


def sao_opostas(a: Direcao, b: Direcao) -> bool:
    return a.dx == -b.dx and a.dy == -b.dy


def dentro_da_grade(p: Ponto) -> bool:
    return 0 <= p.x < LARGURA and 0 <= p.y < ALTURA


def dar_a_volta(p: Ponto) -> Ponto:
    return Ponto(p.x % LARGURA, p.y % ALTURA)


def distancia_manhattan(a: Ponto, b: Ponto) -> int:
    return abs(a.x - b.x) + abs(a.y - b.y)
