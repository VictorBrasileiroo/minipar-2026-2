# Registro de Decisões Técnicas — MiniPar 2026.2

Regras: decisões registram **estado** (`CONFIRMADA`, `PROPOSTA`, `EM ABERTO`, `SUPERADA`), impacto, evidências e data. Não mudar contratos em silêncio. Encaminhar a mudança de contrato como CR.

| ID | Estado inicial | Decisão e justificativa | Efeito |
|---|---|---|---|
| ADR-001 | CONFIRMADA | Evoluir a base MiniPar 2026.1; evitar reescrever um compilador inteiro | Importação/legado imutável |
| ADR-002 | CONFIRMADA | Criar repositório novo do trio, com código anterior em `legacy/minipar-2026.1/` e cópia ativa na raiz | Isola base e desenvolvimento |
| ADR-003 | CONFIRMADA | Eixo A = coordenador, dono de `src/`; B/C nomes em aberto | Reduz concorrência de agentes |
| ADR-004 | CONFIRMADA | Manter terminal e Web anterior; criar Web didática separada | Não quebrar interfaces antigas |
| ADR-005 | CONFIRMADA | Metas 03/11 freeze, 04–10/11 estudo, 11/11 entrega | Gates e escopo priorizado |
| ADR-006 | CONFIRMADA | GitHub + documentação Markdown + Issues/Projects depois de revisar docs; não usar planilha/Jira como fonte primária | Tarefa e código próximos |
| ADR-007 | CONFIRMADA | `AGENTS.md` obrigatório, revisão por card/PR, propriedade de arquivos | IA não reescreve outro eixo |
| ADR-008 | PROPOSTA | Implementar Fork/Join local e remoto usando workers de binário previamente compilado e mensagens identificadas | Evita closures/código remoto |
| ADR-009 | PROPOSTA | C-FJ-v1 com mensagens enquadradas e `join` por ID/timeout | Contrato a congelar no G0 |
| ADR-010 | PROPOSTA | Web didática consome serviço único de fases; trabalhar com fixtures enquanto A não entrega API | Paralelismo de desenvolvimento |
| ADR-011 | PROPOSTA | Teste 11 implementado integralmente em MiniPar como aplicação; não adicionar backend ARM universal ao hospedeiro | Reduz escopo |
| ADR-012 | EM ABERTO | Quem salva `.arm`: MiniPar diretamente vs executor hospedeiro | Consultar requisito/validar |
| ADR-013 | EM ABERTO | Sintaxe específica de Fork/Join e semântica de destino remoto | G0; não inventar como requisito oficial |
| ADR-014 | EM ABERTO | Saída aceita para Sierpinski (janela nativa, SVG, outra) | Definir para Teste 10 |
| ADR-015 | CONFIRMADA | TAC e backend C++ são gerados da AST, em ramos independentes na base; não fingir TAC → C++ | Documentar pipeline real |
| ADR-016 | CONFIRMADA | Hardcode TAC do Quicksort deve ser eliminado e substituído por geração real | Validar mutação de programa |
| ADR-017 | CONFIRMADA | Não declarar execução distribuída sem duas máquinas reais | Prova em rede |
| ADR-018 | PROPOSTA | Repositório novo privado inicialmente até esclarecer direitos de redistribuição da base sem licença explícita | Evitar publicação indevida |
| ADR-019 | CONFIRMADA | `dev` é a branch padrão (remoto com `HEAD` em `dev`, conferido em 19/10/2026): branches de card nascem dela e PRs apontam para ela; `main` só recebe promoção decidida pelo coordenador. Todo merge exige pelo menos uma aprovação de revisor que não seja o autor | Atualiza a regra de PR contra `main` do `AGENTS.md`; configuração da proteção no GitHub conferida no SET-03 |

## Estado das decisões em 05/11/2026

Revisão do card `DOC-03` contra o que foi implementado e mergeado em `dev` (`59ea77d`). A coluna "Estado inicial" acima fica como registro histórico. Mudanças de estado que tocam decisões de A ou B valem depois da aprovação deles neste PR. Nada aqui redecide uma ADR: só registra a evidência de que a proposta foi adotada, ou aponta divergência.

| ID | Estado inicial | Estado em 05/11 | Evidência / observação |
|---|---|---|---|
| ADR-008 | PROPOSTA | **CONFIRMADA** | Implementada no runtime: workers do mesmo binário, mensagens identificadas por `task_id` (RUN-02 #9, RUN-04 #20); usada pelo backend (CORE-07 #18) e provada entre dois computadores (RUN-03 #10) |
| ADR-009 | PROPOSTA | **CONFIRMADA** | C-FJ-v1 aprovado por A e mergeado (CON-01 #7, 26/10); frames e `join` por ID/timeout implementados (RUN-02 #9). Pendência: o cabeçalho do C-FJ-v1 em `02_CONTRATOS_TECNICOS.md` §2 ainda diz "proposta de congelamento"; registrar `v1 FROZEN` como o #25 fez para C-WEB/C-T11 (coordenador) |
| ADR-010 | PROPOSTA | **CONFIRMADA** | Serviço único de fases (CORE-08 #19) consumido pela Web didática real (WEB-03 #30, WEB-04 #31); fixtures só no desenvolvimento (WEB-01 #12) |
| ADR-011 | PROPOSTA | **CONFIRMADA** | MiniCompilador escrito em MiniPar, sem backend ARM no hospedeiro (T11-01/02/03 #26–#28) |
| ADR-012 | EM ABERTO | **CONFIRMADA**: exportação pelo executor | C-T11-v1 §3.6.1 (PR #2, `v1 FROZEN` em 22/10): o `.arm` é o bloco copiado da saída, como na referência do professor; PEND-T11-02 resolvida, com pedido de registro nesta ADR (C-T11-v1, quadro de pendências) |
| ADR-013 | EM ABERTO | **CONFIRMADA** | Sintaxe e semântica de Fork/Join e destino remoto adotadas pelo A (CORE-04/05 #15, `docs/CR-CORE05-FJ-DECISOES.md`), BNF em `12_BNF_MINIPAR_2026_2.md` (DOC-01 #32) |
| ADR-014 | EM ABERTO | **EM ABERTO** | Proposta do T10 (#23): Sierpinski em ASCII + SVG gerado pelo harness a partir da saída. Falta decisão do coordenador (CT-07) |
| ADR-018 | PROPOSTA | **DIVERGENTE** | Em 05/11 o repositório no GitHub está **público** (`gh repo view`: `PUBLIC`), ao contrário da proposta de mantê-lo privado. Decisão do coordenador: confirmar a publicação ou voltar a privado. Os logs de evidência do Eixo C já saem mascarados (RUN-05, RUN-06) |
| ADR-001–007, 015–017, 019 | CONFIRMADA | sem mudança | — |

## Padrão para novas decisões

```text
### ADR-0XX — Título
- Data e autoria:
- Estado:
- Contexto e restrições:
- Alternativas comparadas:
- Decisão:
- Motivos:
- Componentes afetados:
- Testes/evidências:
- Migração / reversão:
- Data de revisão:
```

**Alterações já aprovadas em documento mestre não devem ser "redecididas" por agentes por conveniência.** Quando as evidências contrariarem uma decisão, abrir ADR/CR e solicitar revisão ao trio.
