# BNF MiniPar 2026.2 — gramática consolidada a partir da implementação

| Campo | Valor |
|---|---|
| Card | `DOC-01` — BNF final e pseudocódigos núcleo (Eixo B) |
| Fonte da verdade | `src/lexer.py` e `src/parser.py` (léxico e sintaxe); `src/semantic.py` (restrições de contexto) |
| Base verificada | `origin/dev` em `f54c75e` (inclui `CORE-04/05` #15, `CORE-06` #17, `CORE-07` #18/#29, `CORE-08` #19) |
| Verificação | `python docs/auditorias/DOC-01_sondas_bnf.py`; evidências em [`auditorias/DOC-01_BNF_PSEUDOCODIGOS.md`](auditorias/DOC-01_BNF_PSEUDOCODIGOS.md) |
| Estado | `IN_REVIEW`: falta a **aprovação de exatidão pelo Eixo A**, exigida pelo card |
| Documento irmão | [`13_PSEUDOCODIGOS_NUCLEO.md`](13_PSEUDOCODIGOS_NUCLEO.md) |

Este documento descreve a linguagem **que o compilador aceita hoje**, não a desejada.
Onde o código e a `BNF-grammar.md` da raiz (arquivo do Eixo A) divergem, vale o
código, e a divergência está listada na seção 8 para o A corrigir no arquivo dele.
Nenhuma produção nova foi criada por este card.

---

## 1. Notação

| Símbolo | Significado |
|---|---|
| `<nao_terminal>` | Regra da gramática |
| `"texto"` | Terminal literal (lexema exato) |
| `<MAIUSCULO>` | Classe de token produzida pelo lexer (`TokenType`) |
| `[ x ]` | `x` opcional (0 ou 1) |
| `{ x }` | `x` repetido 0 ou mais vezes |
| `x \| y` | Alternativa |
| `( x )` | Agrupamento |

A gramática é LL(1) na prática: o parser é de **descida recursiva** com um token
de lookahead (`_peek`). Cada regra abaixo cita o método do parser que a implementa.

---

## 2. Léxico (`src/lexer.py`)

### 2.1 Espaços e comentários

```bnf
<ignorado>   ::= <espaco> | <comentario>
<espaco>     ::= qualquer caractere c com c.isspace()          (* inclui \n, \t, \r *)
<comentario> ::= "#" { qualquer caractere exceto "\n" }        (* até o fim da linha *)
```

Não há comentário de bloco. Linha e coluna começam em 1; `\n` incrementa a linha.

### 2.2 Identificadores e palavras reservadas

```bnf
<IDENTIFIER> ::= ( <letra> | "_" ) { <letra> | <digito_u> | "_" }
<letra>      ::= qualquer caractere c com c.isalpha()          (* Unicode: "ação" é aceito *)
<digito_u>   ::= qualquer caractere c com c.isalnum() e não letra
```

Um identificador cujo lexema está na tabela `KEYWORDS` vira o token correspondente:

| Grupo | Lexemas | Token |
|---|---|---|
| Declarações | `class` `extends` `new` `func` `var` `this` | `CLASS` `EXTENDS` `NEW` `FUNC` `VAR` `THIS` |
| Controle | `if` `else` `while` `do` `for` `in` `break` `continue` `return` | um token por palavra |
| Blocos | `seq` `par` | `SEQ` `PAR` |
| Fork/Join (2026.2) | `fork` `join` `on` | `FORK` `JOIN` `ON` |
| Canais e E/S | `c_channel` `send` `receive` `input` `print` | um token por palavra |
| Coleções | `matrix` | `MATRIX` |
| Booleanos | `true` `false` | `BOOL_LITERAL` |
| Tipos | `number` `int` `string` `bool` `void` `list` `dict` | `TYPE` (lexema guarda o nome) |

Os nomes da biblioteca nativa (`exp`, `random`, `range`, `len`, `to_number`,
`parse_ints`, `substr`, `to_string`) **não** são palavras reservadas no léxico: são
`IDENTIFIER`. A reserva é semântica (seção 6).

### 2.3 Literais

```bnf
<NUMBER>         ::= <digito> { <digito> } [ "." { <digito> } ]  (* "1." é aceito; ".5" não *)
<digito>         ::= qualquer caractere c com c.isdigit()

<STRING_LITERAL> ::= '"' { <caractere_string> } '"'
<caractere_string> ::= qualquer caractere exceto '"' e "\"     (* pode conter quebra de linha *)
                     | "\" <caractere>
<BOOL_LITERAL>   ::= "true" | "false"
```

Escapes: `\n`→nova linha, `\t`→tabulação, `\"`→aspas, `\\`→barra. Qualquer outro
`\x` produz só `x` (a barra é descartada). Não há notação científica (`1e3` vira
`NUMBER 1` seguido de `IDENTIFIER e3`).

### 2.4 Operadores e delimitadores

| Lexema | Token | Lexema | Token |
|---|---|---|---|
| `+` `-` `*` `/` `%` | `PLUS` `MINUS` `STAR` `SLASH` `MOD` | `=` | `ASSIGN` |
| `==` `!=` | `EQ` `NEQ` | `!` | `NOT` |
| `<` `>` `<=` `>=` | `LT` `GT` `LTE` `GTE` | `&&` `\|\|` | `AND` `OR` |
| `(` `)` `{` `}` `[` `]` | `LPAREN` … `RBRACKET` | `.` `;` `,` | `DOT` `SEMICOLON` `COMMA` |

O lexer reconhece o operador mais longo (`<=` antes de `<`). `&` ou `|` isolados e
qualquer outro caractere viram `UNKNOWN`. O fluxo termina com `END_OF_FILE`.

### 2.5 Erros léxicos

| Código | Quando | Efeito |
|---|---|---|
| `LEX_UNTERMINATED_STRING` | Fim do arquivo antes de `"` de fechamento | O token `STRING_LITERAL` é emitido mesmo assim |
| `LEX_UNKNOWN_CHAR` | Token `UNKNOWN` | Um diagnóstico por caractere |

O lexer **não para** no primeiro erro: acumula diagnósticos ordenados por
(linha, coluna). O serviço (`src/service.py`) não chama o parser se houver qualquer
diagnóstico léxico.

---

## 3. Gramática sintática consolidada (`src/parser.py`)

```bnf
(* ===================================================================== *)
(*  MiniPar 2026.2 — derivada de src/parser.py em origin/dev f54c75e      *)
(* ===================================================================== *)

(* ─── PROGRAMA ─────────────────────────────────── Parser.parse ─── *)
<programa> ::= { <comando> } <END_OF_FILE>

(* ─── COMANDOS ─────────────────────────────── _parse_statement ─── *)
<comando> ::= <declaracao_classe>
            | <declaracao_funcao>
            | <comando_return>
            | <comando_break>
            | <comando_continue>
            | <declaracao_variavel>
            | <bloco_seq>
            | <bloco_par>
            | <comando_print>
            | <comando_send>
            | <comando_if>
            | <comando_while>
            | <comando_do_while>
            | <comando_for>
            | <comando_expressao>

(* class e func são comandos: podem aparecer dentro de blocos. *)

(* ─── DECLARAÇÕES ─────────────────────────────────────────────────── *)
<declaracao_variavel> ::= ( "var" | <TYPE> ) <IDENTIFIER> [ "=" <expressao> ] ";"
                                                      (* _parse_var_decl *)

<declaracao_funcao>   ::= "func" <IDENTIFIER> "(" [ <lista_parametros> ] ")" <bloco_chaves>
<lista_parametros>    ::= <parametro> { "," <parametro> }
<parametro>           ::= [ <TYPE> ] <IDENTIFIER>    (* o tipo é lido e descartado *)
                                                      (* _parse_func_decl *)

<declaracao_classe>   ::= "class" <IDENTIFIER> [ "extends" <IDENTIFIER> ]
                          "{" { <membro_classe> } "}"
<membro_classe>       ::= "var" <IDENTIFIER> [ "=" <expressao> ] ";"
                        | "func" <IDENTIFIER> "(" [ <lista_parametros> ] ")" <bloco_chaves>
                                                      (* _parse_class_decl *)

(* ─── COMANDOS SIMPLES ────────────────────────────────────────────── *)
<comando_return>   ::= "return" [ <expressao> ] [ ";" ]     (* _parse_return_stmt *)
<comando_break>    ::= "break" [ ";" ]
<comando_continue> ::= "continue" [ ";" ]
<comando_print>    ::= "print" "(" [ <lista_argumentos> ] ")" ";"
<comando_send>     ::= "send" "(" <expressao> "," <expressao> ")" ";"

<comando_expressao> ::= <expressao_inicial> "=" <expressao> ";"   (* atribuição *)
                      | <expressao_inicial> ";"                    (* chamada/fork/join *)

(* <expressao_inicial> é uma <expressao> cujo primeiro token é um de:
   IDENTIFIER this new receive input c_channel matrix "[" fork join.
   Restrições verificadas pelo parser depois de analisar a expressão:
   - com "=": o lado esquerdo deve ser IDENTIFIER, acesso a propriedade
     (x.p) ou indexação (x[i]); senão SYN_INVALID_ASSIGNMENT.
     Produz Assignment, PropertyAssign ou IndexAssign.
   - sem "=": a expressão inteira deve ser chamada de função, chamada de
     método, fork ou join; senão SYN_INVALID_STATEMENT.               *)

(* ─── BLOCOS ──────────────────────────── _parse_seq/_parse_par_block ─── *)
<bloco_seq>    ::= [ "seq" ] <bloco_chaves>
<bloco_chaves> ::= "{" { <comando> } "}"
<bloco_par>    ::= "par" "{" { <comando> } "}"   (* cada comando é um ramo paralelo *)

(* ─── CONTROLE ────────────────────────────────────────────────────── *)
<comando_if>       ::= "if" "(" <expressao> ")" <comando> [ "else" <comando> ]
                       (* "else" casa com o if mais próximo; else-if = else + <comando_if> *)
<comando_while>    ::= "while" "(" <expressao> ")" <comando>
<comando_do_while> ::= "do" <comando> "while" "(" <expressao> ")" [ ";" ]

<comando_for>      ::= "for" "(" ( <for_iterador> | <for_classico> ) ")" <comando>
<for_iterador>     ::= "var" <IDENTIFIER> "in" <expressao>
<for_classico>     ::= [ <inicializador_for> ] ";" [ <expressao> ] ";" [ <passo_for> ]
<inicializador_for>::= ( "var" | <TYPE> ) <IDENTIFIER> [ "=" <expressao> ]
                     | <expressao> [ "=" <expressao> ]
<passo_for>        ::= <expressao> [ "=" <expressao> ]
                                                      (* _parse_for_stmt *)

(* ─── EXPRESSÕES (da menor para a maior precedência) ──────────────── *)
<expressao>      ::= <expressao_ou>                                  (* _parse_expression *)
<expressao_ou>   ::= <expressao_e> { "||" <expressao_e> }            (* _parse_or *)
<expressao_e>    ::= <expressao_comp> { "&&" <expressao_comp> }      (* _parse_and *)
<expressao_comp> ::= <expressao_termo>
                     { ( "==" | "!=" | "<" | ">" | "<=" | ">=" ) <expressao_termo> }
                                                                     (* _parse_comparison *)
<expressao_termo>::= <expressao_fator> { ( "+" | "-" ) <expressao_fator> }   (* _parse_term *)
<expressao_fator>::= <expressao_unaria> { ( "*" | "/" | "%" ) <expressao_unaria> }
                                                                     (* _parse_factor *)
<expressao_unaria>::= ( "-" | "+" | "!" ) <expressao_unaria>
                    | <expressao_posfixa>                            (* _parse_unary *)

<expressao_posfixa>  ::= <expressao_primaria> { <sufixo> }          (* _parse_primary, laço final *)
<sufixo>             ::= "." <IDENTIFIER> [ "(" [ <lista_argumentos> ] ")" ]
                       | "[" <expressao> "]"

<expressao_primaria> ::= <expressao_fork>
                       | <expressao_join>
                       | "matrix" "(" <expressao> "," <expressao> "," <expressao> ")"
                       | "[" [ <lista_argumentos> ] "]"
                       | "c_channel" "(" <expressao> "," <expressao> ")"
                       | "receive" "(" <expressao> ")"
                       | "input" "(" [ <expressao> ] ")"
                       | "new" <IDENTIFIER> "(" [ <lista_argumentos> ] ")"
                       | "this"
                       | <NUMBER> | <STRING_LITERAL> | <BOOL_LITERAL>
                       | <IDENTIFIER> [ "(" [ <lista_argumentos> ] ")" ]
                       | "(" <expressao> ")"

<lista_argumentos>   ::= <expressao> { "," <expressao> }

(* ─── FORK/JOIN (2026.2, CORE-04/05) ──────────────────────────────── *)
<expressao_fork> ::= "fork" <IDENTIFIER> "(" [ <lista_argumentos> ] ")" [ "on" <expressao> ]
<expressao_join> ::= "join" "(" <expressao> [ "," <expressao> ] ")"
```

### 3.1 Observações que a gramática acima captura e que costumam surpreender

- `seq` é opcional: `{ ... }` sozinho já é um bloco sequencial.
- `;` é **opcional** depois de `return`, `break`, `continue` e `do … while (…)`; é
  **obrigatório** nos demais comandos simples.
- Uma expressão isolada só é comando se for chamada, `fork` ou `join` (`x + 1;`,
  `input();` e `receive(c);` são rejeitados; `1;` e `(f());` também, porque o
  comando não pode começar com literal nem com `(`).
- Atributos de classe só podem ser declarados com `var` (não `int x;`), e o corpo da
  classe só aceita `var` e `func`.
- O `for` com `in` exige `var`; `for (x in l)` é erro sintático.
- No `fork`, `on` consome uma **expressão completa**: `fork f() on d + 1` usa
  `d + 1` como destino. Para operar sobre o handle, parentize o `fork`.
- O `fork` e o `join` são primárias, então aceitam sufixos (`.`, `[ ]`) e podem
  aparecer como comando; as regras semânticas da seção 5 decidem se o uso é válido.

---

## 4. Precedência e associatividade

| Nível | Operadores | Associatividade | Método |
|---|---|---|---|
| 7 (maior) | `.` `.m(...)` `[ ]` (sufixos) | esquerda | `_parse_primary` |
| 6 | `-` `+` `!` (unários) | direita | `_parse_unary` |
| 5 | `*` `/` `%` | esquerda | `_parse_factor` |
| 4 | `+` `-` | esquerda | `_parse_term` |
| 3 | `==` `!=` `<` `>` `<=` `>=` (mesmo nível) | esquerda | `_parse_comparison` |
| 2 | `&&` | esquerda | `_parse_and` |
| 1 (menor) | `\|\|` | esquerda | `_parse_or` |

Igualdade e relacionais ficam **no mesmo nível**: `1 < 2 == true` é
`(1 < 2) == true`. Não existe operador ternário, de atribuição composta (`+=`) nem
incremento (`++`).

---

## 5. Fork/Join — sintaxe, regras estáticas e tradução

### 5.1 Sintaxe e AST

| Forma | Nó da AST | Campos |
|---|---|---|
| `fork f(a, b)` | `ForkExpr` | `function_name="f"`, `arguments=[a, b]`, `destination=None` (local) |
| `fork f(a) on d` | `ForkExpr` | `destination=d` (expressão; `"local"` ou `"host:porta"` em execução) |
| `join(h)` | `JoinExpr` | `handle=h`, `timeout=None` |
| `join(h, t)` | `JoinExpr` | `timeout=t` (milissegundos) |

`fork` devolve um valor do tipo inferido `task` (não há palavra de tipo `task`).
`join` devolve o tipo de retorno da função da tarefa, quando conhecido.

### 5.2 Regras estáticas (`src/semantic.py`)

| Regra | O que é rejeitado | Origem | `code` no diagnóstico |
|---|---|---|---|
| FJ-SEM-01 | `fork` de nome que não é `func` global (variável, método, local que sombreia, inexistente) | C-FJ-v1 §2.2.2 | `SEM_FJ_01` |
| FJ-SEM-02 | Número de argumentos ≠ número de parâmetros | C-FJ-v1 §2.2.2 | `SEM_ARITY` |
| FJ-SEM-03 | `join` de expressão de tipo conhecido ≠ `task` | C-FJ-v1 §2.2.2 | `SEM_FJ_03` |
| FJ-SEM-04 | Destino conhecido não-string; `timeout` conhecido não numérico | C-FJ-v1 §2.2.2 | `SEM_FJ_04` |
| FJ-SEM-05 | Tarefa que lê/escreve global mutável (direta ou transitivamente, inclusive métodos e inicializadores de classe); `this` em tarefa global; `input`, `c_channel`, `send`, `receive` na tarefa; método de tipo desconhecido na tarefa | C-FJ-v1 §2.2.5 + CR-CORE05 (PEND-FJ-06) | `SEM_FJ_05` |
| FJ-SEM-06 | Argumento ou retorno que não cruza tarefas (objeto, `c_channel`, `task`, também dentro de listas); aritmética com objeto, canal ou handle | C-FJ-v1 §2.2.2/§2.2.4 | `SEM_FJ_06` |
| FJ-SEM-07 | `fork` usado como comando (handle descartado) | **extensão proposta** CR-CORE05, ratificação A/C pendente | `SEM_FJ_07` |
| FJ-SEM-08 | Resultado conhecido `none` de `join` usado como valor; `join(h);` como comando é válido | **extensão proposta** CR-CORE05, ratificação A/C pendente | `SEM_FJ_08` |

O texto da mensagem começa com o identificador (`"FJ-SEM-05: tarefa acessa global
mutavel 'g'."`). Os valores `SEM_FJ_01`…`SEM_FJ_08` do campo `code` são a extensão
de catálogo **proposta** em `docs/CR-CORE08-DIAGNOSTICOS.md` (ratificação A+B
pendente); a aridade de `fork` usa o código vigente `SEM_ARITY`. Tipos `var`/`unknown` não provados não geram erro: viram nota em
`SemanticAnalyzer.unresolved_fj`. **Ausência de diagnóstico não prova** que a
tarefa é serializável ou executável (C-FJ-v1 §2.2.5).

Tipos que cruzam tarefas: `number`/`int`, `bool`, `string`, `void` (como `none`) e
listas desses, inclusive aninhadas.

### 5.3 Tradução (resumo; detalhes nos documentos do A)

| Fase | `fork f(a) on d` | `join(h, t)` | Referência |
|---|---|---|---|
| TAC (`src/tac.py`) | `tK = capture a` … `tN = fork f(tK) on tD` (`"local"` sem `on`) | `tM = join h, timeout t` (como comando, sem temporário) | `docs/auditorias/CORE-06_TAC_FORK_JOIN.md` |
| C++ (`src/codegen.py`) | `minipar_rt::start("f", {to_value(a)}, Destination::parse(d))` | `value_cast<T>(__fj_join(h, __fj_timeout(t)))` | `docs/auditorias/CORE-07_BACKEND_RUNTIME.md` |

O C++ de programas com Fork/Join só é gerado se `CppTaskContext` provar tipos
concretos para todas as tarefas; caso contrário a fase `cpp` falha com
`CPP_UNSUPPORTED_FEATURE` (recusa explícita, nunca valor inventado).

---

## 6. Restrições de contexto verificadas no semântico

A gramática livre de contexto aceita programas que o semântico rejeita. Os códigos
abaixo são os emitidos por `src/semantic.py`. O catálogo vigente é o de C-WEB-v1
(`docs/02_CONTRATOS_TECNICOS.md`); `SEM_RESERVED_NAME`, `SEM_INHERITANCE_CYCLE` e
`SEM_UNSUPPORTED_FEATURE` são extensões **propostas** em
`docs/CR-CORE08-DIAGNOSTICOS.md`, ainda sem ratificação A+B.

| Código | Regra |
|---|---|
| `SEM_UNDECLARED_VARIABLE` | Uso ou atribuição de nome não declarado em nenhum escopo visível |
| `SEM_REDECLARED` | Nome declarado duas vezes no mesmo escopo (sombrear em escopo interno é permitido) |
| `SEM_TYPE_MISMATCH` | Declaração/atribuição com tipo incompatível; `string` com outro tipo em `+` ou comparação sem conversão; argumento de `substr`/`to_string`/`len` com tipo errado |
| `SEM_NUMERIC_OPERANDS` | `-` `*` `/` `%` com operando de tipo conhecido não numérico |
| `SEM_OUTSIDE_LOOP` | `break`/`continue` fora de laço |
| `SEM_UNDECLARED_FUNCTION` | Chamada a função não declarada nem nativa |
| `SEM_ARITY` | Número de argumentos diferente em função, método, nativa (`substr` 3, `to_string` 1, `len` 1) ou `fork` |
| `SEM_RESERVED_NAME` | `func` global com nome de função nativa |
| `SEM_UNDECLARED_CLASS` / `SEM_UNDECLARED_SUPERCLASS` | `new` ou `extends` de classe inexistente |
| `SEM_INHERITANCE_CYCLE` | Cadeia de herança cíclica |
| `SEM_UNDECLARED_ATTRIBUTE` / `SEM_UNDECLARED_METHOD` | Membro inexistente em objeto de classe conhecida (considera herança) |
| `SEM_UNSUPPORTED_FEATURE` | Indexação de string (`s[i]`; usar `substr(s, i, 1)`); lista de strings (literal ou `append`) — restrição temporária C-T11-v1 §3.4 |

Compatibilidade de tipos: `var` e `unknown` são compatíveis com tudo; `int` e
`number` são compatíveis entre si; os demais exigem igualdade.

Funções nativas reconhecidas: `exp`, `random`, `range`, `len`, `to_number`,
`parse_ints`, `substr`, `to_string`; métodos de lista `append`/`push_back`, `pop`,
`size`. Semântica de execução de `substr`/`to_string` em C-T11-v1 §3.3 e na
`BNF-grammar.md` da raiz, seção 15.

---

## 7. Rastreabilidade produção → código → sonda

| Produção | Método | Sondas (`DOC-01_sondas_bnf.py`) |
|---|---|---|
| Léxico (2.x) | `Lexer.tokenize` | LEX-01 a LEX-14 |
| `<declaracao_variavel>` | `_parse_var_decl` | SYN-01 a SYN-03 |
| `<declaracao_funcao>` | `_parse_func_decl` | SYN-04, SYN-05, SYN-39 |
| `<declaracao_classe>` | `_parse_class_decl` | SYN-06, SYN-07 |
| `<comando_return>` `<comando_break>` `<comando_continue>` | `_parse_statement`, `_parse_return_stmt` | SYN-08, SYN-09 |
| `<bloco_seq>` `<bloco_par>` | `_parse_seq_block`, `_parse_par_block` | SYN-10, SYN-11 |
| `<comando_if>` `<comando_while>` `<comando_do_while>` | `_parse_if_stmt`, `_parse_while_stmt`, `_parse_do_while_stmt` | SYN-12, SYN-13 |
| `<comando_for>` | `_parse_for_stmt` | SYN-14 a SYN-18 |
| `<comando_print>` `<comando_send>` | `_parse_print_stmt`, `_parse_send_stmt` | SYN-19, SYN-20 |
| `<comando_expressao>` | `_parse_statement`, `_parse_assignment_tail` | SYN-21 a SYN-28, SYN-32 |
| `<expressao_fork>` `<expressao_join>` | `_parse_primary` | SYN-29 a SYN-32, PREC-07 |
| Demais primárias | `_parse_primary` | SYN-33 a SYN-38, SYN-40 |
| Precedência (seção 4) | `_parse_or` … `_parse_unary` | PREC-01 a PREC-06 |
| Regras de contexto (seção 6) | `SemanticAnalyzer` | SEM-01 a SEM-20 |
| Fork/Join (seção 5.2) | `_validate_fork`, `_validate_join`, `_check_*` | FJ-01 a FJ-16 |
| Programas reais | pipeline Lexer → Parser | 16 arquivos `tests/**/*.minipar` |

---

## 8. Divergências encontradas na `BNF-grammar.md` da raiz (para o Eixo A)

A `BNF-grammar.md` da raiz pertence ao Eixo A e está fora do escopo de arquivos do
`DOC-01` (`docs/`). Por isso **não foi editada**; as divergências ficam registradas
para o A corrigir ou contestar na revisão deste PR.

| ID | Trecho da `BNF-grammar.md` (seção 17) | Comportamento real | Sonda |
|---|---|---|---|
| DIV-01 | Título "Linguagem MiniPar 2026.1" e cabeçalho da seção 17 "2026.1" | O arquivo já documenta Fork/Join e `substr`/`to_string` (2026.2) | — |
| DIV-02 | `<membro_classe> ::= "var" <declaracao_variavel> \| "func" <declaracao_funcao>` repete a palavra-chave (`var var x`) | `var IDENT [= expr] ;` e `func IDENT (...) bloco`; declaração tipada não é aceita na classe | SYN-06, SYN-07 |
| DIV-03 | `<comando_return> ::= "return" [ <expressao> ] ";"`; idem `break`/`continue` | `;` opcional nos três | SYN-08, SYN-09 |
| DIV-04 | `<programa> ::= { <declaracao_global> \| <comando> }` e `<comando>` sem `class`/`func` | `class` e `func` são comandos e podem aparecer dentro de blocos | SYN-39 |
| DIV-05 | `<letra> ::= "A" … "Z" \| "a" … "z"` | Lexer usa `str.isalpha()`/`isalnum()`/`isdigit()`: letras e dígitos Unicode são aceitos | LEX-13 |
| DIV-06 | `<caractere_string>` lista só `\n` `\t` `\"` `\\` | Escape desconhecido `\x` produz `x` (barra descartada); quebra de linha literal é aceita na string | LEX-07 |
| DIV-07 | `<comando>` admite `<chamada_funcao> ";"` sem dizer quais tokens iniciam o comando | Comando-expressão só começa por IDENTIFIER, `this`, `new`, `receive`, `input`, `c_channel`, `matrix`, `[`, `fork`, `join` e precisa ser chamada/fork/join (ou atribuição) | SYN-23 a SYN-26 |

Nenhuma divergência muda o que o compilador aceita; todas são de documentação.
