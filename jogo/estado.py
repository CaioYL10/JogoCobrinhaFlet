"""O estado da partida e a regra de um passo.

Esta classe é o jogo inteiro. Ela não sabe desenhar nada: só sabe guardar onde
tudo está e avançar um passo. Quem desenha é a pasta `ui`.
"""

import random
from collections import deque
from dataclasses import dataclass

from .grade import (
    ACELERACAO_POR_FRUTA_MS,
    ALTURA,
    DIREITA,
    INTERVALO_INICIAL_MS,
    INTERVALO_MINIMO_MS,
    LARGURA,
    Direcao,
    Ponto,
    dar_a_volta,
    dentro_da_grade,
    sao_opostas,
)
from .modos import Modo
from .poderes import (
    DEFINICOES,
    FRUTAS_ENTRE_ITENS,
    INSTANTANEO,
    SORTEAVEIS,
    PoderAtivo,
    TipoPoder,
)

TAMANHO_INICIAL = 3
TAMANHO_MINIMO = 3
PASSOS_ENTRE_MOVIMENTOS_DE_NUVEM = 3
DISTANCIA_DO_RAIO = 6


@dataclass
class ResultadoPasso:
    """O que aconteceu no passo — a tela usa isto para efeitos e som."""

    comeu: bool = False
    poder_pego: TipoPoder | None = None
    escudo_salvou: bool = False
    morreu: bool = False


@dataclass
class ItemPoder:
    posicao: Ponto
    tipo: TipoPoder


class EstadoJogo:
    def __init__(self, modo: Modo, semente: int | None = None) -> None:
        self.modo = modo
        self.rng = random.Random(semente)

        centro = Ponto(LARGURA // 2, ALTURA // 2)
        self.cobra: deque[Ponto] = deque(
            Ponto(centro.x - i, centro.y) for i in range(TAMANHO_INICIAL)
        )
        self.direcao: Direcao = DIREITA
        self._proxima_direcao: Direcao = DIREITA
        # Onde a cobra estava antes do último passo. A tela usa isso para
        # desenhar as posições intermediárias e o movimento sair deslizando
        # em vez de pulando de célula em célula.
        self.cobra_anterior: list[Ponto] = list(self.cobra)

        # Onde a cobra nasce e para onde ela vai correr nos primeiros passos:
        # nada pode ocupar essas células, senão a partida acaba antes de o
        # jogador encostar no teclado.
        zona_inicial = frozenset(
            set(self.cobra) | {Ponto(centro.x + i, centro.y) for i in range(1, 6)}
        )

        self.obstaculos = modo.criar_obstaculos(self.rng) - zona_inicial
        self.nuvens = modo.criar_nuvens(self.rng, zona_inicial)
        self._passos_ate_mover_nuvens = PASSOS_ENTRE_MOVIMENTOS_DE_NUVEM

        self.pontos = 0
        self.frutas_comidas = 0
        self.viva = True
        self.poderes: dict[TipoPoder, PoderAtivo] = {}
        self.item_poder: ItemPoder | None = None

        self._cauda_guardada = 0
        self._devolver_cauda = 0

        self.fruta = self._sortear_celula_livre()

    # ------------------------------------------------------------------
    # consultas
    # ------------------------------------------------------------------

    @property
    def cabeca(self) -> Ponto:
        return self.cobra[0]

    def celulas_das_nuvens(self) -> set[Ponto]:
        celulas: set[Ponto] = set()
        for nuvem in self.nuvens:
            celulas |= nuvem.celulas()
        return celulas

    def intervalo_ms(self) -> int:
        """Quanto esperar até o próximo passo. Cai conforme a cobra cresce."""
        intervalo = max(
            INTERVALO_MINIMO_MS,
            INTERVALO_INICIAL_MS - self.frutas_comidas * ACELERACAO_POR_FRUTA_MS,
        )
        if TipoPoder.LENTIDAO in self.poderes:
            intervalo *= 2
        return intervalo

    def tem_poder(self, tipo: TipoPoder) -> bool:
        return tipo in self.poderes

    # ------------------------------------------------------------------
    # comandos
    # ------------------------------------------------------------------

    def girar(self, nova: Direcao) -> None:
        """Guarda a direção para o próximo passo.

        A comparação é com a direção do último passo aplicado, e não com a que
        já está na fila. Sem isso, duas teclas no mesmo intervalo conseguem
        virar 180 graus e matar a cobra no próprio pescoço.
        """
        if not sao_opostas(nova, self.direcao):
            self._proxima_direcao = nova

    def passo(self) -> ResultadoPasso:
        if not self.viva:
            return ResultadoPasso(morreu=True)

        self.cobra_anterior = list(self.cobra)
        self.direcao = self._proxima_direcao
        destino = self.cabeca.somar(self.direcao)

        if self.modo.atravessa_paredes:
            destino = dar_a_volta(destino)
        elif not dentro_da_grade(destino):
            return self._sofrer_colisao()

        self._mover_nuvens()

        vai_comer = destino == self.fruta
        vai_crescer = vai_comer or self._devolver_cauda > 0
        # Quando não cresce, o rabo sai neste mesmo passo — então a célula dele
        # está livre para a cabeça ocupar.
        corpo = set(self.cobra) if vai_crescer else set(list(self.cobra)[:-1])

        if destino in corpo or destino in self.obstaculos:
            return self._sofrer_colisao()
        if destino in self.celulas_das_nuvens():
            return self._sofrer_colisao()

        self.cobra.appendleft(destino)
        resultado = ResultadoPasso()

        if vai_comer:
            self._comer()
            resultado.comeu = True
        elif self._devolver_cauda > 0:
            self._devolver_cauda -= 1  # cresce um: o rabo não sai
        else:
            self.cobra.pop()

        if self.item_poder is not None and destino == self.item_poder.posicao:
            tipo = self.item_poder.tipo
            self.item_poder = None
            self._ativar(tipo)
            resultado.poder_pego = tipo

        if TipoPoder.IMA in self.poderes:
            self._atrair_fruta()

        self._envelhecer_poderes()
        return resultado

    # ------------------------------------------------------------------
    # internos
    # ------------------------------------------------------------------

    def _sofrer_colisao(self) -> ResultadoPasso:
        """O escudo gasta a si mesmo e a cobra fica parada este passo — o que
        dá ao jogador um intervalo para virar antes de bater de novo."""
        if TipoPoder.ESCUDO in self.poderes:
            del self.poderes[TipoPoder.ESCUDO]
            return ResultadoPasso(escudo_salvou=True)
        self.viva = False
        return ResultadoPasso(morreu=True)

    def _comer(self) -> None:
        self.frutas_comidas += 1
        self.pontos += 2 if TipoPoder.DOBRO in self.poderes else 1
        self.fruta = self._sortear_celula_livre()
        if (
            self.item_poder is None
            and self.frutas_comidas % FRUTAS_ENTRE_ITENS == 0
        ):
            self.item_poder = ItemPoder(
                posicao=self._sortear_celula_livre(),
                tipo=self.rng.choice(SORTEAVEIS),
            )

    def _ativar(self, tipo: TipoPoder) -> None:
        definicao = DEFINICOES[tipo]

        if tipo == TipoPoder.RAIO:
            self.fruta = self._sortear_celula_livre(longe_de=self.cabeca)
            return

        if tipo == TipoPoder.ENCOLHER:
            cortaveis = max(0, len(self.cobra) - TAMANHO_MINIMO)
            quantos = min(len(self.cobra) // 2, cortaveis)
            for _ in range(quantos):
                self.cobra.pop()
            self._cauda_guardada += quantos

        if definicao.duracao != INSTANTANEO:
            self.poderes[tipo] = PoderAtivo(tipo=tipo, restante=definicao.duracao)

    def _envelhecer_poderes(self) -> None:
        expirados = []
        for tipo, ativo in self.poderes.items():
            if ativo.permanente:
                continue
            ativo.restante -= 1
            if ativo.restante <= 0:
                expirados.append(tipo)

        for tipo in expirados:
            del self.poderes[tipo]
            if tipo == TipoPoder.ENCOLHER:
                self._devolver_cauda += self._cauda_guardada
                self._cauda_guardada = 0

    def _mover_nuvens(self) -> None:
        if not self.nuvens:
            return
        self._passos_ate_mover_nuvens -= 1
        if self._passos_ate_mover_nuvens > 0:
            return
        self._passos_ate_mover_nuvens = PASSOS_ENTRE_MOVIMENTOS_DE_NUVEM
        for nuvem in self.nuvens:
            nuvem.mover()

    def _atrair_fruta(self) -> None:
        """Puxa a fruta uma célula pelo eixo em que ela está mais longe."""
        dx = self.cabeca.x - self.fruta.x
        dy = self.cabeca.y - self.fruta.y
        if dx == 0 and dy == 0:
            return
        if abs(dx) >= abs(dy):
            passo = Ponto(self.fruta.x + (1 if dx > 0 else -1), self.fruta.y)
        else:
            passo = Ponto(self.fruta.x, self.fruta.y + (1 if dy > 0 else -1))
        if passo not in self._celulas_ocupadas():
            self.fruta = passo

    def _celulas_ocupadas(self) -> set[Ponto]:
        ocupadas = set(self.cobra) | self.obstaculos | self.celulas_das_nuvens()
        if self.item_poder is not None:
            ocupadas.add(self.item_poder.posicao)
        return ocupadas

    def _sortear_celula_livre(self, longe_de: Ponto | None = None) -> Ponto:
        ocupadas = self._celulas_ocupadas()
        livres = [
            Ponto(x, y)
            for x in range(LARGURA)
            for y in range(ALTURA)
            if Ponto(x, y) not in ocupadas
        ]
        if not livres:
            # Tabuleiro cheio: a partida acabou de qualquer jeito.
            return self.cabeca

        if longe_de is not None:
            distantes = [
                p
                for p in livres
                if abs(p.x - longe_de.x) + abs(p.y - longe_de.y) >= DISTANCIA_DO_RAIO
            ]
            if distantes:
                livres = distantes

        return self.rng.choice(livres)
