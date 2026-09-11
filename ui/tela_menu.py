"""Menu: escolher modo e skin, ver recordes e o que cada poder faz."""

from typing import Callable

import flet as ft

from jogo import modos, skins
from jogo import progresso as prog
from jogo.modos import Modo
from jogo.poderes import DEFINICOES, TipoPoder
from jogo.skins import Skin

from .desenho import COR_FUNDO, LARGURA_PX

COR_PAINEL = "#131C20"
COR_PAINEL_ATIVO = "#1B2C33"
COR_TEXTO = "#E3ECEF"
COR_TEXTO_FRACO = "#7E9299"
COR_DESTAQUE = "#66DDA0"
COR_BLOQUEADO = "#3A4A50"


class TelaMenu(ft.Container):
    def __init__(
        self,
        progresso: prog.Progresso,
        ao_jogar: Callable[[Modo, Skin], None],
    ) -> None:
        self.progresso = progresso
        self.ao_jogar = ao_jogar

        self.modo_escolhido = modos.POR_ID.get(
            progresso.modo_escolhido, modos.CLASSICO
        )
        escolhida = skins.obter(progresso.skin_escolhida)
        self.skin_escolhida = (
            escolhida if escolhida.liberada_com(progresso.recorde) else skins.PADRAO
        )

        self.linha_modos = ft.Column(spacing=8)
        self.linha_skins = ft.Row(spacing=10, wrap=True)
        self.texto_descricao_skin = ft.Text(size=12, color=COR_TEXTO_FRACO)

        super().__init__(
            bgcolor=COR_FUNDO,
            padding=20,
            # O menu é mais alto que a janela, então ele ocupa toda a altura e
            # rola por dentro — centralizar na vertical cortaria o conteúdo.
            expand=True,
            alignment=ft.Alignment.TOP_CENTER,
            content=ft.Column(
                spacing=18,
                scroll=ft.ScrollMode.AUTO,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    self._cabecalho(),
                    self._secao("Modo de jogo", self.linha_modos),
                    self._secao(
                        "Skin",
                        ft.Column(
                            spacing=8,
                            controls=[self.linha_skins, self.texto_descricao_skin],
                        ),
                    ),
                    self._secao("Poderes", self._lista_de_poderes()),
                    ft.ElevatedButton(
                        content="Jogar",
                        width=LARGURA_PX,
                        on_click=self._jogar,
                        style=ft.ButtonStyle(
                            bgcolor=COR_DESTAQUE,
                            color="#0B1114",
                            padding=ft.Padding(0, 18, 0, 18),
                        ),
                    ),
                ],
            ),
        )

        self._montar_modos()
        self._montar_skins()

    # ------------------------------------------------------------------
    # blocos
    # ------------------------------------------------------------------

    def _cabecalho(self) -> ft.Control:
        proxima = skins.proxima_a_liberar(self.progresso.recorde)
        if proxima is None:
            meta = "todas as skins liberadas"
        else:
            faltam = proxima.pontos_para_liberar - self.progresso.recorde
            meta = f"faltam {faltam} pontos para a skin {proxima.nome.lower()}"

        return ft.Container(
            width=LARGURA_PX,
            padding=ft.Padding(18, 16, 18, 16),
            bgcolor=COR_PAINEL,
            border_radius=12,
            content=ft.Column(
                spacing=4,
                controls=[
                    ft.Text(
                        "Jogo da Cobrinha",
                        size=28,
                        weight=ft.FontWeight.BOLD,
                        color=COR_TEXTO,
                    ),
                    ft.Row(
                        spacing=16,
                        controls=[
                            ft.Text(
                                f"recorde {self.progresso.recorde}",
                                size=13,
                                color=COR_DESTAQUE,
                                weight=ft.FontWeight.BOLD,
                            ),
                            ft.Text(
                                f"{self.progresso.partidas} partidas",
                                size=13,
                                color=COR_TEXTO_FRACO,
                            ),
                        ],
                    ),
                    ft.Text(meta, size=12, color=COR_TEXTO_FRACO),
                ],
            ),
        )

    def _secao(self, titulo: str, conteudo: ft.Control) -> ft.Control:
        return ft.Container(
            width=LARGURA_PX,
            content=ft.Column(
                spacing=8,
                controls=[
                    ft.Text(
                        titulo.upper(),
                        size=11,
                        weight=ft.FontWeight.BOLD,
                        color=COR_TEXTO_FRACO,
                    ),
                    conteudo,
                ],
            ),
        )

    def _lista_de_poderes(self) -> ft.Control:
        linhas = []
        for tipo in TipoPoder:
            definicao = DEFINICOES[tipo]
            linhas.append(
                ft.Row(
                    spacing=10,
                    vertical_alignment=ft.CrossAxisAlignment.START,
                    controls=[
                        ft.Container(
                            width=24,
                            height=24,
                            bgcolor=definicao.cor,
                            border_radius=6,
                            alignment=ft.Alignment.CENTER,
                            content=ft.Text(
                                definicao.simbolo,
                                size=12,
                                weight=ft.FontWeight.BOLD,
                                color="#10181C",
                            ),
                        ),
                        ft.Column(
                            spacing=0,
                            expand=True,
                            controls=[
                                ft.Text(
                                    definicao.nome,
                                    size=13,
                                    weight=ft.FontWeight.BOLD,
                                    color=COR_TEXTO,
                                ),
                                ft.Text(
                                    definicao.descricao, size=12, color=COR_TEXTO_FRACO
                                ),
                            ],
                        ),
                    ],
                )
            )
        return ft.Column(spacing=10, controls=linhas)

    # ------------------------------------------------------------------
    # seleção de modo
    # ------------------------------------------------------------------

    def _montar_modos(self) -> None:
        self.linha_modos.controls = [
            self._cartao_de_modo(modo) for modo in modos.TODOS
        ]

    def _cartao_de_modo(self, modo: Modo) -> ft.Control:
        ativo = modo.id == self.modo_escolhido.id
        recorde = self.progresso.recorde_do_modo(modo.id)

        return ft.Container(
            padding=ft.Padding(14, 12, 14, 12),
            bgcolor=COR_PAINEL_ATIVO if ativo else COR_PAINEL,
            border_radius=10,
            border=ft.Border.all(1, COR_DESTAQUE if ativo else "#1F2E34"),
            on_click=lambda _, m=modo: self._escolher_modo(m),
            content=ft.Row(
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.Column(
                        spacing=2,
                        expand=True,
                        controls=[
                            ft.Text(
                                modo.nome,
                                size=14,
                                weight=ft.FontWeight.BOLD,
                                color=COR_DESTAQUE if ativo else COR_TEXTO,
                            ),
                            ft.Text(modo.descricao, size=12, color=COR_TEXTO_FRACO),
                        ],
                    ),
                    ft.Text(
                        f"{recorde}" if recorde else "—",
                        size=16,
                        weight=ft.FontWeight.BOLD,
                        color=COR_TEXTO_FRACO,
                    ),
                ],
            ),
        )

    def _escolher_modo(self, modo: Modo) -> None:
        self.modo_escolhido = modo
        self._montar_modos()
        self.update()

    # ------------------------------------------------------------------
    # seleção de skin
    # ------------------------------------------------------------------

    def _montar_skins(self) -> None:
        self.linha_skins.controls = [
            self._botao_de_skin(skin) for skin in skins.TODAS
        ]
        self.texto_descricao_skin.value = self._descricao_da_skin()

    def _descricao_da_skin(self) -> str:
        return f"{self.skin_escolhida.nome} — {self.skin_escolhida.descricao}"

    def _botao_de_skin(self, skin: Skin) -> ft.Control:
        liberada = skin.liberada_com(self.progresso.recorde)
        escolhida = skin.id == self.skin_escolhida.id

        if liberada:
            amostra = ft.Row(
                spacing=2,
                alignment=ft.MainAxisAlignment.CENTER,
                controls=[
                    ft.Container(width=9, height=26, bgcolor=skin.cor_cabeca, border_radius=3),
                    *[
                        ft.Container(
                            width=9,
                            height=26,
                            bgcolor=skin.cor_do_segmento(i),
                            border_radius=3,
                        )
                        for i in range(3)
                    ],
                ],
            )
            legenda = skin.nome
        else:
            amostra = ft.Row(
                spacing=2,
                alignment=ft.MainAxisAlignment.CENTER,
                controls=[
                    ft.Container(width=9, height=26, bgcolor=COR_BLOQUEADO, border_radius=3)
                    for _ in range(4)
                ],
            )
            legenda = f"{skin.pontos_para_liberar} pts"

        return ft.Container(
            padding=ft.Padding(10, 8, 10, 8),
            bgcolor=COR_PAINEL_ATIVO if escolhida else COR_PAINEL,
            border_radius=10,
            border=ft.Border.all(1, COR_DESTAQUE if escolhida else "#1F2E34"),
            opacity=1.0 if liberada else 0.55,
            on_click=(lambda _, s=skin: self._escolher_skin(s)) if liberada else None,
            content=ft.Column(
                spacing=6,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    amostra,
                    ft.Text(
                        legenda,
                        size=10,
                        color=COR_TEXTO if liberada else COR_TEXTO_FRACO,
                    ),
                ],
            ),
        )

    def _escolher_skin(self, skin: Skin) -> None:
        self.skin_escolhida = skin
        self._montar_skins()
        self.update()

    # ------------------------------------------------------------------

    def _jogar(self, _=None) -> None:
        self.ao_jogar(self.modo_escolhido, self.skin_escolhida)
