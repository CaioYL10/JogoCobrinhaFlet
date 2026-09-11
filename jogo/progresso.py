"""Recorde e skin escolhida, guardados num JSON ao lado do jogo.

O arquivo é escrito por nós mas pode ser apagado, editado à mão ou ficar pela
metade se o computador desligar na hora errada. Por isso a leitura nunca
confia no conteúdo: qualquer problema vira um progresso zerado em vez de um
erro que derruba o jogo.
"""

import json
from dataclasses import dataclass, field
from pathlib import Path

ARQUIVO = Path(__file__).resolve().parent.parent / "progresso.json"


@dataclass
class Progresso:
    recorde: int = 0
    recordes_por_modo: dict[str, int] = field(default_factory=dict)
    partidas: int = 0
    skin_escolhida: str = "verde"
    modo_escolhido: str = "classico"

    def registrar_partida(self, modo_id: str, pontos: int) -> bool:
        """Guarda o resultado. Devolve True se bateu o recorde geral."""
        self.partidas += 1
        self.modo_escolhido = modo_id
        anterior = self.recordes_por_modo.get(modo_id, 0)
        if pontos > anterior:
            self.recordes_por_modo[modo_id] = pontos

        if pontos > self.recorde:
            self.recorde = pontos
            return True
        return False

    def recorde_do_modo(self, modo_id: str) -> int:
        return self.recordes_por_modo.get(modo_id, 0)


def carregar(caminho: Path = ARQUIVO) -> Progresso:
    try:
        dados = json.loads(caminho.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return Progresso()

    if not isinstance(dados, dict):
        return Progresso()

    por_modo = dados.get("recordes_por_modo")
    return Progresso(
        recorde=_inteiro(dados.get("recorde")),
        recordes_por_modo={
            str(k): _inteiro(v) for k, v in por_modo.items()
        }
        if isinstance(por_modo, dict)
        else {},
        partidas=_inteiro(dados.get("partidas")),
        skin_escolhida=str(dados.get("skin_escolhida") or "verde"),
        modo_escolhido=str(dados.get("modo_escolhido") or "classico"),
    )


def salvar(progresso: Progresso, caminho: Path = ARQUIVO) -> None:
    dados = {
        "recorde": progresso.recorde,
        "recordes_por_modo": progresso.recordes_por_modo,
        "partidas": progresso.partidas,
        "skin_escolhida": progresso.skin_escolhida,
        "modo_escolhido": progresso.modo_escolhido,
    }
    caminho.write_text(
        json.dumps(dados, indent=2, ensure_ascii=False), encoding="utf-8"
    )


def _inteiro(valor: object) -> int:
    return valor if isinstance(valor, int) and not isinstance(valor, bool) else 0
