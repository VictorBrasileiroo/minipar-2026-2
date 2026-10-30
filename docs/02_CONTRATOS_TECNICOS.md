# Contratos Técnicos e Fronteiras entre Eixos — v0.1 PROPOSTA

**Estado:** rascunho detalhado **não congelado**. Deve ser aprovado por A+B+C até o gate G0 (18/10/2026) antes de alterações incompatíveis. Este documento define **interfaces pretendidas**, não afirma que o código as implementa.

## 0. Regras comuns

- Contrato precede implementação. Quem consome pode usar mock com o **mesmo formato**; não inventar versão própria.
- `src/` pertence ao Eixo A; `runtime/` ao C; `web_didatica/` ao B; Teste 11 ao B; testes 8–10 ao C.
- Contratos têm versões (`v1`) e revisões controladas. Modificação incompatível precisa de CR aprovado por fornecedor e consumidor.
- Erros são objetos explicitamente representados; não usar `true/false` genérico quando o consumidor precisa saber fase ou localização.
- Não misturar compilador principal (Python → C++) com MiniCompilador do Teste 11 (programa MiniPar → texto ARMv7).
- **Modelo atual observado:** `AST → TAC` e `AST → C++` são ramos independentes. O backend **não consome TAC**. Ambos devem refletir a mesma semântica; não arquitetar fingindo que TAC é o input do backend.

---

## 1. C-WEB-v1 — Serviço de inspeção/compilação do MiniPar

**Estado:** `v1 — PROPOSTA DE CONGELAMENTO` redigida pelo B em 19/10/2026 no card `CON-02`. Passa a `v1 FROZEN` quando A aprovar o PR (quadro em 1.11). Até lá, nenhum lado trata nomes e campos abaixo como definitivos.

**Revisão 2 (19/10/2026):** incorpora a revisão do coordenador no PR do `CON-02`: `\n` final explícito nas fixtures, regra única para fases ignoradas, tipos e escopos da tabela de símbolos, algoritmo de truncamento da AST, testes de isolamento/timeout/artefatos e entrega do `.arm` do Teste 11 pela Web. Ajuste de 22/10/2026: a extração do `.arm` (1.7) segue todos os erros de C-T11-v1 §3.6 item 2 e normaliza CRLF, conferida na integração com o PR do `CON-03`.

**Fornecedor:** A (`CORE-08`, biblioteca Python sobre o compilador real). **Consumidor:** B (`WEB-01` a `WEB-04`, servidor e interface em `web_didatica/`).
**Objetivo:** permitir que B construa a Web didática com fixtures no formato exato que o serviço real vai devolver, e que A saiba exatamente o que entregar.

### 1.1 Divisão de camadas

```text
navegador (web_didatica/static)          ← B
   │  HTTP JSON (seção 1.8)
web_didatica/server.py (Flask)           ← B: só repassa, valida tamanho, serve arquivos
   │  chamadas Python (seção 1.2)
src/service.py                           ← A: único ponto que chama Lexer/Parser/Semântico/TAC/C++/g++
   │
src/lexer.py · parser.py · semantic.py · tac.py · codegen.py
```

- B não reimplementa nenhuma fase nem lê `stderr` do compilador para extrair informação. Tudo vem de `src/service.py`.
- A não escreve HTML/JS nem rotas Flask da Web didática.
- A Web antiga (`app.py`, porta 5000) e o terminal continuam funcionando como hoje (`CORE-09`). A Web didática roda separada, em `127.0.0.1:5001`.

### 1.2 Interface Python (fornecida por A em `src/service.py`)

| Função | Retorno | O que faz |
|---|---|---|
| `analyze(source: str) -> dict` | envelope `minipar.compile.v1` | Lexer, Parser, Semântico, TAC e geração do texto C++. **Não** chama o g++ |
| `compile_program(source: str) -> dict` | envelope `minipar.compile.v1` | Tudo de `analyze` e mais o g++. Registra artefatos (`cpp`, `tac`, `binary`) |
| `execute(artifact_id: str, stdin: str = "", timeout_sec: int = 10) -> dict` | resultado `minipar.execute.v1` | Executa o binário daquela compilação |
| `get_artifact(artifact_id: str, kind: str) -> dict` | `{"ok", "path", "filename", "media_type"}` ou `{"ok": false, "error": {...}}` | Localiza `cpp`, `tac` ou `binary` para download |

O nome `compile_program` evita sombrear o `compile` nativo do Python. Os retornos são `dict` com apenas tipos JSON (`str`, `int`, `float`, `bool`, `None`, `list`, `dict`). B os serializa com `json.dumps` sem conversão.

**Regras obrigatórias da biblioteca:**
1. **Nunca encerra o processo.** Hoje o parser chama `sys.exit(1)` no primeiro erro (`parser.py` em `_consume` e mais quatro pontos). O serviço precisa transformar isso em diagnóstico, seja por exceção própria, seja capturando `SystemExit`. O servidor da Web não pode cair por erro no programa do usuário.
2. **Não depende de `stdout`/`stderr` como canal de dados.** Mensagens que hoje vão para `stderr` precisam chegar como `diagnostics`.
3. **Sem estado entre chamadas.** Cada chamada cria seus próprios `Lexer`, `Parser`, `SemanticAnalyzer`, `TACGenerator` e `CppCodeGenerator`.
4. **Chamadas simultâneas não se atrapalham.** Cada compilação usa um diretório próprio (proposta: `output/web/<request_id>/`), sem `os.chdir` e sem sobrescrever artefatos de outra requisição.
5. **Erro interno vira envelope.** Exceção inesperada no compilador gera `ok: false`, a fase em andamento com `status: "error"` e diagnóstico `INTERNAL_ERROR`, sem stack trace no `message` (pode ir em `detail`).

### 1.3 Envelope `minipar.compile.v1`

```json
{
  "contract": "minipar.compile.v1",
  "operation": "analyze",
  "request_id": "9f1c2e7a4b3d4c5e8f6a7b8c9d0e1f2a",
  "ok": true,
  "source_hash": "sha256:c04f30bbe5ce38a21f9f87c8fc6949ab1bdafb922161c6cf275d9f954b73bcc6",
  "duration_ms": 41,
  "phases": {
    "lexer":    {"status": "ok", "tokens": []},
    "parser":   {"status": "ok", "ast": {}, "ast_stats": {}},
    "semantic": {"status": "ok", "symbols": []},
    "tac":      {"status": "ok", "text": ""},
    "cpp":      {"status": "ok", "text": ""},
    "gpp":      {"status": "skipped", "reason": "not_requested"}
  },
  "diagnostics": [],
  "artifacts": {"cpp_id": null, "tac_id": null, "binary_id": null}
}
```

| Campo | Regra |
|---|---|
| `operation` | `"analyze"` ou `"compile"` |
| `request_id` | 32 caracteres hexadecimais (UUID4 sem hífens), novo a cada chamada |
| `source_hash` | `"sha256:"` + hash do código em UTF-8, exatamente como recebido. A Web descarta respostas cujo hash não bate com o código atual do editor |
| `phases` | sempre as **seis** chaves, sempre nesta ordem: `lexer`, `parser`, `semantic`, `tac`, `cpp`, `gpp` |
| `status` de fase | `"ok"`, `"error"` ou `"skipped"`. Toda fase `skipped` traz `reason`, e só fases `skipped` trazem `reason` (regra abaixo) |
| propagação | a primeira fase com erro interrompe as seguintes. Erro semântico também interrompe TAC e C++, como faz o `main.py` hoje |
| payload da fase | presente quando `status` é `"ok"`; também presente em `"error"` quando houver resultado parcial útil (ex.: tokens até o caractere inválido). Ausente em `"skipped"` |
| `ok` | `analyze`: `true` se `lexer` a `cpp` estão `ok`. `compile`: `true` só se as seis estão `ok` **e** o binário desta requisição existe e tem tamanho > 0 |
| listas | nunca `null`: lista vazia quando não houver itens |
| `artifacts` | ids iguais ao `request_id` quando o artefato existe nesta requisição, senão `null`. `analyze` nunca registra artefatos |

**Regra única para fases ignoradas.** Cada operação tem um conjunto fixo de fases solicitadas:

| Operação | Fases solicitadas | Fases não solicitadas |
|---|---|---|
| `analyze` | `lexer`, `parser`, `semantic`, `tac`, `cpp` | `gpp` |
| `compile` | as seis | nenhuma |

1. Fase **não solicitada** fica sempre `skipped` com `reason: "not_requested"`, mesmo que uma fase anterior tenha falhado. Por isso `gpp` em `analyze` é sempre `not_requested`.
2. Fase **solicitada** depois da primeira fase com `error` fica `skipped` com `reason: "previous_phase_failed"`.
3. Fase solicitada nunca fica `skipped` por outro motivo: ou executa (`ok`/`error`) ou a regra 2 se aplica.

| Situação | `gpp` |
|---|---|
| `analyze`, com ou sem erro | `skipped` / `not_requested` |
| `compile`, erro em `lexer` a `cpp` | `skipped` / `previous_phase_failed` |
| `compile`, `lexer` a `cpp` ok | `ok` ou `error` |

### 1.4 Fases e payloads

**`lexer.tokens[]`** — `{"type", "lexeme", "line", "column"}`
- `type`: nome exato do membro de `TokenType` em `src/lexer.py` (`"VAR"`, `"IDENTIFIER"`, `"NUMBER"`, `"STRING_LITERAL"`, `"PLUS"`, `"UNKNOWN"`...). Palavras de tipo (`number`, `string`...) vêm como `"TYPE"`; `true`/`false` como `"BOOL_LITERAL"`.
- `lexeme`: texto do token. Em `STRING_LITERAL` é o valor **sem aspas e com escapes já resolvidos** (comportamento atual do lexer).
- `line`, `column`: base 1, coluna contada em caracteres.
- `END_OF_FILE` **não** entra na lista.

**`parser.ast`** — nó `{"id", "kind", "label", "role", "index", "line", "attributes", "children"}`

| Campo | Regra |
|---|---|
| `id` | nós reais: `"n0"`, `"n1"`... em pré-ordem. Marcadores de truncamento: `"x0"`, `"x1"`... na ordem em que são criados. Únicos na resposta |
| `kind` | nome exato da classe em `src/ast_nodes.py`, ou `"Truncated"` para marcador |
| `label` | texto para exibição (regra abaixo). B não interpreta o label |
| `role` | nome do campo do pai que contém o nó (`"init_value"`, `"left"`, `"condition"`...); `null` na raiz |
| `index` | posição (base 0) quando o campo do pai é lista (`statements`, `arguments`...); senão `null` |
| `line` | linha do nó (o compilador atual não guarda coluna na AST) |
| `attributes` | objeto com os campos de atributo (regra abaixo); `{}` quando não houver |
| `children` | lista com os campos de nó (regra abaixo); `[]` quando não houver |

**Campo de nó ou de atributo.** A classificação vem do **tipo declarado** no dataclass, não do valor em tempo de execução:
- **campo de nó**: anotação que cita `ASTNode` ou uma subclasse (`ASTNode`, `Optional[ASTNode]`, `List[ASTNode]`, `List[VarDecl]`, `List[FuncDecl]`). Gera filhos, na ordem de declaração dos campos; listas geram um filho por elemento, com `index`. Valor `None` ou lista vazia não gera filho e **não** vai para `attributes`;
- **campo de atributo**: todos os demais, exceto `line`. Sempre presentes em `attributes`, inclusive com `null`. Conversão: `str` → texto (o `value` de `NumberExpr` continua texto, ex. `"3.14"`), `bool` → booleano, `int` → número, `None` → `null`, `List[str]` → lista de textos (ex. `params`).

**Label.** `kind(valor)`, onde `valor` é o primeiro atributo não nulo entre `op`, `name`, `value`, `class_name`, `method_name`, `property_name`; sem nenhum deles, só `kind`. Formatação do valor: booleano como `true`/`false`; o `value` de `StringExpr` entre aspas duplas com escapes JSON (`StringExpr("a\nb")`); demais textos como estão. Valor formatado com mais de 40 caracteres vira os 39 primeiros seguidos de `…`. Ex.: `"BinaryExpr(+)"`, `"VarDecl(x)"`, `"BoolExpr(true)"`, `"Program"`.

**Tipos de nó v1** (os 35 dataclasses atuais): `NumberExpr`, `StringExpr`, `BoolExpr`, `IdentifierExpr`, `BinaryExpr`, `UnaryExpr`, `VarDecl`, `Assignment`, `PrintStmt`, `SeqBlock`, `ParBlock`, `IfStmt`, `WhileStmt`, `DoWhileStmt`, `ForStmt`, `BreakStmt`, `ContinueStmt`, `ClassDecl`, `FuncDecl`, `ReturnStmt`, `MethodCall`, `FuncCallExpr`, `PropertyAccess`, `PropertyAssign`, `NewExpr`, `ThisExpr`, `CChannelExpr`, `SendStmt`, `ReceiveExpr`, `InputExpr`, `ListLiteral`, `MatrixCreateExpr`, `IndexExpr`, `IndexAssign`, `Program`. Nós novos (ex.: Fork/Join do `CORE-04`) entram como `v1.1` aditiva e seguem as mesmas regras; a Web desenha qualquer `kind` desconhecido de forma genérica.

**Limites e truncamento.** `MAX_NODES = 5000` nós reais e `MAX_DEPTH = 200` (a raiz tem profundidade 1). A serialização percorre a AST em pré-ordem:
1. **Profundidade:** um filho que ficaria com profundidade maior que 200 não é emitido. No lugar dele entra um marcador com `reason: "max_depth"` e `omitted_nodes` igual ao tamanho da subárvore omitida.
2. **Quantidade:** quando 5000 nós reais já foram emitidos, nenhum outro nó real é emitido. Cada nó já emitido que ainda tinha filhos por emitir recebe, como **último** filho, **um único** marcador com `reason: "max_nodes"` e `omitted_nodes` igual à soma dos tamanhos de todas as subárvores dele que ficaram de fora.
3. **Marcador:** `{"id": "x<k>", "kind": "Truncated", "label": "Truncated(<omitted_nodes> nós)", "role": <role do primeiro filho omitido>, "index": <index do primeiro filho omitido>, "line": <line do primeiro filho omitido>, "attributes": {"reason": ..., "omitted_nodes": <int>}, "children": []}`. Marcadores não contam para `MAX_NODES`.

`parser.ast_stats`: `{"nodes": <nós reais da AST completa>, "emitted": <nós reais emitidos>, "depth": <profundidade da AST completa>, "truncated": <emitted < nodes>, "max_nodes": 5000, "max_depth": 200}`. A AST nunca tem ciclos. A serialização não pode estourar o limite de recursão do Python, mesmo com a AST completa mais profunda que 200.

**`semantic.scopes[]`** — `{"id", "kind", "name", "parent", "line"}`

Lista de todos os escopos abertos pelo semântico, na ordem em que são abertos. Os escopos espelham exatamente os pontos em que `SemanticAnalyzer` chama `_enter_scope` hoje:

| `kind` | Quando é aberto | `name` |
|---|---|---|
| `"global"` | início da análise; sempre `s0` | `null` |
| `"class"` | corpo de `ClassDecl` (atributos e métodos) | nome da classe |
| `"function"` | `FuncDecl` fora de classe (guarda os parâmetros) | nome da função |
| `"method"` | `FuncDecl` dentro de classe (guarda os parâmetros) | `Classe.metodo` |
| `"seq"` / `"par"` | cada `SeqBlock` / `ParBlock`, inclusive o corpo de funções, `if`, `while` e `for` | `null` |
| `"for"` | cada `ForStmt` (guarda o inicializador ou o iterador) | `null` |

- `id`: `"s0"`, `"s1"`... em ordem de abertura; único na resposta. É a única referência de escopo; não há identificadores textuais ambíguos.
- `parent`: `id` do escopo que contém este; `null` só em `s0`.
- `line`: linha do nó que abriu o escopo (`1` para `s0`).
- O caminho para exibição (ex.: `global › class Pilha › method Pilha.empilhar › seq`) é montado pela Web a partir de `parent`.

**`semantic.symbols[]`** — `{"name", "kind", "type", "scope", "line", "params"}`

| Campo | Valores |
|---|---|
| `kind` | `"variable"` (`VarDecl` fora de classe), `"attribute"` (`VarDecl` no escopo `class`), `"parameter"`, `"iterator"` (variável de `for ... in`), `"function"`, `"method"` (`FuncDecl` no escopo `class`), `"class"` |
| `type` | texto registrado pelo semântico, de um conjunto fechado (tabela abaixo); `null` para `function`, `method` e `class`, que hoje o semântico registra como `"FUNC"`/`"CLASS"` |
| `scope` | `id` de um item de `semantic.scopes` |
| `line` | linha da declaração |
| `params` | nomes dos parâmetros para `function` e `method`; `[]` nos demais |

| `type` | Origem no semântico atual |
|---|---|
| `"number"`, `"int"`, `"string"`, `"bool"`, `"void"`, `"list"`, `"dict"` | tipo declarado com palavra-chave (`number x = ...`) |
| `"number"`, `"string"`, `"bool"`, `"list"`, `"matrix"`, `"c_channel"` | tipo inferido do inicializador em `var x = ...` |
| nome de uma classe declarada | inferido de `new Classe(...)` ou de `this` |
| `"var"` | sem tipo conhecido: parâmetros, iterador de `for in` e `var x = ...` cujo inicializador não tem tipo inferível (ex.: chamada de função) |

`"unknown"` nunca aparece em `symbols`: o semântico usa `"var"` nesse caso. Um `var` inicializado com o nome de uma função ou classe herda hoje `"FUNC"`/`"CLASS"` no semântico; o serviço o publica como `"var"`. Tipos novos entram como `v1.1`.

- Ordem: ordem de definição durante a análise. Só entram símbolos efetivamente definidos: uma redeclaração (`SEM_REDECLARED`) não gera segunda entrada.
- Com `semantic.status = "error"`, `scopes` e `symbols` trazem o que foi registrado até o fim da análise (o semântico atual percorre o programa inteiro mesmo com erros).
- **Mudança necessária no A:** hoje os escopos internos são descartados ao sair do bloco e só o escopo global sobrevive à análise. O serviço precisa registrar escopos e símbolos no momento em que são criados.

**`tac.text`** e **`cpp.text`**: texto completo gerado, com `\n`. `tac` também traz `"lines": int`. O texto C++ é o mesmo que seria gravado em `.cpp`. Gerar esse texto **sem** compilar exige separar a tradução do `g++` dentro do `CppCodeGenerator.generate` atual.

**`gpp`** (só em `compile`): `{"status", "command", "returncode", "stdout", "stderr", "duration_ms"}`. `command` é a lista de argumentos usada; `stdout`/`stderr` limitados a 64 KB cada, com `"stderr_truncated": true` quando cortados.

### 1.5 Diagnósticos

```json
{"phase": "semantic", "severity": "error", "code": "SEM_UNDECLARED_VARIABLE",
 "message": "Variavel 'y' nao declarada.", "line": 1, "column": null}
```

- `phase`: uma das seis fases ou `"internal"`. `severity`: `"error"` ou `"warning"`.
- `message`: o texto que o compilador já produz, **sem** o prefixo `[ERRO ...] Linha N:` (a linha vai no campo `line`).
- `line`/`column`: base 1. `column` é `null` quando a fase não sabe (o semântico hoje só conhece a linha).
- Ordem: pela ordem das fases e, dentro da fase, pela linha. O parser atual para no primeiro erro, então há no máximo um diagnóstico sintático na v1. O semântico continua acumulando vários.

**Catálogo de códigos v1:**

| Fase | Código | Origem no código atual |
|---|---|---|
| lexer | `LEX_UNKNOWN_CHAR` | **novo**: token `UNKNOWN` |
| lexer | `LEX_UNTERMINATED_STRING` | **novo**: aspas sem fechamento até o fim do arquivo |
| parser | `SYN_EXPECTED_TOKEN` | `Parser._consume` — mensagem com `(Encontrado: '...')` |
| parser | `SYN_EXPECTED_EXPRESSION` | `Expressao esperada` |
| parser | `SYN_INVALID_ASSIGNMENT` | `Atribuicao invalida` |
| parser | `SYN_INVALID_STATEMENT` | `Instrucao ou expressao isolada invalida` |
| parser | `SYN_UNRECOGNIZED_STATEMENT` | `Instrucao nao reconhecida` |
| semantic | `SEM_REDECLARED` | `Variavel '...' ja declarada.` |
| semantic | `SEM_UNDECLARED_VARIABLE` | `Variavel '...' nao declarada.` |
| semantic | `SEM_TYPE_MISMATCH` | `Tipo incompativel ...` (declaração e atribuição) |
| semantic | `SEM_NUMERIC_OPERANDS` | `Operador '...' exige operandos numericos.` |
| semantic | `SEM_OUTSIDE_LOOP` | `'break'/'continue' usado fora de laco.` |
| semantic | `SEM_UNDECLARED_FUNCTION` | `Funcao '...' nao declarada.` |
| semantic | `SEM_UNDECLARED_CLASS` | `Classe '...' nao declarada.` |
| semantic | `SEM_UNDECLARED_SUPERCLASS` | `Superclasse '...' nao declarada.` |
| semantic | `SEM_UNDECLARED_METHOD` | `Metodo '...' nao declarado em '...'.` |
| semantic | `SEM_UNDECLARED_ATTRIBUTE` | `Atributo '...' nao declarado em '...'.` |
| semantic | `SEM_ARITY` | `... espera N argumento(s), recebeu M.` (função e método) |
| tac | `TAC_HARDCODED` (`warning`) | TAC fixo de `quicksort_iterativo` em `tac.py`, até o `CORE-02` |
| gpp | `GPP_FAILED` | `returncode` ≠ 0 |
| gpp | `GPP_NO_BINARY` | `returncode` 0 sem binário válido |
| gpp | `GPP_TIMEOUT` | compilação acima de 120 s |
| gpp | `GPP_NOT_FOUND` | compilador ausente |
| internal | `INTERNAL_ERROR` | exceção inesperada no serviço |

**Mudança de comportamento pedida ao A:** hoje o lexer não acusa nada. `var x = 2 @ 3;` vira token `UNKNOWN` e o erro aparece como sintático enganoso (`Esperado ';' apos declaracao de variavel (Encontrado: '@')`). Uma string sem aspas de fechamento engole o resto do arquivo e o erro aponta a linha seguinte. Na v1, os dois casos são erro da fase `lexer`. Código novo só pode ser acrescentado por versão `v1.1` (seção 4).

### 1.6 Execução — `minipar.execute.v1`

```json
{
  "contract": "minipar.execute.v1",
  "artifact_id": "9f1c2e7a4b3d4c5e8f6a7b8c9d0e1f2a",
  "ok": true,
  "exit_code": 0,
  "timed_out": false,
  "duration_ms": 12,
  "stdout": "5\n",
  "stderr": "",
  "stdout_truncated": false,
  "stderr_truncated": false,
  "error": null
}
```

- `ok` é `true` só com `exit_code == 0` e `timed_out == false`.
- `stdin` é entregue inteiro antes da execução; não há entrada interativa na v1. Cada `input()` do programa consome uma linha.
- `timeout_sec`: padrão 10, máximo 30. Ao estourar, o processo é encerrado, `timed_out: true` e `exit_code: null`.
- `stdout`/`stderr` limitados a 1 MB cada, com os indicadores `*_truncated`.
- Artefato inexistente ou expirado: `ok: false`, `exit_code: null` e `"error": {"code": "ARTIFACT_NOT_FOUND", "message": "..."}`.
- `artifact_id` fora do formato (32 hexadecimais) ou `timeout_sec` fora de 1–30: `ok: false` com `"error": {"code": "INVALID_ARGUMENT", ...}`, sem tocar no sistema de arquivos. O formato fixo do id impede caminhos como `../`.
- O processo encerrado por timeout não pode continuar vivo depois do retorno de `execute`.
- Programas que abrem canais de rede (`c_channel`) podem ficar bloqueados esperando o outro lado; o timeout garante o retorno.

### 1.7 Artefatos e download

- Tipos: `"cpp"`, `"tac"`, `"binary"`. Só existem para `compile_program`; `binary` só quando `gpp` terminou `ok`.
- O id é sempre o `request_id` da compilação. Nunca se devolve um arquivo de outra compilação, nem "o último `.exe` de `output/`".
- Retenção mínima: as 20 compilações mais recentes ou 60 minutos. Depois disso, `ARTIFACT_NOT_FOUND`.
- Nomes de download: `minipar_<8 primeiros do id>.cpp`, `.tac`, e `.exe` no Windows (sem extensão em Linux).
- `media_type`: `text/x-c++src`, `text/plain`, `application/octet-stream`.
- `get_artifact` com `kind` fora de `cpp`/`tac`/`binary` ou id fora do formato devolve `INVALID_ARGUMENT`; artefato que não existe nesta compilação (ex.: `binary` quando o g++ falhou) devolve `ARTIFACT_NOT_FOUND`.

**Arquivo `.arm` do Teste 11 — responsabilidade do B, sem nova função no serviço.** O `.arm` não é artefato do compilador hospedeiro: é texto que o MiniCompilador (programa MiniPar) imprime no `stdout`. A Web o obtém assim:
1. Compila o programa do Teste 11 com `compile_program` e o executa com `execute`, passando a expressão no `stdin`.
2. O navegador recorta o `stdout` recebido pelas regras de C-T11-v1 §3.6 item 2 (revisão 2): copia literalmente as linhas entre a linha de título, reconhecida pelo texto `Assembly ARMv7 (CPUlator):` no fim da linha, e a primeira linha vazia seguinte. Antes de reconhecer e copiar, o `\r` do fim de cada linha é removido, porque o stdout no Windows usa CRLF (C-T11-v1 §3.2). Título ausente ou repetido, bloco vazio, bloco que não começa com `.global _start` ou bloco sem a linha vazia que o fecha é erro exibido ao usuário. Não há marcadores próprios: os `===MINIPAR_ARM_BEGIN===`/`===MINIPAR_ARM_END===` da revisão 1 de C-T11-v1 foram revogados (§3.6.1).
3. Se `stdout_truncated` for `true`, a Web recusa a extração, porque o bloco pode estar incompleto.
4. O download é gerado no próprio navegador como `t11_<8 primeiros do artifact_id>.arm`, em UTF-8 com `\n`, terminando com uma linha em branco, como o `.arm` de referência. Não há rota nem função nova: `kind` continua limitado a `cpp`, `tac` e `binary`.

O script de linha de comando do B em `tests/2026_2/test11/` aplica as mesmas regras de §3.6, inclusive a remoção do `\r` e a gravação com `\n`, para que Web e evidências produzam o mesmo arquivo. Essa integração depende de C-T11-v1 estar aprovado (PR do `CON-03`).

### 1.8 Rotas HTTP da Web didática (responsabilidade do B)

| Método e rota | Corpo | Resposta |
|---|---|---|
| `POST /api/v1/analyze` | `{"source": "..."}` | envelope `minipar.compile.v1` |
| `POST /api/v1/compile` | `{"source": "..."}` | envelope `minipar.compile.v1` |
| `POST /api/v1/execute` | `{"artifact_id": "...", "stdin": "...", "timeout_sec": 10}` | `minipar.execute.v1` |
| `GET /api/v1/artifacts/<id>/<kind>` | — | arquivo para download |

- **HTTP 200** para todo programa processado, inclusive com erro de compilação (`ok: false`). Erro do programa do usuário não é erro HTTP.
- **HTTP 400** para requisição malformada: JSON inválido, `source` ausente, código acima de **200 000 bytes** ou `timeout_sec` fora de 1–30. Corpo: `{"error": {"code": "BAD_REQUEST", "message": "..."}}`.
- **HTTP 404** para artefato inexistente; **HTTP 500** só para falha do próprio servidor.
- O servidor escuta apenas em `127.0.0.1`. Não expor em rede sem isolamento (seção 6 do `05_VALIDACAO_E_ACEITE.md`).

### 1.9 Fixtures aprovadas (base para `WEB-01` e aceite do `CORE-08`)

Geradas pelo B em 19/10/2026 a partir das fases **reais** do commit `a37c168` (tokens, AST, símbolos, TAC e mensagens), serializadas com as regras de 1.4. Exceções, marcadas: os valores voláteis (`request_id`, `duration_ms`), o texto C++ abreviado e o erro léxico, que descreve o comportamento **contratado** (hoje o compilador não o produz). No `WEB-01` o B grava as versões completas em `web_didatica/fixtures/`, incluindo um programa maior.

#### FIX-01 — sucesso (`analyze`)

Código: string exata `"var x = 2 + 3;\nprint(x);\n"` (duas linhas, com `\n` final; o `source_hash` depende dele).

```json
{
  "contract": "minipar.compile.v1",
  "operation": "analyze",
  "request_id": "00000000000000000000000000000001",
  "ok": true,
  "source_hash": "sha256:c04f30bbe5ce38a21f9f87c8fc6949ab1bdafb922161c6cf275d9f954b73bcc6",
  "duration_ms": 0,
  "phases": {
    "lexer": {"status": "ok", "tokens": [
      {"type": "VAR", "lexeme": "var", "line": 1, "column": 1},
      {"type": "IDENTIFIER", "lexeme": "x", "line": 1, "column": 5},
      {"type": "ASSIGN", "lexeme": "=", "line": 1, "column": 7},
      {"type": "NUMBER", "lexeme": "2", "line": 1, "column": 9},
      {"type": "PLUS", "lexeme": "+", "line": 1, "column": 11},
      {"type": "NUMBER", "lexeme": "3", "line": 1, "column": 13},
      {"type": "SEMICOLON", "lexeme": ";", "line": 1, "column": 14},
      {"type": "PRINT", "lexeme": "print", "line": 2, "column": 1},
      {"type": "LPAREN", "lexeme": "(", "line": 2, "column": 6},
      {"type": "IDENTIFIER", "lexeme": "x", "line": 2, "column": 7},
      {"type": "RPAREN", "lexeme": ")", "line": 2, "column": 8},
      {"type": "SEMICOLON", "lexeme": ";", "line": 2, "column": 9}
    ]},
    "parser": {"status": "ok",
      "ast": {"id": "n0", "kind": "Program", "label": "Program", "role": null, "index": null, "line": 1, "attributes": {}, "children": [
        {"id": "n1", "kind": "VarDecl", "label": "VarDecl(x)", "role": "statements", "index": 0, "line": 1, "attributes": {"name": "x", "type": "var"}, "children": [
          {"id": "n2", "kind": "BinaryExpr", "label": "BinaryExpr(+)", "role": "init_value", "index": null, "line": 1, "attributes": {"op": "+"}, "children": [
            {"id": "n3", "kind": "NumberExpr", "label": "NumberExpr(2)", "role": "left", "index": null, "line": 1, "attributes": {"value": "2"}, "children": []},
            {"id": "n4", "kind": "NumberExpr", "label": "NumberExpr(3)", "role": "right", "index": null, "line": 1, "attributes": {"value": "3"}, "children": []}
          ]}
        ]},
        {"id": "n5", "kind": "PrintStmt", "label": "PrintStmt", "role": "statements", "index": 1, "line": 2, "attributes": {}, "children": [
          {"id": "n6", "kind": "IdentifierExpr", "label": "IdentifierExpr(x)", "role": "arguments", "index": 0, "line": 2, "attributes": {"name": "x"}, "children": []}
        ]}
      ]},
      "ast_stats": {"nodes": 7, "emitted": 7, "depth": 4, "truncated": false, "max_nodes": 5000, "max_depth": 200}
    },
    "semantic": {"status": "ok",
      "scopes": [
        {"id": "s0", "kind": "global", "name": null, "parent": null, "line": 1}
      ],
      "symbols": [
        {"name": "x", "kind": "variable", "type": "number", "scope": "s0", "line": 1, "params": []}
      ]
    },
    "tac": {"status": "ok", "text": "t0 = 2 + 3\nx = t0\nprint x\n", "lines": 3},
    "cpp": {"status": "ok", "text": "<ABREVIADO NO CONTRATO: texto completo do C++ gerado>"},
    "gpp": {"status": "skipped", "reason": "not_requested"}
  },
  "diagnostics": [],
  "artifacts": {"cpp_id": null, "tac_id": null, "binary_id": null}
}
```

#### FIX-02 — erro léxico (comportamento contratado, ainda não existente)

Código: string exata `"var x = 2 @ 3;\n"` (com `\n` final; o `source_hash` depende dele).

```json
{
  "contract": "minipar.compile.v1",
  "operation": "analyze",
  "request_id": "00000000000000000000000000000002",
  "ok": false,
  "source_hash": "sha256:8ebaae15eef31616d24eb05e9cd7aa97fec2adf777674b64aa39edb88f193bf1",
  "duration_ms": 0,
  "phases": {
    "lexer": {"status": "error", "tokens": [
      {"type": "VAR", "lexeme": "var", "line": 1, "column": 1},
      {"type": "IDENTIFIER", "lexeme": "x", "line": 1, "column": 5},
      {"type": "ASSIGN", "lexeme": "=", "line": 1, "column": 7},
      {"type": "NUMBER", "lexeme": "2", "line": 1, "column": 9},
      {"type": "UNKNOWN", "lexeme": "@", "line": 1, "column": 11},
      {"type": "NUMBER", "lexeme": "3", "line": 1, "column": 13},
      {"type": "SEMICOLON", "lexeme": ";", "line": 1, "column": 14}
    ]},
    "parser":   {"status": "skipped", "reason": "previous_phase_failed"},
    "semantic": {"status": "skipped", "reason": "previous_phase_failed"},
    "tac":      {"status": "skipped", "reason": "previous_phase_failed"},
    "cpp":      {"status": "skipped", "reason": "previous_phase_failed"},
    "gpp":      {"status": "skipped", "reason": "not_requested"}
  },
  "diagnostics": [
    {"phase": "lexer", "severity": "error", "code": "LEX_UNKNOWN_CHAR", "message": "Caractere desconhecido '@'", "line": 1, "column": 11}
  ],
  "artifacts": {"cpp_id": null, "tac_id": null, "binary_id": null}
}
```

#### FIX-03 — erro sintático

Código: string exata `"var x = 2 + ;\n"` (com `\n` final; o `source_hash` depende dele). Mensagem real atual: `Expressao esperada`, na linha 1; a coluna é a do token encontrado (`;`).

```json
{
  "contract": "minipar.compile.v1",
  "operation": "analyze",
  "request_id": "00000000000000000000000000000003",
  "ok": false,
  "source_hash": "sha256:d055e271d45107ad4bd080e7523db2077ee31328aa3d446fa9eb6ce0e804512a",
  "duration_ms": 0,
  "phases": {
    "lexer": {"status": "ok", "tokens": [
      {"type": "VAR", "lexeme": "var", "line": 1, "column": 1},
      {"type": "IDENTIFIER", "lexeme": "x", "line": 1, "column": 5},
      {"type": "ASSIGN", "lexeme": "=", "line": 1, "column": 7},
      {"type": "NUMBER", "lexeme": "2", "line": 1, "column": 9},
      {"type": "PLUS", "lexeme": "+", "line": 1, "column": 11},
      {"type": "SEMICOLON", "lexeme": ";", "line": 1, "column": 13}
    ]},
    "parser":   {"status": "error"},
    "semantic": {"status": "skipped", "reason": "previous_phase_failed"},
    "tac":      {"status": "skipped", "reason": "previous_phase_failed"},
    "cpp":      {"status": "skipped", "reason": "previous_phase_failed"},
    "gpp":      {"status": "skipped", "reason": "not_requested"}
  },
  "diagnostics": [
    {"phase": "parser", "severity": "error", "code": "SYN_EXPECTED_EXPRESSION", "message": "Expressao esperada", "line": 1, "column": 13}
  ],
  "artifacts": {"cpp_id": null, "tac_id": null, "binary_id": null}
}
```

#### FIX-04 — erro semântico

Código: string exata `"print(y);\n"` (com `\n` final; o `source_hash` depende dele). Mensagem real atual: `Variavel 'y' nao declarada.`, linha 1. A AST é devolvida porque o parser terminou.

```json
{
  "contract": "minipar.compile.v1",
  "operation": "analyze",
  "request_id": "00000000000000000000000000000004",
  "ok": false,
  "source_hash": "sha256:02f8182f02049699050146c15b6f8ae98902571c6a71c079036921d83cfb95fb",
  "duration_ms": 0,
  "phases": {
    "lexer": {"status": "ok", "tokens": [
      {"type": "PRINT", "lexeme": "print", "line": 1, "column": 1},
      {"type": "LPAREN", "lexeme": "(", "line": 1, "column": 6},
      {"type": "IDENTIFIER", "lexeme": "y", "line": 1, "column": 7},
      {"type": "RPAREN", "lexeme": ")", "line": 1, "column": 8},
      {"type": "SEMICOLON", "lexeme": ";", "line": 1, "column": 9}
    ]},
    "parser": {"status": "ok",
      "ast": {"id": "n0", "kind": "Program", "label": "Program", "role": null, "index": null, "line": 1, "attributes": {}, "children": [
        {"id": "n1", "kind": "PrintStmt", "label": "PrintStmt", "role": "statements", "index": 0, "line": 1, "attributes": {}, "children": [
          {"id": "n2", "kind": "IdentifierExpr", "label": "IdentifierExpr(y)", "role": "arguments", "index": 0, "line": 1, "attributes": {"name": "y"}, "children": []}
        ]}
      ]},
      "ast_stats": {"nodes": 3, "emitted": 3, "depth": 3, "truncated": false, "max_nodes": 5000, "max_depth": 200}
    },
    "semantic": {"status": "error",
      "scopes": [
        {"id": "s0", "kind": "global", "name": null, "parent": null, "line": 1}
      ],
      "symbols": []
    },
    "tac":      {"status": "skipped", "reason": "previous_phase_failed"},
    "cpp":      {"status": "skipped", "reason": "previous_phase_failed"},
    "gpp":      {"status": "skipped", "reason": "not_requested"}
  },
  "diagnostics": [
    {"phase": "semantic", "severity": "error", "code": "SEM_UNDECLARED_VARIABLE", "message": "Variavel 'y' nao declarada.", "line": 1, "column": null}
  ],
  "artifacts": {"cpp_id": null, "tac_id": null, "binary_id": null}
}
```

### 1.10 Responsabilidades, aceite e pendências

**A comprova (`CORE-08`)** com testes automatizados executados de verdade, registrando comandos e saídas no handoff:

| ID | Teste | Oráculo |
|---|---|---|
| ACE-01 | `analyze` dos códigos de FIX-01 a FIX-04 | saída igual à fixture, **ignorando apenas** `request_id`, `duration_ms`, ids de `artifacts` e o texto abreviado de `cpp`. FIX-02 só passa depois de PEND-WEB-01 |
| ACE-02 | `compile_program` + `execute` do código de FIX-01, stdin vazio | `ok: true` nos dois; `stdout` igual a `"5\n"`, `exit_code` 0 |
| ACE-03 | `compile_program` de código que passa no semântico e falha no g++ (exemplo atual: sonda "literal string em `var s = "123"` + `len(s)`" de C-T11-v1 §3.2, FAIL no g++ no commit `a37c168`) | `gpp.status: "error"`, diagnóstico `GPP_FAILED`, `binary_id: null`; `get_artifact(id, "binary")` devolve `ARTIFACT_NOT_FOUND`. Se não restar nenhum programa assim, testar com `CXX` apontando para executável inexistente e esperar `GPP_NOT_FOUND` |
| ACE-04 | **Isolamento sequencial:** `compile_program("print(1);\n")` e depois `compile_program("print(2);\n")` | `request_id` e `source_hash` diferentes; `execute(id1)` dá `"1\n"` e `execute(id2)` dá `"2\n"`; o SHA-256 dos artefatos de `id1` é o mesmo antes e depois da segunda compilação |
| ACE-05 | **Isolamento concorrente:** as duas compilações de ACE-04 disparadas ao mesmo tempo em duas threads, repetido 5 vezes | em todas as rodadas cada id executa a própria saída; nenhum artefato trocado ou sobrescrito |
| ACE-06 | **Sem estado residual:** `analyze` do código de FIX-04 seguido de `analyze` do código de FIX-01 | o segundo resultado é idêntico a ACE-01/FIX-01: nenhum diagnóstico, escopo ou símbolo herdado |
| ACE-07 | **Timeout de execução:** compilar `while (true) {\n    print(".");\n}\n` e executar com `timeout_sec: 2` | `ok: false`, `timed_out: true`, `exit_code: null`, `duration_ms` < 3500, `stdout_truncated: true` se o limite de 1 MB foi atingido; nenhum processo do binário vivo depois do retorno (conferido no gerenciador de tarefas ou `tasklist`/`ps`) |
| ACE-08 | **Associação de artefatos:** `get_artifact` de `cpp`, `tac` e `binary` para os ids de ACE-04 | cada arquivo pertence à própria requisição (o `.cpp` de `id1` contém a tradução de `print(1)`, não de `print(2)`); nomes seguem 1.7 |
| ACE-09 | **Argumentos inválidos:** `execute`/`get_artifact` com id `"../x"`, id inexistente de 32 hexadecimais, `kind: "arm"` e `timeout_sec: 0` e `31` | `INVALID_ARGUMENT` para formato, `kind` e timeout; `ARTIFACT_NOT_FOUND` para o id inexistente; nada lido ou criado fora do diretório de artefatos |
| ACE-10 | **Retenção:** 21 compilações seguidas | as 20 mais recentes continuam acessíveis por `get_artifact` |
| ACE-11 | **AST grande:** `analyze` de um programa gerado com mais de 5000 nós, e a serialização chamada diretamente sobre uma AST montada em Python com profundidade 250 (o parser recursivo atual pode não aceitar esse aninhamento em código-fonte) | `truncated: true`, `emitted` ≤ 5000, marcadores `max_nodes`/`max_depth` conforme 1.4 e nenhuma exceção de recursão na serialização |
| ACE-12 | Regressão de interfaces | terminal e Web antiga continuam funcionando (`CORE-09`) |

**B comprova (`WEB-01` a `WEB-04`):**
- a interface funciona só com as fixtures enquanto o `CORE-08` não existe, identificada como **mock**;
- na integração, nenhum dado é fixo no fluxo real: tudo vem do serviço;
- respostas com `source_hash` diferente do código atual do editor são descartadas (teste: editar o código durante uma análise lenta);
- execução e download usam o `artifact_id` da compilação exibida, inclusive depois de uma nova compilação em outra aba;
- extração do `.arm` (1.7) com seis saídas de teste: bloco válido com fim de linha `\n`, o mesmo bloco com `\r\n`, título ausente, título repetido, bloco que não começa com `.global _start` e bloco sem linha vazia de fechamento; só as duas primeiras geram arquivo, ambos iguais byte a byte entre si e ao produzido pelo script de `tests/2026_2/test11/`.

**Processo:** campo novo pedido pela Web vira CR (versão `v1.1` se for aditivo). B não edita `src/`.

| ID | Pendência | Dono |
|---|---|---|
| PEND-WEB-01 | Detecção de erros léxicos (`LEX_*`) não existe no lexer atual | A |
| PEND-WEB-02 | Parser encerra o processo com `sys.exit`; precisa virar diagnóstico | A |
| PEND-WEB-03 | Semântico descarta escopos internos; tabela de símbolos completa exige registro durante a análise | A |
| PEND-WEB-04 | `CppCodeGenerator.generate` traduz e compila juntos e grava em `output/` relativo ao diretório atual; precisa separar tradução e compilação e usar diretório por requisição | A |
| PEND-WEB-05 | Enquanto o `CORE-02` não for feito, o TAC de programas com `quicksort_iterativo` é texto fixo. O serviço deve emitir `warning` `TAC_HARDCODED` nesses casos até a correção | A |

### 1.11 Aprovação

| Parte | Responsável | Decisão | Data |
|---|---|---|---|
| B — consumidor | José Riquelme | Proposta apresentada | 19/10/2026 |
| A — fornecedor | Coordenador | *pendente* | |

---

## 2. C-FJ-v1 — Fork/Join, execução local e remota

**Estado:** `v1 — PROPOSTA DE CONGELAMENTO, revisão 2` (23/10/2026), redigida pelo C (Erasmo) no card `CON-01`. A revisão 1 é de 22/10/2026; a revisão 2 atende à revisão do PR #7 (tipagem do `task`, retorno do `join`, wrappers e isolamento), alinhada ao que o A implementou no `CORE-04`/`CORE-05` (PR #15), e registra os ajustes de robustez do `RUN-02` (envio assíncrono com limite, `RESULT` grande, versão em toda mensagem). Passa a `v1 FROZEN` quando A aprovar o PR (quadro em 2.10). Até lá, nenhum lado trata as sintaxes abaixo como definitivas.

**Fornecedores conjuntos:** A (linguagem, semântico e código gerado: `CORE-04`, `CORE-05`, `CORE-06`, `CORE-07`) e C (runtime: `RUN-01`, `RUN-02`, `RUN-03`, `RUN-04`). **Consumidores:** A (backend) e os testes 8–10 do C. **Prazo:** contrato no Marco 1 (22/10).

**Divisão de responsabilidades nesta proposta.** As seções 2.3 a 2.7 (API C++, tipos, erros e protocolo) são a parte do C: estão **implementadas e testadas** em `runtime/` nos cards `RUN-01` e `RUN-02` (prova isolada em C++, sem `src/`). A seção 2.2 (sintaxe e semântica MiniPar) é **proposta do C para decisão do A**: A pode trocar palavras-chave ou a forma da produção sem mudar a API, desde que mantenha os efeitos de 2.1.

### 2.1 Modelo semântico alvo

- Um `fork` inicia uma **tarefa assíncrona** reconhecida, com identificador/handle.
- O `join` bloqueia até a tarefa terminar ou retornar um erro explícito (falha, timeout, destino inacessível).
- Tarefas recebem **entradas copiadas/serializadas** em vez de capturar por referência dados externos mutáveis.
- O destino pode ser `local` ou remoto `host:port`, conforme sintaxe escolhida.
- O código de worker **já está compilado e disponibilizado nas máquinas**; enviar argumentos e nome/ID de função, não serializar código-fonte ou closures.
- Comunicação entre participantes ocorre por mensagens/canais; avaliar coerência com `par`, `seq`, `c_channel`, `send` e `receive` herdados.
- Tarefa remota executa de fato trabalho em outro processo/computador; localhost é prova de protocolo, não prova remota.
- `join` associa corretamente cada resultado à tarefa e não depende da ordem de resposta.

### 2.2 Linguagem — proposta do C para decisão do A

Respostas propostas às sete perguntas do G0:

| # | Pergunta | Proposta | Motivo |
|---|---|---|---|
| 1 | Fork é expressão ou statement? | **Expressão** que devolve um valor do tipo `task` (handle) | T08 guarda 4 handles em lista/variáveis e faz `join` depois; expressão cobre os dois usos |
| 2 | Onde fica o destino? | No código: sufixo opcional `on <expressao_string>`; sem sufixo = `"local"`. A string é `"local"` ou `"host:porta"` | O enunciado pede o programa descrevendo a distribuição; uma expressão permite ler o host de `input()` na demo sem recompilar |
| 3 | O que o `join` recebe? | Um handle: `join(h)`; com limite opcional `join(h, timeout_ms)`. Lista de handles = laço em MiniPar | Mantém a API mínima; lista não exige tipo novo |
| 4 | Que funções podem ser tarefas? | Só `func` declaradas no **nível global** (não métodos, não blocos). O ID da função é o próprio nome | O worker precisa da função já compilada e registrada por nome |
| 5 | Tipos que cruzam a rede | `number` (inteiro ou real), `bool`, `string`, e listas desses (inclusive aninhadas). **Não** cruzam: objetos de classe, `c_channel`, `task` | Cobre T08–T10 (notas, coordenadas, linhas de fractal como strings) |
| 6 | Relação com `par` e captura | `par` continua como está (blocos compartilham escopo por referência). `fork` **copia** os argumentos no momento do disparo; a função da tarefa só usa seus parâmetros e variáveis locais | Isolamento verificável e igual no local e no remoto |
| 7 | Erros | Semântico (A) rejeita os casos de 2.2.2; runtime devolve `TaskResult` com código de 2.5; `join` que falha encerra o programa com mensagem e código 1 (2.2.3) | Erro explícito, nunca bloqueio infinito nem valor inventado |

#### 2.2.1 Produções propostas (adição à BNF 2026.1)

```bnf
<expressao_fork> ::= "fork" <IDENTIFIER> "(" [ <lista_argumentos> ] ")" [ "on" <expressao> ]
<expressao_join> ::= "join" "(" <expressao> [ "," <expressao> ] ")"
<primario>       ::= ... | <expressao_fork> | <expressao_join>
```

Palavras reservadas novas: `fork`, `join`, `on`. Exemplo (o T08 real fica no `T08-01`):

```minipar
func avaliar(inicio, fim) {
    var soma = 0;
    var i = inicio;
    while (i < fim) { soma = soma + i * i; i = i + 1; }
    return soma;
}

seq {
    var destino = input("Worker (host:porta ou local): ");
    var h1 = fork avaliar(0, 40);
    var h2 = fork avaliar(40, 80) on destino;
    print("Resultados:", join(h1), join(h2, 30000));
}
```

#### 2.2.2 Regras semânticas propostas (A implementa no `CORE-05`)

| ID | Rejeitar na compilação |
|---|---|
| FJ-SEM-01 | `fork` de nome que não é `func` global (método, variável, classe, inexistente) |
| FJ-SEM-02 | Número de argumentos diferente do número de parâmetros |
| FJ-SEM-03 | `join` aplicado a expressão cujo tipo conhecido não é `task` |
| FJ-SEM-04 | `timeout_ms` ou destino com tipo conhecido incompatível (número / string) |
| FJ-SEM-05 | Função usada em `fork` que lê ou escreve variável global mutável (só parâmetros e locais), direta ou transitivamente; detalhes em 2.2.5 |
| FJ-SEM-06 | Argumento ou retorno de tipo que não cruza a rede (objeto de classe, `c_channel`, `task`) |

Destino com valor inválido em tempo de execução (ex.: `"host:abc"`) não é erro de compilação: gera `BAD_DESTINATION` no `join`.

#### 2.2.3 Tradução proposta para C++ (A implementa no `CORE-07`)

- O programa gerado inclui `#include "minipar_rt/minipar_rt.hpp"` e compila com `-I <repo>/runtime/include`. Não há biblioteca para linkar além de `-pthread` e, no Windows, `-lws2_32`.
- Para cada `func` usada em `fork`, A gera um **wrapper** `minipar_rt::TaskFn` que converte `TaskArgs` para os tipos do parâmetro (`value_cast<T>`), chama a função e devolve `to_value(retorno)`, e o registra com `register_function("<nome>", wrapper)` antes de qualquer `start`. Regras do wrapper:

  | Regra | Conteúdo |
  |---|---|
  | Um por função | Um wrapper e um `register_function` por `func` global que aparece em algum `fork`, identificado pelo **nome** (não um por ponto de chamada). Função forkada em vários pontos usa o mesmo `function_id` |
  | Em todo binário | O registro ocorre no início do `main`, antes de `worker_main_if_requested` e de qualquer `start`; como coordenador e worker são o mesmo binário, as duas pontas têm o mesmo registro |
  | Tipos conhecidos | Uma única assinatura em `fork_signatures` com tipos conhecidos: `value_cast<T>` por parâmetro e `to_value` no retorno |
  | Tipos variados ou desconhecidos | Mais de uma assinatura distinta, ou `unknown`: o wrapper recebe `Value` e despacha pelo `kind()` em tempo de execução, **ou** A rejeita o programa de forma conservadora. Escolha do A (PEND-FJ-02) |
  | Erro de conversão | `value_cast` com forma incompatível lança `std::invalid_argument`; o runtime devolve `TASK_FAILED` (2.4), nunca valor inventado |
  | Sem retorno | Função sem `return` devolve `Value` `none` (2.2.4) |
- `set_build_id("<sha256 do fonte MiniPar>")` é chamado no início do `main`, e logo depois vem `if (int rc = minipar_rt::worker_main_if_requested(argc, argv); rc >= 0) return rc;`. O **mesmo binário** vira worker com `programa --minipar-worker <porta> [--bind <ip>]`. É esse o "worker pré-compilado": compilado do mesmo fonte em cada máquina, e o build id garante que as duas pontas têm as mesmas funções.
- `fork f(a, b) on d` → `minipar_rt::start("f", {to_value(a), to_value(b)}, minipar_rt::Destination::parse(d))`.
- `join(h)` / `join(h, t)` → `minipar_rt::join_or_exit(h)` / `join_or_exit(h, t)`, que devolve o `Value` ou imprime `[minipar_rt] join <task_id> falhou: <CODIGO>: <mensagem>` em stderr e encerra com código 1.

#### 2.2.4 Tipo `task` e retorno do `join`

| Item | Contrato |
|---|---|
| Tipo `task` | Tipo estático do handle devolvido por `fork`, com o tipo de resultado associado (conceitualmente `task<T>`, `T` = retorno da função; no semântico do A, `ValueType("task", result=T)`) |
| Usos permitidos | Guardar em variável, atribuir, copiar e colocar em lista homogênea de `task`; passar para `join` |
| Usos proibidos | Cruzar tarefas como argumento ou retorno (FJ-SEM-06); aritmética (FJ-SEM-06); `join` em expressão de tipo conhecido diferente de `task` (FJ-SEM-03) |
| Cópia | Copiar um handle **não** cria tarefa nova: as cópias apontam para a mesma tarefa. O primeiro `join` em qualquer cópia coleta o resultado; outro `join` (na mesma ou em outra cópia) dá `INVALID_HANDLE` (RT-07) e, em MiniPar, encerra o programa |
| Representação C++ | `minipar_rt::TaskHandle` (struct copiável de `id` e `task_id`); listas de `task` viram `std::vector<TaskHandle>` |
| Tipo do `join(h)` | `T` da assinatura do `fork` que gerou `h` (`fork_signatures`). Em C++, `join_or_exit` devolve `Value`; o backend converte com `value_cast<T>` quando `T` é conhecido e mantém `Value` quando não é |
| Função sem `return` | O resultado é `Value` `none` (o tipo `void` é aceito no transporte). Se usar esse valor em expressão é erro de compilação ou de execução é decisão do A (PEND-FJ-07) |
| `timeout_ms` | Expressão numérica (FJ-SEM-04). O backend converte para `int` truncando. Valor negativo equivale a sem limite: local espera o tempo que for, remoto usa o padrão de 60 s (RT-06), como `join(h, -1)` da API |
| Falha no `join` MiniPar | Qualquer erro, inclusive `TIMEOUT`, encerra o programa com código 1 via `join_or_exit`. "Handle continua válido depois do `TIMEOUT`" (RT-05) vale só para a API C++ `join`; MiniPar v1 não tem nova tentativa |

#### 2.2.5 Isolamento das funções de tarefa (FJ-SEM-05)

Verificado pelo semântico do A (`CORE-05`):

| Regra | Conteúdo |
|---|---|
| Dados acessíveis | Só parâmetros e variáveis locais da função. Ler ou escrever variável global que não seja `func` ou `class` é erro |
| Transitividade | A verificação percorre as funções chamadas, os métodos e os inicializadores de objetos usados pela tarefa, inclusive ciclos recursivos, com escopo léxico global (nunca os locais de quem chamou) |
| `this` | Proibido em função global usada como tarefa |
| Método de tipo desconhecido | Chamada rejeitada, porque não dá para comprovar o isolamento |
| Entrada | Argumentos copiados no disparo (RT-03); listas são valores copiados |

Fora do que é verificado no v1:

- `print` dentro da tarefa sai no stdout do processo que a executa: o worker, quando remoto. O resultado volta ao coordenador só pelo `return`.
- `input`, `c_channel`, `send` e `receive` dentro da tarefa não fazem parte do contrato v1. Rejeitar ou permitir é decisão do A (PEND-FJ-06).
- A inferência de tipos genéricos, retornos recursivos e coleções mutadas é parcial; o que não é comprovado fica em `unresolved_fj` (handoff do `CORE-04`/`05`).

### 2.3 API C++ do runtime (implementada no `RUN-01`/`RUN-02`)

Biblioteca **header-only** em `runtime/include/minipar_rt/` (C++20, só biblioteca padrão e sockets do SO). Assinaturas públicas:

```cpp
namespace minipar_rt {
  class Value;                                   // ver 2.4
  using TaskArgs = std::vector<Value>;
  using TaskFn   = std::function<Value(const TaskArgs&)>;

  enum class ErrorCode { NONE, TASK_FAILED, UNKNOWN_FUNCTION, TIMEOUT, WORKER_UNAVAILABLE,
                         WORKER_LOST, INVALID_HANDLE, PROTOCOL_ERROR, VERSION_MISMATCH, BAD_DESTINATION };
  struct TaskError  { ErrorCode code; std::string message; };
  struct TaskHandle { std::uint64_t id; std::string task_id; };          // task_id = "task-<n>"
  struct TaskResult { bool ok; Value value; TaskError error; std::string task_id;
                      std::string executed_by; };                       // "local:<pid>" ou "<host>:<pid>"
  struct Destination {
    static Destination local();
    static Destination remote(std::string host, std::uint16_t port);
    static Destination parse(const std::string& text);                  // "local" | "host:porta"
  };

  void register_function(const std::string& function_id, TaskFn fn);
  void set_build_id(std::string build_id);
  TaskHandle start(const std::string& function_id, TaskArgs args,
                   const Destination& where = Destination::local());
  TaskResult join(const TaskHandle& handle, int timeout_ms = -1);
  Value      join_or_exit(const TaskHandle& handle, int timeout_ms = -1);
  int  run_worker(std::uint16_t port, const std::string& bind_address = "127.0.0.1");
  int  worker_main_if_requested(int argc, char** argv);                 // -1 se não é modo worker
}
```

Garantias:

| ID | Garantia |
|---|---|
| RT-01 | `start` **não espera** o cálculo nem a rede: dispara uma thread local, ou coloca o `TASK` na fila da conexão (uma thread escritora por conexão faz o envio), e retorna o handle |
| RT-02 | `start` nunca lança exceção por falha de destino; a falha aparece no `join` (`WORKER_UNAVAILABLE`, `BAD_DESTINATION`, `VERSION_MISMATCH`) |
| RT-03 | `args` é recebido **por valor** (cópia ou `move`); mudar a variável original depois do `start` não afeta a tarefa |
| RT-04 | `join` devolve o resultado do handle certo, qualquer que seja a ordem de término |
| RT-05 | `join(h, t)` com `t >= 0` devolve `TIMEOUT` se a tarefa não acabou em `t` ms; o handle **continua válido** e um `join` posterior pode coletar o resultado |
| RT-06 | `join(h)` sem limite: tarefa local espera o tempo que for; tarefa remota usa o limite padrão de 60 s (`MINIPAR_RT_REMOTE_TIMEOUT_MS`) |
| RT-07 | Depois de um resultado coletado (ok ou erro final), novo `join` no mesmo handle → `INVALID_HANDLE`. Handle desconhecido → `INVALID_HANDLE` |
| RT-08 | Exceção lançada pela função da tarefa → `TASK_FAILED` com a mensagem; o processo não cai |
| RT-09 | Conexão com o worker perdida com tarefas pendentes → todas recebem `WORKER_LOST`, sem bloqueio. Vale também para envio parado: se o `send` não progride por `MINIPAR_RT_SEND_TIMEOUT_MS` (padrão 10000 ms), a conexão é fechada |
| RT-10 | Thread-safe: `start`/`join` podem ser chamados de threads diferentes (inclusive dentro de `par`) |

### 2.4 Tipos que cruzam tarefas (`Value`)

`Value` é um tipo-valor com uma das formas: `none`, `int` (`int64`), `float` (`double`), `bool`, `string` (UTF-8), `list` (vetor de `Value`). Conversões fornecidas:

- `to_value(x)` para inteiros, `double`, `bool`, `std::string`, `const char*`, `std::vector<T>` (recursivo) e `Value`;
- `value_cast<T>(v)` para os mesmos tipos. Entre `int` e `float` a conversão é numérica; para os demais tipos, uma forma diferente lança `std::invalid_argument`, que a tarefa devolve como `TASK_FAILED`.

### 2.5 Códigos de erro

| Código | Quando |
|---|---|
| `TASK_FAILED` | A função lançou exceção (local ou no worker), um valor não pôde ser convertido, ou o `TASK`/`RESULT` passaria de 8 MiB (o worker responde o erro em vez de ficar calado) |
| `UNKNOWN_FUNCTION` | `function_id` não registrado (local ou no worker) |
| `TIMEOUT` | Limite do `join` esgotado (handle continua válido, RT-05) |
| `WORKER_UNAVAILABLE` | Não conectou ao `host:porta` (recusado, sem rota, host não resolvido) dentro de 3 s |
| `WORKER_LOST` | Conexão caiu com a tarefa pendente (worker morto, rede caiu) ou o envio ficou parado por mais de `MINIPAR_RT_SEND_TIMEOUT_MS` (worker que não lê) |
| `INVALID_HANDLE` | Handle desconhecido ou já coletado |
| `PROTOCOL_ERROR` | Frame inválido, JSON inválido, mensagem fora de ordem |
| `VERSION_MISMATCH` | `protocol_version` (em qualquer mensagem) ou `build_id` diferentes entre coordenador e worker |
| `BAD_DESTINATION` | Texto de destino que não é `local` nem `host:porta` válido |

### 2.6 Protocolo remoto (implementado no `RUN-02`)

**Transporte:** TCP, **uma conexão persistente por destino** (`host:porta`), aberta no primeiro `start` para ele e reutilizada. Várias tarefas ficam pendentes na mesma conexão; o worker executa cada `TASK` em sua própria thread e responde na ordem em que terminar. No coordenador, o `start` só enfileira o `TASK`; uma thread escritora por conexão envia, com limite de envio parado (RT-09).

**Frame:** 4 bytes de tamanho em ordem de rede (big-endian, sem sinal), seguidos de `N` bytes de JSON UTF-8 com um objeto. `1 <= N <= 8 MiB`; `N = 0` ou `N > 8 MiB` é `PROTOCOL_ERROR`. Leitura com `recv_exact` (acumula até completar o tamanho, aceitando fragmentação) e escrita com `send_all`. A codificação JSON é própria do runtime (subconjunto estrito, sem biblioteca externa).

**Codificação de `Value` no JSON:** `none` → `null`; `bool` → `true`/`false`; `int` → número sem ponto nem expoente; `float` → número **sempre** com ponto ou expoente (ex.: `2.0`); `string` → string JSON; `list` → array. `NaN` e infinito não são enviados (`TASK_FAILED` na origem).

**Mensagens** (todos os objetos têm `"protocol_version": 1` e `"type"`):

| type | Sentido | Campos | Observação |
|---|---|---|---|
| `HELLO` | coord → worker | `build_id`, `request_id` | Obrigatória e primeira em cada conexão |
| `HELLO_OK` | worker → coord | `worker_id`, `host`, `pid`, `build_id` | `worker_id = "<host>:<pid>"` |
| `TASK` | coord → worker | `request_id`, `task_id`, `function_id`, `args` (array) | |
| `RESULT` | worker → coord | `request_id`, `task_id`, `status` (`ok`/`error`), `result` ou `error{code,message}`, `worker_id` | Associado pelo `task_id`, nunca pela ordem |
| `ERROR` | qualquer | `error{code,message}` | Erro de conexão (versão, frame); quem envia fecha a conexão em seguida |

Exemplos:

```json
{"protocol_version":1,"type":"HELLO","build_id":"3f2a...","request_id":"run-4120-1"}
{"protocol_version":1,"type":"HELLO_OK","worker_id":"pc-lab-2:7744","host":"pc-lab-2","pid":7744,"build_id":"3f2a..."}
{"protocol_version":1,"type":"TASK","request_id":"run-4120-1","task_id":"task-4","function_id":"avaliar","args":[20,35]}
{"protocol_version":1,"type":"RESULT","request_id":"run-4120-1","task_id":"task-4","status":"ok","result":55,"worker_id":"pc-lab-2:7744"}
{"protocol_version":1,"type":"RESULT","request_id":"run-4120-1","task_id":"task-5","status":"error","error":{"code":"TASK_FAILED","message":"divisao por zero"},"worker_id":"pc-lab-2:7744"}
```

**Versão:** `protocol_version` é conferido em **toda** mensagem, nos dois lados; `build_id` é conferido no `HELLO`. Se diferem, o worker responde `ERROR` `VERSION_MISMATCH` e fecha a conexão; o coordenador que recebe mensagem de outra versão fecha a conexão. Em ambos os casos as tarefas daquela conexão terminam com `VERSION_MISMATCH`.

**Resultado grande:** se o `RESULT` passaria de 8 MiB, o worker responde `RESULT` com `status` `error` e `TASK_FAILED`, sem fechar a conexão.

**Robustez do worker:** frame ou JSON inválido em uma conexão gera `ERROR` `PROTOCOL_ERROR` e fecha **só essa conexão**; o worker continua aceitando outras. O worker registra em stderr `worker_id`, host, PID, endereço do coordenador, `task_id`, função e duração de cada tarefa.

**Segurança operacional:** o worker escuta em `127.0.0.1` por padrão; escutar na rede exige `--bind <ip>` explícito (necessário no `RUN-03`). Ele só executa funções **registradas no binário**; nada de código recebido pela rede. Uso acadêmico em rede local, sem autenticação nem criptografia: não expor à internet.

### 2.7 Critérios de teste do runtime

- `start` retorna antes do cálculo longo terminar (assíncrono).
- `join` aguarda conclusão real e devolve resultados identificados.
- Dois trabalhos concluem fora de ordem sem troca de resultados.
- O worker remoto executa cálculo verificável e registra endereço/host/PID.
- Perda do worker antes da resposta produz erro e não bloqueio infinito.
- Protocolo suporta mensagens fragmentadas e maiores que um `recv` simples.
- Execução local não utiliza captura por referência de variável mutável para passagem de entrada.
- Pelo menos **duas máquinas físicas** na prova final, com comandos reproduzíveis.
- Teste 8 divide 160 tarefas sem perda/duplicação.
- As funções são reais, não apenas strings prontas devolvidas para a demonstração.

O mapeamento de cada critério para o teste automatizado que o cobre está em `runtime/README.md`.

### 2.8 Compatibilidade com runtime antigo

`MiniParChannel` atual usa TCP básico com listener a cada mensagem e `send`/`recv` únicos. O baseline do `CORE-01` mostrou que isso trava o T01 de forma intermitente (DEF-01 em `docs/auditorias/CORE-01_BASELINE_T01_T07.md`). **Decisão proposta:** o runtime de Fork/Join é um componente **novo** (`runtime/`) e não altera `c_channel`/`send`/`receive`; a correção do canal herdado é card de A. Se A quiser, pode reaproveitar `minipar_rt/net.hpp` (`send_all`, `recv_exact`, frames) nessa correção, sem mudar a interface MiniPar do canal. Regressão do Teste 1 é obrigatória em qualquer mudança.

### 2.9 Pendências registradas

| ID | Pendência | Dono | Impacto se não resolver |
|---|---|---|---|
| PEND-FJ-01 | A decide palavras-chave e forma final de 2.2 (pode trocar `on` ou a forma do `join` sem mudar a API de 2.3) | A | `CORE-04` não começa |
| PEND-FJ-02 | Wrapper com tipos variados ou desconhecidos (2.2.3): despachar pelo `kind()` do `Value` em tempo de execução ou rejeitar o programa. O `CORE-05` já entrega `fork_signatures` e `unresolved_fj` | A | Wrapper do `CORE-07` |
| PEND-FJ-03 | Prova em duas máquinas físicas (`RUN-03`): depende de duas máquinas na mesma rede e de liberar a porta do worker no firewall de uma delas, ação da pessoa que roda a prova | C + equipe | G1 sem prova remota (plano de contingência do doc 01, M1) |
| PEND-FJ-04 | Limite padrão de 60 s do `join` remoto sem timeout (RT-06): confirmar com as cargas do T08–T10 | C | Join remoto longo encerrado cedo |
| PEND-FJ-05 | Interpretação do professor sobre despacho remoto automático (doc 00, P02). Esta proposta faz despacho **explícito** por destino no código | Trio | Reabrir 2.2 se o professor exigir alocação automática |
| PEND-FJ-06 | `input`, `c_channel`, `send` e `receive` dentro de função de tarefa (2.2.5): rejeitar no semântico ou permitir com comportamento documentado | A | Tarefa remota esperando stdin do worker ou canal sem par |
| PEND-FJ-07 | Uso do resultado de `join` de função sem `return` (`none`, 2.2.4): erro de compilação ou de execução | A | Valor `none` usado em expressão no C++ gerado |

### 2.10 Aprovação

| Parte | Responsável | Decisão | Data |
|---|---|---|---|
| C — runtime | Erasmo | Proposta revisão 1: API, tipos, erros e protocolo implementados e testados (`RUN-01`/`RUN-02`); linguagem proposta para decisão do A | 22/10/2026 |
| C — runtime | Erasmo | Revisão 2: tipo `task`, retorno do `join`, wrappers e isolamento detalhados (2.2.3–2.2.5) conforme `CORE-04`/`05`; envio assíncrono com limite, `RESULT` grande e versão em toda mensagem (2.3, 2.5, 2.6); PEND-FJ-06/07 | 23/10/2026 |
| A — linguagem e backend | Coordenador (Victor) | *pendente* | |

Mudança depois do congelamento segue a seção 4 (CR). Funções novas no runtime que não mudam as assinaturas acima entram como `v1.1` aditiva.

---

## 3. C-T11-v1 — MiniCompilador escrito em MiniPar

**Estado:** `v1 — PROPOSTA DE CONGELAMENTO, revisão 2` (22/10/2026). A revisão 1 foi redigida pelo B em 19/10/2026 no card `CON-03`; a revisão 2 incorpora os ajustes pedidos na revisão de 22/10 (quadro em 3.10). Passa a `v1 FROZEN` quando A aprovar o PR. Até lá, nenhum lado trata as sintaxes abaixo como definitivas.

**Conferido contra a referência do professor em 22/10/2026.** Os três anexos do Classroom estão, sem alteração de conteúdo, em `docs/fontes/teste11/`: `MiniCompiladorCompleto_ARMv7.java` (o MiniCompilador), `Codigo-Assembly-ARMV7.arm` (o `.arm` de referência) e `Execucao-Saida-okRodounoCPULATOR.txt` (a saída de uma execução de `((2+4)*7)-(5*4)`). A comparação item a item está em 3.11, e o formato de saída que o T11 reproduz está em 3.12.

**Fornecedor de primitivas:** A (`CORE-03`). **Consumidor de linguagem:** B (`T11-01`, `T11-02`, `T11-03`). **Prazo:** contrato e primitivas no Marco 1 (22/10); `.arm` validado no CPUlator no Marco 2 (29/10).

### 3.1 Escopo da aplicação

MiniCompilador implementado **na linguagem MiniPar**, com tokenização, análise com precedência, AST, TAC, tabela de símbolos, avaliação e texto Assembly ARMv7, todos produzidos por lógica MiniPar. O compilador hospedeiro só compila e executa esse programa.

O comunicado do Teste 11 pede para implementar o MiniCompilador em MiniPar 2026.2 **atualizando a BNF e os módulos do compilador necessários**. Por isso toda primitiva nova do `CORE-03` (3.3) entra também na `BNF-grammar.md` (tabela da biblioteca nativa e tabela de tradução para C++), e não só em `src/`.

**Entrada:** uma expressão por execução, lida com `input("Digite uma expressão infixada: ")` (uma linha do stdin), como o `Scanner.nextLine()` da referência. Os três casos obrigatórios são três execuções do mesmo binário:

| Caso | Entrada (stdin) | Resultado | Registrador final no ARM |
|---|---|---:|---|
| 1 | `((2+4)*7)-(5*4)` | 22 | `r8` |
| 2 | `((10 -8*7)+4)*2` | -84 | `r8` |
| 3 | `((2+4)*7)-(5*4)` | 22 | `r8` |

**Linguagem de expressões aceita na v1:**
- inteiros não negativos com um ou mais dígitos (`10`, `8`), sem zero à esquerda (`0` sozinho vale);
- operadores `+`, `-`, `*` com precedência usual (`*` antes de `+`/`-`) e associatividade à esquerda, por descida recursiva `expr → term → factor`, como a referência;
- parênteses aninhados;
- espaços ignorados (o caso 2 contém espaço);
- `#` inicia comentário até o fim da linha, como na referência.

**Rejeitado com mensagem de erro explícita, nunca resultado silencioso nem Assembly inválido:** menos unário, números decimais, zero à esquerda (`010`), identificadores e `=`, caracteres desconhecidos, parênteses desbalanceados, tokens sobrando depois da expressão, entrada vazia e divisão `/`. A referência aceita vários desses casos e gera saída errada ou quebra (3.11); o T11 corrige rejeitando. A divisão é rejeitada porque a referência não gera ARM para ela (só um comentário, e o registrador do resultado fica sem valor).

**Saída do programa, nesta ordem, no formato exato da referência (3.12):** prompt, tokens, AST, TAC, Assembly ARMv7, tabela de símbolos e resultado final.

### 3.2 Linha de base observada (antes do `CORE-03`)

Sondagem executada pelo B em 19/10/2026 sobre o commit `a37c168` (`main`), Windows 11, Python 3.14.7, g++ 16.2.0 (MSYS2 UCRT64), pipeline real `Lexer → Parser → SemanticAnalyzer → CppCodeGenerator → g++ -std=c++20 -O3`, executando o binário com stdin fixo e comparando o stdout com o oráculo. Cada sonda tem de 1 a 10 linhas de MiniPar.

| Recurso | Resultado | Observação |
|---|---|---|
| `input()` + `len` da string lida | PASS | |
| literal string em `var s = "123"` + `len(s)` | **FAIL** (g++) | `auto s = "123"` vira `const char*` |
| acumular `acc = ""; acc = acc + "1"` | **FAIL** (g++) | mesmo motivo |
| concatenação string lida + literal | PASS | |
| comparação `==` e `>=`/`<=` entre strings | PASS | |
| `substr(s, i, n)` | **FAIL** (semântico) | função não declarada |
| `s.substr(i, n)` | **FAIL** (g++) | traduzido como `s->substr` |
| `s[0] == "("` | **FAIL** (g++) | `char` comparado a ponteiro |
| `to_string(x)` | **FAIL** (semântico) | função não declarada |
| `to_number("7") * 2` | PASS | |
| `print` de inteiros e negativos, `"\n"` em literal | PASS | |
| lista numérica: `append`, `pop`, índice, atribuição por índice, `len` | PASS | |
| função que monta e **retorna** lista | PASS | |
| classe com atributo lista alterado por método | PASS | |
| recursão (`fat(5)`) | PASS | |
| função com parâmetro e retorno string | PASS | |
| lista literal de strings `["a","b"]` | **FAIL silencioso** | compila e imprime `0` no lugar de `b` |
| lista vazia + `append("x")` | **FAIL** (g++) | `std::vector<double>` |
| variável global lida dentro de função | **FAIL** (g++) | globais são emitidas dentro de `main` |
| lista passada a função e alterada lá dentro | **FAIL silencioso** | cópia por valor, chamador não vê a alteração |
| `len(v) - 1` com `v` vazia (sondado em 22/10) | **FAIL silencioso** | imprime `18446744073709551615`: `size()` sem sinal |
| `"R" + 3` (sondado em 22/10) | **FAIL silencioso** | compila, imprime linha vazia: aritmética de ponteiro |
| função que só retorna literais string, concatenada: `"    " + mnemonico(1)` (22/10) | **FAIL** (g++) | o retorno vira `const char*`; literal + `const char*` não compila |
| método recursivo sobre atributos lista, alterando atributo numérico (22/10) | PASS | molde dos percursos da AST (TAC, ARM, avaliação) |
| método recursivo que devolve string montada por concatenação (22/10) | PASS | molde do `formatExpr` |
| objeto passado a função recursiva, alterado lá dentro (22/10) | PASS | objetos são compartilhados (`shared_ptr`); listas não |
| literal com acento e emoji (`"⚙️ Assembly ARMv7 (CPUlator):"`) em `print` (22/10) | PASS | bytes UTF-8 saem intactos; stdout no Windows usa CRLF |

Status desta tabela vale só para o commit indicado. Ela não substitui a baseline T01–T07 do `CORE-01`.

### 3.3 Primitivas obrigatórias (P0) — fornecidas por A no `CORE-03`

| ID | Primitiva | Sintaxe congelada | Semântica exigida |
|---|---|---|---|
| PRIM-01 | string com armazenamento real | `var s = "abc";` · `string s = "abc";` · `var s = "";` · `return "ADD";` | toda variável, atributo de classe **e retorno de função ou método** cujo valor é literal string é uma string de verdade (no C++, `std::string`), aceitando `len`, `substr`, `+`, comparação e reatribuição. Uma função com um `return` literal e outro `return` de string calculada (`substr`, concatenação) também devolve string. Literais com acentos e emojis em UTF-8 são impressos byte a byte |
| PRIM-02 | comprimento | `len(s)` | número de caracteres de qualquer string: literal, lida, concatenada ou vinda de `substr`/`to_string`. O resultado se comporta como `number` com sinal: `len("") - 1` vale `-1` (hoje `len` vira `x.size()`, sem sinal, e a subtração dá `18446744073709551615`; ver 3.2) |
| PRIM-03 | recorte | `substr(s, inicio, tamanho)` | string com `tamanho` caracteres a partir de `inicio` (base 0). `inicio` e `tamanho` aceitam qualquer número de valor inteiro, inclusive vindo de lista numérica (`double`). Limites, índices inválidos e string vazia: especificação completa em 3.3.1 |
| PRIM-04 | número → texto | `to_string(x)` | valor inteiro sai sem casas decimais e com `-` quando negativo (`42` → `"42"`, `0 - 84` → `"-84"`), **inclusive** quando o valor vem de `to_number` ou de lista numérica (`-46.0` → `"-46"`). Valores não inteiros não são usados pelo T11; formato livre, desde que documentado |
| PRIM-05 | concatenação | `a + b` | funciona em todas as combinações: variável + literal, literal + variável, **literal + literal**, literal + `to_string(...)`, resultado de `substr` ou de função, variável + variável, acumulação `acc = acc + c` dentro de laço e acumulação em **atributo string de classe** (`this.texto = this.texto + s`). String + número sem `to_string` (`"R" + 3`) é **rejeitado na compilação**, em qualquer fase; nunca vira aritmética de ponteiro em silêncio |
| PRIM-06 | comparação | `==` `!=` `<` `<=` `>` `>=` | entre strings, pelo **conteúdo**, em ordem lexicográfica por código de caractere (permite `c >= "0" && c <= "9"`). Vale também para **literal com literal** (`"x" == "x"`), que hoje seria comparação de ponteiros. A ordem não é numérica: `"10" < "9"` é verdadeiro, então o B só usa a faixa de dígitos em strings de 1 caractere. String comparada com número é **rejeitada na compilação** |

**Já disponíveis e cobertos por regressão** (A não deve quebrar): `input()`, `to_number`, `print` com vários argumentos, `"\n"` em literal, listas numéricas (`append`, `pop`, índice, atribuição por índice, `len`), função que retorna lista, classe com atributo lista alterado por método, recursão, `while`/`for`/`if`, funções com parâmetro e retorno string, métodos recursivos que leem atributos lista e alteram atributos numéricos, métodos recursivos que devolvem string, objeto passado a função e alterado lá dentro, literais UTF-8 em `print` (todos sondados em 22/10, 3.2), e **curto-circuito de `&&` e `||`** (o T11 protege a leitura adiante com `i < len(e) && substr(e, i, 1) ...`; sem curto-circuito, o `substr` do fim da string viraria erro de execução).

**BNF:** `substr` e `to_string` entram na tabela "Biblioteca Nativa" da `BNF-grammar.md` (assinatura, retorno e descrição) e na tabela de tradução MiniPar → C++. A regra de tipos de `len`, `+` e das comparações entre strings é registrada na seção de tipos da BNF.

B **não** altera `src/` para viabilizar o algoritmo. Se faltar algo fora desta lista, B abre card para A com programa MiniPar reprodutível de 10–30 linhas.

#### 3.3.1 Especificação do `substr`

**Assinatura:** `substr(s, inicio, tamanho)` → `string`. Exatamente três argumentos (outro número de argumentos é erro semântico). `s` é string; `inicio` e `tamanho` são `number`. A forma de método `s.substr(i, n)` não faz parte do contrato.

**Unidade:** um caractere = um byte, a mesma unidade de `len`. As entradas do T11 são ASCII. Os acentos e emojis da saída da referência (`🔍`, `é`, `→`...) aparecem só em literais impressos inteiros: o T11 nunca aplica `substr` nem `len` sobre eles. Recortar ou medir strings com caracteres UTF-8 de vários bytes fica fora do contrato (o resultado conta bytes).

**Índices:** `inicio` e `tamanho` precisam ter valor inteiro exato (`2` e `2.0` valem o mesmo). Parte fracionária (`1.5`), NaN ou infinito é erro de execução; o valor **nunca** é truncado ou arredondado em silêncio.

**Domínio válido:** `0 ≤ inicio ≤ len(s)` e `0 ≤ tamanho ≤ len(s) - inicio`. O resultado é uma **cópia** dos caracteres `inicio` até `inicio + tamanho - 1`; `s` não é alterada. Qualquer valor fora desse domínio é erro de execução: **não há recorte automático** (como faz o `std::string::substr` do C++, que corta o tamanho) **nem índice negativo contado do fim** (como em Python).

| Caso | Exemplo com `s = "abc"` | Resultado |
|---|---|---|
| recorte interno | `substr(s, 1, 1)` | `"b"` |
| string inteira | `substr(s, 0, 3)` | `"abc"` |
| último caractere | `substr(s, 2, 1)` | `"c"` |
| tamanho zero no meio | `substr(s, 1, 0)` | `""` |
| tamanho zero no fim (`inicio == len`) | `substr(s, 3, 0)` | `""` |
| string vazia com `0, 0` | `substr("", 0, 0)` | `""` |
| índice vindo de lista numérica | `substr(s, pos[0], 1)` com `pos[0] = 1` | `"b"` |
| `inicio` negativo | `substr(s, 0 - 1, 1)` | erro |
| `tamanho` negativo | `substr(s, 0, 0 - 1)` | erro |
| `inicio > len` | `substr(s, 4, 0)` | erro |
| fim além do limite | `substr(s, 2, 2)` | erro (não devolve `"c"`) |
| `inicio == len` com `tamanho > 0` | `substr(s, 3, 1)` | erro |
| string vazia com `tamanho > 0` | `substr("", 0, 1)` | erro |
| índice não inteiro | `substr(s, 1.5, 1)` | erro |

**Erro de execução:** o programa escreve no **stderr** uma mensagem que contém `substr`, `inicio`, `tamanho` e `len` (sugestão: `Erro de execucao: substr fora dos limites (inicio=4, tamanho=0, len=3)`) e termina com **código de saída 1**. O que já foi impresso no stdout antes do erro precisa aparecer (saída descarregada). Exceção não tratada que vire `abort`, ou código de saída diferente de 1, não atende.

**Por que estrito:** no lexer do T11, um erro de um índice a mais com recorte automático produziria um token errado sem aviso. Com erro de execução, o defeito aparece no primeiro teste. A leitura adiante fica a cargo do B, protegida por `i < len(e) && ...`.

### 3.4 Fora do que o T11 usa (B não depende destes recursos)

Esta tabela diz só do que o **T11** deixa de depender. Ela **não retira** nenhum recurso da linguagem MiniPar 2026.2: a BNF continua com eles, e a correção segue em card próprio de A, fora do `CORE-03`.

| Recurso | Motivo | Como o B contorna |
|---|---|---|
| acesso por índice em string (`s[i]`) | produziria `char`, e a comparação com literal exigiria outro tipo na linguagem | `substr(s, i, 1)` |
| listas de strings | hoje falham, uma delas em silêncio; corrigir exige inferir o tipo do elemento. **Continuam no escopo geral do MiniPar** (PEND-T11-03) | a referência guarda tokens e valores dos nós da AST como `String`; o T11 guarda, em listas numéricas paralelas, tipo do token, **início e tamanho do lexema** na expressão, e para cada nó o índice do token e os filhos (`-1` para nenhum). O texto sai sempre de `substr(e, inicio, tamanho)`, então tokens, AST, TAC, `#k` do ARM e chaves da tabela de símbolos repetem o lexema exato. Decisão confirmada na revisão de 22/10 |
| variáveis globais dentro de funções | globais são emitidas dentro de `main` | estado em objetos de classe (atributos lista) ou passado e retornado por parâmetro |
| passagem de lista por referência | parâmetros são cópias | método de classe ou função que retorna a lista nova |
| escrita de arquivo pelo programa MiniPar | a referência Java também não grava arquivo (3.6 item 5) | exportação pelo executor (3.6) |
| expressões regulares | a referência usa `Pattern`/`Matcher` no lexer; MiniPar não tem regex | lexer por classificação de caractere com `substr` e comparações (PRIM-03, PRIM-06) |
| `HashMap` | a referência guarda a tabela de símbolos num `HashMap` | chaves deduplicadas por comparação de strings e ordenadas por valor numérico (3.12) |

**Defeito registrado para A, fora do escopo do `CORE-03`:** `var l = ["a", "b"]; print(l[1]);` compila e imprime `0`. É resultado falso sem erro. Como listas de strings continuam na linguagem, a solução esperada é **corrigir** em card próprio (lista literal e lista vazia + `append` de string, com `len`, índice e atribuição por índice). Enquanto o card não fecha, o semântico deve **rejeitar** a lista de strings com mensagem, em vez de compilar e devolver `0`. O T11 não depende de nenhuma das duas soluções.

### 3.5 Programas de prova com oráculo (aceite do `CORE-03`)

PROVA-01 a PROVA-09 e PROVA-INT precisam **compilar e executar pelo pipeline real**, sem alteração, com stdout idêntico ao oráculo (sem espaço no fim da linha) e código de saída 0. PROVA-ERR e PROVA-NEG têm oráculo próprio, descrito em cada uma. Em 19/10/2026 (PROVA-01 a 05 e INT) e em 22/10/2026 (PROVA-06 a 09, ERR e NEG) todas passam no Lexer/Parser do commit `a37c168`. PROVA-01 falha no g++. As demais param no semântico **apenas** por `substr`/`to_string` não declaradas, com exceção de NEG-01 e NEG-02 (ver PROVA-NEG).

Para reproduzir (de qualquer pasta, porque os artefatos vão para `./output`):

```bash
python C:/dev/minipar-2026-2/main.py PROVA_02.minipar
```

Depois rodar o binário `output/PROVA_02.exe` com a entrada indicada no stdin e comparar com o oráculo.

#### PROVA-01 — PRIM-01, PRIM-02

```minipar
var s = "123";
string t = "abc";
print(len(s), len(t));
```

stdin: (vazio) · stdout: `3 3`

#### PROVA-02 — PRIM-03

```minipar
var e = input();
print(substr(e, 0, 1));
print(substr(e, 2, 1));
print(substr(e, 2, 3));
print(len(substr(e, 0, 2)));
```

stdin: `((2+4)*7)-(5*4)` · stdout (4 linhas): `(` · `2` · `2+4` · `2`

#### PROVA-03 — PRIM-04

```minipar
print(to_string(42));
print(to_string(0 - 84));
print(to_string((2 + 4) * 7 - 5 * 4));
var n = to_number("10") - 8 * 7;
print(to_string(n));
```

stdin: (vazio) · stdout (4 linhas): `42` · `-84` · `22` · `-46`

#### PROVA-04 — PRIM-01, PRIM-03, PRIM-05

```minipar
var acc = "";
var e = input();
var i = 0;
while (i < len(e)) {
    var c = substr(e, i, 1);
    if (c != " ") {
        acc = acc + c;
    }
    i = i + 1;
}
print(acc);
print("MOV R0, #" + to_string(22));
print("t" + to_string(1) + " = " + acc);
var r = "R" + to_string(3);
print(r + ", " + r);
```

stdin: `10 -8*7` · stdout (4 linhas): `10-8*7` · `MOV R0, #22` · `t1 = 10-8*7` · `R3, R3`

#### PROVA-05 — PRIM-03, PRIM-06

```minipar
var e = input();
var i = 0;
var digitos = 0;
var operadores = 0;
var parenteses = 0;
while (i < len(e)) {
    var c = substr(e, i, 1);
    if (c >= "0" && c <= "9") {
        digitos = digitos + 1;
    } else {
        if (c == "+" || c == "-" || c == "*" || c == "/") {
            operadores = operadores + 1;
        } else {
            if (c == "(" || c == ")") {
                parenteses = parenteses + 1;
            }
        }
    }
    i = i + 1;
}
print(digitos, operadores, parenteses);
```

stdin: `((2+4)*7)-(5*4)` · stdout: `5 4 6`

#### PROVA-INT — integração das primitivas no padrão de uso do T11

Tokens de vários dígitos guardados em listas numéricas paralelas dentro de um objeto. O lexema de cada símbolo é recuperado com `substr` usando a posição armazenada como `double`.

```minipar
class Tokens {
    var tipos = [];
    var valores = [];
    func adicionar(tipo, valor) {
        this.tipos.append(tipo);
        this.valores.append(valor);
    }
}

var e = input();
var tk = new Tokens();
var i = 0;
while (i < len(e)) {
    var c = substr(e, i, 1);
    if (c >= "0" && c <= "9") {
        var num = "";
        while (i < len(e) && substr(e, i, 1) >= "0" && substr(e, i, 1) <= "9") {
            num = num + substr(e, i, 1);
            i = i + 1;
        }
        tk.adicionar(0, to_number(num));
    } else {
        if (c != " ") {
            tk.adicionar(1, i);
        }
        i = i + 1;
    }
}

var j = 0;
var linha = "";
while (j < len(tk.tipos)) {
    if (j > 0) {
        linha = linha + " ";
    }
    if (tk.tipos[j] == 0) {
        linha = linha + "NUM(" + to_string(tk.valores[j]) + ")";
    } else {
        linha = linha + "SIM(" + substr(e, tk.valores[j], 1) + ")";
    }
    j = j + 1;
}
print(linha);
print("total=" + to_string(len(tk.tipos)));
```

stdin: `((10 -8*7)+4)*2` · stdout (2 linhas):

```text
SIM(() SIM(() NUM(10) SIM(-) NUM(8) SIM(*) NUM(7) SIM()) SIM(+) NUM(4) SIM()) SIM(*) NUM(2)
total=13
```

#### PROVA-06 — PRIM-02, PRIM-03 nos limites válidos (3.3.1) e curto-circuito

```minipar
var e = input();
var vazio = "";
print("[" + substr(e, 0, 0) + "]");
print("[" + substr(e, len(e), 0) + "]");
print("[" + substr(vazio, 0, 0) + "]");
print(len(substr(vazio, 0, 0)));
if (substr(e, 0, len(e)) == e) { print("inteira"); } else { print("ERRO"); }
print("[" + substr(e, len(e) - 1, 1) + "]");
var pos = [];
pos.append(3);
print(substr(e, pos[0], 2));
print(substr(e, 2.0, 1));
print(len(vazio) - 1);
var i = len(e);
if (i < len(e) && substr(e, i, 1) == ")") { print("ERRO"); } else { print("curto-circuito"); }
print(e);
```

stdin: `((2+4)*7)-(5*4)` · stdout (11 linhas):

```text
[]
[]
[]
0
inteira
[)]
+4
2
-1
curto-circuito
((2+4)*7)-(5*4)
```

A última linha confirma que `substr` não altera a string original.

#### PROVA-07 — PRIM-06 (comparações entre strings)

Cada `if` acrescenta `V` (verdadeiro) ou `F` (falso) a uma string, para o oráculo não depender de como `print` formata booleanos.

```minipar
var e = input();
var a = "abc";
var b = "abd";
var c = substr(e, 2, 1);
var r = "";
if (a == "abc") { r = r + "V"; } else { r = r + "F"; }
if ("abc" == a) { r = r + "V"; } else { r = r + "F"; }
if ("x" == "x") { r = r + "V"; } else { r = r + "F"; }
if ("x" != "y") { r = r + "V"; } else { r = r + "F"; }
if (a < b) { r = r + "V"; } else { r = r + "F"; }
if ("ab" < "abc") { r = r + "V"; } else { r = r + "F"; }
if ("10" < "9") { r = r + "V"; } else { r = r + "F"; }
if ("(" < "0") { r = r + "V"; } else { r = r + "F"; }
if (c >= "0" && c <= "9") { r = r + "V"; } else { r = r + "F"; }
if (substr(e, 0, 1) == "(") { r = r + "V"; } else { r = r + "F"; }
if (a + "d" == "abcd") { r = r + "V"; } else { r = r + "F"; }
if (to_string(22) == "22") { r = r + "V"; } else { r = r + "F"; }
if ("" == substr(e, 0, 0)) { r = r + "V"; } else { r = r + "F"; }
if (a == b) { r = r + "V"; } else { r = r + "F"; }
if (b <= a) { r = r + "V"; } else { r = r + "F"; }
if ("A" > "a") { r = r + "V"; } else { r = r + "F"; }
print(r);
```

stdin: `((2+4)*7)-(5*4)` · stdout: `VVVVVVVVVVVVVFFF`

| Posição | Comparação | O que verifica |
|---:|---|---|
| 1–2 | variável × literal, nos dois lados | igualdade por conteúdo |
| 3–4 | literal × literal | conteúdo, não endereço do literal |
| 5–6 | `"abc" < "abd"`, `"ab" < "abc"` | ordem lexicográfica e prefixo |
| 7 | `"10" < "9"` | a ordem não é numérica |
| 8 | `"(" < "0"` | ordem por código de caractere (40 < 48) |
| 9 | faixa de dígito | uso do lexer do T11 |
| 10–13 | `substr`, concatenação, `to_string` e string vazia comparados | resultados de primitivas são strings comparáveis |
| 14–16 | casos falsos | `==`, `<=` e `>` também respondem falso (`"A"` = 65 vem antes de `"a"` = 97) |

#### PROVA-08 — PRIM-01, PRIM-05 (concatenações)

```minipar
class Buffer {
    var texto = "";
    func add(s) {
        this.texto = this.texto + s;
    }
}

func rotulo(n) {
    return "t" + to_string(n);
}

var e = input();
print("a" + "b");
print("[" + "" + "]");
var x = "R";
print(x + to_string(3) + ", #" + to_string(0 - 84));
print(to_string(7) + "*" + substr(e, 2, 1));
print(e + "\n" + "fim");
print(rotulo(1) + " = " + rotulo(2));
var buf = new Buffer();
buf.add("MOV");
buf.add(" R0");
buf.add(", #" + to_string(22));
print(buf.texto);
var acc = "";
var k = 0;
while (k < 3) {
    acc = acc + to_string(k) + ";";
    k = k + 1;
}
print(acc);
print(len("ab" + "cd"));
```

stdin: `((2+4)*7)-(5*4)` · stdout (10 linhas):

```text
ab
[]
R3, #-84
7*2
((2+4)*7)-(5*4)
fim
t1 = t2
MOV R0, #22
0;1;2;
4
```

#### PROVA-09 — PRIM-01 em retorno de função e literais UTF-8

Molde do T11: o mnemônico ARM vem de uma função que só retorna literais, e o valor de uma folha vem de `substr`.

```minipar
func mnemonico(op) {
    if (op == 0) {
        return "ADD";
    }
    if (op == 1) {
        return "SUB";
    }
    return "MUL";
}

func folha(e, n) {
    if (n == 0) {
        return "?";
    }
    return substr(e, 0, n);
}

var e = input();
print("    " + mnemonico(1) + "    r2");
var m = mnemonico(2);
m = m + "!";
print(m);
print("[" + folha(e, 0) + "|" + folha(e, 2) + "]");
print("⚙️ Assembly ARMv7 (CPUlator):");
print("🔹 " + substr(e, 2, 1) + " → CONST");
```

stdin: `((2+4)*7)-(5*4)` · stdout (5 linhas, em UTF-8):

```text
    SUB    r2
MUL!
[?|((]
⚙️ Assembly ARMv7 (CPUlator):
🔹 2 → CONST
```

#### PROVA-ERR — erros de execução do `substr` (3.3.1)

Um programa por linha da tabela, todos com o mesmo molde:

```minipar
var e = input();
print("antes");
print(substr(e, INICIO, TAMANHO));
print("depois");
```

**Oráculo de todos:** stdout exatamente `antes` (uma linha), stderr contendo `substr`, código de saída **1**.

| ID | stdin | `INICIO` | `TAMANHO` | Caso |
|---|---|---|---|---|
| ERR-01 | `abc` | `0 - 1` | `1` | `inicio` negativo |
| ERR-02 | `abc` | `0` | `0 - 1` | `tamanho` negativo |
| ERR-03 | `abc` | `4` | `0` | `inicio > len` |
| ERR-04 | `abc` | `2` | `2` | fim além do limite |
| ERR-05 | `abc` | `3` | `1` | `inicio == len` com `tamanho > 0` |
| ERR-06 | `abc` | `1.5` | `1` | índice não inteiro |
| ERR-07 | (linha vazia) | `0` | `1` | string vazia com `tamanho > 0` |

#### PROVA-NEG — rejeição na compilação

Cada programa precisa **falhar na compilação**, em qualquer fase (semântico ou g++), com mensagem. Nenhum binário pode ser executado com resultado.

| ID | Programa | Motivo |
|---|---|---|
| NEG-01 | `print("R" + 3);` | string + número sem `to_string` (em C++ seria aritmética de ponteiro) |
| NEG-02 | `var s = "abc"; if (s == 3) { print("x"); }` | string comparada com número |
| NEG-03 | `print(substr("abc", 0));` | `substr` com dois argumentos |

Sondagem de 22/10/2026 no `src/` do commit `a37c168`: **NEG-01 compila e executa, imprime uma linha vazia e sai com código 0** (resultado falso em silêncio, porque `"R"` vira `const char*`); NEG-02 já falha no g++; NEG-03 falha no semântico porque `substr` não existe, e depois do `CORE-03` precisa falhar pela aridade.

**Regra anti-hardcode:** A não pode reconhecer estes programas por nome, conteúdo ou entrada (como o `EXPECTED_QUICKSORT_TAC` do T07). O B pode trocar as entradas na revisão, por exemplo `(7+8)*3` na PROVA-02, e o resultado precisa continuar correto.

### 3.6 Fronteira do `.arm`

1. **Quem gera:** o programa MiniPar imprime o Assembly no stdout **do mesmo jeito que a referência**: a linha de título `⚙️ Assembly ARMv7 (CPUlator):`, o Assembly com uma instrução por linha e uma linha em branco antes de `📚 Tabela de Símbolos:`. Não há marcadores próprios. O `.arm` de referência do professor é exatamente esse bloco da saída dele: as linhas 38–51 de `Execucao-Saida-okRodounoCPULATOR.txt` são iguais a `Codigo-Assembly-ARMV7.arm`, a menos do fim de linha (CRLF). O Java não grava arquivo nenhum (não usa `FileWriter`, `PrintWriter` nem `Files`).
2. **Quem salva:** um script do B em `tests/2026_2/test11/` (e, no M2, o download da Web didática pelo `WEB-04`) copia **literalmente** as linhas entre a linha de título e a primeira linha vazia seguinte para `caso1.arm`, `caso2.arm`, `caso3.arm`, em UTF-8, terminando com uma linha em branco, como o arquivo de referência. A linha de título é reconhecida pelo texto `Assembly ARMv7 (CPUlator):` no fim da linha, sem depender do emoji. É erro: título ausente ou repetido, bloco vazio, bloco que não começa com `.global _start`, ou falta da linha em branco final. O script não pode reescrever, completar nem analisar o Assembly: nada de Lexer, AST, TAC ou ARM em Python.
3. **Formato do Assembly = o da referência** (`gerarAssemblyARM`), em sintaxe GNU `as`, aceita pelo CPUlator:
   - cabeçalho de três linhas sem recuo: `.global _start`, `.text`, `_start:`;
   - percurso **pós-ordem** da AST: filho esquerdo, filho direito, nó;
   - folha: `    MOV    rN, #k` (4 espaços, `MOV`, 4 espaços), com `k` igual ao lexema do número;
   - operador: `    OPC    rD, rE, rR    @ resultado de 'EXPR'`. `OPC` é `ADD`, `SUB` ou `MUL`, num campo de 6 colunas (o `%-6s` da referência). `rE` e `rR` são os registradores dos filhos. `EXPR` é a expressão totalmente parentizada do `formatExpr`: `(esq op dir)`, com um espaço de cada lado do operador. Há 4 espaços antes do `@`;
   - registradores em minúsculas (`r0`, `r1`...), alocados por um contador global na ordem de emissão, **sem reaproveitamento**. O registrador do resultado de um operador é alocado depois dos dois filhos;
   - última linha: `    b .    @ loop infinito para parar o programa`;
   - o **resultado final fica no registrador da raiz**, `r(N-1)` para uma AST de `N` nós. Nos três casos obrigatórios é `r8`;
   - comentários só com `@` (no GNU `as` para ARM, `;` separa instruções) e nenhum `SWI`/`SVC` (o "ARMv7 generic" do CPUlator não tem sistema operacional).
4. **Desvios do formato, só onde a referência gera Assembly errado.** Nenhum deles ocorre nos três casos obrigatórios, cujo `.arm` precisa sair idêntico ao formato do item 3.

   | Situação | Referência Java | T11 |
   |---|---|---|
   | constante maior que 255 | `MOV rN, #k`, que o montador recusa quando `k` não cabe num imediato de 8 bits rotacionado (ex.: `257`) | `    LDR    rN, =k` até 2147483647; acima disso, rejeita com mensagem |
   | AST com mais de 13 nós (8 números ou mais) | continua em `r13` (SP), `r14` (LR) e `r15` (PC) | rejeita a entrada com mensagem |
   | divisão `/` | imprime só um comentário; o registrador do resultado fica sem valor e o resto do cálculo usa lixo | rejeitada (3.1) |
   | número decimal ou identificador | `MOV r0, #2.5` ou `MOV r0, #x`, que não montam | rejeitado (3.1) |
   | zero à esquerda | `#010` é octal no GNU `as` (vale 8), enquanto a avaliação dá 10 | rejeitado (3.1) |

5. **Escrita direta do arquivo pelo MiniPar:** desnecessária. A referência também não grava o arquivo: o `.arm` dela foi copiado da saída, que é o mesmo procedimento que o script automatiza.

#### 3.6.1 Relação com a saída do professor (conclusão definitiva)

- O comunicado pede que o Assembly **gerado na saída** rode no CPUlator e seja salvo num `.arm`. A referência faz exatamente isso: imprime o Assembly, e o `.arm` é o bloco copiado da saída. Extrair o `.arm` da saída do MiniCompilador é, portanto, o procedimento do professor. PEND-T11-02 fica resolvida.
- **Equivalência exigida:** nos três casos obrigatórios, o `.arm` gerado pelo T11 é **idêntico** ao que a referência gera, desconsiderando CR e linhas em branco no fim. Para os casos 1 e 3, isso significa igual a `docs/fontes/teste11/Codigo-Assembly-ARMV7.arm`; para o caso 2, igual ao oráculo de 3.12. É mais do que a revisão 1 pedia (só o resultado), e não exige primitiva nova além das de 3.3.
- Fora dos casos obrigatórios, valem os desvios de 3.6 item 4, cada um com o motivo no relatório.
- **Revogado da revisão 1:** `LDR` para toda constante, resultado em `R0`, laço `_fim: B _fim` e marcadores `===MINIPAR_ARM_BEGIN===`/`===MINIPAR_ARM_END===`.

### 3.7 Validação no CPUlator

- **Ambiente:** CPUlator, sistema "ARMv7 generic" (`https://cpulator.01xz.net/?sys=arm`). O nome do arquivo de saída do professor ("okRodounoCPULATOR") indica que o `.arm` de referência rodou ali; o B precisa repetir a execução com os arquivos gerados pelo T11.
- **Passos:** carregar o `.arm` no editor, *Compile and Load*, *Continue*, pausar quando o PC estiver na linha `b .` e ler o registrador final.
- **Oráculos:**

  | Arquivo | Registrador final | Decimal | Hexadecimal | Conferência intermediária |
  |---|---|---:|---|---|
  | `caso1.arm` | `r8` | 22 | `0x00000016` | `r2` = 6, `r4` = 42, `r7` = 20 |
  | `caso2.arm` | `r8` | -84 | `0xFFFFFFAC` | `r3` = 56, `r4` = -46 (`0xFFFFFFD2`), `r6` = -42 (`0xFFFFFFD6`) |
  | `caso3.arm` | `r8` | 22 | `0x00000016` | igual ao caso 1 |

- **Evidência guardada pelo B** em `tests/2026_2/test11/evidencias/`: captura da tela com o editor e os registradores, data, sistema do CPUlator, SHA-256 de cada `.arm` e o stdout completo da execução MiniPar que o gerou. Assembly impresso sem execução no CPUlator conta no máximo como `PARTIAL`.

### 3.8 Responsabilidades e handoff

**A comprova (`CORE-03`):**
- PRIM-01 a PRIM-06 implementadas no compilador hospedeiro;
- PROVA-01 a PROVA-09, PROVA-INT, PROVA-ERR (ERR-01 a 07) e PROVA-NEG (NEG-01 a 03) em PASS pelo pipeline real, com comandos, stdout, stderr e código de saída no handoff;
- `BNF-grammar.md` atualizada com `substr` e `to_string` (biblioteca nativa e tradução para C++) e com as regras de tipo de 3.3;
- os recursos de "já disponíveis" (3.3) continuam passando;
- regressão T01–T07 não piora em relação à baseline do `CORE-01`;
- nenhum reconhecimento por nome ou conteúdo de programa.

**B comprova (`T11-01` → `T11-03`):**
- tokenização, parser com precedência, AST, TAC, tabela de símbolos e ARM são lógica MiniPar, gerada dinamicamente a partir da entrada;
- os três casos dão 22, -84 e 22, e ao menos três entradas extras também (variação de parênteses e de operador);
- entradas inválidas são rejeitadas com mensagem: as da lista de 3.1 e os desvios de 3.6 item 4;
- stdout dos três casos idêntico ao oráculo de 3.12 (caso 1 e 3: saída do professor; caso 2: oráculo derivado), e `.arm` idêntico ao formato de 3.6 item 3;
- três `.arm` executados no CPUlator com os oráculos de 3.7.

**Processo:** se B precisar de uma primitiva nova, abre card para A com programa de 10–30 linhas. B não mergeia patch em `src/`. Mudança de sintaxe ou semântica de PRIM-01 a PRIM-06 depois do congelamento exige CR (seção 4).

### 3.9 Pendências registradas

| ID | Pendência | Dono | Impacto se não resolver |
|---|---|---|---|
| PEND-T11-01 | **Resolvida em 22/10/2026.** Java, `.arm` e saída do professor anexados em `docs/fontes/teste11/` e comparados (3.11) | Trio | — |
| PEND-T11-02 | **Resolvida em 22/10/2026 pela referência.** O Java não grava arquivo: o `.arm` do professor é o bloco copiado da saída, o mesmo procedimento do script do B (3.6.1). ADR-012 pode ser fechada com "exportação pelo executor" | Coordenador (registrar na ADR-012) | — |
| PEND-T11-04 | Oráculo do caso 2 (3.12) derivado do algoritmo da referência e conferido por tradução literal (que reproduz o caso 1 real), mas não pela execução do próprio Java, que não está instalado. Confirmar rodando o Java uma vez e executando o `caso2.arm` no CPUlator | B | Se divergir, corrigir 3.12 antes do aceite do `T11-03` |
| PEND-T11-03 | Listas de strings: lista literal retorna valor falso sem erro, lista vazia + `append` de string não compila (3.4). Recurso **continua na linguagem**; abrir card próprio de A para corrigir, com rejeição no semântico enquanto não corrige | A | Risco para outros testes e para a BNF; não bloqueia o T11 |

### 3.10 Aprovação

| Parte | Responsável | Decisão | Data |
|---|---|---|---|
| B — consumidor | José Riquelme | Proposta apresentada (revisão 1) | 19/10/2026 |
| Revisão | Colega da equipe | De acordo com listas numéricas + `substr` no T11; pediu ajustes antes de aprovar | 22/10/2026 |
| B — consumidor | José Riquelme | Revisão 2: listas de strings mantidas na linguagem (3.4), especificação do `substr` (3.3.1), PROVA-06 a 09, ERR e NEG (3.5), BNF no escopo do `CORE-03`, comparação com a referência do professor (3.11), formato do Assembly e da saída iguais aos da referência (3.6, 3.6.1, 3.12), PRIM-01 estendida a retornos de função | 22/10/2026 |
| A — fornecedor | Coordenador | *pendente* | |

O congelamento não depende de mais nenhuma comparação: 3.11 foi concluída com os arquivos do professor e não pediu primitiva nova além da extensão de PRIM-01 (retorno literal), já incluída nesta revisão. Primitiva nova que surgir depois entra como `v1.1` aditiva, por CR.

### 3.11 Comparação com a referência Java (concluída em 22/10/2026)

Fonte: `docs/fontes/teste11/`. "Linha" se refere a `MiniCompiladorCompleto_ARMv7.java`.

| Item | Referência (Java e saída) | Contrato C-T11-v1 | Situação |
|---|---|---|---|
| Entrada | `print` do prompt `Digite uma expressão infixada: ` e `Scanner.nextLine()` (linhas 66–68). Na saída anexada a expressão aparece depois do prompt só por eco do terminal | `input("Digite uma expressão infixada: ")` | igual |
| Lexer | regex `\s*(?:(\d+(\.\d+)?)\|([a-zA-Z_]\w*)\|([+\-*/])\|(=)\|([()])\|(#.*))` com `find()` (linhas 23–43). Tipos `NUMERO` (inclui decimal), `IDENTIFICADOR`, `OPERADOR`, `ATRIBUICAO`, `PARENTESE`; `#...` é descartado. **Caractere desconhecido é pulado em silêncio**, porque `find()` procura o próximo casamento | `NUMERO`, `OPERADOR`, `PARENTESE`; espaço e `#...` ignorados; o resto rejeitado com mensagem (3.1). Sem regex: classificação por `substr` e comparação (3.4) | divergência deliberada: validação |
| Impressão dos tokens | `[%s: '%s']`, um por linha (linha 18) | igual | igual |
| Parser | descida recursiva `parseExpr`/`parseTerm`/`parseFactor`, associatividade à esquerda (linhas 101–137). O `)` é consumido sem conferência (linha 131); tokens que sobram são ignorados; `2+` ou entrada vazia estoura `IndexOutOfBoundsException`; menos unário vira folha `-` sem filhos e estoura `NullPointerException` no TAC; `=` nunca é consumido, então `x = 2` vira só `x` | mesma gramática e associatividade; cada um desses casos é rejeitado com mensagem (3.1) | divergência deliberada: validação |
| `isOperador` | `"+-*/".contains(s)` (linha 214): teste de substring. Com os tokens que o lexer produz equivale a pertencer a `{+, -, *, /}` | comparação com cada operador | sem efeito |
| AST | nó com `valor` `String` e filhos `esquerda`/`direita`. Impressa em ordem simétrica invertida (direita, nó, esquerda), 2 espaços por nível (linhas 149–154) | mesma impressão; nós em listas numéricas (3.4) | igual na saída |
| Tabela de símbolos | `HashMap<String,String>` do lexema para `CONST` ou `VAR`, preenchida nas folhas (linhas 139–147); impressa como `🔹 %s → %s` na ordem de iteração do `HashMap`, que a linguagem Java não especifica. **Não guarda temporários nem registradores** | só `CONST` (identificadores rejeitados); ordem crescente pelo valor numérico, que coincide com a do `HashMap` nos três casos (2, 4, 5, 7 e 2, 4, 7, 8, 10) | ajuste: ordem definida. Revoga a proposta provisória da revisão 1 (temporário, valor e registrador) |
| TAC | pós-ordem, `tN = a op b`, contador a partir de 1, folhas pelo lexema (linhas 156–163). Uma expressão só com um número não gera linha de TAC | igual; o `N` sai de `to_string` (PRIM-04) | igual |
| ARM | 3.6 item 3: `MOV` por folha, contador global sem reaproveitamento, comentário `@ resultado de '...'`, `b .` no fim. Divisão vira só um comentário (linhas 184–185) | igual nos casos obrigatórios; desvios em 3.6 item 4 | igual; revoga `LDR`, `R0` e `_fim` da revisão 1 |
| Resultado | avaliação em `double`, impressa com `Double.toString`: `22.0` (linhas 193–211). Identificador vale 0 com aviso no stderr; divisão por zero dá `NaN` | aritmética inteira (`+`, `-`, `*`), impressa como `to_string(r) + ".0"`, com o mesmo texto para inteiros | igual nos casos aceitos |
| Ordem e títulos das seções | prompt, `🔍` tokens, `🌳` AST, `📦` TAC, `⚙️` Assembly, `📚` tabela, `🧮` resultado (`➡️  ` com dois espaços) | igual (3.12) | igual |
| Arquivo `.arm` | o Java não grava arquivo; o `.arm` anexado é o bloco da saída | exportação pelo executor (3.6) | igual no procedimento |
| Primitivas | regex, `String.format`/`printf`, `" ".repeat(n)`, `HashMap`, recursão, `Double.toString` | classificação por `substr` + PRIM-06; literais + PRIM-05; laço de concatenação; listas numéricas + ordenação; recursão (já disponível, 3.2); `to_string` + `".0"` | sem primitiva nova; **um defeito**: função que só retorna literal não concatena (3.2) e foi incluído em PRIM-01 (PROVA-09) |

### 3.12 Formato da saída e oráculos dos três casos

**Regra de comparação:** com o stdin redirecionado, a primeira linha do stdout é o prompt `Digite uma expressão infixada: ` (com o espaço final; é a única linha com espaço no fim), sem a expressão, porque não há eco do terminal. Da linha `🔍 Tokens gerados pelo analisador léxico:` até o fim, o stdout tem de ser **idêntico** ao oráculo, byte a byte, desconsiderando CR (`\r\n` e `\n` valem o mesmo).

**Casos 1 e 3** (`((2+4)*7)-(5*4)`): oráculo = linhas 3–59 de `docs/fontes/teste11/Execucao-Saida-okRodounoCPULATOR.txt`, a saída real da referência. O `.arm` extraído tem de ser igual a `docs/fontes/teste11/Codigo-Assembly-ARMV7.arm`.

**Caso 2** (`((10 -8*7)+4)*2`): oráculo **derivado à mão** do algoritmo da referência (PEND-T11-04), com os títulos copiados byte a byte da saída do professor. A ordem da tabela de símbolos é a de iteração do `HashMap` para essas chaves (2, 4, 7, 8, 10), conferida pelo cálculo de `hashCode` de cada lexema. Conferência cruzada em 22/10: uma tradução literal do Java para Python, feita fora do repositório só para isso, reproduz byte a byte as linhas 3–59 da saída do professor no caso 1 e gera exatamente o bloco abaixo no caso 2.

```text
🔍 Tokens gerados pelo analisador léxico:
[PARENTESE: '(']
[PARENTESE: '(']
[NUMERO: '10']
[OPERADOR: '-']
[NUMERO: '8']
[OPERADOR: '*']
[NUMERO: '7']
[PARENTESE: ')']
[OPERADOR: '+']
[NUMERO: '4']
[PARENTESE: ')']
[OPERADOR: '*']
[NUMERO: '2']

🌳 Árvore Sintática Abstrata (AST):
  2
*
    4
  +
        7
      *
        8
    -
      10

📦 Código de Três Endereços (TAC):
t1 = 8 * 7
t2 = 10 - t1
t3 = t2 + 4
t4 = t3 * 2

⚙️ Assembly ARMv7 (CPUlator):
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

📚 Tabela de Símbolos:
🔹 2 → CONST
🔹 4 → CONST
🔹 7 → CONST
🔹 8 → CONST
🔹 10 → CONST

🧮 Resultado final da expressão:
➡️  -84.0
```

O `.arm` do caso 2 é o bloco entre `⚙️ Assembly ARMv7 (CPUlator):` e a linha em branco seguinte, acima.

---

## 4. Compatibilidade, versões e change requests

**Versão `v0.1 PROPOSTA`**: só documentação.  
**Versão `v1 FROZEN`**: quando cada par A+B/A+C assinar via comentário/PR de planejamento.  
**Alteração pontual:** `v1.1` se aditiva e compatível; `v2` se quebra consumidores; ambos exigem CR.

Template mínimo de CR:
```text
CR-ID:
Contrato:
Motivo e evidência:
Antes / Depois:
Quem fornece / quem consome:
Mocks/fixtures alterados:
Impacto nos testes:
Responsáveis que aprovam:
Plano de migração:
Data:
```

**Se B ou C precisam modificar `src/`:** manter o patch em branch experimental separada para demonstração; passar o diff/prova a A e criar card CORE correspondente; **não** mergear o patch experimental por conta própria.

---

## 5. Decisões pendentes de congelamento

| ID | Decisão | Donos | Prazo |
|---|---|---|---|
| CT-01 | Sintaxe definitiva Fork/Join na BNF 2026.2 — proposta do C em C-FJ-v1 §2.2 (revisão 2, 23/10), adotada pelo A no `CORE-04`/`05` (PR #15), aguardando aprovação formal do A | A+C | 18/10 |
| CT-02 | API runtime C++ final e registry de workers — proposta em C-FJ-v1 §2.3–2.5, implementada no `RUN-01`/`RUN-02`, aguardando A | A+C | 18/10 |
| CT-03 | Estrutura JSON e API da Web | A+B | 18/10 |
| CT-04 | Primitivas para strings/coleções Teste 11 — proposta em C-T11-v1 §3.3–3.5 (revisão 2, 22/10), aguardando A | A+B | 18/10 |
| CT-05 | Modelo de deploy dos workers entre hosts — proposta em C-FJ-v1 §2.2.3 e §2.6: mesmo binário compilado em cada máquina, modo `--minipar-worker`, `build_id` conferido no `HELLO` | C+A | 18/10 |
| CT-06 | CPUlator e escrita `.arm` — proposta em C-T11-v1 §3.6–3.7, alinhada à referência do professor; escrita direta desnecessária (PEND-T11-02 resolvida em 22/10) | B+A | 19/10 |
| CT-07 | Saída gráfica do T10 | C | 20/10 |

**Não iniciar implementação ampla sem estes contratos.** Provas isoladas reversíveis são permitidas para reduzir risco.
