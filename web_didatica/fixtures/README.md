# Fixtures mock da Web didática (WEB-01)

Respostas de exemplo no formato do contrato **C-WEB-v1** (`docs/02_CONTRATOS_TECNICOS.md`, §1), criadas para a Web didática antes de existir o serviço `src/service.py` do Eixo A (`CORE-08`). **Tudo aqui é mock**: a interface exibe esse estado ao usuário.

Desde o WEB-03 a Web usa o serviço real por padrão e, nesse modo, lê destas fixtures **só o campo `source`** (o código dos exemplos); os envelopes daqui só aparecem com `?fonte=mock`. Medido em 05/11/2026 sobre o `dev` atual: o serviço real devolve para FIX-01 a FIX-04, PROG-02 e EXEC-01 (em `analyze`) o mesmo conteúdo destas fixtures, fora `request_id`, `duration_ms` e o texto C++. O PROG-01 diverge em `semantic.symbols` e `tac.text`, porque a fixture foi gerada antes das mudanças do TAC e do semântico do Eixo A; no modo real a Web mostra o resultado atual.

## Arquivos

| Arquivo | Fixture | Operação | Conteúdo |
|---|---|---|---|
| `fix-01-sucesso.json` | FIX-01 | `analyze` | `var x = 2 + 3;` / `print(x);`, todas as fases `ok` |
| `fix-02-erro-lexico.json` | FIX-02 | `analyze` | `@` desconhecido → `LEX_UNKNOWN_CHAR` |
| `fix-03-erro-sintatico.json` | FIX-03 | `analyze` | expressão faltando → `SYN_EXPECTED_EXPRESSION` |
| `fix-04-erro-semantico.json` | FIX-04 | `analyze` | `y` não declarado → `SEM_UNDECLARED_VARIABLE` |
| `prog-01-quicksort-classes.json` | PROG-01 | `analyze` | Teste 6 (classe, cinco métodos, laços): 149 nós, 17 escopos, 24 símbolos |
| `prog-02-grande-truncado.json` | PROG-02 | `analyze` | programa gerado (função com laço e mil declarações): 6029 nós, AST truncada em 5000 com dois marcadores `max_nodes`; 9055 tokens, 3019 linhas de TAC. JSON compacto (1,4 MB) |
| `exec-01-fix01.json` | EXEC-01 | `compile` + `execute` | código de FIX-01 compilado com g++ e executado: `stdout` `"5\n"` |
| `index.json` | — | — | lista das fixtures para a interface |

Cada arquivo tem `fixture`, `title`, `mock: true`, `source` (o código exato, com `\n`), `notes` e o envelope da operação (`analyze`, ou `compile` e `execute`). O envelope é exatamente o que o serviço devolveria; `source` fica junto porque o envelope não traz o código. O código fica dentro do JSON, e não em `.minipar`, para o `core.autocrlf` do Git não trocar `\n` por `\r\n` e quebrar o `source_hash`.

## Como foram geradas

```bash
py -B web_didatica/tools/gerar_fixtures.py
py -B web_didatica/tools/validar_fixtures.py
```

O gerador **lê** `src/` sem alterar nada: roda o Lexer, o Parser, o Semântico, o TAC e o `CppCodeGenerator` reais e serializa o resultado pelas regras do §1.4. Não é o serviço de fases e a Web nunca o chama. Onde o compilador atual ainda não faz o que o contrato pede, o gerador produz o comportamento **contratado**:

| Pendência do contrato | O que o gerador faz |
|---|---|
| PEND-WEB-01 (lexer não acusa erro) | token `UNKNOWN` vira `LEX_UNKNOWN_CHAR`. String sem fechamento (`LEX_UNTERMINATED_STRING`) **não** é emulada |
| PEND-WEB-02 (parser chama `sys.exit`) | captura o `SystemExit` e converte a mensagem em diagnóstico |
| PEND-WEB-03 (semântico descarta escopos) | uma subclasse do `SemanticAnalyzer` registra escopos e símbolos no momento em que são criados |
| PEND-WEB-04 (tradução e g++ juntos) | lê o `.cpp` gravado pelo gerador atual num diretório temporário; em `analyze` o g++ aponta para um executável inexistente de propósito |

O validador confere FIX-01 a FIX-04 contra os blocos JSON do §1.9, campo a campo, ignorando só o texto C++ (abreviado no contrato), e verifica em todas as fixtures o `source_hash`, a ordem das fases, a regra das fases ignoradas, os ids da AST e as regras de truncamento do §1.4 (no máximo 5000 nós emitidos, um marcador `max_nodes` como último filho, emitidos + omitidos = `nodes`). Em PROG-02 exige truncamento em exatamente 5000 nós; em EXEC-01, `stdout` igual a `"5\n"` (ACE-02).

O PROG-02 é o exemplo de desempenho do WEB-02. Linha de base medida no wireframe do WEB-01 (painel interno do Claude Code, Chromium, `PerformanceObserver` do tipo `longtask`), ao abrir cada aba: Tokens 810 ms, TAC 346 ms, Semântico 233 ms, AST 218 ms, C++ 150 ms.

Medição antes e depois dos painéis em blocos do WEB-02, nas mesmas condições: mesmo navegador, aba em segundo plano, tempo síncrono do clique em cada aba, incluindo remover o painel anterior. Com a aba em segundo plano o navegador não desenha a tela, então os números não incluem layout e pintura e só valem para comparar entre si.

| Aba (PROG-02) | Antes (após AST recolhível) | Depois (blocos de 500) | Elementos no painel depois |
|---|---|---|---|
| Tokens | 2264 ms | 32 ms | 2512 (antes 45 286) |
| Semântico | 248 ms | 42 ms | 3072 |
| TAC | 300 ms | 13 ms | 506 |
| C++ | 167 ms | 15 ms | 506 |
| AST | 322 ms | 54 ms | 3845 |

## Limitações conhecidas

- **Linha dos blocos:** o parser não define `line` em `SeqBlock`/`ParBlock`, então esses nós e os escopos `seq`/`par` saem com `line: 1`. A fixture mostra o comportamento real. A correção é do Eixo A.
- **Contexto de função na mensagem semântica:** o semântico imprime `Linha N (Funcao: f): mensagem`. O gerador trata `(Funcao: f)` como parte do prefixo e o remove do `message`. O contrato não diz isso explicitamente; precisa ser confirmado com o A no `CORE-08`.
- **EXEC-01:** o comando do g++ é o do gerador atual (`output\minipar_<id>.cpp`); o serviço real usará um diretório por requisição. `gpp.duration_ms` e `execute.duration_ms` são medidas reais, então mudam a cada geração.
- O gerador foi executado com Python 3.14 (`py`). O ambiente padronizado do projeto é Python 3.12.4 na `.venv` (SET-02).
