# Teste 11 — MiniCompilador escrito em MiniPar

Contrato: C-T11-v1 (`docs/02_CONTRATOS_TECNICOS.md` §3). Eixo B, cards `T11-01` → `T11-03`.

## Arquivos

| Arquivo | Conteúdo |
|---|---|
| `minicompilador.minipar` | O MiniCompilador: análise léxica, descida recursiva `expr → term → factor`, AST, TAC e avaliação, todos em MiniPar |
| `verificar_t11.py` | Compila pelo pipeline real (`main.py` → g++), executa o binário com cada entrada e compara o stdout com os oráculos |

## Como executar

Na raiz do repositório, com o `g++` C++20 no `PATH`:

```bash
python tests/2026_2/test11/verificar_t11.py
```

O binário fica em `output/minicompilador_t11.exe`. Para rodar uma entrada à mão:

```bash
python main.py tests/2026_2/test11/minicompilador.minipar minicompilador_t11
```

```bash
echo "((2+4)*7)-(5*4)" | output/minicompilador_t11.exe
```

## Estrutura do programa

Listas de strings estão fora do recorte (C-T11-v1 §3.4). Por isso a classe
`MiniCompilador` guarda tudo em listas numéricas paralelas:

- tokens: `tipos` (0 `NUMERO`, 1 `OPERADOR`, 2 `PARENTESE`), `inicios` e `tamanhos` do lexema na entrada;
- nós da AST: `ntok` (índice do token), `nesq` e `ndir` (índice dos filhos, `-1` para nenhum).

Todo texto impresso (tokens, nós, operandos do TAC) é recuperado da própria
entrada com `substr(e, inicio, tamanho)`. As regras do parser são métodos sem
retorno que deixam o nó construído em `ultimo`, e um erro é guardado em `erro`:
a primeira falha interrompe as fases seguintes, e a saída termina com a
mensagem `❌ Erro <fase>: ...`, sem resultado.

## Entradas rejeitadas

Menos unário, número decimal, zero à esquerda, identificador, `=`, divisão `/`,
caractere desconhecido, parênteses desbalanceados, tokens sobrando e entrada
vazia (C-T11-v1 §3.1). `#` inicia comentário até o fim da linha.
