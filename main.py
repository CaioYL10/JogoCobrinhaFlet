"""Jogo da cobrinha em Flet.

Rode com:  python main.py
"""

import flet as ft

from jogo import progresso as prog
from jogo.modos import Modo
from jogo.skins import Skin
from ui.desenho import ALTURA_PX, COR_FUNDO, LARGURA_PX
from ui.tela_jogo import TelaJogo
from ui.tela_menu import TelaMenu

LARGURA_JANELA = LARGURA_PX + 76
# Altura do tabuleiro mais o placar, o espaço entre eles e a barra de título.
# Os poderes não entram na conta: eles flutuam sobre o tabuleiro.
ALTURA_JANELA = ALTURA_PX + 150


def _tamanho_da_tela() -> tuple[int, int] | None:
    """Medidas do monitor. Devolve None fora do Windows."""
    try:
        import ctypes

        usuario = ctypes.windll.user32
        usuario.SetProcessDPIAware()
        return usuario.GetSystemMetrics(0), usuario.GetSystemMetrics(1)
    except (AttributeError, OSError):
        return None


def _centralizar(page: ft.Page) -> None:
    """Põe a janela no meio do monitor.

    O `page.window.center()` do Flet 0.86 não move a janela — ela continua no
    canto — então a posição é calculada na mão. Se não der para medir a tela,
    deixa o sistema decidir onde abrir.
    """
    tela = _tamanho_da_tela()
    if tela is None:
        return
    largura_tela, altura_tela = tela
    page.window.left = max(0, (largura_tela - LARGURA_JANELA) / 2)
    page.window.top = max(0, (altura_tela - ALTURA_JANELA) / 2)


def main(page: ft.Page) -> None:
    page.title = "Jogo da Cobrinha"
    page.theme_mode = ft.ThemeMode.DARK
    page.window.width = LARGURA_JANELA
    page.window.height = ALTURA_JANELA
    page.window.min_width = LARGURA_JANELA
    page.window.min_height = ALTURA_JANELA
    _centralizar(page)

    progresso = prog.carregar()
    # O alinhamento central é o que mantém o tabuleiro no meio quando a janela
    # é maximizada ou vai a tela cheia: a raiz ocupa tudo, o conteúdo não.
    raiz = ft.Container(
        expand=True, bgcolor=COR_FUNDO, alignment=ft.Alignment.CENTER
    )
    page.add(raiz)

    # Guarda a tela ativa para saber a quem entregar as teclas. É uma lista de
    # um elemento só porque as funções abaixo precisam reatribuir o valor.
    atual: list[ft.Control | None] = [None]

    def trocar_para(tela: ft.Control) -> None:
        anterior = atual[0]
        if isinstance(anterior, TelaJogo):
            anterior.parar()
        atual[0] = tela
        raiz.content = tela
        raiz.update()

    def mostrar_menu() -> None:
        trocar_para(TelaMenu(progresso, ao_jogar=comecar_partida))

    def comecar_partida(modo: Modo, skin: Skin) -> None:
        progresso.modo_escolhido = modo.id
        progresso.skin_escolhida = skin.id
        prog.salvar(progresso)

        tela = TelaJogo(modo, skin, progresso, ao_voltar_ao_menu=mostrar_menu)
        trocar_para(tela)
        tela.iniciar()

    def ao_teclar(e: ft.KeyboardEvent) -> None:
        tela = atual[0]
        if isinstance(tela, TelaJogo):
            tela.tratar_tecla(e)

    page.on_keyboard_event = ao_teclar
    mostrar_menu()


if __name__ == "__main__":
    ft.run(main)
