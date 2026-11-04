# Teste 11 — MiniCompilador escrito em MiniPar

Contrato: C-T11-v1 (`docs/02_CONTRATOS_TECNICOS.md` §3). Eixo B, cards `T11-01` → `T11-03`.

## Arquivos

| Arquivo | Conteúdo |
|---|---|
| `minicompilador.minipar` | O MiniCompilador: análise léxica, descida recursiva `expr → term → factor`, AST, TAC, verificação semântica, Assembly ARMv7, tabela de símbolos e avaliação, todos em MiniPar |
| `verificar_t11.py` | Compila pelo pipeline real (`main.py` → g++), executa o binário com cada entrada e compara o stdout com os oráculos de C-T11-v1 §3.12 e o `.arm` com o de referência |
| `extrair_arm.py` | Copia o bloco do Assembly do stdout para um `.arm` (regras de C-T11-v1 §3.6 item 2); não analisa nem reescreve o Assembly |
| `arm/casoN.arm`, `arm/casoN.stdout.txt` | `.arm` dos três casos obrigatórios e o stdout completo de onde cada um foi extraído |
| `evidencias/` | Execução dos `.arm` no CPUlator (T11-03): ambiente, procedimento, registradores finais, SHA-256 e capturas de tela |

## Como executar

Na raiz do repositório, com o `g++` C++20 no `PATH`:

```bash
python tests/2026_2/test11/verificar_t11.py
```

Para regenerar os três `.arm` (o `verificar_t11.py` falha se os arquivos de
`arm/` divergirem da extração atual):

```bash
python tests/2026_2/test11/extrair_arm.py --casos tests/2026_2/test11/arm
```

Os arquivos de `arm/` são gravados em UTF-8 com fim de linha LF e marcados `-text` no
`.gitattributes`, para que o SHA-256 seja o mesmo em qualquer checkout.

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

Fases, na ordem: léxica → sintática → semântica → avaliação. Só depois que
todas aceitam a entrada o programa imprime AST, TAC, Assembly, tabela de
símbolos e resultado, no formato exato da referência (C-T11-v1 §3.12).

- **Tabela de símbolos:** constantes sem repetição (`svals`/`stoks`), em ordem
  crescente de valor, por inserção ordenada.
- **Assembly:** pós-ordem, um registrador por nó com contador global sem
  reaproveitamento, mnemônico no campo de 6 colunas, comentário com a expressão
  totalmente parentizada e `b .` no fim (C-T11-v1 §3.6 item 3). O resultado
  fica no registrador da raiz, `r8` nos três casos obrigatórios.

## Entradas rejeitadas

Menos unário, número decimal, zero à esquerda, identificador, `=`, divisão `/`,
caractere desconhecido, parênteses desbalanceados, tokens sobrando e entrada
vazia (C-T11-v1 §3.1). `#` inicia comentário até o fim da linha.

Desvios da referência onde ela geraria Assembly errado (C-T11-v1 §3.6 item 4):

| Situação | T11 |
|---|---|
| constante de 256 a 2147483647 | `LDR    rN, =k` em vez de `MOV` |
| constante acima de 2147483647 | rejeitada no léxico |
| AST com mais de 13 nós | rejeitada no semântico (só há `r0`–`r12` livres) |
| resultado intermediário fora de 32 bits com sinal | rejeitado no semântico: o ARM calcularia o valor truncado e divergiria do resultado impresso |
