# HANDOFF — CORE-08: serviço de fases para a Web didática

**Estado: PARTIAL, implementação local para revisão independente.** Responsável A/coordenador. Data: 30/10/2026. Contrato: C-WEB-v1 §1, sem mudança de envelope ou aprovação inferida. Sem stage, commit, push, PR ou merge.

## Autorização, base e dependências

O pedido anexado do coordenador autoriza diretamente CORE-08, incluindo ajustes delimitados em Lexer/Parser/semântico/TAC/backend, testes e documentação. Proíbe incorporar outros PRs, editar Web didática/runtime/Teste 11/legacy e marcar DONE/FROZEN. Essa autorização específica foi registrada apenas no card CORE-08; `ready=false`, dependências e aprovações anteriores foram preservados.

- Branch inicial: `eixo-a/CORE-07-backend-runtime`, HEAD `d7b52d5` (SHA completo no JSON de resultados). Workspace inicialmente limpo; nenhum trabalho local alheio foi removido. A branch CORE-07 permanece intacta.
- `git fetch origin` executado. Branch criada: `eixo-a/CORE-08-servico-fases`, diretamente de `origin/dev`, SHA `29cff941e4e4a2b7f37b08bf3fc0d24e98c40ce1`. Não foi necessário modificar a branch local `dev`.
- Base contém CORE-02 (#16), CORE-03 (#14), CORE-04/05 (#15). Consulta atual do conector GitHub encontrou #17/CORE-06 e #18/CORE-07 abertos; nenhum foi incorporado. Sua ausência também foi conferida no histórico de `origin/dev`.
- Git precisou de `-c safe.directory=<workspace>` por diferença de proprietário do sandbox. Fetch e criação da branch exigiram execução fora do sandbox para escrever `.git`, autorizadas pelo pedido. Nenhuma configuração global foi alterada.

## Implementado e arquivos

| Arquivo/ponto | Mudança |
|---|---|
| `src/service.py:73` | Pipeline de seis fases, UUID4, SHA-256 do UTF-8 exato, interrupção na primeira falha, envelopes JSON, diretórios próprios |
| `src/service.py:155` | `analyze(source)`, sem subprocesso e sem artefatos registrados |
| `src/service.py:159` | `compile_program(source)`, tradução e G++ reais, registro condicionado à existência do artefato |
| `src/service.py:163` | `get_artifact(id,kind)`, validação antes do acesso, caminhos explícitos, nomes e media types contratuais |
| `src/service.py:180` | `execute(id,stdin="",timeout_sec=10)`, somente binário registrado daquele ID |
| `src/service_ast.py:34` | Serialização iterativa: tipos declarados, labels, pré-ordem, atributos/filhos, limites 5000/200 e marcadores |
| `src/service_process.py:48` | Drenagem simultânea com buffers limitados, escrita de stdin em thread e posse da árvore de processos |
| `src/lexer.py:111` | Diagnósticos reais, distinção UNKNOWN/string sem fechamento e proteção de escape incompleto |
| `src/parser.py:27` | `ParseError`, diagnósticos, opção aditiva `exit_on_error=False`; padrão da CLI continua encerrando com código 1 |
| `src/semantic.py:50` | Opção aditiva `emit_diagnostics=False`, códigos nos pontos de detecção, registro de escopos/símbolos antes do descarte |
| `src/codegen.py:267` | `generate_text(program)` sem escrita/compilação; `compile_cpp` compartilhado com `generate` antigo |
| `src/tac.py` | Apenas import relativo condicional para suportar `from src.service import ...`; gerador e guarda FJ preservados |
| `main.py:37` | CLI imprime diagnóstico léxico estruturado e retorna falha antes do parser; sem traceback para escape incompleto |
| `tests/2026_2/core08/` | Suíte de contrato/integração, runner com relatório e smoke das interfaces antigas |

Imports relativos condicionais nos módulos auxiliares preservam a importação antiga com `src` no `sys.path` e permitem o consumo por pacote, sem alterar `sys.path` dentro do serviço. Os chamadores antigos mantêm suas assinaturas. Não há captura global de stdout/stderr, regex sobre mensagens, alteração global de ambiente nem `os.chdir` na biblioteca. AST→TAC e AST→C++ continuam independentes. Não há TAC hardcoded nem warning indevido.

## Decisões verificáveis

- Diagnósticos cobertos vêm diretamente da fase. Semântico acumula erros e publica ordem por linha; redeclaração não cria segundo símbolo. Especializações de tarefas não entram na tabela de apresentação.
- Catálogo incompleto: recusas FJ/recursos ausentes não são falsamente `INTERNAL_ERROR`. A fase retorna erro; os itens sem código aprovado ficam fora de `diagnostics`. **Isso pode produzir `diagnostics=[]` numa fase com erro.** O consumidor deve mostrar o erro da fase e restringir a homologação aos programas suportados. A atribuição de códigos e o tipo `task` aguardam [CR mínima](../CR-CORE08-DIAGNOSTICOS.md). Não há aprovação ou versão nova aplicada.
- Registro protegido por `RLock`, com nomes fixos e diretórios UUID exclusivos. Sem limpeza automática: todas as compilações registradas permanecem disponíveis enquanto o processo vive, atendendo às 20 mais recentes sem corrida com operações ativas. Reiniciar o processo perde o registro, mesmo com arquivos no disco. Não há persistência entre workers/processos.
- Não há fallback para “último executável”. `binary_id` só é registrado após G++ exit 0 e arquivo regular, não redirecionado e não vazio. C++/TAC continuam acessíveis após falha de G++.
- São rejeitados IDs/kinds inválidos antes do filesystem; registro fechado de arquivos, diretório gerenciado e caminhos resolvidos impedem traversal/redirecionamento. A área de artefatos deve permanecer sob controle do processo hospedeiro; isto não é sandbox de programas arbitrários.
- G++ usa subprocesso com cwd explícito, timeout 120 s e retenção de até 64 KiB por stream. Execução retém até 1 MiB por stream enquanto drena o excedente; não captura tudo para só então truncar. UTF-8 inválido é substituído, CRLF nativo vira LF.
- Windows: processo suspenso antes de atribuição a Job Object próprio com `KILL_ON_JOB_CLOSE`; só depois é retomado. Timeout e término normal fecham a árvore própria, inclusive descendentes. POSIX usa nova sessão e `killpg` do grupo próprio. O ramo Windows foi executado; POSIX permanece UNTESTED nesta máquina.
- Ambiente do compilador/executor é uma cópia por subprocesso; o diretório da toolchain selecionada entra apenas nesse ambiente para resolver DLLs MinGW. Nenhum PATH persistente ou `os.environ` global foi alterado pela biblioteca.

## Comandos executados e resultados da rodada inicial (hist?rico)

Shell PowerShell, Python 3.12.4 da venv, Windows 11, G++ UCRT64 16.2.0. Nas chamadas de validação, estas variáveis foram definidas apenas no processo do comando:

```powershell
$env:CXX='C:\msys64\ucrt64\bin\g++.exe'
$env:PATH='C:\msys64\ucrt64\bin;'+$env:PATH
.\.venv\Scripts\python.exe -B tests/2026_2/core08/verify_core08.py
.\.venv\Scripts\python.exe -B tests/2026_2/core08/smoke_legacy.py
.\.venv\Scripts\python.exe -B -m unittest discover -s tests -p test_core02_tac.py -v
.\.venv\Scripts\python.exe -B tests/2026_2/core03/verify_core03.py
.\.venv\Scripts\python.exe -B tests/2026_2/core0405/verify_core0405.py
.\.venv\Scripts\python.exe -B scripts/baseline_t01_t07.py --only T02,T03,T04,T05,T06,T07 --repeat 10
.\.venv\Scripts\python.exe -B scripts/validar_planejamento.py
git -c safe.directory=C:/Users/victo/Desktop/FACULDADE/Compiladores/minipar-2026-2 diff --check
```

| Verificação desta rodada | Resultado e oráculo |
|---|---|
| CORE-08 final | **22 PASS**, 0 FAIL/ERROR; 80,016 s |
| FIX-01 a FIX-04 | Igualdade com fixtures, excluindo somente request_id/duração e texto C++ conforme contrato; sem alteração das fixtures |
| ACE-02 | Compilação e execução reais: stdout `5\n`, stderr vazio, exit 0; input UTF-8 também conferido |
| ACE-03 | Falha real de G++ com caso herdado de retorno numérico inconsistente; compilador ausente real; timeout/sucesso sem binário por injeção controlada do runner, não por esperar 120 s |
| ACE-04/08 | Dois fontes, IDs distintos, saídas próprias; SHA-256 dos três artefatos do primeiro id inalterado após o segundo; nomes/media types conferidos |
| ACE-05 | **5 rodadas**, 2 compilações nativas simultâneas em cada; cada ID executou `1\n` ou `2\n` corretamente |
| ACE-06 | Erro seguido de sucesso sem diagnóstico/símbolo residual |
| ACE-07 | Loop nativo, timeout 2 s, retorno <3500 ms, stdout truncado e binário liberado; teste separado verificou PID descendente encerrado pelo Job Object |
| ACE-09 | IDs/kinds/timeouts inválidos e id desconhecido com códigos previstos |
| ACE-10 | **21 builds nativos**; três artefatos e execução correta dos 20 mais recentes |
| ACE-11 | Programa de 5201 nós: 5000 emitidos; AST Python de profundidade 250: 200 emitidos e marcador omitindo 50 nós, sem recursão na serialização |
| I/O volumoso | 1,5 MB em stdout e stderr, simultaneamente drenados, 1 MiB retido em cada; stdin de 2 MB não consumido não causou deadlock |
| Símbolos | Classes, atributos, métodos, parâmetros, função, seq/par, for clássico e iterador; nenhuma declaração duplicada pela especialização |
| Smoke CLI + Web antiga | **PASS**, ambas compilaram/executaram `5\n`; cliente Flask real com subprocessos, sem servidor/porta; CLI inválida exit 1 sem traceback |
| CORE-02 | **5 PASS** |
| CORE-03 | **78 PASS + 1 KNOWN_FAIL**, 0 FAIL; o caso conhecido prova rejeição do G++ por dedução numérica inconsistente |
| CORE-04/05 final | **126 PASS**, 0 FAIL |
| T02 | **FAIL intermitente**, 7/10 PASS; 3 saídas com `1200` pelo print não atômico herdado |
| T03/T05/T06/T07 | **PASS** com os oráculos existentes; T07 inclui mutação TAC e assertions de índices |
| T04 | **PARTIAL**, classificação XOR correta; valores divergentes sem tolerância acordada |
| T01 | **BLOCKED nesta rodada**: fonte abre bind INADDR_ANY; não executado para respeitar a proibição de abrir porta pública. Instabilidade anterior é evidência histórica, não resultado atual |
| FJ completo | **BLOCKED** por #17/#18 ainda não integrados; frontend positivo/negativo foi exercitado, sem contornar TAC |
| Planejamento / diff | PASS, 43 cards / sem erro de whitespace |

As primeiras rodadas CORE-08 tiveram 3 e depois 1 falhas em entradas de teste novas: literais numéricos isolados não alcançavam os ramos pretendidos do parser, e duas sondas supostamente inválidas no G++ eram aceitas pela base. Os testes foram corrigidos para exercitar ramos reais e usar o caso herdado conhecido de retorno inconsistente, sem alterar qualquer oráculo existente. Logs anteriores preservados em `tests.log`/`tests-round2.log`. A rodada final é a evidência de aceite acima; não atribuir as sondas inadequadas ao compilador.

Os validadores herdados geram artefatos em suas pastas canônicas `output/core01`, `core03`, `core0405`; os relatórios atuais foram copiados para `output/core08/baseline`, `core03` e `core0405`. A suíte nova, smoke, reprodução, logs e seus artefatos ficam em `output/core08/`. Binários não são versionados.

## Reprodução mínima e consumo por Riquelme

No mesmo processo Python e na raiz do projeto, com CXX configurado:

```python
from src.service import analyze, compile_program, execute, get_artifact
source = "var x = 2 + 3;\nprint(x);\n"
a = analyze(source)
assert a["ok"] and a["artifacts"]["binary_id"] is None
c = compile_program(source)
assert c["ok"], c["diagnostics"]
r = execute(c["artifacts"]["binary_id"], stdin="", timeout_sec=10)
assert (r["ok"], r["stdout"], r["stderr"], r["exit_code"]) == (True, "5\n", "", 0)
files = {kind: get_artifact(c["request_id"], kind) for kind in ("cpp", "tac", "binary")}
assert all(item["ok"] for item in files.values())
```

B implementa as rotas e entrega os dicts por JSON. Consultar o hash para descartar resposta obsoleta; usar o `binary_id` retornado, nunca nome/caminho enviado pelo navegador. Para download, resolver `get_artifact` dentro do processo que compilou e usar seus campos `path`, `filename`, `media_type`. Não compartilhar IDs entre processos/servidores ou após reiniciar. `kind="arm"` é inválido; extração do stdout do MiniCompilador continua no B. Para fase em erro sem diagnóstico, apresentar falha genérica de fase e consultar a CR; não mostrar sucesso nem inventar mensagem específica. Homologação final de FJ, integração WEB-03/04 e CORE-09 integral permanecem pendentes.

A reprodução acima foi executada com resultado completo em `output/core08/reproduction.json`, incluindo checagem de cwd e ambiente inalterados. `output/core08/legacy/smoke.json` e `web.json` registram o smoke. `output/core08/tests-final.json` lista todos os testes. Hashes SHA-256 dos fontes finais e dados selecionados estão em [CORE-08_RESULTADOS.json](CORE-08_RESULTADOS.json).

## Verificação documental obrigatória e próximos consumidores

Verificados AGENTS.md, MEMORY.md, README, planejamento geral, marcos, C-WEB seção 1 inteira, backlog, validação/aceite, CR-CORE02-TAC-STATUS, handoffs disponíveis e BNF. Atualizados README, ficha CORE-08 em `docs/04_BACKLOG.md`, metadados somente desse card em `planning/cards.json`, esta entrega, CR e evidências selecionadas. Contrato normativo foi preservado; não marcar as pendências antigas como resolvidas/aprovadas por inferência. BNF não muda porque não houve mudança de linguagem ou AST; detalhes novos da API estão neste handoff e README.

**AGENTS.md e MEMORY.md revisados, sem alteração:** a implementação aplica arquitetura, ownership e fluxo já definidos. Não muda instruções permanentes; a exceção de execução local/sem PR é autorização desta tarefa, registrada no card e handoff, não nova política global.

Próximos consumidores: Riquelme/B (WEB-03/04) e revisor independente A. A+B precisam deliberar a CR; após integração dos PRs #17/#18, reexecutar FJ e adaptar a assinatura textual aditiva entregue pelo backend. C não recebeu mudanças de runtime. Não houve publicação nem envio de mensagens a terceiros. Nenhuma aprovação humana foi declarada, nenhum card foi marcado DONE/FROZEN e nenhum stage/commit/push/PR/merge foi feito.

## Revisão corretiva P2 — parâmetros homônimos e flags UTF-8

**Estado mantido: PARTIAL.** Mesma branch `eixo-a/CORE-08-servico-fases`, base e alterações anteriores preservadas. Correção restrita aos dois achados da revisão; sem mudança de contratos, resolução da CR de diagnósticos, stage, commit, push, PR ou merge. Os resultados anteriores acima são históricos; esta seção e `review_p2` no JSON contêm a validação atual.

### Causas e correções

- `src/semantic.py:119`: a observação de um `FuncDecl` distinguia declaração e parâmetro pela igualdade entre os nomes. Agora distingue pela natureza da definição: o símbolo declarado tem tipo interno `FUNC`, enquanto parâmetros são definidos como `var`. Assim, `f(f)` e `m(m)` preservam função/método e registram o parâmetro separadamente como `kind=parameter`, `type=var`, `params=[]`. Escopos, ordem, parâmetros normais e exclusão das especializações continuam iguais.
- `src/service_process.py:107`: o buffer bruto era limitado, mas os bytes de substituição UTF-8 podiam expandir o resultado e sofrer um segundo corte sem sinalização. Cada flag agora considera o excesso bruto **ou** a expansão acima do limite antes do segundo corte. O retorno remove sequência UTF-8 incompleta no limite e mantém a normalização CRLF. Os buffers continuam limitados; a conversão usa no máximo expansão proporcional ao buffer já retido (até 3×), sem armazenar a saída total. Drenagem simultânea e controle dos processos permanecem iguais.
- `tests/2026_2/core08/test_service.py:96` e `:110`: testes de função/método com parâmetro homônimo e controle normal, comparando registros completos, ordem e escopos.
- `tests/2026_2/core08/test_service.py:266`, `:278` e `:286`: ambos os streams com UTF-8 inválido expandido, inválido pequeno sem corte e UTF-8 válido multibyte próximo do limite sem corte.

### Demonstração de regressão e reproduções corrigidas

Antes da correção, os cinco testes novos foram executados contra os fontes anteriores: falharam quatro subcasos, exatamente função homônima, método homônimo, stdout e stderr expandidos. Os controles passaram. Log: `output/core08/review-p2/before-tests.log`. Os fontes, handoff, JSON e resultados anteriores foram copiados antes da correção para `output/core08/review-p2/before/`; seus hashes estão em `before-hashes.json`.

Após a correção, estas entradas foram analisadas com sucesso:

```minipar
func f(f) { return f; }
print(f(1));
```

A tabela contém `f/function/null/s0/params=["f"]`, seguido de `f/parameter/var/s1/params=[]`, sem duplicação.

```minipar
class C { func m(m) { return m; } }
var c = new C();
print(c.m(1));
```

A tabela contém `C/class`, `m/method` no escopo da classe, `m/parameter/var/params=[]` no escopo do método e `c/variable/C`, nessa ordem. Reprodução independente de saída: um processo Python escreve `bytes([255])*400000` em cada stream; cada retorno contém **349.525** caracteres U+FFFD, **1.048.575** bytes UTF-8 e `truncated=true`, com exit 0 e sem timeout. JSON reduzido verificável em `output/core08/review-p2/reproductions.json`.

### Comandos desta revisão

```powershell
# Executado antes da correção: 5 testes, 4 subcasos FAIL esperados.
.\.venv\Scripts\python.exe -B -m unittest discover -s tests/2026_2/core08 -p test_service.py -k review_p2 -v

$env:CXX='C:\msys64\ucrt64\bin\g++.exe'
$env:PATH='C:\msys64\ucrt64\bin;'+$env:PATH
.\.venv\Scripts\python.exe -B tests/2026_2/core08/verify_core08.py
.\.venv\Scripts\python.exe -B tests/2026_2/core0405/verify_core0405.py
.\.venv\Scripts\python.exe -B tests/2026_2/core03/verify_core03.py
.\.venv\Scripts\python.exe -B output/core08/review-p2/collect_results.py
git -c safe.directory=C:/Users/victo/Desktop/FACULDADE/Compiladores/minipar-2026-2 diff --check
```

CORE-08: **27 PASS**, 0 FAIL/ERROR, 102,176 s. CORE-04/05: **126 PASS**, 0 FAIL/ERROR. CORE-03: **78 PASS + 1 KNOWN_FAIL herdado**, 0 FAIL, exit 0; relatório e log dedicados preservados. As validações da rodada inicial de baseline, smoke e CORE-02 não foram repetidas nem promovidas a execução atual.

Evidências atuais: `output/core08/review-p2/` contém logs/relatórios CORE-08 e semânticos, comandos com exit codes, reproduções, `fix.diff` relativo ao início desta revisão, `results.json` e `final-source-hashes.json`. O JSON versionável `docs/auditorias/CORE-08_RESULTADOS.json` preserva `results` histórico e os hashes anteriores em `source_hash_history`; os resultados atuais ficam em `review_p2`, com `source_sha256` atualizado. Os artefatos nativos da suíte permanecem em `output/core08/web/`.

Documentos verificados nesta correção: C-WEB, planejamento, backlog, validação, README, handoff, resultados, AGENTS e MEMORY. Atualizados somente o handoff e JSON/evidências impactados. README e contrato já descrevem o comportamento corrigido e não precisam mudar. **AGENTS.md e MEMORY.md revisados e mantidos**, pois não houve mudança de arquitetura, convenções ou fluxo de desenvolvimento. CR de diagnósticos permanece proposta pendente e CORE-08 permanece PARTIAL. Nenhuma publicação ou aprovação humana foi realizada nesta revisão.
