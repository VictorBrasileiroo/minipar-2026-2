# HANDOFF — DOC-02

**Responsável:** José Riquelme (Eixo B) | **Branch/PR:** `eixo-b/DOC-02-uml` → `dev` | **Data:** 09/11/2026 | **Contrato usado:** C-WEB-v1 §1.2–1.8, C-FJ-v1 §2.3–2.6, C-T11-v1 §3.3–3.4; `00_DOCUMENTO_MESTRE_INICIAL.md` §11

Base: `origin/dev` em `8d07433` (09/11/2026; branch criada sobre `59ea77d` e atualizada com o `dev`). Dependência do card: `INT-01` integrado (PR #24, merge `3940ae7`).

**Estado após integração (REL-PRE, 09/11):** PR #42 mergeado em `a7454bc` às 11:34:25Z; review APPROVED de Victor/A sobre `4cdae73` às 11:31:33Z. DONE de integração; revisão C registrada em 09/11 como APROVADO COM RESSALVAS ([parecer C](DOC-02_REVISAO_C_RUNTIME.md)), com RC-01/RC-02 a corrigir por B; aceite conjunto PARTIAL até essa correção. Fonte: [snapshot de sincronização REL-PRE](REL-PRE_GITHUB.json). Sondas reexecutadas na árvore sincronizada: 853/853 PASS. As seções de implementação/verificação originais abaixo preservam o histórico.

**Atualização de 09/11 (histórico anterior ao merge):** o `dev` recebeu o `DOC-03`, que criou `docs/14_PRODUCT_E_SPRINT_BACKLOGS.md`; a UML passou de `14_` para `docs/15_UML_MINIPAR_2026_2.md`. As mudanças de código que vieram junto (`CORE-09`, `DEF-01`, `DEF-02`) foram refletidas: `main.compile_file` captura o `SystemExit` do parser, `print` é atômico (`__minipar_print_mutex`) e `app.py` ganhou `_requested_test_path` e nomes `ide_<uuid>` em `/api/compile`.

**Ajustes da revisão do PR (09/11):** o revisor apontou dois erros nas relações do diagrama de
casos de uso (seção 2), ambos corrigidos:

| Apontado na revisão | Antes | Depois |
|---|---|---|
| `«extend»` invertido | `UC07 → UC08` | `UC08 → UC07`: o diagnóstico (UC08) estende a inspeção (UC07) quando há erro |
| Fork/Join ligado à geração | `UC12`/`UC13` estendiam `UC03` (gerar C++ e binário) | Novo `UC16 Executar o binário gerado`, incluído por `UC04`, `UC06`, `UC09` e `UC15` e usado pelo programador; `UC12`/`UC13` estendem `UC16` |

Na mesma conferência foi corrigido um terceiro erro do mesmo tipo, que não estava na revisão:
`UC13 «include» UC14` dizia que a tarefa remota inicia o worker, mas quem inicia o worker é o
operador, antes e em outro processo. A aresta foi retirada e `UC14` passou a constar como
**pré-condição** de `UC13` (nota 2.1 e tabela 2.2). Os diagramas de classes, componentes e
sequência não mudaram.

### Implementado

- [`docs/15_UML_MINIPAR_2026_2.md`](../15_UML_MINIPAR_2026_2.md): UML **derivada do código**, em Mermaid:
  - **Casos de uso** (seção 2): 7 atores, 16 casos de uso com `«include»`/`«extend»` e tabela
    que liga cada caso ao ponto de entrada real (comando, função ou rota).
  - **Componentes** (seção 3): camadas apresentação → serviços → núcleo → TAC → backend →
    runtime, com as interfaces C-WEB-v1, HTTP `/api/v1`, CLI, C-FJ-v1 §2.3 e §2.6; tabela de
    componentes × arquivos × eixo × interface fornecida/requerida.
  - **Classes por componente** (seção 4, 13 diagramas): Lexer; AST (37 nós, em duas figuras);
    Parser; semântico e tabela de símbolos; **gerador TAC**; **gerador C++** (com
    `CppTaskContext`/`CppType`); serviço; CLI e Web original; Web didática (módulos JS);
    runtime `minipar_rt` (núcleo e execução remota); `MiniCompilador` do Teste 11.
  - **Sequência** (seção 5): compilar e executar pela Web didática; Fork/Join local e remoto.
  - Correspondência com os componentes exigidos em §11.1 e 7 observações sobre a
    implementação real (seções 6 e 7).
- [`DOC-02_sondas_uml.py`](DOC-02_sondas_uml.py): 853 sondas que confrontam os diagramas de
  classes com o código (classe, membro, herança, pontas de aresta e cobertura).
- [`DOC-02_RESULTADOS.json`](DOC-02_RESULTADOS.json): saída registrada das sondas.

Nenhuma classe, interface ou método foi inventado; nenhum arquivo fora de `docs/` foi alterado.

### Arquivos alterados

- `docs/15_UML_MINIPAR_2026_2.md` (novo)
- `docs/auditorias/DOC-02_UML.md` (novo, este handoff)
- `docs/auditorias/DOC-02_sondas_uml.py` (novo)
- `docs/auditorias/DOC-02_RESULTADOS.json` (novo)

Todos dentro de `docs/`, único caminho autorizado pelo card.

### Verificação documental — MANDATORY (histórico da entrega original)

Os estados descritos nesta seção são anteriores ao merge. O estado atual está no registro REL-PRE no início deste handoff: cards/backlogs/checklist/README foram sincronizados, DOC-02 integrado e revisão C registrada com ressalvas ([parecer C](DOC-02_REVISAO_C_RUNTIME.md)).

- **Documentos verificados e impacto identificado:**
  - `docs/00_DOCUMENTO_MESTRE_INICIAL.md` §11 (componentes e diagramas exigidos): usado como
    lista de requisitos; a seção 6 do documento 15 mostra a cobertura. Sem alteração.
  - `docs/02_CONTRATOS_TECNICOS.md` (C-WEB-v1, C-FJ-v1, C-T11-v1): nomes de interfaces,
    rotas, mensagens e códigos de erro conferidos com o código. Sem divergência encontrada;
    sem alteração (arquivo compartilhado).
  - `docs/12_BNF_MINIPAR_2026_2.md` e `docs/13_PSEUDOCODIGOS_NUCLEO.md` (`DOC-01`):
    referenciados nos diagramas do Lexer e do Parser; sem conflito; sem alteração.
  - `docs/11_CHECKLIST_DE_ENTREGA.md` (itens UML casos de uso, componentes e classes):
    na entrega original não marcados; após #42, casos de uso conferidos/aprovados por A e marcados em REL-PRE; componentes/classes marcados após a revisão C de 09/11 (componentes sem ressalva; classes com omissões menores RC-03/RC-04).
  - `docs/relatorio/README.md` (índice das seções do relatório): lista só arquivos de
    `docs/relatorio/`; os documentos 12/13 do `DOC-01` também não estão lá. Mantido sem
    alteração; o `DOC-04` decide como incorporar 12, 13, 14 (DOC-03) e 15.
  - `README.md`: já cita "documentação/UML"; não lista documentos além de 00–06. Link para o
    14 fica como sugestão à coordenação (arquivo compartilhado), como no `DOC-01`.
  - `planning/cards.json` e `docs/04_BACKLOG.md`: estado do card não alterado (arquivo
    compartilhado; backlog é do C via `DOC-03`).
  - `docs/14_PRODUCT_E_SPRINT_BACKLOGS.md` (`DOC-03`, Eixo C): registra `DOC-02` como `BACKLOG`
    e "UML não iniciada" (PB-13). Não editado (arquivo do C); atualizar quando este PR for aberto.
- **Documentos atualizados nesta mesma entrega/PR:** os quatro arquivos novos acima.
- **`AGENTS.md`:** revisado; **não precisa mudar**. O card não altera regras, convenções,
  arquitetura nem fluxo de trabalho; só acrescenta documentação de referência.

### Interface exposta ao consumidor

Sem interface de código. Consumidores documentais:
- `DOC-04` (relatório): seções "Diagrama de casos de uso", "Arquitetura de componentes" e
  "Modelagem de classes" podem usar o documento 15 (os blocos Mermaid exportam para imagem).
- Eixos A e C: revisão de exatidão dos diagramas das suas camadas.

### Como reproduzir e validar

Comandos (raiz do repositório, Python 3.14, Windows 11):

```bash
python docs/auditorias/DOC-02_sondas_uml.py
python docs/auditorias/DOC-02_sondas_uml.py --json docs/auditorias/DOC-02_RESULTADOS.json
```

Saída observada:

```text
  documento          1/1
  classe             106/106
  membro             500/500
  aresta             107/107
  heranca            40/40
  cobertura-arquivo  30/30
  cobertura-classe   69/69
DOC-02 sondas: 853/853 PASS
```

| Grupo | Casos | O que confere |
|---|---|---|
| documento | 1 | Há pelo menos 10 blocos `classDiagram` |
| classe | 106 | Cada classe/módulo com `%% @fonte` existe no arquivo indicado |
| membro | 500 | Cada atributo, método e valor de enumeração listado existe (Python por AST, com `self.x` e campos de dataclass; C++, JS e MiniPar por declaração no arquivo) |
| aresta | 107 | As duas pontas de cada relação foram declaradas no bloco (evita classe fantasma por erro de digitação) |
| heranca | 40 | Cada `Pai <|-- Filho` existe nas bases da classe (Python) ou no `extends` (JS) |
| cobertura-arquivo | 30 | Todo `src/*.py`, os módulos da raiz, `web_didatica/server.py`, todo `static/js/*.js`, todo cabeçalho do runtime e o `minicompilador.minipar` aparecem em algum `@fonte` |
| cobertura-classe | 69 | Toda classe de `src/*.py`, todo `class`/`struct`/`enum class` de nível de namespace do runtime e toda classe JS aparece em algum diagrama |

**Controle negativo** (prova que as sondas podem falhar): aplicando em memória 8 mutações ao
documento — método Python inexistente (`Lexer.fantasma`), herança falsa
(`Program <|-- ForkExpr`), classe renomeada (`CppTipo`), aresta para classe não declarada
(`Tokn`), método MiniPar inexistente, método C++ inexistente (`Executor.drain`), função JS
inexistente (`extrairX86`) e valor de enumeração inexistente (`WORKER_GONE`) — o script relatou
`844/854 PASS`, 10 `FAIL` (cada mutação detectada; a classe renomeada derruba também a aresta
e a cobertura) e retorno 1. Versão mínima reproduzível (saída observada:
`FAIL [membro] bloco 3: Lexer.fantasma method`, `853/854 PASS`, `rc 1`):

```bash
python -c "import importlib.util as u; s=u.spec_from_file_location('s','docs/auditorias/DOC-02_sondas_uml.py'); m=u.module_from_spec(s); s.loader.exec_module(m); t=m.DOC.read_text(encoding='utf-8'); print('rc', m.main(['x'], t.replace('+tokenize() List~Token~', '+tokenize() List~Token~\n        +fantasma() None', 1)))"
```

**Renderização:** os 17 blocos Mermaid do documento (2 `flowchart`, 13 `classDiagram`,
2 `sequenceDiagram`) foram renderizados com `mermaid@11.4.1` (jsDelivr) numa página local
servida em `127.0.0.1`, no navegador do Claude Desktop: **17/17 sem erro de sintaxe** e
nenhum texto em negrito indevido. Essa verificação encontrou e corrigiu dois problemas: um
rótulo de relação com `:` (erro de parse) e `__init__` virando negrito (trocado pela notação
UML de construtor, `+Classe(...)`). A página de teste não foi versionada; para repetir, basta
renderizar cada bloco ` ```mermaid ` com `mermaid.render`, ou abrir o arquivo no GitHub.

Depois dos ajustes da revisão (09/11), a renderização foi repetida: **17/17 sem erro**, e os
identificadores das arestas no SVG do diagrama de casos de uso confirmam o sentido novo
(`L_UC08_UC07`, `L_UC12_UC16`, `L_UC13_UC16`, `L_UC04/UC06/UC09/UC15_UC16`, `L_prog_UC16`),
sem `UC07→UC08`, sem `UC12/UC13→UC03` e sem `UC13→UC14`. As sondas continuam `853/853 PASS`
(a revisão não mexeu nos diagramas de classes; `DOC-02_RESULTADOS.json` ficou igual).

Oráculo: o código em `8d07433` (`src/`, `main.py`, `menu.py`, `app.py`,
`test_orchestrator.py`, `program_analyzer.py`, `web_didatica/server.py`,
`web_didatica/static/js/`, `runtime/include/minipar_rt/`,
`tests/2026_2/test11/minicompilador.minipar`).

**Status atual:** `DONE` de integração (#42, `a7454bc`); **aceite técnico conjunto PARTIAL**. Diagramas e evidências integrados, com aprovação A após os ajustes. Revisão específica C registrada em 09/11 como APROVADO COM RESSALVAS ([parecer C](DOC-02_REVISAO_C_RUNTIME.md)); RC-01/RC-02 (§5.2/UC12) aguardam correção por B. Resultados do autor: 853/853, controle negativo e 17/17 renderizados; sondas 853/853 reexecutadas por REL-PRE, sem repetir renderização.

### Regressões executadas

- Nenhum código de produção mudou; não há regressão funcional a executar.

### Pendências, riscos e limitações

- **Revisão A:** APPROVED no #42 em `4cdae73`. **Revisão C** (runtime e runners): APROVADO COM RESSALVAS em 09/11 ([parecer C](DOC-02_REVISAO_C_RUNTIME.md)). RC-01 (`join` gerado usa `__fj_join`) e RC-02 (fork sem destino passa `Destination::parse("local")`) impedem declarar aceite técnico conjunto completo até a correção por B; RC-03..RC-06 são omissões menores recomendadas.
- As sondas conferem **existência**, não semântica: um método listado na classe certa com
  papel descrito errado no texto não é detectado. Em C++, JS e MiniPar a busca é por nome no
  arquivo, não restrita ao corpo da classe. As relações de associação/uso (`..>`, `-->`)
  não são conferidas além das pontas declaradas; diagramas de casos de uso, componentes e
  sequência são conferidos só pela renderização e pela leitura do código.
- Os diagramas de classes listam membros públicos completos e privados selecionados; a
  seleção está explicada na seção 1 do documento.
- Mermaid não tem os tipos "casos de uso" e "componentes"; a adaptação em `flowchart` está
  descrita nas notas 2.1 e 3.1. Se o relatório exigir notação UML estrita desses dois, será
  preciso redesenhá-los em outra ferramenta (ex.: PlantUML) a partir das mesmas tabelas.
- O documento reflete `8d07433`. Mudanças em `src/`, `runtime/include/`,
  `web_didatica/static/js/` ou no `minicompilador.minipar` exigem reexecutar as sondas; a
  cobertura acusa classes novas que não entrarem nos diagramas.

### Próxima pessoa/card dependente

- Eixo A: aprovação registrada no #42; sem nova revisão automática por REL-PRE.
- Eixo C: revisar seções 4.9 e 5.2 e aprovar exatidão.
- `DOC-04` (B): usar o documento 15 nas seções de UML do relatório.
- Coordenação: marcar os itens UML de `11_CHECKLIST_DE_ENTREGA.md` após as revisões e decidir
  sobre o link no `README.md`.

**Declaração:** não alterei outro eixo nem `legacy/` sem autorização de CR.
