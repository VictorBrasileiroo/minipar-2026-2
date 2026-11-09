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
| ADR-009 | PROPOSTA | **CONFIRMADA** | C-FJ-v1 aprovado por A e mergeado (CON-01 #7, 26/10); frames e `join` por ID/timeout implementados (RUN-02 #9). Atualização REL-PRE em 09/11: cabeçalho e aprovação em §2.10 corrigidos para `v1 FROZEN` com a review real do #7; sem mudança de contrato |
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

## Revisão REL-PRE — 09/11/2026 (decisões ainda não tomadas)

### ADR-014 — proposta de resolução em duas etapas

- **Estado:** EM ABERTO. Parecer técnico favorável ao recorte calculado; não é aceite do coordenador nem do professor.
- Referência e requisito: documento mestre §8.5 e [Python fornecido](fontes/Teste10_Python_referencia.py): Turtle, grau 4; a referência só desenha após cinco joins e omite Sierpinski na carga sequencial.
- Implementado (#23): seis forks antes dos joins; Sierpinski iterativo em MiniPar retorna ASCII; harness produz SVG a partir desse texto; modos seq/par executam as mesmas seis chamadas. Não há janela Turtle no binário.
- Evidência adicional REL-PRE: grau 4 real, 81×81 e 4096 células cheias, igual ao oráculo recursivo. Isso prova o cálculo; não demonstra aceite do formato nem seis computadores/núcleos exclusivos.
- **Proposta para decisão do coordenador:** aceitar internamente ASCII + SVG externo como representação visual, registrar a divergência de Turtle e manter confirmação docente PENDING. Só registrar CONFIRMADA internamente após aprovação explícita. Se o professor exigir janela nativa, reabrir escopo por card autorizado; nenhuma renderização nova nesta entrega.
- Próxima evidência externa: resposta do professor com data/autor e demonstração do SVG; T10 em duas máquinas continua UNTESTED.

### ADR-018 — divergência de privacidade e direitos sobre o legado

- **Estado:** DIVERGENTE / PENDING de decisão da coordenação. GitHub consultado em 09/11: PUBLIC, branch padrão dev. A linha inicial era PROPOSTA de privacidade; não foi encontrada decisão posterior que documente sua substituição.
- Proveniência: [estado da base §6](08_ESTADO_DA_BASE_2026_1.md), `luizwhirl/minipar-improvement`, main consultada em 15/10/2026; sem licença declarada na consulta original. Nenhum LICENSE/LICENÇA/COPYING versionado foi localizado no snapshot local. Isso não prova inexistência de autorização fora do repositório.
- Riscos concretos: exposição do snapshot e derivados sem permissão de redistribuição comprovada; atribuição incompleta; circulação de PDFs/referências e dados de logs. Acesso público ao repositório de origem, crédito acadêmico e eventual autorização de uso em aula não demonstram, por si, permissão para redistribuir.
- Alternativa A: obter autorização escrita dos titulares, delimitando cópia, derivados, acesso público e materiais anexos; registrar origem e créditos com evidência, sem relicenciar material alheio.
- Alternativa B: decidir acesso privado/restrito enquanto esclarece direitos; registrar eventual conflito com o acesso exigido na entrega. Mudar visibilidade exige ação explícita da coordenação; não remove clones anteriores.
- Alternativa C: negociar com titulares/professor um pacote entregável sem material não autorizado, mantendo origem rastreável. Remoção do legado ou reescrita de histórico exige autorização e planejamento próprios; snapshot imutável não foi tocado.
- Nesta entrega: nenhuma alteração de visibilidade, licença, histórico ou declaração de autorização. Coordenador escolhe tratamento e apresenta a evidência; nenhuma alternativa foi executada.

Detalhamento, números do XOR, parecer DOC-02 e dependências: [relatório REL-PRE](auditorias/REL-PRE_FECHAMENTO_EIXO_A.md).
