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

**Fornecedor:** A. **Consumidor:** B (Web didática). **Prazo aprovação:** 18/10.  
**Objetivo:** permitir implementar a UI isoladamente com fixtures reais de contrato.

### 1.1 Modelo de dados (ilustrativo a revisar)

```json
{
  "contract": "compile.v1",
  "request_id": "id-da-requisicao",
  "ok": true,
  "source_hash": "sha256-do-codigo",
  "phases": {
    "lexer": {"status":"ok","tokens":[{"type":"NUMBER","lexeme":"42","line":1,"column":1}]},
    "parser": {"status":"ok","ast":{"id":"n0","kind":"Program","label":"Program","children":[]}},
    "semantic": {"status":"ok","symbols":[{"name":"x","type":"int","scope":"global"}]},
    "tac": {"status":"ok","text":"t1 = 2 + 4"},
    "cpp": {"status":"ok","text":"// código gerado"}
  },
  "diagnostics": [],
  "artifacts": {"cpp_id":null,"binary_id":null}
}
```

**Observações:** os valores acima são fictícios (fixture de forma). Tipos de token, símbolos e AST definitivos seguem a implementação e serão ajustados no G0. `source_hash` evita confundir resultados de compilações diferentes. `status`: `ok`, `error`, `skipped`. Campos opcionais têm contrato explícito; não devolver listas indefinidas como `null` sem razão.

**Diagnóstico v1:**

```json
{"phase":"semantic","severity":"error","code":"UNDECLARED_SYMBOL",
 "message":"Identificador não declarado","line":5,"column":3}
```

**AST visual:** árvore serializada `id,kind,label,children[]`, sem referências cíclicas; cada nó corresponde à AST real. Informações específicas em `attributes` de tipos simples, se necessárias. Limite de profundidade/tamanho explícito, com fallback para árvore grande.

### 1.2 Interface de serviço sugerida

Em Python: `analyze(source: str) -> AnalysisResult`; `compile(source: str, target: str="native") -> CompilationResult`; `execute(artifact_id: str, stdin: str="", timeout_sec: int=30) -> ExecutionResult`.

O serviço pode expor rotas REST em `web_didatica/server.py`, usando **chamadas da biblioteca Python do compilador**, sem implementar Lexer/Parser próprio. Nomes finais de funções e rotas ficam congelados no G0.

**Contrato de execução:**
- `compile` só retorna `ok=true` quando G++ produziu binário da compilação atual (verificar returncode).
- `execute` devolve `stdout`, `stderr`, `exit_code`, `timed_out`, `duration_ms`.
- `download` devolve **o binário correto associado ao request_id**; não reutilizar artefato velho.
- Erro em fase anterior marca fases posteriores como `skipped`.
- Programas gerados executam em processo controlado com timeout; interface acadêmica local, não expor publicamente sem isolamento.

### 1.3 Handoff e testes

A entrega de A deve incluir um fixture JSON validado pela produção com: programa simples, erro léxico, erro sintático, erro semântico e um teste maior. B adapta a visualização apenas após confirmar a forma de dados. Se Web precisar de novos campos, B abre CR, não edita `src/semantic.py`.

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

**Estado:** `v1 — PROPOSTA DE CONGELAMENTO` redigida pelo B em 19/10/2026 no card `CON-03`. Passa a `v1 FROZEN` quando A aprovar o PR (quadro em 3.10). Até lá, nenhum lado trata as sintaxes abaixo como definitivas.

**Fornecedor de primitivas:** A (`CORE-03`). **Consumidor de linguagem:** B (`T11-01`, `T11-02`, `T11-03`). **Prazo:** contrato e primitivas no Marco 1 (22/10); `.arm` validado no CPUlator no Marco 2 (29/10).

### 3.1 Escopo da aplicação

MiniCompilador implementado **na linguagem MiniPar**, com tokenização, análise com precedência, AST, TAC, tabela de símbolos, avaliação e texto Assembly ARMv7, todos produzidos por lógica MiniPar. O compilador hospedeiro só compila e executa esse programa.

**Entrada:** uma expressão por execução, lida com `input()` (uma linha do stdin). Os três casos obrigatórios são três execuções do mesmo binário:

| Caso | Entrada (stdin) | Resultado |
|---|---|---:|
| 1 | `((2+4)*7)-(5*4)` | 22 |
| 2 | `((10 -8*7)+4)*2` | -84 |
| 3 | `((2+4)*7)-(5*4)` | 22 |

**Linguagem de expressões aceita na v1:**
- inteiros não negativos com um ou mais dígitos (`10`, `8`);
- operadores `+`, `-`, `*` com precedência usual (`*` antes de `+`/`-`) e associatividade à esquerda;
- parênteses aninhados;
- espaços ignorados (o caso 2 contém espaço).

**Fora da v1, com mensagem de erro explícita, nunca resultado silencioso:** menos unário, números decimais, variáveis e caracteres desconhecidos. A divisão `/` é decisão interna do B no `T11-02`: ou é suportada também no ARM (por rotina de divisão, já que a referência Java não gera ARM funcional para divisão), ou é rejeitada com erro. Não afeta o contrato com A.

**Saída do programa, nesta ordem:** tokens, AST, tabela de símbolos, TAC, resultado da avaliação e o bloco ARM delimitado (3.6). O formato exato dos quatro primeiros segue a referência Java (pendência PEND-T11-01).

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

Status desta tabela vale só para o commit indicado. Ela não substitui a baseline T01–T07 do `CORE-01`.

### 3.3 Primitivas obrigatórias (P0) — fornecidas por A no `CORE-03`

| ID | Primitiva | Sintaxe congelada | Semântica exigida |
|---|---|---|---|
| PRIM-01 | string com armazenamento real | `var s = "abc";` · `string s = "abc";` · `var s = "";` | toda variável inicializada com literal string é uma string de verdade (no C++, `std::string`), aceitando `len`, `substr`, `+` e reatribuição |
| PRIM-02 | comprimento | `len(s)` | número de caracteres de qualquer string: literal, lida, concatenada ou vinda de `substr`/`to_string` |
| PRIM-03 | recorte | `substr(s, inicio, tamanho)` | string com `tamanho` caracteres a partir de `inicio` (base 0). `inicio` e `tamanho` aceitam qualquer número de valor inteiro, inclusive vindo de lista numérica (`double`). Índice fora dos limites: erro de execução com mensagem e código de saída ≠ 0, nunca comportamento indefinido |
| PRIM-04 | número → texto | `to_string(x)` | valor inteiro sai sem casas decimais e com `-` quando negativo (`42` → `"42"`, `0 - 84` → `"-84"`), **inclusive** quando o valor vem de `to_number` ou de lista numérica (`-46.0` → `"-46"`). Valores não inteiros não são usados pelo T11; formato livre, desde que documentado |
| PRIM-05 | concatenação | `a + b` | funciona em todas as combinações: variável + literal, literal + variável, literal + `to_string(...)`, variável + variável, e acumulação `acc = acc + c` dentro de laço |
| PRIM-06 | comparação | `==` `!=` `<` `<=` `>` `>=` | entre strings, com ordem lexicográfica (permite `c >= "0" && c <= "9"`). Já funciona, e entra no contrato para não regredir |

**Já disponíveis e cobertos por regressão** (A não deve quebrar): `input()`, `to_number`, `print` com vários argumentos, `"\n"` em literal, listas numéricas (`append`, `pop`, índice, atribuição por índice, `len`), função que retorna lista, classe com atributo lista alterado por método, recursão, `while`/`for`/`if`, funções com parâmetro e retorno string.

B **não** altera `src/` para viabilizar o algoritmo. Se faltar algo fora desta lista, B abre card para A com programa MiniPar reprodutível de 10–30 linhas.

### 3.4 Fora do contrato v1 (B não usará)

| Recurso | Motivo | Como o B contorna |
|---|---|---|
| acesso por índice em string (`s[i]`) | produziria `char`, e a comparação com literal exigiria outro tipo na linguagem | `substr(s, i, 1)` |
| listas de strings | hoje falham, uma delas em silêncio; corrigir exige inferir o tipo do elemento | tokens em listas numéricas paralelas (tipo, valor, posição); o lexema sai de `substr` na expressão original |
| variáveis globais dentro de funções | globais são emitidas dentro de `main` | estado em objetos de classe (atributos lista) ou passado e retornado por parâmetro |
| passagem de lista por referência | parâmetros são cópias | método de classe ou função que retorna a lista nova |
| escrita de arquivo pelo programa MiniPar | ver PEND-T11-02 | exportação pelo executor (3.6) |

**Defeito registrado para A, fora do escopo do `CORE-03`:** `var l = ["a", "b"]; print(l[1]);` compila e imprime `0`. É resultado falso sem erro. Recomendação: rejeitar no semântico ou corrigir em card próprio. O T11 não depende disso.

### 3.5 Programas de prova com oráculo (aceite do `CORE-03`)

Cada programa abaixo precisa **compilar e executar pelo pipeline real**, sem alteração, com stdout idêntico ao oráculo (sem espaço no fim da linha) e código de saída 0. Em 19/10/2026 os seis passam no Lexer/Parser atual. PROVA-01 falha no g++. As demais param no semântico **apenas** por `substr`/`to_string` não declaradas.

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

**Regra anti-hardcode:** A não pode reconhecer estes programas por nome, conteúdo ou entrada (como o `EXPECTED_QUICKSORT_TAC` do T07). O B pode trocar as entradas na revisão, por exemplo `(7+8)*3` na PROVA-02, e o resultado precisa continuar correto.

### 3.6 Fronteira do `.arm`

1. **Quem gera:** o programa MiniPar imprime o Assembly no stdout, uma instrução por linha, entre duas linhas marcadoras exatas:

   ```text
   ===MINIPAR_ARM_BEGIN===
   ... assembly ...
   ===MINIPAR_ARM_END===
   ```

2. **Quem salva:** um script do B em `tests/2026_2/test11/` (e, no M2, o download da Web didática pelo `WEB-04`) copia **literalmente** as linhas entre os marcadores para `caso1.arm`, `caso2.arm`, `caso3.arm`, em UTF-8 com quebra `\n`. O script não pode reescrever, completar nem analisar o Assembly: nada de Lexer, AST, TAC ou ARM em Python. Faltar um marcador, ou haver mais de um bloco, é erro.
3. **Convenções do Assembly** (sintaxe GNU `as`, aceita pelo CPUlator):
   - começa com `.global _start` e `_start:`;
   - constantes carregadas com `LDR Rn, =valor`, que aceita qualquer inteiro de 32 bits, inclusive negativos, sem o limite de `MOV` imediato da referência Java;
   - usa apenas `R0`–`R12`;
   - o **resultado final fica em `R0`**;
   - termina em laço `_fim: B _fim`, para o resultado ser inspecionado com o programa parado.
4. **Escrita direta pelo MiniPar:** fora da v1. Se o professor exigir (PEND-T11-02), abrir CR para uma builtin de arquivo no A.

### 3.7 Validação no CPUlator

- **Ambiente:** CPUlator, sistema "ARMv7 generic" (`https://cpulator.01xz.net/?sys=arm`).
- **Passos:** carregar o `.arm` no editor, *Compile and Load*, *Continue*, pausar quando o PC estiver em `_fim` e ler `R0`.
- **Oráculos:**

  | Arquivo | R0 decimal | R0 hexadecimal |
  |---|---:|---|
  | `caso1.arm` | 22 | `0x00000016` |
  | `caso2.arm` | -84 | `0xFFFFFFAC` |
  | `caso3.arm` | 22 | `0x00000016` |

- **Evidência guardada pelo B** em `tests/2026_2/test11/evidencias/`: captura da tela com o editor e os registradores, data, sistema do CPUlator, SHA-256 de cada `.arm` e o stdout completo da execução MiniPar que o gerou. Assembly impresso sem execução no CPUlator conta no máximo como `PARTIAL`.

### 3.8 Responsabilidades e handoff

**A comprova (`CORE-03`):**
- PRIM-01 a PRIM-06 implementadas no compilador hospedeiro;
- PROVA-01 a PROVA-05 e PROVA-INT em PASS pelo pipeline real, com comandos e saídas no handoff;
- os recursos de "já disponíveis" (3.3) continuam passando;
- regressão T01–T07 não piora em relação à baseline do `CORE-01`;
- nenhum reconhecimento por nome ou conteúdo de programa.

**B comprova (`T11-01` → `T11-03`):**
- tokenização, parser com precedência, AST, TAC, tabela de símbolos e ARM são lógica MiniPar, gerada dinamicamente a partir da entrada;
- os três casos dão 22, -84 e 22, e ao menos três entradas extras também (variação de parênteses e de operador);
- entradas inválidas são rejeitadas com mensagem (caractere desconhecido, parênteses desbalanceados, entrada vazia);
- três `.arm` executados no CPUlator com os oráculos de 3.7;
- tabela de símbolos fiel à referência Java no escopo aceito (depende de PEND-T11-01).

**Processo:** se B precisar de uma primitiva nova, abre card para A com programa de 10–30 linhas. B não mergeia patch em `src/`. Mudança de sintaxe ou semântica de PRIM-01 a PRIM-06 depois do congelamento exige CR (seção 4).

### 3.9 Pendências registradas

| ID | Pendência | Dono | Impacto se não resolver |
|---|---|---|---|
| PEND-T11-01 | Código Java e exemplos de execução do professor não estão no repositório (`docs/fontes/README.md`). Sem eles, o formato exato de tokens, AST e tabela de símbolos não pode ser conferido. Proposta provisória para a tabela: nome do temporário, valor e registrador ARM | Trio (anexar em `docs/fontes/`) | `T11-02` só fecha a tabela de símbolos depois disso |
| PEND-T11-02 | Confirmar com o professor se a exportação do `.arm` pelo executor atende, ou se o programa MiniPar deve gravar o arquivo (P08 / ADR-012) | Coordenador | Se exigir escrita direta: CR e builtin de arquivo no A |
| PEND-T11-03 | Lista literal de strings retorna valor falso sem erro (3.4) | A | Risco para outros testes; não bloqueia o T11 |

### 3.10 Aprovação

| Parte | Responsável | Decisão | Data |
|---|---|---|---|
| B — consumidor | José Riquelme | Proposta apresentada | 19/10/2026 |
| A — fornecedor | Coordenador | *pendente* | |

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
| CT-04 | Primitivas para strings/coleções Teste 11 — proposta em C-T11-v1 §3.3–3.5, aguardando A | A+B | 18/10 |
| CT-05 | Modelo de deploy dos workers entre hosts | C+A | 18/10 |
| CT-06 | CPUlator e escrita `.arm` — proposta em C-T11-v1 §3.6–3.7; escrita direta pendente (PEND-T11-02) | B+A | 19/10 |
| CT-07 | Saída gráfica do T10 | C | 20/10 |

**Não iniciar implementação ampla sem estes contratos.** Provas isoladas reversíveis são permitidas para reduzir risco.
