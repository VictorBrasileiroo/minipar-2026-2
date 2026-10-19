# AGENTS — Contrato operacional para pessoas e agentes Codex

**MANDATORY — Antes de iniciar qualquer nova tarefa:** consultar `MEMORY.md`, quando existir, e este arquivo. A política de manutenção documental da regra 11 é permanente e obrigatória para todas as futuras execuções do Codex neste projeto.

**Obrigatório:** ler `docs/01_PLANEJAMENTO_GERAL.md`, `docs/02_CONTRATOS_TECNICOS.md`, `docs/04_BACKLOG.md`, `docs/05_VALIDACAO_E_ACEITE.md` antes de modificar código. O contexto consolidado está em `docs/00_DOCUMENTO_MESTRE_INICIAL.md`.

## Regras inegociáveis

1. **Uma única fonte de verdade:** documentação normativa em `docs/`, cards em `planning/cards.json` (antes das Issues) e depois GitHub Issues; implementação via PR.
2. **Não editar `legacy/minipar-2026.1/`.** Referência imutável. Nunca gerar artefatos dentro de `legacy/`.
3. **Respeitar propriedade de arquivos.**
   - Eixo A: raiz original ativa (`src/`, `main.py`, `app.py`, `menu.py`, `templates/`, `static/` e testes herdados), camada de serviço de compilação e interfaces com runtime. B e C não editam esses arquivos sem permissão registrada.
   - Eixo B: `web_didatica/`, `tests/2026_2/test11/`, produção de BNF/UML/pseudocódigos e relatório em `docs/` **apenas nos cards atribuídos**, sempre com aprovação de A/C nas partes técnicas. Não reimplementar Lexer/Parser do **compilador hospedeiro**; o MiniCompilador escrito em MiniPar tem seu próprio lexer como aplicação de Teste 11.
   - Eixo C: `runtime/`, `tests/2026_2/test08/`, `test09/`, `test10/`, execução de QA 1–7 e atualização de backlogs **apenas nos cards atribuídos**, sem mudar `src/`. Não editar `src/`.
   - Arquivos partilhados (`README.md`, `AGENTS.md`, `planning/cards.json`, `docs/02_CONTRATOS_TECNICOS.md`, CI): coordenador autoriza modificações; a edição do backlog pelo C e do relatório pelo B ocorre por card atribuído e PR revisado.
4. **Sem alterações de interface em silêncio.** Se precisar de assinatura/campo/evento diferente, abrir pedido de mudança (ver contrato), não alterar de forma unilateral.
5. **Cada card é uma unidade de entrega.** Começar somente quando `ready=true` e dependências atendidas ou mock contratual aprovado.
6. **Sem falsos positivos.** Gerar TAC/C++ não prova compilação; `exit=0` não prova resultado; localhost não prova execução entre computadores; texto ARM não prova execução no CPUlator.
7. **Preservar implementações reais.** Proibido introduzir saídas esperadas hardcoded para satisfazer testes. Não sacrificar tratamento correto para demos.
8. **Sem retrabalho voluntário.** Não reformatar ou refatorar arquivos de outro eixo. Mudanças extras precisam de card e aprovação.
9. **Operação segura.** Não instalar dependências globalmente, executar comandos destrutivos, sobrescrever arquivos históricos, abrir portas públicas, alterar PATH do sistema ou publicar repositório sem autorização.
10. **Sem trabalho tácito.** Ao final de cada card registrar: arquivos alterados, testes realizados/comandos, evidências, pendências, impacto de interface, próximo consumidor.
11. **Documentação acompanha o código.** Diagramas, BNF e pseudocódigos devem refletir a implementação verdadeira.
    **MANDATORY — Manutenção documental como critério de conclusão:**
    - Após cada implementação, correção, refatoração ou alteração relevante, verificar a documentação impactada e atualizar o que for necessário (`README.md`, documentação técnica, APIs, guias e demais documentos aplicáveis).
    - Sempre verificar se `AGENTS.md` precisa de atualização e atualizá-lo quando houver mudanças nas instruções, convenções, arquitetura, padrões ou fluxo de desenvolvimento.
    - Nenhuma implementação está concluída sem essa verificação. Incluir as atualizações documentais necessárias na mesma entrega/PR da implementação, respeitando ownership, aprovações e CRs existentes.
    - No resumo final e no handoff/PR, registrar documentos verificados e atualizados e o resultado da revisão de `AGENTS.md`. Se nenhuma atualização documental for necessária, informar isso explicitamente no resumo final, com justificativa; justificar também quando `AGENTS.md` não precisar mudar.
    - Preservar regras existentes, evitar duplicações e conflitos e não modificar documentos que não foram impactados. Estas obrigações não são recomendações opcionais.
12. **Escalonar bloqueios cedo.** Se falta API, contrato, ambiente ou teste, registrar `BLOCKED` e comunicar responsável. Não improvisar mudança estrutural.

## Passo a passo obrigatório por card

**Antes:** identificar ID, dono, objetivo, arquivos autorizados, dependências, critério de aceite; ler contratos; criar branch `eixo-<a|b|c>/<ID>-resumo`.

**Durante:** implementar alteração mínima; adicionar testes locais; verificar regressão pertinente; registrar problemas; não invadir arquivos alheios.

**Depois:** produzir resumo de handoff em `docs/templates/TEMPLATE_HANDOFF.md` ou corpo do PR; demonstrar entradas/saídas; abrir PR contra `main`; não fazer merge sem checagens e aprovação conforme regra do time.

**Ao integrar:** contrato satisfeiro, smoke test, teste de regressão e evidências. O dono da interface verifica a compatibilidade. Documentos atualizados. Só então marcar `DONE`.

## Mudança de contrato (CR)

Abrir PR/documento com: contrato anterior, novo contrato proposto, motivo, consumidores afetados, plano de migração, testes e data. A coordenação aprova após consulta aos consumidores. Não alterar `frozen` sem CR.

## Convenções de provas

- `PASS` = teste realmente executado com oráculo verificado.
- `FAIL` = executado e divergente.
- `BLOCKED` = impossível executar/testar com bloqueio identificado.
- `UNTESTED` = ainda não executado.
- `PARTIAL` = recorte demonstrado, não a exigência completa.

## Uso de IA

Não afirmar que a revisão por ChatGPT/Codex equivale a execução local. Os responsáveis humanos conferem logs, comandos, diff e demonstração. Manter `main` executável sempre que possível.
