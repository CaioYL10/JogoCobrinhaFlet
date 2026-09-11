# Jogo da Cobrinha

Cobrinha em Python com [Flet](https://flet.dev), com poderes, skins
desbloqueáveis e quatro modos de jogo.

## Como rodar

```
python main.py
```

Precisa do Flet instalado (`pip install flet`). Não precisa de mais nada.

## Como jogar

| Tecla | O que faz |
|---|---|
| Setas ou WASD | Move a cobra |
| Espaço | Pausa e despausa |
| Enter | Joga de novo, na tela de fim de jogo |
| Esc | Volta ao menu |

## Modos

- **Clássico** — bateu na parede, morreu. A velocidade sobe conforme você cresce.
- **Sem paredes** — sai de um lado, entra pelo outro.
- **Labirinto** — blocos fixos, sorteados a cada partida entre três plantas.
- **Nuvens** — quatro nuvens flutuam pelo mapa e ricocheteiam nas bordas.

## Poderes

Nascem no tabuleiro a cada quatro frutas. Vários podem ficar ativos ao mesmo
tempo, e cada um aparece como um marcador no canto do tabuleiro, com uma
barrinha mostrando quanto falta para acabar. Passe o mouse no marcador para
ver o nome completo e o que o poder faz.

| Poder | O que faz |
|---|---|
| Escudo | Absorve uma colisão e some |
| Ímã | Puxa a fruta uma célula na sua direção a cada passo |
| Câmera lenta | Dobra o tempo entre os passos |
| Pontos em dobro | Cada fruta vale 2× |
| Raio | Destrói a fruta atual; ela renasce longe |
| Encolher | Corta metade do corpo; o rabo volta quando acaba |

A duração é contada em **passos da cobra**, não em segundos. Assim um poder
rende o mesmo tanto de jogo mesmo com a câmera lenta ligada.

## Skins

Liberadas pelo seu recorde geral, guardado em `progresso.json`.

| Skin | Libera com |
|---|---|
| Verde clássica | início |
| Azul gelo | início |
| Laranja fogo | 50 |
| Roxo neon | 120 |
| Arco-íris | 250 |
| Dourada | 500 |

## Como o código está organizado

```
main.py      ponto de entrada; troca entre menu e jogo
jogo/        as regras — Python puro, nenhum import de flet
ui/          tudo que desenha e fala com o Flet
testes/      testes das regras, sem abrir janela
```

A divisão entre `jogo/` e `ui/` é a decisão mais importante do projeto.
Nenhum arquivo dentro de `jogo/` importa `flet`: o estado da partida é uma
estrutura de dados que sabe avançar um passo, e a pasta `ui/` lê esse estado e
desenha. Por isso os testes rodam em milissegundos sem abrir janela nenhuma —
e por isso dá para trocar a interface inteira sem tocar nas regras.

### Os arquivos

| Arquivo | Responsabilidade |
|---|---|
| `jogo/grade.py` | Tamanho do tabuleiro, coordenadas e direções |
| `jogo/estado.py` | A partida e a regra de um passo |
| `jogo/modos.py` | Os quatro modos, as plantas de labirinto e as nuvens |
| `jogo/poderes.py` | Definição dos seis poderes |
| `jogo/skins.py` | Catálogo de skins e regra de desbloqueio |
| `jogo/progresso.py` | Lê e grava `progresso.json` |
| `ui/desenho.py` | Converte o estado em formas do Canvas |
| `ui/tela_jogo.py` | Tabuleiro, placar e o laço que faz o tempo passar |
| `ui/tela_menu.py` | Escolha de modo e skin, recordes |

## Testes

```
python -m unittest discover -s testes -t .
```

São 65 testes e rodam em cerca de dois décimos de segundo, porque nenhum deles
abre janela. Usam o `unittest`, que já vem com o Python — não precisa
instalar pytest.

## Como o movimento fica suave

A cobra só muda de célula a cada 150 ms — sete vezes por segundo. Se a tela
fosse redesenhada junto com o passo, o movimento pareceria picotado.

Por isso o relógio do jogo é separado do relógio da tela: a lógica anda de
célula em célula no ritmo de sempre, mas o desenho acontece cerca de trinta
vezes por segundo, colocando a cobra nas posições intermediárias entre uma
célula e a próxima (`_entre`, em `ui/desenho.py`).

Para isso valer a pena, o tabuleiro é desenhado em dois canvas empilhados: a
grade e os blocos do labirinto ficam num canvas que nunca é reenviado, e só o
canvas de cima — cobra, fruta, nuvens — é atualizado a cada quadro.
