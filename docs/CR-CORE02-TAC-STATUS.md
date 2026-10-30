# CR-CORE02-TAC-STATUS — proposta documental, 26/10/2026

Estado: PROPOSTA, sem alteração aplicada ao contrato. Fornecedor A e consumidor B devem revisar antes da integração CORE-08.

Contrato anterior: C-WEB-v1 §1.5 contém `TAC_HARDCODED`; PEND-WEB-05 descreve o warning temporário até CORE-02. Na base histórica isso corresponde ao gerador real; no head do PR #16 o hardcode foi removido.

Proposta: depois de integrar #16, registrar PEND-WEB-05 como resolvida por esse commit; manter o código no catálogo como histórico/inativo. N?o emitir warning de hardcode quando o gerador percorre a AST. Se for necessário remover o código do catálogo ou mudar o envelope, versionar por CR aprovada; esta manutenção não muda schema, fixtures ou eventos congelados.

Motivo: impedir que CORE-08/Web relatem hardcode inexistente ou tratem o snapshot antigo como oráculo novo. Consumidores: B/Web, CORE-06/08/10. Migração: conferir ancestralidade do commit integrado e usar o comportamento do gerador daquela compilação. Testes: cinco regressões TAC, T07 mutado, execução nativa/assertions e serviço real no CORE-08. Evidências da rodada atual no handoff CORE-02. Data de revisão: antes de CORE-08.
