"""Os seis poderes.

A duração é contada em PASSOS da cobra, não em segundos. Isso é de propósito:
o passo é o relógio do jogo, então um poder dura o mesmo tanto de jogo
independentemente da velocidade — e os testes não precisam esperar tempo real.
Em velocidade normal (150 ms por passo), 50 passos dão uns 7 segundos.
"""

from dataclasses import dataclass
from enum import Enum

ATE_USAR = -1
INSTANTANEO = 0


class TipoPoder(Enum):
    ESCUDO = "escudo"
    IMA = "ima"
    LENTIDAO = "lentidao"
    DOBRO = "dobro"
    RAIO = "raio"
    ENCOLHER = "encolher"


@dataclass(frozen=True)
class DefinicaoPoder:
    tipo: TipoPoder
    nome: str
    simbolo: str
    cor: str
    duracao: int
    descricao: str
    # Usado no marcador que fica sobre o tabuleiro, onde a largura é curta:
    # com os nomes inteiros, cinco poderes ativos cobriam o topo do jogo.
    nome_curto: str = ""

    def __post_init__(self) -> None:
        if not self.nome_curto:
            object.__setattr__(self, "nome_curto", self.nome)


DEFINICOES: dict[TipoPoder, DefinicaoPoder] = {
    TipoPoder.ESCUDO: DefinicaoPoder(
        TipoPoder.ESCUDO,
        "Escudo",
        "E",
        "#4FC3F7",
        ATE_USAR,
        "Absorve uma colisão. Some depois de salvar você uma vez.",
    ),
    TipoPoder.IMA: DefinicaoPoder(
        TipoPoder.IMA,
        "Ímã",
        "I",
        "#EC407A",
        50,
        "Puxa a fruta uma célula na sua direção a cada passo.",
    ),
    TipoPoder.LENTIDAO: DefinicaoPoder(
        TipoPoder.LENTIDAO,
        "Câmera lenta",
        "L",
        "#AB7DF6",
        40,
        "Dobra o tempo entre os passos. Dá fôlego quando a cobra está grande.",
        nome_curto="Lenta",
    ),
    TipoPoder.DOBRO: DefinicaoPoder(
        TipoPoder.DOBRO,
        "Pontos em dobro",
        "2",
        "#FFC107",
        60,
        "Cada fruta vale o dobro enquanto durar.",
        nome_curto="Dobro",
    ),
    TipoPoder.RAIO: DefinicaoPoder(
        TipoPoder.RAIO,
        "Raio",
        "R",
        "#FFEE58",
        INSTANTANEO,
        "Destrói a fruta atual; ela renasce longe da cobra.",
    ),
    TipoPoder.ENCOLHER: DefinicaoPoder(
        TipoPoder.ENCOLHER,
        "Encolher",
        "C",
        "#66DDA0",
        50,
        "Corta metade do corpo. O rabo volta a crescer quando acaba.",
    ),
}

SORTEAVEIS = tuple(DEFINICOES)

# A cada quantas frutas comidas nasce um item de poder no tabuleiro.
FRUTAS_ENTRE_ITENS = 4


@dataclass
class PoderAtivo:
    """Um poder em vigor. `restante` conta passos; ATE_USAR nunca decrementa."""

    tipo: TipoPoder
    restante: int

    @property
    def definicao(self) -> DefinicaoPoder:
        return DEFINICOES[self.tipo]

    @property
    def permanente(self) -> bool:
        return self.restante == ATE_USAR

    def fracao_restante(self) -> float:
        """Quanto sobrou, de 0.0 a 1.0 — para desenhar a barrinha no HUD."""
        if self.permanente:
            return 1.0
        total = self.definicao.duracao
        return self.restante / total if total > 0 else 0.0
