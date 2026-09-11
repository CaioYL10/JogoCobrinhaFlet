"""Traduz o estado do jogo em formas do Canvas.

As formas do cenário (grade e blocos do labirinto) não mudam durante a
partida, então são montadas uma vez só. A cada passo só as formas móveis são
refeitas — é o que mantém o jogo fluido mesmo com a cobra grande.
"""

import flet as ft
import flet.canvas as cv

from jogo.estado import EstadoJogo
from jogo.grade import ALTURA, CELULA, LARGURA, Ponto
from jogo.modos import Modo
from jogo.poderes import DEFINICOES
from jogo.skins import Skin

LARGURA_PX = LARGURA * CELULA
ALTURA_PX = ALTURA * CELULA

COR_FUNDO = "#0E1518"
COR_GRADE = "#18232880"
COR_OBSTACULO = "#37474F"
COR_BORDA_OBSTACULO = "#455A64"
COR_NUVEM = "#B0BEC5"
COR_FRUTA = "#EF5350"
COR_BRILHO_FRUTA = "#FF8A80"
COR_OLHO = "#FFFFFF"
COR_PUPILA = "#101010"


def _preencher(cor: str) -> ft.Paint:
    return ft.Paint(color=cor, style=ft.PaintingStyle.FILL)


def _contornar(cor: str, espessura: float = 1) -> ft.Paint:
    return ft.Paint(color=cor, style=ft.PaintingStyle.STROKE, stroke_width=espessura)


def _celula_livre(
    cx: float, cy: float, cor: str, margem: float = 1, raio: float = 4
) -> cv.Rect:
    """Quadrado numa posição de grade fracionária — é o que permite animar."""
    return cv.Rect(
        x=cx * CELULA + margem,
        y=cy * CELULA + margem,
        width=CELULA - margem * 2,
        height=CELULA - margem * 2,
        border_radius=raio,
        paint=_preencher(cor),
    )


def _celula(p: Ponto, cor: str, margem: float = 1, raio: float = 4) -> cv.Rect:
    return _celula_livre(p.x, p.y, cor, margem, raio)


def _entre(anterior: Ponto | None, atual: Ponto, fracao: float) -> tuple[float, float]:
    """Posição desenhada entre dois passos.

    Um salto maior que uma célula só acontece quando a cobra dá a volta pela
    borda no modo sem paredes. Aí não dá para deslizar — ela atravessaria a
    tela inteira — então o segmento aparece direto no destino.
    """
    if anterior is None:
        return float(atual.x), float(atual.y)
    dx = atual.x - anterior.x
    dy = atual.y - anterior.y
    if abs(dx) > 1 or abs(dy) > 1:
        return float(atual.x), float(atual.y)
    return anterior.x + dx * fracao, anterior.y + dy * fracao


def formas_do_cenario(estado: EstadoJogo, modo: Modo) -> list:
    """Grade de fundo e blocos fixos. Montado uma vez por partida."""
    formas: list = []

    grade = _contornar(COR_GRADE, 1)
    for x in range(1, LARGURA):
        formas.append(cv.Line(x * CELULA, 0, x * CELULA, ALTURA_PX, paint=grade))
    for y in range(1, ALTURA):
        formas.append(cv.Line(0, y * CELULA, LARGURA_PX, y * CELULA, paint=grade))

    for bloco in sorted(estado.obstaculos):
        formas.append(_celula(bloco, COR_OBSTACULO, margem=0, raio=2))
        formas.append(
            cv.Rect(
                x=bloco.x * CELULA,
                y=bloco.y * CELULA,
                width=CELULA,
                height=CELULA,
                border_radius=2,
                paint=_contornar(COR_BORDA_OBSTACULO, 1),
            )
        )

    return formas


def formas_moveis(estado: EstadoJogo, skin: Skin, fracao: float = 1.0) -> list:
    """Nuvens, fruta, item de poder e a cobra.

    `fracao` diz o quanto o passo atual já avançou, de 0 a 1. A cobra é
    desenhada nessa posição intermediária, o que faz o movimento deslizar em
    vez de pular de célula em célula.
    """
    formas: list = []
    formas += _nuvens(estado)
    formas += _fruta(estado)
    formas += _item_de_poder(estado)
    formas += _cobra(estado, skin, fracao)
    return formas


def _nuvens(estado: EstadoJogo) -> list:
    return [
        _celula(celula, COR_NUVEM, margem=0, raio=8)
        for celula in sorted(estado.celulas_das_nuvens())
    ]


def _fruta(estado: EstadoJogo) -> list:
    centro_x = estado.fruta.x * CELULA + CELULA / 2
    centro_y = estado.fruta.y * CELULA + CELULA / 2
    return [
        cv.Circle(centro_x, centro_y, CELULA / 2 - 2, paint=_preencher(COR_FRUTA)),
        cv.Circle(
            centro_x - 2, centro_y - 2, CELULA / 7, paint=_preencher(COR_BRILHO_FRUTA)
        ),
    ]


def _item_de_poder(estado: EstadoJogo) -> list:
    item = estado.item_poder
    if item is None:
        return []

    definicao = DEFINICOES[item.tipo]
    return [
        _celula(item.posicao, definicao.cor, margem=2, raio=6),
        cv.Text(
            x=item.posicao.x * CELULA + CELULA / 2,
            y=item.posicao.y * CELULA + 2,
            value=definicao.simbolo,
            text_align=ft.TextAlign.CENTER,
            alignment=ft.Alignment.TOP_CENTER,
            style=ft.TextStyle(
                size=13, weight=ft.FontWeight.BOLD, color="#10181C"
            ),
        ),
    ]


def _cobra(estado: EstadoJogo, skin: Skin, fracao: float) -> list:
    formas: list = []
    anterior = estado.cobra_anterior

    def posicao(indice: int) -> tuple[float, float]:
        de = anterior[indice] if indice < len(anterior) else None
        return _entre(de, estado.cobra[indice], fracao)

    # De trás para a frente, para a cabeça ficar por cima do pescoço.
    for indice in range(len(estado.cobra) - 1, 0, -1):
        cx, cy = posicao(indice)
        formas.append(_celula_livre(cx, cy, skin.cor_do_segmento(indice)))

    cabeca_x, cabeca_y = posicao(0)
    formas.append(_celula_livre(cabeca_x, cabeca_y, skin.cor_cabeca, margem=0, raio=6))
    formas += _olhos(estado, cabeca_x, cabeca_y)
    return formas


def _olhos(estado: EstadoJogo, cabeca_x: float, cabeca_y: float) -> list:
    """Dois olhos apontando para onde a cobra vai — ajuda a ler a direção."""
    centro_x = cabeca_x * CELULA + CELULA / 2
    centro_y = cabeca_y * CELULA + CELULA / 2
    direcao = estado.direcao

    afastamento = CELULA / 4
    avanco = CELULA / 5
    # Perpendicular à direção, para separar os dois olhos.
    perp_x, perp_y = -direcao.dy, direcao.dx

    formas = []
    for lado in (-1, 1):
        olho_x = centro_x + direcao.dx * avanco + perp_x * afastamento * lado
        olho_y = centro_y + direcao.dy * avanco + perp_y * afastamento * lado
        formas.append(cv.Circle(olho_x, olho_y, 2.6, paint=_preencher(COR_OLHO)))
        formas.append(
            cv.Circle(
                olho_x + direcao.dx * 1.1,
                olho_y + direcao.dy * 1.1,
                1.3,
                paint=_preencher(COR_PUPILA),
            )
        )
    return formas
