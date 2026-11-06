# UML do MiniPar 2026.2 — casos de uso, componentes e classes

**Card:** `DOC-02` (Eixo B) · **Base:** `origin/dev` em `59ea77d` (05/11/2026) ·
**Revisão técnica pendente:** Eixo A (núcleo, serviço e geradores) e Eixo C (runtime e runners).

Este documento modela o sistema **como ele está implementado**. Cada classe, atributo, método,
rota e mensagem citado aqui existe no código da base acima. Nada foi acrescentado para
"completar" o modelo: onde o código não tem uma abstração (por exemplo, uma interface
Python explícita entre fases), o diagrama não a inventa.

As sondas em [`auditorias/DOC-02_sondas_uml.py`](auditorias/DOC-02_sondas_uml.py)
conferem os diagramas de classes contra o código (seção 8).

## Sumário

1. [Notação e convenções](#1-notação-e-convenções)
2. [Diagrama de casos de uso](#2-diagrama-de-casos-de-uso)
3. [Diagrama de componentes](#3-diagrama-de-componentes)
4. [Diagramas de classes por componente](#4-diagramas-de-classes-por-componente)
5. [Diagramas de sequência](#5-diagramas-de-sequência)
6. [Correspondência com os componentes exigidos](#6-correspondência-com-os-componentes-exigidos)
7. [Observações sobre a implementação real](#7-observações-sobre-a-implementação-real)
8. [Verificação dos diagramas](#8-verificação-dos-diagramas)

---

## 1. Notação e convenções

Os diagramas estão em **Mermaid**, que o GitHub desenha direto no Markdown e que pode ser
exportado para imagem do relatório (`DOC-04`).

| Elemento UML | Como aparece | Observação |
|---|---|---|
| Classe | `classDiagram` | Nome igual ao do código |
| Módulo Python sem classe, módulo JS, cabeçalho C++ com funções livres | classe com estereótipo `<<module>>` | Operações = funções do módulo |
| Visibilidade | `+` público, `-` privado (prefixo `_` em Python, `private:` em C++) | |
| Método estático | sufixo `$` | `@staticmethod` em Python, `static` em C++ |
| Construtor | `+NomeDaClasse(parâmetros)` | Em Python, é o `__init__` |
| Herança | `Pai <|-- Filho` | Só onde há herança real no código |
| Composição / agregação / uso | `*--` / `o--` / `..>` | |
| Caso de uso | elipse (forma arredondada) num `flowchart` | Mermaid não tem diagrama de casos de uso; ver nota 2.1 |
| Componente e interface | caixa `«component»` e círculo de interface num `flowchart` | Mermaid não tem diagrama de componentes; ver nota 3.1 |

Comentários `%% @fonte Classe caminho` dentro dos blocos dizem de qual arquivo cada classe
vem; eles não aparecem no desenho e são usados pelas sondas.

Os diagramas de classes listam os membros **públicos completos** e os privados que explicam o
funcionamento. Métodos privados auxiliares que não mudam o entendimento (por exemplo, os
`_parse_*` do Parser além dos mostrados) foram omitidos; a omissão não esconde nenhuma
responsabilidade.

---

## 2. Diagrama de casos de uso

### 2.1 Atores e casos de uso

```mermaid
flowchart LR
    prog["«ator»<br/>Programador MiniPar<br/>(terminal)"]
    ide["«ator»<br/>Usuário da IDE Web original"]
    est["«ator»<br/>Estudante<br/>(Web didática)"]
    qa["«ator»<br/>Equipe de QA"]
    opw["«ator»<br/>Operador do worker<br/>(outro computador)"]
    gpp["«ator sistema»<br/>G++ (MinGW-w64)"]
    cpul["«ator sistema»<br/>CPUlator ARMv7"]

    subgraph S["Sistema MiniPar 2026.2"]
        direction TB
        UC01(["UC01 Compilar programa .minipar"])
        UC02(["UC02 Gerar TAC"])
        UC03(["UC03 Gerar C++ e binário nativo"])
        UC04(["UC04 Executar teste do catálogo pelo menu"])
        UC05(["UC05 Participar de sessão multi-terminal"])
        UC06(["UC06 Editar, compilar e executar na IDE Web original"])
        UC07(["UC07 Inspecionar fases<br/>(tokens, AST, símbolos, TAC, C++)"])
        UC08(["UC08 Ver diagnóstico com linha e coluna"])
        UC09(["UC09 Compilar e executar o binário atual"])
        UC10(["UC10 Baixar artefato (.cpp, .tac, binário)"])
        UC11(["UC11 Rodar o MiniCompilador do Teste 11<br/>e extrair o .arm"])
        UC12(["UC12 Executar tarefa Fork/Join local"])
        UC13(["UC13 Executar tarefa Fork/Join remota"])
        UC14(["UC14 Iniciar worker do binário"])
        UC15(["UC15 Executar runners dos testes 8–11 e smoke"])
    end

    prog --- UC01
    prog --- UC04
    prog --- UC05
    ide --- UC06
    est --- UC07
    est --- UC09
    est --- UC10
    est --- UC11
    opw --- UC14
    qa --- UC15

    UC01 -. «include» .-> UC02
    UC01 -. «include» .-> UC03
    UC04 -. «include» .-> UC01
    UC06 -. «include» .-> UC01
    UC09 -. «include» .-> UC07
    UC09 -. «include» .-> UC03
    UC07 -. «extend»<br/>se houver erro .-> UC08
    UC11 -. «include» .-> UC09
    UC05 -. «extend»<br/>teste multi-terminal .-> UC04
    UC12 -. «extend»<br/>fork sem destino .-> UC03
    UC13 -. «extend»<br/>fork com on host:porta .-> UC03
    UC13 -. «include» .-> UC14
    UC15 -. «include» .-> UC01

    UC03 --- gpp
    UC11 --- cpul
```

**Nota 2.1.** Mermaid não tem o tipo "diagrama de casos de uso"; o desenho usa um `flowchart`
com a mesma semântica: atores fora da fronteira do sistema, casos de uso como elipses dentro
dela, associações em linha cheia e `«include»`/`«extend»` em linha tracejada, apontando do caso
base para o incluído (include) e do caso que estende para o base (extend), como na UML.
`UC12`/`UC13` estendem `UC03` porque o comportamento de tarefa só existe no binário gerado
quando o programa usa `fork`/`join`. O CPUlator (UC11) é usado **fora** do sistema: a Web
didática extrai o `.arm` da saída do binário; a execução no simulador é manual (C-T11-v1 §3.7).

### 2.2 Descrição dos casos de uso

| ID | Ator | Ponto de entrada real | Resultado |
|---|---|---|---|
| UC01 | Programador | `python main.py <arquivo.minipar> [saida]` → `main.compile_file` | `output/<saida>.tac`, `.cpp` e `.exe`, ou erro da fase |
| UC02 | (incluído) | `TACGenerator.generate` / `generate_text` | Código de três endereços |
| UC03 | (incluído) | `CppCodeGenerator.generate` / `generate_text` + `compile_cpp` | `.cpp` e binário pelo `g++ -std=c++20 -O3` |
| UC04 | Programador | `python main.py` → opção 1 → `menu.exibir_menu` (`rodar_teste`, `rodar_todos`, `escolher_teste`) | Compilação e execução de `tests/*.minipar` |
| UC05 | Programador (2º terminal) | `test_orchestrator.check_active_session_for_new_terminal`, `join_session`, `run_joiner_progress_monitor` | Terminal entra como participante de uma sessão ativa |
| UC06 | Usuário IDE | `python main.py` → opção 2 → `app.py` (porta 5000), `POST /api/compile` | Saída, `.cpp` e `.tac` mostrados na IDE |
| UC07 | Estudante | `POST /api/v1/analyze` (`web_didatica/server.py`) → `service.analyze` | Envelope `minipar.compile.v1` com as fases `lexer`…`cpp` |
| UC08 | (extensão) | `diagnostics[]` do envelope; `erros.js` `criarCartaoErro` | Cartão com código, fase, linha e coluna |
| UC09 | Estudante | `POST /api/v1/compile` → `service.compile_program`; `POST /api/v1/execute` → `service.execute` | Binário da própria requisição executado com stdin e limite de tempo |
| UC10 | Estudante | `GET /api/v1/artifacts/<id>/<tipo>` → `service.get_artifact` | Download do `.cpp`, `.tac` ou binário |
| UC11 | Estudante | `GET /exemplos/t11.json`, depois UC09; `arm.js` `armDaExecucao` | Seção ARM extraída da saída; cópia para o CPUlator |
| UC12 | (extensão) | `fork f(args)` → `minipar_rt::start(id, args)` | Tarefa em thread do `Executor` |
| UC13 | (extensão) | `fork f(args) on "host:porta"` → `minipar_rt::start(id, args, Destination)` | Tarefa executada no worker remoto pelo protocolo C-FJ-v1 §2.6 |
| UC14 | Operador | `<binario> --minipar-worker <porta> [--bind <ip>]` → `worker_main_if_requested` | Processo worker aceitando `HELLO`/`TASK` |
| UC15 | QA | `tests/2026_2/test08/run_t08.py`, `test09/run_t09.py`, `test10/run_t10.py`, `test11/verificar_t11.py`, `scripts/smoke_int01.py` | Relatórios e oráculos dos testes |

---

## 3. Diagrama de componentes

### 3.1 Arquitetura em camadas

```mermaid
flowchart LR
    subgraph APR["Apresentação"]
        CLI["«component»<br/>CLI<br/>main.py · menu.py"]
        ORQ["«component»<br/>Orquestrador de sessão<br/>test_orchestrator.py · program_analyzer.py"]
        WEBO["«component»<br/>Web original (IDE)<br/>app.py · templates/ · static/"]
        WEBD["«component»<br/>Web didática<br/>web_didatica/server.py · static/js/"]
    end

    subgraph SRV["Serviços de aplicação"]
        SVC["«component»<br/>Serviço de compilação<br/>src/service.py"]
        SAST["«component»<br/>Serializador de AST<br/>src/service_ast.py"]
        SPROC["«component»<br/>Processo limitado<br/>src/service_process.py"]
    end

    subgraph NUC["Núcleo da linguagem"]
        LEX["«component»<br/>Analisador léxico<br/>src/lexer.py"]
        PAR["«component»<br/>Analisador sintático<br/>src/parser.py"]
        AST["«component»<br/>AST<br/>src/ast_nodes.py"]
        SEM["«component»<br/>Analisador semântico +<br/>tabela de símbolos<br/>src/semantic.py"]
    end

    subgraph IR["Representação intermediária"]
        TAC["«component»<br/>Gerador TAC<br/>src/tac.py"]
    end

    subgraph BE["Backend"]
        CPP["«component»<br/>Gerador C++<br/>src/codegen.py · src/cpp_template.py"]
    end

    subgraph RT["Runtime (header-only C++20)"]
        MRT["«component»<br/>minipar_rt<br/>runtime/include/minipar_rt/"]
    end

    subgraph ART["Artefatos gerados"]
        BIN["«artifact»<br/>Binário do programa<br/>(coordenador e worker)"]
        T11["«artifact»<br/>minicompilador.minipar<br/>tests/2026_2/test11/"]
    end

    subgraph EXT["Externos"]
        GPP["«external»<br/>g++ (MinGW-w64)"]
        CPUL["«external»<br/>CPUlator"]
    end

    IWEB(("C-WEB-v1<br/>analyze · compile_program<br/>execute · get_artifact"))
    IHTTP(("HTTP /api/v1"))
    IRT(("C-FJ-v1 §2.3<br/>start · join · join_or_exit<br/>register_function"))
    IPROTO(("C-FJ-v1 §2.6<br/>TCP: HELLO · TASK · RESULT"))
    ICLI(("CLI<br/>python main.py arquivo [saida]"))

    SVC --- IWEB
    WEBD --- IHTTP
    WEBD -. usa .-> IWEB
    CLI --- ICLI
    WEBO -. "subprocess<br/>python main.py" .-> ICLI
    CLI -. usa .-> ORQ
    WEBO -. usa .-> ORQ

    SVC -. usa .-> SAST
    SVC -. usa .-> SPROC
    SVC -. "usa as fases" .-> NUC
    CLI -. "usa as fases" .-> NUC
    SVC -. usa .-> TAC
    CLI -. usa .-> TAC
    SVC -. usa .-> CPP
    CLI -. usa .-> CPP

    LEX -- "List[Token]" --> PAR
    PAR -- "Program" --> AST
    SEM -. lê .-> AST
    TAC -. lê .-> AST
    CPP -. lê .-> AST
    CPP -. "usa CppTaskContext" .-> SEM
    CPP -. "compile_cpp via run_bounded" .-> SPROC
    CPP -. invoca .-> GPP
    GPP -- produz --> BIN
    MRT --- IRT
    BIN -. "#include" .-> IRT
    BIN --- IPROTO
    T11 -. "compilado por UC09/UC01" .-> SVC
    T11 -. ".arm copiado" .-> CPUL
```

**Nota 3.1.** Mermaid não tem o tipo "diagrama de componentes". Os componentes são caixas
`«component»`; as interfaces fornecidas são círculos ligados ao componente por linha cheia
(notação "pirulito"); o uso de interface ou de outro componente é seta tracejada (dependência).
A seta "usa as fases" aponta para o pacote **Núcleo da linguagem** inteiro: a CLI e o serviço
chamam `Lexer`, `Parser` e `SemanticAnalyzer` diretamente (ver 4.7 e 4.8.1).
As interfaces nomeadas são os contratos de `docs/02_CONTRATOS_TECNICOS.md`.

### 3.2 Componentes, arquivos e interfaces

| Componente | Arquivos | Eixo dono | Interface fornecida | Requer |
|---|---|---|---|---|
| CLI | `main.py`, `menu.py` | A | `python main.py <arquivo> [saida]`; `compile_file(source_path, output_name) -> bool` | Núcleo, TAC, C++, Orquestrador |
| Orquestrador de sessão | `test_orchestrator.py`, `program_analyzer.py` | A | `create_session`, `join_session`, `prepare_test_execution`, `finalize_test_execution`; `analyze_program`, `get_program_spec` | Arquivo `output/.test_session.json` |
| Web original | `app.py`, `templates/index.html`, `static/js/script.js` | A | Rotas `/`, `/api/tests`, `/api/get_test`, `/api/test_spec`, `/api/session[/join\|/create\|/ready\|/clear]`, `/api/compile` | CLI por subprocesso, Orquestrador |
| Web didática | `web_didatica/server.py`, `web_didatica/static/` | B | `GET /`, `/fixtures/<nome>`, `/exemplos/t11.json`; `POST /api/v1/analyze`, `/api/v1/compile`, `/api/v1/execute`; `GET /api/v1/artifacts/<id>/<tipo>` (C-WEB-v1 §1.8) | Serviço de compilação |
| Serviço de compilação | `src/service.py` | A | `analyze`, `compile_program`, `get_artifact`, `execute` (C-WEB-v1 §1.2) | Núcleo, TAC, C++, `service_ast`, `service_process` |
| Serializador de AST | `src/service_ast.py` | A | `serialize_ast(program) -> (ast, stats)` | AST |
| Processo limitado | `src/service_process.py` | A | `run_bounded(command, *, cwd, stdin, timeout, limit, env)` | SO (Job Object no Windows) |
| Analisador léxico | `src/lexer.py` | A | `Lexer(source).tokenize() -> List[Token]`, `diagnostics` | — |
| Analisador sintático | `src/parser.py` | A | `Parser(tokens, exit_on_error=...).parse() -> Program`; `ParseError` | Léxico, AST |
| AST | `src/ast_nodes.py` | A | 37 classes de nó; `iter_child_nodes`, `find_fork_join` | — |
| Semântico + tabela de símbolos | `src/semantic.py` | A | `SemanticAnalyzer.analyze(program) -> bool`, `scopes`, `symbols`, `diagnostics`; `CppTaskContext` | AST |
| Gerador TAC | `src/tac.py` | A | `TACGenerator.generate_text(program) -> str`, `generate(program, output_name) -> str` | AST |
| Gerador C++ | `src/codegen.py`, `src/cpp_template.py` | A | `CppCodeGenerator.generate_text(...) -> str`, `generate(...) -> bool`, `compile_cpp(cpp, exe) -> (payload, code)` | AST, Semântico, `run_bounded`, g++, runtime |
| Runtime `minipar_rt` | `runtime/include/minipar_rt/*.hpp` | C | API C-FJ-v1 §2.3 e protocolo §2.6 | Threads e sockets do SO |
| MiniCompilador T11 | `tests/2026_2/test11/minicompilador.minipar` | B | Programa MiniPar: lê a expressão, imprime tokens, AST, TAC, ARM, símbolos e resultado | Primitivas C-T11-v1 §3.3 |

---

## 4. Diagramas de classes por componente

### 4.1 Analisador léxico

```mermaid
classDiagram
    %% @fonte TokenType src/lexer.py
    %% @fonte Token src/lexer.py
    %% @fonte Lexer src/lexer.py
    class TokenType {
        <<enumeration>>
        IDENTIFIER
        NUMBER
        STRING_LITERAL
        BOOL_LITERAL
        CLASS
        FUNC
        VAR
        SEQ
        PAR
        FORK
        JOIN
        ON
        C_CHANNEL
        SEND
        RECEIVE
        TYPE
        END_OF_FILE
        UNKNOWN
    }
    class Token {
        <<dataclass>>
        +type: TokenType
        +lexeme: str
        +line: int
        +col: int
    }
    class Lexer {
        +diagnostics: list~dict~
        -_source: str
        -_pos: int
        -_line: int
        -_col: int
        +Lexer(source_code: str)
        +tokenize() List~Token~
        -_peek() str
        -_advance() str
        -_skip_whitespace_and_comments() None
        -_make_token(token_type, lexeme, line, col) Token
    }
    Lexer ..> Token : cria
    Token --> TokenType
```

`TokenType` tem 57 valores; o diagrama mostra os literais e as palavras-chave da extensão
2026.2 (`FORK`, `JOIN`, `ON`, `TYPE`) e omite operadores e pontuação (`PLUS` … `COMMA`). A
lista completa e a gramática estão em [`12_BNF_MINIPAR_2026_2.md`](12_BNF_MINIPAR_2026_2.md).
Erros léxicos não interrompem a varredura: entram em `diagnostics` (`LEX_*`) e o token vira
`UNKNOWN`.

### 4.2 Árvore sintática abstrata (AST)

```mermaid
classDiagram
    direction LR
    %% @fonte ASTNode src/ast_nodes.py
    %% @fonte Program src/ast_nodes.py
    %% @fonte NumberExpr src/ast_nodes.py
    %% @fonte StringExpr src/ast_nodes.py
    %% @fonte BoolExpr src/ast_nodes.py
    %% @fonte IdentifierExpr src/ast_nodes.py
    %% @fonte BinaryExpr src/ast_nodes.py
    %% @fonte UnaryExpr src/ast_nodes.py
    %% @fonte FuncCallExpr src/ast_nodes.py
    %% @fonte MethodCall src/ast_nodes.py
    %% @fonte PropertyAccess src/ast_nodes.py
    %% @fonte NewExpr src/ast_nodes.py
    %% @fonte ThisExpr src/ast_nodes.py
    %% @fonte ListLiteral src/ast_nodes.py
    %% @fonte MatrixCreateExpr src/ast_nodes.py
    %% @fonte IndexExpr src/ast_nodes.py
    %% @fonte InputExpr src/ast_nodes.py
    %% @fonte CChannelExpr src/ast_nodes.py
    %% @fonte ReceiveExpr src/ast_nodes.py
    %% @fonte ForkExpr src/ast_nodes.py
    %% @fonte JoinExpr src/ast_nodes.py
    class ASTNode {
        +line: int
    }
    class Program {
        +statements: List~ASTNode~
    }
    class NumberExpr { +value: str }
    class StringExpr { +value: str }
    class BoolExpr { +value: bool }
    class IdentifierExpr { +name: str }
    class BinaryExpr {
        +op: str
        +left: ASTNode
        +right: ASTNode
    }
    class UnaryExpr {
        +op: str
        +operand: ASTNode
    }
    class FuncCallExpr {
        +name: str
        +arguments: List~ASTNode~
    }
    class MethodCall {
        +object: ASTNode
        +method_name: str
        +arguments: List~ASTNode~
    }
    class PropertyAccess {
        +object: ASTNode
        +property_name: str
    }
    class NewExpr {
        +class_name: str
        +arguments: List~ASTNode~
    }
    class ThisExpr
    class ListLiteral { +elements: List~ASTNode~ }
    class MatrixCreateExpr {
        +rows: ASTNode
        +cols: ASTNode
        +init_value: ASTNode
    }
    class IndexExpr {
        +object: ASTNode
        +index: ASTNode
    }
    class InputExpr { +prompt: Optional~ASTNode~ }
    class CChannelExpr {
        +ip: ASTNode
        +port: ASTNode
    }
    class ReceiveExpr { +channel: ASTNode }
    class ForkExpr {
        +function_name: str
        +arguments: List~ASTNode~
        +destination: Optional~ASTNode~
        +column: int
    }
    class JoinExpr {
        +handle: ASTNode
        +timeout: Optional~ASTNode~
        +column: int
    }
    ASTNode <|-- Program
    ASTNode <|-- NumberExpr
    ASTNode <|-- StringExpr
    ASTNode <|-- BoolExpr
    ASTNode <|-- IdentifierExpr
    ASTNode <|-- BinaryExpr
    ASTNode <|-- UnaryExpr
    ASTNode <|-- FuncCallExpr
    ASTNode <|-- MethodCall
    ASTNode <|-- PropertyAccess
    ASTNode <|-- NewExpr
    ASTNode <|-- ThisExpr
    ASTNode <|-- ListLiteral
    ASTNode <|-- MatrixCreateExpr
    ASTNode <|-- IndexExpr
    ASTNode <|-- InputExpr
    ASTNode <|-- CChannelExpr
    ASTNode <|-- ReceiveExpr
    ASTNode <|-- ForkExpr
    ASTNode <|-- JoinExpr
    Program *-- ASTNode : statements
```

*Figura 4.2a — raiz e nós de expressão.*

```mermaid
classDiagram
    direction LR
    %% @fonte ASTNode src/ast_nodes.py
    %% @fonte VarDecl src/ast_nodes.py
    %% @fonte Assignment src/ast_nodes.py
    %% @fonte PropertyAssign src/ast_nodes.py
    %% @fonte IndexAssign src/ast_nodes.py
    %% @fonte PrintStmt src/ast_nodes.py
    %% @fonte SendStmt src/ast_nodes.py
    %% @fonte SeqBlock src/ast_nodes.py
    %% @fonte ParBlock src/ast_nodes.py
    %% @fonte IfStmt src/ast_nodes.py
    %% @fonte WhileStmt src/ast_nodes.py
    %% @fonte DoWhileStmt src/ast_nodes.py
    %% @fonte ForStmt src/ast_nodes.py
    %% @fonte BreakStmt src/ast_nodes.py
    %% @fonte ContinueStmt src/ast_nodes.py
    %% @fonte ReturnStmt src/ast_nodes.py
    %% @fonte FuncDecl src/ast_nodes.py
    %% @fonte ClassDecl src/ast_nodes.py
    class ASTNode {
        +line: int
    }
    class VarDecl {
        +name: str
        +init_value: Optional~ASTNode~
        +type: str
    }
    class Assignment {
        +name: str
        +value: ASTNode
    }
    class PropertyAssign {
        +object: ASTNode
        +property_name: str
        +value: ASTNode
    }
    class IndexAssign {
        +target: ASTNode
        +value: ASTNode
    }
    class PrintStmt { +arguments: List~ASTNode~ }
    class SendStmt {
        +channel: ASTNode
        +message: ASTNode
    }
    class SeqBlock { +statements: List~ASTNode~ }
    class ParBlock { +statements: List~ASTNode~ }
    class IfStmt {
        +condition: ASTNode
        +then_branch: ASTNode
        +else_branch: Optional~ASTNode~
    }
    class WhileStmt {
        +condition: ASTNode
        +body: ASTNode
    }
    class DoWhileStmt {
        +body: ASTNode
        +condition: ASTNode
    }
    class ForStmt {
        +initializer: Optional~ASTNode~
        +condition: Optional~ASTNode~
        +increment: Optional~ASTNode~
        +body: ASTNode
        +iterator_name: Optional~str~
        +iterable: Optional~ASTNode~
    }
    class BreakStmt
    class ContinueStmt
    class ReturnStmt { +value: Optional~ASTNode~ }
    class FuncDecl {
        +name: str
        +params: List~str~
        +body: ASTNode
    }
    class ClassDecl {
        +name: str
        +superclass: Optional~str~
        +attributes: List~VarDecl~
        +methods: List~FuncDecl~
    }
    ASTNode <|-- VarDecl
    ASTNode <|-- Assignment
    ASTNode <|-- PropertyAssign
    ASTNode <|-- IndexAssign
    ASTNode <|-- PrintStmt
    ASTNode <|-- SendStmt
    ASTNode <|-- SeqBlock
    ASTNode <|-- ParBlock
    ASTNode <|-- IfStmt
    ASTNode <|-- WhileStmt
    ASTNode <|-- DoWhileStmt
    ASTNode <|-- ForStmt
    ASTNode <|-- BreakStmt
    ASTNode <|-- ContinueStmt
    ASTNode <|-- ReturnStmt
    ASTNode <|-- FuncDecl
    ASTNode <|-- ClassDecl
    ClassDecl *-- VarDecl : attributes
    ClassDecl *-- FuncDecl : methods
```

*Figura 4.2b — declarações e comandos.*

Todas as classes de nó são `@dataclass` com `line: int = 1`. `ForStmt` representa as duas
formas de `for`: com `initializer`/`condition`/`increment` ou com `iterator_name in iterable`.
`fork` e `join` são **expressões** (`ForkExpr`, `JoinExpr`); `par { ... }` é o comando
`ParBlock`. O módulo também oferece as funções `iter_child_nodes(node)` e
`find_fork_join(node)`, usadas pelos geradores.

### 4.3 Analisador sintático

```mermaid
classDiagram
    %% @fonte Parser src/parser.py
    %% @fonte ParseError src/parser.py
    %% @fonte Lexer src/lexer.py
    %% @fonte Program src/ast_nodes.py
    class Exception
    class ParseError {
        +diagnostic: dict
        +ParseError(diagnostic)
    }
    class Parser {
        +exit_on_error: bool
        +diagnostics: list~dict~
        -_tokens: List~Token~
        -_pos: int
        +Parser(tokens, exit_on_error: bool)
        +parse() Program
        -_peek() Token
        -_advance() Token
        -_match(token_type) bool
        -_consume(token_type, err_msg) Token
        -_fail(code, message, line, column)
        -_parse_statement() ASTNode
        -_parse_var_decl(declared_type, require_semicolon) ASTNode
        -_parse_class_decl() ASTNode
        -_parse_func_decl() ASTNode
        -_parse_par_block() ASTNode
        -_parse_expression() ASTNode
        -_parse_or() ASTNode
        -_parse_and() ASTNode
        -_parse_comparison() ASTNode
        -_parse_term() ASTNode
        -_parse_factor() ASTNode
        -_parse_unary() ASTNode
        -_parse_primary() ASTNode
    }
    class Lexer
    class Program
    Exception <|-- ParseError
    Parser ..> Lexer : consome tokens de
    Parser ..> Program : cria
    Parser ..> ParseError : lança
```

Descida recursiva com um método por nível de precedência (`_parse_or` → `_parse_primary`).
Em erro, `_fail` monta o diagnóstico `SYN_*`; com `exit_on_error=True` (CLI) imprime e encerra
o processo, com `exit_on_error=False` (serviço) lança `ParseError`. Pseudocódigo em
[`13_PSEUDOCODIGOS_NUCLEO.md`](13_PSEUDOCODIGOS_NUCLEO.md).

### 4.4 Analisador semântico e tabela de símbolos

```mermaid
classDiagram
    %% @fonte SemanticAnalyzer src/semantic.py
    %% @fonte Symbol src/semantic.py
    %% @fonte ValueType src/semantic.py
    %% @fonte Program src/ast_nodes.py
    class SemanticAnalyzer {
        +emit_diagnostics: bool
        +diagnostics: list~dict~
        +scopes: list~dict~
        +symbols: list~dict~
        +expression_types: dict
        +fork_signatures: dict
        +function_contexts: dict
        +analyzed_program: Program
        -_scopes: list~dict~
        -_scope_ids: list~str~
        -_classes: dict
        -_superclasses: dict
        -_functions: dict
        -_fj_functions: set
        -_current_function
        -_current_class
        -_loop_depth: int
        +SemanticAnalyzer(emit_diagnostics: bool)
        +analyze(program: Program) bool
        +validate_node(node, value_required: bool) None
        -_enter_scope() None
        -_exit_scope() None
        -_define_symbol(name, type_, line, params) None
        -_lookup(name) Symbol
        -_report(line, message, code) None
        -_infer_type(node) str
        -_types_compatible(declared, actual) bool
        -_collect_declarations(program) None
        -_collect_fj_functions() None
        -_check_function(function, arguments, isolated, owner) ValueType
        -_check_transport(info, line, role) None
        -_check_global_access(name, line) None
        -_validate_fork(node: ForkExpr) None
        -_validate_join(node: JoinExpr, value_required) None
        -_validate_node(node, value_required) None
    }
    class Symbol {
        <<dataclass>>
        +name: str
        +type: str
        +params: List~str~
        +attributes: Dict
        +methods: Dict
        +value_type: Optional~ValueType~
    }
    class ValueType {
        <<dataclass frozen>>
        +kind: str
        +elements: tuple
        +result: Optional~ValueType~
    }
    class Program
    SemanticAnalyzer "1" *-- "0..*" Symbol : _scopes (pilha de dict nome→Symbol)
    Symbol --> ValueType
    SemanticAnalyzer ..> ValueType : infere
    SemanticAnalyzer ..> Program : percorre
```

**Tabela de símbolos.** Não há classe `SymbolTable` no código: a tabela é a pilha
`_scopes` (uma lista de dicionários `nome → Symbol`) mantida por `_enter_scope`,
`_exit_scope`, `_define_symbol` e `_lookup` (busca do escopo mais interno para o global).
Para as interfaces, o analisador **publica** duas listas de registros planos:

| Lista | Campos de cada registro | Preenchida em |
|---|---|---|
| `scopes` | `id` (`s0`, `s1`, …), `kind` (`global`, `class`, `function`, `method`, `seq`, `par`, `for`), `name`, `parent`, `line` | `_enter_scope` |
| `symbols` | `name`, `kind` (`class`, `attribute`, `method`, `function`, `parameter`, `variable`, `iterator`), `type`, `scope`, `line`, `params` | `_define_symbol` |

Essas listas são as que o serviço devolve na fase `semantic` do envelope C-WEB-v1 e que a
Web didática desenha como árvore de escopos. As regras FJ-SEM-01…08 ficam em
`_collect_fj_functions`, `_check_function`, `_validate_fork` e `_validate_join`.

### 4.5 Gerador TAC

```mermaid
classDiagram
    %% @fonte TACGenerator src/tac.py
    %% @fonte Program src/ast_nodes.py
    class TACGenerator {
        +lines: list~str~
        +temp_count: int
        +label_count: int
        +break_stack: list
        +continue_stack: list
        +reserved: set
        +has_fork_join: bool
        +branch_context
        +TACGenerator()
        +generate_text(program: Program) str
        +generate(program: Program, output_name: str) str
        -_unsupported(node, message)$ NotImplementedError
        -_temp() str
        -_label(prefix) str
        -_emit(line) None
        -_save(value, operation) str
        -_arguments(arguments) list~str~
        -_join(node: JoinExpr, value_required) str
        -_par(node: ParBlock) None
        -_expr(node) str
        -_stmt(node) None
    }
    class Program
    TACGenerator ..> Program : percorre
```

`generate_text` devolve o texto (usado pelo serviço); `generate` grava
`output/<nome>.tac` e devolve o caminho (usado pela CLI). Construções sem tradução lançam
`NotImplementedError` com prefixo `Linha N:`, que o serviço converte em
`TAC_UNSUPPORTED_FEATURE`. `fork`, `join` e `par` têm tradução própria (`_join`, `_par`);
detalhes em `docs/auditorias/CORE-06_TAC_FORK_JOIN.md`.

### 4.6 Gerador C++ (backend)

```mermaid
classDiagram
    %% @fonte CppCodeGenerator src/codegen.py
    %% @fonte CppTaskContext src/semantic.py
    %% @fonte CppType src/semantic.py
    %% @fonte CppProofError src/semantic.py
    %% @fonte SemanticAnalyzer src/semantic.py
    %% @fonte cpp_template src/cpp_template.py
    %% @fonte service_process src/service_process.py
    class CppCodeGenerator {
        +fj: CppTaskContext
        +context
        +function_names: dict
        -_serial: int
        -_prefix: str
        +CppCodeGenerator()
        +generate_text(program, semantic, source) str
        +generate(program, output_name, semantic, source) bool
        +compile_cpp(cpp_path, exe_path)$ tuple
        -_validate_output_name(output_name)$ bool
        -_escape_string(value)$ str
        -_fj_program(program, semantic, source)
        -_fj_expression(node)
        -_fj_index(node, target)
        -_ordered(expressions, call, returns)
        -_translate_expression(node) str
        -_translate_statement(node, indent) str
        -_translate_for_part(node) str
        -_return_type(body) str
        -_uses_float_return(node) bool
        -_has_value_return(node) bool
    }
    class CppTaskContext {
        +functions: dict
        +contexts: dict
        +forks: dict
        +active: set
        +float_return
        +main: dict
        +CppTaskContext(program, semantic, float_return)
        +new_context()$ dict
        +fail(node, message)$
        +lookup(node, scopes, name)
        +bind(scopes, ctx, name, typ, node)
        +unify(old, new, node)
        +finish(ctx)
        +function(node, name, args)
        +expr(node, scopes, ctx, required)
        +stmt(node, scopes, ctx, returns)
    }
    class CppType {
        <<dataclass frozen>>
        +kind: str
        +item: Optional~CppType~
        +cpp() str
        +transportable() bool
    }
    class ValueError
    class CppProofError
    class SemanticAnalyzer
    class cpp_template {
        <<module>>
        -_CPP_HEADER: str
        -_FJ_HEADER: str
    }
    class service_process {
        <<module>>
        +run_bounded(command, cwd, stdin, timeout, limit, env) dict
        -_windows_job(process)
    }
    ValueError <|-- CppProofError
    CppCodeGenerator --> CppTaskContext : fj
    CppTaskContext ..> SemanticAnalyzer : lê tipos de
    CppTaskContext ..> CppType : infere
    CppTaskContext ..> CppProofError : lança
    CppCodeGenerator ..> cpp_template : prólogo do .cpp
    CppCodeGenerator ..> service_process : compile_cpp
```

Duas rotas de geração convivem em `generate_text`:

- **Programa sem `fork`/`join`:** tradução direta da AST (`_translate_statement`,
  `_translate_expression`) com o prólogo `_CPP_HEADER` (funções nativas, `MiniParChannel`
  para `c_channel`/`send`/`receive`).
- **Programa com `fork`/`join` (CORE-07):** `CppTaskContext` prova os tipos C++ de cada função
  de tarefa (`CppType`; recusa com `CppProofError`) e `_fj_program` gera as funções tipadas, os
  invólucros `__fj_wrap_<f>(const TaskArgs&)`, o `register_function` de cada uma, o
  `set_build_id(sha256 do fonte)` e o `worker_main_if_requested(argc, argv)` no `main`,
  incluindo o prólogo `_FJ_HEADER` (`#include "minipar_rt/minipar_rt.hpp"`).

`compile_cpp` chama `g++ -std=c++20 -O3 <cpp> -o <exe> -pthread -I runtime/include`
(`-lws2_32` no Windows) por `run_bounded`, com limite de 120 s, e devolve
`(payload, code)` com `code` em `GPP_TIMEOUT`, `GPP_FAILED`, `GPP_NO_BINARY`, `GPP_NOT_FOUND`
ou `None`.

### 4.7 Serviço de compilação (C-WEB-v1)

```mermaid
classDiagram
    %% @fonte service src/service.py
    %% @fonte service_ast src/service_ast.py
    %% @fonte service_process src/service_process.py
    %% @fonte Lexer src/lexer.py
    %% @fonte Parser src/parser.py
    %% @fonte SemanticAnalyzer src/semantic.py
    %% @fonte TACGenerator src/tac.py
    %% @fonte CppCodeGenerator src/codegen.py
    class service {
        <<module>>
        +ROOT: Path
        +ARTIFACT_ROOT: Path
        +PHASES: tuple
        -_registry: dict
        -_execution_env: dict
        -_registry_lock: RLock
        +analyze(source: str) dict
        +compile_program(source: str) dict
        +get_artifact(artifact_id: str, kind: str) dict
        +execute(artifact_id: str, stdin: str, timeout_sec: int) dict
        -_pipeline(source, operation) dict
        -_diag(phase, code, message, line, column) dict
        -_unsupported(phase, exc) dict
        -_error(code, message) dict
        -_valid_id(value) bool
        -_safe_directory(request_id) Path
        -_register(request_id, kind, path) None
    }
    class service_ast {
        <<module>>
        +MAX_NODES: int
        +MAX_DEPTH: int
        +serialize_ast(program) tuple
        -_node_type(annotation)
        -_parts(node)
    }
    class service_process {
        <<module>>
        +run_bounded(command, cwd, stdin, timeout, limit, env) dict
    }
    class Lexer
    class Parser
    class SemanticAnalyzer
    class TACGenerator
    class CppCodeGenerator
    service ..> Lexer
    service ..> Parser
    service ..> SemanticAnalyzer
    service ..> TACGenerator
    service ..> CppCodeGenerator
    service ..> service_ast : AST da fase parser
    service ..> service_process : execute
```

O serviço é um módulo de funções, não uma classe. `_pipeline` roda as fases na ordem de
`PHASES` (`lexer`, `parser`, `semantic`, `tac`, `cpp`, `gpp`), para na primeira com erro e
marca as seguintes como `skipped`/`previous_phase_failed`; `analyze` não executa `gpp`
(`not_requested`). Cada compilação usa o diretório `output/web/<request_id>/` e registra os
artefatos em `_registry` (vivo durante todo o processo, sem limpeza). Envelopes:
`minipar.compile.v1` (`analyze`/`compile_program`) e `minipar.execute.v1` (`execute`).

### 4.8 Apresentação

#### 4.8.1 CLI e Web original

```mermaid
classDiagram
    %% @fonte main main.py
    %% @fonte menu menu.py
    %% @fonte test_orchestrator test_orchestrator.py
    %% @fonte program_analyzer program_analyzer.py
    %% @fonte app app.py
    class main {
        <<module>>
        +BASE_DIR: str
        +compile_file(source_path: str, output_name: str) bool
        +start_interactive()
        +main() int
    }
    class menu {
        <<module>>
        +exibir_menu()
        +escolher_teste()
        +rodar_teste(test_path: str) None
        +rodar_todos()
        +obter_testes() list
        +executar_binario(output_name: str, interactive: bool) str
    }
    class test_orchestrator {
        <<module>>
        +SESSION_FILE: str
        +get_terminal_id() str
        +get_test_spec(filename) dict
        +create_session(test_path, spec) dict
        +join_session(session) dict
        +clear_session() None
        +check_active_session_for_new_terminal() tuple
        +prepare_test_execution(test_path) tuple
        +finalize_test_execution(test_path, output) None
        +set_session_phase(phase, message, percent) None
        +append_session_log(message, source) None
        +record_execution_output(text) None
        +run_joiner_progress_monitor(session) bool
    }
    class program_analyzer {
        <<module>>
        +analyze_program(source_path) dict
        +get_program_spec(source_path) dict
    }
    class app {
        <<module Flask>>
        +app: Flask
        +index()
        +get_tests()
        +get_test()
        +get_test_spec_api()
        +get_session()
        +session_join()
        +session_create()
        +session_ready()
        +session_clear()
        +compile_code()
    }
    main ..> menu : opção 1
    main ..> app : opção 2 (porta 5000)
    main ..> test_orchestrator
    menu ..> main : compile_file
    menu ..> test_orchestrator
    menu ..> program_analyzer
    app ..> test_orchestrator
    app ..> program_analyzer
    app ..> main : subprocess python main.py
    test_orchestrator ..> program_analyzer
```

| Rota (`app.py`) | Método | Função |
|---|---|---|
| `/` | GET | `index` |
| `/api/tests` | GET | `get_tests` |
| `/api/get_test` | POST | `get_test` |
| `/api/test_spec` | POST | `get_test_spec_api` |
| `/api/session` | GET | `get_session` |
| `/api/session/join`, `/create`, `/ready`, `/clear` | POST | `session_join`, `session_create`, `session_ready`, `session_clear` |
| `/api/compile` | POST | `compile_code` (grava em `temp_code/`, roda `python main.py`, executa `output/<nome>.exe`) |

#### 4.8.2 Web didática

```mermaid
classDiagram
    %% @fonte server web_didatica/server.py
    %% @fonte app_js web_didatica/static/js/app.js
    %% @fonte fonte_real web_didatica/static/js/fonte_real.js
    %% @fonte fonte_mock web_didatica/static/js/fonte_mock.js
    %% @fonte arvore_ast web_didatica/static/js/arvore_ast.js
    %% @fonte erros web_didatica/static/js/erros.js
    %% @fonte arm web_didatica/static/js/arm.js
    %% @fonte ErroExtracao web_didatica/static/js/arm.js
    %% @fonte service src/service.py
    class server {
        <<module Flask>>
        +HOST: str
        +PORTA: int
        +LIMITE_FONTE_BYTES: int
        +PROGRAMA_T11: Path
        +ENTRADA_T11: str
        +criar_app() Flask
        -_ler_fonte()
        -_ler_execucao()
        -_ler_corpo()
        -_erro(status, codigo, mensagem)
        -_utf8_valido(texto) bool
    }
    class app_js {
        <<module ES>>
        +estado
        +iniciar()
        +analisarCodigo()
        +compilarExecutar()
        +executarDeNovo()
        +abrirExemplo(arquivo)
        +baixarArtefato(id, tipo)
        +aplicarEnvelope(resposta, enviado)
        +selecionarFase(chave)
        +painelTokens(dados)
        +painelAst(dados)
        +painelSemantico(dados)
        +painelTac(dados)
        +painelCpp(dados)
        +painelExecucao(dados)
    }
    class fonte_real {
        <<module ES>>
        +modo: "real"
        +listarExemplos()
        +carregarExemplo(arquivo)
        +analisar(source)
        +compilar(source)
        +executar(artifactId, stdin, timeoutSec)
        +urlArtefato(artifactId, tipo)
    }
    class fonte_mock {
        <<module ES>>
        +modo: "mock"
        +listarExemplos()
        +carregarExemplo(arquivo)
    }
    class arvore_ast {
        <<module ES>>
        +criarArvoreAst(raiz, aoSelecionar)
    }
    class erros {
        <<module ES>>
        +criarCartaoErro(d, ctx, aoAbrir)
        +contextoErros(codigoFonte, tokens)
        +CODIGOS_COM_EXPLICACAO
    }
    class arm {
        <<module ES>>
        +SUFIXO_TITULO
        +extrairArm(stdout)
        +armDaExecucao(execucao)
    }
    class ErroExtracao
    class Error
    class service {
        <<module>>
    }
    Error <|-- ErroExtracao
    app_js ..> fonte_real : padrão
    app_js ..> fonte_mock : ?fonte=mock
    app_js ..> arvore_ast
    app_js ..> erros
    app_js ..> arm
    arm ..> ErroExtracao : lança
    fonte_real ..> server : fetch /api/v1/*
    server ..> service : analyze · compile_program · execute · get_artifact
```

`app.js` escolhe a fonte de dados uma vez: `fonte_real` (HTTP para o servidor) ou
`fonte_mock` (fixtures JSON de `web_didatica/fixtures/`, só leitura, sem compilar). As duas
expõem `modo`, `listarExemplos` e `carregarExemplo`; apenas `fonte_real` expõe
`analisar`/`compilar`/`executar`/`urlArtefato`. Não existe uma interface JS formal comum: o
contrato é por convenção de nomes. As rotas do servidor estão na tabela da seção 3.2.

### 4.9 Runtime `minipar_rt` (Fork/Join local e distribuído)

```mermaid
classDiagram
    %% @fonte Value runtime/include/minipar_rt/value.hpp
    %% @fonte ValueCast runtime/include/minipar_rt/value.hpp
    %% @fonte Json runtime/include/minipar_rt/json.hpp
    %% @fonte JsonError runtime/include/minipar_rt/json.hpp
    %% @fonte ErrorCode runtime/include/minipar_rt/core.hpp
    %% @fonte TaskError runtime/include/minipar_rt/core.hpp
    %% @fonte TaskHandle runtime/include/minipar_rt/core.hpp
    %% @fonte TaskResult runtime/include/minipar_rt/core.hpp
    %% @fonte Destination runtime/include/minipar_rt/core.hpp
    %% @fonte TaskState runtime/include/minipar_rt/core.hpp
    %% @fonte Registry runtime/include/minipar_rt/core.hpp
    %% @fonte Executor runtime/include/minipar_rt/core.hpp
    %% @fonte api runtime/include/minipar_rt/api.hpp runtime/include/minipar_rt/core.hpp runtime/include/minipar_rt/value.hpp
    class Value {
        -data_: variant
        +kind() Kind
        +is_none() bool
        +is_int() bool
        +is_float() bool
        +is_bool() bool
        +is_string() bool
        +is_list() bool
        +as_int() int64
        +as_number() double
        +as_bool() bool
        +as_string() string
        +as_list() List
        +to_display() string
    }
    class ValueCast~T~ {
        +from(v: Value)$ T
    }
    class Json {
        +kind() Kind
        +dump() string
        +parse(text)$ Json
        +from_value(v: Value)$ Json
        +to_value() Value
    }
    class JsonError
    class ErrorCode {
        <<enumeration>>
        NONE
        TASK_FAILED
        UNKNOWN_FUNCTION
        TIMEOUT
        WORKER_UNAVAILABLE
        WORKER_LOST
        INVALID_HANDLE
        PROTOCOL_ERROR
        VERSION_MISMATCH
        BAD_DESTINATION
    }
    class TaskError {
        +code: ErrorCode
        +message: string
    }
    class TaskHandle {
        +id: uint64
        +task_id: string
    }
    class TaskResult {
        +ok: bool
        +value: Value
        +error: TaskError
        +task_id: string
        +executed_by: string
        +success(v, task_id, by)$ TaskResult
        +failure(code, message, task_id, by)$ TaskResult
    }
    class Destination {
        +kind: Kind
        +host: string
        +port: uint16
        +text: string
        +problem: string
        +local()$ Destination
        +remote(host, port)$ Destination
        +parse(raw)$ Destination
    }
    class TaskState {
        +m: mutex
        +cv: condition_variable
        +done: bool
        +remote: bool
        +result: TaskResult
        +task_id: string
    }
    class Registry {
        +m: mutex
        +functions: map~string, TaskFn~
        +tasks: map~uint64, TaskState~
        +next_id: atomic
        +build_id: string
        +get()$ Registry
    }
    class Executor {
        +get()$ Executor
        +submit(job) void
        +thread_count() size_t
        -loop() void
    }
    class api {
        <<module>>
        +start(function_id, args, where) TaskHandle
        +join(handle, timeout_ms) TaskResult
        +join_or_exit(handle, timeout_ms) Value
        +register_function(function_id, fn) void
        +set_build_id(build_id) void
        +build_id() string
        +to_value(v) Value
        +value_cast(v) T
        -start_local(st, function_id, args) void
        -complete(st, r) void
        -execute(function_id, args, executor) TaskResult
        -new_task(h, remote) TaskState
    }
    TaskResult *-- Value
    TaskResult *-- TaskError
    TaskError --> ErrorCode
    TaskState *-- TaskResult
    Registry o-- TaskState : tasks
    Json ..> Value : converte
    Json ..> JsonError : lança
    ValueCast ..> Value
    api ..> Registry
    api ..> Executor : tarefa local
    api ..> Destination
    api ..> TaskHandle : devolve
    api ..> TaskResult
```

*Figura 4.9a — núcleo do runtime (`value.hpp`, `json.hpp`, `core.hpp`, `api.hpp`).* As
funções `register_function`, `set_build_id`, `build_id` ficam em `core.hpp`; `to_value` e
`value_cast` em `value.hpp`; `start`, `join` e `join_or_exit` em `api.hpp`. Elas aparecem
juntas no módulo `api` porque formam a API C-FJ-v1 §2.3 que o código gerado chama. Os
membros `-` são do namespace `minipar_rt::detail`.

```mermaid
classDiagram
    %% @fonte RemoteConnection runtime/include/minipar_rt/remote.hpp
    %% @fonte ConnectionPool runtime/include/minipar_rt/remote.hpp
    %% @fonte remote runtime/include/minipar_rt/remote.hpp
    %% @fonte WorkerConnection runtime/include/minipar_rt/worker.hpp
    %% @fonte worker runtime/include/minipar_rt/worker.hpp
    %% @fonte Socket runtime/include/minipar_rt/net.hpp
    %% @fonte FrameStatus runtime/include/minipar_rt/net.hpp
    %% @fonte net runtime/include/minipar_rt/net.hpp
    %% @fonte TaskState runtime/include/minipar_rt/core.hpp
    %% @fonte Destination runtime/include/minipar_rt/core.hpp
    %% @fonte Json runtime/include/minipar_rt/json.hpp
    class RemoteConnection {
        -dest_: Destination
        -key_: string
        -pending_: map~string, TaskState~
        -queued_: deque~string~
        -worker_id_: string
        +key() string
        +begin() void
        +submit(st, payload) void
        -run() void
        -write_loop(fd) void
        -fail_all(code, msg) void
    }
    class ConnectionPool {
        +get()$ ConnectionPool
        +connection_for(d: Destination) RemoteConnection
        +remove(key, which) void
    }
    class remote {
        <<module>>
        +kProtocolVersion: int
        -start_remote(st, function_id, args, where) void
        -make_message(type, fields) Json
        -make_error_message(code, message) Json
        -result_from_message(msg, fallback_worker) TaskResult
        -same_protocol_version(msg) bool
    }
    class WorkerConnection {
        +sock: Socket
        +write_m: mutex
        +peer: string
        +send(msg: Json) bool
        +reject(code, message) void
    }
    class worker {
        <<module>>
        +run_worker(port, bind_address) int
        +worker_main_if_requested(argc, argv) int
        -serve_connection(c) void
        -run_task(c, request_id, task_id, function_id, args) void
        -worker_id() string
    }
    class Socket {
        +get() socket_t
        +valid() bool
        +shutdown_both() void
        +close() void
    }
    class FrameStatus {
        <<enumeration>>
        Ok
        Closed
        Invalid
    }
    class net {
        <<module>>
        +kMaxFrame: uint32
        +connect_tcp(host, port, timeout_ms, err) Socket
        +listen_tcp(bind_address, port, err) Socket
        +accept_tcp(listener, peer) Socket
        +write_frame(s, payload) bool
        +read_frame(s, out, err) FrameStatus
        +send_all(s, data, len) bool
        +recv_exact(s, data, len) bool
    }
    class TaskState
    class Destination
    class Json
    ConnectionPool o-- RemoteConnection : uma por destino (host e porta)
    RemoteConnection o-- TaskState : pending_
    RemoteConnection --> Destination
    RemoteConnection ..> net : connect_tcp · frames
    remote ..> ConnectionPool
    remote ..> Json
    worker ..> WorkerConnection : uma por coordenador
    WorkerConnection *-- Socket
    worker ..> net : listen_tcp · accept_tcp · frames
    net ..> FrameStatus
```

*Figura 4.9b — execução remota (`remote.hpp`, `worker.hpp`, `net.hpp`).* O mesmo binário é
coordenador ou worker: `worker_main_if_requested` só assume o processo quando recebe
`--minipar-worker <porta>`. Detalhes do protocolo e dos códigos de erro em C-FJ-v1 §2.5–2.6.

### 4.10 MiniCompilador do Teste 11 (classe escrita em MiniPar)

```mermaid
classDiagram
    %% @fonte MiniCompilador tests/2026_2/test11/minicompilador.minipar
    class MiniCompilador {
        +e: string
        +erro: string
        +tipos: list
        +inicios: list
        +tamanhos: list
        +ntok: list
        +nesq: list
        +ndir: list
        +raiz: number
        +pos: number
        +ultimo: number
        +svals: list
        +stoks: list
        +temp: number
        +reg: number
        +compilar(entrada)
        +analisarLexico()
        +analisarSintatico()
        +analisarSemantico()
        +gerarSaidas(resultado)
        +parseExpr()
        +parseTerm()
        +parseFactor()
        +novoNo(t, esq, dir)
        +imprimirTokens()
        +imprimirAST(no, nivel)
        +gerarTAC(no)
        +gerarARM(no)
        +registrarSimbolos()
        +imprimirSimbolos()
        +avaliar(no)
        +falhar(fase, msg)
    }
```

Os tokens e os nós da AST ficam em **listas numéricas paralelas** (`tipos`/`inicios`/`tamanhos`
e `ntok`/`nesq`/`ndir`) porque listas de strings estão fora do recorte (C-T11-v1 §3.4); o texto
de cada token é recuperado da entrada com `substr`. MiniPar não tem modificadores de acesso:
todos os membros são públicos. O programa principal cria `new MiniCompilador()` e chama
`compilar(input(...))`.

---

## 5. Diagramas de sequência

### 5.1 Compilar e executar pela Web didática (UC09)

```mermaid
sequenceDiagram
    actor E as Estudante
    participant UI as app.js
    participant FR as fonte_real.js
    participant S as server.py
    participant SV as service
    participant L as Lexer
    participant P as Parser
    participant SA as SemanticAnalyzer
    participant T as TACGenerator
    participant C as CppCodeGenerator
    participant G as g++
    participant B as binário

    E->>UI: Compilar e executar
    UI->>FR: compilar(source)
    FR->>S: POST /api/v1/compile {source}
    S->>SV: compile_program(fonte)
    SV->>L: Lexer(source).tokenize()
    L-->>SV: tokens, diagnostics
    SV->>P: Parser(tokens, exit_on_error=False).parse()
    P-->>SV: Program (ou ParseError)
    SV->>SV: serialize_ast(program)
    SV->>SA: analyze(program)
    SA-->>SV: ok, scopes, symbols, diagnostics
    SV->>T: generate_text(program)
    T-->>SV: texto TAC
    SV->>C: generate_text(program, semantic, source)
    C-->>SV: texto C++
    SV->>SV: grava output/web/<id>/program.cpp e .tac, _register
    SV->>C: compile_cpp(program.cpp, program.exe)
    C->>G: g++ -std=c++20 -O3 ... (run_bounded)
    G-->>C: returncode, stdout, stderr
    C-->>SV: (payload, code)
    SV-->>S: envelope minipar.compile.v1 (artifacts.binary_id)
    S-->>FR: HTTP 200 JSON
    FR-->>UI: envelope
    UI->>UI: aplicarEnvelope (confere source_hash)
    UI->>FR: executar(binary_id, stdin, timeout)
    FR->>S: POST /api/v1/execute
    S->>SV: execute(artifact_id, stdin, timeout_sec)
    SV->>SV: get_artifact(id, "binary")
    SV->>B: run_bounded([binário], stdin, timeout)
    B-->>SV: returncode, stdout, stderr, timed_out
    SV-->>S: envelope minipar.execute.v1
    S-->>FR: HTTP 200 JSON
    FR-->>UI: execução
    UI-->>E: painelExecucao (e seção ARM no Teste 11)
```

Em qualquer fase com erro, o serviço para, devolve `ok: false` com o diagnóstico e as fases
seguintes `skipped`; o servidor responde HTTP 200 mesmo assim (C-WEB-v1 §1.8). A CLI
(`main.compile_file`) segue a mesma ordem de fases, mas grava em `output/<nome>.*`, usa
`Parser` com `exit_on_error=True` e `TACGenerator.generate`/`CppCodeGenerator.generate`.

### 5.2 Fork/Join local e remoto no binário gerado (UC12, UC13)

```mermaid
sequenceDiagram
    participant M as main gerado
    participant A as minipar_rt api
    participant R as Registry
    participant X as Executor
    participant CP as ConnectionPool
    participant RC as RemoteConnection
    participant W as worker (outro processo)

    M->>A: set_build_id(sha256 do fonte)
    M->>A: register_function("f", __fj_wrap_f)
    M->>A: worker_main_if_requested(argc, argv)
    A-->>M: -1 (não é worker)

    Note over M,X: fork f(x) — sem destino
    M->>A: start("f", args)
    A->>R: new_task(h, remote=false)
    A->>X: submit(job)
    A-->>M: TaskHandle
    X->>R: find_function("f")
    X->>X: execute → __fj_wrap_f(args)
    X->>A: complete(TaskState, TaskResult)

    Note over M,W: fork f(x) on "host:porta"
    M->>A: start("f", args, Destination::parse("host:porta"))
    A->>R: new_task(h, remote=true)
    A->>CP: connection_for(destino)
    CP-->>A: RemoteConnection (criada no 1º uso)
    A->>RC: submit(TaskState, TASK JSON)
    A-->>M: TaskHandle
    RC->>W: HELLO {build_id, request_id}
    W-->>RC: HELLO_OK {worker_id, host, pid, build_id}
    RC->>W: TASK {task_id, function_id, args}
    W->>W: run_task em thread própria → execute
    W-->>RC: RESULT {task_id, status, result | error, worker_id}
    RC->>A: complete(TaskState, TaskResult)

    Note over M,A: join h
    M->>A: join_or_exit(handle, timeout)
    A->>R: localiza TaskState
    A->>A: espera cv até done (ou TIMEOUT)
    A->>R: remove a tarefa (handle coletado)
    A-->>M: Value (ou stderr + exit 1 em erro)
```

A conexão é uma por destino `host:porta` e é reutilizada; o `HELLO` acontece uma vez por
conexão (no diagrama, antes do primeiro `TASK`). Se `build_id` ou `protocol_version` não
conferem, todas as tarefas pendentes daquela conexão terminam com `VERSION_MISMATCH`. Perda
de conexão termina as pendentes com `WORKER_LOST`; worker inacessível, com
`WORKER_UNAVAILABLE`.

---

## 6. Correspondência com os componentes exigidos

Componentes pedidos em `00_DOCUMENTO_MESTRE_INICIAL.md` §11.1 e onde estão modelados:

| Componente exigido | Componente / classe real | Diagrama |
|---|---|---|
| Analisador léxico | `Lexer`, `Token`, `TokenType` | 3.1, 4.1 |
| Analisador sintático | `Parser`, `ParseError`; AST em `ast_nodes` | 3.1, 4.2, 4.3 |
| Analisador semântico | `SemanticAnalyzer`, `ValueType` | 3.1, 4.4 |
| Tabela de símbolos | `Symbol` + pilha `_scopes`; listas publicadas `scopes`/`symbols` | 4.4 |
| Gerador TAC | `TACGenerator` | 3.1, 4.5 |
| Gerador C++ | `CppCodeGenerator`, `CppTaskContext`, `CppType`, `cpp_template` | 3.1, 4.6 |
| Controle/orquestração do compilador | `main.compile_file` (CLI) e `service._pipeline` (serviço) | 3.1, 4.7, 4.8.1, 5.1 |
| Execução | `CppCodeGenerator.compile_cpp`, `service.execute`, `run_bounded`, `Executor` | 4.6, 4.7, 4.9 |
| Comunicação | `MiniParChannel` (C++ do `c_channel`), `RemoteConnection`, `ConnectionPool`, `WorkerConnection`, `net` | 4.6, 4.9, 5.2 |
| Interfaces | CLI, Web original, Web didática; contratos C-WEB-v1, C-FJ-v1, C-T11-v1 | 2, 3, 4.8 |

Os diagramas recomendados de §11.4 também estão cobertos: fluxo de compilação (5.1),
sequência de Fork/Join e comunicação distribuída (5.2) e fluxo da interface didática (5.1).

---

## 7. Observações sobre a implementação real

Pontos em que o modelo segue o código e não uma arquitetura idealizada. Nenhum deles é
defeito apontado por este card; ficam registrados para quem revisar ou escrever o relatório.

1. **Sem interfaces abstratas entre as fases.** As fases são classes concretas chamadas em
   sequência por `main.compile_file` e por `service._pipeline`. O "contrato" entre elas é o
   tipo dos dados (`List[Token]`, `Program`, `SemanticAnalyzer` já analisado). Isso segue a
   decisão de `00_DOCUMENTO_MESTRE_INICIAL.md` §11.3 de não criar camadas artificiais.
2. **Dois orquestradores.** A CLI e o serviço repetem a sequência de fases com diferenças
   reais: a CLI grava em `output/`, usa `exit_on_error=True` e imprime; o serviço captura
   diagnósticos, isola cada requisição em `output/web/<id>/` e devolve envelopes.
3. **A Web original não usa o serviço.** `app.compile_code` chama `python main.py` por
   subprocesso e lê os arquivos de `output/`. Só a Web didática consome C-WEB-v1.
4. **A tabela de símbolos não é uma classe.** Ver 4.4.
5. **`CppTaskContext` mora em `semantic.py`** mas é usada só pelo gerador C++
   (`CppCodeGenerator.fj`). O diagrama de componentes mostra essa dependência como
   "Gerador C++ usa CppTaskContext".
6. **Runtime header-only.** `minipar_rt` não é uma biblioteca compilada à parte: entra no
   binário por `#include` e `-I runtime/include` em `compile_cpp`.
7. **Canais legados x Fork/Join.** `c_channel`/`send`/`receive` usam `MiniParChannel`
   (`cpp_template.py`, sockets próprios) e não o protocolo do `minipar_rt`.

---

## 8. Verificação dos diagramas

Script: [`auditorias/DOC-02_sondas_uml.py`](auditorias/DOC-02_sondas_uml.py). Ele lê os blocos
`classDiagram` deste arquivo e confere, para cada classe com `%% @fonte`:

- a classe (ou módulo) existe no arquivo indicado;
- cada atributo e método listado existe naquela classe ou módulo (Python por AST; C++, JS e
  MiniPar por busca de declaração no arquivo);
- cada herança `Pai <|-- Filho` existe no código (Python e JS);
- **cobertura:** toda classe de `src/*.py`, todo `class`/`struct`/`enum class` de nível de
  namespace em `runtime/include/minipar_rt/*.hpp` e todo módulo de
  `web_didatica/static/js/*.js` aparece em algum diagrama.

Resultado e controle negativo estão no handoff
[`auditorias/DOC-02_UML.md`](auditorias/DOC-02_UML.md). Mudanças em `src/`, `runtime/include/`
ou `web_didatica/static/js/` exigem reexecutar as sondas.
