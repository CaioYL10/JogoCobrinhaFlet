"""A tela onde se joga: tabuleiro, placar e o laço que faz o tempo passar."""

import asyncio
import time
from typing import Callable

import flet as ft
import flet.canvas as cv

from jogo import progresso as prog
from jogo.estado import EstadoJogo
from jogo.grade import BAIXO, CIMA, DIREITA, ESQUERDA, Direcao
from jogo.modos import Modo
from jogo.poderes import DEFINICOES, PoderAtivo
from jogo.skins import Skin

from .desenho import (
    ALTURA_PX,
    COR_FUNDO,
    LARGURA_PX,
    formas_do_cenario,
    formas_moveis,
)

TECLAS: dict[str, Direcao] = {
    "Arrow Up": CIMA,
    "Arrow Down": BAIXO,
    "Arrow Left": ESQUERDA,
    "Arrow Right": DIREITA,
    "W": CIMA,
    "S": BAIXO,
    "A": ESQUERDA,
    "D": DIREITA,
}

# Alvo de 60 quadros por segundo. O Flet entrega perto de 30 na prática, o que
# já é quatro vezes mais fluido do que redesenhar só a cada passo da cobra.
SEGUNDOS_POR_QUADRO = 1 / 60

COR_PAINEL = "#131C20"
COR_TEXTO = "#E3ECEF"
COR_TEXTO_FRACO = "#7E9299"
COR_DESTAQUE = "#66DDA0"


class TelaJogo(ft.Container):
    def __init__(
        self,
        modo: Modo,
        skin: Skin,
        progresso: prog.Progresso,
        ao_voltar_ao_menu: Callable[[], None],
    ) -> None:
        self.modo = modo
        self.skin = skin
        self.progresso = progresso
        self.ao_voltar_ao_menu = ao_voltar_ao_menu

        self.estado = EstadoJogo(modo)
        self._cenario = formas_do_cenario(self.estado, modo)
        self._rodando = False
        self.pausado = False

        # Dois canvas empilhados de propósito: a grade e os blocos não mudam
        # durante a partida, então ficam num canvas que nunca é atualizado.
        # Só o de cima é reenviado a cada quadro — reenviar o cenário junto
        # custava quase o dobro do tempo e era o que travava a animação.
        self.canvas_cenario = cv.Canvas(
            shapes=self._cenario, width=LARGURA_PX, height=ALTURA_PX
        )
        self.canvas_moveis = cv.Canvas(
            shapes=formas_moveis(self.estado, skin),
            width=LARGURA_PX,
            height=ALTURA_PX,
        )

        self.texto_pontos = ft.Text("0", size=26, weight=ft.FontWeight.BOLD, color=COR_TEXTO)
        self.texto_recorde = ft.Text(
            self._rotulo_recorde(), size=11, color=COR_TEXTO_FRACO
        )
        self.faixa_poderes = ft.Row(spacing=8, wrap=True)
        self.sobreposicao = ft.Container(visible=False)

        super().__init__(
            bgcolor=COR_FUNDO,
            padding=12,
            # Ocupa a janela toda e centraliza o tabuleiro dentro dela, para
            # que maximizar ou ir a tela cheia não jogue o jogo para o canto.
            expand=True,
            alignment=ft.Alignment.CENTER,
            # Sem rolagem de propósito: a altura da janela é calculada para
            # caber tudo, e uma barra de rolagem aqui esconderia justamente a
            # faixa de poderes, que precisa estar sempre à vista.
            content=ft.Column(
                spacing=6,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    self._placar(),
                    ft.Stack(
                        width=LARGURA_PX,
                        height=ALTURA_PX,
                        controls=[
                            ft.Container(
                                content=self.canvas_cenario,
                                border_radius=10,
                                border=ft.Border.all(2, "#22323A"),
                            ),
                            self.canvas_moveis,
                            # Os poderes flutuam sobre o tabuleiro em vez de
                            # ocupar uma faixa embaixo dele. Ali eles ficavam
                            # para fora da janela quando a altura apertava;
                            # aqui estão sempre visíveis, porque o tabuleiro
                            # sempre está.
                            ft.Container(
                                content=self.faixa_poderes,
                                left=8,
                                top=8,
                                right=8,
                            ),
                            self.sobreposicao,
                        ],
                    ),
                ],
            ),
        )

    # ------------------------------------------------------------------
    # montagem do topo
    # ------------------------------------------------------------------

    def _placar(self) -> ft.Control:
        return ft.Container(
            width=LARGURA_PX,
            bgcolor=COR_PAINEL,
            padding=ft.Padding(14, 8, 14, 8),
            border_radius=10,
            content=ft.Row(
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.Column(
                        spacing=1,
                        controls=[
                            ft.Text(
                                self.modo.nome.upper(),
                                size=11,
                                weight=ft.FontWeight.BOLD,
                                color=COR_DESTAQUE,
                            ),
                            self.texto_recorde,
                            # As teclas moravam numa linha própria embaixo do
                            # tabuleiro; vieram para cá para o jogo caber na
                            # janela sem precisar rolar.
                            ft.Text(
                                "setas ou WASD  ·  espaço pausa  ·  Esc menu",
                                size=10,
                                color=COR_TEXTO_FRACO,
                            ),
                        ],
                    ),
                    ft.Row(
                        spacing=6,
                        vertical_alignment=ft.CrossAxisAlignment.END,
                        controls=[
                            self.texto_pontos,
                            ft.Text("pontos", size=11, color=COR_TEXTO_FRACO),
                        ],
                    ),
                ],
            ),
        )

    def _rotulo_recorde(self) -> str:
        return f"recorde neste modo: {self.progresso.recorde_do_modo(self.modo.id)}"

    # ------------------------------------------------------------------
    # ciclo de vida
    # ------------------------------------------------------------------

    def iniciar(self) -> None:
        """Chamado pelo main depois que a tela já está na página."""
        self._rodando = True
        self.page.run_task(self._laco)

    def parar(self) -> None:
        self._rodando = False

    async def _laco(self) -> None:
        """Separa o relógio do jogo do relógio da tela.

        A cobra só muda de célula a cada `intervalo_ms`, mas a tela é
        redesenhada muito mais vezes por segundo, desenhando a cobra no meio
        do caminho entre uma célula e a próxima. É isso que tira a impressão
        de que o jogo está pulando.
        """
        intervalo = self.estado.intervalo_ms() / 1000
        proximo_passo = time.perf_counter() + intervalo

        while self._rodando:
            agora = time.perf_counter()

            if self.pausado:
                # Enquanto pausado o relógio não corre, senão a cobra daria
                # vários passos de uma vez ao despausar.
                proximo_passo = agora + intervalo
                await asyncio.sleep(SEGUNDOS_POR_QUADRO)
                continue

            if agora >= proximo_passo:
                resultado = self.estado.passo()
                intervalo = self.estado.intervalo_ms() / 1000
                proximo_passo = agora + intervalo
                self._atualizar_placar()

                if resultado.morreu:
                    self._desenhar_quadro(1.0)
                    self._terminar()
                    return

            avanco = 1 - (proximo_passo - agora) / intervalo
            self._desenhar_quadro(min(1.0, max(0.0, avanco)))
            await asyncio.sleep(SEGUNDOS_POR_QUADRO)

    def _desenhar_quadro(self, avanco: float) -> None:
        """Redesenha só o que se move. Roda dezenas de vezes por segundo."""
        self.canvas_moveis.shapes = formas_moveis(self.estado, self.skin, avanco)
        self.canvas_moveis.update()

    def _atualizar_placar(self) -> None:
        """Pontos e poderes mudam no ritmo do jogo, não no ritmo da tela."""
        self.texto_pontos.value = str(self.estado.pontos)
        self.texto_pontos.update()
        self.faixa_poderes.controls = [
            self._chip_de_poder(ativo) for ativo in self.estado.poderes.values()
        ]
        self.faixa_poderes.update()

    def _chip_de_poder(self, ativo: PoderAtivo) -> ft.Control:
        definicao = DEFINICOES[ativo.tipo]
        conteudo: list[ft.Control] = [
            ft.Text(
                definicao.nome_curto,
                size=11,
                weight=ft.FontWeight.BOLD,
                color=definicao.cor,
            )
        ]
        if not ativo.permanente:
            conteudo.append(
                ft.ProgressBar(
                    value=ativo.fracao_restante(),
                    width=54,
                    height=3,
                    color=definicao.cor,
                    bgcolor="#24343B",
                )
            )

        return ft.Container(
            padding=ft.Padding(8, 4, 8, 4),
            # Quase opaco: o chip fica por cima do tabuleiro, e a cobra
            # precisa continuar visível se passar por baixo dele.
            bgcolor="#0E1518E6",
            border_radius=8,
            border=ft.Border.all(1, definicao.cor),
            tooltip=f"{definicao.nome}: {definicao.descricao}",
            content=ft.Column(spacing=3, controls=conteudo),
        )

    # ------------------------------------------------------------------
    # fim de partida e pausa
    # ------------------------------------------------------------------

    def _terminar(self) -> None:
        self._rodando = False
        bateu_recorde = self.progresso.registrar_partida(
            self.modo.id, self.estado.pontos
        )
        self.progresso.skin_escolhida = self.skin.id
        self.progresso.modo_escolhido = self.modo.id
        prog.salvar(self.progresso)

        self.texto_recorde.value = self._rotulo_recorde()
        self._mostrar_sobreposicao(
            titulo="Recorde!" if bateu_recorde else "Fim de jogo",
            cor_titulo=COR_DESTAQUE if bateu_recorde else COR_TEXTO,
            detalhe=f"{self.estado.pontos} pontos em {self.modo.nome.lower()}",
            botoes=[
                ft.ElevatedButton(content="Jogar de novo", on_click=self._reiniciar),
                ft.OutlinedButton(
                    content="Voltar ao menu", on_click=lambda _: self.ao_voltar_ao_menu()
                ),
            ],
        )

    def _mostrar_sobreposicao(
        self, titulo: str, cor_titulo: str, detalhe: str, botoes: list[ft.Control]
    ) -> None:
        self.sobreposicao.width = LARGURA_PX
        self.sobreposicao.height = ALTURA_PX
        self.sobreposicao.bgcolor = "#0B1114E6"
        self.sobreposicao.border_radius = 10
        self.sobreposicao.alignment = ft.Alignment.CENTER
        self.sobreposicao.visible = True
        self.sobreposicao.content = ft.Column(
            spacing=10,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            alignment=ft.MainAxisAlignment.CENTER,
            controls=[
                ft.Text(titulo, size=34, weight=ft.FontWeight.BOLD, color=cor_titulo),
                ft.Text(detalhe, size=14, color=COR_TEXTO_FRACO),
                ft.Row(
                    spacing=10,
                    alignment=ft.MainAxisAlignment.CENTER,
                    controls=botoes,
                ),
            ],
        )
        self.update()

    def _esconder_sobreposicao(self) -> None:
        self.sobreposicao.visible = False
        self.update()

    def _reiniciar(self, _=None) -> None:
        self.estado = EstadoJogo(self.modo)
        # O labirinto é sorteado de novo a cada partida, então o cenário
        # também precisa ser redesenhado — é a única hora em que isso ocorre.
        self._cenario = formas_do_cenario(self.estado, self.modo)
        self.canvas_cenario.shapes = self._cenario
        self.canvas_cenario.update()

        self.pausado = False
        self._esconder_sobreposicao()
        self._atualizar_placar()
        self._desenhar_quadro(1.0)
        self._rodando = True
        self.page.run_task(self._laco)

    def _alternar_pausa(self) -> None:
        if not self.estado.viva:
            return
        self.pausado = not self.pausado
        if self.pausado:
            self._mostrar_sobreposicao(
                titulo="Pausado",
                cor_titulo=COR_TEXTO,
                detalhe="espaço para continuar",
                botoes=[],
            )
        else:
            self._esconder_sobreposicao()

    # ------------------------------------------------------------------
    # teclado
    # ------------------------------------------------------------------

    def tratar_tecla(self, e: ft.KeyboardEvent) -> None:
        if e.key == "Escape":
            self.ao_voltar_ao_menu()
            return
        if e.key == " ":
            self._alternar_pausa()
            return
        if e.key == "Enter" and not self.estado.viva:
            self._reiniciar()
            return

        direcao = TECLAS.get(e.key)
        if direcao is not None and not self.pausado:
            self.estado.girar(direcao)
