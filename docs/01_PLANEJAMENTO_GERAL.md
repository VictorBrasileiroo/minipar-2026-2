# Planejamento Geral de Execução — MiniPar 2026.2

> **DOCUMENTO OPERACIONAL PRINCIPAL — v0.1 (15/10/2026).**
> Use este arquivo para decidir **o que fazer, em qual ordem, quando, quem pode começar e como validar**.
> Os requisitos do professor estão consolidados em `00_DOCUMENTO_MESTRE_INICIAL.md`. Este plano **não altera** o enunciado.
>
> **Estado:** proposta detalhada pronta para revisão dos três integrantes; NÃO inicia implementação automaticamente.
> **Prazo oficial:** 11/11/2026. **Código funcional congelado:** 03/11. **Estudo:** 04–10/11.

---

## 1. Missão e definição de sucesso

Evoluir o MiniPar 2026.1 com compilação real (Lexer → Parser/AST → semântico/símbolos; AST → TAC e AST → C++ → G++ → binário), preservando testes 1–7; implementar Fork/Join local e distribuído via comunicação por mensagens; implementar testes 8–11; manter terminal e Web anterior e acrescentar Web didática; entregar BNF/UML/pseudocódigos, backlogs, relatório, testes e evidências.

**Sucesso verificável =** programa MiniPar de entrada gera artefatos verdadeiros e executável; resultados comparados com oráculos; tarefas paralelas/distribuídas comprovadas; Teste 11 **escrito em MiniPar** gera `.arm` validado no CPUlator; três interfaces acessíveis; documentos condizentes com código; trio sabe defender as partes.

**Não é sucesso:** arquivos existem sem execução, resultados fixos, apenas localhost rotulado como distribuído, `exit=0` sem resultado correto, ARM textual não executado, promessa de funcionalidade futura.

### 1.2 Estados de trabalho e regras de liberação

`BACKLOG` (proposto) → `READY` (contratos + dependências atendidas) → `IN_PROGRESS` (branch com dono) → `IN_REVIEW` (testes/evidências + PR) → `DONE` (integrado e validado).

Se faltar contrato/recurso, usar `BLOCKED` (marcação auxiliar, explicando causa/dono/data de reavaliação); jamais fingir que está em progresso. Um card com mock aprovado pode começar enquanto a dependência real não terminou, **somente se o contrato de dados estiver congelado**.

**Definition of Ready (DoR)** — autoriza iniciar:
1. Objetivo e resultado observável.
2. Dono humano + agente responsável.
3. Arquivos permitidos e proibidos.
4. Dependências concluídas ou mock documentado.
5. Contratos aprovados, incluindo tipos/erros.
6. Critérios de aceite verificáveis e comando planejado de teste.
7. Prazo e evidência de entrega.

**Definition of Done (DoD)** — autoriza concluir:
1. PR revisado, sem tocar componentes de outro eixo sem aprovação.
2. Testes executados com logs e oráculos; regressão relevante aprovada.
3. Casos de erro relevantes verificados.
4. Integração com consumidores comprovada, não apenas interface inventada.
5. Documentação necessária atualizada e citações do código real.
6. Handoff e evidência anexados; sem bloqueios ocultos.
7. `dev` integra alterações sem regressão conhecida não registrada.

---

## 2. Estrutura organizacional dos três eixos

### Eixo A — Núcleo do compilador e integração central (**responsável: coordenador**)

**Missão:** manter o compilador correto e integrado, garantindo a tradução das novas construções sem quebrar programas herdados.

**Responsabilidade exclusiva principal:** `src/lexer.py`, `src/parser.py`, `src/ast_nodes.py`, `src/semantic.py`, `src/tac.py`, `src/codegen.py`, `src/cpp_template.py` (exceto runtime extraído acordado), `main.py`, CLI antiga, `app.py` e templates originais; BNF e adaptação de API central.

**Entregas:** toolchain reprodutível; correções decorrentes da regressão 1–7 executada pelo C; correção do TAC especial do Quicksort e bug da pilha no programa de teste; suporte coerente a strings/coleções exigidas; novos nós semânticos; Fork/Join traduzido a APIs do runtime; serviço de fases consumido pela Web; orientação de integração; documentação do núcleo.

**Fronteira:** A **não implementa sozinho** runtime remoto do C nem interface didática do B. Ao receber um pedido para alterar sua API, registra CR e devolve contrato, em vez de deixar colegas reescreverem `src/`.

**Orçamento sugerido:** ~2h/dia de entrega central + ~1h/dia para review, integração e comunicação; não tentar executar todas as tarefas centrais simultaneamente. Se tarefas A ultrapassarem 57h, replanejar o volume antes de aceitar o compromisso.

### Eixo B — Web didática + Teste 11 (**responsável: A DEFINIR**)

**Missão:** desenvolver uma nova interface educativa independente e implementar em MiniPar o MiniCompilador de expressões, validado no CPUlator.

**Propriedade:** `web_didatica/`, `tests/2026_2/test11/`, artefatos/documentação desses módulos. B solicita serviço de compilação ao A, não edita `src/` diretamente.

**Entregas:** Web com editor, tokens, AST visual, semântico/símbolos, TAC, C++, compilar/baixar, executar; integração com API real; documentação e prints; MiniCompilador MiniPar com tokenização/AST/TAC/símbolos/ARM; três expressões obrigatórias; `.arm` executado no CPUlator. **Também consolida BNF/pseudocódigos/UML a partir das evidências dos responsáveis, coordena a regressão final e edita o relatório (sem inventar informações dos outros eixos).**

**Independência inicial:** Web desenvolvida com fixtures JSON de contrato; Teste 11 parte da **prova MiniPar** da auditoria em cópia isolada, com dependências de strings registradas ao A. Pode emitir ARM em arquivo usando executor **provisoriamente**, sujeito a confirmação de exigência.

**Risco:** Web + Teste 11 são dois produtos. Se B tiver poucas horas, revisar cedo o escopo cosmético e concentrar esforço no teste 11 e nos controles exigidos.

### Eixo C — Runtime paralelo/distribuído + testes 8–10 (**responsável: A DEFINIR**)

**Missão:** fornecer biblioteca invocável pelo código C++ gerado, coordenando tarefas reais local e remotamente e entregando programas/exemplos de 4/5/6 trabalhadores.

**Propriedade:** `runtime/` e `tests/2026_2/test08/`, `test09/`, `test10/` e documentação própria. **Não edita `src/` sem contrato de mudança.**

**Entregas:** API local para iniciar/juntar tarefas; isolamento explícito; registro de funções de worker; socket com framing e leitura/escrita completas; coordenador e worker remoto pré-compilado; timeout/erros; prova em **duas máquinas**; 160 avaliações, Mandelbrot ASCII e Sierpinski visual; benchmarks justos e evidências. **Coordena QA de baseline e regressão 1–7 sem alterar `src/`, smoke inicial de integração e atualização de backlogs/decisões.**

**Independência inicial:** testar biblioteca diretamente em C++ com worker mock/precompilado. Somente A integra a API em `codegen.py`. A execução real do teste MiniPar dependerá da integração INT.

---

## 3. Controle de sobreposição e política de PR

**Invariante:** nunca dois agentes editando a mesma área de responsabilidade simultaneamente.

| Área | Escreve | Pode ler/usar | Como pedir mudança |
|---|---|---|---|
| `src/`, entrada/Flask originais, `tests/` herdados | A | Todos | CR em `docs/03_DECISOES.md` + card de A |
| `runtime/`, testes 8–10 | C | A/B | API do runtime contratada |
| `web_didatica/`, Teste 11 | B | A/C | API de compilação contratada |
| `legacy/` | Ninguém | Todos | Arquivo histórico, imutável |
| `AGENTS.md`, plano, contratos, cards | Coordenador após consulta | Todos | PR de documentação |
| `docs` específicos por eixo | Dono | Todos | Review técnico do eixo consumidor |

**Branches:** `eixo-a/CORE-XX-descricao`, `eixo-b/WEB-XX-descricao`, `eixo-c/RUN-XX-descricao`, `integracao/INT-XX-descricao`, `docs/DOC-XX-descricao`.

**Merge:** sempre via PR contra `dev`, a branch padrão do repositório, com **pelo menos uma aprovação de revisor diferente do autor**; não empurrar commits diretamente em `dev` nem em `main`. `main` não recebe PRs de card: promoção de `dev` para `main` só por decisão do coordenador. A coordenação não deve assumir que "PR sem conflito" implica "sem conflito semântico".

**Alteração de contrato:** PR do tipo `CR` com versão antiga/nova, dependentes impactados, plano de transição, fixtures e testes; só aplicar após anuência de A + consumidor.

---

## 4. Estratégia crítica: contratos ANTES de código novo

A ordem inicial não é "cada um abrir Codex". É **G0: congelar três contratos v0.1**:

1. **C-FJ — tarefas Fork/Join:** sintaxe MiniPar proposta, AST, chamadas geradas, `TaskSpec` e `TaskResult`, `join`, isolamento, destinos, framing e falhas. A consome API do C. **A e C aprovam**.
2. **C-WEB — fases do compilador:** estrutura de resposta para tokens, AST JSON hierárquica, símbolos, erros, TAC/C++, compilação e execução; endpoints. A fornece, B consome. **A e B aprovam**.
3. **C-T11 — recursos mínimos da linguagem para MiniCompilador:** `input`, `string`, `len`, `substr`, `to_string`, listas, operações matemáticas, saída e delimitação ARM. A fornece, B consome. **A e B aprovam**.

**Congelar contrato não significa implementar.** A partir do aceite, B e C podem utilizar fixtures/mocks da interface antes de A acabar suas alterações.

**Perguntas não resolvidas:** alocação remota automática vs workers coordenados; exportação `.arm` dentro vs fora de MiniPar; representação gráfica Sierpinski. Arquitetura proposta **não deve ser apresentada como interpretação definitiva do professor** até ser demonstrada/validada.

---

## 5. Marcos do calendário e gates de aceitação

As datas representam **prazo-limite de um resultado verificável**, não obrigação de trabalhar o dia inteiro. Cards específicos e dependências estão em `docs/04_BACKLOG.md` e `planning/cards.json`.

### M0 — 16 a 18/10 | Preparação, baseline e contratos (G0)

**A:** importar snapshot original, definir ambiente de C++20/compilação; analisar falhas da regressão 1–7 executada por C; registrar problemas já vistos (TAC fixo, vetor Teste 7, XOR etc.); aprovar gramática mínima Fork/Join e API de fases.

**B:** entender enunciado, estudar prova MiniPar da auditoria e código Java; fixar recursos mínimos Teste 11; desenhar wireframe Web; fixtures estruturadas.

**C:** estudar runtime/protocolo da prova da auditoria; propor funções e mensagens; implementar primeiro smoke isolado de worker/coordenador (sem `src/`), documentar protocolo. Executar baseline T01–T07 e reportar bugs ao A, sem alterar o núcleo.

**Saída obrigatória G0 (até 18/10):** repositório preparado, build reproduzível ou bloqueio nomeado, baseline real, contratos C-FJ/C-WEB/C-T11 **aprovados**, proprietários dos arquivos e responsáveis definidos, testes para provas verticais escritos.

**Se G0 falhar:** não liberar os três agentes em implementação irrestrita. Resolver contrato/build no dia seguinte, proteger as mudanças do núcleo.

### M1 — 19 a 23/10 | Provas verticais dos dois maiores riscos (G1)

**A:** compatibilizar toolchain; eliminar TAC hardcoded do T07; corrigir o acesso fora dos limites; corrigir strings essenciais/coleções; criar Lexer/Parser/AST/semântico Fork/Join mínimo; primeiro C++ chamando runtime local.

**B:** **prova vertical Teste 11:** expression `((2+4)*7)-(5*4)` analisada por MiniCompilador escrito em MiniPar, produzindo tokens, árvore, TAC, símbolos/estado de símbolos, `.arm`; executar no CPUlator o **quanto antes**, mesmo antes dos detalhes da Web; interface didática estática com fixtures.

**C:** biblioteca local + `join` verdadeiro; coordenador/worker com mensagens identificadas; primeira prova em **dois computadores**, não apenas localhost, com tarefa e erro por queda do worker.

**Saída G1 até 23/10:** (1) Teste 11 demonstrado em recorte real com ARM validado no CPUlator ou bloqueio tecnicamente preciso; (2) Fork/Join gerando tarefa de MiniPar e executando ao menos localmente; (3) rede em duas máquinas com worker real comprovada, mesmo que ainda sem MiniPar completo; (4) T01–T07 com regressão documentada. É um **marco de redução de risco**, não final de funcionalidade.

**Alerta crítico:** se C não provar computação remota identificável até 23/10, **abrir plano de contingência imediatamente**. Não adiar a primeira prova remota para 31/10.

### M2 — 24 a 28/10 | Funcionalidades completas e primeiras integrações (G2)

**A:** finalizar comandos Fork/Join em Parser/AST/semântico/TAC/C++; API de fases real; revisar regressões; integração contínua com C e B.

**B:** completar MiniCompilador (expressões obrigatórias, tabela de símbolos, exportação `.arm`, ARM validado, erros); conectar Web a tokens/AST/semântico/TAC/C++; download/executar.

**C:** integrar runtime real à geração C++ via PR de A; implementar T08 (160 avaliações, 4 trabalhadores), T09 (+ Mandelbrot), T10 (+ Sierpinski), com resultados, comparação sequencial/paralela e falhas.

**Saída G2 até 28/10:** pelo menos T08 completo MiniPar → C++ → execução → resultados; Teste 11 completo nos exemplos obrigatórios, com CPUlator; Web didática conectada em ao menos um exemplo; demonstração remota integrada em andamento e repetível.

**Se G2 falhar:** parar melhorias de interface/benchmark cosmético; resolver primeiro compilação, Fork/Join remoto e Teste 11. B não deve tentar corrigir `src/` diretamente; reportar card para A.

### M3 — 29 a 31/10 | Fechar escopo técnico (G3)

**Equipe:** execução real T01–T11; Web didática completa; terminal/Web original sem regressão; duas máquinas comunicando com tarefa MiniPar, se exigência adotada; fractais corretos; ARM/CPUlator; erros negativos básicos; evidências e documentação em produção.

**Saída G3 até 31/10:** nenhuma funcionalidade obrigatória iniciada do zero a partir daqui; lacunas restantes classificadas e endereçadas. O foco passa a bugfix, evidência e acabamento.

**Se G3 falhar:** reduzir opcionais imediatamente; renegociar a meta interna de congelamento somente com plano explícito — nunca fingir entrega integral.

### M4 — 01 a 03/11 | Congelamento funcional / candidata a entrega (G4)

**Equipe:** regressão, logs, testes de integração, asserts/oráculos, demonstração repetível, README instalação, BNF, UML, pseudocódigos, Product/Sprint Backlogs, capturas e relatório; pacote candidato. **B edita documentos integrados; C centraliza resultados de QA e backlog; A valida exatidão da BNF, dos pseudocódigos e dos contratos.**

**Saída G4 — 03/11:** versão marcada (tag sugerida `v0.9.0-rc1`), instruções de execução, links internos de artefatos, evidência por teste, interfaces demonstráveis e lista honesta de limitações.

**Se G4 falhar:** estudo 04–10/11 deve ser protegido **tanto quanto possível**; priorizar correções críticas com sessões curtas e comunicar riscos de entrega; evitar redesenhos grandes.

### M5 — 04 a 10/11 | Estudo, relatório final e ensaios (G5)

**04/11:** mapa do sistema, principais classes, Lexer/Parser/AST.  
**05/11:** semântico, símbolos, TAC, backend C++ e diferenças entre representações.  
**06/11:** Fork/Join, workers, sockets, isolamento e demonstração em rede.  
**07/11:** testes 8–10, cargas, Mandelbrot, Sierpinski e benchmarks.  
**08/11:** Teste 11, AST de expressões, TAC, geração ARM, CPUlator.  
**09/11:** duas Webs, CLI, UML, processo de compilação e relatório; ensaio completo.  
**10/11:** ensaio final com três participantes, verificação dos links/artefatos e backup.

**Regra:** todos devem explicar visão geral, mesmo que não tenham codificado todo o sistema. O coordenador também precisa reservar tempo para estudar o outro projeto de CG, conforme arranjo do trio.

### M6 — 11/11 | Entrega oficial

GitHub novo com código ativo e legado identificado, documentação, relatório, evidências e links; apresentação. Ver checklist `docs/11_CHECKLIST_DE_ENTREGA.md`.

---

## 6. Caminho crítico de dependências

```text
D0 Importar base/compilar baseline
 ├──> D1 C-T11 / recursos de string (A+B)
 │     └──> B implementa MiniCompilador (B) ──> `.arm` ──> CPUlator ──> evidências
 ├──> D2 C-WEB / formato dos artefatos (A+B)
 │     ├──> B cria Web com fixtures
 │     └──> A expõe artefatos reais ──> B integra Web ──> testes
 └──> D3 C-FJ / gramática + API (A+C)
       ├──> A integra Parser/AST/semântico/TAC/gerador C++
       └──> C desenvolve runtime local/remoto + worker
                 └──> integração A+C ──> T08 ──> T09 ──> T10
```

**Caminho mais arriscado:** contrato Fork/Join → runtime remoto comprovado → geração C++ → T08–T10 + duas máquinas. **Segundo caminho crítico:** strings MiniPar → MiniCompilador real → Assembly executado no CPUlator.

A Web é paralelizável com fixtures; seu vínculo com A ocorre em um **gate explícito de API**, não em alterações simultâneas de Flask/Parser.

---

## 7. Reuniões mínimas, atualizações e escalação

**Kickoff (16/10, sugestão 30–45 min):** confirmar donos B/C, horários, instalar base, decidir contrato C-FJ/C-WEB/C-T11 e permissões GitHub. Se faltar nome, deixar os eixos abertos e não atribuir PRs.

**Checkpoint assíncrono diário (até 5 min por eixo):** card iniciado/concluído, teste demonstrado, bloqueio, contrato que precisa alterar, risco para marco. Atualizar no board (quando criado) ou `planning/cards.json` antes dele.

**Reuniões curtas de integração (sugeridas 18, 23, 28, 31/10 e 03/11, 15–30 min):** demonstração ao vivo das provas do gate, não uma conversa genérica sobre progresso.

**Política de bloqueio:** 2h investidas sem avanço objetivo ou dependência alheia indisponível → registrar `BLOCKED`, chamar responsável; não produzir workaround que quebre o contrato.

**Política de atraso:** 24h antes do marco, se um P0 estiver em risco, reordenar cards e suspender P2; 48h de atraso em caminho crítico requer decisão explícita de redistribuir/reduzir opcionais e talvez revisar a meta interna.

**Política de bugs:** classificar P0 (não compila/risco de não entregar), P1 (funcionalidade essencial incorreta), P2 (problema importante), P3 (cosmético). Priorizar correção por severidade.

---

## 8. Critérios de prioridade

| Nível | Exemplos | Regra |
|---|---|---|
| **P0 — Não negociável** | Compilação real; Fork/Join; duas máquinas; T08–T11; três interfaces mínimas; documentação obrigatória | Atacar cedo, bloquear extras |
| **P1 — Confiabilidade** | TAC verdadeiro, regressão, tipos essenciais, validação negativa, scripts reprodutíveis | Não deixar para a véspera |
| **P2 — Qualidade** | Busca interativa na AST, animações, extensões além dos testes, refatoração extensa | Só depois de P0/P1 |
| **P3 — Opcional** | Deploy público, distribuição genérica de closures, GUI gráfica complexa, UI ornamental | Não incluir sem folga comprovada |

**O que não pode ser cortado silenciosamente:** exigências do professor. Se algo impossível, registrar pendência e buscar orientação; reduzir **ambição técnica interna**, não esconder requisitos.

---

## 9. Regras de decisão em caso de incerteza

1. **Enunciado prevalece** sobre escolhas arquiteturais, sobre relatório antigo e sobre sugestão de agente.
2. **Evidência prevalece** sobre autoconfiança do Codex.
3. **Contrato aprovado prevalece** sobre conveniência de mudança local.
4. **Prazos de integração prevalecem** sobre aperfeiçoamento cosmético.
5. **Reaproveitar** código 2026.1 onde válido; não apagar histórico.
6. Dúvida com duas arquiteturas plausíveis: escolher aquela que minimiza alterações no compilador e atende teste demonstrável, registrando trade-off.
7. Redesenho que afete dois eixos exige reunião breve de decisão e CR.

---

## 10. Critérios de aceite por eixo (handoff entre equipes)

**Handoff A → B:** serviço produz JSON documentado para tokens/AST/símbolos/diagnósticos/TAC/C++; compilação e execução retornam status/artefato real; fixtures batem com produção; versão de contrato anotada.

**Handoff C → A:** funções/headers/lib do runtime compilam em isolamento; registry de tasks com IDs; `start` não bloqueia de maneira indevida; `join` aguarda resultado/erro; conexão remota registrada; logs/exemplos; C++ gerado por A consegue chamar API sem acoplamento a detalhes privados do C.

**Handoff A → B Teste 11:** operações `input`/`string`/`len`/`substr`/`to_string`/listas essenciais funcionam em MiniPar e geram binários. Não prometer dicionários e floats se não foram implementados; B escreve o algoritmo do Teste 11 em MiniPar com essas primitivas.

**Handoff de todos → QA:** comandos de reprodução, ambiente, entradas, saídas, prints, timestamps quando úteis, critérios reais de aceitação; evitar logs enormes no Git.

---

## 11. Integração e revisões

- Cada implementação começa com **smoke test pequeno** e termina com teste de integração no consumidor.
- O dono do contrato participa do review da integração (A+B ou A+C).
- Nenhuma tarefa é dada por concluída apenas porque o agente abriu PR.
- `dev` deve permanecer minimamente demonstrável.
- Não criar workflows CI complexos antes de a toolchain estar estabilizada; começar com validação Python, lint/compilação básica e depois ampliar.
- Entradas/sockets/executáveis devem ser testados em ambiente controlado. Web acadêmica local não é serviço público seguro.

### 11.1 Política de merge quando o coordenador tem só 3h/dia

**Máximo sugerido: 2 PRs de integração por dia para revisão pelo coordenador.** PRs menores podem ser revisados por outro integrante (o consumidor designado ou o dono do eixo afetado), conforme regras combinadas. Todo PR precisa de pelo menos uma aprovação que não seja do autor.

Reserve no calendário 30–60 minutos/dia para reviews/comunicação. Se o coordenador vira gargalo, redistribua revisão de módulos próprios, nunca libere bypass irrestrito em `src/`.

---

## 12. Matriz de rastreabilidade resumida

| Exigência | Responsável principal | Gate | Evidência |
|---|---|---|---|
| Lexer/Parser/AST/Semântico/Símbolos | A | G2 | Testes válidos/negativos + introspecção |
| TAC genérico | A | G2 | T07 mutado não recebe TAC fixo |
| C++/G++/executável | A | G0/G3 | build e execução verificáveis |
| `seq`, `par`, `fork`, `join` | A + contrato C | G2/G3 | programa MiniPar e trace real |
| Canais/sockets/remoto | C + integração A | G1/G3 | dois hosts reais e resultados |
| T01–T07 | A | G3 | saídas/oráculos comparados |
| T08–T10 | C | G3 | 160 avaliações + fractais + joins |
| T11/ARM/CPUlator | B | G2/G3 | três expressões + `.arm` executado |
| Terminal e Web original | A | G3 | smoke tests |
| Nova Web didática | B + API A | G3 | telas com dados reais |
| BNF/UML/pseudocódigos | B consolida, A/C revisam | G4 | documentação alinhada |
| Product/Sprint Backlogs, relatório e GitHub | C mantém backlogs, B edita relatório, A valida | G4 | links, screenshots, anexos |
| Apresentação | Todos | G5 | ensaio completo |

---

## 13. Pendências que **não bloqueiam o planejamento**, mas têm dono/prazo

| Dúvida | Dono para resolver | Data-alvo | Impacto se não resolvida |
|---|---|---|---|
| Escopo do despacho remoto automático | A + C | 18/10 | Má arquitetura runtime |
| Forma de escrita `.arm` exigida | B + A | 19/10 | Teste 11 incompleto |
| Sierpinski gráfico: janela/SVG/outra saída | C | 20/10 | Não aceitação de T10 |
| Ambiente G++20 e Web Flask | A | 18/10 | Regressão e Web bloqueadas |
| Disponibilidade de dois computadores | C + equipe | 18/10 | Demonstração remota bloqueada |
| Horas disponíveis B e C | Equipe | 16/10 | Datas inexequíveis |
| Licença/atribuição do código anterior | Coordenação | Antes de publicar publicamente | Risco de redistribuição |

---

## 14. Política de evolução deste plano

Este planejamento é `v0.1`. Depois da aprovação dos três contratos e das horas disponíveis, atualizar para `v0.2`, ajustando datas/estimativas sem apagar decisões. Publicação das GitHub Issues ocorrerá **somente depois de revisar** `planning/cards.json`.

A cada gate, registrar decisão: **PASSOU / PASSOU COM RESSALVAS / BLOQUEADO / FALHOU**, responsáveis pela correção e nova data. Novos requisitos não entram silenciosamente no escopo.

**Próxima ação prática:** ler `docs/10_GUIA_SETUP_REPOSITORIO.md`, importar o legado, confirmar responsáveis e agendar o kickoff G0. Criar as Issues depois da revisão dos cards.
