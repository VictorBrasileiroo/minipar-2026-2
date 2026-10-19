# Guia de operação com Codex, Git, revisões e handoffs

## 1. Por que este guia existe

O maior risco de usar três agentes em paralelo é **alterar contratos e arquivos centrais ao mesmo tempo**. Portanto, cada agente trabalha em **um card por vez**, com dono de arquivos, DoR/DoD e interfaces acordadas. Não é permitido substituir especificação por "o agente sabe o que fazer".

## 2. Ponto de partida antes de toda sessão

1. Abrir o repositório **novo** e a branch do card; confirmar que não está em `legacy/`.
2. Consultar `MEMORY.md`, quando existir, e ler `AGENTS.md`, `docs/01_PLANEJAMENTO_GERAL.md`, `docs/02_CONTRATOS_TECNICOS.md` e a ficha do card antes de iniciar a tarefa.
3. Confirmar dependências prontas, owners, branch e `git status` limpo.
4. Registrar tempo disponível da sessão e critério de parada.
5. Só então dar a tarefa ao Codex. **Não liberar agente B/C para editar `src/`**.

## 3. Modelo de prompt por card

```text
Você está no MiniPar 2026.2, eixo [A/B/C], card [ID].
CONSULTE MEMORY.md, quando existir, e LEIA AGENTS.md e os documentos de contrato/plano ligados ao card.

Objetivo verificável: [entrega, não descrição vaga].
Dependências liberadas: [IDs / contrato frozen / fixtures].
Arquivos que PODE modificar: [lista].
Arquivos PROIBIDOS: [lista, especialmente legacy/ e src/ para B/C].
API/contrato obrigatório: [referência docs/02].
Teste mínimo exigido: [comando/entrada/oráculo].
Regressão necessária: [subset relevante dos testes].
Prazo/timebox: [período, não force solução incorreta].
Não faça refatoração fora do escopo nem invente resultado esperado.
Se faltar API/contrato, pare, reporte BLOCKED e descreva pedido de mudança.
Ao terminar, devolva: resumo do diff, comandos exatos, evidências, FAIL/BLOCKED e HANDOFF.
MANDATORY: aplique a regra 11 de AGENTS.md antes de concluir: verifique a documentação impactada e sempre revise a necessidade de atualizar AGENTS.md; inclua as atualizações necessárias na mesma entrega/PR. Registre o resultado no resumo final e no HANDOFF; justifique explicitamente quando nenhuma atualização documental for necessária e quando AGENTS.md não precisar mudar.
Não faça merge em main nem instale dependências globalmente.
```

## 4. Branches e PRs

Nomes: `eixo-a/CORE-03-strings`, `eixo-b/T11-02-arm`, `eixo-c/RUN-02-protocolo`. Separar branches por card, preferir PRs pequenos e apontar `Closes #...` **depois** de criar Issues. PR de contrato usa prefixo `contract/CR-XX`.

PR deve incluir:
- Card e objetivo.
- O que mudou.
- Verificação documental obrigatória (regra 11 de `AGENTS.md`): documentos verificados/atualizados e resultado da revisão de `AGENTS.md`, com justificativa quando não houver atualização necessária.
- Quais arquivos mudou (comparar com ownership).
- Como testar e quais comandos foram executados.
- Saída/oráculo.
- Implicações para outro eixo.
- Pendências e riscos.
- Fotos/screenshots quando UI/CPUlator/rede.
- Aprovação do consumidor da API quando integração.

PR que altera `src/` sem dono autorizado deve ser recusado, mesmo que o código "pareça bom".

## 5. Regras específicas por eixo

### Eixo A
- Não reescrever runtime do C sem CR.
- Não alterar o formato JSON Web sem consultar B.
- Priorizar regressão T01–T07 e prova `MiniPar→C++→binário`.
- Descrever semântica Fork/Join de forma coerente em BNF/AST/semântico/TAC/C++.
- Comunicar readiness de strings a B e integração FJ a C.

### Eixo B
- Começar Web com fixtures, mas **retirar fixtures do fluxo principal** na integração.
- Teste 11 precisa ser **código MiniPar**, não gerador ARM implementado em Python/JS.
- ARM impresso não é PASS: executar CPUlator.
- Se `len`/`substr`/listas falharem, abrir caso mínimo para A.
- Não editar `app.py` antigo ou `src/` sem CR; criar aplicativo/adapter em `web_didatica/`.

### Eixo C
- Começar runtime com C++ isolado, usando contrato aprovado.
- `localhost` prova protocolo, não prova 2 máquinas.
- Worker faz cálculo verdadeiro, não devolve strings fixas.
- Join deve associar IDs corretamente, tratar falhas e não aguardar eternamente.
- Testes 8–10 precisam ser programas MiniPar para entrega, não só versões C++/Python.
- Não editar `codegen.py`; levar header/API testado para A.

## 6. Cadência

- **Início de dia:** olhar prioridade P0 e dependências, escolher 1–2 cards de maior valor.
- **Durante:** timebox para bloqueios, registrar no card; não improvisar feature lateral.
- **Fim:** status 3 linhas: feito/comprovado, bloqueado, próximo.
- **Gate:** demo real com três participantes, decisão `PASSOU/PARCIAL/BLOQUEADO`.
- **03/11:** tag release candidata; não inserir features novas sem revisão de risco.
- **04–10/11:** estudo/ensaios e apenas correções críticas.

## 7. Segurança e privacidade

- Verificar comandos antes de executar, especialmente rm/clean, instalação e rede.
- Não publicar logs com IPs sensíveis, diretórios privados, tokens ou dados pessoais.
- Serviço Web executa binários gerados: não hospedá-lo publicamente sem sandbox.
- Não enviar `.env`, credenciais, senhas ou sessões de Git para agentes.
- Preservar autoria da base anterior e verificar direitos antes de publicação pública.

## 8. Fluxo de escalada em 5 linhas

1. **Pare** se o contrato estiver inadequado.
2. Monte um **reprodutor mínimo**.
3. Abra pedido à pessoa dona da interface.
4. Só após aprovação mude os dois lados, cada um em sua branch.
5. Execute teste de contrato antes de marcar DONE.

## 9. Ferramentas

Git/GitHub e Markdown bastam. Depois da revisão dos documentos, converter `planning/cards.json` em GitHub Issues/Projects. **Não criar outro Kanban paralelo** sem sincronização; após criar Issues elas passam a ser a fonte oficial de estado.
