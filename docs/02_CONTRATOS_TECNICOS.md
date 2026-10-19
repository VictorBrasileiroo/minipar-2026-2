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

**Revisão 2 (19/10/2026):** incorpora a revisão do coordenador no PR do `CON-02`: `\n` final explícito nas fixtures, regra única para fases ignoradas, tipos e escopos da tabela de símbolos, algoritmo de truncamento da AST, testes de isolamento/timeout/artefatos e entrega do `.arm` do Teste 11 pela Web.

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
2. O navegador recorta o `stdout` recebido pelas regras de C-T11-v1 §3.6: linhas entre `===MINIPAR_ARM_BEGIN===` e `===MINIPAR_ARM_END===`, copiadas literalmente; falta de marcador ou mais de um bloco é erro exibido ao usuário.
3. Se `stdout_truncated` for `true`, a Web recusa a extração, porque o bloco pode estar incompleto.
4. O download é gerado no próprio navegador como `t11_<8 primeiros do artifact_id>.arm`, em UTF-8 com `\n`. Não há rota nem função nova: `kind` continua limitado a `cpp`, `tac` e `binary`.

O script de linha de comando do B em `tests/2026_2/test11/` aplica as mesmas regras de §3.6, para que Web e evidências produzam o mesmo arquivo. Essa integração depende de C-T11-v1 estar aprovado (PR do `CON-03`).

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
| ACE-03 | `compile_program` de código que passa no semântico e falha no g++ (exemplo atual: sonda `P11` de C-T11-v1 §3.2) | `gpp.status: "error"`, diagnóstico `GPP_FAILED`, `binary_id: null`; `get_artifact(id, "binary")` devolve `ARTIFACT_NOT_FOUND`. Se não restar nenhum programa assim, testar com `CXX` apontando para executável inexistente e esperar `GPP_NOT_FOUND` |
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
- extração do `.arm` (1.7) com três saídas de teste: bloco válido, marcador ausente e dois blocos; só a primeira gera arquivo, igual byte a byte ao produzido pelo script de `tests/2026_2/test11/`.

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

**Fornecedores conjuntos:** A (linguagem/código gerado) e C (runtime). **Consumidores:** A + testes C. **Congelamento:** 18/10.

### 2.1 Modelo semântico alvo

- Um `fork` inicia uma **tarefa assíncrona** reconhecida, com identificador/handle.
- O `join` bloqueia até a tarefa terminar ou retornar um erro explícito (falha, timeout, destino inacessível).
- Tarefas recebem **entradas copiadas/serializadas** em vez de capturar por referência dados externos mutáveis.
- O destino pode ser `local` ou remoto `host:port`, conforme sintaxe escolhida.
- O código de worker **já está compilado e disponibilizado nas máquinas**; enviar argumentos e nome/ID de função, não serializar código-fonte ou closures.
- Comunicação entre participantes ocorre por mensagens/canais; avaliar coerência com `par`, `seq`, `c_channel`, `send` e `receive` herdados.
- Tarefa remota executa de fato trabalho em outro processo/computador; localhost é prova de protocolo, não prova remota.
- `join` associa corretamente cada resultado à tarefa e não depende da ordem de resposta.

### 2.2 Gramática — proposta para discussão, **NÃO sintaxe aceita**

Exemplo ilustrativo da intenção:

```text
handle1 = fork avaliar(bloco1) on local
handle2 = fork avaliar(bloco2) on computador_2
resultado1 = join(handle1)
resultado2 = join(handle2)
```

**Atenção:** a sintaxe acima **não faz parte da BNF aprovada** nem afirma que `handle` é um tipo já suportado. A deve projetar a produção mínima compatível com a BNF 2026.1, com regras de função, retorno, variáveis e endereços. C não implementa um parser próprio.

**G0 deve resolver:**
1. Fork é expressão que retorna handle ou statement com identificação explícita?
2. Destino `local/remoto` faz parte do código MiniPar, do canal ou da configuração da execução?
3. Join recebe handle individual, lista de handles ou bloco?
4. A tarefa pode chamar quais funções do programa? Como registrar funções elegíveis?
5. Quais tipos podem cruzar rede? Definir um subconjunto seguro para testes 8–10.
6. Relação com `par` existente e regras de captura/cópia.
7. Tratamento de erros no semântico e no runtime.

### 2.3 API C++ proposta para o runtime (assinaturas conceituais)

```cpp
namespace minipar_rt {
  struct Destination;    // local ou remote(host,port)
  struct TaskArgs;       // dados copiáveis e serializáveis
  struct TaskHandle;     // identificador único
  struct TaskResult;     // payload ou erro explícito
  TaskHandle start(const std::string& function_id,
                   const TaskArgs& args,
                   const Destination& where);
  TaskResult join(const TaskHandle& handle, int timeout_ms);
}
```

Estas assinaturas indicam a **fronteira**, não uma decisão sobre uso de classes JSON, templates ou bibliotecas externas. Nome do namespace, headers, status e tipos ficam definidos no G0. A não deve assumir assinatura antes de C aprovar compilação de um `hello_task`.

### 2.4 Mensagens e protocolo remoto

**Proposta robusta e mínima:** TCP com prefixo de tamanho (4 bytes em ordem de rede) + payload com campos `protocol_version`, `request_id`, `task_id`, `function_id`, `args`, `status`, `result`, `error`. Impor tamanho máximo de frame e timeouts. `send_all` e `recv_exact`; protocolo compatível com processo worker em computador distinto.

Exemplo meramente conceitual:
```json
{"protocol_version":1,"type":"TASK","request_id":"run-2",
 "task_id":"task-004","function_id":"avaliar","args":[20,35]}
```
Resposta:
```json
{"protocol_version":1,"type":"RESULT","request_id":"run-2",
 "task_id":"task-004","status":"ok","result":55}
```
Falha:
```json
{"protocol_version":1,"type":"RESULT","request_id":"run-2",
 "task_id":"task-004","status":"error","error":{"code":"TASK_FAILED","message":"..."}}
```

Pode usar outro formato se documentado e testado. **Não pressupor biblioteca JSON nativa em C++**; a escolha da implementação é de C, preservando o contrato. Verificar versão do worker/build para rejeitar execução incompatível.

### 2.5 Critérios de teste do runtime

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

### 2.6 Compatibilidade com runtime antigo

`MiniParChannel` atual usa TCP básico com listener a cada mensagem e `send`/`recv` únicos. C deve decidir se cria wrapper novo ou corrige o existente **sem mudar interfaces de A sem CR**. A pode continuar emitindo `c_channel` existente se a correção for compatível; regressão Teste 1 é obrigatória.

---

## 3. C-T11-v1 — MiniCompilador escrito em MiniPar

**Fornecedor de primitivas:** A. **Consumidor de linguagem:** B. **Prazo:** recursos mínimos aprovados em G0; prova ARM em G1.

### 3.1 Escopo da aplicação

MiniCompilador implementado **na linguagem MiniPar** com lógica de tokenização, análise de precedência, AST, TAC, tabela de símbolos/representação equivalente exigida e texto Assembly ARMv7. Os operadores e entradas devem respeitar enunciado Java; **não** assumir que toda funcionalidade não testada é opcional sem confirmação.

Entradas obrigatórias (referência):
- `((2+4)*7)-(5*4)` → `22`.
- `((10-8*7)+4)*2` → `-84`.
- repetir primeira → `22`.

### 3.2 Primitivas mínimas acordáveis

`input()`, tipo `string` com armazenamento correto, comprimento (`len`), acesso a caractere (`substr` ou índice), `to_string`, concatenação, listas de números e strings, laços/condicionais, funções necessárias, mensagens e saída para capturar `.arm`. **Prova da auditoria rodada 2** mostrou correções localizadas mas não tipagem geral resolvida.

A deve fornecer testes **nativos** para essas operações; B não deve alterar codegen para viabilizar o algoritmo. Quando uma primitiva faltar, abrir card para A com programa MiniPar reprodutível de 10–30 linhas.

### 3.3 Fronteira do `.arm`

**Proposta:** MiniCompilador imprime uma seção ARM com marcadores inequívocos; executor hospedeiro extrai **apenas** ARM e salva em `.arm`. Essa exportação não pode implementar Lexer/AST/TAC/ARM em Python. Se professor exigir escrita física do próprio programa MiniPar, abrir CR e implementar builtin de arquivo — **pendente**.

**Validação indispensável:** CPUlator aceita assembly e execução produz registrador/estado equivalente ao resultado. Não confundir código ARM impresso com sucesso no simulador.

### 3.4 Handoff A → B

A comprova:
- `string s = "123"; len(s)` compila e executa.
- `substr` em string lida funciona.
- `to_string(42)` produz `"42"`.
- lista homogênea de strings é manipulável conforme uso do Teste 11.
- os três casos não dependem de constantes hardcoded na aplicação.
- regressão 1–7 não piora.

B comprova:
- Lexer/Parser de **expressões** são lógica MiniPar.
- AST e TAC são emitidos dinamicamente por essa lógica.
- ARM `.arm` foi gerado e executado no CPUlator.
- erros/entradas adicionais testados.
- tabela de símbolos fiel ao enunciado Java para o escopo aceito.

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
| CT-01 | Sintaxe definitiva Fork/Join na BNF 2026.2 | A+C | 18/10 |
| CT-02 | API runtime C++ final e registry de workers | A+C | 18/10 |
| CT-03 | Estrutura JSON e API da Web | A+B | 18/10 |
| CT-04 | Primitivas para strings/coleções Teste 11 | A+B | 18/10 |
| CT-05 | Modelo de deploy dos workers entre hosts | C+A | 18/10 |
| CT-06 | CPUlator e escrita `.arm` | B+A | 19/10 |
| CT-07 | Saída gráfica do T10 | C | 20/10 |

**Não iniciar implementação ampla sem estes contratos.** Provas isoladas reversíveis são permitidas para reduzir risco.
