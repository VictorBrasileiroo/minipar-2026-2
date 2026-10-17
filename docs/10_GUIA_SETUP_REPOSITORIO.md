# Guia de criação do repositório novo e importação segura da base

**Estado local verificado — SET-01, 16/10/2026:** este workspace já contém a base ativa, snapshot histórico (36 arquivos), Git/histórico e remoto configurado. SHA-256: 34 correspondências exatas, diferenças esperadas em `README.md` e `.gitignore`, nenhum ausente. **Não executar nova importação ou inicialização Git aqui.** As seções de criação abaixo se aplicam somente a uma estrutura nova ainda sem a base. Evidências: [`auditorias/SET-01_VALIDACAO_ESTRUTURAL.md`](auditorias/SET-01_VALIDACAO_ESTRUTURAL.md).

## 1. Decisão estrutural

O trio terá **repositório novo**, inicialmente recomendado **privado**:

- **Raiz:** projeto MiniPar **2026.2 ativo**, começando por cópia do 2026.1.
- **`legacy/minipar-2026.1/`:** snapshot completo e **imutável** do projeto anterior, para comparação e atribuição.
- **`docs/`:** planejamento, contrato, decisões, backlog e documentação.
- **`runtime/` (C)** e **`web_didatica/` (B)**: implementações futuras isoladas.
- **`tests/2026_2/`**: novos programas 8–11. Os testes anteriores ficam em `tests/` do código ativo após importação.

**Neste workspace o código Python herdado já está copiado.** A orientação anterior de que o pacote continha somente planejamento/importador ficou desatualizada. O método e a data da cópia anterior não foram comprovados; o manifesto que o importador atual produziria não está presente. Não reconstruir metadados dentro de `legacy/` nem repetir a cópia para tentar suprir essa lacuna.

## 2. Criar repositório vazio no GitHub

1. GitHub → New repository.
2. Nome sugerido: `minipar-2026-2` (ou nome escolhido pelo trio).
3. Visibilidade: **Private** inicialmente, até confirmar os direitos de redistribuição da base anterior.
4. **Não** marcar criação automática de README, `.gitignore` ou LICENSE: o pacote já contém README e ignore.
5. Criar. Convidar os outros dois com permissão apropriada depois do primeiro push.

## 3. Obter o MiniPar 2026.1

Fonte: https://github.com/luizwhirl/minipar-improvement .

Pode clonar na sua máquina:
```bash
git clone https://github.com/luizwhirl/minipar-improvement.git minipar-base-2026-1
```

Ou baixar ZIP pelo próprio GitHub e extrair para uma pasta local. **Não** copiar a pasta `.git` da origem para dentro do novo repositório.

Antes de publicar, manter os créditos e verificar as condições de reutilização. Repositório público sem LICENSE **não garante** redistribuição livre.

## 4. Descompactar o pacote deste chat

Somente numa estrutura nova, extrair todo o ZIP para uma pasta de trabalho, por exemplo `MINIPAR_2026_2`, e verificar que a base ainda não existe. Simular primeiro:

Windows PowerShell:
```powershell
py scripts/importar_base.py --source "C:\CAMINHO\minipar-base-2026-1"
```
Se o alias `py` falhar, usar caminho absoluto do Python 3.12 que funcionou na auditoria:
```powershell
& "C:\CAMINHO\Python312\python.exe" scripts/importar_base.py --source "C:\CAMINHO\minipar-base-2026-1"
```
Substituir **ambos** os caminhos pelo seu ambiente real.

Linux/macOS:
```bash
python3 scripts/importar_base.py --source ../minipar-base-2026-1
```

Somente após conferir caminhos, exclusões e ausência de destinos existentes numa estrutura nova, acrescentar `--apply` para copiar. O script bloqueia substituição de arquivos existentes; não edita documentos `docs/` nem `AGENTS.md`. No SET-01 atual nenhum comando `--apply` foi executado.

## 5. Verificações após importação

Confira:
- `legacy/minipar-2026.1/src/lexer.py` existe.
- `src/lexer.py` existe na **raiz** ativa.
- `main.py`, `app.py`, `tests/`, `templates/` e outros componentes antigos ativos estão presentes.
- `legacy/minipar-2026.1/` contém o snapshot; o importador atual também gera `ORIGEM_SNAPSHOT.json` com hashes, data UTC e commit quando a fonte é a raiz de um repositório Git. Neste workspace esse manifesto está ausente e o commit de origem permanece desconhecido. O histórico do novo repositório não comprova o commit antigo.
- `README.md` da raiz continua este guia inicial.
- `python scripts/validar_planejamento.py` retorna sem erros.
- `git status` não inclui `.exe`, `.env`, `venv`, logs, tokens ou artefatos gerados.

Se o script reportar conflito, **não force nem apague o snapshot**. Verifique primeiro se a importação já está completa; se estiver, não a repita. Uma importação parcial exige diagnóstico e correção revisada, preservando os arquivos existentes.

## 6. Inicializar repositório local

Somente para uma estrutura nova que ainda não possua `.git`. Não executar estes comandos no workspace já auditado:

```bash
git init
git branch -M main
git add .
git commit -m "chore: bootstrap MiniPar 2026.2 with legacy snapshot and project plan"
git remote add origin URL_DO_REPO_NOVO
git push -u origin main
```

**Nunca executar `git push --force`** no início. Se o remoto já tiver commits, conciliar antes.

## 7. Proteções básicas no GitHub

- Convidar os outros dois.
- Preferir PR para `main` com revisão, não commits diretos.
- Prefixos de branch por eixo (`eixo-a/`, `eixo-b/`, `eixo-c/`).
- Não criar GitHub Issues ainda; primeiro revisar `docs/01..07` e `planning/cards.json`.
- Evitar upload de segredos e dados pessoais; conferir `git status` antes de commit.
- Se algum recurso de branch protection exigir plano/permite gestão, registrar limitação e usar revisão de PR disciplinada.

## 8. Preparar toolchain — SET-02

**Estado verificado após a instalação manual do usuário (16/10/2026):** CPython **3.12.4**, pip **24.0**, **Flask 3.0.0 na `.venv`**, G++ **16.2.0 (Rev6, Built by MSYS2 project)** em `C:\msys64\ucrt64\bin\g++.exe`, alvo `x86_64-w64-mingw32`, thread model `posix`. Probe C++20/threads/Winsock, smoke `14`, T02 nativo e **T01 local com comunicação real/resultado 5 PASS**. T01: compilação exit=0, execução exit=0 em 0,562 s, sem timeout/stderr, firewall ativo. SET-02 fica IN_PROGRESS, aguardando revisão humana/PR/integração, sem DONE. Evidências atuais na [seção 16 do relatório](auditorias/SET-02_AMBIENTE_E_SMOKE.md#16-t01-local-controlado--validação-final).

### Python local e Flask

Usar a venv do projeto sem depender dos aliases WindowsApps:

~~~powershell
$pyProjeto = Join-Path $PWD '.venv\Scripts\python.exe'
& $pyProjeto --version
& $pyProjeto -m pip --version
& $pyProjeto -c "from importlib.metadata import version; import flask; print(version('Flask'))"
& $pyProjeto -m pip check
~~~

Resultados reais: Python 3.12.4, pip 24.0, Flask 3.0.0 importado, `No broken requirements found.`. Nenhum servidor Web foi aberto; importar Flask não homologa app.py/interface antiga.

Para outro checkout ainda sem venv, localizar um Python funcional e executar `python.exe -m venv .venv`. Instalar somente nela, usando o nome histórico **`requeriments.txt`**, com `Flask==3.0.0`:

~~~powershell
& .\.venv\Scripts\python.exe -m pip install --index-url https://pypi.org/simple -r requeriments.txt
~~~

As tentativas iniciais do Codex falharam e o download oficial do MSYS2 encontrou `WinError 10013`. O usuário fez o setup manualmente; nesta retomada apenas verificamos a instalação existente. Não houve contorno das restrições, instalação global ou mudança de configuração do pip pelo agente. O histórico do diagnóstico está na seção 13 do relatório.

### G++ e DLLs apenas nos processos de teste

O G++ moderno foi conferido por caminho absoluto. Fora dos processos configurados de teste, `Get-Command g++` ainda apontou `C:\MinGW\bin\g++.exe`; manter esse compilador intacto. Não usar `setx`, não editar perfil PowerShell ou variáveis persistentes do usuário/sistema.

Os testes desta rodada foram lançados numa sessão descartável do processo PowerShell, com variáveis herdadas somente pelos seus filhos:

~~~powershell
$env:CXX = 'C:\msys64\ucrt64\bin\g++.exe'
$env:Path = 'C:\msys64\ucrt64\bin;' + $env:Path
$env:PYTHONIOENCODING = 'utf-8'
& .\.venv\Scripts\python.exe -B output/set02/verify_set02.py
~~~

Executar esse trecho em processo/sessão dedicado aos testes. Encerrar o processo descarta as alterações. `CXX` recebe somente o executável, sem flags/aspas internas. O PATH desse processo permite carregar as DLLs da mesma toolchain; não copiar DLLs do MinGW antigo nem adicionar `usr\bin` do MSYS ao PATH do projeto.

O smoke nativo importou `libgcc_s_seh-1.dll`, `libstdc++-6.dll` e `WS2_32.dll`, além das DLLs do Windows/UCRT. A toolchain também contém `libwinpthread-1.dll`; o programa com std::jthread executou corretamente com o ambiente temporário.

### Reproduzir os testes do SET-02

Se o harness ignorado não existir, reconstruí-lo pelo comando da seção 11 do relatório; seu conteúdo está versionado na seção 12. Ele cria uma rodada exclusiva sob `output/set02/`, preservando as anteriores e SET-01. Timeout do compilador: 120 s; timeout de execução: 10 s.

- Probe real: C++20 com parâmetro auto/std::jthread, Winsock inicializado, socket criado/fechado sem bind/listen; stdout esperado e obtido `42`.
- Smoke: `seq { var resultado = 2 + 3 * 4; print(resultado); }`, stdout `14`.
- T02: fatorial `120`, Fibonacci `0,1,1,2,3,5,8,13`. Não exigir ordem global rígida; impressões concorrentes podem se concatenar. O oráculo do harness confere os dois fluxos.
- T01: o harness acima conserva a rodada de compilação e **não inicia o executável**. A execução real foi realizada pelo script abaixo; servidor recebeu `+ 2 3`, cliente recebeu `5.000000`. Uma execução local aprovada não demonstra estabilidade universal nem comunicação entre computadores.

### T01 local controlado no Windows

Script: [`testar_set02_t01_offline.ps1`](../scripts/testar_set02_t01_offline.ps1). O nome do arquivo foi preservado; **o modo padrão agora é local**, autorizado pelo usuário, sem exigir VM ou desativação de adaptadores. Não altera firewall, regras, adaptadores, rotas, runtime, T01 ou política persistente. CXX/PATH são configurados somente nos filhos.

Na raiz do repositório:

~~~powershell
powershell.exe -NoProfile -File .\scripts\testar_set02_t01_offline.ps1 -CheckOnly
powershell.exe -NoProfile -File .\scripts\testar_set02_t01_offline.ps1
~~~

Se a política local impedir carregar o arquivo, após revisão e somente quando permitido pela política organizacional, usar **RemoteSigned no processo**, sem gravar configurações persistentes:

~~~powershell
powershell.exe -NoProfile -ExecutionPolicy RemoteSigned -File .\scripts\testar_set02_t01_offline.ps1 -CheckOnly
powershell.exe -NoProfile -ExecutionPolicy RemoteSigned -File .\scripts\testar_set02_t01_offline.ps1
~~~

Essa forma foi executada nesta rodada e retornou READY e depois PASS. Não usar Bypass ou alterar política de grupo. [Escopo de processo documentado pela Microsoft](https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.core/about/about_execution_policies?view=powershell-5.1).

Os controles são:

- Serviço MpsSvc Running e firewall habilitado nos três perfis, consultados pela API oficial HNetCfg.FwPolicy2 antes/durante/depois das fases. Nenhuma regra de liberação é criada.
- Fonte T01 conferida com os dois canais destinados a `127.0.0.1:5101/5102`. O listener herdado continua `INADDR_ANY`: este modo é teste local sob firewall, sem alegar isolamento total ou bind exclusivo no loopback.
- Portas 5101/5102 livres, por inventário .NET de listeners e conexões IPv4/IPv6, antes da compilação e do runtime. Conflito bloqueia sem encerrar participantes preexistentes; TimeWait/Closed não impedem nova rodada.
- Compilação atual em diretório exclusivo; limite externo 130 s e binário não vazio. Runtime com **10 s** e stdin `+`, `2`, `3`. Job Object estabelecido antes dos filhos encerra a árvore no timeout/aborto. O supervisor usa o interpretador real indicado pela venv, evitando o PID intermediário do launcher Windows; main.py continua usando Python da venv.
- Logs, hashes, returncodes, timeout e limpeza em `output/set02/t01-local-<UTC>-<GUID>/`. PASS exige exit=0, sem timeout/stderr, exatamente um recebimento `Servidor recebeu: + 2 3` e exatamente um resultado numérico 5. READY/CheckOnly é apenas inspeção.

Exit 0=PASS/READY, 1=FAIL, 2=BLOCKED. Falta de controle/recurso impede iniciar. Timeout/erro funcional depois de iniciar é FAIL e registra handoff para CORE-01/Eixo A, separado do ambiente já validado; não corrigir o runtime neste card. Resultado da rodada aprovada: [seção 16](auditorias/SET-02_AMBIENTE_E_SMOKE.md#16-t01-local-controlado--validação-final).

### Offline rigoroso opcional

Adicionar `-StrictOffline` ativa as verificações conservadoras anteriores, **além do firewall**:

~~~powershell
powershell.exe -NoProfile -File .\scripts\testar_set02_t01_offline.ps1 -StrictOffline -CheckOnly
powershell.exe -NoProfile -File .\scripts\testar_set02_t01_offline.ps1 -StrictOffline
~~~

Somente nesse modo, usar Windows local; anotar adaptadores habilitados, desativar temporariamente interfaces físicas/virtuais/VPN e mantê-las assim até terminar, preservando loopback IPv4. O script cruza .NET, adaptadores ocultos, interfaces/rotas em todos os compartimentos; recusa consulta negada, estado desconhecido, compartimentos/rotas externos. A inspeção é amostragem, não barreira atômica. Ao fim, reativar manualmente apenas os adaptadores originalmente habilitados. No Codex, esse modo continua BLOCKED por consulta CIM negada; isso **não bloqueia o modo local**, que passou. Não alterar rede ou política para forçar a aprovação.

### Resultados para revisão

Ao terminar, revisar e enviar `resultado.json`, `run.stdout.txt`, `run.stderr.txt` e `run.result.json`, quando existirem; se falhar na compilação, incluir `compile.stdout.txt`, `compile.stderr.txt` e `compile.result.json`. READY/BLOCKED podem gerar somente resultado.json; recusa anterior ao carregamento do PS não gera pasta. Não é necessário enviar binários/DLLs/credenciais.

### Segurança e compatibilidade de saída

CLI e codegen validam `output_name` antes de ler fonte/remover/gerar arquivos: nome simples, sem caminhos/drives/UNC, caracteres/dispositivos reservados, ponto/espaço final ou destino real fora de output/. Foram aprovados 32 negativos em ambas as entradas, 29 via CLI e 16 nomes legítimos, incluindo todos os 11 programas herdados, espaços internos, acentos e pontos internos.

O backend preserva `-std=c++20 -O3 -pthread`, usa `-lws2_32` somente no Windows e mantém `output/<nome>.exe` e assinaturas herdadas. Linux/macOS tiveram somente fixtures de seleção de flags; não foram compilados nesta rodada. Não há alteração de contrato Fork/Join/Web/T11 nem homologação das interfaces.

### Referências para outros ambientes ainda sem MSYS2

Instalação manual autorizada para este projeto: [página oficial MSYS2](https://www.msys2.org/), [checksum e instalador](https://www.msys2.org/docs/installer/), [atualização](https://www.msys2.org/docs/updating/), [ambientes](https://www.msys2.org/docs/environments/). Usar x86_64/UCRT64 em pasta própria, conferir checksum da mesma versão, atualizar com `pacman -Syu` (reabrir terminal/repetir se solicitado) e instalar `pacman -S --needed mingw-w64-ucrt-x86_64-gcc`. Não repetir a instalação já presente nesta máquina e não reduzir o padrão C++20.

## 9. Próximo passo após push

1. Reunião G0 para nomear B/C e confirmar disponibilidade.
2. Congelar contratos técnicos.
3. Marcar cards READY.
4. Criar GitHub Issues/Project a partir do backlog revisado, sem duplicar fonte de verdade.
5. Começar implementação de acordo com ownership.

**A pasta `legacy/` jamais é o local de desenvolvimento da versão 2026.2.**
