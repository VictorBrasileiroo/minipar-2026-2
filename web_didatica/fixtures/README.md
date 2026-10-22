# Fixtures mock da Web didática (WEB-01)

Respostas de exemplo no formato do contrato **C-WEB-v1** (`docs/02_CONTRATOS_TECNICOS.md`, §1), usadas pela Web didática enquanto o serviço `src/service.py` do Eixo A (`CORE-08`) não existe. **Tudo aqui é mock**: a interface deve exibir esse estado ao usuário.

## Arquivos

| Arquivo | Fixture | Operação | Conteúdo |
|---|---|---|---|
| `fix-01-sucesso.json` | FIX-01 | `analyze` | `var x = 2 + 3;` / `print(x);`, todas as fases `ok` |
| `fix-02-erro-lexico.json` | FIX-02 | `analyze` | `@` desconhecido → `LEX_UNKNOWN_CHAR` |
| `fix-03-erro-sintatico.json` | FIX-03 | `analyze` | expressão faltando → `SYN_EXPECTED_EXPRESSION` |
| `fix-04-erro-semantico.json` | FIX-04 | `analyze` | `y` não declarado → `SEM_UNDECLARED_VARIABLE` |
| `prog-01-quicksort-classes.json` | PROG-01 | `analyze` | Teste 6 (classe, cinco métodos, laços): 149 nós, 17 escopos, 24 símbolos |
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

O validador confere FIX-01 a FIX-04 contra os blocos JSON do §1.9, campo a campo, ignorando só o texto C++ (abreviado no contrato), e verifica em todas as fixtures o `source_hash`, a ordem das fases, a regra das fases ignoradas e os ids da AST. Em EXEC-01 exige `stdout` igual a `"5\n"` (ACE-02).

## Limitações conhecidas

- **Linha dos blocos:** o parser não define `line` em `SeqBlock`/`ParBlock`, então esses nós e os escopos `seq`/`par` saem com `line: 1`. A fixture mostra o comportamento real. A correção é do Eixo A.
- **Contexto de função na mensagem semântica:** o semântico imprime `Linha N (Funcao: f): mensagem`. O gerador trata `(Funcao: f)` como parte do prefixo e o remove do `message`. O contrato não diz isso explicitamente; precisa ser confirmado com o A no `CORE-08`.
- **EXEC-01:** o comando do g++ é o do gerador atual (`output\minipar_<id>.cpp`); o serviço real usará um diretório por requisição. `gpp.duration_ms` e `execute.duration_ms` são medidas reais, então mudam a cada geração.
- O gerador foi executado com Python 3.14 (`py`). O ambiente padronizado do projeto é Python 3.12.4 na `.venv` (SET-02).
