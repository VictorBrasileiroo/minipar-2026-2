# Seção do relatório — Teste 11: MiniCompilador escrito em MiniPar

> Card `WEB-05` (Eixo B). Texto pronto para o `DOC-04` copiar para o relatório. Fonte da verdade:
> `tests/2026_2/test11/minicompilador.minipar` (código), contrato C-T11-v1
> (`docs/02_CONTRATOS_TECNICOS.md` §3) e evidências de `T11-01` a `T11-03`. O pseudocódigo
> abaixo segue o programa MiniPar método a método; se o programa mudar, esta seção muda junto
> (regra 11 do `AGENTS.md`).

## 1. O que o Teste 11 pede e o que foi feito

O Teste 11 pede um compilador de expressões aritméticas **escrito na própria linguagem MiniPar**:
ele lê uma expressão infixada, mostra os tokens, a árvore sintática (AST), o código de três
endereços (TAC), a tabela de símbolos, o resultado e um programa Assembly ARMv7 que roda no
simulador CPUlator e deixa o resultado num registrador.

O MiniCompilador é a classe `MiniCompilador` de `minicompilador.minipar` (429 linhas). Ele é
compilado pelo compilador hospedeiro do projeto (Lexer → Parser → Semântico → C++ → g++) e o
binário resultante é que faz todo o trabalho: nenhuma fase do Teste 11 é feita em Python. O
compilador hospedeiro só ganhou as primitivas de string de que o programa precisava (`substr`,
`to_string`, concatenação e comparação de strings, card `CORE-03` do Eixo A).

A referência do professor (`docs/fontes/teste11/MiniCompiladorCompleto_ARMv7.java`) foi seguida
no formato da saída e do Assembly. Onde a referência aceita uma entrada e gera resultado ou
Assembly errado, o T11 rejeita a entrada com mensagem (seção 6).

## 2. Estruturas de dados

O recorte de listas do MiniPar 2026.2 usado no T11 é o de listas numéricas (listas de strings
ficaram fora, C-T11-v1 §3.4). Por isso tokens e nós ficam em **listas paralelas de números**, e
todo texto (lexema de token, operando do TAC, constante do Assembly) é recuperado da própria
entrada com `substr(e, início, tamanho)`.

| Campo | Conteúdo |
|---|---|
| `e` | a expressão lida do stdin |
| `erro` | primeira mensagem de erro (`""` enquanto não houve erro) |
| `tipos[t]`, `inicios[t]`, `tamanhos[t]` | token `t`: tipo (0 `NUMERO`, 1 `OPERADOR`, 2 `PARENTESE`), posição e tamanho do lexema em `e` |
| `ntok[n]`, `nesq[n]`, `ndir[n]` | nó `n` da AST: índice do token e índices dos filhos esquerdo e direito (`-1` = nenhum; folha tem os dois `-1`) |
| `raiz` | índice do nó raiz |
| `pos`, `ultimo` | token atual do parser e último nó construído (as regras do parser não retornam valor; deixam o nó em `ultimo`) |
| `svals[j]`, `stoks[j]` | tabela de símbolos: valor da constante e token da sua primeira ocorrência, em ordem crescente de valor |
| `temp`, `reg` | contadores do próximo temporário do TAC (`t1`, `t2`…) e do próximo registrador (`r0`, `r1`…) |

Funções auxiliares usadas no pseudocódigo: `lexema(t) = substr(e, inicios[t], tamanhos[t])`;
`atual()` é o lexema do token `pos` (ou `""` no fim); `falhar(fase, msg)` guarda
`"Erro <fase>: <msg>"` **só se ainda não houver erro**, de modo que a primeira falha é a que
aparece; `coluna(i)` devolve `"coluna " + (i + 1)`.

## 3. Pseudocódigo

### 3.1 Programa principal e ordem das fases

```text
entrada ← input("Digite uma expressão infixada: ")
mc ← novo MiniCompilador
mc.compilar(entrada)

procedimento compilar(entrada)
    e ← entrada
    analisarLexico()
    se erro = "" então
        imprimirTokens()               ▷ os tokens saem antes da análise sintática, como na referência
        analisarSintatico()
    se erro = "" então analisarSemantico()
    se erro = "" então gerarSaidas(avaliar(raiz))   ▷ avaliar também pode falhar (estouro de 32 bits)
    se erro ≠ "" então imprimir "❌ " + erro       ▷ nada de AST, TAC, Assembly ou resultado
```

### 3.2 Análise léxica

```text
procedimento analisarLexico()
    i ← 0; n ← len(e)
    enquanto i < n e erro = "":
        c ← substr(e, i, 1)
        se c é espaço ou tabulação: i ← i + 1
        senão se c = "#": i ← n                       ▷ comentário até o fim da linha
        senão se c é dígito:
            ini ← i
            enquanto i < n e substr(e, i, 1) é dígito: i ← i + 1
            num ← substr(e, ini, i − ini)
            se o próximo caractere é ".":       falhar("léxico", "número decimal não suportado na " + coluna(ini))
            senão se len(num) > 1 e num começa com "0":
                                                 falhar("léxico", "zero à esquerda não suportado em '" + num + "' …")
            senão se len(num) > 10 ou valor(num) > 2147483647:
                                                 falhar("léxico", "constante '" + num + "' fora do intervalo 0..2147483647 …")
            senão adicionarToken(NUMERO, ini, i − ini)
        senão:
            se c ∈ {+, −, *}:   adicionarToken(OPERADOR, i, 1)
            senão se c ∈ {(, )}: adicionarToken(PARENTESE, i, 1)
            senão rejeitarCaractere(c, i)
            i ← i + 1
    se erro = "" e não há tokens: falhar("léxico", "entrada vazia")

procedimento rejeitarCaractere(c, i)            ▷ mensagem específica para cada caso proibido
    "/"          → "divisão '/' não suportada"
    "="          → "atribuição '=' não suportada"
    letra ou "_" → "identificador não suportado"
    "."          → "número decimal não suportado"
    imprimível   → "caractere desconhecido '<c>'"
    outro        → "caractere não suportado"
    (todas terminam com " na " + coluna(i))
```

### 3.3 Análise sintática (descida recursiva)

Gramática, a mesma da referência, com `*` mais forte que `+` e `−` e associatividade à esquerda:

```text
expr   → term   { ("+" | "−") term }
term   → factor { "*" factor }
factor → NUMERO | "(" expr ")"
```

```text
procedimento novoNo(t, esq, dir)                ▷ acrescenta o nó e o deixa em ultimo
    ntok.append(t); nesq.append(esq); ndir.append(dir); ultimo ← len(ntok) − 1

procedimento parseExpr()
    parseTerm(); no ← ultimo
    enquanto erro = "" e atual() ∈ {"+", "−"}:
        t ← pos; pos ← pos + 1
        parseTerm()
        novoNo(t, no, ultimo); no ← ultimo        ▷ o nó antigo vira filho esquerdo: associatividade à esquerda
    ultimo ← no

procedimento parseTerm()                         ▷ igual a parseExpr, com "*" e parseFactor

procedimento parseFactor()
    se erro ≠ "": retornar
    se pos ≥ número de tokens: falhar("sintático", "expressão incompleta: esperado número ou '(' no fim da entrada")
    senão se lexema(pos) = "(":
        t ← pos; pos ← pos + 1
        parseExpr()
        se erro = "" e atual() ≠ ")":
            se acabaram os tokens: falhar("sintático", "'(' da coluna X sem ')' correspondente")
            senão                  falhar("sintático", "esperado ')' e encontrado '<lexema>' na coluna Y")
        pos ← pos + 1                              ▷ o ")" não vira nó: a AST já guarda o agrupamento
    senão se tipos[pos] = NUMERO:
        pos ← pos + 1; novoNo(pos − 1, −1, −1)    ▷ folha
    senão se lexema(pos) = "−": falhar("sintático", "menos unário não suportado na coluna …")
    senão                       falhar("sintático", "esperado número ou '(' e encontrado '<lexema>' …")

procedimento analisarSintatico()
    pos ← 0; parseExpr(); raiz ← ultimo
    se erro = "" e pos < número de tokens:
        falhar("sintático", "token '<lexema>' inesperado depois do fim da expressão, na coluna …")
```

### 3.4 Análise semântica e tratamento de erros

O T11 não tem variáveis, então o semântico confere os limites do Assembly gerado:

```text
procedimento analisarSemantico()
    ▷ um registrador por nó; só r0–r12 estão livres (r13–r15 são SP, LR e PC)
    se len(ntok) > 13: falhar("semântico", "a AST tem N nós e o Assembly comporta no máximo 13 (registradores r0 a r12)")

função avaliar(no)                               ▷ pós-ordem; também é a última verificação semântica
    se no é folha: retornar valor(lexema(ntok[no]))
    a ← avaliar(nesq[no]); b ← avaliar(ndir[no])
    v ← a op b, com op = lexema(ntok[no]) ∈ {+, −, *}
    se v > 2147483647 ou v < −2147483648:
        falhar("semântico", "o resultado de '<expressão parentizada>' não cabe em 32 bits com sinal")
    retornar v
```

**Tratamento de erros.** Cada fase verifica `erro = ""` antes de trabalhar, e `falhar` guarda só
a primeira mensagem. A primeira falha interrompe as fases seguintes; a saída termina com
`❌ Erro <fase>: <mensagem>` e não mostra AST, TAC, Assembly nem resultado. A verificação de
32 bits existe porque o ARM calcula em registradores de 32 bits: se um resultado intermediário
estourasse, o registrador final divergiria do resultado impresso.

### 3.5 Tabela de símbolos

As entradas são as constantes da expressão (o T11 não tem identificadores), sem repetição e em
ordem crescente de valor, por inserção ordenada:

```text
procedimento registrarSimbolos()
    para cada nó folha no, na ordem de criação:
        v ← valor(lexema(ntok[no]))
        se v não está em svals:
            svals.append(v); stoks.append(ntok[no])
            j ← último índice
            enquanto j > 0 e svals[j − 1] > svals[j]:   ▷ inserção ordenada
                trocar svals[j] com svals[j − 1]; trocar stoks[j] com stoks[j − 1]; j ← j − 1

procedimento imprimirSimbolos()
    para cada j: imprimir "🔹 " + lexema(stoks[j]) + " → CONST"
```

### 3.6 Geração das saídas: AST, TAC e Assembly ARMv7

```text
procedimento imprimirAST(no, nivel)             ▷ ordem simétrica invertida: direita, nó, esquerda
    se no ≥ 0:
        imprimirAST(ndir[no], nivel + 1)
        imprimir (2 × nivel espaços) + lexema(ntok[no])
        imprimirAST(nesq[no], nivel + 1)

função gerarTAC(no)                              ▷ pós-ordem; devolve o endereço do valor do nó
    se no é folha: retornar lexema(ntok[no])
    a1 ← gerarTAC(nesq[no]); a2 ← gerarTAC(ndir[no])
    t ← "t" + temp; temp ← temp + 1
    imprimir t + " = " + a1 + " " + op + " " + a2
    retornar t

função formatExpr(no)                            ▷ expressão totalmente parentizada, para os comentários
    se no é folha: retornar lexema
    retornar "(" + formatExpr(esq) + " " + op + " " + formatExpr(dir) + ")"

função gerarARM(no)                              ▷ pós-ordem; registrador novo por nó, sem reaproveitamento
    se no é folha:
        r ← "r" + reg; reg ← reg + 1
        se valor > 255: imprimir "    LDR    " + r + ", =" + k     ▷ não cabe no imediato de MOV
        senão          imprimir "    MOV    " + r + ", #" + k
        retornar r
    a1 ← gerarARM(esq); a2 ← gerarARM(dir)
    r ← "r" + reg; reg ← reg + 1                  ▷ alocado depois dos dois filhos
    imprimir "    " + ADD|SUB|MUL (campo de 6 colunas) + " " + r + ", " + a1 + ", " + a2
             + "    @ resultado de '" + formatExpr(no) + "'"
    retornar r

procedimento gerarSaidas(resultado)
    registrarSimbolos()
    imprimir título "🌳 Árvore Sintática Abstrata (AST):"; imprimirAST(raiz, 0)
    imprimir título "📦 Código de Três Endereços (TAC):"; gerarTAC(raiz)
    imprimir título "⚙️ Assembly ARMv7 (CPUlator):"
    imprimir ".global _start", ".text", "_start:"
    gerarARM(raiz)
    imprimir "    b .    @ loop infinito para parar o programa"
    imprimir título "📚 Tabela de Símbolos:"; imprimirSimbolos()
    imprimir título "🧮 Resultado final da expressão:"; imprimir "➡️  " + resultado + ".0"
```

O resultado fica no registrador da raiz, o último alocado: `r(N−1)` para uma AST de `N` nós
(`r8` nos três casos obrigatórios, que têm 9 nós). O `b .` deixa o processador parado na mesma
instrução, para ler os registradores no CPUlator (o sistema "ARMv7 generic" não tem sistema
operacional para encerrar o programa).

## 4. Do stdout ao `.arm` e ao CPUlator

O MiniCompilador imprime o Assembly no stdout, como a referência (que também não grava
arquivo). O `.arm` é o bloco entre a linha que termina em `Assembly ARMv7 (CPUlator):` e a
primeira linha vazia, copiado sem alteração (C-T11-v1 §3.6). Isso é feito de dois jeitos, com as
mesmas regras e o mesmo resultado byte a byte:

- `tests/2026_2/test11/extrair_arm.py --casos tests/2026_2/test11/arm` grava `caso1.arm`,
  `caso2.arm` e `caso3.arm`;
- na Web didática, o botão **Baixar .arm** recorta o stdout da execução exibida
  (`web_didatica/static/js/arm.js`). Ver a seção da interface, figuras 13 a 16.

Nenhum dos dois analisa nem reescreve o Assembly: o texto é o que o programa MiniPar gerou.

## 5. Resultados

### 5.1 Casos obrigatórios

| Caso | Entrada | Resultado impresso | `.arm` (SHA-256) | CPUlator: registrador final | Situação |
|---|---|---|---|---|---|
| 1 | `((2+4)*7)-(5*4)` | `➡️  22.0` | `40adc1e1…a82476c7` | `r8` = `0x00000016` = 22 | PASS |
| 2 | `((10 -8*7)+4)*2` | `➡️  -84.0` | `1a232e2b…6793445e` | `r8` = `0xFFFFFFAC` = −84 | PASS |
| 3 | `((2+4)*7)-(5*4)` | `➡️  22.0` | `40adc1e1…a82476c7` | `r8` = `0x00000016` = 22 | PASS |

- O stdout dos casos 1 e 3, da linha dos tokens até o fim, é idêntico byte a byte às linhas
  3–59 da saída do professor (`docs/fontes/teste11/Execucao-Saida-okRodounoCPULATOR.txt`), e o
  `.arm` é idêntico a `Codigo-Assembly-ARMV7.arm`. O caso 2 é idêntico ao oráculo de C-T11-v1
  §3.12.
- Registradores intermediários conferidos no CPUlator: caso 1, `r2` = 6, `r4` = 42, `r7` = 20;
  caso 2, `r3` = 56, `r4` = −46, `r6` = −42. Ambiente, procedimento, registradores completos e
  capturas: `tests/2026_2/test11/evidencias/README.md` (`caso1_cpulator.jpg`,
  `caso2_cpulator.jpg`, `caso3_cpulator.jpg`).
- Stdout completo de cada caso: `tests/2026_2/test11/arm/casoN.stdout.txt`.

Assembly do caso 2, como gerado pelo MiniCompilador:

```text
.global _start
.text
_start:
    MOV    r0, #10
    MOV    r1, #8
    MOV    r2, #7
    MUL    r3, r1, r2    @ resultado de '(8 * 7)'
    SUB    r4, r0, r3    @ resultado de '(10 - (8 * 7))'
    MOV    r5, #4
    ADD    r6, r4, r5    @ resultado de '((10 - (8 * 7)) + 4)'
    MOV    r7, #2
    MUL    r8, r6, r7    @ resultado de '(((10 - (8 * 7)) + 4) * 2)'
    b .    @ loop infinito para parar o programa
```

### 5.2 Entradas extras (sem nenhum valor fixo por entrada)

Conferidas por `verificar_t11.py`: `(7+8)*3` = 45, `2*3+4*5` = 26, `100-2-3` = 95
(associatividade à esquerda), `2-3*4` = −10 (precedência), `((1+2)*(3+4))-5` = 16,
`  2 * ( 3+4 ) # comentário` = 14, `7` = 7 (só uma folha, sem TAC), `0*5` = 0 e
`(((((((9)))))))` = 9. Um caso extra com constantes grandes, `1000*3-(65536+2)` = −62538,
exercita o `LDR rN, =k` e também foi executado no CPUlator (`r6` = −62538,
`evidencias/extra_ldr_cpulator.jpg`).

## 6. Entradas rejeitadas e diferenças em relação à referência

Mensagens reais do binário (`output/minicompilador_t11.exe`, 05/11/2026), uma execução por linha:

| Entrada | Saída do T11 |
|---|---|
| `-2+3` | `❌ Erro sintático: menos unário não suportado na coluna 1` |
| `2.5*4` | `❌ Erro léxico: número decimal não suportado na coluna 1` |
| `010+1` | `❌ Erro léxico: zero à esquerda não suportado em '010' na coluna 1` |
| `x+1` | `❌ Erro léxico: identificador não suportado na coluna 1` |
| `8/2` | `❌ Erro léxico: divisão '/' não suportada na coluna 2` |
| `2 $ 3` | `❌ Erro léxico: caractere desconhecido '$' na coluna 3` |
| `((2+3)` | `❌ Erro sintático: '(' da coluna 1 sem ')' correspondente` |
| `2+3)` | `❌ Erro sintático: token ')' inesperado depois do fim da expressão, na coluna 4` |
| `2+` | `❌ Erro sintático: expressão incompleta: esperado número ou '(' no fim da entrada` |
| (vazia) | `❌ Erro léxico: entrada vazia` |
| `2147483648` | `❌ Erro léxico: constante '2147483648' fora do intervalo 0..2147483647 na coluna 1` |
| `1+2+3+4+5+6+7+8` | `❌ Erro semântico: a AST tem 15 nós e o Assembly comporta no máximo 13 (registradores r0 a r12)` |
| `65536*65536` | `❌ Erro semântico: o resultado de '(65536 * 65536)' não cabe em 32 bits com sinal` |

Por que o T11 rejeita onde a referência Java aceita (C-T11-v1 §3.6 item 4 e §3.11):

| Situação | Referência Java | T11 | Motivo |
|---|---|---|---|
| constante de 256 a 2147483647 | `MOV rN, #k`, que o montador recusa quando `k` não cabe no imediato | `LDR rN, =k` | o `.arm` precisa montar no CPUlator |
| AST com mais de 13 nós | continua em `r13`–`r15` (SP, LR, PC) | rejeita | sobrescrever SP/LR/PC quebra o programa |
| divisão `/` | só um comentário; o registrador fica sem valor | rejeita | a referência não gera instrução para a divisão (C-T11-v1 §3.1) |
| número decimal, identificador | `MOV r0, #2.5`, `MOV r0, #x`, que não montam | rejeita | Assembly inválido |
| zero à esquerda | `#010` é octal no GNU `as` (vale 8), a avaliação dá 10 | rejeita | registrador divergiria do resultado |
| caractere desconhecido, `)` sobrando, `2+` | pulado em silêncio, ignorado, exceção | rejeita com mensagem | nunca resultado silencioso |

## 7. Como reproduzir

Na raiz do repositório, com o g++ C++20 no `PATH`:

```bash
python tests/2026_2/test11/verificar_t11.py
```

Compila o MiniCompilador pelo pipeline real, executa os três casos, as 9 entradas extras e as 21
entradas de erro, compara com os oráculos, confere os `.arm` e o SHA-256 das evidências do
CPUlator e testa a extração. Resultado em 05/11/2026 (Windows 11, g++ 16.2.0 MSYS2 UCRT64):
**48/48 PASS**.

No CPUlator (`https://cpulator.01xz.net/?sys=arm`, sistema ARMv7 generic): *File → Open* com o
`.arm`, *Compile and Load*, *Continue*, *Stop* quando o `pc` estiver na linha `b .`, e ler `r8`.

## 8. Limitações e pendências

- **PEND-T11-04:** o oráculo do caso 2 foi derivado do algoritmo da referência e confirmado no
  CPUlator (`r8` = −84 e intermediários), mas o Java do professor ainda não foi executado no
  caso 2 (não há JDK na máquina de desenvolvimento).
- A execução no CPUlator do `T11-03` foi conduzida pelo agente (Claude Code) no navegador
  embutido. Pela seção "Uso de IA" do `AGENTS.md`, um responsável humano deve repetir *File →
  Open* com os três `.arm` e conferir os registradores antes do aceite final.
- Uma expressão por execução, como a referência: os três casos são três execuções do mesmo
  binário.
