## Documento Mestre Inicial de Contexto, Requisitos e Diretrizes

**Versão:** 0.1 — Contexto inicial consolidado  
**Data de elaboração:** 15/10/2026  
**Disciplina:** Compiladores — Ciência da Computação — UFAL  
**Professor:** Arturo Hernandez Dominguez  
**Equipe:** Trio de desenvolvimento — integrantes a definir  
**Prazo oficial informado:** 11/11/2026  
**Meta interna de conclusão funcional:** 03/11/2026  
**Período reservado para estudo e apresentação:** 04/11 a 10/11/2026

**Estado do projeto:** Levantamento inicial de requisitos concluído. Auditoria técnica, planejamento detalhado, divisão de responsabilidades e implementação ainda não iniciados nesta etapa.

---

# 1. Finalidade deste documento

Este documento consolida o conhecimento inicial sobre o projeto **Compilador da Linguagem MiniPar 2026.2**, reunindo as informações disponibilizadas pelo professor, materiais de versões anteriores, código-fonte existente, testes solicitados e decisões preliminares da equipe.

Ele servirá como referência central para:

- Preservar o entendimento dos requisitos e evitar perda de contexto.
- Orientar a análise técnica da implementação MiniPar 2026.1.
- Fundamentar o planejamento e a divisão de tarefas entre os três integrantes.
- Fornecer contexto para agentes de IA que auxiliarão na implementação.
- Distinguir exigências explícitas, decisões propostas e questões pendentes.
- Estabelecer critérios para revisar o código e verificar o funcionamento.
- Registrar decisões futuras e suas justificativas.
- Apoiar a elaboração do relatório e a preparação da apresentação.

**Este documento não é o planejamento operacional do projeto.** Ele é sua base de conhecimento inicial. Cronograma detalhado, distribuição de atividades, especificação final da arquitetura e estratégia concreta de implementação serão elaborados em etapas posteriores.

## 1.1 Classificação das informações

Para evitar que hipóteses sejam confundidas com requisitos, adotam-se as seguintes classificações:

| Classificação | Significado |
|---|---|
| **EXIGIDO** | Requisito explicitamente presente no enunciado ou em comunicado do professor. |
| **DECIDIDO** | Diretriz preliminar aprovada para conduzir o projeto. |
| **PROPOSTO** | Solução técnica recomendada, ainda sujeita à validação na auditoria. |
| **IDENTIFICADO** | Característica ou possível problema observado na implementação anterior. |
| **PENDENTE** | Questão não resolvida que precisa ser investigada ou confirmada. |
| **RECOMENDADO** | Prática de engenharia e validação adotada para melhorar a confiabilidade do projeto. |

---

# 2. Visão geral do projeto

## 2.1 Objetivo central

Desenvolver o compilador da linguagem de programação **MiniPar 2026.2**, orientada a objetos, com suporte à execução sequencial e paralela, comunicação entre processos/computadores e novas instruções de Fork e Join.

O compilador deverá processar programas escritos em MiniPar, realizar análises léxica, sintática e semântica, gerar código intermediário de três endereços (TAC), produzir código C ou C++ e compilá-lo para gerar executáveis funcionais.

O projeto deve preservar a implementação e as interfaces existentes da versão 2026.1, ampliando sua gramática e suas funcionalidades para atender aos programas de teste solicitados em 2026.2.

Também deve acrescentar uma segunda interface Web, voltada especificamente ao uso didático por estudantes iniciantes.

## 2.2 Estratégia geral aprovada

**DECIDIDO — Evoluir a implementação 2026.1, em vez de recomeçar do zero.**

A implementação anterior será utilizada como ponto de partida porque já contém diversos componentes necessários:

- Analisador léxico.
- Analisador sintático.
- Representação da AST.
- Analisador semântico.
- Geração de TAC.
- Geração de C++.
- Interface de terminal.
- Interface Web.
- Programas de teste.
- Estruturas para execução paralela e comunicação por canais.

O reaproveitamento não implica aceitar automaticamente a correção do código anterior.

Antes de construir as novas funcionalidades, será necessário verificar o funcionamento real dos componentes existentes, identificar fragilidades e estabelecer uma baseline de testes.

## 2.3 Resultado esperado

Ao final do desenvolvimento, a equipe deverá apresentar:

1. Compilador MiniPar 2026.2 funcional.
2. Gramática BNF atualizada.
3. Suporte a orientação a objetos, funções, estruturas de controle e operações já previstas na versão anterior.
4. Execução paralela com Fork/Join e comunicação entre computadores.
5. Código intermediário TAC gerado corretamente.
6. Tradução para C ou C++ com compilação nativa.
7. Interface terminal preservada.
8. Primeira interface Web preservada.
9. Segunda interface Web didática funcionando.
10. Execução e validação dos testes 1 a 11.
11. Teste 11 com geração de Assembly ARMv7 e validação no CPUlator.
12. Documentação, modelagem UML e relatório técnico.
13. Repositório GitHub completo.
14. Apresentação demonstrando o sistema e explicando sua implementação.

---

# 3. Fontes e materiais de referência

## 3.1 Material principal

**Projeto-Compilador-MiniPar2026-2-Atualizado.pdf**

Documento oficial disponibilizado pelo professor, contendo:

- Objetivo do projeto.
- Requisitos de compilação.
- Organização orientada a objetos.
- Componentes de software.
- Gramática e necessidades de extensão.
- Conceitos de execução sequencial e paralela.
- Fork/Join.
- Comunicação entre computadores.
- Programas de teste 1 a 10.
- Interface didática.
- Exigências de documentação e modelagem.

**Prioridade:** referência principal para definição do escopo.

## 3.2 Gramática anterior

**BNF-grammaMiniPAR2026-1.md**

Gramática da versão 2026.1, derivada da implementação anterior.

Contém definições de declarações, expressões, funções, classes, objetos, controle de fluxo, coleções, canais e blocos paralelos.

**Uso previsto:** base para a gramática 2026.2, preservando compatibilidade sempre que possível.

## 3.3 Implementação anterior

**Repositório GitHub:**

https://github.com/luizwhirl/minipar-improvement

Implementação em Python com geração de código C++20, interface Flask e programas de teste.

**Uso previsto:** base do novo projeto e principal objeto da auditoria técnica inicial.

## 3.4 Relatórios anteriores

**Relatório-MiniPar-Compiladores-2026.1**

Referência para arquitetura, implementação, decisões técnicas e testes anteriores.

**Relatório-MiniPar2025.1-Compiladores-Helio-10,0-InterfaceWeb.pdf**

Referência histórica para:

- Pipeline do compilador.
- Modelagem UML.
- Arquitetura dos componentes.
- Pseudocódigos.
- Testes.
- Geração de código.
- Interface Web.
- Organização do relatório técnico.

O relatório de 2025.1 não deve ser interpretado automaticamente como especificação obrigatória da versão 2026.2.

## 3.5 Materiais de modelagem

**Modelagem do Interpretador para a Linguagem MiniPar utilizando Componentes de Software**

Material sobre:

- Separação de responsabilidades.
- Interface dos componentes.
- Diagrama de componentes.
- Diagrama de classes.
- Relação entre classes concretas e interfaces.

**Material sobre Scrum e desenvolvimento incremental no MiniPar**

Referência para Product Backlog, Sprint Backlog e organização incremental da implementação.

## 3.6 Testes paralelos

Arquivos fornecidos como referência:

- `Teste8-Avaliacao-Atividades-Versao-Uso-de-4Nucleos.py`
- `Teste9-5Nucleos-4Avaliadores-UmFractal.py`
- `Teste10-Nucleos-AvaliacaoAtiv-e-2Fractais.py`

Esses códigos apresentam aplicações Python que deverão ser representadas por programas MiniPar, com adaptações necessárias à linguagem e ao modelo de execução definido.

## 3.7 Teste 11

Comunicado adicional no Classroom:

**Implementar em MiniPar 2026.2 um MiniCompilador de expressões infixadas, com análise léxica, AST, TAC, tabela de símbolos, avaliação da expressão e geração Assembly ARMv7.**

O professor disponibilizou código Java e exemplos de execução.

A saída Assembly deve ser validada no CPUlator e salva em arquivos `.arm`.

## 3.8 Interface de referência

http://pesquisa06.lages.ifsc.edu.br/

Referência visual e didática indicada pelo professor.

As imagens disponibilizadas apresentam um compilador educacional com exemplos de sintaxe, variáveis, funções, entrada e saída, condicionais e laços.

**Importante:** esse material é uma referência de interface e apresentação didática, não uma substituição da gramática do MiniPar 2026.1/2026.2.

## 3.9 Vídeo de explicação

O professor disponibilizou um vídeo de aproximadamente 1h40 explicando o projeto.

A tentativa inicial de processamento do vídeo enviado não foi concluída.

**Estado: PENDENTE, não bloqueante.**

A equipe decidiu continuar o planejamento sem depender desse vídeo, mantendo abertas as dúvidas específicas sobre a execução distribuída com Fork/Join.

---

# 4. Requisitos funcionais do compilador

## 4.1 Pipeline de compilação

O compilador deverá possuir as seguintes etapas:

```text
Programa MiniPar
       |
       v
Análise Léxica
       |
       v
Tokens
       |
       v
Análise Sintática
       |
       v
AST
       |
       v
Análise Semântica
       |
       v
AST validada / Tabela de Símbolos
       |
       v
Geração de TAC
       |
       v
Código de Três Endereços
       |
       v
Geração de C++
       |
       v
Código C++ compilável
       |
       v
G++ / GCC
       |
       v
Executável nativo
       |
       v
Execução do programa
```

A representação acima descreve o fluxo lógico esperado. A arquitetura interna e as APIs ainda serão definidas.

### RF-01 — Análise léxica

**EXIGIDO**

O compilador deverá reconhecer os tokens da linguagem MiniPar 2026.2.

Responsabilidades:

- Identificar palavras reservadas.
- Identificar nomes de variáveis, classes e funções.
- Reconhecer números e strings.
- Reconhecer operadores e delimitadores.
- Tratar comentários.
- Detectar caracteres inválidos.
- Informar localização dos tokens, quando disponível.

**Critério preliminar de aceite:** o Lexer deve reconhecer todos os construtos da BNF final e rejeitar ou sinalizar entradas lexicalmente inválidas.

### RF-02 — Análise sintática

**EXIGIDO**

O Parser deverá verificar se a sequência de tokens segue a gramática MiniPar 2026.2.

Responsabilidades:

- Interpretar declarações.
- Interpretar comandos.
- Interpretar expressões segundo a precedência.
- Reconhecer funções e classes.
- Reconhecer blocos sequenciais e paralelos.
- Reconhecer Fork/Join.
- Construir AST consistente.

**Critério preliminar de aceite:** programas válidos geram uma AST; programas sintaticamente inválidos produzem erros sem resultar em execução indevida.

### RF-03 — Árvore Sintática Abstrata

**EXIGIDO**

Deverá existir representação estruturada dos programas por nós de AST.

A árvore deverá representar as construções existentes e as novas funcionalidades da linguagem.

Será necessária uma representação serializável para a interface didática.

**RECOMENDADO:** manter uma única AST interna, reutilizada pelas fases semântica, TAC, geração C++ e visualização.

### RF-04 — Análise semântica

**EXIGIDO**

Verificar propriedades que dependem do significado das construções, incluindo:

- Declaração e uso de identificadores.
- Escopo.
- Tipos.
- Chamadas de funções e métodos.
- Quantidade de argumentos.
- Existência de classes, métodos e atributos.
- Restrições dos comandos.
- Compatibilidade das operações.
- Regras semânticas do novo modelo de tarefas.

As regras definitivas dependerão da BNF 2026.2.

### RF-05 — Tabela de símbolos

**EXIGIDO**

Registrar símbolos definidos nos programas, incluindo seus tipos e escopos.

A implementação anterior possui estruturas de símbolos dentro da análise semântica.

Durante a auditoria será avaliado se é necessário extrair esse mecanismo para um componente próprio, mantendo interfaces claras e documentação compatível com o modelo UML exigido.

### RF-06 — Código intermediário TAC

**EXIGIDO**

Gerar uma representação intermediária de três endereços a partir do programa analisado.

O TAC deverá representar corretamente as operações e o fluxo de controle.

Deverá ser estendido para os recursos novos de paralelismo, sem simplesmente ignorar Fork/Join.

**Critério preliminar de aceite:** o TAC deve corresponder ao programa de entrada e não a uma resposta fixa associada ao nome de um teste.

### RF-07 — Geração de C ou C++

**EXIGIDO**

Produzir código nativo equivalente ao programa MiniPar.

**DECIDIDO:** continuar priorizando C++20, por ser o backend existente na versão 2026.1.

A continuidade dessa decisão depende de confirmar sua viabilidade e corrigir eventuais incompatibilidades.

### RF-08 — Compilação nativa

**EXIGIDO**

Compilar o código C++ gerado utilizando GCC/G++, com opção de otimização.

Deverá ser possível:

- Gerar executável.
- Detectar erros de compilação nativa.
- Exibir mensagens de erro.
- Executar o binário gerado.
- Obter a saída de execução.
- Disponibilizar o executável para download na interface didática.

A extensão do binário dependerá da plataforma. Em Windows, `.exe`; em Linux, normalmente sem extensão.

### RF-09 — Tratamento de erros

**EXIGIDO**

O compilador deverá tratar erros léxicos, sintáticos e semânticos.

**RECOMENDADO:** estruturar os erros com fase, descrição e localização para apresentação uniforme nas interfaces.

Erros do compilador, erros do compilador C++ e falhas em tempo de execução deverão ser identificáveis separadamente.

---

# 5. Requisitos da linguagem MiniPar 2026.2

## 5.1 Compatibilidade com 2026.1

**DECIDIDO**

A gramática anterior será usada como ponto de partida.

A implementação deverá preservar, na medida necessária aos requisitos e aos testes:

- Variáveis.
- Tipos primitivos e coleções.
- Expressões aritméticas.
- Expressões lógicas e relacionais.
- Funções.
- Recursão.
- Classes e objetos.
- Instanciação com `new`.
- Atributos e métodos.
- Herança já suportada.
- `if` e `else`.
- `while`, `do-while` e `for`.
- `break`, `continue` e `return`.
- Entrada e saída.
- Comentários `#`.
- `seq` e `par`.
- Canais de comunicação.
- Operações `send` e `receive`.

A lista descreve o escopo herdado identificado na BNF de 2026.1. A auditoria determinará o grau de suporte funcional de cada item.

## 5.2 Fork e Join

**EXIGIDO**

O professor solicita adicionar Fork e Join à gramática e aos componentes do compilador.

Semântica descrita no enunciado:

- Fork: uma tarefa principal é dividida em duas ou mais subtarefas independentes.
- Join: a tarefa principal aguarda a conclusão das subtarefas criadas.
- As subtarefas podem ser alocadas localmente ou em computadores diferentes.
- A comunicação entre participantes ocorre por mensagens.

**PENDENTE:** definir a sintaxe oficial utilizada pelo projeto.

Essa decisão deverá considerar:

- Identificação das subtarefas.
- Escopo das variáveis.
- Passagem de argumentos.
- Representação dos resultados.
- Criação de tarefas.
- Execução local.
- Execução remota.
- Sincronização.
- Tratamento de falhas.

Não se deve adicionar apenas os tokens `fork` e `join` ao Lexer sem implementar comportamento correspondente.

## 5.3 Distinção entre SEQ, PAR, Fork e Join

| Construção | Significado |
|---|---|
| `seq` | Agrupamento de comandos executados sequencialmente. |
| `par` | Agrupamento de atividades executadas paralelamente. |
| `fork` | Criação/disparo de subtarefas independentes. |
| `join` | Sincronização e espera pela conclusão de subtarefas. |

A diferença exata entre `par` e a API de Fork/Join será definida durante a especificação da linguagem.

## 5.4 Concorrência versus paralelismo real

O projeto exige execução paralela, não apenas uma aparência de execução simultânea.

Entretanto, criar várias threads não garante que cada thread ficará permanentemente associada a um núcleo físico exclusivo.

O escalonamento normalmente é responsabilidade do sistema operacional.

**RECOMENDADO:** utilizar a expressão “tarefas concorrentes executadas em paralelo quando existem recursos disponíveis”, a menos que a equipe implemente e comprove afinidade explícita de CPU.

## 5.5 Isolamento de tarefas

O enunciado descreve participantes independentes, sem compartilhamento direto de informações, com comunicação por mensagens.

A implementação atual de `par` em C++ utiliza threads com captura por referência.

**IDENTIFICADO:** isso exige revisão, pois a captura `[&]` pode permitir compartilhamento de variáveis e ocasionar condições de corrida.

O modelo final deverá distinguir claramente dados locais, argumentos, resultados e canais.

---

# 6. Estratégia inicial de paralelismo e distribuição

## 6.1 Decisão aprovada

**DECIDIDO — Implementação incremental em duas modalidades.**

A equipe seguirá a seguinte abordagem:

**Modalidade A — Execução local**

Implementar e validar inicialmente a criação de subtarefas no mesmo computador.

A primeira versão deve permitir disparo real, execução concorrente, sincronização e obtenção dos resultados.

**Modalidade B — Execução distribuída**

Estender o modelo para execução entre computadores, utilizando comunicação por canais/sockets e um mecanismo adequado de coordenação.

O código-fonte MiniPar deverá descrever a operação segundo a gramática definida.

**Modalidade C — Validação**

Comprovar a diferença entre execução sequencial, paralela local e execução distribuída, conforme as demonstrações aplicáveis.

## 6.2 Limite de complexidade

**DECIDIDO**

Evitar infraestrutura distribuída excessivamente elaborada se uma solução mais simples atender aos requisitos.

Entretanto, não será considerado suficiente:

- Simular tarefas sem executá-las.
- Criar threads que não realizam trabalho real.
- Executar todas as tarefas sequencialmente e apenas rotular o resultado como paralelo.
- Usar sockets em um exemplo independente, sem integração com a semântica prevista de Fork/Join.
- Afirmar uso de múltiplos computadores quando a demonstração ocorreu somente via localhost.

## 6.3 Questão aberta principal

**PENDENTE**

O enunciado não deixa completamente explícito se o Fork deverá realizar despacho remoto automático de subtarefas ou se será suficiente coordenar programas/tarefas distribuídos utilizando os canais da linguagem.

A arquitetura deverá permitir evolução, reduzindo a necessidade de reescrever os componentes quando essa decisão for confirmada.

**Pergunta possível ao professor:**

“Na execução de Fork/Join entre computadores, o compilador deve despachar automaticamente as subtarefas para máquinas remotas ou podemos coordenar processos nos computadores por meio de `c_channel`, sincronizando os resultados com Join?”

## 6.4 Requisitos mínimos de validação

A estratégia de testes deverá contemplar:

- Duas tarefas independentes com resultados conhecidos.
- Várias tarefas iniciadas antes do Join.
- Join aguardando tarefas efetivamente pendentes.
- Coleta correta dos resultados.
- Execução local com mais de um trabalhador.
- Comunicação entre processos por canal.
- Demonstração real utilizando dois computadores, conforme solicitado no enunciado.
- Diagnóstico de falhas como desconexão, erro da tarefa e timeout.
- Ausência de compartilhamento indevido de memória conforme o modelo escolhido.

Esses critérios constituem diretrizes iniciais de qualidade; sua forma exata de verificação será definida posteriormente.

---

# 7. Base de código MiniPar 2026.1

## 7.1 Repositório de referência

https://github.com/luizwhirl/minipar-improvement

**Estado:** estrutura inspecionada parcialmente, mas a execução integral ainda não foi auditada.

## 7.2 Componentes identificados

| Arquivo | Responsabilidade principal |
|---|---|
| `src/lexer.py` | Tokenização. |
| `src/parser.py` | Parsing e construção da AST. |
| `src/ast_nodes.py` | Classes dos nós da AST. |
| `src/semantic.py` | Verificações semânticas. |
| `src/tac.py` | Geração de código de três endereços. |
| `src/codegen.py` | Tradução para C++ e compilação. |
| `src/cpp_template.py` | Código C++ auxiliar/runtime. |
| `main.py` | Entrada principal e fluxo de compilação. |
| `menu.py` | Interface de terminal. |
| `app.py` | API e servidor Web Flask. |
| `templates/index.html` | Interface Web anterior. |
| `static/` | CSS e JavaScript da interface. |
| `program_analyzer.py` | Identificação de características de programas. |
| `test_orchestrator.py` | Coordenação de sessões de execução/teste. |
| `tests/` | Programas MiniPar anteriores. |
| `tests/expected_results/` | Resultados de referência. |

## 7.3 Características positivas da base

A implementação anterior já possui separação razoável entre fases do compilador.

Há estruturas de AST representadas por classes, geradores dedicados, analisador semântico e integração com GCC/G++.

A interface Web anterior utiliza Flask e um editor baseado em CodeMirror.

A existência de código separado para testes e orquestração também favorece o reaproveitamento.

## 7.4 Problemas identificados para auditoria

### PA-01 — TAC específico para Quicksort

No arquivo `src/tac.py`, o gerador contém tratamento especial para uma função chamada `quicksort_iterativo`, retornando uma representação TAC predefinida.

**Risco:** o sistema pode apresentar TAC aparentemente correto para um teste específico sem gerar essa representação a partir da AST real.

**Diretriz:** remover comportamentos especiais que substituem geração real por resultados fixos, mantendo testes de regressão.

### PA-02 — Distinção entre SEQ e PAR no TAC

O gerador percorre `SeqBlock` e `ParBlock` de maneira semelhante.

**Risco:** a representação intermediária não expressar adequadamente o paralelismo.

**Diretriz:** verificar e projetar representação explícita de início, execução e sincronização de tarefas quando necessário.

### PA-03 — Captura por referência em threads

O gerador C++ utiliza captura `[&]` ao gerar threads de blocos paralelos.

**Risco:** compartilhamento não intencional, condições de corrida e divergência em relação ao modelo por mensagens.

**Diretriz:** revisar captura, passagem de parâmetros, escopo e ciclo de vida das tarefas.

### PA-04 — Compilação multiplataforma

A compilação C++ utiliza `-lws2_32`, biblioteca associada ao ambiente Windows.

**Risco:** incompatibilidade em sistemas Linux.

**Diretriz:** ajustar a geração e a configuração de compilação conforme a plataforma ou definir e documentar explicitamente o ambiente suportado.

### PA-05 — Distribuição entre computadores

Há suporte básico de sockets e a classe `MiniParChannel`, além de um orquestrador de sessões entre terminais.

**Limitação observada:** isso não comprova a existência de um mecanismo geral de execução remota de tarefas iniciadas por Fork.

**Diretriz:** avaliar separadamente comunicação, orquestração visual, criação de processos e execução remota real.

### PA-06 — API insuficiente para inspeção didática

A interface anterior expõe funcionalidades de compilação e execução e apresenta TAC/C++.

A segunda interface necessita acesso individual às fases de análise e seus artefatos.

**Diretriz:** criar uma interface compartilhada de serviço para cada fase sem duplicar o compilador.

### PA-07 — Validação insuficiente

A presença de programas de teste e resultados esperados não comprova, por si só, a correção geral do sistema.

**Diretriz:** criar testes independentes, incluindo entradas negativas, casos limites e programas que não constam dos exemplos anteriores.

## 7.5 Estado de confiança

O código anterior é uma **base de implementação reutilizável**, não uma versão funcional integralmente certificada.

A auditoria deverá estabelecer precisamente:

- O que compila.
- O que executa.
- O que produz resultados corretos.
- O que funciona apenas em determinados ambientes.
- O que depende de tratamento especial.
- O que precisa ser corrigido antes da extensão.
- O que pode ser preservado sem alterações.

---

# 8. Programas de teste 1 a 10

## 8.1 Requisito geral

**EXIGIDO**

Os programas de referência devem ser implementados ou mantidos em MiniPar 2026.2, compilados e executados com sucesso.

Testes herdados devem ser preservados, mas revalidados após alterações no compilador.

## 8.2 Matriz dos testes

| ID | Teste | Objetivo | Situação inicial |
|---|---|---|---|
| T01 | Calculadora cliente-servidor | Comunicação por canais/sockets. | Existe versão anterior; revalidar. |
| T02 | Fatorial e Fibonacci | Paralelismo de duas atividades. | Existe versão anterior; revalidar. |
| T03 | Neurônio | Classes, objetos, métodos e treinamento. | Existe versão anterior; revalidar. |
| T04 | Rede neural XOR | Funções, classes, listas e operações numéricas. | Existe versão anterior; revalidar. |
| T05 | Sistema de recomendação | Aplicação orientada a objetos com rede neural. | Existe versão anterior; revalidar. |
| T06 | Quicksort OO | Ordenação usando classes e recursão. | Existe versão anterior; revalidar. |
| T07 | Quicksort iterativo | Ordenação e geração real de TAC. | Existe versão anterior; revisar TAC. |
| T08 | 4 avaliadores | Distribuição de atividades em paralelo. | Implementação MiniPar 2026.2 necessária. |
| T09 | 4 avaliadores e Mandelbrot | Paralelismo com carga heterogênea. | Implementação MiniPar 2026.2 necessária. |
| T10 | 4 avaliadores e 2 fractais | Execução com seis unidades lógicas de trabalho. | Implementação MiniPar 2026.2 necessária. |

## 8.3 Teste 8 — Correção de atividades

O programa fornecido em Python cria 160 atividades, considerando 40 alunos com quatro atividades cada.

Na execução paralela, o trabalho é distribuído entre quatro avaliadores:

- Professor.
- Monitor 1.
- Monitor 2.
- Monitor 3.

A implementação utiliza processos e uma fila para devolver resultados.

**Expectativa para MiniPar:**

Representar a divisão da carga, executar os trabalhadores, recuperar os resultados e comparar as modalidades de execução.

**Validação recomendada:**

- Total correto de atividades.
- Ausência de perda ou duplicação.
- Conclusão de todos os trabalhadores.
- Medição adequada do tempo.
- Registro do número de trabalhadores efetivos.

## 8.4 Teste 9 — Avaliações e Mandelbrot

Amplia o Teste 8 com um quinto trabalhador lógico responsável pelo cálculo do fractal de Mandelbrot.

O fractal é produzido como arte ASCII.

**Expectativa para MiniPar:**

Executar a correção de atividades e a geração do fractal de maneira concorrente, sincronizando os resultados.

**Validação recomendada:**

- As 160 atividades são processadas.
- O fractal apresenta o formato esperado.
- O trabalhador do fractal conclui corretamente.
- O resultado não depende de uma saída ASCII predefinida.
- Todas as tarefas são sincronizadas.

## 8.5 Teste 10 — Avaliações, Mandelbrot e Sierpinski

Amplia o cenário anterior com um segundo fractal: Tapete de Sierpinski.

O código Python utiliza Turtle para a representação gráfica.

**Questão importante identificada:**

O código fornecido dispara cinco processos e aguarda sua conclusão antes de desenhar o fractal de Sierpinski.

Portanto, a implementação de referência não demonstra de maneira completa seis trabalhadores executando simultaneamente.

Além disso, o benchmark sequencial não executa exatamente a mesma carga da versão denominada paralela.

**Decisão técnica preliminar:**

Implementar as funcionalidades solicitadas de forma correta e documentar qualquer diferença em relação ao código Python fornecido.

**PENDENTE:** escolher a representação gráfica final em C++/MiniPar e confirmar se uma saída visual alternativa, como SVG, atende à exigência.

## 8.6 Métricas e benchmarks

Métricas relevantes:

- Tempo sequencial.
- Tempo paralelo.
- Speedup.
- Redução percentual do tempo.
- Número de tarefas.
- Número de trabalhadores.
- Quantidade de resultados concluídos.

Definições:

`speedup = tempo_sequencial / tempo_paralelo`

`reducao_percentual = 100 * (tempo_sequencial - tempo_paralelo) / tempo_sequencial`

**Regras de validação:**

- Comparar cargas equivalentes.
- Registrar ambiente e recursos utilizados.
- Não afirmar speedup sem medi-lo.
- Não confundir quantidade de processos com núcleos exclusivos.
- Registrar variações entre execuções.
- Não tomar um benchmark isolado como evidência suficiente de desempenho.

Speedup inferior a 1 indica que a implementação paralela foi mais lenta naquele experimento.

---

# 9. Teste 11 — MiniCompilador em MiniPar

## 9.1 Origem

**EXIGIDO — Comunicado adicional do Classroom.**

O professor solicita implementar, na linguagem MiniPar 2026.2, o MiniCompilador originalmente disponibilizado em Java.

Esse MiniCompilador deverá receber expressões matemáticas infixadas, respeitando parênteses e precedência de operadores.

## 9.2 Diferença entre os dois compiladores

Existirão dois programas com papéis distintos.

**Compilador principal MiniPar 2026.2**

Responsável por compilar programas escritos em MiniPar.

**MiniCompilador de expressões**

Um programa escrito na própria linguagem MiniPar, compilado pelo sistema principal, que recebe expressões matemáticas e gera saídas de análise e tradução.

Essa distinção é fundamental para evitar implementar funcionalidades desnecessárias no compilador principal.

## 9.3 Funcionalidades exigidas do MiniCompilador

A aplicação deverá:

1. Ler uma expressão infixada.
2. Realizar tokenização.
3. Identificar números, operadores e parênteses.
4. Construir a AST da expressão.
5. Exibir a AST.
6. Gerar o TAC.
7. Gerar Assembly ARMv7.
8. Registrar/exibir a tabela de símbolos.
9. Calcular o resultado da expressão.
10. Disponibilizar o código Assembly em um arquivo `.arm`.
11. Produzir código que possa ser executado corretamente no CPUlator.

## 9.4 Expressões obrigatórias

| Entrada | Resultado aritmético esperado |
|---|---:|
| `((2+4)*7)-(5*4)` | 22 |
| `((10 -8*7)+4)*2` | -84 |
| `((2+4)*7)-(5*4)` | 22 |

A primeira e a terceira entradas são idênticas no comunicado.

O segundo exemplo deve ser avaliado de acordo com a precedência:

`10 - 8*7 = -46`

`-46 + 4 = -42`

`-42 * 2 = -84`

## 9.5 Estratégia técnica escolhida

**DECIDIDO — Não implementar inicialmente um backend ARMv7 geral no compilador MiniPar.**

A aplicação MiniCompilador escrita em MiniPar produzirá o texto Assembly.

O compilador principal continuará prioritariamente traduzindo programas MiniPar para C++.

Essa estratégia respeita a distinção entre a aplicação solicitada e o compilador principal e reduz o escopo técnico.

A exigência de gerar Assembly válido permanece integralmente.

## 9.6 Salvamento dos arquivos ARM

**DECIDIDO — Preferir exportação pelo sistema de execução.**

A proposta inicial é fazer o MiniCompilador produzir uma saída Assembly identificável e permitir que a interface ou o sistema executor salve essa saída em um arquivo `.arm`.

Isso evita acrescentar operações de manipulação de arquivos à linguagem sem necessidade.

**PENDENTE:** validar se o professor exige especificamente que o programa MiniPar realize diretamente a escrita no arquivo.

Se essa condição for exigida, será necessário reavaliar a solução.

## 9.7 Requisitos técnicos potenciais

A implementação poderá precisar ampliar recursos de MiniPar relacionados a:

- Acesso a caracteres de strings.
- Comprimento de strings.
- Conversão entre caracteres e números.
- Manipulação de listas.
- Construção de strings.
- Nós de AST.
- Referências entre objetos.
- Representação de ausência de filhos em árvores.
- Recursão.
- Controle de erros.
- Geração incremental de texto.

Esses itens representam **necessidades potenciais**, não uma lista de novas funcionalidades já aprovadas.

Durante o planejamento do Teste 11, será verificado o que já existe e quais extensões são realmente indispensáveis.

## 9.8 Limitações do código Java fornecido

O MiniCompilador Java disponibilizado pelo professor possui limitações importantes:

- A geração de ARM para divisão não é funcional.
- A manipulação de registradores é simplificada.
- A validação de expressões inválidas é limitada.
- Variáveis não inicializadas são tratadas com valor zero.
- A geração ARM baseada em `MOV` imediato não resolve genericamente constantes arbitrárias ou números decimais.
- O código não implementa uma estratégia completa de alocação/reutilização de registradores.

**Diretriz:** cumprir os exemplos obrigatórios e corrigir os problemas relevantes ao escopo suportado.

Não é necessário transformar o MiniCompilador em um compilador geral para toda a linguagem Java.

## 9.9 Validação no CPUlator

A validação deverá demonstrar que os arquivos `.arm`:

- Possuem sintaxe ARMv7 aceita pelo ambiente.
- São carregados corretamente.
- Executam as operações esperadas.
- Produzem o resultado matemático correto.
- Permitem inspecionar o registrador ou local onde o resultado final foi armazenado.

Uma saída textual contendo Assembly não constitui, sozinha, comprovação de execução bem-sucedida no CPUlator.

**RECOMENDADO:** documentar claramente o registrador final que armazena o resultado, para facilitar a demonstração.

---

# 10. Interfaces do sistema

## 10.1 Quantidade exigida

**EXIGIDO — Três interfaces no total.**

| Interface | Público-alvo | Situação |
|---|---|---|
| Terminal | Desenvolvedor/usuário técnico. | Preservar. |
| Web original | Desenvolvedor. | Preservar. |
| Web didática | Aluno iniciante. | Desenvolver. |

O professor não pede três interfaces Web, mas sim duas interfaces Web e uma interface de terminal.

## 10.2 Terminal

Preservar o fluxo existente de interação, seleção de programas, compilação e execução.

A extensão do compilador deverá estar disponível também pela interface de terminal quando aplicável.

## 10.3 Primeira interface Web

Preservar a interface implementada pela turma anterior.

Manter recursos existentes de edição, compilação, visualização de código intermediário, código C++ e execução.

A nova implementação não deverá quebrar os fluxos originais.

## 10.4 Segunda interface Web didática

**EXIGIDO**

Desenvolver uma nova interface mais clara, acessível a iniciantes e visualmente organizada.

Funcionalidades solicitadas:

| Recurso | Comportamento esperado |
|---|---|
| Editor | Permitir escrever ou carregar código MiniPar. |
| Tokens — Lexer | Exibir análise léxica. |
| AST — Sintático | Exibir árvore sintática. |
| Análise Semântica | Exibir resultado da verificação semântica. |
| TAC | Exibir código intermediário. |
| Código C++ | Exibir código gerado. |
| Compilar e baixar | Gerar e disponibilizar executável. |
| Executar | Executar programa e apresentar resultado. |

## 10.5 Visualização da AST

**EXIGIDO — Melhoria significativa em relação às interfaces anteriores.**

**PROPOSTO:**

Representação hierárquica e interativa com:

- Nós expansíveis e recolhíveis.
- Distinção visual entre tipos de nós.
- Relacionamentos pai-filho claros.
- Visualização dos operadores e operandos.
- Informações de cada nó.
- Associação com trechos do código-fonte, quando possível.
- Organização apropriada para árvores grandes.
- Navegação sem poluição visual.

A biblioteca de visualização será escolhida no planejamento técnico.

## 10.6 Didática e ergonomia

**RECOMENDADO:**

- Interface em português brasileiro.
- Terminologia técnica consistente.
- Textos de apoio curtos.
- Exemplos carregáveis.
- Separação entre código-fonte e resultados.
- Destaque de sintaxe.
- Indicação da fase atual.
- Diferenciação entre sucesso, aviso e erro.
- Mensagens de erro legíveis.
- Indicação de linha/coluna quando disponível.

## 10.7 Arquitetura das interfaces

**DECIDIDO — Compartilhar um único núcleo de compilação.**

As interfaces deverão consumir os mesmos componentes de análise e geração.

**PROPOSTO:** criar uma camada de serviços que permita obter individualmente os resultados de cada fase.

Não será necessário implementar Lexer, Parser ou geradores de código separadamente para cada interface.

## 10.8 Execução segura

**RECOMENDADO**

O sistema gera e executa código nativo. Por isso, programas maliciosos ou incorretos podem causar travamentos, consumo excessivo de recursos e outras falhas.

Para o escopo acadêmico, é preferível trabalhar inicialmente em ambiente local controlado, com limites de tempo e isolamento adequado.

A publicação pública do serviço de compilação dependeria de controles de segurança adicionais.

---

# 11. Arquitetura e componentes de software

## 11.1 Exigência de modelagem

**EXIGIDO**

O professor solicita implementação orientada a objetos e arquitetura baseada em componentes de software.

A modelagem deverá utilizar UML.

Componentes relevantes:

- Analisador léxico.
- Analisador sintático.
- Analisador semântico.
- Tabela de símbolos.
- Gerador TAC.
- Gerador C++.
- Controle/orquestração do compilador.
- Execução.
- Comunicação.
- Interfaces.

## 11.2 Organização recomendada

A arquitetura deverá separar:

**Núcleo da linguagem**

Definições léxicas, parser, AST e regras semânticas.

**Representações intermediárias**

TAC e estruturas relacionadas.

**Backend**

Tradução para C++ e compilação nativa.

**Runtime**

Bibliotecas necessárias à execução, incluindo paralelismo, canais e suporte de funções nativas.

**Serviços de aplicação**

Orquestração, armazenamento temporário de artefatos, diagnósticos e comunicação com interfaces.

**Apresentação**

CLI, Web original e Web didática.

## 11.3 Reutilização e interfaces

O professor utiliza como referência interfaces de componentes e classes concretas/abstratas.

**PROPOSTO:** evoluir o código orientado a objetos existente em Python, adotando contratos claros entre componentes onde isso trouxer benefício.

Não será necessário reescrever todo o compilador apenas para criar camadas de abstração artificiais.

A modelagem UML deverá refletir fielmente a implementação real.

## 11.4 Diagramas necessários

**EXIGIDO:**

- Diagrama de casos de uso.
- Arquitetura/diagrama de componentes UML.
- Diagramas de classes por componente.

**RECOMENDADO:**

- Diagrama do fluxo de compilação.
- Diagrama de sequência para Fork/Join.
- Diagrama da comunicação distribuída.
- Diagrama do fluxo da interface didática.

Os diagramas recomendados não substituem aqueles explicitamente exigidos.

---

# 12. Documentação e relatório final

## 12.1 Exigências expressas no material

O relatório deverá contemplar, entre outros pontos:

- Gramática e requisitos do MiniPar 2026.2.
- Pseudocódigo do Lexer.
- Pseudocódigo do Parser.
- Pseudocódigo do analisador semântico e tratamento de erros.
- Pseudocódigo da tabela de símbolos.
- Descrição das interfaces.
- Product Backlog.
- Sprint Backlog.
- Diagrama de casos de uso UML.
- Arquitetura de componentes UML.
- Modelagem de classes UML.
- Testes de integração.
- Testes dos programas MiniPar.
- Tecnologias utilizadas.
- Ambiente de desenvolvimento.
- Comentários explicativos no código-fonte.
- Capturas de tela das execuções.
- Repositório GitHub com código, testes e relatório.
- Link do GitHub na capa do relatório.

## 12.2 Documentação recomendada no repositório

**PROPOSTO:**

- `README.md` — apresentação e instruções.
- `docs/ARCHITECTURE.md` — arquitetura técnica.
- `docs/BNF-2026.2.md` — gramática atualizada.
- `docs/DECISIONS.md` — registro de decisões.
- `docs/TESTS.md` — matriz de testes e validação.
- `docs/PARALLELISM.md` — semântica e implementação de Fork/Join.
- `docs/WEB.md` — interfaces e APIs.
- `docs/KNOWN_ISSUES.md` — limitações identificadas.
- `docs/PRESENTATION.md` — tópicos para estudo e apresentação.
- `tests/` — programas e verificações automatizadas.

Os nomes e diretórios são sugestões e não devem ser tratados como estrutura definitiva.

## 12.3 Evidências de validação

As evidências deverão incluir:

- Código MiniPar usado.
- Resultado de cada fase relevante.
- Resultado esperado.
- Resultado obtido.
- Logs de compilação.
- Saída de execução.
- Capturas das interfaces.
- Demonstração de paralelismo.
- Demonstração distribuída quando aplicável.
- Arquivos `.arm` e evidências no CPUlator para o Teste 11.

**Regra:** não registrar um teste como concluído com sucesso sem evidência de sua execução correspondente.

---

# 13. Estratégia de testes e qualidade

## 13.1 Princípio

**DECIDIDO — Validar comportamento, não apenas existência de código.**

Um compilador não estará correto somente porque gera arquivos ou passa exemplos específicos.

A equipe deverá verificar a equivalência entre o programa MiniPar e o comportamento do executável produzido.

## 13.2 Camadas de validação

### Testes unitários

Verificar componentes isoladamente:

- Lexer.
- Parser.
- AST.
- Semântico.
- TAC.
- Gerador C++.
- Runtime.
- Canais.
- Fork/Join.

### Testes de integração

Verificar sequências de fases:

- Lexer → Parser.
- Parser → Semântico.
- Semântico → TAC.
- TAC/AST → Backend.
- Backend → Compilação.
- Compilação → Execução.
- Backend → Interfaces.

### Testes de regressão

Garantir que as alterações não quebrem os programas antigos.

Os testes 1–7 deverão constituir parte importante da regressão.

### Testes de ponta a ponta

Executar programas MiniPar completos, compilando-os e validando os resultados reais.

### Testes negativos

Validar que o compilador rejeita programas inválidos.

Exemplos:

- Variável não declarada.
- Parêntese não fechado.
- Operador sem operando.
- Chamada de função inexistente.
- Argumentos incompatíveis.
- Uso inadequado de Join.
- Referência inválida a tarefa.
- Operações sem tipos compatíveis.

### Testes de paralelismo

Validar sincronização, isolamento, resultados e condições de falha.

### Testes de interface

Validar apresentação correta de cada fase e download/execução.

## 13.3 Critério global de aceitação

O projeto será considerado tecnicamente pronto quando:

1. A gramática estiver atualizada e consistente com a implementação.
2. O compilador conseguir processar os programas esperados.
3. Os testes 1–11 estiverem executados e validados.
4. As falhas relevantes da implementação anterior estiverem corrigidas.
5. Fork/Join tiver comportamento demonstrável.
6. A execução distribuída exigida estiver demonstrada.
7. As três interfaces estiverem funcionais.
8. A interface didática conseguir apresentar as fases solicitadas.
9. O Teste 11 gerar arquivos ARM válidos.
10. O CPUlator confirmar os resultados das expressões.
11. A documentação e o relatório estiverem completos.
12. A apresentação puder ser realizada a partir de um ambiente reproduzível.

Os critérios detalhados de cada módulo ainda serão definidos no planejamento.

---

# 14. Diretrizes para uso de IA e agentes

## 14.1 Papel da IA

**DECIDIDO**

IA poderá ser utilizada para:

- Análise de código existente.
- Proposição de arquitetura.
- Implementação de funcionalidades.
- Criação de testes.
- Revisão de código.
- Identificação de erros.
- Documentação.
- Geração e revisão de diagramas.
- Preparação de materiais de estudo.
- Apoio à apresentação.

O uso de IA não substitui a necessidade de a equipe compreender, testar e defender a implementação.

## 14.2 Estratégia de execução

**PROPOSTO**

Dividir o trabalho em tarefas com:

- Problema definido.
- Arquivos envolvidos.
- Entradas e saídas esperadas.
- Restrições.
- Interfaces com outros componentes.
- Critérios de aceite.
- Testes obrigatórios.
- Regras para preservar funcionalidades existentes.

Evitar instruções amplas como “implemente todo o Fork/Join” sem antes definir sua semântica.

## 14.3 Revisão do trabalho gerado

Todo código relevante produzido por agentes deverá passar por:

- Revisão de alterações.
- Testes de comportamento.
- Testes de regressão.
- Inspeção de impactos entre módulos.
- Verificação de compatibilidade.
- Verificação de segurança quando aplicável.
- Validação por pelo menos um integrante responsável.

## 14.4 Atenção à dívida de compreensão

A implementação poderá avançar mais rapidamente que o entendimento técnico dos integrantes.

Esse risco será controlado por:

- Registro de decisões.
- Explicações do fluxo principal.
- Revisões curtas após funcionalidades complexas.
- Testes com entradas conhecidas.
- Demonstrações intermediárias.
- Estudo concentrado antes da apresentação.

**O objetivo é automatizar a implementação sem perder a capacidade de supervisioná-la.**

---

# 15. Prazo e restrições de calendário

## 15.1 Datas consolidadas

**Prazo oficial:** 11 de novembro de 2026.

**Meta de congelamento das funcionalidades:** 03 de novembro de 2026.

**Janela reservada para estudo:** 04 a 10 de novembro de 2026.

## 15.2 Orçamento de calendário

Considerando início efetivo em 16/10/2026:

- Desenvolvimento inicial, integração e estabilização: 16/10 a 03/11 — 19 dias corridos.
- Revisão técnica, estudo e ensaios: 04/11 a 10/11 — 7 dias corridos.
- Entrega: 11/11.

Esses períodos representam disponibilidade de calendário e não equivalem a jornadas integrais de trabalho.

A disponibilidade real dos três integrantes será levantada no planejamento.

## 15.3 Princípio de congelamento

**DECIDIDO**

A equipe deverá buscar concluir as funcionalidades relevantes até 03/11.

Durante a semana seguinte, a prioridade será:

- Compreender a arquitetura.
- Consolidar a documentação.
- Revisar os algoritmos.
- Ensaiar a apresentação.
- Reproduzir os testes.
- Corrigir defeitos críticos.

A data de congelamento é uma meta interna. Caso exista risco de não atendê-la, o planejamento deverá prever medidas de recuperação sem sacrificar a validação.

## 15.4 Dependências do planejamento futuro

O planejamento detalhado dependerá de:

- Auditoria da versão 2026.1.
- Identificação de dependências técnicas.
- Escolha da sintaxe Fork/Join.
- Definição dos contratos dos componentes.
- Identificação das necessidades reais do Teste 11.
- Disponibilidade dos integrantes.
- Definição do fluxo Git.
- Estimativa das tarefas.
- Priorização por risco.

---

# 16. Principais riscos do projeto

| ID | Risco | Impacto potencial | Estratégia inicial |
|---|---|---|---|
| R01 | Base 2026.1 apresentar falhas ocultas | Retrabalho e regressões | Auditoria antes das extensões. |
| R02 | Fork/Join distribuído exigir infraestrutura complexa | Atraso no núcleo técnico | Construção incremental e esclarecimento da semântica. |
| R03 | Sintaxe nova afetar muitos componentes | Erros e conflitos de integração | Fechar BNF e contratos antes do código. |
| R04 | Testes anteriores utilizarem soluções específicas | Falsa sensação de correção | Testes independentes e negativos. |
| R05 | Teste 10 possuir referência inconsistente | Benchmark ou demonstração incorretos | Validar cargas e documentar diferenças. |
| R06 | Teste 11 exigir recursos adicionais de linguagem | Aumento inesperado do escopo | Mapear dependências antes de portar o Java. |
| R07 | Assembly gerado não funcionar no CPUlator | Falha do Teste 11 | Validar no simulador desde os primeiros exemplos. |
| R08 | Interface didática duplicar lógica do compilador | Inconsistência e retrabalho | Reutilizar serviços de compilação. |
| R09 | Integrações simultâneas causarem conflitos | Retrabalho entre integrantes | Interfaces estáveis e revisões de integração. |
| R10 | Documentação ficar para o último dia | Entrega incompleta | Produzir evidências e documentos incrementalmente. |
| R11 | IA gerar código aparentemente correto | Defeitos difíceis de identificar | Testes de comportamento e revisão humana. |
| R12 | Estudo começar somente após a implementação | Dificuldade na apresentação | Reservar a última semana e revisar durante o desenvolvimento. |

## 16.1 Riscos prioritários

Os maiores riscos preliminares são:

**1. Execução distribuída com Fork/Join.**

Pode exigir alterações profundas no runtime, na geração C++ e nos contratos de comunicação.

**2. Qualidade real do código anterior.**

A quantidade de funcionalidades existentes não garante a correção dos componentes nem a estabilidade do sistema.

**3. Teste 11.**

O MiniCompilador pode depender de operações de strings, objetos e estruturas de dados que ainda não são suportadas adequadamente pela linguagem.

Esses riscos deverão orientar a ordem do planejamento posterior.

---

# 17. Decisões já tomadas

| ID | Decisão | Estado |
|---|---|---|
| D01 | Evoluir MiniPar 2026.1 em vez de reescrever do zero. | Aprovada |
| D02 | Auditar antes de implementar mudanças significativas. | Aprovada |
| D03 | Preservar terminal e primeira interface Web. | Aprovada |
| D04 | Desenvolver a segunda interface Web com foco didático. | Aprovada |
| D05 | Priorizar C++ como backend existente. | Preliminar |
| D06 | Implementar Fork/Join local primeiro. | Aprovada |
| D07 | Evoluir posteriormente para suporte distribuído. | Aprovada |
| D08 | Não depender do vídeo para iniciar o planejamento. | Aprovada |
| D09 | Não criar backend ARMv7 completo sem necessidade. | Aprovada |
| D10 | Implementar o MiniCompilador do Teste 11 em MiniPar. | Exigida |
| D11 | Preferir exportar `.arm` pelo executor/interface. | Preliminar |
| D12 | Validar os 11 testes, incluindo CPUlator. | Exigida |
| D13 | Usar IA para implementação com testes e supervisão. | Aprovada |
| D14 | Concluir funcionalidades até 03/11. | Meta aprovada |
| D15 | Reservar 04/11–10/11 para estudo e apresentação. | Aprovada |
| D16 | Criar planejamento e divisão de tarefas depois deste documento. | Aprovada |

---

# 18. Questões pendentes

## P01 — Sintaxe Fork/Join

Definir formalmente as novas produções da BNF.

A sintaxe deverá estar relacionada à semântica de criação de tarefas, distribuição, resultados e sincronização.

## P02 — Modelo de execução distribuída

Determinar o grau de despacho automático exigido para processos remotos.

Não impede o planejamento inicial, mas precisa ser tratado antes da implementação definitiva.

## P03 — Execução do código herdado

Confirmar funcionamento da versão 2026.1 em ambiente controlado, com evidências dos testes 1–7.

## P04 — Modelo da tabela de símbolos

Decidir se a estrutura atual é suficiente ou se precisa ser formalizada como componente independente.

## P05 — Modelo dos dados entre tarefas

Definir como argumentos e resultados serão representados na comunicação local e remota.

## P06 — Teste 10

Definir formato de saída para Sierpinski e resolver a diferença entre a descrição de seis trabalhadores e o código fornecido.

## P07 — Teste 11

Determinar quais operações de strings, listas e objetos faltam no MiniPar anterior.

## P08 — Arquivos `.arm`

Validar se a exportação pelo sistema executor atende ao professor ou se a escrita deve acontecer dentro do programa MiniPar.

## P09 — Interface didática

Escolher stack visual, biblioteca para AST e contratos da API.

## P10 — Ambiente de execução

Definir sistema operacional principal, compilador C++, dependências e configuração para demonstração.

## P11 — Equipe

Registrar os três integrantes, responsabilidades, disponibilidade e estratégia de trabalho.

## P12 — Integração

Definir estratégia de branches, revisão de PRs, testes obrigatórios e releases.

## P13 — Evidências de apresentação

Definir quais cenários serão demonstrados ao vivo e quais deverão possuir registros reproduzíveis.

---

# 19. Diretrizes para a próxima etapa

A próxima etapa do projeto será a **Auditoria e Mapeamento da Implementação MiniPar 2026.1**.

Essa etapa deverá responder:

1. Como o repositório está organizado?
2. Como executar o sistema?
3. Quais bibliotecas e ferramentas são necessárias?
4. Qual é o fluxo real entre as fases de compilação?
5. Como funcionam a CLI e a Web original?
6. Qual é a cobertura funcional dos testes anteriores?
7. Quais componentes já são suficientemente reutilizáveis?
8. Quais comportamentos estão incorretos ou incompletos?
9. Como o runtime atual implementa paralelismo?
10. Como funciona a comunicação por sockets?
11. Quais limitações impedem os testes 8–11?
12. Quais são as dependências entre as extensões?
13. Quais contratos devem ser estabilizados antes da divisão de tarefas?
14. Qual é a menor sequência de incrementos capaz de atender ao enunciado?

**Saída esperada da auditoria:**

- Mapa da arquitetura existente.
- Inventário das funcionalidades.
- Matriz de testes da baseline.
- Lista priorizada de defeitos.
- Lacunas em relação à BNF 2026.2.
- Mapa de dependências técnicas.
- Recomendações para o planejamento.

A etapa posterior será o **Planejamento Geral e Divisão de Tarefas do Trio**, usando este documento e o resultado da auditoria.

---

# 20. Critérios para considerar o planejamento pronto

Antes de distribuir grandes tarefas de implementação, a equipe deverá conseguir responder:

- Qual arquitetura será preservada?
- Quais componentes serão modificados?
- Qual é a sintaxe aprovada de Fork/Join?
- Qual é o contrato de criação e sincronização de tarefas?
- Como serão executadas tarefas locais?
- Como ocorrerá a comunicação distribuída?
- Como as interfaces acessarão os resultados das fases?
- Quais funcionalidades faltam para o Teste 11?
- Como serão validadas as saídas ARMv7?
- Quem será responsável por cada componente?
- Como os integrantes evitarão conflitos de código?
- Quais testes deverão passar antes de integrar alterações?
- Quais entregas precisam estar prontas antes de 03/11?
- Como será preservada a semana de estudo?

Sem essas definições, o uso simultâneo de agentes de IA em partes dependentes do projeto poderá gerar retrabalho significativo.

---

# 21. Resumo executivo

O projeto MiniPar 2026.2 consiste na evolução de um compilador acadêmico orientado a objetos, com suporte a análise léxica, sintática e semântica, geração de TAC, tradução para C++ e compilação nativa.

As principais novidades são:

**1. Extensão da linguagem:** atualização da BNF e implementação de Fork/Join.

**2. Paralelismo real:** criação, execução e sincronização de tarefas independentes, com suporte à comunicação e execução em computadores diferentes.

**3. Testes:** preservação dos testes 1–7, implementação dos testes 8–10 e atendimento ao Teste 11, que acrescenta um MiniCompilador em MiniPar gerando ARMv7.

**4. Interface didática:** criação de uma segunda Web com visualização clara das fases do compilador, especialmente a AST.

**5. Documentação acadêmica:** atualização de UML, backlogs, pseudocódigos, relatório, testes e evidências de execução.

A equipe utilizará o MiniPar 2026.1 como base, mantendo uma abordagem incremental e validação contínua.

O planejamento deverá priorizar os riscos associados a Fork/Join, execução distribuída, limitações do código herdado e Teste 11.

**Meta de execução:** sistema funcional e integrado até 03/11/2026, com o período de 04/11 a 10/11 reservado para estudo, correções e ensaios, visando à entrega em 11/11/2026.

---

# 22. Controle de evolução do documento

| Versão | Data | Alteração |
|---|---|---|
| 0.1 | 15/10/2026 | Consolidação inicial de requisitos, testes, decisões, riscos e diretrizes. |
| 0.2 | A definir | Incorporar auditoria da versão 2026.1. |
| 0.3 | A definir | Incorporar arquitetura 2026.2 e decisões de Fork/Join. |
| 0.4 | A definir | Incorporar planejamento e divisão de tarefas. |
| 1.0 | A definir | Consolidar a referência técnica validada do projeto. |

**Observação final:** este documento registra o entendimento inicial da equipe. Ele não substitui o enunciado oficial nem demonstra a execução dos requisitos. Sempre que houver divergência entre uma proposta técnica e uma exigência comprovada do professor, a decisão deverá ser revisada e registrada.

**Fim do Documento Mestre Inicial — MiniPar 2026.2 — v0.1.**
