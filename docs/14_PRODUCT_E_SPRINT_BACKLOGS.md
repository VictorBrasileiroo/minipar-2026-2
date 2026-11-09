# Product Backlog e Sprint Backlogs — MiniPar 2026.2

**Card:** `DOC-03` (Eixo C) · **Estado conferido em:** 09/11/2026, `dev` em `8d07433` (REL-PRE autorizado pelo coordenador) · **Fonte estruturada:** [`planning/cards.json`](../planning/cards.json) v0.3
**Exigência:** relatório final, itens "Product Backlog" e "Sprint Backlog" (doc 00 §12.1; doc 11).

Regras deste documento:

- O estado de cada card vem do Git: **`DONE` só com PR mergeado em `dev` e evidência**. Recortes parciais ficam escritos ao lado do card.
- **Exceção única:** um card de configuração/coordenação que não produz artefato no repositório pode ficar `DONE` sem PR próprio, desde que cada critério de aceite tenha evidência verificável registrada na seção 2.1. Hoje isso vale só para o **SET-03**.
- Uma **Sprint** é um **marco** do planejamento ([`planning/MiniPar_2026_2_Marcos_de_Entrega.md`](../planning/MiniPar_2026_2_Marcos_de_Entrega.md)): prazo único por marco, status e dependências por card.
- "Entregue em" é a data do merge do último PR do card. Uma data depois do prazo do marco é registrada como atraso, sem ajuste retroativo.
- A planilha de acompanhamento da equipe é um espelho; em divergência, valem o `cards.json` e o Git (ADR-006).

## 1. Product Backlog

O Product Backlog tem os itens de produto que o MiniPar 2026.2 precisa entregar (doc 00 e doc 01), ordenados por prioridade. Cada item é atendido por um ou mais cards.

| # | Item de produto (épico) | Prioridade | Cards | Estado em 09/11 |
|---|---|---|---|---|
| PB-01 | Base 2026.1 importada, ambiente reproduzível (Python + G++ C++20) | P0 | SET-01, SET-02, SET-03 | **Entregue** |
| PB-02 | Contratos entre eixos congelados: Fork/Join (C-FJ-v1), serviço Web (C-WEB-v1), Teste 11 (C-T11-v1) | P0 | CON-01, CON-02, CON-03 | **Entregue** |
| PB-03 | Compilador corrigido: TAC autêntico (sem hardcode), strings e coleções para o T11 | P0 | CORE-02, CORE-03 | **Entregue** |
| PB-04 | Linguagem com Fork/Join: BNF, Lexer/Parser/AST, semântico, TAC e backend C++ que chama o runtime | P0 | CORE-04, CORE-05, CORE-06, CORE-07 | **Entregue** |
| PB-05 | Runtime de tarefas local e remoto (TCP, worker pré-compilado, falhas explícitas) | P0 | RUN-01, RUN-02, RUN-04 | **Entregue** |
| PB-06 | Execução provada entre dois computadores reais | P0 | RUN-03, RUN-06 | **Parcial**: prova da demo feita (RUN-03); reprodução documentada por outro integrante pendente (RUN-06) |
| PB-07 | Programas paralelos T08, T09 e T10 em MiniPar, com oráculo | P0 | T08-01, T09-01, T10-01 | **Entregue** (T09/T10 com cenário remoto só no loopback; saída do Sierpinski depende da ADR-014) |
| PB-08 | Desempenho e falhas medidos de forma justa | P0 | RUN-05 | **Parcial**: #36 integrado em 06/11; medido numa máquina; cenário em dois PCs PENDING |
| PB-09 | Teste 11: MiniCompilador escrito em MiniPar, com ARMv7 validado no CPUlator | P0 | T11-01, T11-02, T11-03 | **Entregue** |
| PB-10 | Web didática com fases reais (tokens, AST, símbolos, TAC, C++), compilar, executar e baixar | P0 | WEB-01 a WEB-04, CORE-08 | **Entregue** |
| PB-11 | Interfaces antigas (terminal e Web 2026.1) preservadas | P0 | CORE-09 | **Entregue** (#35, 06/11) |
| PB-12 | Regressão: testes herdados T01–T07 e integração dos três eixos | P0 | CORE-01, CORE-10, INT-01, INT-02 | **Parcial**: baseline, regressão #38 e smoke integrados; DEF-01/02 corrigidos (#40/#41); INT-02 sem evidência disponível em 09/11 |
| PB-13 | Documentação: BNF, pseudocódigos, UML, backlogs, relatório | P0 | DOC-01 a DOC-04, WEB-05 | **Parcial**: BNF/pseudocódigos e seções da Web/T11 entregues; UML em revisão (#42); relatório completo sem PR; backlogs integrados (#39) |
| PB-14 | Release candidata, estudo e entrega final | P0 | REL-01, EST-01, EST-02, ENT-01 | **Não iniciado** |

**Defeitos e pendências no Product Backlog** (estado atualizado em 09/11; detalhes no [CORE-10](auditorias/CORE-10_REGRESSAO_FINAL_T01_T07.md)):

| ID | Defeito | Severidade | Dono sugerido |
|---|---|---|---|
| DEF-01 | DONE: correção #40 integrada e aprovada; T01 10/10 PASS em REL-PRE (loopback) | P1 | Eixo A (CORE-09 ou card novo) |
| DEF-02 | DONE: correção #41 integrada e aprovada; T02 10/10 PASS em REL-PRE | P2 | Eixo A |
| T04-TOL | Falta a tolerância numérica do T04 (XOR) | — | A + C |

## 2. Sprint Backlogs

### Sprint 1 — Marco 1 (16/10 a 22/10)

**Meta:** projeto reproduzível, contratos definidos, strings para o T11, gramática de Fork/Join iniciada, UI com AST simulada, MiniCompilador mínimo e infraestrutura de worker.

| Card | Eixo | Entrega | Estado | PR | Entregue em |
|---|---|---|---|---|---|
| SET-01 | A | Estrutura e importação da base 2026.1 | DONE | #1 | 17/10 |
| SET-02 | A | Python e G++20; smoke | DONE | #1 | 17/10 |
| SET-03 | A | Permissões Git, responsáveis, acesso a dois PCs | DONE (exceção sem PR, §2.1) | — | sem data de merge; evidências de 17/10 a 04/11 |
| CON-01 | A+C | Contrato Fork/Join C-FJ-v1 | DONE | #7 | 26/10 (atraso) |
| CON-02 | A+B | Contrato do serviço Web C-WEB-v1 | DONE | #3, #25 | 22/10 (`FROZEN` registrado em 05/11) |
| CON-03 | A+B | Contrato do Teste 11 C-T11-v1 | DONE | #2, #25 | 22/10 (`FROZEN` registrado em 05/11) |
| CORE-01 | C | Baseline T01–T07 | DONE | #6 | 23/10 (atraso de 1 dia) |
| CORE-03 | A | Strings e coleções para o T11 | DONE | #14 | 28/10 (atraso) |
| CORE-04 | A | BNF, tokens e AST de Fork/Join | DONE | #15 | 29/10 (atraso) |
| WEB-01 | B | Wireframe e fixtures | DONE | #12 | 23/10 (atraso de 1 dia) |
| WEB-02 | B | AST interativa e painéis | DONE | #13 | 23/10 (atraso de 1 dia) |
| T11-01 | B | MVP do MiniCompilador | DONE | #26 | 04/11 (atraso) |
| RUN-01 | C | Runtime local start/join | DONE | #8 | 26/10 (atraso) |
| RUN-02 | C | Protocolo TCP e worker | DONE | #9 | 26/10 (atraso) |
| RUN-03 | C | Prova em dois computadores | DONE | #10 | 04/11 (atraso) |

**Resultado:** 15/15 cards concluídos (o SET-03 pela exceção da §2.1), 4 dentro do prazo do marco (SET-01, SET-02, CON-02, CON-03). Os PRs do Eixo C (#7–#10) foram abertos em 22/10 e esperaram a revisão do contrato C-FJ-v1 até 26/10; o RUN-03 dependeu de duas máquinas disponíveis ao mesmo tempo (04/11).

#### 2.1 Exceção: SET-03 aceito sem PR próprio

O SET-03 é de configuração e coordenação: dar acesso ao repositório, nomear os responsáveis, combinar o fluxo de branches e garantir duas máquinas. Nada disso gera arquivo no repositório, então não há PR para mergear. O aceite se apoia nas evidências abaixo, conferidas em 06/11/2026 (revisão do #39):

| Critério de aceite do card | Evidência | Situação |
|---|---|---|
| Trio com acesso ao repositório | `gh api .../collaborators`: VictorBrasileiroo (admin), erasmossj (write), JoseRiquelmeTds (write). PRs mergeados por autor: Victor 9, Riquelme 14, Erasmo 12 | **atendido** |
| Responsáveis B/C nomeados | Eixo B = Riquelme, Eixo C = Erasmo, registrados nos contratos (`02_CONTRATOS_TECNICOS.md`, quadros de aprovação de CON-01/02/03) e na autoria dos PRs de cada eixo | **atendido** |
| Branches | `dev` como branch padrão e branches `eixo-<a\|b\|c>/<ID>-…` (ADR-019, PR #4, 22/10); os PRs de card seguem o padrão, exceto o #1 (`setup/…`, 17/10, anterior à regra); #4 e #5 são de documentação geral | **atendido** |
| Proteção de branch "quando viável" | Revisão obrigatória por outra pessoa (ADR-019): desde o #4, os 33 PRs mergeados tiveram aprovação; só #1 e #5 (17 e 19/10, antes da regra) entraram sem. A configuração de proteção no GitHub **não é legível** com permissão de escrita (a API exige admin): fica a cargo do coordenador confirmar | **atendido pela prática**; configuração não conferida pelo Eixo C |
| Hosts de rede definidos (dois PCs) | Execução real entre duas máquinas no RUN-03 (04/11), com log do worker anexado (`docs/evidencias/RUN-03_DOIS_COMPUTADORES.md`) | **atendido** |
| Trio confirma horas | Sem registro escrito no repositório | **não documentado**: o coordenador confirma ao aprovar este PR |

Divergência registrada, sem efeito no estado do card: o entregável fala em "repositório **privado**", mas em 06/11 o repositório está público (ver ADR-018 em `03_DECISOES.md`).

### Sprint 2 — Marco 2 (23/10 a 29/10)

**Meta:** T08 ponta a ponta, Web consumindo a API real, Teste 11 obrigatório validado.

| Card | Eixo | Entrega | Estado | PR | Entregue em |
|---|---|---|---|---|---|
| CORE-02 | A | TAC autêntico e T07 seguro | DONE | #16 | 29/10 |
| CORE-05 | A | Semântico de Fork/Join | DONE | #15 | 29/10 |
| CORE-07 | A | C++ que chama o runtime | DONE | #18, #29 | 05/11 (atraso) |
| CORE-08 | A | Serviço de fases para a Web | DONE | #19, #34 | 03/11 (atraso; catálogo v1.1 em 05/11) |
| WEB-03 | B | Web no serviço real | DONE | #30 | 05/11 (atraso) |
| WEB-04 | B | Compilar, executar e baixar | DONE | #31 | 05/11 (atraso) |
| T11-02 | B | Semântica, símbolos e ARM do T11 | DONE | #27 | 04/11 (atraso) |
| T11-03 | B | `.arm` no CPUlator | DONE | #28 | 04/11 (atraso) |
| RUN-04 | C | Handoff da API do runtime | DONE | #20 | 05/11 (atraso) |
| T08-01 | C | Teste 8: 160 avaliações | DONE | #21 | 05/11 (atraso) |
| T09-01 | C | Teste 9: Mandelbrot | DONE (PARTIAL: remoto no loopback) | #22 | 05/11 (atraso) |
| T10-01 | C | Teste 10: dois fractais | DONE (PARTIAL: loopback + ADR-014) | #23 | 05/11 (atraso) |
| INT-01 | C | Smoke dos três eixos | DONE | #24 | 05/11 (atraso) |

**Resultado:** 13/13 cards concluídos, 2 dentro do prazo (CORE-02, CORE-05). O caminho crítico foi o CORE-07 (#18): os PRs de RUN-04, T08–T10 e INT-01 foram abertos em 30/10, validados numa integração local, e só puderam entrar em `dev` depois dele (05/11).

### Sprint 3 — Marco 3 (30/10 a 03/11)

**Meta:** T01–T11 e três interfaces demonstrados ou com falhas registradas; documentação e release candidata.

| Card | Eixo | Entrega | Estado em 09/11 | PR |
|---|---|---|---|---|
| CORE-06 | A | TAC de Fork/Join e `par` | DONE | #17 (05/11) |
| WEB-05 | B | Documentação da Web e do T11 | DONE | #33 (05/11) |
| DOC-01 | B | BNF final e pseudocódigos | DONE | #32 (05/11) |
| CORE-10 | C | Regressão final T01–T07 | DONE (relatório; T04 PARTIAL) | #38 (06/11) |
| RUN-05 | C | Benchmarks e falhas | IN_PROGRESS / PARTIAL (`par_rede` PENDING) | #36 integrado (06/11) |
| RUN-06 | C | Protocolo, topologia, deploy | IN_PROGRESS (reprodução PENDING) | #37 integrado (06/11) |
| DOC-03 | C | Product/Sprint Backlogs e decisões | DONE | #39 (06/11) |
| CORE-09 | A | Interfaces antigas preservadas | DONE | #35 (06/11) |
| INT-02 | B | Regressão integral e rede real | BACKLOG (CORE-10 integrado; sem PR até 09/11) | — |
| DOC-02 | B | UML | IN_REVIEW (parecer A em REL-PRE; review C pendente) | #42 |
| DOC-04 | B | Relatório completo | BACKLOG (depende de DOC-02, DOC-03, INT-02, RUN-06) | — |
| REL-01 | A | Release candidata | BACKLOG (depende do DOC-04) | — |

**Resultado em 09/11:** 6/12 concluídos; RUN-05/06 têm PR integrado com aceite parcial; DOC-02 está em revisão; INT-02, DOC-04 e REL-01 permanecem no backlog. O prazo original de 03/11 não foi reescrito. Ordem pelas dependências: CORE-10 → INT-02; DOC-02 e RUN-06 → DOC-04 → REL-01.

### Sprint 4 — Estudo e entrega (04/11 a 11/11)

| Card | Eixo | Entrega | Prazo | Estado |
|---|---|---|---|---|
| EST-01 | Trio | Estudo de módulos e roteiro individual | 08/11 | BACKLOG (depende do REL-01) |
| EST-02 | Trio | Ensaio completo e contingência de demo | 10/11 | BACKLOG |
| ENT-01 | Trio | Entrega final | 11/11 | BACKLOG |

Ver [REL-PRE](auditorias/REL-PRE_FECHAMENTO_EIXO_A.md) para medições posteriores a DEF-01/02, decisões e dependências externas. Os resultados antigos não foram apagados.

## 3. Observações do processo

- **Revisão como gargalo.** A regra de um revisor que não é o autor (ADR-019) e o merge em pilha (RUN-04 → T08 → T09 → T10) fizeram vários cards prontos esperarem dias pela revisão de uma dependência. A integração local antecipada (Eixo C, 30/10) achou defeitos de integração antes do merge.
- **Prova em rede depende de agenda.** As provas com duas máquinas (RUN-03 em 04/11; RUN-05 `par_rede` e RUN-06 pendentes) exigem duas pessoas e duas máquinas ao mesmo tempo. Convém juntá-las numa sessão só.
- **Planilha × Git.** Em 05/11 a planilha ainda mostrava como "Planejado" cards de A e B já mergeados. Este documento e o `cards.json` seguem o Git.

## 4. Como atualizar

1. Alterar `status`, `pr_url`, `evidence` e, se preciso, `status_note` em `planning/cards.json`.
2. `python scripts/validar_planejamento.py`.
3. Atualizar as tabelas deste documento e a seção "Estado em …" de `docs/04_BACKLOG.md`.
4. Nunca marcar `DONE` sem PR mergeado e evidência (04_BACKLOG, "Instrução de atualização"). Uma nova exceção sem PR só entra com a mesma tabela da §2.1, critério por critério, e aprovação do coordenador.
