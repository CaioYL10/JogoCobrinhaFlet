"""Os quatro modos de jogo e os obstáculos de cada um."""

import random
from dataclasses import dataclass

from .grade import ALTURA, LARGURA, Direcao, Ponto, dar_a_volta


def _bloco(x: int, y: int, largura: int, altura: int) -> set[Ponto]:
    return {Ponto(x + dx, y + dy) for dx in range(largura) for dy in range(altura)}


def _planta_cruz() -> set[Ponto]:
    """Duas barras cruzadas no meio, com passagem no centro."""
    meio_x, meio_y = LARGURA // 2, ALTURA // 2
    barras = _bloco(meio_x - 1, 4, 2, 6) | _bloco(meio_x - 1, ALTURA - 10, 2, 6)
    barras |= _bloco(4, meio_y - 1, 6, 2) | _bloco(LARGURA - 10, meio_y - 1, 6, 2)
    return barras


def _planta_cantos() -> set[Ponto]:
    """Um bloco em cada quadrante, longe das bordas."""
    return (
        _bloco(4, 4, 4, 4)
        | _bloco(LARGURA - 8, 4, 4, 4)
        | _bloco(4, ALTURA - 8, 4, 4)
        | _bloco(LARGURA - 8, ALTURA - 8, 4, 4)
    )


def _planta_corredores() -> set[Ponto]:
    """Barras horizontais alternadas — dá para zigue-zaguear entre elas."""
    paredes: set[Ponto] = set()
    for i, y in enumerate(range(5, ALTURA - 4, 6)):
        if i % 2 == 0:
            paredes |= _bloco(0, y, LARGURA - 7, 2)
        else:
            paredes |= _bloco(7, y, LARGURA - 7, 2)
    return paredes


PLANTAS = (_planta_cruz, _planta_cantos, _planta_corredores)


@dataclass
class Nuvem:
    """Bloco 2x2 que anda em linha reta e ricocheteia nas bordas."""

    canto: Ponto
    direcao: Direcao
    tamanho: int = 2

    def celulas(self) -> set[Ponto]:
        return {
            Ponto(self.canto.x + dx, self.canto.y + dy)
            for dx in range(self.tamanho)
            for dy in range(self.tamanho)
        }

    def mover(self) -> None:
        destino = self.canto.somar(self.direcao)
        bateu_x = destino.x < 0 or destino.x + self.tamanho > LARGURA
        bateu_y = destino.y < 0 or destino.y + self.tamanho > ALTURA
        if bateu_x or bateu_y:
            self.direcao = Direcao(
                -self.direcao.dx if bateu_x else self.direcao.dx,
                -self.direcao.dy if bateu_y else self.direcao.dy,
            )
            destino = self.canto.somar(self.direcao)
        self.canto = destino


@dataclass(frozen=True)
class Modo:
    id: str
    nome: str
    descricao: str
    atravessa_paredes: bool = False
    tem_labirinto: bool = False
    tem_nuvens: bool = False
    quantidade_nuvens: int = 0

    def criar_obstaculos(self, rng: random.Random) -> set[Ponto]:
        if not self.tem_labirinto:
            return set()
        return rng.choice(PLANTAS)()

    def criar_nuvens(
        self, rng: random.Random, proibidas: frozenset[Ponto] = frozenset()
    ) -> list[Nuvem]:
        """Sorteia as nuvens fora de `proibidas` e sem empilhar uma na outra.

        Sem isso uma nuvem pode nascer em cima da cobra — ou logo à frente
        dela — e a partida acaba antes de o jogador encostar no teclado.
        """
        if not self.tem_nuvens:
            return []

        diagonais = [Direcao(1, 1), Direcao(1, -1), Direcao(-1, 1), Direcao(-1, -1)]
        ocupadas = set(proibidas)
        nuvens: list[Nuvem] = []

        for _ in range(self.quantidade_nuvens):
            nuvem = self._sortear_nuvem(rng, ocupadas, diagonais)
            if nuvem is None:
                continue  # mapa apertado demais: joga com menos nuvens
            ocupadas |= nuvem.celulas()
            nuvens.append(nuvem)
        return nuvens

    def _sortear_nuvem(
        self,
        rng: random.Random,
        ocupadas: set[Ponto],
        diagonais: list[Direcao],
    ) -> Nuvem | None:
        for _ in range(200):
            canto = Ponto(rng.randrange(2, LARGURA - 4), rng.randrange(2, ALTURA - 4))
            candidata = Nuvem(canto=canto, direcao=rng.choice(diagonais))
            if not candidata.celulas() & ocupadas:
                return candidata
        return None

    def ajustar_posicao(self, p: Ponto) -> Ponto:
        """Onde a cabeça vai parar. Fora da grade sem wrap devolve o ponto cru,
        e quem chama trata como colisão."""
        return dar_a_volta(p) if self.atravessa_paredes else p


CLASSICO = Modo(
    id="classico",
    nome="Clássico",
    descricao="Bateu na parede, morreu. A velocidade sobe conforme você cresce.",
)

SEM_PAREDES = Modo(
    id="sem_paredes",
    nome="Sem paredes",
    descricao="Sai de um lado, entra pelo outro. Bom para treinar os poderes.",
    atravessa_paredes=True,
)

LABIRINTO = Modo(
    id="labirinto",
    nome="Labirinto",
    descricao="Blocos fixos no mapa, sorteados a cada partida.",
    tem_labirinto=True,
)

NUVENS = Modo(
    id="nuvens",
    nome="Nuvens",
    descricao="Quatro nuvens flutuam pelo mapa. O terreno muda sozinho.",
    atravessa_paredes=True,
    tem_nuvens=True,
    quantidade_nuvens=4,
)

TODOS = (CLASSICO, SEM_PAREDES, LABIRINTO, NUVENS)
POR_ID = {modo.id: modo for modo in TODOS}
