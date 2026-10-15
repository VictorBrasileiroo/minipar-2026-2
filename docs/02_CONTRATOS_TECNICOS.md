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
