# Backlog operacional detalhado — MiniPar 2026.2

> **PRÉ-ISSUES, v0.1 — 15/10/2026.** Nenhuma GitHub Issue foi criada. Fonte estruturada: `planning/cards.json`. Revisar com os três responsáveis antes de publicar.

## Regras para usar este backlog

- Cada card tem **um eixo responsável**, prazo-limite, dependências, arquivos autorizados, evidência e critério de aceite. Os nomes de B/C serão decididos no kickoff.
- `ready=false` no JSON até a Definition of Ready ser comprovada. Não começar código só porque existe prazo.
- `BACKLOG` → `READY` → `IN_PROGRESS` → `IN_REVIEW` → `DONE`. `BLOCKED` é um impedimento rastreável, jamais uma conclusão.
- Eixo **A é dono de `src/`**. Execução de baseline/regressão por C **não autoriza C a alterar o compilador**; C abre defeito para A.
- B pode produzir pseudocódigos, UML e consolidar o relatório, mas **A valida detalhes do núcleo, C valida o runtime**; nenhum editor deve inventar implementação.
- Se um contrato mudar, abrir CR conforme `docs/02_CONTRATOS_TECNICOS.md` e `AGENTS.md`.
- `estimate_hours` são estimativas de supervisão e execução humana assistida por IA; **não são esforço mensurado** e podem mudar após G0.

## Marcos de controle

| Gate | Data | Evidência para aprovação |
|---|---|---|
| G0 | 18/10 | Repositório/base importados; ambiente/base testados ou bloqueio concreto; três contratos aprovados |
| G1 | 23/10 | Fork/Join local via MiniPar; teste remoto de worker em dois PCs; prova Teste 11 com ARM/CPUlator |
| G2 | 28/10 | T08 ponta a ponta; Web consumindo API real; Teste 11 obrigatório validado |
| G3 | 31/10 | T01–T11 e três interfaces demonstrados ou falhas registradas; teste remoto integrado |
| G4 | 03/11 | Release candidata, documentação/relatório e evidências verificáveis |
| G5 | 10/11 | Estudo e ensaio de apresentação concluídos |

## Visão resumida dos 43 cards

| ID | Eixo | Prioridade | Prazo | Est. (h) | Dependências | Entrega |
|---|---|---|---|---:|---|---|
| `SET-01` | A | P0 | 16/10 | 2 | — | Criar estrutura e importar base 2026.1 |
| `SET-02` | A | P0 | 18/10 | 4 | `SET-01` | Padronizar Python e G++20; executar smoke |
| `SET-03` | A | P0 | 16/10 | 1 | — | Permissões Git, responsáveis B/C, branches e acesso a dois PCs |
| `CON-01` | A+C | P0 | 18/10 | 3 | `SET-01` | Congelar contrato de Fork/Join e destino local/remoto |
| `CON-02` | A+B | P0 | 18/10 | 2 | `SET-01` | Congelar contrato serviço de fases para a Web |
| `CON-03` | A+B | P0 | 18/10 | 2 | `SET-01` | Congelar recursos mínimos Teste 11 e saída ARM |
| `CORE-01` | C | P0 | 18/10 | 3 | `SET-02` | Registrar baseline reprodutível dos testes 1–7 |
| `CORE-02` | A | P0 | 21/10 | 5 | `CORE-01` | Remover TAC fixo do Quicksort e corrigir T07 |
| `CORE-03` | A | P0 | 21/10 | 6 | `CON-03`, `SET-02` | Corrigir primitivas strings e coleções usadas por T11 |
| `CORE-04` | A | P0 | 22/10 | 6 | `CON-01` | Implementar BNF, tokens e AST de Fork/Join |
| `CORE-05` | A | P0 | 23/10 | 4 | `CORE-04` | Semântico de Fork/Join e isolamento |
| `CORE-06` | A | P0 | 25/10 | 5 | `CORE-05`, `CORE-02` | TAC autêntico para Fork/Join e `par` |
| `CORE-07` | A | P0 | 26/10 | 6 | `CORE-05`, `RUN-01`, `RUN-02` | Gerar C++ que invoca runtime real de C |
| `CORE-08` | A | P0 | 25/10 | 5 | `CON-02`, `SET-02` | Expor serviço de fases ao eixo Web |
| `CORE-09` | A | P0 | 30/10 | 3 | `CORE-07`, `CORE-08` | Preservar terminal e Web antiga após mudanças |
| `CORE-10` | C | P0 | 31/10 | 3 | `CORE-02`, `CORE-03`, `CORE-07` | Regressão final T01–T07 com oráculos reais |
| `WEB-01` | B | P1 | 20/10 | 4 | `CON-02` | Wireframe e fixtures JSON dos painéis didáticos |
| `WEB-02` | B | P0 | 24/10 | 7 | `WEB-01` | Implementar AST interativa e painéis de fases |
| `WEB-03` | B | P0 | 28/10 | 5 | `CORE-08`, `WEB-02` | Integrar UI ao serviço real fornecido pelo A |
| `WEB-04` | B | P0 | 30/10 | 5 | `WEB-03` | Compilar, executar e baixar binário atual |
| `T11-01` | B | P0 | 21/10 | 5 | `CON-03`, `CORE-03` | Recuperar prova experimental e concluir MVP MiniCompilador |
| `T11-02` | B | P0 | 26/10 | 8 | `T11-01` | Completar semântica, símbolos, erros e emissão ARM do T11 |
| `T11-03` | B | P0 | 28/10 | 5 | `T11-02` | Validar Assembly no CPUlator e arquivar evidências |
| `WEB-05` | B | P0 | 02/11 | 4 | `WEB-04`, `T11-03` | Documentar interface, T11 e preparar screenshots |
| `RUN-01` | C | P0 | 21/10 | 7 | `CON-01` | Runtime local de start/join com isolamento |
| `RUN-02` | C | P0 | 22/10 | 8 | `CON-01` | Protocolo TCP robusto e worker pré-compilado |
| `RUN-03` | C | P0 | 23/10 | 5 | `RUN-02`, `SET-03` | Prova de execução em dois computadores reais |
| `RUN-04` | C | P0 | 26/10 | 4 | `RUN-01`, `RUN-03`, `CORE-05` | Handoff de API runtime e integração com backend A |
| `T08-01` | C | P0 | 27/10 | 6 | `RUN-04`, `CORE-07` | MiniPar T08: 160 avaliações em quatro trabalhadores |
| `T09-01` | C | P0 | 29/10 | 6 | `T08-01` | MiniPar T09: avaliadores + Mandelbrot ASCII |
| `T10-01` | C | P0 | 30/10 | 7 | `T09-01` | MiniPar T10: avaliações + Mandelbrot + Sierpinski |
| `RUN-05` | C | P0 | 31/10 | 4 | `T10-01`, `RUN-03` | Benchmarks e falhas distribuídas repetíveis |
| `RUN-06` | C | P0 | 02/11 | 4 | `RUN-05` | Documentar protocolo, topologia, deploy e testes |
| `INT-01` | C | P0 | 28/10 | 3 | `CORE-07`, `WEB-03`, `RUN-04` | Smoke de integração 3 eixos antes do fechamento |
| `INT-02` | B | P0 | 31/10 | 4 | `INT-01`, `WEB-04`, `T11-03`, `T10-01`, `CORE-10` | Regressão integral, três interfaces e rede real |
| `DOC-01` | B | P0 | 02/11 | 4 | `CORE-06` | BNF final e pseudocódigos núcleo |
| `DOC-02` | B | P0 | 02/11 | 4 | `INT-01` | UML casos de uso, componentes, classes |
| `DOC-03` | C | P0 | 02/11 | 2 | `INT-01` | Product Backlog, Sprint Backlogs e decisões atualizados |
| `DOC-04` | B | P0 | 03/11 | 5 | `INT-02`, `DOC-01`, `DOC-02`, `DOC-03`, `WEB-05`, `RUN-06` | Relatório completo, evidências e GitHub na capa |
| `REL-01` | A | P0 | 03/11 | 2 | `DOC-04` | Congelar release candidata 03/11 |
| `EST-01` | EQUIPE | P0 | 08/11 | 4 | `REL-01` | Estudo de módulos e roteiro individual |
| `EST-02` | EQUIPE | P0 | 10/11 | 3 | `EST-01` | Ensaio completo e contingência de demo |
| `ENT-01` | EQUIPE | P0 | 11/11 | 2 | `EST-02` | Entrega final 11/11 |

## Carga aproximada por eixo e alerta de capacidade

| Eixo | Horas estimadas dos cards | Observação |
|---|---:|---|
| A | 49 | Responsável pelo núcleo; tem limite relatado de até 3h/dia |
| B | 60 | Nome e disponibilidade ainda em aberto |
| C | 62 | Nome e disponibilidade ainda em aberto |
| A+B | 4 | Horas conjuntas; evitar somar duas vezes |
| A+C | 3 | Horas conjuntas; evitar somar duas vezes |
| EQUIPE | 9 | Horas conjuntas de estudo/entrega, após 03/11 |

**Alerta:** A possui ~49h exclusivas até 03/11, além de participação em contratos, PRs e estudo. Seu teto de ~57h **não permite absorver** o QA de C, os documentos de B ou o runtime. Se as horas disponíveis de B/C forem menores que o estimado, replanejar imediatamente os cards e marcos, mantendo os requisitos do professor visíveis.

## Fichas completas por responsável

### Eixo A — Núcleo e coordenação

#### `SET-01` — Criar estrutura e importar base 2026.1

**Prazo:** 16/10/2026 · **Prioridade:** P0 · **Estimativa:** 2 h · **Estado inicial:** BACKLOG

**Estado atual (16/10/2026):** IN_PROGRESS · `ready=true`. Pessoa A/coordenador e agente Codex; sem dependências ou contratos de implementação consumidos neste recorte estrutural. Branch de preparação `setup/ambiente-baseline` preservada por instrução do coordenador. Evidências em `auditorias/SET-01_VALIDACAO_ESTRUTURAL.md`; revisão humana, PR e integração pendentes. Não libera automaticamente SET-02.

**Eixo responsável:** A. **Nome humano:** A (coordenador).

**Dependências:** Nenhuma.

**Entrega objetiva:** Código legado imutável e cópia ativa na raiz; registrar origem/commit

**Critério de aceite:** Arquivos ativos presentes; `legacy` preservado; scripts de importação conferidos; workspace inicial sem alterações preexistentes indevidas e diff final restrito ao SET-01 (pode haver alterações do card antes do commit).

**Escopo de arquivos autorizado:** `scripts/`, `legacy/`, `raiz ativa`.

**Evidência mínima de conclusão:** PR/commit associado, comandos e saídas do teste ou artefato documental revisado, status real PASS/FAIL/BLOCKED, e handoff ao consumidor.

**Antes de iniciar:** confirmar que todos os contratos consumidos estão congelados ou existe fixture/mock aprovado. Nunca tocar arquivos de outro eixo por conveniência.

#### `SET-02` — Padronizar Python e G++20; executar smoke

**Prazo:** 18/10/2026 · **Prioridade:** P0 · **Estimativa:** 4 h · **Estado inicial:** BACKLOG

**Estado atual (16/10/2026):** IN_PROGRESS · `ready=true`, validação técnica PASS e revisão humana/PR/integração pendentes. Pessoa A/coordenador e agente Codex; SET-01 aprovado tecnicamente e commitado em `0455de3`; continuidade autorizada em `setup/ambiente-baseline`, com commits separados no PR conjunto. G++ UCRT64 16.2.0 e Flask 3.0.0 na venv conferidos; probe C++20/threads/sockets, smoke 14, T02 e negativos PASS. **T01 compilou e executou realmente em teste local controlado: servidor recebeu + 2 3, cliente recebeu 5.000000, exit=0, 0,562 s, sem timeout/stderr.** Script `scripts/testar_set02_t01_offline.ps1` usa modo local por padrão, firewall ativo, cliente 127.0.0.1, portas livres, limite de 10 s e Job Object; offline rigoroso opcional com `-StrictOffline`. Nenhuma configuração de rede/firewall/PATH persistente alterada. Evidência atual na seção 16 de `auditorias/SET-02_AMBIENTE_E_SMOKE.md`; ambiente e critério técnico T01 aprovados nesta rodada, sem afirmar estabilidade universal ou comunicação entre computadores. CORE-01 receberá a evidência quando liberado; SET-03 não iniciado. Sem DONE ou commit.

**Eixo responsável:** A. **Nome humano:** A (coordenador).

**Dependências:** `SET-01`.

**Entrega objetiva:** Instruções reprodutíveis de build; superar GCC 6.3 incompatível

**Critério de aceite:** T01 simples compila e executa em ferramenta suportada; log identifica versões e comandos.

**Escopo de arquivos autorizado:** `docs/`, `src/`, `main.py`.

**Evidência mínima de conclusão:** PR/commit associado, comandos e saídas do teste ou artefato documental revisado, status real PASS/FAIL/BLOCKED, e handoff ao consumidor.

**Antes de iniciar:** confirmar que todos os contratos consumidos estão congelados ou existe fixture/mock aprovado. Nunca tocar arquivos de outro eixo por conveniência.

#### `SET-03` — Permissões Git, responsáveis B/C, branches e acesso a dois PCs

**Prazo:** 16/10/2026 · **Prioridade:** P0 · **Estimativa:** 1 h · **Estado inicial:** BACKLOG

**Eixo responsável:** A. **Nome humano:** A (coordenador).

**Dependências:** Nenhuma.

**Entrega objetiva:** Repositório privado acessível aos três, owners nomeados, hosts disponíveis

**Critério de aceite:** Trio confirma acesso/horas; hosts de rede definidos; branch protect quando viável.

**Escopo de arquivos autorizado:** `docs/`, `planning/`.

**Evidência mínima de conclusão:** PR/commit associado, comandos e saídas do teste ou artefato documental revisado, status real PASS/FAIL/BLOCKED, e handoff ao consumidor.

**Antes de iniciar:** confirmar que todos os contratos consumidos estão congelados ou existe fixture/mock aprovado. Nunca tocar arquivos de outro eixo por conveniência.

#### `CORE-02` — Remover TAC fixo do Quicksort e corrigir T07

**Prazo:** 21/10/2026 · **Prioridade:** P0 · **Estimativa:** 5 h · **Estado inicial:** BACKLOG

**Eixo responsável:** A. **Nome humano:** A (coordenador).

**Dependências:** `CORE-01`.

**Entrega objetiva:** TAC calculado da AST e ordenação segura

**Critério de aceite:** Programa modificado com mesmo nome não reproduz TAC fixo; T07 compila/ordena sem bounds violation.

**Escopo de arquivos autorizado:** `src/tac.py`, `tests/`, `src/codegen.py`.

**Evidência mínima de conclusão:** PR/commit associado, comandos e saídas do teste ou artefato documental revisado, status real PASS/FAIL/BLOCKED, e handoff ao consumidor.

**Antes de iniciar:** confirmar que todos os contratos consumidos estão congelados ou existe fixture/mock aprovado. Nunca tocar arquivos de outro eixo por conveniência.

#### `CORE-03` — Corrigir primitivas strings e coleções usadas por T11

**Prazo:** 21/10/2026 · **Prioridade:** P0 · **Estimativa:** 6 h · **Estado inicial:** BACKLOG

**Eixo responsável:** A. **Nome humano:** A (coordenador).

**Dependências:** `CON-03`, `SET-02`.

**Entrega objetiva:** `len`, `substr`, `to_string`, string `std::string`; listas numéricas para T11; rejeição temporária de listas textuais (C-T11-v1 §3.4)

**Critério de aceite:** Programas de prova T11 compilam/produzem oráculos; regressão anterior sem piora.

**Escopo de arquivos autorizado:** `src/codegen.py`, `src/semantic.py`, `src/cpp_template.py`, `BNF-grammar.md`, `tests/2026_2/core03/`, `docs/auditorias/CORE-03_*`.

**Extensão autorizada (26/10/2026):** auditoria/correção e atualização do PR #14 pelo coordenador, com testes, BNF e evidências; alinhamento a C-T11-v1 §3.4. Listas textuais completas permanecem em PEND-T11-03. Não altera ready/status nem aprova contrato por inferência.

**Evidência mínima de conclusão:** PR/commit associado, comandos e saídas do teste ou artefato documental revisado, status real PASS/FAIL/BLOCKED, e handoff ao consumidor.

**Antes de iniciar:** confirmar que todos os contratos consumidos estão congelados ou existe fixture/mock aprovado. Nunca tocar arquivos de outro eixo por conveniência.

#### `CORE-04` — Implementar BNF, tokens e AST de Fork/Join

**Prazo:** 22/10/2026 · **Prioridade:** P0 · **Estimativa:** 6 h · **Estado inicial:** BACKLOG

**Eixo responsável:** A. **Nome humano:** A (coordenador).

**Dependências:** `CON-01`.

**Entrega objetiva:** Gramática adotada, Lexer/Parser/AST e diagnósticos

**Critério de aceite:** Programas MiniPar positivos/negativos de Fork/Join têm AST correta; BNF coerente.

**Escopo de arquivos autorizado:** `src/lexer.py`, `src/parser.py`, `src/ast_nodes.py`, `docs/`.

**Evidência mínima de conclusão:** PR/commit associado, comandos e saídas do teste ou artefato documental revisado, status real PASS/FAIL/BLOCKED, e handoff ao consumidor.

**Antes de iniciar:** confirmar que todos os contratos consumidos estão congelados ou existe fixture/mock aprovado. Nunca tocar arquivos de outro eixo por conveniência.

#### `CORE-05` — Semântico de Fork/Join e isolamento

**Prazo:** 23/10/2026 · **Prioridade:** P0 · **Estimativa:** 4 h · **Estado inicial:** BACKLOG

**Eixo responsável:** A. **Nome humano:** A (coordenador).

**Dependências:** `CORE-04`.

**Entrega objetiva:** Regras semânticas e tipos/handles necessários

**Critério de aceite:** Uso indevido rejeitado; funções e destinos válidos aceitos; semântico preserva regressão.

**Escopo de arquivos autorizado:** `src/semantic.py`.

**Evidência mínima de conclusão:** PR/commit associado, comandos e saídas do teste ou artefato documental revisado, status real PASS/FAIL/BLOCKED, e handoff ao consumidor.

**Antes de iniciar:** confirmar que todos os contratos consumidos estão congelados ou existe fixture/mock aprovado. Nunca tocar arquivos de outro eixo por conveniência.

#### `CORE-06` — TAC autêntico para Fork/Join e `par`

**Prazo:** 25/10/2026 · **Prioridade:** P0 · **Estimativa:** 5 h · **Estado inicial:** BACKLOG

**Eixo responsável:** A. **Nome humano:** A (coordenador).

**Dependências:** `CORE-05`, `CORE-02`.

**Entrega objetiva:** TAC representa criação, sincronização e fluxo; sem hardcodes

**Critério de aceite:** TAC distingue sequência/paralelismo; casos com diferentes tarefas geram representação coerente.

**Escopo de arquivos autorizado:** `src/tac.py`.

**Evidência mínima de conclusão:** PR/commit associado, comandos e saídas do teste ou artefato documental revisado, status real PASS/FAIL/BLOCKED, e handoff ao consumidor.

**Antes de iniciar:** confirmar que todos os contratos consumidos estão congelados ou existe fixture/mock aprovado. Nunca tocar arquivos de outro eixo por conveniência.

#### `CORE-07` — Gerar C++ que invoca runtime real de C

**Prazo:** 26/10/2026 · **Prioridade:** P0 · **Estimativa:** 6 h · **Estado inicial:** BACKLOG

**Eixo responsável:** A. **Nome humano:** A (coordenador).

**Dependências:** `CORE-05`, `RUN-01`, `RUN-02`.

**Entrega objetiva:** Backend integra contratos `start/join` locais e remotos

**Critério de aceite:** MiniPar→C++→binário cria tarefa local e remota de teste; join retorna dado correto.

**Escopo de arquivos autorizado:** `src/codegen.py`, `src/cpp_template.py`.

**Evidência mínima de conclusão:** PR/commit associado, comandos e saídas do teste ou artefato documental revisado, status real PASS/FAIL/BLOCKED, e handoff ao consumidor.

**Antes de iniciar:** confirmar que todos os contratos consumidos estão congelados ou existe fixture/mock aprovado. Nunca tocar arquivos de outro eixo por conveniência.

#### `CORE-08` — Expor serviço de fases ao eixo Web

**Prazo:** 25/10/2026 · **Prioridade:** P0 · **Estimativa:** 5 h · **Estado inicial:** BACKLOG

**Eixo responsável:** A. **Nome humano:** A (coordenador).

**Dependências:** `CON-02`, `SET-02`.

**Entrega objetiva:** API Python estruturada com tokens, AST, símbolos, erros, TAC, C++

**Critério de aceite:** Fixtures combinam com resultados reais; IDs evitam cache errado; erro separa fases.

**Escopo de arquivos autorizado:** `src/`, `app.py`.

**Evidência mínima de conclusão:** PR/commit associado, comandos e saídas do teste ou artefato documental revisado, status real PASS/FAIL/BLOCKED, e handoff ao consumidor.

**Antes de iniciar:** confirmar que todos os contratos consumidos estão congelados ou existe fixture/mock aprovado. Nunca tocar arquivos de outro eixo por conveniência.

#### `CORE-09` — Preservar terminal e Web antiga após mudanças

**Prazo:** 30/10/2026 · **Prioridade:** P0 · **Estimativa:** 3 h · **Estado inicial:** BACKLOG

**Eixo responsável:** A. **Nome humano:** A (coordenador).

**Dependências:** `CORE-07`, `CORE-08`.

**Entrega objetiva:** CLI e Web original sem regressões relevantes

**Critério de aceite:** Executar cenário básico nas duas interfaces e comparar com versão inicial.

**Escopo de arquivos autorizado:** `main.py`, `menu.py`, `app.py`, `templates/`, `static/`.

**Evidência mínima de conclusão:** PR/commit associado, comandos e saídas do teste ou artefato documental revisado, status real PASS/FAIL/BLOCKED, e handoff ao consumidor.

**Antes de iniciar:** confirmar que todos os contratos consumidos estão congelados ou existe fixture/mock aprovado. Nunca tocar arquivos de outro eixo por conveniência.

#### `REL-01` — Congelar release candidata 03/11

**Prazo:** 03/11/2026 · **Prioridade:** P0 · **Estimativa:** 2 h · **Estado inicial:** BACKLOG

**Eixo responsável:** A. **Nome humano:** A (coordenador).

**Dependências:** `DOC-04`.

**Entrega objetiva:** Tag, checklist, instruções, estado conhecido

**Critério de aceite:** Build reproduzível a partir de checkout limpo; evidências acessíveis; pendências explícitas.

**Escopo de arquivos autorizado:** `docs/`, `README.md`.

**Evidência mínima de conclusão:** PR/commit associado, comandos e saídas do teste ou artefato documental revisado, status real PASS/FAIL/BLOCKED, e handoff ao consumidor.

**Antes de iniciar:** confirmar que todos os contratos consumidos estão congelados ou existe fixture/mock aprovado. Nunca tocar arquivos de outro eixo por conveniência.

### Eixo B — Web, Teste 11 e documentos (nome em aberto)

#### `WEB-01` — Wireframe e fixtures JSON dos painéis didáticos

**Prazo:** 20/10/2026 · **Prioridade:** P1 · **Estimativa:** 4 h · **Estado inicial:** BACKLOG

**Eixo responsável:** B. **Nome humano:** a confirmar com a equipe.

**Dependências:** `CON-02`.

**Entrega objetiva:** Design de fluxo editor/tokens/AST/semântico/TAC/C++/run

**Critério de aceite:** Todas as fases navegáveis em mock; AST desenhada de fixture; Web original intocada.

**Escopo de arquivos autorizado:** `web_didatica/`.

**Evidência mínima de conclusão:** PR/commit associado, comandos e saídas do teste ou artefato documental revisado, status real PASS/FAIL/BLOCKED, e handoff ao consumidor.

**Antes de iniciar:** confirmar que todos os contratos consumidos estão congelados ou existe fixture/mock aprovado. Nunca tocar arquivos de outro eixo por conveniência.

#### `WEB-02` — Implementar AST interativa e painéis de fases

**Prazo:** 24/10/2026 · **Prioridade:** P0 · **Estimativa:** 7 h · **Estado inicial:** BACKLOG

**Eixo responsável:** B. **Nome humano:** a confirmar com a equipe.

**Dependências:** `WEB-01`.

**Entrega objetiva:** Visão hierárquica realista de AST; tokens, símbolos, diagnósticos, TAC, C++

**Critério de aceite:** AST expandir/recolher; erros legíveis; programas grandes sem travar UI em exemplo.

**Escopo de arquivos autorizado:** `web_didatica/`.

**Evidência mínima de conclusão:** PR/commit associado, comandos e saídas do teste ou artefato documental revisado, status real PASS/FAIL/BLOCKED, e handoff ao consumidor.

**Antes de iniciar:** confirmar que todos os contratos consumidos estão congelados ou existe fixture/mock aprovado. Nunca tocar arquivos de outro eixo por conveniência.

#### `WEB-03` — Integrar UI ao serviço real fornecido pelo A

**Prazo:** 28/10/2026 · **Prioridade:** P0 · **Estimativa:** 5 h · **Estado inicial:** BACKLOG

**Eixo responsável:** B. **Nome humano:** a confirmar com a equipe.

**Dependências:** `CORE-08`, `WEB-02`.

**Entrega objetiva:** Web didática usa resultados de compilação real

**Critério de aceite:** Exemplo positivo e erro são fiéis à compilação; sem dados hardcoded no fluxo real.

**Escopo de arquivos autorizado:** `web_didatica/`.

**Evidência mínima de conclusão:** PR/commit associado, comandos e saídas do teste ou artefato documental revisado, status real PASS/FAIL/BLOCKED, e handoff ao consumidor.

**Antes de iniciar:** confirmar que todos os contratos consumidos estão congelados ou existe fixture/mock aprovado. Nunca tocar arquivos de outro eixo por conveniência.

#### `WEB-04` — Compilar, executar e baixar binário atual

**Prazo:** 30/10/2026 · **Prioridade:** P0 · **Estimativa:** 5 h · **Estado inicial:** BACKLOG

**Eixo responsável:** B. **Nome humano:** a confirmar com a equipe.

**Dependências:** `WEB-03`.

**Entrega objetiva:** Ações reais com timeout, stdout/stderr e download

**Critério de aceite:** G++ realmente compila; returncode validado; download é artefato correto; timeout/erro apresentados.

**Escopo de arquivos autorizado:** `web_didatica/`.

**Evidência mínima de conclusão:** PR/commit associado, comandos e saídas do teste ou artefato documental revisado, status real PASS/FAIL/BLOCKED, e handoff ao consumidor.

**Antes de iniciar:** confirmar que todos os contratos consumidos estão congelados ou existe fixture/mock aprovado. Nunca tocar arquivos de outro eixo por conveniência.

#### `T11-01` — Recuperar prova experimental e concluir MVP MiniCompilador

**Prazo:** 21/10/2026 · **Prioridade:** P0 · **Estimativa:** 5 h · **Estado inicial:** BACKLOG

**Eixo responsável:** B. **Nome humano:** a confirmar com a equipe.

**Dependências:** `CON-03`, `CORE-03`.

**Entrega objetiva:** Expressões com parênteses, operadores, tokens, AST por índices, TAC

**Critério de aceite:** Ao menos a primeira expressão obrigatória retorna 22 em programa MiniPar executado.

**Escopo de arquivos autorizado:** `tests/2026_2/test11/`.

**Evidência mínima de conclusão:** PR/commit associado, comandos e saídas do teste ou artefato documental revisado, status real PASS/FAIL/BLOCKED, e handoff ao consumidor.

**Antes de iniciar:** confirmar que todos os contratos consumidos estão congelados ou existe fixture/mock aprovado. Nunca tocar arquivos de outro eixo por conveniência.

#### `T11-02` — Completar semântica, símbolos, erros e emissão ARM do T11

**Prazo:** 26/10/2026 · **Prioridade:** P0 · **Estimativa:** 8 h · **Estado inicial:** BACKLOG

**Eixo responsável:** B. **Nome humano:** a confirmar com a equipe.

**Dependências:** `T11-01`.

**Entrega objetiva:** Três expressões obrigatórias, tabela símbolos, impressão ARM e `.arm`

**Critério de aceite:** Resultados 22,-84,22; nenhum valor fixo por entrada; erros relevantes rejeitados.

**Escopo de arquivos autorizado:** `tests/2026_2/test11/`.

**Evidência mínima de conclusão:** PR/commit associado, comandos e saídas do teste ou artefato documental revisado, status real PASS/FAIL/BLOCKED, e handoff ao consumidor.

**Antes de iniciar:** confirmar que todos os contratos consumidos estão congelados ou existe fixture/mock aprovado. Nunca tocar arquivos de outro eixo por conveniência.

#### `T11-03` — Validar Assembly no CPUlator e arquivar evidências

**Prazo:** 28/10/2026 · **Prioridade:** P0 · **Estimativa:** 5 h · **Estado inicial:** BACKLOG

**Eixo responsável:** B. **Nome humano:** a confirmar com a equipe.

**Dependências:** `T11-02`.

**Entrega objetiva:** Arquivos ARM executados, prints/resultados com registrador final

**Critério de aceite:** Três `.arm` executam com resultados; registrar CPUlator/versão e instruções.

**Escopo de arquivos autorizado:** `tests/2026_2/test11/`, `docs/evidencias/`.

**Evidência mínima de conclusão:** PR/commit associado, comandos e saídas do teste ou artefato documental revisado, status real PASS/FAIL/BLOCKED, e handoff ao consumidor.

**Antes de iniciar:** confirmar que todos os contratos consumidos estão congelados ou existe fixture/mock aprovado. Nunca tocar arquivos de outro eixo por conveniência.

#### `WEB-05` — Documentar interface, T11 e preparar screenshots

**Prazo:** 02/11/2026 · **Prioridade:** P0 · **Estimativa:** 4 h · **Estado inicial:** BACKLOG

**Eixo responsável:** B. **Nome humano:** a confirmar com a equipe.

**Dependências:** `WEB-04`, `T11-03`.

**Entrega objetiva:** Pseudocódigo Teste 11, instruções UI, prints e explicações

**Critério de aceite:** Seções prontos para relatório com evidências verificáveis.

**Escopo de arquivos autorizado:** `docs/`, `web_didatica/`.

**Evidência mínima de conclusão:** PR/commit associado, comandos e saídas do teste ou artefato documental revisado, status real PASS/FAIL/BLOCKED, e handoff ao consumidor.

**Antes de iniciar:** confirmar que todos os contratos consumidos estão congelados ou existe fixture/mock aprovado. Nunca tocar arquivos de outro eixo por conveniência.

#### `INT-02` — Regressão integral, três interfaces e rede real

**Prazo:** 31/10/2026 · **Prioridade:** P0 · **Estimativa:** 4 h · **Estado inicial:** BACKLOG

**Eixo responsável:** B. **Nome humano:** a confirmar com a equipe.

**Dependências:** `INT-01`, `WEB-04`, `T11-03`, `T10-01`, `CORE-10`.

**Entrega objetiva:** Coordenação da regressão final; A e C validam respectivamente compilador e runtime

**Critério de aceite:** Cada caso PASS/FAIL/BLOCKED com oráculo; falhas e severidade registradas.

**Escopo de arquivos autorizado:** `docs/auditorias/`, `tests/`, `scripts/`.

**Evidência mínima de conclusão:** PR/commit associado, comandos e saídas do teste ou artefato documental revisado, status real PASS/FAIL/BLOCKED, e handoff ao consumidor.

**Antes de iniciar:** confirmar que todos os contratos consumidos estão congelados ou existe fixture/mock aprovado. Nunca tocar arquivos de outro eixo por conveniência.

#### `DOC-01` — BNF final e pseudocódigos núcleo

**Prazo:** 02/11/2026 · **Prioridade:** P0 · **Estimativa:** 4 h · **Estado inicial:** BACKLOG

**Eixo responsável:** B. **Nome humano:** a confirmar com a equipe.

**Dependências:** `CORE-06`.

**Entrega objetiva:** Consolidar BNF e pseudocódigos a partir do código de A; A aprova exatidão

**Critério de aceite:** Consistência com implementação real e regras de Fork/Join.

**Escopo de arquivos autorizado:** `docs/`.

**Evidência mínima de conclusão:** PR/commit associado, comandos e saídas do teste ou artefato documental revisado, status real PASS/FAIL/BLOCKED, e handoff ao consumidor.

**Antes de iniciar:** confirmar que todos os contratos consumidos estão congelados ou existe fixture/mock aprovado. Nunca tocar arquivos de outro eixo por conveniência.

#### `DOC-02` — UML casos de uso, componentes, classes

**Prazo:** 02/11/2026 · **Prioridade:** P0 · **Estimativa:** 4 h · **Estado inicial:** BACKLOG

**Eixo responsável:** B. **Nome humano:** a confirmar com a equipe.

**Dependências:** `INT-01`.

**Entrega objetiva:** Produzir UML a partir das interfaces reais dos três eixos; A/C revisam

**Critério de aceite:** Interfaces e classes existentes, geradores TAC/C++ incluídos; peer review dos eixos.

**Escopo de arquivos autorizado:** `docs/`.

**Evidência mínima de conclusão:** PR/commit associado, comandos e saídas do teste ou artefato documental revisado, status real PASS/FAIL/BLOCKED, e handoff ao consumidor.

**Antes de iniciar:** confirmar que todos os contratos consumidos estão congelados ou existe fixture/mock aprovado. Nunca tocar arquivos de outro eixo por conveniência.

#### `DOC-04` — Relatório completo, evidências e GitHub na capa

**Prazo:** 03/11/2026 · **Prioridade:** P0 · **Estimativa:** 5 h · **Estado inicial:** BACKLOG

**Eixo responsável:** B. **Nome humano:** a confirmar com a equipe.

**Dependências:** `INT-02`, `DOC-01`, `DOC-02`, `DOC-03`, `WEB-05`, `RUN-06`.

**Entrega objetiva:** Consolidar relatório e evidências de A/B/C com link GitHub na capa; revisão conjunta

**Critério de aceite:** Professor encontra todos entregáveis; referências e anexos testados.

**Escopo de arquivos autorizado:** `docs/`, `README.md`.

**Evidência mínima de conclusão:** PR/commit associado, comandos e saídas do teste ou artefato documental revisado, status real PASS/FAIL/BLOCKED, e handoff ao consumidor.

**Antes de iniciar:** confirmar que todos os contratos consumidos estão congelados ou existe fixture/mock aprovado. Nunca tocar arquivos de outro eixo por conveniência.

### Eixo C — Runtime, testes 8–10 e QA (nome em aberto)

#### `CORE-01` — Registrar baseline reprodutível dos testes 1–7

**Prazo:** 18/10/2026 · **Prioridade:** P0 · **Estimativa:** 3 h · **Estado inicial:** BACKLOG

**Eixo responsável:** C. **Nome humano:** a confirmar com a equipe.

**Dependências:** `SET-02`.

**Entrega objetiva:** Matriz baseline dos testes herdados, sem alterar src/; falhas encaminhadas a A

**Critério de aceite:** Execução nativa de cada T01–T07 com status PASS/FAIL/BLOCKED e evidência.

**Escopo de arquivos autorizado:** `docs/auditorias/`, `tests/`, `scripts/`.

**Evidência mínima de conclusão:** PR/commit associado, comandos e saídas do teste ou artefato documental revisado, status real PASS/FAIL/BLOCKED, e handoff ao consumidor.

**Antes de iniciar:** confirmar que todos os contratos consumidos estão congelados ou existe fixture/mock aprovado. Nunca tocar arquivos de outro eixo por conveniência.

#### `CORE-10` — Regressão final T01–T07 com oráculos reais

**Prazo:** 31/10/2026 · **Prioridade:** P0 · **Estimativa:** 3 h · **Estado inicial:** BACKLOG

**Eixo responsável:** C. **Nome humano:** a confirmar com a equipe.

**Dependências:** `CORE-02`, `CORE-03`, `CORE-07`.

**Entrega objetiva:** Executar testes 1–7 no código de A e registrar oráculos; A corrige src/

**Critério de aceite:** Não há falsos PASS; bugs remanescentes com risco registrado.

**Escopo de arquivos autorizado:** `docs/auditorias/`, `tests/`, `scripts/`.

**Evidência mínima de conclusão:** PR/commit associado, comandos e saídas do teste ou artefato documental revisado, status real PASS/FAIL/BLOCKED, e handoff ao consumidor.

**Antes de iniciar:** confirmar que todos os contratos consumidos estão congelados ou existe fixture/mock aprovado. Nunca tocar arquivos de outro eixo por conveniência.

#### `RUN-01` — Runtime local de start/join com isolamento

**Prazo:** 21/10/2026 · **Prioridade:** P0 · **Estimativa:** 7 h · **Estado inicial:** BACKLOG

**Eixo responsável:** C. **Nome humano:** a confirmar com a equipe.

**Dependências:** `CON-01`.

**Entrega objetiva:** Funções registry, args isolados, handles e resultados

**Critério de aceite:** `start` retorna sem aguardar tarefa; `join` aguarda e coleta resultado/erro em testes C++ isolados.

**Escopo de arquivos autorizado:** `runtime/`.

**Evidência mínima de conclusão:** PR/commit associado, comandos e saídas do teste ou artefato documental revisado, status real PASS/FAIL/BLOCKED, e handoff ao consumidor.

**Antes de iniciar:** confirmar que todos os contratos consumidos estão congelados ou existe fixture/mock aprovado. Nunca tocar arquivos de outro eixo por conveniência.

#### `RUN-02` — Protocolo TCP robusto e worker pré-compilado

**Prazo:** 22/10/2026 · **Prioridade:** P0 · **Estimativa:** 8 h · **Estado inicial:** BACKLOG

**Eixo responsável:** C. **Nome humano:** a confirmar com a equipe.

**Dependências:** `CON-01`.

**Entrega objetiva:** framing, send_all/recv_exact, IDs, compatibilidade build, falhas

**Critério de aceite:** Fragmentação, frame inválido, worker indisponível e duas tarefas fora de ordem testados.

**Escopo de arquivos autorizado:** `runtime/`.

**Evidência mínima de conclusão:** PR/commit associado, comandos e saídas do teste ou artefato documental revisado, status real PASS/FAIL/BLOCKED, e handoff ao consumidor.

**Antes de iniciar:** confirmar que todos os contratos consumidos estão congelados ou existe fixture/mock aprovado. Nunca tocar arquivos de outro eixo por conveniência.

#### `RUN-03` — Prova de execução em dois computadores reais

**Prazo:** 23/10/2026 · **Prioridade:** P0 · **Estimativa:** 5 h · **Estado inicial:** BACKLOG

**Eixo responsável:** C. **Nome humano:** a confirmar com a equipe.

**Dependências:** `RUN-02`, `SET-03`.

**Entrega objetiva:** Coordinator/worker em hosts diferentes com cálculo e logs

**Critério de aceite:** Provar IPs distintos e cálculo remoto verdadeiro; join com timeout quando worker cai.

**Escopo de arquivos autorizado:** `runtime/`, `docs/evidencias/`.

**Evidência mínima de conclusão:** PR/commit associado, comandos e saídas do teste ou artefato documental revisado, status real PASS/FAIL/BLOCKED, e handoff ao consumidor.

**Antes de iniciar:** confirmar que todos os contratos consumidos estão congelados ou existe fixture/mock aprovado. Nunca tocar arquivos de outro eixo por conveniência.

#### `RUN-04` — Handoff de API runtime e integração com backend A

**Prazo:** 26/10/2026 · **Prioridade:** P0 · **Estimativa:** 4 h · **Estado inicial:** BACKLOG

**Eixo responsável:** C. **Nome humano:** a confirmar com a equipe.

**Dependências:** `RUN-01`, `RUN-03`, `CORE-05`.

**Entrega objetiva:** Header/build e testes interoperáveis com C++ gerado

**Critério de aceite:** A integra `start/join` em CORE-07; teste simples local/remoto passa sem mexer `src/` via C.

**Escopo de arquivos autorizado:** `runtime/`, `docs/`.

**Evidência mínima de conclusão:** PR/commit associado, comandos e saídas do teste ou artefato documental revisado, status real PASS/FAIL/BLOCKED, e handoff ao consumidor.

**Antes de iniciar:** confirmar que todos os contratos consumidos estão congelados ou existe fixture/mock aprovado. Nunca tocar arquivos de outro eixo por conveniência.

#### `T08-01` — MiniPar T08: 160 avaliações em quatro trabalhadores

**Prazo:** 27/10/2026 · **Prioridade:** P0 · **Estimativa:** 6 h · **Estado inicial:** BACKLOG

**Eixo responsável:** C. **Nome humano:** a confirmar com a equipe.

**Dependências:** `RUN-04`, `CORE-07`.

**Entrega objetiva:** Programa completo e resultado agregado correto

**Critério de aceite:** 40×4=160, sem perda/duplicata, quatro workers, sequência/paralelo comparados corretamente.

**Escopo de arquivos autorizado:** `tests/2026_2/test08/`.

**Evidência mínima de conclusão:** PR/commit associado, comandos e saídas do teste ou artefato documental revisado, status real PASS/FAIL/BLOCKED, e handoff ao consumidor.

**Antes de iniciar:** confirmar que todos os contratos consumidos estão congelados ou existe fixture/mock aprovado. Nunca tocar arquivos de outro eixo por conveniência.

#### `T09-01` — MiniPar T09: avaliadores + Mandelbrot ASCII

**Prazo:** 29/10/2026 · **Prioridade:** P0 · **Estimativa:** 6 h · **Estado inicial:** BACKLOG

**Eixo responsável:** C. **Nome humano:** a confirmar com a equipe.

**Dependências:** `T08-01`.

**Entrega objetiva:** Cinco trabalhos, impressão ASCII e resultados de avaliações

**Critério de aceite:** 160 avaliações; fractal calculado dinamicamente; cinco tarefas sincronizadas.

**Escopo de arquivos autorizado:** `tests/2026_2/test09/`.

**Evidência mínima de conclusão:** PR/commit associado, comandos e saídas do teste ou artefato documental revisado, status real PASS/FAIL/BLOCKED, e handoff ao consumidor.

**Antes de iniciar:** confirmar que todos os contratos consumidos estão congelados ou existe fixture/mock aprovado. Nunca tocar arquivos de outro eixo por conveniência.

#### `T10-01` — MiniPar T10: avaliações + Mandelbrot + Sierpinski

**Prazo:** 30/10/2026 · **Prioridade:** P0 · **Estimativa:** 7 h · **Estado inicial:** BACKLOG

**Eixo responsável:** C. **Nome humano:** a confirmar com a equipe.

**Dependências:** `T09-01`.

**Entrega objetiva:** Seis trabalhos planejados e fractais visualmente verificáveis

**Critério de aceite:** Fractais produzidos; trabalho Sierpinski realmente integrado ao modelo; documentar divergência da referência Python.

**Escopo de arquivos autorizado:** `tests/2026_2/test10/`.

**Evidência mínima de conclusão:** PR/commit associado, comandos e saídas do teste ou artefato documental revisado, status real PASS/FAIL/BLOCKED, e handoff ao consumidor.

**Antes de iniciar:** confirmar que todos os contratos consumidos estão congelados ou existe fixture/mock aprovado. Nunca tocar arquivos de outro eixo por conveniência.

#### `RUN-05` — Benchmarks e falhas distribuídas repetíveis

**Prazo:** 31/10/2026 · **Prioridade:** P0 · **Estimativa:** 4 h · **Estado inicial:** BACKLOG

**Eixo responsável:** C. **Nome humano:** a confirmar com a equipe.

**Dependências:** `T10-01`, `RUN-03`.

**Entrega objetiva:** Tempos justos, speedup, registro de hosts e falhas

**Critério de aceite:** Cargas sequencial/paralela equivalentes; relatório sem confundir workers com núcleos físicos.

**Escopo de arquivos autorizado:** `tests/2026_2/`, `docs/evidencias/`.

**Evidência mínima de conclusão:** PR/commit associado, comandos e saídas do teste ou artefato documental revisado, status real PASS/FAIL/BLOCKED, e handoff ao consumidor.

**Antes de iniciar:** confirmar que todos os contratos consumidos estão congelados ou existe fixture/mock aprovado. Nunca tocar arquivos de outro eixo por conveniência.

#### `RUN-06` — Documentar protocolo, topologia, deploy e testes

**Prazo:** 02/11/2026 · **Prioridade:** P0 · **Estimativa:** 4 h · **Estado inicial:** BACKLOG

**Eixo responsável:** C. **Nome humano:** a confirmar com a equipe.

**Dependências:** `RUN-05`.

**Entrega objetiva:** README runtime, diagrama e evidências de duas máquinas

**Critério de aceite:** Outro integrante reproduz dois PCs seguindo instruções; logs sem dados pessoais.

**Escopo de arquivos autorizado:** `runtime/`, `docs/`.

**Evidência mínima de conclusão:** PR/commit associado, comandos e saídas do teste ou artefato documental revisado, status real PASS/FAIL/BLOCKED, e handoff ao consumidor.

**Antes de iniciar:** confirmar que todos os contratos consumidos estão congelados ou existe fixture/mock aprovado. Nunca tocar arquivos de outro eixo por conveniência.

#### `INT-01` — Smoke de integração 3 eixos antes do fechamento

**Prazo:** 28/10/2026 · **Prioridade:** P0 · **Estimativa:** 3 h · **Estado inicial:** BACKLOG

**Eixo responsável:** C. **Nome humano:** a confirmar com a equipe.

**Dependências:** `CORE-07`, `WEB-03`, `RUN-04`.

**Entrega objetiva:** Coordenação de smoke da integração; A valida alterações de interfaces do núcleo

**Critério de aceite:** Teste único ponta a ponta reproduzível, resultados anexados, defeitos classificados.

**Escopo de arquivos autorizado:** `docs/auditorias/`, `tests/`, `scripts/`.

**Evidência mínima de conclusão:** PR/commit associado, comandos e saídas do teste ou artefato documental revisado, status real PASS/FAIL/BLOCKED, e handoff ao consumidor.

**Antes de iniciar:** confirmar que todos os contratos consumidos estão congelados ou existe fixture/mock aprovado. Nunca tocar arquivos de outro eixo por conveniência.

#### `DOC-03` — Product Backlog, Sprint Backlogs e decisões atualizados

**Prazo:** 02/11/2026 · **Prioridade:** P0 · **Estimativa:** 2 h · **Estado inicial:** BACKLOG

**Eixo responsável:** C. **Nome humano:** a confirmar com a equipe.

**Dependências:** `INT-01`.

**Entrega objetiva:** Atualizar Product/Sprint Backlogs e decisões com insumos dos três eixos

**Critério de aceite:** Corresponde ao desenvolvimento feito, sem declarar resultado inexistente.

**Escopo de arquivos autorizado:** `docs/`, `planning/`.

**Evidência mínima de conclusão:** PR/commit associado, comandos e saídas do teste ou artefato documental revisado, status real PASS/FAIL/BLOCKED, e handoff ao consumidor.

**Antes de iniciar:** confirmar que todos os contratos consumidos estão congelados ou existe fixture/mock aprovado. Nunca tocar arquivos de outro eixo por conveniência.

### Contrato conjunto A e B

#### `CON-02` — Congelar contrato serviço de fases para a Web

**Prazo:** 18/10/2026 · **Prioridade:** P0 · **Estimativa:** 2 h · **Estado inicial:** BACKLOG

**Eixo responsável:** A+B. **Nome humano:** a confirmar com a equipe.

**Dependências:** `SET-01`.

**Entrega objetiva:** Esquema tokens, AST, símbolos, TAC, C++, compile/run/download

**Critério de aceite:** A e B aprovam fixture de sucesso e três erros; Web poderá usar mocks.

**Escopo de arquivos autorizado:** `docs/02_CONTRATOS_TECNICOS.md`.

**Evidência mínima de conclusão:** PR/commit associado, comandos e saídas do teste ou artefato documental revisado, status real PASS/FAIL/BLOCKED, e handoff ao consumidor.

**Antes de iniciar:** confirmar que todos os contratos consumidos estão congelados ou existe fixture/mock aprovado. Nunca tocar arquivos de outro eixo por conveniência.

#### `CON-03` — Congelar recursos mínimos Teste 11 e saída ARM

**Prazo:** 18/10/2026 · **Prioridade:** P0 · **Estimativa:** 2 h · **Estado inicial:** BACKLOG

**Eixo responsável:** A+B. **Nome humano:** a confirmar com a equipe.

**Dependências:** `SET-01`.

**Entrega objetiva:** Contrato strings/listas/T11, estratégia arquivo `.arm` e CPUlator

**Critério de aceite:** A e B aprovam programas de prova com oráculo e responsabilidades.

**Escopo de arquivos autorizado:** `docs/02_CONTRATOS_TECNICOS.md`.

**Evidência mínima de conclusão:** PR/commit associado, comandos e saídas do teste ou artefato documental revisado, status real PASS/FAIL/BLOCKED, e handoff ao consumidor.

**Antes de iniciar:** confirmar que todos os contratos consumidos estão congelados ou existe fixture/mock aprovado. Nunca tocar arquivos de outro eixo por conveniência.

### Contrato conjunto A e C

#### `CON-01` — Congelar contrato de Fork/Join e destino local/remoto

**Prazo:** 18/10/2026 · **Prioridade:** P0 · **Estimativa:** 3 h · **Estado inicial:** BACKLOG

**Eixo responsável:** A+C. **Nome humano:** a confirmar com a equipe.

**Dependências:** `SET-01`.

**Entrega objetiva:** BNF proposta e API runtime aprovadas, tipos/handles/erros delimitados

**Critério de aceite:** A e C aprovam contrato; exemplos/fixtures; mudança via CR; pendências registradas.

**Escopo de arquivos autorizado:** `docs/02_CONTRATOS_TECNICOS.md`.

**Evidência mínima de conclusão:** PR/commit associado, comandos e saídas do teste ou artefato documental revisado, status real PASS/FAIL/BLOCKED, e handoff ao consumidor.

**Antes de iniciar:** confirmar que todos os contratos consumidos estão congelados ou existe fixture/mock aprovado. Nunca tocar arquivos de outro eixo por conveniência.

### Trio — estudo e entrega

#### `EST-01` — Estudo de módulos e roteiro individual

**Prazo:** 08/11/2026 · **Prioridade:** P0 · **Estimativa:** 4 h · **Estado inicial:** BACKLOG

**Eixo responsável:** EQUIPE. **Nome humano:** os três.

**Dependências:** `REL-01`.

**Entrega objetiva:** Três pessoas com roteiro e demonstrações compreendidas

**Critério de aceite:** Cada um explica seu eixo e fluxo completo; coordenador reserva tempo CG.

**Escopo de arquivos autorizado:** `docs/`.

**Evidência mínima de conclusão:** PR/commit associado, comandos e saídas do teste ou artefato documental revisado, status real PASS/FAIL/BLOCKED, e handoff ao consumidor.

**Antes de iniciar:** confirmar que todos os contratos consumidos estão congelados ou existe fixture/mock aprovado. Nunca tocar arquivos de outro eixo por conveniência.

#### `EST-02` — Ensaio completo e contingência de demo

**Prazo:** 10/11/2026 · **Prioridade:** P0 · **Estimativa:** 3 h · **Estado inicial:** BACKLOG

**Eixo responsável:** EQUIPE. **Nome humano:** os três.

**Dependências:** `EST-01`.

**Entrega objetiva:** Ensaio de ponta a ponta, video/log backup, falas

**Critério de aceite:** Cada aluno apresenta e responde conceitos; dois computadores/CPUlator testados.

**Escopo de arquivos autorizado:** `docs/`.

**Evidência mínima de conclusão:** PR/commit associado, comandos e saídas do teste ou artefato documental revisado, status real PASS/FAIL/BLOCKED, e handoff ao consumidor.

**Antes de iniciar:** confirmar que todos os contratos consumidos estão congelados ou existe fixture/mock aprovado. Nunca tocar arquivos de outro eixo por conveniência.

#### `ENT-01` — Entrega final 11/11

**Prazo:** 11/11/2026 · **Prioridade:** P0 · **Estimativa:** 2 h · **Estado inicial:** BACKLOG

**Eixo responsável:** EQUIPE. **Nome humano:** os três.

**Dependências:** `EST-02`.

**Entrega objetiva:** GitHub, relatório, programas, executáveis e apresentações

**Critério de aceite:** Links conferidos, arquivos entregues, sistema demonstrável e documentação coerente.

**Escopo de arquivos autorizado:** `docs/`, `README.md`.

**Evidência mínima de conclusão:** PR/commit associado, comandos e saídas do teste ou artefato documental revisado, status real PASS/FAIL/BLOCKED, e handoff ao consumidor.

**Antes de iniciar:** confirmar que todos os contratos consumidos estão congelados ou existe fixture/mock aprovado. Nunca tocar arquivos de outro eixo por conveniência.

---

## Instrução de atualização

Durante a fase pré-Issues, atualize `planning/cards.json` e regenere este Markdown; **não mantenha dois backlogs divergentes**. Quando as Issues forem publicadas, o board será a fonte de verdade de estado e responsável, enquanto os contratos e os gate dates permanecem nos docs. Nunca marque `DONE` sem validação correspondente.
