# REL-PRE — fechamento técnico e documental do Eixo A

**Data:** 09/11/2026 · **Responsável:** coordenação / Eixo A · **Entrega oficial:** 11/11/2026.
**Branch:** `eixo-a/REL-PRE-fechamento-tecnico`, criada após fast-forward de `dev` para `8d0743302ffe29e012ef4a3a4cc1eeba0281637c`.
**Autorização:** solicitação explícita do coordenador para auditoria e correções documentais compartilhadas. REL-PRE é este fechamento, não um novo card funcional; `ready` dos 43 cards existentes foi preservado.
**Sincronização posterior (09/11):** `dev` em `a7454bc89f8c7c854e578f7b03fa91bced059ff5` integrada na branch REL-PRE. #42 aprovado por A em `4cdae73` e mergeado às 11:34:25Z; revisão C registrada depois, na mesma branch, em [DOC-02_REVISAO_C_RUNTIME.md](DOC-02_REVISAO_C_RUNTIME.md) (§11). As execuções nativas anteriores continuam vinculadas a `8d07433`; somente validações documentais foram repetidas.

**Resultado:** fechamento PARTIAL. Correções DEF-01/02 integradas e verificadas; decisões, provas externas e revisão documental final continuam pendentes. Não é release pronta.

## 1. Fontes e estado verificável

Lidos AGENTS, MEMORY, planejamento, contratos, backlog, validação e documento mestre; conferidos README, checklist, Product/Sprint Backlogs, ADRs, evidências e templates de handoff. Nenhuma modificação em código produtivo, runtime, programas oficiais, legado ou arquivos das branches de B/C.

- `git fetch origin --prune`, `git switch dev`, `git merge --ff-only origin/dev` e criação da branch concluídos. Árvore inicial limpa. Branches remotas históricas de cards mergeados ainda existem; não foram removidas. `main` não foi promovida.
- GitHub: branch padrão `dev`, visibilidade **PUBLIC**; zero Issues retornadas. `#40`/`#41` são números de PRs, não Issues encontradas. Fonte operacional continua sendo [cards.json](../../planning/cards.json).
- Fotografia inicial, anterior à sincronização: PRs #1–#41 mergeados; PR então aberto: [DOC-02 #42](https://github.com/VictorBrasileiroo/minipar-2026-2/pull/42), base `dev`, autor José Riquelme, head `a346a59293a70569d2c43ee5b35d1fbc40fa244c`, sem reviews/checks retornados na consulta.
- Nenhuma branch, PR ou evidência específica de INT-02/DOC-04 localizada. Há seções WEB-05 no relatório, não um DOC-04 consolidado. Isto descreve o repositório consultado, não afirma ausência de trabalho local de outra pessoa.
- Fotografia com datas de merge, hashes e reviews: [REL-PRE_GITHUB.json](REL-PRE_GITHUB.json). Resultados locais persistidos, com comandos/saídas e caminhos pessoais substituídos: [REL-PRE_RESULTADOS.json](REL-PRE_RESULTADOS.json).

| Pendência / unidade | Estado deste fechamento | Evidência e limite |
|---|---|---|
| DEF-01 | DONE | #40 aprovado por C após corrigir espera interativa; merge 06/11 19:28:38Z; nova baseline T01 10/10 PASS no loopback |
| DEF-02 | DONE | #41 aprovado por C; merge 06/11 20:15:44Z; nova baseline T02 10/10 PASS; saída bruta conferida |
| Núcleo CORE-02–09 | DONE nos cards integrados | #14–#19/#29/#35; T03/T05/T06/T07 PASS; T07 mutação TAC e limites PASS; isto não aprova todos os programas possíveis |
| CORE-10 | DONE como relatório | #38 mergeado 06/11; histórico de FAIL anterior aos defeitos preservado, não reescrito como PASS |
| T04-TOL | PARTIAL | classificação e equivalência ao algoritmo PASS; equivalência numérica ao referencial histórico FAIL; decisão PENDING (§2) |
| T10 / ADR-014 | PARTIAL | #23, cálculo e seis tarefas documentados; grau 4 seq reexecutado; formato e prova específica em dois hosts PENDING (§3) |
| C-FJ-v1 / CON-01 | DONE | APPROVED por Victor em `a0fd60f`, #7; merge 26/10. Corrigido registro FROZEN, sem mudar contrato |
| C-WEB v1.1 | DONE na ratificação documental | #34: proposta de B e aprovações A/C em `204fe48`; merge 05/11. Registro de aceite corrigido; ressalvas preservadas |
| DOC-03 | DONE | #39 aprovado e mergeado 06/11; espelhos atualizados conforme fatos posteriores |
| DOC-02 | DONE | #42 aprovado por A em 4cdae73 e mergeado em a7454bc (09/11); ajustes conferidos, 853/853 sondas repetidas; revisão C APROVADO COM RESSALVAS (§11); correções RC-01..RC-06 aplicadas neste PR (§13) e aceitas por B na revisão de 10/11 (§14) |
| INT-02 | PARTIAL (integrado) | #44 aprovado por A e mergeado em `249afaa` (09/11, depois desta fotografia): T01–T03/T05–T11 PASS, T04 PARTIAL, três interfaces PASS; rede real BLOCKED. Validação C do recorte de runtime em §12 |
| DOC-04 | PENDING | sem relatório completo/PR localizado; DOC-02 já integrado; depende de INT-02 e aceite RUN-06; correções da UML aceitas por B (§14) |
| RUN-05 | PARTIAL | #36 integrado; `par_rede` PENDING, sem benchmark novo nesta auditoria |
| RUN-06 | PARTIAL | #37 integrado como documentação; review A explicitamente mantém reprodução por outro integrante e logs A/B PENDING |
| ADR-018 | PENDING | divergência PUBLIC versus proposta de privacidade; direitos não comprovados (§4) |
| REL-01 | BLOCKED para início | DOC-04 não entregue e `ready=false`; não foi iniciado, tag não criada |

Estados de card no JSON continuam no vocabulário existente: 35 DONE, 3 IN_PROGRESS, 0 IN_REVIEW e 5 BACKLOG (após integrar o #44). RUN-05 permanece IN_PROGRESS porque a entrega é parcial apesar do merge; RUN-06 e INT-02 (rede real BLOCKED) também. T09/T10 mantêm DONE de integração com PARTIAL explícito em `status_note`, conforme DOC-03 aprovado. Não confundir essas contagens com testes aceitos.

## 2. T04 — auditoria numérica e proposta para decisão

Fonte: [programa oficial](../../tests/teste4_rede_neural_xor.minipar), [esperado histórico](../../tests/expected_results/teste4_rede_neural_xor.expected.txt), [oráculo existente](../../scripts/baseline_t01_t07.py), relatórios [CORE-01](CORE-01_BASELINE_T01_T07.md) e [CORE-10](CORE-10_REGRESSAO_FINAL_T01_T07.md).

Rede 2–3–1, sigmoid/backpropagation online, taxa 0,5, pesos e vieses literais fixos. São 20000 épocas, amostras `00,01,10,11` nesta ordem; deltas ocultos usam os pesos de saída anteriores à atualização. Não há chamada aleatória. O arquivo esperado só informa quatro números a quatro casas; não acompanha a implementação geradora nem sua configuração de treinamento. Não é possível concluir que a diferença é erro do compilador, aleatoriedade ou outro algoritmo da referência.

| Entrada | Nativo atual | Referência | Diferença absoluta | Diferença relativa à referência |
|---|---:|---:|---:|---:|
| 00 | 0,00684395 | 0,0089 | 0,00205605 | 23,1017% |
| 01 | 0,986493 | 0,9769 | 0,009593 | 0,9820% |
| 10 | 0,989250 | 0,9758 | 0,013450 | 1,3784% |
| 11 | 0,0140296 | 0,0291 | 0,0150704 | 51,7883% |

A reprodução independente em Python, implementada apenas como sonda de auditoria, dá `0.006843949363778706`, `0.9864926370672501`, `0.9892503459073175`, `0.014029626978671725`. A tradução atual coincide com esses valores dentro de meia unidade da última casa impressa. A maior diferença nativo/modelo é `3,62933e-7`, na entrada 01, inferior a `5e-7` de arredondamento da impressão de seis algarismos significativos.

**Critério proposto, sem aprovação automática:**

1. Funcional: quatro saídas finitas em `[0,1]`; classificação `0,1,1,0` pelo ponto médio 0,5 da sigmoid. PASS observado. Esse ponto de decisão corresponde à classificação binária, não à tolerância para reproduzir um treinamento.
2. Equivalência da tradução: mesmos pesos, ordem, épocas e atualizações do modelo independente. Para valor `m` não nulo, erro de impressão de seis algarismos significativos limitado por `0,5 × 10^(floor(log10(abs(m))) − 5)`, mais `1e-12` de folga de comparação. PASS observado para os quatro valores. A folga é muito menor que a resolução impressa e não explica a divergência histórica; não é garantia universal de erro acumulado de treinamento ou de outras plataformas.
3. Equivalência ao esperado histórico a quatro casas: tolerância derivada da resolução do arquivo, `0,00005` absoluta, acrescida da meia unidade da impressão atual. FAIL nos quatro valores. Não ampliar para 0,02: não há distribuição amostral, análise de erro ou especificação que sustente esse aumento. O comentário histórico “com 0,02 passaria” é uma observação, não justificativa de aceite.

**Decisão do coordenador:** manter T04 PARTIAL até obter a implementação/configuração geradora do esperado, ou aprovar explicitamente aceite funcional + equivalência ao algoritmo atual com a ressalva de não equivalência histórica. Neste segundo caso, registrar qual critério foi aceito e quem aceitou; não substituir o arquivo oficial esperado ou o oráculo atual nesta entrega. A sonda independente repete as equações, não prova sozinha a correção matemática de todo o backpropagation. Linux/outra libm continuam UNTESTED.

## 3. T10 — o que está e não está demonstrado

Requisito no [documento mestre §8.5](../00_DOCUMENTO_MESTRE_INICIAL.md) e [Python fornecido](../fontes/Teste10_Python_referencia.py). Implementação/evidência no [T10](../../tests/2026_2/test10/README.md), programa e harness da mesma pasta.

| Aspecto | Referência | Implementação / evidência |
|---|---|---|
| Geometria | Tapete, Turtle recursivo, grau 4 | Regra iterativa de dígitos base 3 em MiniPar; harness com oráculo recursivo independente |
| Representação | Janela Turtle, quadrado azul com vazios brancos | ASCII no binário; SVG externo, células navy sobre fundo branco, a partir do stdout; não reproduz a API/janela Turtle |
| Sexto trabalho | Desenha após joins dos cinco processos | Seis forks antes do primeiro join; logs de seis workers no loopback no harness anterior |
| Carga seq/par | Referência omite Sierpinski no seq | Mesmas seis funções nos dois modos |
| Grau | 4 | Harness anterior executou graus 2 e 3; nesta auditoria, binário oficial executado em seq, carga 1000, grau 4, Mandelbrot 50×20×100 |
| Resultado novo | 81×81 | 4096 células cheias (`8^4`), igual caractere a caractere ao oráculo recursivo; PASS |
| Rede | Exigência de prova real | Provas anteriores T10 só no loopback; RUN-03 de outra demo não substitui T10 em dois PCs |

Proposta de resolução da ADR-014 registrada no [livro de decisões](../03_DECISOES.md): aceite interno de ASCII/SVG depende do coordenador; conformidade do formato alternativo com o professor continua PENDING até resposta identificável. Não há evidência de confirmação docente localizada. O grau 4 novo foi calculado, mas não foi feita uma nova inspeção visual do SVG nem repetida a concorrência de seis workers nesta auditoria. Sem nova renderização implementada.

## 4. ADR-018 — direitos e acesso

O snapshot local não contém licença/autorizações localizadas; [proveniência documentada](../08_ESTADO_DA_BASE_2026_1.md) aponta `luizwhirl/minipar-improvement`, main consultada em 15/10, sem comprovação do commit de origem. A consulta de 09/11 ao repositório atual confirmou PUBLIC. Não foi consultado novamente o estado de licença do upstream nem presumida inexistência de documentos fora do Git.

As alternativas e riscos estão na atualização da [ADR-018](../03_DECISOES.md): obter autorização escrita com escopo, restringir acesso por decisão explícita, ou negociar pacote entregável sem redistribuição não autorizada. Créditos não substituem permissão. Privacidade nova não desfaz cópias anteriores. Nenhuma visibilidade, licença, atribuição de titularidade ou história Git foi alterada.

## 5. Parecer técnico DOC-02 — histórico de a346a59 e integração de 4cdae73

**Estado atual:** PR #42 aprovado por Victor/A em `4cdae73` e integrado em `a7454bc`. Os dois ajustes de casos de uso foram corrigidos: UC08 estende UC07; UC12/UC13 estendem UC16 (execução). A inclusão UC13→UC14 também foi removida pelo autor, com worker como pré-condição. O apontamento sobre cobertura de `MiniParChannel` abaixo é uma observação histórica de REL-PRE; não foi exigido na review humana nem bloqueou o merge. Revisão C registrada em §11. O parecer abaixo se refere ao head anterior e não reabre automaticamente o PR integrado.

**Conclusão da inspeção anterior (a346a59):** material útil e substancialmente aderente ao núcleo; ajustes documentais abaixo precisam ser tratados antes do aceite técnico final. Nenhuma review/aprovação foi enviada ao GitHub e nenhum arquivo do PR foi modificado.

Conferidos componentes (§3), léxico/AST/parser/semântico/geradores (§4.1–4.7), CLI/Web original (§4.8.1), sequência serviço (§5.1) e observações de arquitetura (§7). São coerentes: AST→TAC e AST→C++ independentes; `CppTaskContext` no semântico consumido pelo backend; CLI/Web original por subprocesso e Web didática pelo serviço; mutex do DEF-02; geração nativa via `compile_cpp`/`run_bounded`; isolamento por requisição; registro de artefatos em memória e CPUlator externo/manual.

| Achado | Local no documento do PR | Correção recomendada |
|---|---|---|
| Relação `extend` de diagnóstico invertida | §2.1: `UC07 ... extend ... UC08`; §2.2 identifica UC08 como extensão | Seta do caso de diagnóstico UC08 para o caso base UC07, coerente com a própria Nota 2.1. Existência de nomes e renderização não detectam esse erro UML |
| Execução de tarefa modelada como extensão de geração/compilação | §2.1: UC12/UC13 estendem UC03 (gerar C++/binário), justificativa na Nota 2.1 | Distinguir compilar de executar o programa; tarefas são disparadas durante execução do binário, não pelo g++. Modelar extensão do caso de execução ou explicitar a abstração usada |
| Alegação de cobertura de comunicação legada não representada como classe | §6 remete `MiniParChannel` a §4.6; §4.6 só mostra `cpp_template` com strings de prólogo | Acrescentar o modelo mínimo de `MiniParChannel` (`sendData`/`receiveData`) ou corrigir a alegação e declarar o limite. A classe real está embutida na string C++ de `cpp_template.py`; a cobertura da sonda não enumera esse tipo |

A revisão C do runtime (§4.9/§5.2) foi feita depois desta inspeção (§11). Não se recomenda novo desenvolvimento de produção por esses achados. Os 17 diagramas renderizados são evidência do autor; renderização **UNTESTED nesta auditoria**.

Sonda do autor fixada no commit acima: **853/853 PASS**, exit 0 reexecutado localmente. O comando inicialmente foi rejeitado pela revisão automática de segurança por executar código da branch externa; após aprovação manual específica do usuário, a ação exata foi repetida e passou. O código foi carregado em memória para apontar `--doc` à cópia de inspeção; produção e PR permaneceram intactos. Resultado completo local em `output/rel_pre/doc02_review/results.json`; resumo versionado no JSON REL-PRE. A sonda confirma nomes, membros, cobertura e herança; não prova semântica das relações. Não repetidos os mutantes do autor.

INT-02/DOC-04: indisponíveis no remoto consultado na inspeção original, portanto avaliação de suas evidências **BLOCKED por ausência de entrega acessível**; nenhuma evidência inventada ou aprovada. O smoke local REL-PRE não substitui o card INT-02 de B. Depois, o INT-02 foi integrado no #44 (ver §12); DOC-04 continua sem entrega.

## 6. Verificações realmente executadas

Ambiente: Windows 11 `10.0.26200`, Python 3.12.4 da venv existente, G++ UCRT64 16.2.0 Rev6. `CXX` e diretório de DLLs no PATH apenas do processo; sem instalações globais. Comandos na raiz, Python invocado pelo caminho `.venv/Scripts/python.exe`, todos com `-B`:

| Comando / verificação | Resultado |
|---|---|
| `scripts/baseline_t01_t07.py --repeat 10` | Exit **1 por PARTIAL de T04**, sem novo FAIL: T01 10/10, T02 10/10, T03/T05/T06/T07 PASS; mutação TAC e limites PASS; igualdade com TAC histórico INFO |
| Conferência adicional dos stdout de T02 | 10/10 com linhas completas, fatorial 120 e sequência Fibonacci integral; o oráculo antigo isolado não bastava para atomicidade |
| `scripts/smoke_int01.py` | Exit 0, 25/25: A 8, B 8, C 9 PASS; worker loopback e cliente Flask sem servidor público |
| `docs/auditorias/REL-PRE_sondas.py` | Exit 0 dos recortes: equivalência XOR/modelo, classificação e T10 grau 4 PASS; o JSON explicita FAIL histórico do XOR e aceite PARTIAL |
| Sonda DOC-02 do head fixado | 853/853 PASS, exit 0 após aprovação manual; renderização e controles negativos não repetidos |
| Consultas Git/GitHub e reviews #7/#34/#37/#39/#40/#41 | Merges e aceites documentados; nenhuma review enviada |
| `scripts/validar_planejamento.py` | PASS, 43 IDs únicos, datas/dependências válidas e DAG sem ciclos |
| Verificação documental adicional | PASS: todos os `ready`, dependências, prazos e caminhos autorizados preservados contra origin/dev; JSONs válidos, AST da sonda válida e links relativos dos documentos editados existentes |
| `git diff --check` / diagnósticos do editor | PASS; sem erros de whitespace ou diagnósticos em cards/sonda. Avisos Git de conversão LF/CRLF não são falhas |

Artefatos nativos e logs brutos permanecem ignorados em `output/`. [JSON consolidado](REL-PRE_RESULTADOS.json) preserva entradas/saídas, hashes, resultados e limites de escopo. Não foram executados benchmark, duas máquinas, CPUlator, Java ou uma regressão integral de UI em navegador. As instruções de validação documental, diff e escopo estão no handoff do PR.

## 7. Decisões que exigem aprovação do coordenador

1. **T04:** escolher manter PARTIAL até recuperar o gerador histórico ou aceitar funcionalidade + equivalência ao algoritmo atual com ressalva explícita; nenhuma aprovação numérica presumida.
2. **ADR-014:** aceitar internamente ASCII/SVG como proposta do T10 e obter confirmação docente separada. Até isso, EM ABERTO.
3. **ADR-018:** escolher tratamento de privacidade/direitos e apresentar evidência de autorização/acesso. Nenhuma alteração externa feita.
4. **REL-01:** liberar início apenas após dependências/DoR, revisão do PR e checklist; tag/publicação fora desta autorização. Exceções a evidências abertas precisam ser explícitas, sem converter UNTESTED em PASS.

## 8. Dependências externas abertas

- **B/Riquelme:** DOC-02 integrado e aprovado por A; revisão C registrada (§11) e correções da UML aplicadas neste PR (§13): revisar e aprovar como dono do DOC-02. INT-02 integrado (#44, §12); falta a rede real com C. Disponibilizar DOC-04 com relatório/capa/links/anexos. Resultados de A/C devem entrar com seus limites.
- **C/Erasmo + outro integrante:** RUN-05 `par_rede`; reprodução RUN-06 por não autor com logs dos dois lados, falha e resultados; T09/T10 específicos em dois hosts se exigidos no aceite adotado.
- **Professor:** confirmar representação visual alternativa da ADR-014; interpretação do despacho remoto explícito (PEND-FJ-05) permanece sem confirmação docente localizada.
- **Titulares do legado/coordenação:** direitos de uso/redistribuição e origem do snapshot.
- **B + humano responsável:** confirmação humana no CPUlator; [PEND-T11-04](../../tests/2026_2/test11/evidencias/README.md) ainda requer execução do Java no caso 2. Hashes/prints existentes não equivalem a repetir essa etapa.
- **Coordenador + A/C:** conferir as ressalvas de rastreabilidade da CR-CORE05 (FJ-SEM-06/07/08) no relatório; #34 já registra aprovação de C e A do catálogo, sem exigir redecisão do contrato congelado. Restrições de listas de strings são documentadas, sem nova funcionalidade proposta.

## 9. Checklist para iniciar REL-01 e handoff

O [checklist de entrega](../11_CHECKLIST_DE_ENTREGA.md) contém a sequência objetiva: integrar este PR revisado; decidir T04/ADR-014/ADR-018; DOC-02 já integrado e revisão C registrada (§11) e UML corrigida (§13) e aceita por B (§14); INT-02 integrado (#44), concluir sua rede real e as provas externas; consolidar/revisar/integrar DOC-04; então autorizar `ready` de REL-01 e verificar build de checkout limpo. A dependência formal de REL-01 é DOC-04, ainda BACKLOG; o prazo vencido não autoriza pular o gate.

**Arquivos alterados:** README; contratos (somente registros de estado/aprovação); decisões; backlog; validação/aceite; checklist; Product/Sprint Backlogs; cards; este relatório; sonda documental e JSONs de GitHub/resultados. Não foi atualizado o conteúdo das evidências históricas CORE-01/CORE-10/DEF; na sincronização, apenas os registros de estado/cabeçalho/handoff do DOC-02 foram atualizados, preservando diagramas e resultados do autor.

**Documentos verificados sem edição:** AGENTS, MEMORY, planejamento geral, mestre, proveniência, BNF/pseudocódigos, CR-CORE05 e relatórios/evidências dos três eixos. **AGENTS.md e MEMORY.md não precisam mudar:** não houve nova regra, convenção, arquitetura ou fluxo; ownership e regra 11 foram aplicados. BNF/pseudocódigos continuam correspondentes porque não houve mudança de produção. README/CR-CORE08 receberam contexto atual para remover afirmações de aceite ainda pendente já superadas pelo #34.

**Impacto de interface:** nenhum; não mudou sintaxe, assinatura, campo, protocolo ou contrato congelado. **Próximos consumidores:** coordenador (decisões), B (DOC-02/INT-02/DOC-04), C (provas remotas/RUN-06) e revisor independente deste PR. Nenhum merge de PR pelo agente, tag, promoção de branch, aprovação automática de PR alheio ou declaração de entrega pronta foi realizado. A sincronização integrou origin/dev apenas na branch REL-PRE, conforme solicitação.

## 10. Handoff da sincronização com DOC-02 integrado

Documentos de estado atualizados: cards, backlog, Product/Sprint Backlogs, checklist, README, cabeçalho UML e handoff DOC-02, este relatório e evidências REL-PRE. Diagramas, scripts produtivos, contratos e decisões T04/T10/ADR-018 preservados. Validações reexecutadas: DOC-02 853/853; DOC-01 117/117; planejamento/JSON/links/diff e preservação de pendências conforme registro de sincronização no JSON. Não reexecutados binários, CPUlator, rede real, benchmarks ou Mermaid. `AGENTS.md`/`MEMORY.md` revisados, sem mudança necessária: apenas sincronização de estado, sem alterar regras, arquitetura ou fluxo. Próximos consumidores: C (revisão UML, feita em §11) e B (INT-02/DOC-04); REL-01 continua bloqueado.

## 11. Contribuição do Eixo C (09/11)

**Responsável:** Erasmo (Eixo C), na branch REL-PRE a pedido da coordenação. Nenhum código, contrato, diagrama ou `ready` alterado.

- **Revisão C da UML (runtime e runners):** [parecer](DOC-02_REVISAO_C_RUNTIME.md), **APROVADO COM RESSALVAS**. Componentes e classes do runtime conferem com `runtime/include/minipar_rt/` e com o gerador. Duas imprecisões a corrigir por B: RC-01 (o `join` gerado passa por `__fj_join`; dentro de tarefa vira `TASK_FAILED`, não `exit 1`) e RC-02 (fork sem destino passa `Destination::parse("local")`). RC-03..RC-06 são omissões menores. Aceite conjunto do DOC-02 continua PARTIAL até a correção.
- **Verificações executadas** (Windows 11, G++ 16.2.0 UCRT64, Python 3.14.7, antes de criar a `.venv` da §12): `runtime/tests/run_tests.py` 6/6 etapas PASS (17/17 casos de interop); `runtime/tests/interop_codegen.py` (a)/(b)/(c) PASS; `docs/auditorias/DOC-02_sondas_uml.py` 853/853 PASS. Tudo em loopback; **não prova dois computadores**.
- **Continuam PENDING para C:** RUN-05 `par_rede` e reprodução RUN-06 por outro integrante com logs dos dois hosts. Exigem dois computadores físicos; não foram executados nesta contribuição.
- **Estados atualizados (1ª contribuição, `4b1f03d`):** cards (DOC-02, DOC-04, nota), backlog, Product/Sprint Backlogs, checklist (UML componentes/classes e item de revisão C marcados; item novo para a correção de B), README, cabeçalho da UML e handoff DOC-02. `AGENTS.md`/`MEMORY.md` revisados: sem mudança de regra, arquitetura ou fluxo, portanto não precisam mudar.

## 12. Sincronização com o INT-02 (#44) e validação C (09/11)

**Responsável:** Erasmo (Eixo C). O #44 foi aprovado por Victor/A e mergeado em `dev` (`249afaa`, 12:04Z) depois da fotografia do §1. Isso deixou este PR em conflito com o `dev`.

- **Merge do `dev` na branch (`f6ffb72`):** conflitos só na linha/card do INT-02 em `docs/04_BACKLOG.md` e `planning/cards.json`. Fiquei com o texto do #44, que é o resultado real; nada do REL-PRE foi perdido. Isto também resolve a INT02-04 do relatório INT-02: CORE-10 `DONE` e DEF-01/02 corrigidos chegam ao `dev` com este PR.
- **Estado do INT-02:** IN_PROGRESS (integrado, aceite PARTIAL), na mesma regra do RUN-05: o merge não fecha a rede real, BLOCKED no #44. Contagem dos cards: 35 DONE, 3 IN_PROGRESS, 0 IN_REVIEW, 5 BACKLOG.
- **Validação C do runtime** (o card pede que A e C validem): [INT-02_VALIDACAO_C.md](INT-02_VALIDACAO_C.md) e [JSON](INT-02_VALIDACAO_C_RESULTADOS.json).
  - Comando: `scripts/regressao_int02.py --only T08,T09,T10,INT-01`, em `f6ffb72`; o código é igual ao de `8d07433` (só o orquestrador foi adicionado).
  - Resultado: T08 32 + 1 INFO, T09 54/54, T10 126/126, smoke A 8 + B 8 + C 9, iguais ao INT-02, numa segunda máquina.
  - Ambiente: Python 3.12.10 e Flask 3.0.0 numa `.venv` local criada pelo guia de setup.
  - Só loopback.
- **Atualizados:** cards (INT-02, DOC-04), backlog (tabela e ficha do INT-02), Product/Sprint Backlogs, checklist (INT-02 entregue e validado; item novo para a rede real) e este relatório (§1, §5, §8, §9).
- **Não alterados:** código, contratos, testes, o relatório INT-02 do B e os diagramas. `AGENTS.md`/`MEMORY.md` revisados, sem mudança necessária.

## 13. Correções da UML pela revisão C (09/11)

**Responsável:** Erasmo (Eixo C), a pedido do próprio Eixo C. Como a UML é do DOC-02 (Eixo B), a mudança foi feita **neste PR**, cuja revisão foi pedida ao Riquelme, dono do documento. A aprovação dele vale como aceite de B às correções.

- **Arquivo alterado:** `docs/15_UML_MINIPAR_2026_2.md` (§2.1, Nota 2.1, §2.2, §4.6, figura 4.9b e legenda, §5.2 e texto). Detalhe por item no [§5 do parecer C](DOC-02_REVISAO_C_RUNTIME.md#5-correções-aplicadas-0911-pr-43).
- **RC-01/RC-02** (contrariavam o código gerado): `join` via `__fj_join` (fluxo principal → `join_or_exit`; dentro de tarefa → `join` + exceção → `TASK_FAILED`); `fork` sem destino passa `Destination::parse("local")`.
- **RC-03..RC-06** (omissões): uso do `Executor` pelo remoto e pelo worker; `state_`/`sock_` de `RemoteConnection`; falhas e timeouts na §5.2; runners incluem UC14.
- **Verificação:** sonda DOC-02 **862/862 PASS** (eram 853: mais 2 classes, 2 membros e 5 arestas). `mermaid.parse` do `mermaid@11.4.1` (a versão do autor): **17/17 sem erro**; o controle negativo pegou 3/3 blocos quebrados. Não houve renderização visual em navegador; o GitHub renderiza na revisão.
- **Estado:** RC-01..RC-06 resolvidos e aceitos por B na revisão de 10/11 (§14).

## 14. Ajustes pedidos na revisão de B ao #43 (10/11)

**Responsável:** Erasmo (Eixo C). Riquelme (B, dono do DOC-02) revisou o head `43a7c34` em 10/11. Aceitou o conteúdo técnico de RC-01..RC-06 e pediu quatro correções bloqueantes e cinco não bloqueantes. Todas foram aplicadas neste PR.

- **Sonda REL-PRE (`REL-PRE_sondas.py`):**
  - Itens 1 e 2: os filhos Python rodam com `PYTHONUTF8=1` e `PYTHONIOENCODING=utf-8`, e o stdout do script é reconfigurado para UTF-8. O home em forma POSIX também é substituído. Se ainda sobrar `\ufffd` ou o nome do usuário no relatório, o script falha sem gravar o JSON.
  - Item 8: sem os marcadores do Sierpinski, o T10 grau 4 é registrado como FAIL (`markers_found: false`), sem `IndexError`.
  - Item 9: leitura do esperado do XOR com `encoding='utf-8'`.
- **Estados (itens 3, 4 e 7):** cabeçalho do backlog conferido contra `dev` `249afaa` (#44), com a contagem do `cards.json`: 35 DONE, 3 IN_PROGRESS, 0 IN_REVIEW, 5 BACKLOG. Para o DOC-02 foi adotada a opção (b) de B: manter `DONE` e registrar o aceite dele neste PR. As frases "aprovação de B pendente" saíram de cards, README, UML, backlog, checklist, Product/Sprint Backlogs, parecer C e handoff DOC-02. O critério de `DONE` (entregável integrado; resultado de teste à parte) ficou explícito no backlog e no CORE-10. O checklist não chama mais RC-03/RC-04 de pendentes.
- **UML §5.2 (itens 5 e 6, sugeridos por B):** o diagrama mostra `BAD_DESTINATION` para destino inválido, `UNKNOWN_FUNCTION`/`TASK_FAILED` vindos do worker e o `TIMEOUT` caindo nos ramos de erro (exit 1 no fluxo principal, `TASK_FAILED` dentro de tarefa). O texto diz que o handle reutilizável após `TIMEOUT` só existe na API C++. Conferido em `runtime/include/minipar_rt/api.hpp` (`start`, `join_or_exit`), `core.hpp` (`execute`) e `src/cpp_template.py` (`__fj_join`).
- **Verificação (Windows 11, Python 3.12 da venv, G++ UCRT64):**

| Comando | Resultado |
|---|---|
| `REL-PRE_sondas.py` com `PYTHONIOENCODING=cp1252` no processo pai | exit 0, PASS (XOR modelo/classificação, T10 grau 4 81×81); JSON sem `\ufffd` nem nome do usuário |
| Filho Python imprimindo `C:\Users\JoséRiquelme`, com locale cp1252 | sem o env da sonda: `Jos\ufffdRiquelme` (o defeito de B); com o env: caminho intacto |
| `DOC-02_sondas_uml.py` | 862/862 PASS |
| `mermaid.parse` (`mermaid@11.4.1` + jsdom, pasta isolada fora do repositório) | 17/17 sem erro; controle negativo 17/17 erros detectados |
| `scripts/validar_planejamento.py` | OK, 43 cards, DAG sem ciclos |

- **Não alterados:** código, contratos, testes e `REL-PRE_RESULTADOS.json` (evidência de `8d07433`, sem `\ufffd` nem caminho pessoal). Não houve renderização visual dos diagramas. `AGENTS.md`/`MEMORY.md` revisados, sem mudança necessária. Nenhum código, contrato ou teste alterado.
