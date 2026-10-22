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
| CT-01 | Sintaxe definitiva Fork/Join na BNF 2026.2 | A+C | 18/10 |
| CT-02 | API runtime C++ final e registry de workers | A+C | 18/10 |
| CT-03 | Estrutura JSON e API da Web | A+B | 18/10 |
| CT-04 | Primitivas para strings/coleções Teste 11 — proposta em C-T11-v1 §3.3–3.5 (revisão 2, 22/10), aguardando A | A+B | 18/10 |
| CT-05 | Modelo de deploy dos workers entre hosts | C+A | 18/10 |
| CT-06 | CPUlator e escrita `.arm` — proposta em C-T11-v1 §3.6–3.7, alinhada à referência do professor; escrita direta desnecessária (PEND-T11-02 resolvida em 22/10) | B+A | 19/10 |
| CT-07 | Saída gráfica do T10 | C | 20/10 |

**Não iniciar implementação ampla sem estes contratos.** Provas isoladas reversíveis são permitidas para reduzir risco.
