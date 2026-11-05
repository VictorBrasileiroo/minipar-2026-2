# Pseudocódigos do núcleo do compilador MiniPar 2026.2

| Campo | Valor |
|---|---|
| Card | `DOC-01` — BNF final e pseudocódigos núcleo (Eixo B) |
| Fonte da verdade | `src/lexer.py`, `src/parser.py`, `src/semantic.py`, `src/tac.py`, `src/service.py` |
| Base verificada | `origin/dev` em `f54c75e` |
| Verificação | `python docs/auditorias/DOC-01_sondas_bnf.py` (evidências em [`auditorias/DOC-01_BNF_PSEUDOCODIGOS.md`](auditorias/DOC-01_BNF_PSEUDOCODIGOS.md)) |
| Estado | `IN_REVIEW`: falta a **aprovação de exatidão pelo Eixo A** |
| Gramática | [`12_BNF_MINIPAR_2026_2.md`](12_BNF_MINIPAR_2026_2.md) |

Os pseudocódigos seguem o código real, função por função, e citam o método
correspondente entre colchetes. Detalhes de implementação sem efeito no resultado
(nomes de variáveis internas, otimizações de cache) foram simplificados; regras de
aceitação, ordem das verificações e tratamento de erros foram mantidos.

Convenções: `←` atribuição; `pilha.topo` último elemento; `nó.campo` acesso a campo
da AST; `relatar(...)` registra diagnóstico sem interromper a análise.

---

## 0. Visão geral do pipeline [`service._pipeline`]

```text
função PIPELINE(fonte, operação ∈ {analyze, compile}):
    resultado ← envelope minipar.compile.v1 com todas as fases "skipped"
    // 1. Léxico
    lexer ← LEXER(fonte); tokens ← lexer.TOKENIZAR()
    publicar fase lexer (tokens sem END_OF_FILE)
    se lexer.diagnósticos ≠ ∅: retornar resultado            // não chama o parser
    // 2. Sintaxe
    tentar programa ← PARSER(tokens, sair_no_erro=falso).PARSE()
    se ParseError e: anexar e.diagnóstico; retornar resultado // 1º erro sintático
    publicar AST serializada
    // 3. Semântica + tabela de símbolos
    sem ← ANALISADOR_SEMANTICO(); válido ← sem.ANALISAR(programa)
    publicar sem.escopos, sem.símbolos
    anexar diagnósticos semânticos ordenados por linha
    se não válido: retornar resultado
    // 4. TAC
    tentar tac ← GERADOR_TAC().GERAR_TEXTO(programa)
    se NotImplementedError: anexar TAC_UNSUPPORTED_FEATURE; retornar resultado
    // 5. C++
    tentar cpp ← GERADOR_CPP().GERAR_TEXTO(programa, sem, fonte)
    se NotImplementedError ou CppProofError: anexar CPP_UNSUPPORTED_FEATURE; retornar
    se operação = analyze: resultado.ok ← verdadeiro; retornar resultado
    // 6. g++ (somente compile)
    gravar program.cpp e program.tac; compilar com g++; registrar binário
    resultado.ok ← (g++ terminou com sucesso)
    // Qualquer outra exceção: INTERNAL_ERROR na fase corrente
```

Cada fase só roda se a anterior terminou sem erro. A CLI (`main.py`) segue a mesma
ordem, mas o parser é criado com `sair_no_erro = verdadeiro` (imprime
`[ERRO SINTATICO]` e encerra com código 1).

---

## 1. Lexer [`Lexer.tokenize`]

```text
estrutura TOKEN: tipo, lexema, linha, coluna

função TOKENIZAR(fonte):
    pos ← 0; linha ← 1; coluna ← 1; tokens ← []; diagnósticos ← []

    enquanto pos < |fonte|:
        PULAR_ESPACOS_E_COMENTARIOS()
        se pos ≥ |fonte|: sair do laço
        c ← ESPIAR(); lin0 ← linha; col0 ← coluna

        se c é letra (Unicode) ou "_":
            lexema ← consumir enquanto ESPIAR() é alfanumérico ou "_"
            tipo ← KEYWORDS[lexema] se existir, senão IDENTIFIER
            emitir TOKEN(tipo, lexema, lin0, col0)

        senão se c é dígito:
            lexema ← consumir dígitos
            se ESPIAR() = ".": lexema ← lexema + AVANÇAR() + consumir dígitos
            emitir TOKEN(NUMBER, lexema, lin0, col0)

        senão se c = '"':
            AVANÇAR(); texto ← ""
            enquanto ESPIAR() ∉ {'"', FIM}:
                se ESPIAR() = "\":
                    AVANÇAR(); se FIM: sair
                    e ← AVANÇAR()
                    texto ← texto + {n→"\n", t→"\t", "→'"', \→"\"}.obter(e, e)
                senão texto ← texto + AVANÇAR()
            se ESPIAR() = '"': AVANÇAR()
            senão relatar(LEX_UNTERMINATED_STRING, lin0, col0)
            emitir TOKEN(STRING_LITERAL, texto, lin0, col0)   // emitido mesmo com erro

        senão:   // operadores e delimitadores
            op ← AVANÇAR()
            se op ∈ {"=", "!", "<", ">"} e ESPIAR() = "=": emitir EQ/NEQ/LTE/GTE; AVANÇAR()
            senão se op = "&" e ESPIAR() = "&": emitir AND; AVANÇAR()
            senão se op = "|" e ESPIAR() = "|": emitir OR; AVANÇAR()
            senão se op ∈ {"=", "!", "<", ">"}: emitir ASSIGN/NOT/LT/GT
            senão se op ∈ TABELA_SIMPLES (+ - * / % { } ( ) [ ] ; , .): emitir tipo da tabela
            senão emitir TOKEN(UNKNOWN, op, lin0, col0)        // inclui "&" e "|" isolados

    para cada token t com t.tipo = UNKNOWN: relatar(LEX_UNKNOWN_CHAR, t.linha, t.coluna)
    ordenar diagnósticos por (linha, coluna)
    emitir TOKEN(END_OF_FILE, "", linha, coluna)
    retornar tokens

procedimento PULAR_ESPACOS_E_COMENTARIOS():
    enquanto não FIM:
        se ESPIAR() é espaço: AVANÇAR()
        senão se ESPIAR() = "#": AVANÇAR até "\n" ou FIM   // "\n" fica para o próximo giro
        senão retornar

função AVANÇAR():
    c ← fonte[pos]; pos ← pos + 1
    se c = "\n": linha ← linha + 1; coluna ← 1  senão coluna ← coluna + 1
    retornar c
```

O lexer nunca aborta: produz tokens até o fim e devolve os erros em
`diagnostics`. Quem decide parar é o chamador (serviço/CLI).

---

## 2. Parser — descida recursiva [`Parser`]

### 2.1 Primitivas e erro

```text
ESPIAR()        → token atual (END_OF_FILE se passou do fim)
CASAR(tipo)     → se ESPIAR().tipo = tipo: AVANÇAR(); retornar verdadeiro; senão falso
CONSUMIR(tipo, msg):
    se ESPIAR().tipo = tipo: retornar AVANÇAR()
    FALHAR(SYN_EXPECTED_TOKEN, msg + " (Encontrado: " + ESPIAR().lexema + ")")

FALHAR(código, mensagem, linha, coluna):                         [_fail]
    d ← {phase: "parser", severity: "error", code, message, line, column}
    diagnósticos.anexar(d)
    se sair_no_erro: imprimir "[ERRO SINTATICO] Linha L: msg" em stderr; encerrar(1)
    lançar ParseError(d)
```

Não há recuperação de erro: o **primeiro** erro sintático interrompe a análise.

### 2.2 Programa e comandos

```text
função PARSE():                                                   [parse]
    programa ← Program([])
    enquanto ESPIAR().tipo ≠ END_OF_FILE: programa.comandos.anexar(COMANDO())
    retornar programa

função COMANDO():                                                 [_parse_statement]
    se CASAR(CLASS):    retornar DECL_CLASSE()
    se CASAR(FUNC):     retornar DECL_FUNCAO()
    se CASAR(RETURN):   valor ← nulo se ESPIAR()=";" senão EXPRESSAO(); CASAR(";")
                        retornar ReturnStmt(valor)
    se CASAR(BREAK):    CASAR(";"); retornar BreakStmt
    se CASAR(CONTINUE): CASAR(";"); retornar ContinueStmt
    se CASAR(VAR):      retornar DECL_VARIAVEL("var")
    se ESPIAR() é TYPE: t ← AVANÇAR(); retornar DECL_VARIAVEL(t.lexema)
    se CASAR(SEQ) ou ESPIAR()="{": retornar BLOCO_SEQ()
    se CASAR(PAR):      retornar BLOCO_PAR()
    se CASAR(PRINT):    retornar PRINT()        // "(" [args] ")" ";"
    se CASAR(SEND):     retornar SEND()         // "(" canal "," msg ")" ";"
    se CASAR(IF):       retornar IF()
    se CASAR(WHILE):    retornar WHILE()
    se CASAR(DO):       retornar DO_WHILE()
    se CASAR(FOR):      retornar FOR()
    se ESPIAR().tipo ∈ {IDENTIFIER, THIS, NEW, RECEIVE, INPUT, C_CHANNEL,
                        MATRIX, "[", FORK, JOIN}:
        e ← EXPRESSAO()
        se CASAR("="): retornar CAUDA_ATRIBUICAO(e, exige_ponto_virgula=verdadeiro)
        se e é MethodCall, FuncCallExpr, ForkExpr ou JoinExpr:
            CONSUMIR(";"); retornar e
        FALHAR(SYN_INVALID_STATEMENT, "Instrucao ou expressao isolada invalida")
    FALHAR(SYN_UNRECOGNIZED_STATEMENT, "Instrucao nao reconhecida")

função CAUDA_ATRIBUICAO(alvo, exige_ponto_virgula):              [_parse_assignment_tail]
    valor ← EXPRESSAO(); se exige_ponto_virgula: CONSUMIR(";")
    caso alvo seja
        IdentifierExpr → retornar Assignment(alvo.nome, valor)
        PropertyAccess → retornar PropertyAssign(alvo.objeto, alvo.propriedade, valor)
        IndexExpr      → retornar IndexAssign(alvo, valor)
    FALHAR(SYN_INVALID_ASSIGNMENT, "Atribuicao invalida")
```

### 2.3 Declarações, blocos e controle

```text
função DECL_VARIAVEL(tipo, exige_ponto_virgula=verdadeiro):    [_parse_var_decl]
    nome ← CONSUMIR(IDENTIFIER).lexema
    inicial ← EXPRESSAO() se CASAR("=") senão nulo
    se exige_ponto_virgula: CONSUMIR(";")
    retornar VarDecl(nome, tipo, inicial)

função DECL_FUNCAO():                                             [_parse_func_decl]
    nome ← CONSUMIR(IDENTIFIER); CONSUMIR("(")
    params ← []
    se ESPIAR() ≠ ")":
        repetir: se ESPIAR() é TYPE: AVANÇAR()          // tipo do parâmetro é descartado
                 params.anexar(CONSUMIR(IDENTIFIER).lexema)
        enquanto CASAR(",")
    CONSUMIR(")")
    retornar FuncDecl(nome, params, BLOCO_SEQ())      // corpo exige "{"

função DECL_CLASSE():                                             [_parse_class_decl]
    nome ← CONSUMIR(IDENTIFIER)
    super ← CONSUMIR(IDENTIFIER) se CASAR(EXTENDS) senão nulo
    CONSUMIR("{"); atributos ← []; métodos ← []
    enquanto ESPIAR() ∉ {"}", END_OF_FILE}:
        se CASAR(VAR):  atributos.anexar(DECL_VARIAVEL("var"))
        senão se CASAR(FUNC): métodos.anexar(DECL_FUNCAO())
        senão FALHAR(SYN_EXPECTED_TOKEN, "Esperado 'var' ou 'func' na definicao da classe")
    CONSUMIR("}")
    retornar ClassDecl(nome, super, atributos, métodos)

função BLOCO_SEQ() / BLOCO_PAR():                     [_parse_seq_block/_parse_par_block]
    CONSUMIR("{"); comandos ← []
    enquanto ESPIAR() ∉ {"}", END_OF_FILE}: comandos.anexar(COMANDO())
    CONSUMIR("}")
    retornar SeqBlock(comandos) / ParBlock(comandos)

função IF():      CONSUMIR("("); c ← EXPRESSAO(); CONSUMIR(")")
                  então ← COMANDO(); senão_ ← COMANDO() se CASAR(ELSE) senão nulo
                  retornar IfStmt(c, então, senão_)
função WHILE():   CONSUMIR("("); c ← EXPRESSAO(); CONSUMIR(")"); retornar WhileStmt(c, COMANDO())
função DO_WHILE(): corpo ← COMANDO(); CONSUMIR(WHILE); CONSUMIR("(")
                   c ← EXPRESSAO(); CONSUMIR(")"); CASAR(";")       // ";" opcional
                   retornar DoWhileStmt(corpo, c)

função FOR():                                                     [_parse_for_stmt]
    CONSUMIR("("); init ← cond ← passo ← nulo
    se CASAR(VAR):
        nome ← CONSUMIR(IDENTIFIER)
        se CASAR(IN):                                  // for-in
            iterável ← EXPRESSAO(); CONSUMIR(")")
            retornar ForStmt(iterador=nome, iterável, corpo=COMANDO())
        init ← VarDecl(nome, "var", EXPRESSAO() se CASAR("=") senão nulo); CONSUMIR(";")
    senão se ESPIAR() é TYPE:
        t ← AVANÇAR(); init ← DECL_VARIAVEL(t.lexema, exige_ponto_virgula=falso); CONSUMIR(";")
    senão se não CASAR(";"):
        e ← EXPRESSAO()
        init ← CAUDA_ATRIBUICAO(e, falso) se CASAR("=") senão e; CONSUMIR(";")
    se não CASAR(";"): cond ← EXPRESSAO(); CONSUMIR(";")
    se ESPIAR() ≠ ")":
        e ← EXPRESSAO(); passo ← CAUDA_ATRIBUICAO(e, falso) se CASAR("=") senão e
    CONSUMIR(")")
    retornar ForStmt(init, cond, passo, corpo=COMANDO())
```

### 2.4 Expressões por precedência

```text
EXPRESSAO()  → OU()
OU()         → e ← E();      enquanto CASAR("||"): e ← Binária("||", e, E())
E()          → e ← COMP();   enquanto CASAR("&&"): e ← Binária("&&", e, COMP())
COMP()       → e ← TERMO();  enquanto ESPIAR() ∈ {==,!=,<,>,<=,>=}: op ← AVANÇAR(); e ← Binária(op, e, TERMO())
TERMO()      → e ← FATOR();  enquanto ESPIAR() ∈ {+,-}:   op ← AVANÇAR(); e ← Binária(op, e, FATOR())
FATOR()      → e ← UNARIA(); enquanto ESPIAR() ∈ {*,/,%}: op ← AVANÇAR(); e ← Binária(op, e, UNARIA())
UNARIA()     → se ESPIAR() ∈ {-,+,!}: op ← AVANÇAR(); retornar Unária(op, UNARIA())
               retornar PRIMARIA()

função PRIMARIA():                                                [_parse_primary]
    t ← ESPIAR()
    se CASAR(FORK):
        nome ← CONSUMIR(IDENTIFIER, "Esperado nome de funcao global apos fork")
        args ← ARGUMENTOS_ENTRE("(", ")")
        destino ← EXPRESSAO() se CASAR(ON) senão nulo      // expressão completa
        nó ← ForkExpr(nome, args, destino)
    senão se CASAR(JOIN):
        CONSUMIR("("); h ← EXPRESSAO()
        tempo ← EXPRESSAO() se CASAR(",") senão nulo; CONSUMIR(")")
        nó ← JoinExpr(h, tempo)
    senão se CASAR(MATRIX):   nó ← MatrixCreateExpr(três expressões entre "(" "," "," ")")
    senão se CASAR("["):      nó ← ListLiteral(lista separada por "," até "]")
    senão se CASAR(C_CHANNEL):nó ← CChannelExpr(ip, porta)
    senão se CASAR(RECEIVE):  nó ← ReceiveExpr(canal)
    senão se CASAR(INPUT):    nó ← InputExpr(prompt opcional)
    senão se CASAR(NEW):      nó ← NewExpr(CONSUMIR(IDENTIFIER), ARGUMENTOS_ENTRE("(", ")"))
    senão se CASAR(THIS):     nó ← ThisExpr
    senão se CASAR(NUMBER | STRING_LITERAL | BOOL_LITERAL): nó ← literal correspondente
    senão se CASAR(IDENTIFIER):
        nó ← FuncCallExpr(t.lexema, ARGUMENTOS até ")") se CASAR("(") senão IdentifierExpr(t.lexema)
    senão se CASAR("("):      nó ← EXPRESSAO(); CONSUMIR(")")
    senão FALHAR(SYN_EXPECTED_EXPRESSION, "Expressao esperada")

    repetir:                                           // sufixos, associativos à esquerda
        se CASAR("."):
            p ← CONSUMIR(IDENTIFIER)
            nó ← MethodCall(nó, p, ARGUMENTOS até ")") se CASAR("(") senão PropertyAccess(nó, p)
        senão se CASAR("["):
            nó ← IndexExpr(nó, EXPRESSAO()); CONSUMIR("]")
        senão sair
    retornar nó
```

---

## 3. Tabela de símbolos [`SemanticAnalyzer._enter_scope/_exit_scope/_define_symbol/_lookup`]

### 3.1 Estruturas

```text
estrutura SIMBOLO:
    nome, tipo                       // tipo: "var", "number", "int", "string", "bool",
                                     //       "list", "matrix", "c_channel", "task", nome de classe,
                                     //       "FUNC" ou "CLASS"
    params[], atributos{nome→tipo}, métodos{nome→params}
    tipo_valor : ValueType | nulo    // tipo estrutural (elementos de listas, resultado de task)

estrutura VALUE_TYPE: tipo_base, elementos (alternativas, sem posição), resultado (para task)

pilha_escopos  : lista de dicionários nome → SIMBOLO   // escopo [0] = global
escopos_pub    : lista de {id "sN", kind, name, parent, line}   // publicada na Web (C-WEB-v1)
simbolos_pub   : lista de {name, kind, type, scope, line, params}
pilha_ids      : ids dos escopos abertos (para "parent")
pilha_nós      : nós da AST em validação (define o kind do escopo e do símbolo)
especializado  : verdadeiro durante a reanálise de tarefas Fork/Join (não publica nada)
```

### 3.2 Operações

```text
procedimento ENTRAR_ESCOPO():
    pilha_escopos.empilhar({})
    se especializado: retornar
    nó ← pilha_nós.topo (ou nulo no início)
    kind ← caso nó seja ClassDecl → "class"
                        FuncDecl  → "method" se dentro de classe senão "function"
                        SeqBlock  → "seq"; ParBlock → "par"; ForStmt → "for"
                        nulo      → "global"
    id ← "s" + |escopos_pub|
    escopos_pub.anexar({id, kind, name (classe, função ou Classe.método), parent ← pilha_ids.topo, line})
    pilha_ids.empilhar(id)

procedimento SAIR_ESCOPO():
    se |pilha_escopos| > 1:                 // o global nunca é desempilhado
        pilha_escopos.desempilhar()
        se não especializado: pilha_ids.desempilhar()

procedimento DEFINIR(nome, tipo, linha, params=[]):
    se nome ∈ pilha_escopos.topo:
        relatar(linha, "Variavel 'nome' ja declarada.", SEM_REDECLARED); retornar
    pilha_escopos.topo[nome] ← SIMBOLO(nome, tipo, params)
    se especializado: retornar
    nó ← pilha_nós.topo; kind_escopo ← kind do escopo atual
    kind ← caso nó seja VarDecl   → "attribute" se kind_escopo = "class" senão "variable"
                        FuncDecl  → se tipo = "FUNC": "method"/"function" senão "parameter"
                        ClassDecl → "class"
                        outro     → "iterator"          // variável do for-in
    tipo_pub ← nulo se kind ∈ {function, method, class}
               senão "var" se tipo ∈ {unknown, FUNC, CLASS} senão tipo
    simbolos_pub.anexar({nome, kind, tipo_pub, escopo atual, linha, params se função/método})

função BUSCAR(nome):
    para escopo de pilha_escopos.topo até pilha_escopos[0]:
        se nome ∈ escopo: retornar escopo[nome]
    retornar nulo                           // escopo léxico, do mais interno ao global
```

Uma `func` cria dois escopos: o da função (`function`/`method`), onde ficam os
parâmetros, e o do corpo (`seq`), onde ficam as locais. Sombrear um nome em escopo
interno é permitido; redeclarar no mesmo escopo, não. Funções e classes globais
também são coletadas antes da validação (seção 4.1), por isso podem ser chamadas
antes da declaração.

---

## 4. Analisador semântico e tratamento de erros [`SemanticAnalyzer`]

### 4.1 Entrada [`analyze`]

```text
função ANALISAR(programa):
    // Passo 1: coleta antecipada (só nível global)            [_collect_declarations]
    para cada comando c do programa:
        se c é FuncDecl:
            se c.nome ∈ NATIVAS: relatar(SEM_RESERVED_NAME)
            funções[c.nome] ← SIMBOLO(c.nome, "FUNC", c.params)
        se c é ClassDecl:
            registrar nó, superclasse, inicializador sintético dos atributos
            classes[c.nome] ← SIMBOLO("CLASS", atributos{nome→tipo inferido}, métodos{nome→params})
    para cada classe: CADEIA_HERANCA(classe)   // relata SEM_INHERITANCE_CYCLE se houver ciclo
    COLETAR_FUNCOES_FJ()     // fecho: funções/métodos que contêm ou chamam fork/join
    fj_ativo ← programa contém ForkExpr ou JoinExpr
    globais ← funções ∪ {variáveis globais declaradas com seu tipo inferido}

    // Passo 2: validação em ordem do texto
    para cada comando c do programa: VALIDAR(c, valor_exigido=falso)
    juntar assinaturas provisórias de fork que não tiveram chamada especializada
    retornar não houve_erros
```

### 4.2 Relato de erros [`_report`]

```text
procedimento RELATAR(linha, mensagem, código):
    se especializado e mensagem não começa com "FJ-": retornar   // evita duplicar erros comuns
    se mensagem começa com "FJ-":
        chave ← (linha, classe atual, função atual, mensagem)
        se chave já relatada: retornar; senão marcar chave
    diagnósticos.anexar({phase: "semantic", severity: "error", code, message, line, column: nulo})
    se emitir_diagnosticos: imprimir "[ERRO SEMANTICO] Linha L (Funcao: f): msg" em stderr
    houve_erros ← verdadeiro
```

O semântico **não para** no primeiro erro: percorre a AST inteira e acumula todos
os diagnósticos. A CLI aborta depois da fase; o serviço publica os diagnósticos
ordenados por linha e não executa TAC/C++.

### 4.3 Inferência e compatibilidade de tipos [`_infer_type`, `_types_compatible`]

```text
função INFERIR(nó):
    caso nó seja
        ForkExpr         → "task"
        NumberExpr       → "number";  StringExpr, InputExpr, ReceiveExpr → "string"
        BoolExpr         → "bool";    CChannelExpr → "c_channel"
        ListLiteral      → "list";    MatrixCreateExpr → "matrix"
        NewExpr          → nome da classe;  ThisExpr → classe atual
        IdentifierExpr   → BUSCAR(nome).tipo  (tipo estrutural se for task)  ou "unknown"
        UnaryExpr        → "bool" se op = "!" senão INFERIR(operando)
        BinaryExpr       → "bool" para comparações e lógicos
                           "string" se op = "+" e algum lado é string
                           "list"   se op = "+" e algum lado é list
                           "number" nos demais
        PropertyAccess   → tipo do atributo na cadeia de herança, ou "unknown"
        FuncCallExpr     → random/exp/len/to_number → "number"; substr/to_string → "string"
                           range/parse_ints → "list"; demais → "unknown"
        IndexExpr        → "number" se o objeto é list, senão "unknown"
        outro            → "unknown"

função COMPATIVEL(declarado, real):
    se declarado ou real ∈ {"var", "unknown"}: retornar verdadeiro
    se {declarado, real} = {"int", "number"}: retornar verdadeiro
    retornar declarado = real
```

### 4.4 Validação por nó [`validate_node`]

```text
procedimento VALIDAR(nó, valor_exigido=verdadeiro):
    pilha_nós.empilhar(nó)
    caso nó seja
    VarDecl:
        VALIDAR(nó.inicial); real ← INFERIR(nó.inicial)
        declarado ← real se nó.tipo = "var" e real ≠ "unknown" senão nó.tipo
        se não COMPATIVEL(declarado, real): relatar(SEM_TYPE_MISMATCH)
        DEFINIR(nó.nome, declarado); guardar tipo estrutural no símbolo
    Assignment:
        VERIFICAR_GLOBAL_NA_TAREFA(nó.nome)                     // FJ-SEM-05
        s ← BUSCAR(nó.nome); se s = nulo: relatar(SEM_UNDECLARED_VARIABLE)
        VALIDAR(nó.valor)
        se s e não COMPATIVEL(s.tipo, INFERIR(nó.valor)): relatar(SEM_TYPE_MISMATCH)
    IdentifierExpr:
        VERIFICAR_GLOBAL_NA_TAREFA(nó.nome)
        se BUSCAR(nó.nome) = nulo: relatar(SEM_UNDECLARED_VARIABLE)
    BinaryExpr:
        VALIDAR(esq); VALIDAR(dir); te, td ← INFERIR(esq), INFERIR(dir)
        se fj_ativo e op aritmético e (te ou td ∈ {task, c_channel, classe}): relatar(FJ-SEM-06)
        se op ∈ {+, ==, !=, <, <=, >, >=} e um lado é string e o outro é tipo conhecido ≠ string:
            relatar(SEM_TYPE_MISMATCH)
        se op ∈ {-, *, /, %} e algum lado conhecido não é number/int: relatar(SEM_NUMERIC_OPERANDS)
    UnaryExpr:
        VALIDAR(operando); se fj_ativo e op ∈ {+,-} e operando é task/canal/objeto: relatar(FJ-SEM-06)
    SeqBlock, ParBlock:
        ENTRAR_ESCOPO(); para cada c: VALIDAR(c, falso); SAIR_ESCOPO()
    IfStmt:     VALIDAR(cond); VALIDAR(então, falso); VALIDAR(senão, falso)
    WhileStmt, DoWhileStmt:
        VALIDAR(cond); profundidade_laço += 1; VALIDAR(corpo, falso); profundidade_laço −= 1
    ForStmt:
        ENTRAR_ESCOPO()
        se for-in: VALIDAR(iterável); DEFINIR(iterador, "var")
                   tipo estrutural do iterador ← união dos elementos do iterável
        senão: VALIDAR(init, falso); VALIDAR(cond); VALIDAR(passo, falso)
        profundidade_laço += 1; VALIDAR(corpo, falso); profundidade_laço −= 1
        SAIR_ESCOPO()
    BreakStmt, ContinueStmt:
        se profundidade_laço = 0: relatar(SEM_OUTSIDE_LOOP)
    ClassDecl:
        se superclasse ∉ classes: relatar(SEM_UNDECLARED_SUPERCLASS)
        DEFINIR(nome, "CLASS"); ENTRAR_ESCOPO(); classe_atual ← nome
        para cada atributo: VALIDAR(atributo); atualizar tipo do atributo na classe
        para cada método: VALIDAR(método)
        restaurar classe_atual; SAIR_ESCOPO()
    FuncDecl:
        DEFINIR(nome, "FUNC", params); ENTRAR_ESCOPO(); função_atual ← nome
        para cada p em params: DEFINIR(p, "var")
        VALIDAR(corpo)                                    // abre o escopo "seq" do corpo
        restaurar função_atual; SAIR_ESCOPO()
    ReturnStmt:
        VALIDAR(valor); se em análise especializada: acumular tipo do retorno
    FuncCallExpr:
        se em tarefa e nome resolve algo que não é a func global: relatar(FJ-SEM-05)
        se nome ∉ funções e nome ∉ NATIVAS: relatar(SEM_UNDECLARED_FUNCTION)
        senão se nome ∈ funções e |args| ≠ |params|: relatar(SEM_ARITY)
        VALIDAR cada argumento
        se fj_ativo e a chamada envolve FJ: tipo ← VERIFICAR_FUNCAO(especializada nos argumentos)
        se nome ∈ {substr(string,number,number), to_string(number), len(coleção)}:
            aridade errada → SEM_ARITY; tipo conhecido errado → SEM_TYPE_MISMATCH
    MethodCall:
        VALIDAR(objeto) e argumentos; tipo ← INFERIR(objeto)
        se tipo é classe e método ∉ cadeia de herança: relatar(SEM_UNDECLARED_METHOD)
        senão se |args| ≠ |params do método|: relatar(SEM_ARITY)
        se lista.append/push_back com string: relatar(SEM_UNSUPPORTED_FEATURE)
        se fj_ativo: atualizar tipos estruturais (append, pop, size);
                     em tarefa, método de tipo desconhecido → FJ-SEM-05
    PropertyAccess, PropertyAssign:
        se objeto é classe e atributo ∉ cadeia de herança: relatar(SEM_UNDECLARED_ATTRIBUTE)
        PropertyAssign com tipo incompatível: relatar(SEM_TYPE_MISMATCH)
    NewExpr:
        se classe ∉ classes: relatar(SEM_UNDECLARED_CLASS)
        se em tarefa: verificar inicializadores de toda a cadeia de herança isolados
    ListLiteral:   elemento string → relatar(SEM_UNSUPPORTED_FEATURE)   // C-T11-v1 §3.4
    IndexExpr:     objeto string   → relatar(SEM_UNSUPPORTED_FEATURE)   // usar substr
    IndexAssign:   VALIDAR(alvo, valor); se fj_ativo: estender tipo da coleção
    ThisExpr:      em tarefa global → relatar(FJ-SEM-05)
    InputExpr, SendStmt, CChannelExpr, ReceiveExpr:
        em tarefa → relatar(FJ-SEM-05); VALIDAR os filhos
    ForkExpr:      VALIDAR_FORK(nó); se não valor_exigido: relatar(FJ-SEM-07)
    JoinExpr:      VALIDAR_JOIN(nó, valor_exigido)
    pilha_nós.desempilhar()
```

`valor_exigido = falso` marca a posição de **comando** (filhos de blocos, ramos de
`if`, corpos de laço, partes de `for`); nessas posições um `fork` descarta o handle
(FJ-SEM-07) e um `join` de resultado `none` é permitido.

---

## 5. Regras de Fork/Join [`_validate_fork`, `_validate_join`, `_check_function`, `_check_transport`, `_check_global_access`]

```text
procedimento VALIDAR_FORK(nó):
    VALIDAR cada argumento; VALIDAR(nó.destino)
    se destino e tipo(destino) ∉ {string, var, unknown}: relatar(FJ-SEM-04)
    f ← funções_globais[nó.nome]; s ← BUSCAR(nó.nome)
    se f = nulo ou s sombreia a global: relatar(FJ-SEM-01); retornar
    se s ≠ nulo e s.tipo ≠ "FUNC":      relatar(FJ-SEM-01); retornar
    se |args| ≠ |f.params|:             relatar(FJ-SEM-02 / SEM_ARITY); retornar
    tipos_args ← tipo estrutural de cada argumento (resolvendo chamadas)
    para cada t em tipos_args: VERIFICAR_TRANSPORTE(t, "argumento")
    resultado ← VERIFICAR_FUNCAO(f, tipos_args, isolada=verdadeiro)
    VERIFICAR_TRANSPORTE(resultado, "retorno")
    tipo(nó) ← task(resultado)
    registrar assinatura (tipos_args, resultado) em fork_signatures
        (ou em assinaturas provisórias, se analisada fora de contexto concreto)

procedimento VALIDAR_JOIN(nó, valor_exigido):
    VALIDAR(handle); VALIDAR(timeout)
    h ← tipo estrutural do handle
    se h não é task:
        se h ∈ {var, unknown}:
            para cada alternativa conhecida não-task em h.elementos: relatar(FJ-SEM-03)
            anotar em unresolved_fj ("join generico depende do tipo do argumento")
        senão relatar(FJ-SEM-03)
    se timeout e tipo(timeout) ∉ {number, int, var, unknown}: relatar(FJ-SEM-04)
    tipo(nó) ← h.resultado (ou unknown)
    se valor_exigido e h.resultado = void: relatar(FJ-SEM-08)

procedimento VERIFICAR_TRANSPORTE(t, papel):
    se t ∈ {unknown, var}: verificar alternativas; anotar "tipo nao comprovado" em unresolved_fj
    senão se t ∈ {list, matrix}: verificar cada tipo de elemento
    senão se t ∉ {number, int, bool, string, void}: relatar(FJ-SEM-06)   // objeto, canal, task

procedimento VERIFICAR_GLOBAL_NA_TAREFA(nome):
    se não isolada: retornar
    encontrar o escopo mais interno que define nome
    se é o global e o símbolo não é FUNC nem CLASS: relatar(FJ-SEM-05)

função VERIFICAR_FUNCAO(f, tipos_args, isolada, dono=nulo):          // especialização
    chave ← (f, tipos_args, isolada, dono, tipos globais, provisória)
    se chave ∈ cache: retornar cache[chave]
    se (f, isolada, dono) já em análise:          // recursão
        anotar "retorno recursivo nao comprovado" em unresolved_fj; retornar unknown
    salvar estado; especializado ← verdadeiro
    pilha_escopos ← [cópia dos globais]           // nunca herda locais do chamador
    se dono: abrir escopo com atributos da cadeia de herança do dono
    abrir escopo; DEFINIR cada parâmetro com o tipo do argumento
    VALIDAR(f.corpo, falso)                       // só erros "FJ-" são relatados aqui
    resultado ← união dos tipos de return, ou void se não houver return
    cache[chave] ← resultado; restaurar estado
    retornar resultado
```

A isolação é **transitiva**: `VERIFICAR_FUNCAO` revalida o corpo de cada função,
método e inicializador alcançado a partir da tarefa, com `isolada = verdadeiro`,
então um acesso a global mutável em `k()` chamado por `f()` é relatado quando
`fork f()` é analisado (sonda FJ-09).

### 5.1 Tradução de Fork/Join para TAC [`TACGenerator`]

```text
EXPR(ForkExpr f(a1..an) on d):
    para cada ai: ti ← novo_temp; emitir "ti = capture <EXPR(ai)>"     // cópia por valor
    dest ← "\"local\"" se d = nulo senão salvar(EXPR(d))
    retornar salvar("fork f(t1, …, tn) on dest")

JOIN(JoinExpr h, timeout t, valor_exigido):
    hv ← EXPR(h); se t: hv ← salvar(hv)                // t pode alterar a variável de h
    instr ← "join hv" + (", timeout " + EXPR(t) se t)
    se valor_exigido: retornar salvar(instr)  senão emitir instr

COMANDO(ForkExpr) → recusa TAC_UNSUPPORTED_FEATURE ("fork descartado; requer handle (FJ-SEM-07)")

COMANDO(ParBlock com n comandos):
    R ← rótulo PAR; W ← rótulo PAR_WAIT; Bi ← rótulo PAR_BRANCH por comando
    emitir "par_begin R, n"; para cada i: emitir "par_spawn R, i, Bi"
    emitir "goto W"
    para cada i: emitir "Bi:"; "par_branch R, i"
                 traduzir comando i com pilhas de break/continue vazias
                 (return vira "par_return R, i[, value v]")
                 emitir "par_end_branch R, i"
    emitir "W:"; "par_barrier R"; "par_end R"
```

A notação completa e os limites estão em `docs/auditorias/CORE-06_TAC_FORK_JOIN.md`.
A tradução para C++ (prova de tipos concretos em `CppTaskContext`, wrappers
`__fj_wrap_<f>` registrados com `minipar_rt::register_function` antes de
`worker_main_if_requested`, `start`/`join` do runtime) está em
`docs/auditorias/CORE-07_BACKEND_RUNTIME.md` e na seção 5.3 da BNF.

---

## 6. Limites conhecidos (registrados, não corrigidos por este card)

| Limite | Onde está documentado |
|---|---|
| Retorno por caminho implícito (`if (x > 0) { return 1; }` sem `return` final) é inferido como `number` no semântico; o backend C++ recusa o programa | `docs/CR-CORE05-FJ-DECISOES.md` (PEND-FJ-07) |
| Inferência de listas é conservadora: não modela posições, não remove tipos após `pop`; listas heterogêneas viram `unknown` | `BNF-grammar.md` seção 10; handoff CORE-04/05 |
| `unknown`/`var` em Fork/Join não geram erro, só nota em `unresolved_fj`; ausência de erro não prova execução | C-FJ-v1 §2.2.5 |
| Listas de strings e indexação de strings rejeitadas temporariamente | C-T11-v1 §3.4 |
| Parser sem recuperação: só o primeiro erro sintático é relatado | Este documento, seção 2.1 |
