# CORE-09 — regressão do terminal e da Web original

**Responsável:** Eixo A/coordenador, assistido por Codex. **Data:** 05/11/2026.
**Status técnico:** PASS nos fluxos essenciais executados; smoke visual BLOCKED.
Não equivale a DONE, revisão humana, CORE-10 ou INT-02.

## Preparação e autorização

Lidos AGENTS, MEMORY, documentos 00/01/02/04/05, card em `planning/cards.json`,
auditorias CORE-07/08 e smoke anterior, documentação de setup, README e template
de handoff. Árvore inicialmente limpa na branch CORE-07, HEAD `257613f`.
Fetch realizado; `dev` atualizada por fast-forward até
`59ea77d093deb35877243da3383bcd7036e16448`; branch criada diretamente dela:
`eixo-a/CORE-09-regressao-interfaces`.

CORE-07 está integrado via PR #18 (`b6e2705`) e ajustes #29. CORE-08 está presente
em dev, inclusive catálogo integrado via #34. CORE-09 ainda tem `ready=false`
nos metadados: a coordenação autorizou explicitamente sua execução neste pedido
após conferir dependências. Isso não promove outros cards nem aprova contratos.
Backlogs e contratos permaneceram intactos.

Git exigiu execução autorizada para escrever `.git`; usada exceção
`safe.directory` por comando, sem configuração global. Nenhum trabalho local
alheio foi removido, nenhuma dependência instalada e nenhum PATH de sistema
alterado. Somente servidores de teste em loopback, encerrados após uso.

## Ambiente, identidade da revisão e evidências

Windows 11 `10.0.26200`, Python venv 3.12.4 e G++ MSYS2 UCRT64 16.2.0.
Compilação real: C++20, `-O3`, `-pthread`, include do runtime e `-lws2_32`.
Base testada: commit acima com as alterações desta branch. Os SHA-256 dos quatro
arquivos de produção e dos scripts testados estão no
[registro estruturado](CORE-09_RESULTADOS.json); isso identifica a revisão local
sem atribuir os resultados à dev sem estas correções.

Logs locais: `output/core09-final-verified.log`, `core09-before.log`,
`core09-before-detail.log`, `core09-probes-final.log`, `core09-http.log`,
`core09-core02.log`, `core09-core06.log`, `core09-core07.log`,
`core09-service.log`, `core09-baseline.log` e `core09-legacy-smoke.log`.
Detalhes de fontes, entradas, respostas, hashes de TAC/C++ e stdout de execução
foram selecionados no JSON versionado. Binários temporários dos testes próprios
são removidos; os testes os recompilam. Não se gerou nada em `legacy/`.

## Defeitos reproduzidos e correções

| Caso | Antes / causa | Correção e prova |
|---|---|---|
| Sintaxe inválida no menu | Parser lança `SystemExit(1)` e encerra a interface; ERROR na primeira rodada | `compile_file` captura somente essa saída esperada e retorna False; seleção inválida, compilação válida, erro sintático e saída do menu testados |
| Artefatos antigos | Compilar `print(6 * 7);` e depois string não fechada com mesmo nome devolvia os antigos TAC/C++ | CLI invalida `.exe/.cpp/.tac` antes das fases; Web usa UUID interno; painéis JS são limpos antes da requisição e recebem texto vazio após erro |
| Erro nativo como sucesso | `substr("abc", 9, 1)` sai com 1 e stderr real, mas Web devolvia `success=true` | Retorno nativo não zero passa a falha com código, stdout e stderr no log; terminal também explicita returncode |
| Localização e Python | Em cwd isolado a Web procurava `main.py` ali e usava `python` do PATH | Caminho absoluto do compilador e `sys.executable`; PASS mesmo sem Python no PATH, usando G++ configurado |
| Colisão de requisições | Arquivos eram compartilhados pelo nome enviado | Duas compilações simultâneas com `same.minipar` executam 31415 e 27182, cada qual com TAC/C++ correspondentes |
| Timeout e saída parcial | O handler descartava stdout capturado na exceção | Programa real imprime `before timeout` e entra em laço; após 30 s a resposta preserva o texto e informa timeout |

As duas falhas de artefatos/sucesso foram reproduzidas também com snapshots de
`app.py` e `main.py` do commit-base, compilando de verdade com o núcleo integrado.
`probe_baseline.py` valida a presença dos defeitos antigos e registra
`FAIL reproduced`; não é teste de aprovação da implementação antiga.

O prazo externo da Web foi alinhado em 130 s ao compilador nativo limitado a
120 s; não se afirmou reproduzir uma compilação que excedesse o prazo antigo.
O sufixo `.exe` foi alinhado ao backend atual também em POSIX por inspeção;
a execução comprovada desta auditoria é Windows. Entradas Web inválidas retornam
400 em vez de exceção interna. Nenhuma fase foi simulada, nem houve alteração
de oráculos. A simulação de terminal se restringe às teclas do usuário.

## Matriz da execução inicial

| Prova / oráculo | Resultado |
|---|---|
| CORE-09: 13 testes reais, 0 falhas/erros | PASS |
| `main.py` sem argumentos, escolha 1, menu e saída 0 | PASS, processo real |
| Menu: opções inválidas, listagem, seleção, compilação, geração e execução | PASS, `6 * 7` imprime `42`; menu continua após erro sintático |
| Programa legado T07 pelo menu e pela Web | PASS, `Array ordenado: [5, 12, 33, 61, 98]`, TAC/C++ gerados do fonte |
| Fork/Join pela CLI oficial | PASS, dois handles 21/7, join em ordem inversa imprime `14 42`, exit 0 e stderr vazio |
| Flask test_client: HTML, JS, CSS, lista e carregamento de arquivos | PASS, 200 nos recursos existentes e 404 no ausente |
| Erros léxico, sintático e semântico após sucesso | PASS, falha com diagnóstico; TAC/C++ vazios e sem executar saída antiga |
| stdin, troca de fonte sob mesmo nome, artefatos correspondentes | PASS, eco `core09` e segunda compilação/execução `12345` |
| G++ inexistente | PASS negativo, `GPP_NOT_FOUND`, sem executar binário |
| JSON/nome inválidos | PASS negativo, 400 |
| Erro de execução real | PASS negativo, exit 1 no `substr`; `before failure` e stderr apresentados |
| Laço infinito e timeout real | PASS negativo, 30 s e stdout parcial preservado |
| Sessões originais: consultar, criar pelo analisador real, join, ready, clear | PASS via test_client e arquivo de sessão real isolado |
| `main.py` escolha 2 → Flask → HTTP real → compilador → binário | PASS, `print(42);` produz `42`, TAC/C++ presentes |
| Smoke visual em navegador | BLOCKED, `openBrowserPage` falhou e CUA retornou `The browser access host is unavailable` |
| CORE-02 TAC | PASS, 5 testes |
| CORE-06 | PASS, 54 testes |
| CORE-07 | PASS, 17 testes |
| CORE-08 serviço | PASS, 36 testes, zero falhas/erros no JSON do runner |
| Smoke anterior CLI/Web | PASS, `5` e negativo léxico |
| Baseline pertinente T02/T03/T05/T06/T07 | PASS, uma execução de cada; T07 inclui mutação TAC e assertions de índices |
| T04 | PARTIAL, XOR classificado corretamente; divergência numérica herdada sem tolerância acordada |

Os tracebacks `probe` no log CORE-08 são injetados deliberadamente pela suíte
existente; o resultado estruturado tem 36 sucessos. PowerShell também prefixa
stderr de unittest com `NativeCommandError`; o status foi conferido pelo resumo
real e pelo JSON, não pela aparência desse prefixo.

## Comparação com 2026.1

Referência imutável inspecionada: `legacy/minipar-2026.1/main.py`, `menu.py`,
`app.py`, template e JavaScript. Não se executou o compilador histórico dentro
de `legacy/`; a comparação foi de fluxos e comportamento observado na raiz ativa.

| Diferença | Classificação |
|---|---|
| Seleção terminal/Web, lista de testes, editor, TAC/C++, Compile & Run, stdout/erros e sessões mantidos | Comportamento essencial preservado |
| C++20/runtime Fork/Join, T07 com pilha corrigida e TAC derivado da AST | Evolução intencional dos cards já integrados |
| Parser derrubava menu; Web reutilizava artefatos e ignorava exit nativo | Defeitos herdados relevantes, corrigidos para preservar o comportamento esperado; não atribuídos falsamente à integração CORE-07/08 |
| Uso de Python do PATH e busca relativa do compilador | Limitação herdada corrigida |
| Sufixo POSIX esperado pelas interfaces divergia do `.exe` atual do backend | Incompatibilidade corrigida por alinhamento de caminho; POSIX não executado |
| Campos JSON e rotas da Web antiga | Preservados; nenhum endpoint ou contrato do serviço didático alterado |

## Reprodução

Executar da raiz com porta 5000 livre para o smoke HTTP:

```powershell
# Configure CXX com o executável C++20 local antes destes comandos.
$env:PATH=(Split-Path -Parent $env:CXX)+';'+$env:PATH
$env:PYTHONIOENCODING='utf-8'
.\.venv\Scripts\python.exe -B tests/2026_2/core09/probe_baseline.py 59ea77d
.\.venv\Scripts\python.exe -B tests/2026_2/core09/test_interfaces.py
.\.venv\Scripts\python.exe -B tests/2026_2/core09/smoke_http.py
.\.venv\Scripts\python.exe -B -m unittest discover -s tests -p test_core02_tac.py -v
.\.venv\Scripts\python.exe -B -m unittest discover -s tests/2026_2/core06 -v
.\.venv\Scripts\python.exe -B -m unittest discover -s tests/2026_2/core07 -v
.\.venv\Scripts\python.exe -B tests/2026_2/core08/verify_core08.py
.\.venv\Scripts\python.exe -B tests/2026_2/core08/smoke_legacy.py
.\.venv\Scripts\python.exe -B scripts/baseline_t01_t07.py --only T02,T03,T04,T05,T06,T07 --repeat 1
git diff --check
```

O coletor `record_results.py` seleciona os logs desta rodada e recusa PASS sem
os resumos esperados. Para outra rodada, ajustar nele o diretório datado da
baseline e capturar os comandos nos caminhos indicados acima; não confundir
evidências históricas com nova execução. A suíte CORE-09 pode ser rodada por
unittest discovery, mas a execução direta também grava o JSON de evidências.

## Limitações e encaminhamentos

- **BLOCKED visual:** conferir os editores CodeMirror, tabs e limpeza após erro
  no navegador humano antes do merge. O JS foi inspecionado; não se afirma que
  uma captura ou teste visual ocorreu. Dependências CDN originais preservadas.
- **PARTIAL plataforma:** Windows executado; POSIX somente inspecionado.
- **UNTESTED:** timeout externo de compilação de 130 s não foi forçado; o timeout
  de execução de 30 s foi executado de verdade.
- **Limitação herdada do núcleo:** a sondagem `var xs=[1]; print(xs[9]);` na
  versão integrada retornou `0`, exit 0. Não serve como oráculo de falha nativa.
  Encaminhar ao Eixo A/núcleo em card próprio; nenhum arquivo de `src/` alterado.
  O teste de falha usa `substr` inválido com saída 1 real e estável.
- **Limitação herdada de sessões:** fluxo saudável e APIs locais validados;
  participantes em múltiplos terminais/hosts e cancelamento após erro de
  compilação não foram homologados. Sessões locais não provam distribuição.
- **T04 PARTIAL** e intermitência histórica T02 permanecem com seus donos;
  T02 passou nesta rodada única. T01 não foi executado por abrir bind amplo;
  não se assume CORE-10/INT-02, rede física nem CPUlator.
- A Web original continua armazenando artefatos em disco e capturando saídas
  pelo fluxo herdado. Limpeza automática e limites de saída do serviço didático
  não foram transplantados para esta interface.

## Handoff e manutenção documental

Produção alterada: `main.py`, `menu.py`, `app.py`, `static/js/script.js`.
Adicionados quatro scripts em `tests/2026_2/core09/`, esta auditoria e o JSON
selecionado. README atualizado com comandos, ambiente, limites e artefatos.
Nenhuma alteração em `src/`, `runtime/`, Web didática, Teste 11, contratos ou
metadados de outros cards. Templates e CSS foram verificados e dispensam edição:
não mudaram layout, controles ou recursos.

Documentos 00/01/02/04/05, setup, pseudocódigos do núcleo e handoffs anteriores
foram verificados: não precisam mudar, pois contratos, fases e arquitetura
permanecem. A CLI como processo continua saindo com código 1 em erro sintático;
somente o menu passa a receber False. **AGENTS.md e MEMORY.md revisados, sem
alterações necessárias:** não mudaram ownership, convenções, arquitetura,
padrões ou fluxo de desenvolvimento. A autorização específica consta aqui.

Próximo consumidor: revisor independente do Eixo A e usuário das interfaces;
coordenação acompanha as limitações de núcleo/QA. PR único contra `dev`, sem
merge automático. Exigir revisão humana de diff, logs, demonstração visual e
ao menos uma aprovação de pessoa diferente do autor antes de integrar.

## Ajustes finais do PR #35 — 05/11/2026

Pedido da coordenação: correção delimitada de nomes de arquivo, anonimização das
evidências, nova tentativa visual e regressão CORE-09. Branch mantida em
`eixo-a/CORE-09-regressao-interfaces`, inicialmente limpa no commit `01e6976`.
Nenhuma alteração de contrato, outro card, runtime, núcleo ou Web didática.

### Segurança e compatibilidade

`/api/get_test` e `/api/session/create` combinavam o nome recebido diretamente
com o diretório, permitindo acesso externo. `/api/test_spec` reduzia nomes com
`basename` internamente, mas ainda aceitava caminhos indevidos e falhava para
tipos inválidos. Os três agora validam o JSON e exigem um basename `.minipar`,
sem `/`, `\`, `:`, caracteres de controle ou caminho externo após `realpath`.
Requisições inválidas recebem 400 sem conteúdo de arquivos nem criação de sessão.
Arquivo legítimo, arquivo ausente e sessões saudáveis mantêm o comportamento
anterior. Symlink que resolva fora do diretório também é recusado pela validação
de contenção; esse caso específico não foi executado nesta rodada.

O teste negativo foi executado antes da correção e registrou FAIL (59 subcasos
divergentes). Depois da correção, a suíte completa executou **14 testes PASS,
zero falhas e zero erros**, incluindo 69 requisições negativas nos três endpoints,
leitura e especificação legítimas, criação/join/ready/clear de sessão, compilação
e execução reais, concorrência e timeout. Log local:
`output/core09-review-tests.log`; falhas anteriores:
`output/core09-security-before.log`.

```powershell
# Com CXX e PATH configurados localmente conforme a seção Reprodução.
.\.venv\Scripts\python.exe -B -m unittest discover -s tests/2026_2/core09 -p test_interfaces.py -k unsafe_filenames -v
.\.venv\Scripts\python.exe -B tests/2026_2/core09/test_interfaces.py
.\.venv\Scripts\python.exe -B tests/2026_2/core09/record_results.py
git diff --check
```

### Privacidade e evidência

O JSON selecionado foi regenerado com as 14 verificações atuais. O coletor
anonimiza também as evidências históricas retidas: `<REPO>` substitui a raiz
local, `<TOOLCHAIN>` a pasta do compilador e `<LOCAL>/<basename>` outros caminhos
locais em diagnósticos. Fontes, entradas, resultados, oráculos, flags e hashes
permanecem. Não foram modificados logs brutos locais ignorados nem o histórico
Git. Os exemplos desta auditoria e a seção CORE-09 do README não fixam caminhos
absolutos de uma instalação. Os resultados anteriores de CORE-02/06/07/08,
baseline e HTTP são históricos, **não reexecutados neste ajuste**; isso também
está explícito no JSON.

Verificação local da anonimização: PASS, sem caminhos absolutos ou identificação
pessoal nas evidências selecionadas e nos exemplos CORE-09; comparação com o
JSON bruto confirmou preservação dos registros de teste, fontes, entradas,
oráculos, hashes dos artefatos e flags C++20. `git diff --check`: PASS.

Nova tentativa visual: `readPage`/`openBrowserPage` falharam e CUA retornou
`The browser access host is unavailable`. **BLOCKED permanece** para compilação
válida, erro e limpeza dos painéis em navegador. Os testes backend correspondentes
passaram; não substituem validação visual humana.

### Revisão documental e entrega

Auditoria, JSON e instrução de nomes válidos no README atualizados. Verificados
AGENTS/MEMORY e documentos 01/02/04/05; **AGENTS.md não precisa mudar**, pois este
ajuste não altera ownership, arquitetura, convenções ou fluxo. MEMORY e os
demais documentos normativos também dispensam alteração por esse motivo.
Contratos e estados dos cards permanecem intactos.

Próximo consumidor: revisor independente do PR #35. Permanecem as pendências
humanas visuais e de aprovação antes do merge; as limitações históricas acima
não foram promovidas a PASS nem assumidas por esta revisão. Atualizar somente
o PR existente por commit/push, sem novo PR ou merge.
