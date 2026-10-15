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
