# Plano de testes, oráculos, evidências e aceite — v0.1

> Nenhum teste oficial 2026.2 está **automaticamente aprovado** por aparecer nesta matriz. Resultados de auditoria foram feitos em **cópia experimental C++14**, não no código novo.

## 1. Protocolo de prova

Cada evidência contém: ID do teste, fonte MiniPar, commit/branch, ferramenta (Python/G++/OS), comando, stdin, stdout/stderr, returncode, arquivos gerados, **oráculo** (valor/estrutura esperada), avaliação PASS/FAIL/BLOCKED/PARTIAL, data, responsável.

**PASS:** programa percorreu as fases exigidas, gerou o binário, rodou e os valores/efeitos foram conferidos.  
**PARTIAL:** somente recorte funcional demonstrado (ex.: AST/ARM impresso).  
**BLOCKED:** não possível executar por ambiente ou dependência, com causa concreta.  
**FAIL:** execução real divergiu do esperado.  
**UNTESTED:** ainda sem execução.

Status na baseline e no novo branch não devem ser confundidos. Um resultado da auditoria não substitui regressão após merge.

## 2. Matriz T01–T11

| Teste | Dono | Oráculo central | Pontos que invalidam PASS | Estado do NOVO repo |
|---|---|---|---|---|
| T01 Calculadora cliente-servidor | A | `+`, `2`, `3` → `5` e troca real entre processos | Retorno fixo, timeout sem tratamento, socket não comprovado | UNTESTED |
| T02 Fatorial/Fibonacci | A | fatorial 5 = 120; Fibonacci `0,1,1,2,3,5,8,13` | Threads aparentes sem prova, valor errado | UNTESTED |
| T03 Neurônio | A | convergência e valores coerentes do algoritmo | Somente `exit 0`, sem observar treinamento | UNTESTED |
| T04 XOR | A | classificação correta da XOR, comparar saídas numéricas com tolerância acordada | Divergências ignoradas sem tolerância/justificativa | UNTESTED |
| T05 Recomendação | A | produtos e probabilidades com entradas fixadas | Histórico/entrada desconhecidos, texto gerado artificialmente | UNTESTED |
| T06 Quicksort OO | A | vetor numericamente ordenado, inclusive negativos | saída específica hardcoded | UNTESTED |
| T07 Quicksort iterativo/TAC | A | ordenação verdadeira e TAC derivado da AST | `EXPECTED_QUICKSORT_TAC`; acesso fora de limites | UNTESTED |
| T08 4 avaliadores | C + A | 40 alunos × 4 atividades = 160, 4 trabalhos, 160 resultados | perda/duplicata, falso fork/join | UNTESTED |
| T09 5 trabalhos | C + A | T08 + Mandelbrot ASCII calculado | fractal fixo, quinta tarefa serializada | UNTESTED |
| T10 6 trabalhos | C + A | T09 + Sierpinski visual, cargas comparáveis | Sierpinski só depois de join sem registrar; benchmark injusto | UNTESTED |
| T11 MiniCompilador | B + A | `22`, `-84`, `22`, tokens/AST/TAC/símbolos/ARM | lógica em Python em lugar de MiniPar; `.arm` não executado | UNTESTED |

### Particularidades

**T01**: executar loopback e ao menos uma prova de comunicação em hosts distintos se apropriado. A primeira auditoria observou timeout inicial da calculadora; não declarar estabilidade por uma execução bem-sucedida.

**T04**: auditoria viu resultado XOR numérico diferente do referencial (`0.00684395,0.986493,0.98925,0.0140296` contra `0.0089,0.9769,0.9758,0.0291`). A classificação booleana funcionou. Definir tolerância antes de aceitar resultados, considerando inicialização e treino.

**T07**: mutação adversarial obrigatória: substituir o corpo de `quicksort_iterativo` por outro comportamento e verificar que TAC muda. Compilar com verificação de índices/sanitizer quando possível.

**T08**: registrar IDs dos 160 itens, contagem completa e sem duplicidade. Tempo pode piorar no paralelo; não obrigar speedup >1.

**T09**: fractal ASCII deve variar corretamente conforme parâmetros, não ser literal fixo.

**T10**: referência Python inclui comportamento possivelmente não paralelo do Sierpinski e carga sequencial desigual. Documentar qualquer correção/alteração, manter comparação entre cargas equivalentes. Saída gráfica precisa de formato aceito.

**T11**: além das entradas oficiais, testar variação de parênteses, operador, erro de entrada, divisão por zero se suportada. `.arm` **executado no CPUlator** com identificação do registrador final. A prova da auditoria com `2+4*7=30` e 10 casos representa somente `PARTIAL` histórico.

## 3. Testes técnicos por componente

| Componente | Positivos | Negativos |
|---|---|---|
| Lexer | tipos, palavras-chave, strings/comentários, fork/join | string não fechada, caractere inválido |
| Parser | agrupamento, classes, funções, tarefas | parênteses, `join` malformado, destino inválido |
| Semântico | símbolos/escopos, chamadas, handles | chamada inválida, send em inteiro, join em não-handle |
| TAC | operadores, fluxo, fork/start/join, T07 mutado | divergência de representação, hardcode |
| C++ | compilação/execução em toolchain declarada | lista fora limites, tipagem inválida, retorno errado |
| Runtime | local/remoto, IDs, cópia, join, socket | worker morto, frame parcial, erro de tarefa |
| Web | tokens/AST/símbolos/TAC/C++ reais, run/download | compilação inválida, stale artifact, timeout |
| ARM | 3 expressões, registradores e aritmética | código não montável, overflow não tratado no escopo |

## 4. Teste distribuído mínimo obrigatório

1. Escolher dois computadores com endereços de rede distintos e rede alcançável, ferramentas configuradas e builds correspondentes.
2. Iniciar worker no host B com logs identificando `worker_id`, host e PID.
3. Iniciar programa MiniPar compilado no host A com destino B.
4. Disparar pelo menos duas tarefas com entradas diferentes.
5. Demonstrar `join` retornando resultados coerentes (sem troca de IDs).
6. Matar um worker durante tarefa pendente e verificar erro/timeout sem bloqueio infinito.
7. Registrar comandos, versão de binários e evidências; **não** inserir IP privado/sensível desnecessário em repo público.
8. Repetir com cenário local para comparação.

**Protocolo via localhost não substitui o passo 1–7**; o experimento anterior em localhost demonstrou apenas framing/mensagens isolados.

## 5. Benchmark

Registrar: CPU, núcleos/threads lógicos, OS, compilador/flags, carga, quantidade de workers, tipo de prova, medição repetida, tempo sequencial/tempo paralelo, speedup = `Tseq/Tpar`, redução = `100*(Tseq-Tpar)/Tseq`.

Comparar exatamente a **mesma carga**. Se comparação da referência é injusta, preservar evidência e explicar por que a versão corrigida usa cargas equivalentes.

## 6. Política dos artefatos e Web

- Tokens/AST/símbolos devem vir de fases reais; fixtures só no desenvolvimento da UI.
- `compile` retorna sucesso apenas quando G++ retorna sucesso e o binário foi criado.
- `run` mede timeout e lê stdout/stderr do binário certo.
- `download` usa identificador da compilação atual, não qualquer `output/*.exe`.
- Não expor serviço de execução arbitrária na internet sem sandbox adequado.

## 7. Matriz de estados para registrar durante o projeto

| Data/commit | T01 | T02 | T03 | T04 | T05 | T06 | T07 | T08 | T09 | T10 | T11 | Observações |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 15/10 antes da importação | UNTESTED | UNTESTED | UNTESTED | UNTESTED | UNTESTED | UNTESTED | UNTESTED | UNTESTED | UNTESTED | UNTESTED | UNTESTED | Início do novo repo; não confundir com rodada 2 |
| (preencher) | | | | | | | | | | | | |

## 8. Gates de evidência

- G0: testes herdados executados ou bloqueados com causa verificável.
- G1: prova vertical T11 e prova remota cedo, com riscos registrados.
- G2: T08 end-to-end e ARM executado no CPUlator.
- G3: T01–T11 e 3 interfaces testadas; status honesto.
- G4: evidências vinculadas ao relatório.
- G5: demonstração reproduzida pelo trio.

### Ficha de evidência

Usar `docs/templates/TEMPLATE_RELATORIO_TESTE.md`. Para qualquer `PASS`, anexar **resultado + oráculo + artefatos**. Nada de aprovar um programa porque pareceu funcionar.
