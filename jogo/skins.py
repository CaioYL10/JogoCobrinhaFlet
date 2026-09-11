"""As skins da cobrinha e a regra de desbloqueio.

Cada skin guarda um ciclo de cores em vez de uma cor só. O desenho pergunta a
cor de cada segmento pela posição dele no corpo — é isso que deixa a arco-íris
funcionar sem precisar de nenhum código especial só para ela.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Skin:
    id: str
    nome: str
    cor_cabeca: str
    cores_corpo: tuple[str, ...]
    pontos_para_liberar: int
    descricao: str

    def cor_do_segmento(self, indice: int) -> str:
        return self.cores_corpo[indice % len(self.cores_corpo)]

    def liberada_com(self, recorde: int) -> bool:
        return recorde >= self.pontos_para_liberar


TODAS: tuple[Skin, ...] = (
    Skin(
        id="verde",
        nome="Verde clássica",
        cor_cabeca="#1B5E20",
        cores_corpo=("#43A047", "#388E3C"),
        pontos_para_liberar=0,
        descricao="A cobrinha de sempre.",
    ),
    Skin(
        id="gelo",
        nome="Azul gelo",
        cor_cabeca="#01579B",
        cores_corpo=("#039BE5", "#0288D1"),
        pontos_para_liberar=0,
        descricao="Fria e discreta.",
    ),
    Skin(
        id="fogo",
        nome="Laranja fogo",
        cor_cabeca="#BF360C",
        cores_corpo=("#FB8C00", "#F4511E"),
        pontos_para_liberar=50,
        descricao="Esquenta conforme você acerta.",
    ),
    Skin(
        id="neon",
        nome="Roxo neon",
        cor_cabeca="#4A148C",
        cores_corpo=("#AB47BC", "#8E24AA"),
        pontos_para_liberar=120,
        descricao="Fluorescente no escuro.",
    ),
    Skin(
        id="arco_iris",
        nome="Arco-íris",
        cor_cabeca="#D81B60",
        cores_corpo=(
            "#E53935",
            "#FB8C00",
            "#FDD835",
            "#43A047",
            "#1E88E5",
            "#8E24AA",
        ),
        pontos_para_liberar=250,
        descricao="Uma cor diferente a cada segmento.",
    ),
    Skin(
        id="dourada",
        nome="Dourada",
        cor_cabeca="#8D6E00",
        cores_corpo=("#FFD700", "#DAA520"),
        pontos_para_liberar=500,
        descricao="Para quem chegou longe de verdade.",
    ),
)

POR_ID = {skin.id: skin for skin in TODAS}
PADRAO = TODAS[0]


def liberadas(recorde: int) -> tuple[Skin, ...]:
    return tuple(skin for skin in TODAS if skin.liberada_com(recorde))


def bloqueadas(recorde: int) -> tuple[Skin, ...]:
    return tuple(skin for skin in TODAS if not skin.liberada_com(recorde))


def proxima_a_liberar(recorde: int) -> Skin | None:
    """A skin mais barata ainda bloqueada — vira a meta mostrada no menu."""
    restantes = bloqueadas(recorde)
    return min(restantes, key=lambda s: s.pontos_para_liberar) if restantes else None


def obter(skin_id: str) -> Skin:
    return POR_ID.get(skin_id, PADRAO)
