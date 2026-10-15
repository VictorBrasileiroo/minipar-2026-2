# MiniPar 2026.2 — Marcos de Entrega do Trio

> **DOCUMENTO OPERACIONAL DE MARCOS | v1.0 | 15/10/2026**  
> **Marco 1: quinta-feira, 22/10/2026** · **Marco 2: quinta-feira, 29/10/2026** · **Marco 3: terça-feira, 03/11/2026**  
> **Estudo e ensaios:** 04–10/11/2026 · **Entrega oficial:** 11/11/2026.
>
> Este documento **substitui o calendário de G0/G1/G2/G3/G4 da seção 5 de `01_PLANEJAMENTO_GERAL.md`**, mas preserva os contratos, prioridades, dependências, regras de qualidade e o escopo do Documento Mestre. Em caso de conflito de datas, **os três marcos deste documento prevalecem**.

## 1. Como funcionam os marcos

**Não existe prazo individual por card.** Cada um dos três marcos define **um conjunto fechado de cards e um resultado demonstrável até a data-limite**. O integrante decide quando executar seus cards dentro da janela, respeitando as dependências técnicas e a disponibilidade combinada. Um card do Marco 2 pode ser antecipado no Marco 1 se estiver pronto; isso não altera seu prazo contratual.

- **M1 — até 22/10:** base reproduzível, contratos aprovados, provas de risco e UI/MiniCompilador em protótipos utilizáveis.
- **M2 — até 29/10:** funcionalidades de Fork/Join, T08–T10, T11 completo e Web didática integrados em pelo menos um fluxo real por frente.
- **M3 — até 03/11:** regressão geral, documentação acadêmica, evidências, correções, release candidata e congelamento de funcionalidades.

### 1.1 Quem responde por quê

| Eixo | Responsável | Fronteira autorizada |
|---|---|---|
| **A — Núcleo** | **Você (coordenador)** | `src/`, geração C++, semântico, TAC, gramática, compatibilidade de CLI e Web antiga, interfaces de serviço e aprovação das integrações do núcleo |
| **B — Web e Teste 11** | **Colega a definir** | `web_didatica/`, `tests/2026_2/test11/`, AST visual e MiniCompilador em MiniPar, consolidação documental |
| **C — Runtime e testes 8–10** | **Colega a definir** | `runtime/`, `tests/2026_2/test08..10/`, protocolos, workers, comunicação real, QA e evidências de testes distribuídos |
| **Compartilhado** | Todos, com dono nominal do card | Contratos `CON-*`, revisão dos consumidores e demonstrações integradas; ninguém edita código do outro eixo unilateralmente |

**Fonte de acompanhamento:** a planilha compartilhada, não GitHub Issues. GitHub fica para código/branches/PRs. Os IDs dos 43 cards continuam os mesmos da planilha; o prazo visível de cada card corresponde **somente à data do seu marco**.

### 1.2 Regras que evitam sobreposição e espera

1. **Contratos primeiro:** `CON-01` (Fork/Join: A+C), `CON-02` (serviço da Web: A+B), `CON-03` (primitivas/Teste 11: A+B) devem ser aprovados **antes** dos consumidores se integrarem ao código real. Provas reversíveis isoladas são permitidas antes disso.
2. **Dono exclusivo do código:** apenas A altera `src/`; B altera `web_didatica/` e T11; C altera `runtime/` e T08–T10. O legado em `legacy/` permanece imutável.
3. **Mocks contratados:** enquanto A implementa o serviço real, B usa JSON fixtures no formato aprovado; enquanto A produz C++ de `fork/join`, C testa a biblioteca por um harness C++ próprio. Mock não conta como aceitação da integração final.
4. **Dependências mandam na ordem de execução, não o calendário:** nenhuma tarefa começa se estiver sem pré-requisito e sem mock formalmente aprovado. Registrar `BLOQUEADO` e dependência exata.
5. **Só marcar DONE com evidência:** comando de execução, log, resultado comparado, código/commit e, se aplicável, CPUlator ou dois computadores reais. `Exit 0`, código emitido ou UI bonita isoladamente não bastam.
6. **Status na planilha:** `Planejado` → `Em andamento` → `Em revisão` → `Concluído`. Bloqueios e responsáveis são registrados no próprio card; não criar cronogramas diários paralelos.
7. **Mudanças de contrato:** propor em `docs/03_DECISOES.md`, com impacto, teste e aceite das duas pontas. Não atualizar API unilateralmente por instrução de um agente.

### 1.3 Como o trio valida cada marco

No próprio dia-limite, cada eixo apresenta: cards concluídos, comandos executados, evidências verificáveis, dependências atendidas e problemas remanescentes. **Marco aprovado somente se TODOS os seus cards P0 foram aceitos ou se houver uma decisão explícita documentada de mudança de escopo.** O coordenador não precisa fazer as tarefas dos outros eixos: cada responsável responde por seu resultado e sua demonstração.

**Checkpoints internos não são novos prazos:** conversas curtas para detectar problemas cedo são permitidas a qualquer momento, especialmente em interfaces entre eixos; não viram datas individuais de cards.

---

## 2. Marco 1 — Até 22/10/2026

**Resultado do marco:** projeto reproduzível, contratos definidos, correções fundamentais de strings, gramática de Fork/Join iniciada, UI com AST simulada, MiniCompilador mínimo em MiniPar e infraestrutura de workers testada **em dois computadores reais**.

**Janela:** de 16/10 a 22/10 (sete dias corridos). Os cards de setup que já foram executados manualmente **só precisam de conferência e registro de evidência**, não de refazer importação.

**Ordem lógica dentro do marco (sem microdatas):**
`SET-01` → (`SET-02`,`SET-03`) → contratos `CON-01..03` → tarefas dependentes. A entrega de `CORE-03` libera o MVP do Teste 11; `RUN-02` libera a prova remota de `RUN-03`; `WEB-01` libera a construção da árvore visual `WEB-02`.

### Evidências mínimas que devem existir em 22/10

- Ambiente Python + compilador C++ reproduzível; logs de versão/compilação e relatório de testes herdados, distinguindo aprovação real de divergência/bloqueio.
- Os **três contratos assinados/aceitos** por seus fornecedores e consumidores, com API, formatos, falhas e exemplos; confirmação da disponibilidade de duas máquinas e do papel de cada integrante.
- `CORE-03`: strings, `len`, `substr`, `to_string` e listas textuais necessárias ao programa de Teste 11 funcionando em MiniPar compilado e executado.
- `CORE-04`: amostras válidas/inválidas de sintaxe de Fork/Join passam no Lexer/Parser/AST conforme BNF aprovada; não prometer runtime integrado ainda.
- Eixo B: a Web exibe JSON de tokens, AST e painéis a partir de fixtures, claramente identificada como **mock**; Teste 11 prova tokenização, precedência e AST/TAC por lógica escrita em MiniPar, ainda que o ARM final venha no Marco 2.
- Eixo C: runtime local inicia/junta tarefas; protocolo robusto envia e devolve resultados identificados; prova de processo worker em **segundo computador real**, com endereços/hosts e resultado conferível. Se as máquinas não estiverem disponíveis, declarar bloqueio crítico — localhost não equivale à prova remota.

### Condição de avanço para M2

Não liberar integração do gerador C++ com API indefinida nem substituir um contrato faltante por código de IA improvisado. Se C não conseguir a prova remota, o caminho crítico `RUN-04 → T08 → T09 → T10` ficará em risco: replanejar formalmente no próprio dia 22. Se o MiniCompilador mínimo falhar, priorizar o erro de linguagem antes da Web cosmética.


### Cards obrigatórios deste marco (prazo único: **22/10** )

#### **Eixo A — Você**

| Card | Entrega objetiva | Dependência | Aceite verificável |
|---|---|---|---|
| `SET-01` | Criar estrutura e importar base 2026.1 | — | Arquivos ativos presentes; `legacy` preservado; `git status` limpo; scripts de importação conferidos. |
| `SET-02` | Padronizar Python e G++20; executar smoke | `SET-01` | T01 simples compila e executa em ferramenta suportada; log identifica versões e comandos. |
| `SET-03` | Permissões Git, responsáveis B/C, branches e acesso a dois PCs | — | Trio confirma acesso/horas; hosts de rede definidos; branch protect quando viável. |
| `CORE-03` | Corrigir primitivas strings e coleções usadas por T11 | `CON-03`, `SET-02` | Programas de prova T11 compilam/produzem oráculos; regressão anterior sem piora. |
| `CORE-04` | Implementar BNF, tokens e AST de Fork/Join | `CON-01` | Programas MiniPar positivos/negativos de Fork/Join têm AST correta; BNF coerente. |

#### **Contrato conjunto — A + B**

| Card | Entrega objetiva | Dependência | Aceite verificável |
|---|---|---|---|
| `CON-02` | Congelar contrato serviço de fases para a Web | `SET-01` | A e B aprovam fixture de sucesso e três erros; Web poderá usar mocks. |
| `CON-03` | Congelar recursos mínimos Teste 11 e saída ARM | `SET-01` | A e B aprovam programas de prova com oráculo e responsabilidades. |

#### **Contrato conjunto — A + C**

| Card | Entrega objetiva | Dependência | Aceite verificável |
|---|---|---|---|
| `CON-01` | Congelar contrato de Fork/Join e destino local/remoto | `SET-01` | A e C aprovam contrato; exemplos/fixtures; mudança via CR; pendências registradas. |

#### **Eixo B — Colega a definir**

| Card | Entrega objetiva | Dependência | Aceite verificável |
|---|---|---|---|
| `WEB-01` | Wireframe e fixtures JSON dos painéis didáticos | `CON-02` | Todas as fases navegáveis em mock; AST desenhada de fixture; Web original intocada. |
| `WEB-02` | Implementar AST interativa e painéis de fases | `WEB-01` | AST expandir/recolher; erros legíveis; programas grandes sem travar UI em exemplo. |
| `T11-01` | Recuperar prova experimental e concluir MVP MiniCompilador | `CON-03`, `CORE-03` | Ao menos a primeira expressão obrigatória retorna 22 em programa MiniPar executado. |

#### **Eixo C — Colega a definir**

| Card | Entrega objetiva | Dependência | Aceite verificável |
|---|---|---|---|
| `CORE-01` | Registrar baseline reprodutível dos testes 1–7 | `SET-02` | Execução nativa de cada T01–T07 com status PASS/FAIL/BLOCKED e evidência. |
| `RUN-01` | Runtime local de start/join com isolamento | `CON-01` | `start` retorna sem aguardar tarefa; `join` aguarda e coleta resultado/erro em testes C++ isolados. |
| `RUN-02` | Protocolo TCP robusto e worker pré-compilado | `CON-01` | Fragmentação, frame inválido, worker indisponível e duas tarefas fora de ordem testados. |
| `RUN-03` | Prova de execução em dois computadores reais | `RUN-02`, `SET-03` | Provar IPs distintos e cálculo remoto verdadeiro; join com timeout quando worker cai. |

## 3. Marco 2 — Até 29/10/2026

**Resultado do marco:** linguagem e backend geram programas usando o runtime contratado; Testes 8–10 executam o trabalho exigido, Teste 11 gera ARM validado no CPUlator, e a Web didática consegue analisar, compilar e executar pelo serviço real.

**Janela:** de 23/10 a 29/10 (sete dias corridos). **É o marco de maior pressão de integração.** Não esperar o último dia para juntar as branches: integrar cada componente assim que seu contrato estiver validado.

**Ordem lógica dentro do marco (não são prazos individuais):**
- **A → C:** `CORE-05` (semântico Fork/Join) + `RUN-01/RUN-03` → `RUN-04` (handoff API) → `CORE-07` (C++ chama runtime) → `T08-01` → `T09-01` → `T10-01`.
- **A → B:** `CORE-08` (serviço real) + `WEB-02` (UI por fixtures) → `WEB-03` → `WEB-04`.
- **B / T11:** `T11-01` → `T11-02` → `T11-03`; CPUlator valida os artefatos `.arm` produzidos pelo programa MiniPar, não Assembly fabricado em Python.
- **Integração:** `CORE-07` + `WEB-03` + `RUN-04` → `INT-01`. O TAC genérico `CORE-06` permanece explicitamente previsto para correção/fechamento no Marco 3; a execução C++ e os testes não devem fingir que ele já foi concluído.

### Evidências mínimas que devem existir em 29/10

- Compilação MiniPar → C++ → executável com `fork/join`; execução local e remota demonstradas, identificando tarefa, worker, entrada, saída e join.
- **T08:** 160 atividades atribuídas a quatro avaliadores, verificadas sem perda ou duplicação; comparação sequencial/paralela documentada com metodologia honesta.
- **T09:** Teste 8 acrescido do Mandelbrot ASCII em worker adicional; resultados separados e corretos.
- **T10:** Teste 9 acrescido do Sierpinski no sexto worker; confirmar tipo de saída permitido pelo enunciado (gráfico/ASCII/imagem). Se houver dependência de `turtle`, documentar como será demonstrada sem mascarar trabalho no processo pai.
- **T11:** entradas `((2+4)*7)-(5*4)` → **22** e `((10-8*7)+4)*2` → **−84**, com repetição da primeira; tokens, AST, TAC, símbolos e `.arm` emitidos por algoritmo realmente em MiniPar. CPUlator executa assembly e o resultado coincide.
- **Web didática:** tokens, AST hierárquica, símbolos/diagnósticos, TAC, C++, compilar, executar e baixar artefatos associados ao código do usuário; ao menos fluxo real completo com screenshot/log. Terminal e Web legada ainda sujeitos à regressão final em M3.
- `INT-01`: smoke integrado cruzando os três eixos, com logs, build reproduzível e itens pendentes listados; não aceitar somente arquivos simulados.

### Condição de avanço para M3

Até o fim de 29/10, **nenhuma funcionalidade obrigatória nova pode continuar sem implementação básica real**. Se T08–T10 ou ARM/CPUlator estiverem incompletos, abrir contingência no dia 29, realocar apoio humano ou reduzir recursos não obrigatórios. Priorizar executar corretamente em vez de polimento visual e otimizações.


### Cards obrigatórios deste marco (prazo único: **29/10** )

#### **Eixo A — Você**

| Card | Entrega objetiva | Dependência | Aceite verificável |
|---|---|---|---|
| `CORE-02` | Remover TAC fixo do Quicksort e corrigir T07 | `CORE-01` | Programa modificado com mesmo nome não reproduz TAC fixo; T07 compila/ordena sem bounds violation. |
| `CORE-05` | Semântico de Fork/Join e isolamento | `CORE-04` | Uso indevido rejeitado; funções e destinos válidos aceitos; semântico preserva regressão. |
| `CORE-07` | Gerar C++ que invoca runtime real de C | `CORE-05`, `RUN-01`, `RUN-02` | MiniPar→C++→binário cria tarefa local e remota de teste; join retorna dado correto. |
| `CORE-08` | Expor serviço de fases ao eixo Web | `CON-02`, `SET-02` | Fixtures combinam com resultados reais; IDs evitam cache errado; erro separa fases. |

#### **Eixo B — Colega a definir**

| Card | Entrega objetiva | Dependência | Aceite verificável |
|---|---|---|---|
| `WEB-03` | Integrar UI ao serviço real fornecido pelo A | `CORE-08`, `WEB-02` | Exemplo positivo e erro são fiéis à compilação; sem dados hardcoded no fluxo real. |
| `WEB-04` | Compilar, executar e baixar binário atual | `WEB-03` | G++ realmente compila; returncode validado; download é artefato correto; timeout/erro apresentados. |
| `T11-02` | Completar semântica, símbolos, erros e emissão ARM do T11 | `T11-01` | Resultados 22,-84,22; nenhum valor fixo por entrada; erros relevantes rejeitados. |
| `T11-03` | Validar Assembly no CPUlator e arquivar evidências | `T11-02` | Três `.arm` executam com resultados; registrar CPUlator/versão e instruções. |

#### **Eixo C — Colega a definir**

| Card | Entrega objetiva | Dependência | Aceite verificável |
|---|---|---|---|
| `RUN-04` | Handoff de API runtime e integração com backend A | `RUN-01`, `RUN-03`, `CORE-05` | A integra `start/join` em CORE-07; teste simples local/remoto passa sem mexer `src/` via C. |
| `T08-01` | MiniPar T08: 160 avaliações em quatro trabalhadores | `RUN-04`, `CORE-07` | 40×4=160, sem perda/duplicata, quatro workers, sequência/paralelo comparados corretamente. |
| `T09-01` | MiniPar T09: avaliadores + Mandelbrot ASCII | `T08-01` | 160 avaliações; fractal calculado dinamicamente; cinco tarefas sincronizadas. |
| `T10-01` | MiniPar T10: avaliações + Mandelbrot + Sierpinski | `T09-01` | Fractais produzidos; trabalho Sierpinski realmente integrado ao modelo; documentar divergência da referência Python. |
| `INT-01` | Smoke de integração 3 eixos antes do fechamento | `CORE-07`, `WEB-03`, `RUN-04` | Teste único ponta a ponta reproduzível, resultados anexados, defeitos classificados. |

## 4. Marco 3 — Até 03/11/2026

**Resultado do marco:** versão candidata congelada com testes 1–11 documentados, três interfaces demonstráveis, TAC autêntico, execução em rede reproduzível, UML/BNF/pseudocódigos/backlogs/relatório e evidências completas.

**Janela:** 30/10–03/11 (cinco dias corridos). Não aceitar novos recursos cosméticos a partir desta fase. As tarefas documentais devem ser **rascunhadas antes**, quando houver material, mesmo que só possam ser marcadas completas no M3.

**Ordem lógica dentro do marco:**
- A fecha `CORE-06` (TAC real para `par` e Fork/Join), revalida `CORE-09` (CLI + Web antiga) e revisa alterações em contrato/BNF.
- C conclui testes de falha/benchmark (`RUN-05`), regressão T01–T07 (`CORE-10`), documentação de protocolo (`RUN-06`) e backlog/decisões (`DOC-03`).
- B finaliza documentação de interfaces/T11 (`WEB-05`), BNF e pseudocódigos a partir da versão real (`DOC-01`), UML (`DOC-02`), regressão completa (`INT-02`) e relatório (`DOC-04`).
- `INT-02` só é concluído após T10, T11/CPUlator, serviço Web e regressão dos sete testes. `DOC-04` depende das evidências dos três eixos. **`REL-01` é o último card do marco**: só congelar release depois de `DOC-04` e validação integrada.

### Evidências mínimas que devem existir em 03/11

- Compilação/testes 1–11 com tabela `passou`, `falhou` ou `bloqueado`, comandos, entradas e saídas, critérios numéricos quando aplicáveis; sem ocultar falhas.
- Teste 7 com **TAC gerado de verdade**, sem depender do nome fixo `quicksort_iterativo`; programa sem acesso fora dos limites. Registros do caso XOR justificam tolerâncias, caso aplicável.
- Fork/Join com semântico + TAC + C++ coerentes; testes de join, isolamento e erros básicos; demonstração reprodutível em dois hosts.
- Terminal, Web original e Web didática funcionando com o código atualizado; recursos de download/executar vinculados à compilação correta.
- `BNF` atualizada, UML de casos de uso/componentes/classes, pseudocódigos das fases, Product e Sprint Backlogs, decisões, README, instruções de runtime/CPUlator e relatório técnico com link do repositório na capa.
- Evidências para apresentação: capturas de interface, saída do CPUlator, prints/logs de workers em máquinas diferentes, versão de toolchain, testes dos fractais, commit/tag candidato.
- `REL-01`: release candidata identificada (por exemplo, tag `v0.9.0-rc1`), com lista honesta de pendências, se houver, e congelamento da base para a semana de estudo.

### Regra de corte

Se algo obrigatório falhar perto de 03/11, não declarar marco concluído artificialmente. Corrigir defeitos de maior severidade, suspender P2/cosmética, registrar risco do prazo e preservar ao máximo os sete dias de estudo. Não usar 04–10/11 como nova semana normal de desenvolvimento.


### Cards obrigatórios deste marco (prazo único: **03/11** )

#### **Eixo A — Você**

| Card | Entrega objetiva | Dependência | Aceite verificável |
|---|---|---|---|
| `CORE-06` | TAC autêntico para Fork/Join e `par` | `CORE-05`, `CORE-02` | TAC distingue sequência/paralelismo; casos com diferentes tarefas geram representação coerente. |
| `CORE-09` | Preservar terminal e Web antiga após mudanças | `CORE-07`, `CORE-08` | Executar cenário básico nas duas interfaces e comparar com versão inicial. |
| `REL-01` | Congelar release candidata 03/11 | `DOC-04` | Build reproduzível a partir de checkout limpo; evidências acessíveis; pendências explícitas. |

#### **Eixo B — Colega a definir**

| Card | Entrega objetiva | Dependência | Aceite verificável |
|---|---|---|---|
| `WEB-05` | Documentar interface, T11 e preparar screenshots | `WEB-04`, `T11-03` | Seções prontos para relatório com evidências verificáveis. |
| `INT-02` | Regressão integral, três interfaces e rede real | `INT-01`, `WEB-04`, `T11-03`, `T10-01`, `CORE-10` | Cada caso PASS/FAIL/BLOCKED com oráculo; falhas e severidade registradas. |
| `DOC-01` | BNF final e pseudocódigos núcleo | `CORE-06` | Consistência com implementação real e regras de Fork/Join. |
| `DOC-02` | UML casos de uso, componentes, classes | `INT-01` | Interfaces e classes existentes, geradores TAC/C++ incluídos; peer review dos eixos. |
| `DOC-04` | Relatório completo, evidências e GitHub na capa | `INT-02`, `DOC-01`, `DOC-02`, `DOC-03`, `WEB-05`, `RUN-06` | Professor encontra todos entregáveis; referências e anexos testados. |

#### **Eixo C — Colega a definir**

| Card | Entrega objetiva | Dependência | Aceite verificável |
|---|---|---|---|
| `CORE-10` | Regressão final T01–T07 com oráculos reais | `CORE-02`, `CORE-03`, `CORE-07` | Não há falsos PASS; bugs remanescentes com risco registrado. |
| `RUN-05` | Benchmarks e falhas distribuídas repetíveis | `T10-01`, `RUN-03` | Cargas sequencial/paralela equivalentes; relatório sem confundir workers com núcleos físicos. |
| `RUN-06` | Documentar protocolo, topologia, deploy e testes | `RUN-05` | Outro integrante reproduz dois PCs seguindo instruções; logs sem dados pessoais. |
| `DOC-03` | Product Backlog, Sprint Backlogs e decisões atualizados | `INT-01` | Corresponde ao desenvolvimento feito, sem declarar resultado inexistente. |

---

## 5. Capacidade e riscos de calendário

As horas são **estimativas anteriores do backlog assistido por IA**, não medição de produtividade real. Contratos conjuntos aparecem em separado; **não** devem ser cobrados integralmente só do coordenador.

| Marco | A (exclusivas) | B | C | Contratos A+B/A+C | Total previsto dos cards |
|---|---:|---:|---:|---:|---:|

| M1 — 22/10 | 19 h | 16 h | 23 h | 7 h | **65 h** |
| M2 — 29/10 | 20 h | 23 h | 26 h | 0 h | **69 h** |
| M3 — 03/11 | 10 h | 21 h | 13 h | 0 h | **44 h** |

**Leitura importante:**

- Para o eixo A, o limite informado é de **até 3 h/dia**. M1 atribui **19 h exclusivas + participação em 7 h de contratos compartilhados**, e parte do setup já foi realizada manualmente. O coordenador **não pode** executar integralmente as 7 h compartilhadas; B/C devem preparar suas partes, cabendo ao A aprovar/revisar. Reavaliar já no começo se houver retrabalho de ambiente.
- M2 exige **20 h exclusivas de A em sete dias** — quase seu teto de 21 h, antes de reviews. Reservar revisões curtas e evitar tarefas de B/C. No M3 A tem 10 h exclusivas, preservando alguma capacidade de revisão e release.
- O eixo B precisa lidar com **16 h → 23 h → 21 h**, e C com **23 h → 26 h → 13 h**. Isso pressupõe disponibilidade dos colegas **a confirmar** e que possam produzir várias horas por dia nas janelas mais intensas. Sem essa confirmação, o plano não é uma promessa viável.
- **Dependências dentro de um mesmo marco continuam sequenciais**. Por exemplo, `RUN-04 → CORE-07 → T08 → T09 → T10` tem caminho serial; paralelizar por arquivos é necessário, mas não elimina esse gargalo. Se o Codex empacar nessa sequência, escalar imediatamente.
- Os três marcos abrangem **40 cards até 03/11**. Os outros três são de estudo/entrega: `EST-01`, `EST-02` e `ENT-01`.

### Regras de contingência por marco

| Situação | Ação de gestão |
|---|---|
| Falta contrato de interface ou dependência real | Bloquear integração, permitir apenas testes isolados com mock aprovado e documentado |
| M1 sem duas máquinas ou sem strings MiniPar | Reunir responsáveis; concluir prova mínima prioritária antes de ampliar o desenvolvimento |
| M2 sem T08 ou sem ARM/CPUlator | Suspender cosmética, focar nos dois caminhos críticos; reestimar e distribuir apoio dentro dos limites |
| B ou C têm menos horas que a carga do marco | Ajustar distribuição **antes** do marco, não esperar pelo atraso |
| M3 sem regressão íntegra ou relatório | Registrar falhas, decidir correções críticas e preservar período de estudos; não marcar DONE sem aceite |

## 6. O que acontece depois de 03/11

| Período | Cards | Compromisso |
|---|---|---|
| **04–08/11** | `EST-01` | Cada integrante domina seu eixo e sabe explicar o fluxo completo: Lexer, Parser/AST, semântico, símbolos, TAC, C++, Fork/Join, Web, Teste 11 e CPUlator; preparar roteiro e perguntas prováveis |
| **09–10/11** | `EST-02` | Ensaio do trio, execução da demonstração completa, plano para indisponibilidade de máquina, conferência do material de apresentação |
| **11/11 — oficial** | `ENT-01` | Repositório e entregáveis finais enviados, documentos consistentes e apresentação conforme orientação do professor |

**Não confundir:** 03/11 é **prazo interno para finalizar construção**, e 11/11 é **prazo oficial de entrega**. O estudo não é um quarto marco de implementação.

## 7. Procedimento de acompanhamento na planilha

1. Atualizar apenas os estados/evidências dos cards, sem criar prazo por tarefa. Todos os cards do mesmo marco compartilham a **mesma data-limite**.
2. Confirmar o responsável de B/C na aba `EQUIPE` e informar disponibilidade real; A não está autorizado a assumir o eixo alheio por omissão.
3. Antes de começar, verificar colunas de dependência e autorização. Exceções só com contrato/mock registrado.
4. Para encerrar um marco: filtrar os respectivos IDs, conferir 100% dos obrigatórios, executar as demonstrações de aceite, anotar bloqueios e aprovar explicitamente a passagem.
5. Registrar apenas uma linha de decisão por mudança relevante; GitHub continua sendo repositório do código, **não** gerenciador de tarefas.

## 8. Referências internas e precedência

- `docs/00_DOCUMENTO_MESTRE_INICIAL.md`: requisitos e escopo.
- `docs/01_PLANEJAMENTO_GERAL.md`: arquitetura de trabalho, riscos, papéis e padrões — **calendário anterior substituído por este documento**.
- `docs/02_CONTRATOS_TECNICOS.md`: contratos C-WEB, C-FJ e C-T11, a serem congelados pelo trio.
- `docs/04_BACKLOG.md`: descrição integral dos cards e critérios de aceite.
- `planning/cards.json`: mesmas tarefas, com novo campo `milestone` e `due` igual à data do marco.
- Planilha compartilhada: fonte oficial de estados, responsáveis, bloqueios e evidências.

**Aprovação para iniciar:** coordenador confirma os marcos e os responsáveis de B/C; B/C confirmam carga e contratos. Nenhuma data é uma garantia técnica sem evidência de execução.
