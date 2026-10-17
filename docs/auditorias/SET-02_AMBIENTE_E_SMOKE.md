# SET-02 — Ambiente e smoke real

## 1. Identificação e resumo executivo

- **Card:** SET-02, Pessoa A/coordenador técnico; P0; prazo 18/10/2026. Execução assistida por Codex em **16/10/2026**, America/Sao_Paulo.
- **Branch:** `setup/ambiente-baseline`. Commit-base e HEAD preservado: `0455de305114f6af5f49a83ca224d165566161bf`, `chore(setup): validar estrutura e integridade da base 2026.1`.
- **Inicial:** Git limpo, incluindo não rastreados. SET-01 presente e commitado; aprovação técnica e exceção de branch/PR conjunto autorizadas pelo coordenador no pedido SET-02. Nenhuma alteração do SET-01 foi misturada ou modificada.
- **Planejamento:** estado final **IN_PROGRESS/ready=true**, validação técnica PASS, aguardando revisão humana, PR e integração. Bloqueios anteriores de instalação/isolamento foram superados para o recorte local autorizado. Sem DONE, commit, push, merge ou PR automático.
- **Estado atual:** G++ UCRT64 **16.2.0 Rev6** em `C:\msys64\ucrt64\bin\g++.exe`; Flask **3.0.0** na venv e pip check PASS. Probe C++20/threads/sockets, smoke `14`, T02, negativos e **T01 local com comunicação real/resultado 5 PASS**. T01 compilou exit=0 e executou exit=0 em **0,562 s**, sem timeout/stderr. Seção **16** contém a validação final. Seções 6, 13, 14 e 15 conservam as etapas anteriores, com seus limites históricos.
- **Parecer atual:** requisitos técnicos do SET-02 verificados nesta rodada; aceite administrativo PARTIAL por revisão/PR/integração pendentes. Build para G0 disponível, sem declarar o gate inteiro aprovado. Nenhum outro card iniciado.

Leituras realizadas: AGENTS, README, docs/00, 01, 02, 04, 05, 07, 08, 10, auditoria SET-01, TEMPLATE_HANDOFF e cards.json; main.py, codegen, cpp_template, lexer, parser, semantic, tac, T01/T02 e requeriments.txt. Arquitetura real: **AST → TAC** e **AST → C++ → G++**, ramos independentes. Nenhum contrato Fork/Join/Web/T11 foi implementado ou alterado.

## 2. Ambiente e diagnóstico

| Componente | Observado |
|---|---|
| OS | Windows 11 x64, `10.0.26200`, build completo **26200.9711**, DisplayVersion **25H2**; processo AMD64/64 bits |
| Identificação | Python: `Windows-11-10.0.26200-SP0`; registro confirma build/UBR. ProductName legado do registro ainda informa Windows 10 Home Single Language |
| Python funcional | **CPython 3.12.4**, `tags/v3.12.4:8e8a4ba, Jun 6 2024, 19:30:16`, MSC v.1940 64 bit AMD64; `<perfil>\AppData\Local\Programs\Python\Python312\python.exe` |
| python / python3 | Aliases WindowsApps; ambos falham antes de iniciar: sessão de logon inexistente |
| py | Launcher instalado; `py -0p` aponta Python Store 3.12; `py --version` falha ao criar processo |
| pip | **24.0**, no Python-base e na `.venv` criada |
| Flask | **3.0.0 instalado na venv pelo usuário**, import real e pip check PASS. Tentativas anteriores bloqueadas estão na seção 13 |
| G++ usado nos testes atuais | **`C:\msys64\ucrt64\bin\g++.exe`**, **16.2.0 Rev6 Built by MSYS2 project**, target `x86_64-w64-mingw32`, thread model `posix`. MinGW 6.3.0 antigo preservado; ainda resolve por padrão fora dos processos configurados |
| CXX/PATH atuais de teste | G++ UCRT64 absoluto e seu bin no início do PATH somente no processo PowerShell descartável e seus filhos. Nenhuma variável persistente alterada |
| C++20 | **PASS atual:** probe compilou/linkou e executou com stdout 42. Rejeição pelo GCC antigo é histórica |
| Sockets | **PASS no probe atual:** Winsock inicializado e socket criado/fechado sem bind/listen; não prova comunicação do T01 |
| Threads | **PASS atual:** std::jthread real no probe e threads herdadas no T02; UCRT64 declara posix e tem libwinpthread-1.dll |
| Histórico/isolamento | Antes da instalação manual não foi encontrado outro G++. Agora UCRT64 foi verificado. Docker instalado, mas cliente não conectou ao daemon e teve acesso negado à configuração; Windows Sandbox não localizado. WSL teve enumeração negada na inspeção anterior |

Busca: PATH; `C:\msys64`, msys32, mingw64, MinGW, tools, Program Files/Program Files (x86), app, portVict; diretórios por usuário Programs, Downloads, Compiladores, Scoop, WinGet, JetBrains, PlatformIO e Arduino; tmp/temp e Chocolatey, quando existentes/acessíveis. A inspeção não certifica pastas inacessíveis. Na inspeção inicial somente o antigo foi localizado. Após instalação manual, o moderno é selecionado explicitamente com CXX/PATH temporários; não misturar DLLs das duas distribuições.

`Get-CimInstance Win32_OperatingSystem` foi negado; OS identificado por Python/registro. Git inicialmente recusou ownership diferente: foi usada somente exceção por comando `-c safe.directory=<raiz> -c core.excludesFile=`, sem configuração persistente.

## 3. Correções e decisões

1. **CXX e plataforma:** selecionar executável por nome/caminho, sem flags/aspas internas; fallback `g++`. Preservar `-std=c++20 -O3 -pthread`; adicionar `-lws2_32` somente no Windows. Nenhum downgrade.
2. **Subprocess:** lista de argumentos, sem shell; stdin fechado; captura de stdout/stderr; timeout nativo de **120 s**. Diagnósticos de ausência do compilador, erro de inicialização, returncode e timeout explícitos; saídas parciais do timeout apresentadas.
3. **Binário atual:** invalidar `output/<nome>.exe` antes de ler a fonte, inclusive entrada ausente/inválida; codegen também invalida em chamada direta. Sucesso exige returncode=0 e arquivo atual não vazio. Falha/timeout tenta remover arquivo parcial; erro de remoção é apresentado sem retornar sucesso.
4. **Compatibilidade:** preservar `compile_file(source_path, output_name) -> bool`, `generate(program, output_name) -> bool` e caminhos herdados, inclusive `.exe` em todas as plataformas. Nenhum consumidor ou contrato alterado.
5. **Isolamento:** `.venv` local e fixtures em `output/set02/`, ignorados pelo Git. Instalações pelo agente foram bloqueadas; depois o usuário instalou manualmente UCRT64 e Flask, conferidos na seção 14. Esta retomada não instalou pacotes nem alterou PATH persistente.
6. **output_name:** validação compartilhada antes de qualquer leitura/remoção/geração, tanto em compile_file quanto no codegen direto; nomes simples, rejeição de caminhos Windows/POSIX, dispositivos/caracteres reservados e redirecionamento real dos destinos para fora de output/. Assinaturas públicas preservadas; restrição de entrada explicitamente autorizada pelo usuário.

Limites: saídas relativas ao cwd e por nome; compilações concorrentes do mesmo nome não são isoladas. Não foi criado serviço/ID por requisição; Web/download não homologados. TAC/C++ velhos podem permanecer após erro anterior à geração, mas o binário antigo é invalidado. O timeout limita a chamada ao driver; não há prova de encerramento de toda árvore de processos de toolchain travada. Nenhuma lógica de Lexer/Parser/semântico/TAC/AST/runtime foi corrigida neste card.

## 4. Arquivos alterados

| Arquivo | Motivo |
|---|---|
| `src/codegen.py` | Validação compartilhada de nome/destino, compilador, flags, timeout e binário atual |
| `main.py` | Validar nome antes de qualquer efeito e invalidar binário anterior |
| `docs/10_GUIA_SETUP_REPOSITORIO.md` | Seção 8: ambiente real, instalação proposta e reprodução |
| `docs/04_BACKLOG.md` | Somente ficha SET-02 |
| `planning/cards.json` | Somente status/readiness/evidence do SET-02 |
| `docs/auditorias/SET-02_AMBIENTE_E_SMOKE.md` | Relatório, harness e handoff |
| `scripts/testar_set02_t01_offline.ps1` | Teste local controlado padrão, offline rigoroso opcional; firewall/portas/loopback, timeout e árvore protegida por Job Object; autorizado pelo usuário |

Legado, testes herdados, runtime, web_didatica, app.py/menu.py, demais módulos src e testes 8–11 preservados. Constantes no harness são oráculos de teste; nenhuma saída esperada hardcoded foi introduzida na implementação.

## 5. Comandos de preparação realmente usados

Da raiz; caminho por usuário parametrizado, equivalente ao executável absoluto detectado:

~~~powershell
$pyBase = Join-Path $env:LOCALAPPDATA 'Programs\Python\Python312\python.exe'
& $pyBase --version
& $pyBase -m pip --version
& $pyBase -m venv .venv
$pyProjeto = Join-Path $PWD '.venv\Scripts\python.exe'
& $pyProjeto -m pip --version
& $pyProjeto -m pip install --disable-pip-version-check --no-input --retries 0 --timeout 10 -r requeriments.txt
& 'C:\MinGW\bin\g++.exe' --version
& 'C:\MinGW\bin\g++.exe' -v
& 'C:\MinGW\bin\g++.exe' '-print-file-name=libws2_32.a'
& 'C:\MinGW\bin\g++.exe' '-print-file-name=libwinpthread.dll.a'
& 'C:\MinGW\bin\g++.exe' '-print-file-name=libstdc++.a'
& $pyProjeto -m py_compile main.py src/codegen.py
& $pyProjeto scripts/validar_planejamento.py
& $pyProjeto -B output/set02/verify_set02.py
~~~

pip retornou **exit=1**, `Could not find a version that satisfies the requirement Flask==3.0.0` e `No matching distribution found for Flask==3.0.0`. Não houve instalação global. Nome histórico `requeriments.txt` preservado. Uma primeira consulta `-print-file-name` sem aspas foi dividida pelo PowerShell; corrigida com o argumento inteiro entre aspas, como acima; a tentativa inicial não fundamenta conclusão sobre bibliotecas.

Plano autorizado, sem instalação devido ao bloqueio de rede (seção 13): MSYS2 x86_64 em `C:\msys64`, `pacman -Syu`, `pacman -S --needed mingw-w64-ucrt-x86_64-gcc`; CXX e DLLs UCRT64 no PATH **somente da sessão**. Não remover MinGW antigo nem modificar variáveis persistentes. Passos completos no [guia, seção 8](../10_GUIA_SETUP_REPOSITORIO.md#8-preparar-toolchain--set-02). Fontes oficiais consultadas em 16/10/2026: [instalação](https://www.msys2.org/), [atualização](https://www.msys2.org/docs/updating/), [ambientes](https://www.msys2.org/docs/environments/), [instalador/checksum](https://www.msys2.org/docs/installer/). Nenhum desses passos de instalação foi executado.

## 6. Programas, comandos e resultados reais

Rodada inicial, preservada como histórico desta auditoria: **`output/set02/run-b4elrhcp/`**; preliminar preservada em `run-upij7cpz/`. Logs JSON locais/ignorados contêm comando, stdout/stderr, returncode, timeout e duração. Não foram copiados caminhos pessoais dos logs para este documento. A retomada atual está em `output/set02/run-lo1dozpe/` (seção 13). O harness atualizado abaixo permite reproduzir sem depender desses diretórios.

O main.py ativo foi chamado por caminho absoluto, em cwd separado por caso. T01/T02 usam cópias textuais dos programas herdados (somente finais de linha normalizados na cópia). Os originais não foram editados. Antes do CLI: Lexer/Parser reais, sem tokens UNKNOWN, semântico=True e TAC conferido. Depois: TAC/C++ emitidos pelo fluxo real; só executar se a compilação atual tiver sucesso e produzir arquivo não vazio.

### Probe C++20/threads/sockets

O fonte completo `cxx20.cpp` está no harness: parâmetro `auto`, `std::jthread`, WSAStartup e socket criado/fechado **sem bind/listen**. Oráculo: exit=0 e stdout `42`.

~~~text
C:\MinGW\bin\g++.exe -std=c++20 -O3 <rodada>/cxx20.cpp -o <rodada>/cxx20.exe -pthread -lws2_32
~~~

Obtido: **exit=1**, 0,031 s, sem timeout/binário. Diagnóstico: `unrecognized command line option '-std=c++20'; did you mean '-std=c++03'?`. A sugestão não foi adotada. Threads/sockets não chegaram ao link.

### Smoke

~~~minipar
seq { var resultado = 2 + 3 * 4; print(resultado); }
~~~

Oráculo: **14**. TAC real conferido integralmente:

~~~text
t0 = 3 * 4
t1 = 2 + t0
resultado = t1
print resultado
~~~

### T02 e T01

- T02: `tests/teste2_fatorial_fibonacci_par.minipar` do commit-base. Fatorial 5 = **120**; Fibonacci **0,1,1,2,3,5,8,13**. O harness aceita o print fatorial entre inserções Fibonacci, sem impor ordem global. Não houve stdout nativo nesta rodada.
- T01: `tests/teste1_calculadora_cliente_servidor.minipar` do commit-base. Stdin planejado `+\n2\n3\n`; resultado **5** condicionado à comunicação real. Compilação tentada, execução não iniciada; sem prova de troca de mensagens ou timeout de runtime.

Comandos reais, caminhos abreviados; cwd `<rodada>/<caso>`, timeout externo 130 s:

~~~text
<python-venv> -B <raiz>/main.py <rodada>/smoke/smoke.minipar smoke
<python-venv> -B <raiz>/main.py <rodada>/t02/t02.minipar t02
<python-venv> -B <raiz>/main.py <rodada>/t01/t01.minipar t01
C:\MinGW\bin\g++.exe -std=c++20 -O3 output/<caso>.cpp -o output/<caso>.exe -pthread -lws2_32
~~~

| Caso | Tokens (inclui EOF) | TAC linhas | C++ bytes | CLI exit | Duração | Binário/execução |
|---|---:|---:|---:|---:|---:|---|
| Smoke | 18 | 4 | 4466 | 1 | 0,203 s | Ausente / BLOCKED |
| T02 | 111 | 31 | 5396 | 1 | 0,187 s | Ausente / BLOCKED |
| T01 | 239 | 64 | 6213 | 1 | 0,188 s | Ausente / BLOCKED |

Todos receberam o mesmo diagnóstico C++20 e `[ERRO] Falha na compilacao C++ (exit=1).`. Nenhum timeout de compilação disparou. Limite nativo 120 s; limite de execução preparado 10 s, ainda não exercido com binário real.

**Para retomar T01:** cpp_template usa `address.sin_addr.s_addr = INADDR_ANY`; IP de destino `127.0.0.1` não restringe o listener. Preparar rede isolada para impedir exposição externa, sem alterar canais neste card. O harness não inicia T01 automaticamente. No ambiente isolado, executar o binário atual com stdin de referência, subprocess/timeout=10 e verificar mensagens dos participantes/resultado. Timeout futuro deve ser FAIL/BLOCKED funcional para CORE-01/Eixo A. O timeout conhecido é histórico, não resultado desta rodada.

## 7. Critérios de aceite e matriz de estados atuais

| Critério | Estado | Evidência/limite |
|---|---|---|
| Branch/base/SET-01 commitado; alterações anteriores preservadas | PASS | HEAD 0455de3, mesmo escopo SET-02, nenhum commit novo |
| Python funcional, pip e isolamento | PASS | 3.12.4 / 24.0 / venv local |
| Flask instalado/importado e dependências | PASS | 3.0.0 na venv; pip check exit=0 |
| G++ moderno e C++20/threads/sockets | PASS | UCRT64 16.2.0, probe nativo stdout 42 |
| Lexer/Parser/semântico e TAC/C++ dos três casos | PASS | Fluxo real da rodada UCRT64; TAC conferido |
| G++ sucesso e binário novo dos três casos | PASS | Três CLI exit=0, binários atuais em rodada exclusiva, hashes registrados |
| Smoke completo / saída 14 | PASS | Compilação/execução exit=0, stdout 14 |
| T02 nativo / fatorial e Fibonacci | PASS | Oráculos conferidos em quatro execuções, aceitando interleaving |
| T01 compilação | PASS | CLI exit=0 e binário novo |
| T01 execução/mensagens/resultado 5 | PASS | Modo local autorizado: servidor + 2 3, cliente 5.000000, exit=0, 0,562 s, sem timeout/stderr; seção 16 |
| Proteção contra binário velho e falhas nativas | PASS | 5 negativos reais, agora com erro C++ genuíno em native-failure |
| output_name sem escape e nomes legítimos | PASS | 32 casos em ambas entradas; 29 CLI; 16 nomes legítimos; sentinelas intactas |
| Flags multiplataforma | PARTIAL | Windows nativo PASS; Linux/macOS apenas fixtures |
| Regressão pertinente | PASS | Negativos/harness e C++ dos três casos idêntico ao gerado pelo HEAD; não é baseline T01–T07 |
| Sintaxe Python, planejamento e diff | PASS | Seção 9 e verificação final da retomada |
| Script local controlado | PASS | Fluxo real -File com RemoteSigned só no processo; firewall/portas/cliente loopback e oráculo; 45 asserts adicionais PASS |
| Offline rigoroso opcional | BLOCKED | -StrictOffline -CheckOnly exit=2 por consulta CIM negada; não executa T01, não é requisito padrão |
| Revisão humana, PR e integração | UNTESTED | Pendentes, sem DONE/commit |
| Aceite integral SET-02 | PARTIAL | Requisitos técnicos PASS; revisão humana/PR/integração pendentes, card IN_PROGRESS |
| G0 | PARTIAL | Evidência de build disponível; demais requisitos do gate não avaliados/liberados aqui |

## 8. Testes negativos

Cada negativo real precria `OLD-BINARY-SENTINEL` no nome de saída e executa o main.py ativo. Retorno esperado=1; exige remoção do arquivo; nenhum sentinel é executado.

| Cenário | Resultado obtido | Estado |
|---|---|---|
| CXX inexistente | exit=1, diagnóstico claro, binário velho removido | PASS real |
| Fonte inexistente | exit=1, arquivo não encontrado, velho removido | PASS real |
| Sintaxe `seq { print(2 + ); }` | exit=1, erro sintático, sem binário | PASS real |
| Símbolo `seq { print(nao_declarada); }` | exit=1, erro semântico, sem binário | PASS real |
| Falha nativa | exit=1, erro C++20, velho removido. Fixture `print("a" + "b")` chega ao backend, mas na rodada antiga GCC rejeitou a flag; na atual UCRT64 rejeitou os operandos C++ inválidos | PASS real no tratamento da falha; rodada atual UCRT64 mostra erro C++ inválido (seção 14) |
| Exit=0 sem binário | generate=False e diagnóstico | PASS fixture |
| Exit=0 com arquivo vazio | generate=False e arquivo removido | PASS fixture |
| Exit=2 com saída parcial | Diagnósticos preservados, False, parcial removido | PASS fixture |
| Timeout com stdout/stderr parciais | False, ambos exibidos, parcial removido | PASS fixture; não aguardou 120 s reais |
| PermissionError ao iniciar | False e diagnóstico | PASS fixture |
| Sucesso com arquivo atual não vazio | True só após invalidar sentinel | PASS fixture; não é compilação nativa |
| Linux/darwin | C++20/pthread presentes, ws2_32 ausente | PASS em duas fixtures; build nativo UNTESTED |

Total: **5 negativos reais + 8 fixtures de processo**. Exit=0 do harness atesta seus asserts de análise/controle, sem transformar casos BLOCKED em PASS. As fixtures interceptam subprocess.run e criam arquivos fictícios; não são provas de G++ ou execução de programas. Não foi autorizado corrigir strings pelo exemplo negativo.

## 9. Validação final e comparação à base

~~~powershell
$repoGitPath = (Get-Location).Path.Replace('\','/')
function gitlocal { & git -c "safe.directory=$repoGitPath" -c core.excludesFile= @args }
& .\.venv\Scripts\python.exe -m py_compile main.py src/codegen.py
& .\.venv\Scripts\python.exe scripts/validar_planejamento.py
gitlocal diff --check
gitlocal diff --stat
gitlocal status --short --untracked-files=all
gitlocal diff HEAD --name-only -- legacy runtime web_didatica tests app.py menu.py src/lexer.py src/parser.py src/semantic.py src/tac.py src/ast_nodes.py src/cpp_template.py
~~~

Sintaxe: exit=0. Validador: exit=0, **43 cards**, IDs únicos, datas/dependências válidas, DAG sem ciclos. Não valida build/aceite funcional. Comparação semântica adicional confere metadados e outros 42 cards com HEAD, ficha Markdown fora de SET-02 e os 36 hashes históricos registrados no SET-01. Assinaturas públicas preservadas.

`git diff --check`: exit=0. A auditoria nova não aparece no `diff --stat` enquanto não rastreada; é verificada separadamente. `git diff --stat` registra **cinco arquivos rastreados alterados**, mais este relatório e o script offline novos não rastreados. `git status --short` mostrou `M` em docs/04, docs/10, main.py, cards.json e codegen.py, e `??` no relatório e no script offline novo, ambos conferidos separadamente. A lista final tem somente os sete arquivos autorizados da seção 4 (cinco rastreados alterados e dois novos). `.venv/` e `output/` ignorados; nenhum artefato gerado em legacy. Finais de linha existentes preservados, inclusive main.py sem newline final. Nenhuma evidência SET-01 sobrescrita.

## 10. Handoff, limitações e G0

**Parecer técnico atual: PASS** no recorte SET-02: ambiente, probe, smoke, T02 e T01 local controlado com oráculos verificados. Card IN_PROGRESS/ready=true, revisão humana/PR/integração pendentes. G0 permanece PARTIAL: prova de build disponível, sem avaliar/liberar demais requisitos do gate.

- **Pessoa A/coordenador, SET-02:** revisar diff e evidências da seção 16; critério técnico T01 não depende mais de isolamento total. Não marcar DONE antes de revisão, PR e integração.
- **CORE-01/Eixo C + Eixo A:** receber comandos, logs e limite do resultado: uma execução local T01 PASS, sem provar estabilidade universal ou execução entre computadores. Não houve timeout funcional nesta rodada para encaminhar como FAIL; o risco histórico continua relevante à futura baseline. Baseline T01–T07 não foi executada. Nenhum trabalho de CORE-01 iniciado e nenhuma dependência liberada automaticamente.
- **SET-03:** diagnóstico de toolchain/aliases disponível; acesso dos colegas, owners B/C e dois PCs não validados. Card não iniciado.
- **Interfaces/CORE-08/CORE-09:** assinaturas/caminhos mantidos; CXX e DLLs do mesmo compilador só nos processos. app.py ainda depende do alias `python`, limitação herdada fora deste escopo. Terminal/Web não homologados.

Entrada: smoke da seção 6, T01/T02 intactos, harness e script. Saídas comprovadas: TAC/C++/binários novos, probe 42, smoke 14, T02 120/Fibonacci e T01 servidor + 2 3/cliente 5.000000. Próximo consumidor: coordenador para revisão, depois CORE-01 conforme liberação. Nenhum envio a terceiros realizado.

## 11. Reproduzir o harness versionado

O bloco da seção 12 permite reconstruir `output/set02/verify_set02.py` sem depender dos artefatos ignorados. Na raiz, usar Python da venv para ler este Markdown, extrair o trecho entre `<!-- SET02_HARNESS -->` e o fence Python seguinte, salvar em output/set02 e executar. Comando de extração testado:

~~~powershell
& .\.venv\Scripts\python.exe -B -c "from pathlib import Path; s=Path('docs/auditorias/SET-02_AMBIENTE_E_SMOKE.md').read_text(encoding='utf-8'); m='<!-- SET02_'+'HARNESS -->'; c=s.split(m,1)[1].split(chr(96)*3+'python'+chr(10),1)[1].split(chr(10)+chr(96)*3,1)[0]; p=Path('output/set02'); p.mkdir(parents=True,exist_ok=True); (p/'verify_set02.py').write_text(c+chr(10),encoding='utf-8')"
& .\.venv\Scripts\python.exe -B output/set02/verify_set02.py
~~~

Cada rodada é exclusiva e imprime `EVIDENCE`. O harness é específico a Windows (probe Winsock); fixtures POSIX só conferem argumentos. Falha de assert exige investigação. Compilador incompatível gera BLOCKED explícito nos testes nativos, mesmo se os asserts passarem. O harness preserva seu bloqueio histórico de execução T01; para o modo local atual usar o script e os comandos da seção 16, sem relaxar seus controles.

## 12. Harness executado

<!-- SET02_HARNESS -->
```python
from pathlib import Path
import contextlib, io, json, os, re, shutil, subprocess, sys, tempfile, time
from unittest.mock import patch

ROOT = Path.cwd()
sys.path.insert(0, str(ROOT))
import main
import codegen
from lexer import Lexer, TokenType
from parser import Parser
from semantic import SemanticAnalyzer
from tac import TACGenerator

RUN = Path(tempfile.mkdtemp(prefix='run-', dir=ROOT / 'output/set02'))
results = {}
CXX = os.environ.get('CXX') or shutil.which('g++') or 'g++'
ENV = dict(os.environ, PYTHONIOENCODING='utf-8', PYTHONDONTWRITEBYTECODE='1', CXX=CXX)

def run(label, command, cwd, timeout=130, stdin=''):
    started = time.monotonic()
    try:
        proc = subprocess.run(command, cwd=cwd, env=ENV, input=stdin, capture_output=True,
                              text=True, encoding='utf-8', errors='replace', timeout=timeout)
        item = dict(command=command, returncode=proc.returncode, timed_out=False,
                    stdout=proc.stdout, stderr=proc.stderr)
    except subprocess.TimeoutExpired as exc:
        def decode(value):
            return value.decode('utf-8', errors='replace') if isinstance(value, bytes) else (value or '')
        item = dict(command=command, returncode=None, timed_out=True,
                    stdout=decode(exc.stdout), stderr=decode(exc.stderr))
    item['duration_seconds'] = round(time.monotonic() - started, 3)
    results[label] = item
    (RUN / (label + '.json')).write_text(json.dumps(item, indent=2, ensure_ascii=False), encoding='utf-8')
    print(label, 'returncode=', item['returncode'], 'timeout=', item['timed_out'])
    if item['stderr']:
        print(item['stderr'].strip())
    return item

# output_name deve ser validado antes de remover, abrir ou gerar arquivos.
def verify_output_names():
    work = RUN / 'output-names'
    work.mkdir()
    (work / 'output').mkdir()
    (work / 'valid.minipar').write_text('seq { print(14); }\n', encoding='utf-8')
    sentinels = [work / ('outside.' + ext) for ext in ('exe', 'cpp', 'tac')]
    sentinels.append(work / 'output/kept.exe')
    for path in sentinels:
        path.write_bytes(b'PRESERVE-SET02')
    invalid = [
        str(work / 'outside'),
        '../outside',
        '..\\outside',
        'sub/../../outside',
        'sub\\..\\..\\outside',
        'C:\\outside',
        'C:outside',
        '\\outside',
        '/outside',
        '\\\\server\\share\\outside',
        '\\\\?\\C:\\outside',
        '\\\\.\\NUL',
        'name:stream',
        '.',
        '..',
        '',
        'end.',
        'end ',
        'bad?',
        'bad*',
        'bad|',
        '<bad>',
        'bad"',
        'CON',
        'con.txt',
        'LPT1',
        'NUL',
        'COM¹',
        'bad\n',
        'bad\x00',
        None,
        1,
    ]
    program = Parser(Lexer('seq { print(14); }').tokenize()).parse()
    previous = Path.cwd()
    os.chdir(work)
    try:
        for name in invalid:
            for entry in (lambda n: main.compile_file('valid.minipar', n),
                          lambda n: codegen.CppCodeGenerator().generate(program, n)):
                with patch.object(codegen.os, 'remove') as remove, \
                        patch.object(codegen.subprocess, 'run') as native, \
                        patch('builtins.open', side_effect=AssertionError('must not open input/output')):
                    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                        assert entry(name) is False, repr(name)
                    remove.assert_not_called()
                    native.assert_not_called()
            assert all(path.read_bytes() == b'PRESERVE-SET02' for path in sentinels)
        print('PASS:', len(invalid), 'invalid names in both entry points; no remove/open/spawn')
        # CLI real confirma exit=1, inclusive nome vazio e caminhos absolutos/UNC.
        cli_cases = [name for name in invalid if isinstance(name, str) and chr(0) not in name]
        for i, name in enumerate(cli_cases):
            item = run('output-name-' + str(i),
                       [sys.executable, '-B', str(ROOT / 'main.py'), 'valid.minipar', name], work)
            assert item['returncode'] == 1 and 'output_name invalido' in item['stderr']
            assert all(path.read_bytes() == b'PRESERVE-SET02' for path in sentinels)
        print('PASS:', len(cli_cases), 'invalid names via real CLI; sentinels intact')
        valid = sorted({p.stem for p in (ROOT / 'tests').glob('*.minipar')})
        valid += ['ide_temp', 'Meu programa', 'versão-1.2', '.oculto', 'resultado.v1']
        for name in valid:
            output = work / 'output'
            exe = output / (name + '.exe')
            exe.write_bytes(b'OLD-BINARY')
            with patch.object(codegen.subprocess, 'run', return_value=subprocess.CompletedProcess([], 1, '', 'fixture')) as native:
                with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                    assert main.compile_file('valid.minipar', name) is False
                native.assert_called_once()
                assert native.call_args.args[0][3] == str(Path('output') / (name + '.cpp'))
            assert not exe.exists()
            assert (output / (name + '.cpp')).is_file() and (output / (name + '.tac')).is_file()
        print('PASS:', len(valid), 'legitimate names preserved exactly (including all inherited tests)')
        # Redirecionamentos simulados exercem os.path.realpath sem depender de privilegio de symlink.
        actual_realpath = os.path.realpath
        redirected = RUN / 'outside-output'
        for redirect in ('output', str(Path('output') / 'safe.cpp'), str(Path('output') / 'safe.tac'), str(Path('output') / 'safe.exe')):
            def redirected_realpath(path, *args, **kwargs):
                return str(redirected / 'safe.cpp') if str(path) == redirect else actual_realpath(path, *args, **kwargs)
            for entry in (lambda: main.compile_file('valid.minipar', 'safe'),
                          lambda: codegen.CppCodeGenerator().generate(program, 'safe')):
                with patch.object(codegen.os.path, 'realpath', side_effect=redirected_realpath), \
                        patch.object(codegen.os, 'remove') as remove, \
                        patch.object(codegen.subprocess, 'run') as native:
                    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                        assert entry() is False
                    remove.assert_not_called()
                    native.assert_not_called()
        print('PASS: 4 redirected destinations rejected in both entry points (fixtures)')
    finally:
        os.chdir(previous)

verify_output_names()

probe = RUN / 'cxx20.cpp'
probe.write_text('''#include <winsock2.h>
#include <thread>
#include <iostream>
int twice(auto x) { return x * 2; }
int main() {
    WSADATA data;
    if (WSAStartup(MAKEWORD(2,2), &data)) return 2;
    int answer = 0;
    std::jthread t([&] { answer = twice(21); });
    t.join();
    SOCKET s = socket(AF_INET, SOCK_STREAM, 0);
    if (s == INVALID_SOCKET) return 3;
    closesocket(s); WSACleanup();
    std::cout << answer << std::endl;
}
''', encoding='utf-8')
probe_exe = RUN / 'cxx20.exe'
probe_result = run('cxx20', [CXX, '-std=c++20', '-O3', str(probe), '-o', str(probe_exe),
                           '-pthread', '-lws2_32'], RUN, timeout=120)
if probe_result['returncode'] == 0 and probe_exe.is_file():
    pr = run('cxx20-run', [str(probe_exe)], RUN, timeout=10)
    assert pr['returncode'] == 0 and pr['stdout'].strip() == '42'

smoke = 'seq { var resultado = 2 + 3 * 4; print(resultado); }\n'
cases = [
    ('smoke', smoke),
    ('t02', (ROOT / 'tests/teste2_fatorial_fibonacci_par.minipar').read_text(encoding='utf-8')),
    ('t01', (ROOT / 'tests/teste1_calculadora_cliente_servidor.minipar').read_text(encoding='utf-8')),
]
for label, source in cases:
    work = RUN / label
    work.mkdir()
    src = work / (label + '.minipar')
    src.write_text(source, encoding='utf-8')
    tokens = Lexer(source).tokenize()
    assert not any(t.type == TokenType.UNKNOWN for t in tokens)
    program = Parser(tokens).parse()
    assert SemanticAnalyzer().analyze(program)
    tac = TACGenerator().generate_text(program)
    assert tac.strip()
    if label == 'smoke':
        assert tac == 't0 = 3 * 4\nt1 = 2 + t0\nresultado = t1\nprint resultado\n'
    print(label, 'PASS lexer/parser/semantic; tokens=', len(tokens), 'TAC lines=', len(tac.splitlines()))
    compiled = run(label + '-compile', [sys.executable, '-B', str(ROOT / 'main.py'), str(src), label], work)
    output = work / 'output'
    assert (output / (label + '.tac')).read_text(encoding='utf-8') == tac
    cpp = (output / (label + '.cpp')).read_text(encoding='utf-8')
    assert 'int main()' in cpp
    exe = output / (label + '.exe')
    if compiled['returncode'] != 0:
        assert not exe.exists()
        print(label, 'BLOCKED native execution; no binary; generated TAC/C++ only')
        continue
    assert exe.is_file() and exe.stat().st_size > 0
    if label == 't01':
        # O runtime herdado faz bind em INADDR_ANY. Nao iniciar sem isolamento de rede.
        print('t01 BLOCKED execution: listener INADDR_ANY; requires network isolation')
        continue
    executed = run(label + '-run', [str(exe)], work, timeout=10)
    assert executed['returncode'] == 0 and not executed['timed_out']
    if label == 'smoke':
        assert executed['stdout'].strip() == '14'
    else:
        # Aceitar qualquer posicao do print fatorial entre as insercoes Fibonacci.
        text = executed['stdout']
        matched = False
        for factorial in re.finditer('Fatorial de 5:', text):
            for value in re.finditer('120', text[factorial.end():]):
                pos = factorial.end() + value.start()
                candidate = text[:factorial.start()] + text[factorial.end():pos] + text[pos+3:]
                candidate = candidate.replace('Fibonacci:', '', 1)
                if re.findall(r'\d+', candidate) == ['0','1','1','2','3','5','8','13']:
                    matched = True
        assert matched, repr(text)
    print(label, 'PASS native oracle')

work = RUN / 'negative'
work.mkdir()
(work / 'output').mkdir()
valid = work / 'valid.minipar'
valid.write_text(smoke, encoding='utf-8')
invalid = work / 'invalid.minipar'
invalid.write_text('seq { print(2 + ); }\n', encoding='utf-8')
semantic = work / 'semantic.minipar'
semantic.write_text('seq { print(nao_declarada); }\n', encoding='utf-8')
native_invalid = work / 'native-invalid.minipar'
native_invalid.write_text('seq { print(\"a\" + \"b\"); }\n', encoding='utf-8')
exe = work / 'output/negative.exe'
for label, source, compiler in [
    ('missing-compiler', valid, str(work / 'not-installed-g++.exe')),
    ('missing-source', work / 'absent.minipar', CXX),
    ('invalid-source', invalid, CXX),
    ('semantic-error', semantic, CXX),
    ('native-failure', native_invalid, CXX),
]:
    exe.write_bytes(b'OLD-BINARY-SENTINEL')
    ENV['CXX'] = compiler
    item = run(label, [sys.executable, '-B', str(ROOT / 'main.py'), str(source), 'negative'], work)
    assert item['returncode'] == 1 and not exe.exists(), item
    print('PASS', label, 'old binary invalidated, no execution')
ENV['CXX'] = CXX

# Fixtures de processo: provam controle da infraestrutura, nao compilacao nativa.
previous = Path.cwd()
os.chdir(work)
program = Parser(Lexer(smoke).tokenize()).parse()
passed = 0
try:
    for label in ('no-binary','empty-binary','partial-failure','timeout','launch-error','success'):
        exe.write_bytes(b'OLD-BINARY-SENTINEL')
        def fake_run(command, **kwargs):
            assert isinstance(command, list) and command[0] == CXX
            assert '-std=c++20' in command and '-pthread' in command
            assert '-lws2_32' in command and not kwargs.get('shell')
            assert kwargs['timeout'] == 120 and kwargs['capture_output']
            assert not exe.exists(), 'old binary must be invalidated before spawn'
            if label in ('empty-binary','partial-failure','timeout','success'):
                exe.write_bytes(b'' if label == 'empty-binary' else b'NEW-FIXTURE-BINARY')
            if label == 'timeout':
                raise subprocess.TimeoutExpired(command, 120, output=b'partial stdout', stderr=b'partial stderr')
            if label == 'launch-error':
                raise PermissionError('fixture denied')
            return subprocess.CompletedProcess(command, 2 if label == 'partial-failure' else 0,
                                               stdout='fixture stdout\n', stderr='fixture stderr\n')
        captured, errors = io.StringIO(), io.StringIO()
        with patch.dict(os.environ, {'CXX': CXX}), patch.object(codegen.subprocess, 'run', side_effect=fake_run):
            with contextlib.redirect_stdout(captured), contextlib.redirect_stderr(errors):
                ok = codegen.CppCodeGenerator().generate(program, 'negative')
        assert ok == (label == 'success')
        assert exe.exists() == ok
        if label != 'launch-error':
            assert 'fixture stderr' in errors.getvalue() or 'partial stderr' in errors.getvalue()
        passed += 1
        print('PASS fixture', label)
    exe.unlink()
    for platform in ('linux', 'darwin'):
        def posix_run(command, **kwargs):
            assert '-lws2_32' not in command and '-pthread' in command and '-std=c++20' in command
            return subprocess.CompletedProcess(command, 1, '', 'fixture')
        with patch.object(codegen.sys, 'platform', platform), patch.object(codegen.subprocess, 'run', side_effect=posix_run):
            with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                assert not codegen.CppCodeGenerator().generate(program, 'negative')
        passed += 1
        print('PASS fixture platform', platform, '(not native execution)')
finally:
    os.chdir(previous)
print('PASS:', passed, 'process fixtures')
print('EVIDENCE:', RUN.relative_to(ROOT))
(RUN / 'summary.json').write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding='utf-8')
```

## 13. Histórico: retomada autorizada anterior à instalação manual

### 13.1 Fontes confirmadas antes da tentativa

O usuário autorizou instalar MSYS2/UCRT64 em pasta independente, manter MinGW antigo, não alterar permanentemente PATH e tentar Flask 3.0.0 somente na venv. Também determinou não contornar bloqueios do Codex e exigiu validar output_name antes de remover executáveis. Essas condições foram seguidas.

- [Página oficial MSYS2](https://www.msys2.org/): o link x86_64 apontava para `https://github.com/msys2/msys2-installer/releases/download/2026-09-27/msys2-x86_64-20260927.exe`, organização oficial `msys2`, repositório `msys2-installer`.
- [Instalador/checksum](https://www.msys2.org/docs/installer/): `.sha256` da mesma versão para conferir o download. A primeira chamada local tentou somente esse checksum.
- [Flask 3.0.0 no PyPI](https://pypi.org/project/Flask/3.0.0/): versão publicada por Pallets, requer Python >=3.8, wheel `flask-3.0.0-py3-none-any.whl` hospedado em `files.pythonhosted.org`. Essa metadata não aponta incompatibilidade do pacote Flask com Python 3.12.4; não substitui instalação/teste das dependências.

### 13.2 Download bloqueado, sem instalação ou contorno

Tentativa local real via Python da venv:

~~~python
url = 'https://github.com/msys2/msys2-installer/releases/download/2026-09-27/msys2-x86_64-20260927.exe'
urllib.request.urlopen(url + '.sha256', timeout=15)
~~~

Resultado: **URLError**, `<urlopen error [WinError 10013] Foi feita uma tentativa de acesso a um soquete de uma maneira que é proibida pelas permissões de acesso>`. A leitura do checksum falhou antes do download do executável. Registro local: `output/set02/installation-attempt.json`, `downloaded=false`, `installed=false`. `C:\msys64` continua inexistente. Não houve execução de instalador, pacote GCC, elevação de rede, proxy, desativação de segurança, rota alternativa ou troca de ferramenta para contornar o bloqueio. O MinGW antigo permanece intacto e nenhuma variável persistente foi modificada.

Os passos manuais do guia devem ser executados no Windows normal do usuário. Não é possível concluir instalação/build neste sandbox nas condições atuais.

### 13.3 Diagnóstico do pip/Flask

Nova tentativa autorizada, somente na venv:

~~~powershell
& .\.venv\Scripts\python.exe -m pip install --disable-pip-version-check --no-input --no-cache-dir --retries 0 --timeout 10 --index-url https://pypi.org/simple Flask==3.0.0 -v
& .\.venv\Scripts\python.exe -m pip config list
& .\.venv\Scripts\python.exe -m pip config debug
~~~

- Install: **exit=1**, `Could not find a version that satisfies the requirement Flask==3.0.0 (from versions: none)` e `No matching distribution found for Flask==3.0.0`.
- `pip config list`: exit=0, nenhuma configuração listada. Nenhuma variável `PIP_*` definida no processo.
- `pip config debug`: não encontrou pip.ini global, de usuário ou da venv; nenhuma variável/configuração carregada.
- Inspeção local do parser de opções (sem instalação/rede): `no_index=False`, host do index=`pypi.org`, zero `find_links`. Código do pip inspecionado sem alteração; nenhum sitecustomize/usercustomize carregado.
- Python 3.12.4 e pip 24.0 da venv corretos; `sys.prefix` aponta `.venv` e `include-system-site-packages=false`. Flask continua sem módulo instalado (`find_spec=None`).

Conclusão: não foi encontrado índice errado, `--no-index`, config global/local ou versão inexistente. Há bloqueio de socket comprovado no ambiente; o erro genérico do pip sozinho não identifica a exceção de transporte interna. Portanto registra-se **BLOCKED de acesso ao ambiente de pacotes**, sem afirmar incompatibilidade nem trocar a versão. Nenhuma configuração foi gravada, nenhum pacote global foi instalado e não houve novo download após o bloqueio estabelecido.

Para instalação manual no PowerShell normal, na raiz do projeto, usando a venv existente:

~~~powershell
$pyProjeto = Join-Path $PWD '.venv\Scripts\python.exe'
& $pyProjeto -m pip install --index-url https://pypi.org/simple -r requeriments.txt
& $pyProjeto -c "from importlib.metadata import version; print(version('Flask'))"
# Oraculo: 3.0.0, somente depois de install exit=0.
~~~

### 13.4 Segurança de output_name e compatibilidade

`CppCodeGenerator._validate_output_name` é chamado por **compile_file e generate**, antes de remoção, abertura da fonte, criação de output ou execução do G++. Retorna falha explícita quando o nome não é string não vazia ou contém:

- Separadores `/` ou `\`, caminhos absolutos/relativos com diretórios, drive relativo `C:nome`, UNC e namespaces de dispositivo.
- `.`/`..` isolados, NUL/controle, caracteres Windows reservados, terminação em ponto/espaço, dispositivos CON/PRN/AUX/NUL/COM/LPT e variantes reservadas.
- Redirecionamento de output/ ou do caminho real de um artefato `.exe`, `.cpp` ou `.tac` para fora de output/.

Nomes simples não são sanitizados/renomeados. São preservados os 11 stems dos programas herdados e os cinco adicionais `ide_temp`, `Meu programa`, `versão-1.2`, `.oculto`, `resultado.v1`.

Resultados do harness atualizado:

| Prova | Resultado |
|---|---|
| 32 entradas inválidas nas duas APIs (64 chamadas) | PASS: False, nenhuma chamada a remove/open/subprocess; sentinelas preservadas |
| 29 nomes inválidos via CLI real | PASS: exit=1 e diagnóstico output_name; sentinelas `.exe/.cpp/.tac` fora de output intactas |
| 16 nomes legítimos via pipeline com compilador simulado | PASS: alcança a chamada nativa e gera TAC/C++ com nomes exatos; invalida somente binário correspondente |
| 4 destinos redirecionados nas duas APIs | PASS em 8 chamadas com realpath simulado; sem remoção/spawn |
| 5 negativos reais anteriores | PASS, incluindo falha nativa pelo GCC antigo |
| 8 fixtures anteriores de subprocess/plataforma | PASS; não são builds nativos |

Os 29 casos de CLI excluem NUL (não representável em argv), None e inteiro; esses três foram testados diretamente nas APIs. Casos UNC foram rejeitados lexicalmente, sem acessar rede. Os redirecionamentos são fixtures, não alegação de criação de symlinks/junctions reais. As provas de nomes legítimos simulam a chamada do compilador, sem alegar execução dos binários.

### 13.5 Reexecução nativa e critérios naquele momento

Rodada anterior: **`output/set02/run-lo1dozpe/`**, stdout completo em `output/set02/revalidation.txt`; harness exit=0. Comandos/fases iguais aos da seção 6, com o validador de nomes novo.

| Caso | Returncode | Timeout observado | Duração | Resultado |
|---|---:|---|---:|---|
| Probe C++20/threads/sockets | 1 | Não | 0,031 s | BLOCKED: G++ 6.3 rejeita `-std=c++20` |
| Smoke, oráculo 14 | 1 na compilação | Não | 0,188 s | Análise/TAC/C++ PASS; execução BLOCKED, sem binário |
| T02, 120 e Fibonacci | 1 na compilação | Não | 0,172 s | Análise/TAC/C++ PASS; execução BLOCKED, nenhum valor observado |
| T01, comunicação e 5 | 1 na compilação | Não | 0,172 s | Análise/TAC/C++ PASS; execução BLOCKED |

T01 **não foi iniciado**: não há binário nem prova de ambiente de rede isolado. `INADDR_ANY` herdado permanece intacto. Não houve serviço aberto ou teste de rede público. Depois do setup, somente executar T01 em ambiente já isolado (por exemplo, VM disponível com adaptador externo desconectado, loopback interno ativo e toolchain/DLLs acessíveis), com timeout e registro da condição de isolamento. Nenhuma VM, firewall ou configuração de rede foi instalada/modificada neste card.

Estado histórico daquela rodada, superado pela seção 14: **validação de output_name PASS; preservação dos nomes existentes PASS; confirmação das fontes oficiais PASS; instalação moderna BLOCKED; Flask BLOCKED**. Smoke/T02/T01 nativos continuam BLOCKED. G0/build e aceite formal SET-02 não aprovados; estado continua BLOCKED/ready=true. Sem execução de SET-03, CORE-01 ou outro card; sem commit.

## 14. Validação com UCRT64 instalado manualmente — rodada anterior

> Histórico: ambiente/smoke/T02 continuam válidos. O bloqueio T01 e a exigência de isolamento desta seção foram superados pela autorização local e execução da seção 16.

### 14.1 Ambiente confirmado e configuração temporária

O usuário informou instalação manual; antes de testar, foram executados `Test-Path C:\msys64\ucrt64\bin\g++.exe` (True), `g++.exe --version` e `g++.exe -v` por caminho absoluto. Resultado: **g++.exe (Rev6, Built by MSYS2 project) 16.2.0**, target **x86_64-w64-mingw32**, thread model **posix**. Python da venv: **3.12.4**, pip **24.0**, Flask **3.0.0**.

Instalação de Flask realmente importada da `.venv/Lib/site-packages/flask`; `pip check` retornou exit=0 e `No broken requirements found.`. Dependências presentes: blinker 1.9.0, click 8.5.0, itsdangerous 2.2.0, Jinja2 3.1.6, MarkupSafe 3.0.4 e Werkzeug 3.1.9. Um Flask test_client em memória pôde ser criado, sem bind/servidor; o 404 de uma rota não cadastrada não é homologação da Web antiga. Não houve instalação/upgrade de pacote nesta retomada.

Comandos reais do teste, em processo PowerShell descartável:

~~~powershell
$env:CXX = 'C:\msys64\ucrt64\bin\g++.exe'
$env:Path = 'C:\msys64\ucrt64\bin;' + $env:Path
$env:PYTHONIOENCODING = 'utf-8'
& .\.venv\Scripts\python.exe -B output/set02/verify_set02.py *> output/set02/ucrt64-revalidation.txt
~~~

Essas variáveis foram herdadas somente pelos processos filhos de teste. Nenhum setx, perfil ou variável persistente foi alterado. Fora dessa sessão, `Get-Command g++ -All` ainda indicou **C:\MinGW\bin\g++.exe**, preservado.

`objdump.exe -p` no smoke confirmou importações `libgcc_s_seh-1.dll`, `libstdc++-6.dll` e `WS2_32.dll`, além de Windows/UCRT. `libwinpthread-1.dll` existe no bin da toolchain. O PATH temporário contém as DLLs do mesmo compilador, sem cópia/mistura com o MinGW antigo.

### 14.2 Pipeline nativo, returncodes e oráculos

Rodada **`output/set02/run-ac1pt4u6/`**; harness **exit=0**. Cada caso tem cwd exclusivo; fonte → Lexer/Parser → semântico → TAC e C++ → G++ real → binário atual. Probe e comandos de compilação são os da seção 12, agora com `C:\msys64\ucrt64\bin\g++.exe`. Timeout de G++ 120 s, externo 130 s; execução 10 s.

| Caso/fase | Exit | Duração | Timeout | Resultado |
|---|---:|---:|---|---|
| Probe C++20/std::jthread/Winsock — compilação | 0 | 2,407 s | Não | PASS, binário novo |
| Probe — execução | 0 | 0,093 s | Não | PASS, stdout `42\n` |
| Smoke — compilação | 0 | 2,657 s | Não | PASS, TAC/C++ e executável novos |
| Smoke — execução | 0 | 0,047 s | Não | PASS, stdout `14\n`, stderr vazio |
| T02 — compilação | 0 | 3,625 s | Não | PASS, executável novo |
| T02 — execução inicial | 0 | 0,094 s | Não | PASS, fatorial/Fibonacci conferidos |
| T01 — compilação | 0 | 3,156 s | Não | PASS, executável novo |
| T01 — execução | Não iniciado | — | Não aplicável | BLOCKED: isolamento não comprovado |

O probe inicializa Winsock, executa um cálculo numa std::jthread e cria/fecha um socket sem bind/listen. Isso prova C++20, execução de thread e disponibilidade básica de sockets; **não prova comunicação T01**.

Smoke MiniPar: `seq { var resultado = 2 + 3 * 4; print(resultado); }`, oráculo 14, obtido 14. Fontes T02/T01 são cópias textuais dos programas herdados intactos; TAC foi conferido pelo harness real. Nenhuma saída da implementação foi hardcoded.

### 14.3 T02: quatro execuções e interleaving real

Stdout bruto da primeira execução (escapes representam quebras de linha):

~~~text
Fatorial de 5:Fibonacci: \n1200\n\n1\n1\n2\n3\n5\n8\n13\n
~~~

O `1200` resulta da concatenação entre o print fatorial `120` e o primeiro Fibonacci `0`. O oráculo remove as inserções conhecidas do fluxo fatorial e confere os oito valores Fibonacci em ordem, sem exigir ordem global entre as duas threads.

Três execuções adicionais do **mesmo binário atual**, sempre com ambiente temporário e timeout=10, retornaram exit=0 e PASS:

~~~text
Fatorial de 5: Fibonacci:\n0\n1\n1201\n\n2\n3\n5\n8\n13\n
Fibonacci:\n0\n1\n1\n2\n3\n5\n8\n13\nFatorial de 5: 120\n
Fatorial de 5:Fibonacci: \n120\n0\n1\n1\n2\n3\n5\n8\n13\n
~~~

`1201` também é interleaving de 120 e 1, não valor matemático 1201 produzido pelo algoritmo. Não houve perda de valores observada. Os logs completos estão em `t02-additional-runs.json`. Essa prova não homologa a semântica futura de Fork/Join nem estabilidade universal de stdout concorrente.

### 14.4 Negativos e regressão pertinente

Reexecutados no harness UCRT64: 32 nomes inválidos em ambas as APIs (64 chamadas), 29 negativos reais de CLI, 16 nomes legítimos exatos, quatro redirecionamentos de destino simulados nas duas entradas, cinco negativos reais de infraestrutura e oito fixtures de processo/plataforma: **PASS**. Sentinelas fora de output/ preservadas; nenhum nome inválido removeu arquivo ou iniciou compilador.

O cenário `native-failure` agora foi validado pelo **G++ moderno**, exit=1 em 2,297 s: `invalid operands of types 'const char [2]' and 'const char [2]' to binary 'operator+'` no C++ emitido pela fixture `print("a" + "b")`. Diagnóstico capturado, binário velho removido, nenhum binário parcial aceito. É uma limitação herdada usada como fixture de falha; nenhuma correção de strings foi introduzida neste card.

Para detectar mudança acidental de tradução, o codegen do **HEAD-base** foi carregado em memória; só sua chamada ao compilador foi simulada. O C++ emitido para smoke/T02/T01 foi comparado byte a byte com o atual: **três iguais**. Evidência `cpp-compatibility.json`; fontes de comparação em `output/set02/cpp-compat-1fvwpsyr/`. Não é execução nativa do compilador antigo nem baseline completa T01–T07. Uma primeira limpeza automática do temporário falhou porque o processo ainda tinha aquele cwd; o reprodutor foi corrigido para restaurar cwd antes de encerrar, e os três resultados foram reexecutados/registrados com sucesso. Nenhum arquivo de produto foi afetado por essa falha do harness auxiliar.

| Binário atual | Tamanho | SHA-256 |
|---|---:|---|
| smoke.exe | 55017 bytes | `c5db4087e66ec689c322cb51329ac5f90e659259b59f1c307d8f58da2c8f75b9` |
| t02.exe | 61225 bytes | `290250922f35593695551ad1f6368b00befbfe85ef5caf8d3cd834853872344a` |
| t01.exe | 133205 bytes | `74daf50925faceb1aeb382c80631d3a6204a7915eafdb59a4b81ba5ebccc7142` |

Tamanhos/hashes de TAC e C++ também estão em `artifacts.json`. Nenhum binário será versionado.

### 14.5 T01 e isolamento: bloqueio remanescente

O T01 **compilou**, mas `MiniParChannel` continua fazendo bind em **INADDR_ANY**. Não foi iniciada sua execução no host. Não há stdout, mensagens, resultado 5 ou timeout funcional observado nesta rodada; não registrar PASS por compilar.

Inspeção local de recursos: `WindowsSandbox.exe` não foi localizado. Docker CLI existe, mas `docker version` e as consultas de imagens locais retornaram falha de conexão ao pipe do daemon padrão (inexistente), com acesso negado a `<perfil>/.docker/config.json`. Não foram lidas credenciais, iniciados daemons, baixadas imagens, alterados contextos, criadas VMs ou modificados firewall/adaptadores. A enumeração WSL anterior também foi negada. Nenhum desses indícios prova isolamento; o nome do usuário do sandbox tampouco é prova.

Foi solicitado ao usuário informar um ambiente já isolado disponível, enquanto as demais verificações continuavam. A execução T01 permanece **BLOCKED por ambiente de rede isolado indisponível/não comprovado**. Para retomar: usar o procedimento manual offline no Windows da seção 15, ou outro ambiente já isolado de redes externas com loopback ativo, registrar a condição e executar com stdin `+\n2\n3\n`, timeout explícito e conferência de comunicação/resultado 5. Não mudar o runtime neste card. Se travar depois de iniciado com isolamento, classificar o timeout como falha/bloqueio funcional, com logs para Eixo A/CORE-01.

### 14.6 Estado final e handoff

**Toolchain/Flask PASS; probe, smoke, T02 e negativos PASS; T01 compila PASS e execução BLOCKED. Parecer SET-02: PARCIAL.** O card continua BLOCKED/ready=true, sem DONE, aguardando isolamento para seu critério formal. A evidência de build para G0 agora existe; o gate completo inclui requisitos externos a este card e não foi declarado aprovado.

Nenhuma modificação adicional de main.py/codegen.py foi necessária nesta retomada após instalar a toolchain. Atualizados guia, ficha SET-02 e relatório; depois foi preparado o script offline explicitamente autorizado pelo usuário; cards.json conserva o estado verdadeiro já BLOCKED e a evidência existente. Demais 42 cards/contratos/eixos preservados. CORE-01 recebe futuramente a evidência e a pendência, sem ter sido iniciado. SET-03 não executado. Sem commit/push/PR/merge.

## 15. Procedimento manual offline T01 solicitado pelo usuário — histórico

> Histórico da primeira versão. A seção 16 substitui a exigência offline por modo local controlado padrão; as verificações rigorosas permanecem somente em -StrictOffline. O guia contém os comandos atuais. A restrição inicial de carregamento não persistiu na rodada com RemoteSigned só no processo, permitida pela política local sem GPO.

### 15.1 Autorização, arquivo e limites

O usuário informou não ter VM e solicitou explicitamente **um script de teste offline para executar manualmente no PowerShell**, mantendo loopback e recusando rede externa/virtual ativa. Isso autoriza o novo arquivo `scripts/testar_set02_t01_offline.ps1` dentro do SET-02, além do escopo anterior; não autoriza SET-03, runtime ou outras mudanças estruturais. Nenhum outro script herdado foi editado.

O script não desativa/reativa interfaces, não muda firewall/rotas/políticas, não baixa/instala pacotes e não altera fontes herdados. O usuário prepara e mantém o isolamento manualmente. Inspeção combina .NET NetworkInterfaceType.Loopback com Get-NetAdapter -IncludeHidden, Get-NetIPInterface/Get-NetRoute -IncludeAllCompartments e Get-NetCompartment. Falha de consulta, inventário .NET vazio, ausência de loopback IPv4, estados desconhecidos, compartimento adicional ou rota não loopback bloqueiam o teste. Adaptadores não loopback precisam estar administrativamente Down/operacionalmente Down, ou ausentes; cabo desconectado com Admin Up não basta. Não existe opção para ignorar o controle.

A supervisão revalida o isolamento antes/durante/depois de cada fase; isso é amostragem de estado, **não uma barreira atômica de rede**. Manter os adaptadores desativados até o fim é uma condição da execução. O programa não é iniciado se o estado inicial não puder ser validado.

### 15.2 Processo atual, timeout e evidências

Em diretório exclusivo `output/set02/t01-offline-<UTC>-<GUID>`, o script compila pelo main.py real, sem aceitar executável anterior. Exige exit=0 e binário não vazio; registra hashes de fonte, main.py, codegen, template e binário. Verifica portas 5101/5102 antes da compilação e imediatamente antes do runtime; não encerra processos alheios para liberar portas. CXX/PATH são configurados só nos subprocessos Python/G++/executável.

O supervisor Python embutido no PS usa **Job Object com JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE** e associa a si próprio ao job **antes de criar qualquer filho**. Não permite breakaway nem remove limites de jobs herdados. Se o job não puder ser estabelecido, não cria o processo do teste. O handle pertence somente ao supervisor: saída normal, erro ou encerramento pelo PowerShell fecha o handle e o kernel elimina descendentes, inclusive filhos deixados vivos. Compilação tem limite externo de 130 s, runtime 10 s (parâmetro RunTimeoutSeconds aceita 1–60); os limites do supervisor são independentes da duração das consultas de rede. Timeout grava metadados antes de terminar o job inteiro. O processo PowerShell confirma a saída do dono do job e atualiza cleanup_ok. stdout/stderr são gravados diretamente em arquivos para conservar o que já foi emitido mesmo em aborto.

PASS exige **todas** as condições: compilação atual; isolamento inspecionado; execução exit=0 sem timeout/stderr; exatamente uma mensagem do servidor com `+ 2 3`; exatamente um resultado numérico igual a 5 no cliente. Só achar `Resultado: 5` não passa. O stdin é `+\n2\n3\n`. READY de CheckOnly não executa o compilador nem o programa. Saídas: 0=PASS/READY, 1=FAIL, 2=BLOCKED; política do PowerShell pode impedir carregar o arquivo antes de qualquer saída/JSON do script.

### 15.3 Validação realmente executada no Codex

| Validação | Resultado real |
|---|---|
| Parser PowerShell 5.1 no arquivo final | PASS, zero erros de sintaxe |
| Funções de isolamento/oráculo | 18 fixtures PASS: offline/adapter Down aceitos; físico/virtual Up, Admin Up com cabo desconectado, VPN, estado desconhecido, compartimento/rota externos, inventário vazio, loopback ausente e saídas falsas recusados |
| Guarda de portas | 6 fixtures PASS: vazio/TimeWait/porta alheia aceitos; listener 5101, conexão 5102 e erro de consulta recusados |
| Supervisor Windows real em processos fictícios | 6 casos PASS: sucesso com stdin/stdout/stderr, exit=7, executável inexistente, timeout, filho órfão e aborto do supervisor |
| Encerramento de descendentes | PASS: verificado por handles de processo/WaitForSingleObject; pai e descendente não ficaram ativos em timeout, saída do pai ou aborto do supervisor |
| Ambiente do pai | PASS: inalterado após fixtures do supervisor |
| Execução real do PS com -File ... -CheckOnly | BLOCKED: PowerShell recusou carregar scripts por execution policy; não foi usada opção para contornar isso no Codex |
| Consulta real Get-NetAdapter/Get-NetCompartment | BLOCKED: CIM retornou acesso negado; nenhuma interface foi alterada |
| Fluxo completo do script em Windows offline | UNTESTED; depende da execução manual do usuário |
| T01 real pelo script | PENDENTE/UNTESTED; não foi executado e não tem PASS |

A primeira versão experimental do supervisor usava taskkill /T e **falhou** no teste de timeout deste sandbox. Os dois PIDs criados pela fixture foram encerrados explicitamente com Stop-Process, sem tocar processos alheios. Esse supervisor foi removido e substituído pelo Job Object; os seis testes posteriores passaram. Evidência dos testes finais: `output/set02/offline-job-fixtures-a0au9131/summary.json`; as fixtures de funções têm resumo em `offline-functions-test.txt`. O Python do supervisor extraído da AST foi conferido idêntico ao executado. Não houve execução do T01 nessas fixtures; são processos artificiais sem sockets.

### 15.4 Como o usuário executa e devolve os resultados

Passo a passo completo no [guia de setup atual](../10_GUIA_SETUP_REPOSITORIO.md#t01-local-controlado-no-windows): usar Windows local, anotar adaptadores habilitados, desativar temporariamente físicos/virtuais/VPN, manter loopback ativo, não reativar enquanto o teste estiver em curso. Não usar sessão remota que dependa da rede. Consultas podem exigir PowerShell local com privilégios para inspecionar todos os compartimentos.

Na raiz, depois de revisar o script:

~~~powershell
powershell.exe -NoProfile -File .\scripts\testar_set02_t01_offline.ps1 -CheckOnly
# Somente se READY, repetir sem CheckOnly mantendo o isolamento:
powershell.exe -NoProfile -File .\scripts\testar_set02_t01_offline.ps1
~~~

Se a política local Restricted impedir carregar o arquivo e não houver regra organizacional proibindo, o usuário pode escolher somente para esse processo local:

~~~powershell
powershell.exe -NoProfile -ExecutionPolicy RemoteSigned -File .\scripts\testar_set02_t01_offline.ps1 -CheckOnly
powershell.exe -NoProfile -ExecutionPolicy RemoteSigned -File .\scripts\testar_set02_t01_offline.ps1
~~~

RemoteSigned no processo não grava política persistente e não prevalece sobre política de grupo. Não usar Bypass, não alterar política de organização e não afrouxar a inspeção de rede para obter PASS. Se o arquivo for recusado antes de carregar, não haverá pasta/resultado.json: enviar a mensagem exibida.

Ao terminar e confirmar a saída dos processos, reativar manualmente apenas os adaptadores originalmente habilitados. Enviar `resultado.json`, `run.stdout.txt`, `run.stderr.txt` e `run.result.json`, quando existirem. Se houve erro de compilação, incluir compile.stdout.txt, compile.stderr.txt e compile.result.json. READY/BLOCKED podem gerar somente resultado.json; não enviar binários/DLLs/credenciais. Revisaremos status, auditorias, hashes, returncodes, timeout, limpeza e mensagens antes de aceitar o T01. Os logs de inventário não incluem IPs externos, MACs ou nomes de VPN, mas devem ser revisados antes de compartilhar.

Referências primárias usadas: [adaptadores ocultos](https://learn.microsoft.com/en-us/powershell/module/netadapter/get-netadapter), [interfaces/compartimentos](https://learn.microsoft.com/en-us/powershell/module/nettcpip/get-netipinterface), [rotas](https://learn.microsoft.com/en-us/powershell/module/nettcpip/get-netroute), [Job Objects](https://learn.microsoft.com/en-us/windows/win32/procthread/job-objects), [políticas por processo](https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.core/about/about_execution_policies?view=powershell-5.1). Nenhuma referência documental foi tratada como prova de execução do T01.


## 16. T01 local controlado — validação final

### 16.1 Decisão autorizada e controles

O coordenador autorizou substituir a exigência obrigatória de VM/rede totalmente offline por **teste local controlado no Windows**, com firewall ativo, cliente 127.0.0.1, portas livres, timeout de 10 s, limpeza de descendentes, logs e oráculo real. O requisito rigoroso anterior permanece como opção `-StrictOffline`, sem bloquear o modo padrão. Esta seção e o guia atualizado prevalecem sobre as instruções históricas das seções 14/15.

Arquivo preservado: `scripts/testar_set02_t01_offline.ps1`. Nenhuma alteração no runtime, cpp_template.py, T01 ou outro programa herdado. O script consulta MpsSvc e os três perfis pelo COM oficial **HNetCfg.FwPolicy2**; exige serviço Running e todos habilitados e repete a consulta antes/durante/depois. Não escreve regras, não altera a ação padrão, não abre exceções nem desativa adaptadores. A fonte precisa declarar exatamente os canais 127.0.0.1 nas portas 5101/5102. Listeners e conexões TCP IPv4/IPv6 são consultados com .NET antes de compilar e imediatamente antes de iniciar o binário; conflito bloqueia sem matar terceiros. TimeWait/Closed são desconsiderados.

O listener herdado ainda usa **INADDR_ANY**. O modo autorizado é um teste local sob firewall ativo; não certifica bind exclusivo em loopback, ausência de regras preexistentes, isolamento absoluto ou comunicação entre computadores. Ambos os participantes são threads do mesmo executável e percorrem as chamadas TCP herdadas. A validação observa recebimento da operação/operandos pelo servidor e resultado calculado recebido pelo cliente; não usa saída substituta.

Diretório exclusivo por rodada; recompilação real pelo main.py, binário atual não vazio e hashes. CXX/PATH são definidos somente no ambiente dos subprocessos, apontando a UCRT64. Compilação com limite externo 130 s; runtime com **10 s fixos**. Job Object KILL_ON_JOB_CLOSE precede a criação dos filhos. Timeout salva logs/metadados e encerra supervisor, processo e descendentes; saída/aborto do dono também fecha o job. Erro de preflight ou impossibilidade de iniciar a proteção é BLOCKED; timeout/erro funcional após iniciar é FAIL, com handoff registrado para **CORE-01/Eixo A** e sem reclassificar como falha da instalação UCRT64.

### 16.2 Execução real e resultado

Comandos na raiz, sem configuração persistente (nenhuma GPO de execução definida foi encontrada):

~~~powershell
powershell.exe -NoProfile -ExecutionPolicy RemoteSigned -File .\scripts\testar_set02_t01_offline.ps1 -CheckOnly
powershell.exe -NoProfile -ExecutionPolicy RemoteSigned -File .\scripts\testar_set02_t01_offline.ps1
~~~

RemoteSigned aplica-se apenas ao processo PowerShell iniciado, sem set-executionpolicy persistente ou Bypass. O sandbox do Codex permaneceu ativo; não foi usada execução elevada. A consulta CIM Get-NetFirewallProfile retornou acesso negado; o serviço e a API COM oficial de leitura retornaram **MpsSvc Running, perfil ativo Public (4), Domain/Private/Public=True**. As consultas .NET de listeners/conexões funcionaram. Nenhuma consulta negada foi tratada como aprovação. O script usa diretamente essas APIs disponíveis no modo local; só o modo rigoroso depende das consultas CIM de adaptadores.

| Rodada | Fase/resultado | Exit | Tempo | Timeout/limpeza |
|---|---|---:|---:|---|
| `t01-local-20261016-215542-c83e0e761d36471d99b0bed0c712fe93` | CheckOnly READY: firewall, cliente loopback e portas | 0 | — | Não iniciou compilador/runtime |
| `t01-local-20261016-215548-769ba5a2f022475fa795cf830bcb072a` | BLOCKED no controlador: PID intermediário do launcher venv | 2 | — | Compilação exit=0; runtime não iniciado |
| `t01-local-20261016-215617-6617a5e7ce774b2cb4668a0a832c45df` | Compilação atual PASS | 0 | 2,828 s | Sem timeout; job_guard/cleanup_ok=True |
| mesma rodada | T01 real PASS | 0 | 1,094 s | Sem timeout; job_guard/cleanup_ok=True |
| `t01-local-20261016-215904-812a728003684897a15c03ea80d9dbfe` | Compilação final PASS | 0 | 2,640 s | Sem timeout; job_guard/cleanup_ok=True |
| mesma rodada | T01 final real PASS | 0 | **0,562 s** | Limite 10 s; job_guard/cleanup_ok=True |

Pastas sob `output/set02/`, ignoradas pelo Git. A última rodada recompilou e executou a versão final do script após ajuste de classificação de falha de proteção. Stdout nas duas rodadas aprovadas:

~~~text
==== Calculadora cliente-servidor ====
Opcoes: +, -, *, /
Operacao (+,-,*,/): Operando 1: Operando 2: Servidor recebeu: + 2 3
Resultado: 5.000000
~~~

Stdin: `+\n2\n3\n`. Stderr vazio. Oráculo conferido: **um recebimento + 2 3 no servidor e um resultado numérico 5 no cliente**, compilação/execução exit=0, sem timeout. Não foi apenas buscar o caractere 5. Após a saída: nenhum listener ou conexão ativa nas portas 5101/5102 (TimeWait/Closed desconsiderados), e processos conhecidos de supervisor/runtime encerrados.

| Artefato final | Tamanho/SHA-256 |
|---|---|
| t01.exe | 133205 bytes / `933c414c8c41f4a5555e9b20ccd827106e81e6e101e325acb89a7a7afac644b5` |
| Fonte T01 intacta | `67adf92e955d79b4bb0350dbbfebde9334e9ff5f5554cb49a38a1805245387e3` |
| cpp_template.py intacto | `862ae57327f060b5923d55c097297a2c14ff4bca315477ef8844915fe48f48d6` |

Hashes de main.py e codegen.py, comandos, PIDs, duração e auditorias de firewall estão em resultado.json/compile.result.json/run.result.json. Diferenças de hash entre builds PE em horários/caminhos distintos não foram usadas como oráculo funcional. Logs brutos preservados em todas as rodadas, inclusive a tentativa bloqueada.

### 16.3 Correção da supervisão e verificações negativas

A primeira tentativa de fluxo completo encontrou **PID do supervisor divergente**: o python.exe da venv no Windows é um launcher, que iniciou o interpretador real com outro PID. A compilação terminou, mas o controlador recusou avançar para T01. Foi corrigido somente o script: consultar `sys._base_executable` pela venv e usar esse interpretador diretamente no supervisor (apenas stdlib), mantendo **main.py no Python da venv**. Assim o PID monitorado é o próprio dono do Job Object e Kill pelo controlador fecha seu handle, sem deixar o supervisor órfão. Não removemos a conferência de identidade. O teste completo e as fixtures posteriores confirmaram o comportamento corrigido.

Validações adicionais da versão final: **45 asserts PASS**, arquivo local `output/set02/local-functions-test.ps1`, saída `local-functions-test.txt`, fixtures em `local-guard-fixtures-1ae80053f29f4d928ff74ba1c7cdfe3e/`:

- 17 casos de firewall: máscaras 0–7 com os três perfis ativos aceitas; perfis desativados, serviço parado/desconhecido, máscaras desconhecidas, estado ausente/nulo recusados. São fixtures; a consulta real foi conferida separadamente.
- 7 casos de destino: fonte T01 original aceita; 0.0.0.0, endereço remoto, localhost textual, porta diferente, canal extra e fonte vazia recusados.
- 6 casos de oráculo: comunicação correta aceita; só resultado 5, resultado 50, operação/operando errados e resultado duplicado recusados.
- 5 asserts de seleção/guarda: modo padrão não consulta isolamento; StrictOffline chama e exige a guarda rigorosa; firewall desativado bloqueia antes da consulta de isolamento.
- 4 verificações reais do host: firewall ativo, portas livres, **listeners próprios em 127.0.0.1:5101 e :5102 recusados**, cada um encerrado em finally. Não houve listener externo ou regra criada.
- 6 asserts do wrapper/supervisor real: sucesso com stdin/stdout, identidade de PID, timeout artificial de 1 s, cleanup confirmado e supervisor/processo/descendente encerrados. A fixture usa timeout 1 s para testar o mecanismo, sem mudar os 10 s fixos do T01. Três PIDs conhecidos foram verificados ausentes por Process.GetProcessById/HasExited após encerramento.

O worker embutido continua idêntico ao supervisor da seção 15; os seis testes anteriores de sucesso/erro/timeout/órfão/aborto permanecem válidos. O teste atual exercitou também o wrapper PowerShell com o interpretador real. Testes não executam saídas falsas no T01, não mudam fontes/runtime e não matam processos preexistentes.

Os negativos de output_name e da compilação permanecem PASS na rodada UCRT64 da seção 14: 32 casos nas duas APIs, 29 CLI reais, 16 nomes legítimos, quatro fixtures de destino, cinco negativos reais de infraestrutura e oito fixtures de processo/plataforma. Nenhuma nova alteração em main.py/codegen.py nesta etapa; parser/guardas do script, planejamento, sintaxe Python, pip check, diff e integridade foram conferidos novamente.

### 16.4 Offline opcional e estado verdadeiro do aceite

Executado também:

~~~powershell
powershell.exe -NoProfile -ExecutionPolicy RemoteSigned -File .\scripts\testar_set02_t01_offline.ps1 -StrictOffline -CheckOnly
~~~

Rodada `output/set02/t01-offline-20261016-215743-0a22992bd589436eb401f1c4e7c8f321/`: **BLOCKED, exit=2, Acesso negado**, durante consulta CIM, antes de compilação/runtime. Modo offline rigoroso não teve execução T01; não afirmar PASS offline. O firewall já havia sido aprovado. Esse bloqueio opcional não invalida o modo local expressamente autorizado e realmente executado.

**Estado final:** ambiente e requisitos técnicos SET-02 **PASS**, incluindo T01 local e resultado 5. Aceite administrativo **PARTIAL**, card **IN_PROGRESS/ready=true**, aguardando revisão humana, PR e integração. Não DONE. G0 PARTIAL: evidência de build disponível, outros requisitos não avaliados. CORE-01 recebe esta evidência e o risco histórico de timeout quando autorizado; nenhuma falha funcional ocorreu nas duas execuções atuais para registrar como FAIL. Duas execuções locais não certificam estabilidade universal ou distribuição entre PCs. SET-03/CORE-01 e outros cards não iniciados; sem commit/push/PR/merge.

Para reproduzir/revisar: usar os comandos locais da seção 16.2; -StrictOffline só se desejar as verificações adicionais. Arquivos a compartilhar: resultado.json, run.stdout.txt, run.stderr.txt e run.result.json; em falha de compilação, também compile.*. Não enviar binários, DLLs ou credenciais. Diff integral dos sete arquivos em `output/set02/SET-02_COMPLETO.patch`, artefato de revisão sem inclusão no Git.

Referências oficiais: [estado dos perfis do firewall](https://learn.microsoft.com/en-us/windows/win32/api/netfw/nf-netfw-inetfwpolicy2-get_firewallenabled), [perfil ativo](https://learn.microsoft.com/en-us/windows/win32/api/netfw/nf-netfw-inetfwpolicy2-get_currentprofiletypes), [Job Objects](https://learn.microsoft.com/en-us/windows/win32/procthread/job-objects), [política por processo](https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.core/about/about_execution_policies?view=powershell-5.1). Essas referências explicam APIs/escopo, sem substituir os resultados locais registrados.


### 16.5 Conferência final do workspace

- Sintaxe Python (main.py/codegen.py), parser PowerShell, pip check e validar_planejamento.py: PASS. Planejamento: 43 cards, IDs/datas/dependências válidos, DAG sem ciclos.
- Git diff --check: PASS; novas auditoria e script conferidos separadamente, sem whitespace indevido. Cinco rastreados alterados (194 inserções, 18 remoções) e dois novos: exatamente os sete autorizados da seção 4.
- Demais 42 cards/metadados e ficha Markdown fora de SET-02 iguais ao HEAD; assinaturas públicas preservadas. Finais de linha CRLF dos arquivos existentes e main.py sem newline final mantidos.
- Os 36 arquivos em legacy/minipar-2026.1 conferidos por SHA-256 contra a tabela SET-01, todos iguais. A primeira consulta auxiliar usou por engano os caminhos relativos na raiz ativa e acusou .gitignore, já documentado como divergente; corrigido o prefixo do snapshot, os 36 hashes passaram. Nenhum arquivo de produto foi alterado por essa conferência.
- Harness nativo/negativos da seção 12 idêntico ao arquivo realmente executado; stdout/JSON históricos preservados. Testes atuais adicionais sem alteração de configurações permanentes ou dependências.
- Portas 5101/5102 sem listeners/conexões ativas após os testes (ignorando TimeWait/Closed). Encerramento comprovado pelo Job Object e, nas fixtures, pela saída dos processos próprios. Uma consulta tardia encontrou um PID numérico reutilizável ativo e logo depois ausente; não se usa PID sem identidade/tempo como prova de processo órfão, nem se encerra processo por essa consulta.
- HEAD permanece 0455de305114f6af5f49a83ca224d165566161bf, branch setup/ambiente-baseline. Sem commit, SET-03 ou trabalho em outro card.
