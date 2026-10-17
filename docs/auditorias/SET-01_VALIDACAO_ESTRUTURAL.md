# SET-01 — Validação estrutural e integridade da base 2026.1

## 1. Identificação e escopo

- **Card:** SET-01 — Criar estrutura e importar base 2026.1; P0; prazo 16/10/2026.
- **Data da verificação:** 16/10/2026 (America/Sao_Paulo).
- **Responsável:** Pessoa A, coordenador técnico; execução assistida por Codex.
- **Branch:** `setup/ambiente-baseline`, já preparada pelo usuário e preservada por sua instrução específica (exceção ao nome de branch padrão do AGENTS).
- **HEAD inicial e final do repositório 2026.2:** `a37c168cd60c13ab083782877f6c56b0c588bd1b`.
- **Estado do card:** `IN_PROGRESS`, `ready=true`; tecnicamente pronto para revisão. Não marcado DONE: revisão humana, PR e integração continuam pendentes.
- **Dependências:** nenhuma. Não consome contratos de implementação; C-FJ/C-WEB/C-T11 permanecem propostos, sem mudanças.
- **Autorização específica:** pedido SET-01 permite corrigir README, INICIO_AQUI, docs/08, docs/10, este relatório, estado do SET-01 nos dois backlogs e defeito real do importador. Não autoriza modificar o compilador, testes, runtime, Web didática ou legado.

Leituras realizadas: AGENTS, README, INICIO_AQUI, docs/00, 01, 02, 04, 05, 07, 08 e 10, planning/cards.json, scripts/importar_base.py, scripts/validar_planejamento.py e TEMPLATE_HANDOFF. Também foram inspecionados README/.gitignore/BNF históricos, main.py, entradas Flask/menu/orquestrador, declarações dos componentes de src e READMEs das áreas futuras.

## 2. Estado inicial do Git e do workspace

Os comandos Git sem exceção de propriedade falharam com `detected dubious ownership`: o proprietário do repositório difere do usuário do sandbox. Foi usada somente a opção por comando `-c safe.directory=...`; nenhuma configuração global/local foi gravada. Avisos de acesso ao ignore global foram evitados nas verificações finais com `-c core.excludesFile=`, também por comando. Os arquivos de ignore do próprio repositório continuam valendo.

Resultados reais após essa adaptação:

~~~text
git branch --show-current
setup/ambiente-baseline

git status --short
(sem linhas)

git log --oneline -5
a37c168 add planejamento
7fde81a chore: estrutura inicial e planejamento MiniPar 2026.2

git remote -v
origin  https://github.com/VictorBrasileiroo/minipar-2026-2.git (fetch)
origin  https://github.com/VictorBrasileiroo/minipar-2026-2.git (push)
~~~

O remoto foi inspecionado com sanitização de credenciais antes de exibir; nenhuma credencial estava presente nessa URL. Nenhuma operação alterou o remoto. A existência de `origin` não comprova visibilidade, permissões, proteção ou acesso dos colegas (SET-03).

Foi registrado um inventário SHA-256 inicial dos **106 arquivos fora de .git**, incluindo arquivos ocultos. Não havia mudanças preexistentes rastreadas nem arquivos não rastreados. A conferência final restringiu as alterações aos oito caminhos listados na seção 7.

## 3. Estrutura verificada

| Área | Evidência local | Resultado estrutural |
|---|---|---|
| Núcleo ativo | `src/` com 7 arquivos: lexer, parser, ast_nodes, semantic, tac, codegen, cpp_template | PASS |
| Entradas/interfaces herdadas | `main.py`, `menu.py`, `app.py`, `program_analyzer.py`, `test_orchestrator.py` | PASS |
| Web anterior | `templates/index.html`, `static/css/style.css`, `static/js/script.js` | PASS |
| Gramática/dependências | `BNF-grammar.md` e `requeriments.txt` (`Flask==3.0.0`) | PASS |
| Histórico | `legacy/minipar-2026.1/`, 36 arquivos | PASS local; proveniência limitada conforme seção 5 |
| Testes herdados | 11 programas `.minipar`: T01–T07 e 4 adicionais | PASS de presença, sem execução |
| Resultados esperados | 6 arquivos: T03–T06 em texto, T07 em texto e TAC | PASS de presença; T01/T02 não têm arquivo expected nesta base |
| Documentação acadêmica | `docs/00..11`, templates e 7 arquivos em `docs/fontes/` (README + 6 referências) | PASS de presença, sem homologar conteúdo dos PDFs |
| Auxiliares | `scripts/importar_base.py`, `scripts/validar_planejamento.py`; templates GitHub de tarefa/PR | PASS |
| Áreas futuras | `runtime/README.md`, `web_didatica/README.md`, `tests/2026_2/README.md` | PASS de estrutura reservada; sem implementações |

Não foram encontrados componentes essenciais herdados deslocados ou sem correspondente ativo. A duplicação raiz/snapshot é intencional. `requirements.txt` não existe; o nome real é `requeriments.txt`, mantido intacto. `output/` e `temp_code/` não existiam na inspeção inicial e são diretórios de geração, não fontes ausentes. Não foram criados neste card.

As subpastas `tests/2026_2/test08/` a `test11/` ainda não existem; sua criação está prevista nos cards dos respectivos eixos. O README reserva a área. Nenhuma reorganização foi necessária.

A inspeção de `main.py` confirmou dois ramos da AST: TAC e geração C++, com chamada a G++ no codegen (`-std=c++20 -O3 ... -pthread -lws2_32`). Isso é leitura do código, **não compilação executada**. O diagrama linear do documento mestre é contexto inicial; o contrato docs/02 já descreve corretamente os ramos independentes e não foi alterado.

## 4. Comparação integral snapshot × raiz

Método: SHA-256 dos bytes de cada arquivo, incluindo ocultos; correspondência pelo caminho relativo. A tabela registra os hashes do snapshot observado no início, reconferidos no encerramento.

- **Históricos:** 36.
- **Correspondências exatas:** 34.
- **Divergentes:** 2 (`README.md`, `.gitignore`).
- **Ausentes:** 0.
- **Alterados/adicionados/removidos em legacy durante o card:** 0.

Diferenças esperadas:

- `README.md` ativo descreve o projeto 2026.2 e seu planejamento; o histórico contém a apresentação/créditos do compilador anterior. É reservado em `ROOT_RESERVED` do importador e continuou diferente após a correção documental deste card.
- `.gitignore` ativo cobre ambientes, credenciais usuais, caches, binários, diretórios de saída e auditorias experimentais do projeto novo; o histórico tem regras mais curtas da base. Também é reservado pelo importador. Nenhum dos dois arquivos .gitignore foi editado.

Hashes ativos **antes** das edições: README `cdf6e025caea5dc8038470653c430ade188b1ebfdd41961086f2bf3bbf6bbe17`; .gitignore `7b39aab65b1dfb01e293762af14195b651398488570a20f2874570af43f57546`. O hash ativo do README muda com este card; o histórico permanece o da tabela.

| Caminho relativo ao snapshot | SHA-256 histórico | Correspondente ativo |
|---|---|---|
| `.gitignore` | `e6b98b6752e1c1e10a14338a05cbd5f6c6e81866f9a4f90c7e557348805a93be` | DIVERGENTE (esperado) |
| `app.py` | `74f667cb44e93ffe0a3f56a51c60a2736c9cae8c6e54fb666abdca5ec6b60e17` | IDÊNTICO |
| `BNF-grammar.md` | `903fff04cfc99e592ad08bc0076f82d713b9b4705005ae7b12133546bd3ddf10` | IDÊNTICO |
| `main.py` | `272023067adaad7ee36a709a4ba38d297669a60f26e7982a89e27db2e19a7cb1` | IDÊNTICO |
| `menu.py` | `95dbe809c85b905706408dd7298d5d3a529444b468ec6c13942fa6ff2e750152` | IDÊNTICO |
| `program_analyzer.py` | `60ed39e91860b33b6ddc48be135f3de1accd00fa02e813d9e4444e2d09f65514` | IDÊNTICO |
| `README.md` | `e2f0f3ac4ed2d45cc4bfb1bb37d850bd95b2a0b5a10586668b39d52840f8de07` | DIVERGENTE (esperado) |
| `requeriments.txt` | `170f0e8a1a78e8b323150791491f847ebe47ceb8b4f5a026b1333a673b9fa60a` | IDÊNTICO |
| `src/ast_nodes.py` | `8972643eb4bb8c44478368aa767a1e44084b98d6ca2b28037e124687ca7fcadb` | IDÊNTICO |
| `src/codegen.py` | `54843e57376ad95ce317c2bfb590b501d8c30f70595e3a837582c8d770ec8b9d` | IDÊNTICO |
| `src/cpp_template.py` | `862ae57327f060b5923d55c097297a2c14ff4bca315477ef8844915fe48f48d6` | IDÊNTICO |
| `src/lexer.py` | `6a1481b3ccc7ac681fc2af39390f9017544779e3f0a80e44e4238ae19becdda3` | IDÊNTICO |
| `src/parser.py` | `b365fdc61cc3bf0897705bcab42e8fc266686411ccee8713f8925a5333c44861` | IDÊNTICO |
| `src/semantic.py` | `b2658f95fbfd849fff3e5157ef2773bc063099a6b2151074401d7f96735ee4df` | IDÊNTICO |
| `src/tac.py` | `4dece9681051c55e08d0a9996b8f683e6e0688b83bb0954223e1e016f96c7174` | IDÊNTICO |
| `static/css/style.css` | `6f6756d47daf09f78bd71b32cda1a4b06cedf1f075a85f63f184cef38c94091b` | IDÊNTICO |
| `static/js/script.js` | `e2461b00c6d0bfc5d6974bd011814acd3d79c0b4f4c620ccf0e04c61f71f9661` | IDÊNTICO |
| `templates/index.html` | `2d3ce17a0a9c40cadf4c8360bff6684ebb3cdca1227f8e20edde0cb667885852` | IDÊNTICO |
| `test_orchestrator.py` | `508de0d2aa7c436fa699c60792440e1eff88757985aa9b53fa795f0289c3ab17` | IDÊNTICO |
| `tests/expected_results/teste3_neuronio.expected.txt` | `cc362d440ede03b0328b879965b44335ffb032e2792f26fc2eebc5deca4b9d3a` | IDÊNTICO |
| `tests/expected_results/teste4_rede_neural_xor.expected.txt` | `3f799d710f83ba00ec6e89018aa38dea156d6ca3c8068bd7e05180f4b850cd0c` | IDÊNTICO |
| `tests/expected_results/teste5_recomendacao.expected.txt` | `a66b71d46696ccf1b1c526643270a8f37a023d137583cbba0732d32f094a9e62` | IDÊNTICO |
| `tests/expected_results/teste6_quicksort_classes.expected.txt` | `0be84c44f4a4c05d49a554a242f1a6b8cf37caef7ab01b69b8e44dbdbbc21d17` | IDÊNTICO |
| `tests/expected_results/teste7_quicksort_iterativo_tac.expected.tac` | `29138ee6949efffba9572159a215379bcf5288a4c278735779b3018776869b81` | IDÊNTICO |
| `tests/expected_results/teste7_quicksort_iterativo_tac.expected.txt` | `c9df08889d572afe6a9776c3e6690332b45d4e7feca8b2774959e6f55d545ada` | IDÊNTICO |
| `tests/teste_adicional1_paralelismo_3_computadores.minipar` | `535410cc7bd949261c69e1e06217f8f8a92d041a5d25bd80c26ca8d4b261731a` | IDÊNTICO |
| `tests/teste_adicional2_tapete_sierpinski.minipar` | `d1af85f482bf4d734bcfa72bae21f751e0508760f5ea533594643ed46e857086` | IDÊNTICO |
| `tests/teste_ascii_art_divertidapkrl.minipar` | `ad486c310a9da8fac3d280ef1f6b231a901e33a2eec42f00562ca1a0eab916b5` | IDÊNTICO |
| `tests/teste_bnf_controles_input.minipar` | `c9e9629c2044f6d5e616a5089bc18c03b87b8700d95687e9f3b4ee3cc1835b14` | IDÊNTICO |
| `tests/teste1_calculadora_cliente_servidor.minipar` | `67adf92e955d79b4bb0350dbbfebde9334e9ff5f5554cb49a38a1805245387e3` | IDÊNTICO |
| `tests/teste2_fatorial_fibonacci_par.minipar` | `854259c08699360f0c84f4d424d89ef0a0b74c1318936b0e937f8417d634f7fa` | IDÊNTICO |
| `tests/teste3_neuronio.minipar` | `646d48202307445e156d736afb4720e1b206e851346fed0f3b74295cfddc7d9f` | IDÊNTICO |
| `tests/teste4_rede_neural_xor.minipar` | `4cf9d0ccde4ba1ff47224a8bace770b239bf445b3e9a3defe98db2ddfa5ce867` | IDÊNTICO |
| `tests/teste5_recomendacao.minipar` | `a6182635e0d0933b0abe82c7a3d15c34683e58df8528bded76fee90b004d7c32` | IDÊNTICO |
| `tests/teste6_quicksort_classes.minipar` | `76ae29ffa7445af7d50b2093fd3d212c75929f7432cd2127b7c7153e84287f66` | IDÊNTICO |
| `tests/teste7_quicksort_iterativo_tac.minipar` | `6fbca5f272e1670dba1eeb6a9f065c6042f6d849d673131a105661574a8d8d91` | IDÊNTICO |

A preservação aqui comprovada é **local**: igualdade dos 34 correspondentes e estabilidade dos 36 arquivos em relação ao inventário inicial/Git. Sem manifesto de origem ou checkout externo comprovadamente correspondente, isso não certifica igualdade com um commit específico do upstream.

## 5. Origem, autoria e lacunas

**Origem informada:** <https://github.com/luizwhirl/minipar-improvement>, citada no README/BNF históricos e no planejamento. O README preservado credita:

- Emanuele Vitória de Jesus Lima — [Manu-Vii](https://github.com/Manu-Vii).
- José Lucas de Oliveira Quintela — [lucasqtl](https://github.com/lucasqtl).
- Luiz Miguel de Melo Bomfim — [luizwhirl](https://github.com/luizwhirl).

Não existe `ORIGEM_SNAPSHOT.json` nem `.git` próprio no snapshot. Os dois commits disponíveis no histórico local pertencem à preparação do **2026.2**; não demonstram o commit da base 2026.1. O commit de origem, a data/método da cópia e a correspondência exata com o upstream permanecem **não comprovados**. Não foram inventados metadados nem adicionados arquivos em legacy para suprir a ausência.

**Licença/autorização:** a busca local por LICENSE/LICENCE/COPYING/NOTICE/AUTHORS não encontrou arquivos; nenhuma autorização local de redistribuição foi encontrada na documentação inspecionada. O relato anterior em docs/08 menciona ausência de licença declarada na consulta de 15/10; não equivale a consulta atual. A tentativa de abrir a página do repositório nesta execução retornou `Failed to fetch ... Cache miss`, sem conteúdo verificável. Não se presumiu autorização pela visibilidade pública. A coordenação deve esclarecer os direitos antes de publicação pública.

Essas lacunas não impedem revisar o resultado estrutural do SET-01, cujo aceite pede registrá-las explicitamente. Impedem afirmar proveniência por commit e autorização de redistribuição como resolvidas.

## 6. Importador: avaliação, defeitos e validação segura

A importação já está materialmente presente, portanto **não foi repetida**. O importador não foi executado com `--apply`, nem contra uma fonte real para recópia. A validação usou `runpy`, fixtures descartáveis em diretório temporário e somente o fluxo de simulação.

| Aspecto | Evidência/resultado |
|---|---|
| Sobrescrita | Destinos já existentes na raiz/snapshot e manifesto existente causam aborto antes da cópia; exit=2 verificado em fixtures |
| Reimportação | Os caminhos ativos/históricos já presentes seriam conflitos; não existe modo de forçar sobrescrita |
| Estrutura | Caminhos relativos mantidos em `LEGACY / rel` e `ROOT / rel`; README/.gitignore/docs etc. são reservados na raiz |
| Exclusões | Diretórios Git, venvs, caches e saída; extensões de binários/logs; arquivos usuais de ambiente |
| Origem futura | Manifesto no fluxo de aplicação inclui URL declarada, commit ou null, data UTC, SHA-256 e arquivos exclusivos do snapshot; inspecionado, sem gerar manifesto neste card |
| Fonte inválida | Igual/filha/ancestral do destino e sem arquivos essenciais rejeitadas com exit=2 |
| Links | Há rejeição explícita de links simbólicos na fonte, inspecionada; não foi feito teste de criação de link neste Windows |

Foram reproduzidos dois defeitos antes da correção:

1. Uma fixture com `main.py`, `src/lexer.py` e `.env.staging` resultava em **3 fontes elegíveis / 6 cópias previstas**. O arquivo de ambiente não era excluído. Correção mínima: excluir arquivos cujo nome começa por `.env.`, além das exclusões existentes.
2. `git_head(src/)`, em subdiretório do repositório atual sem Git próprio, retornava `a37c168...` (com exceção safe.directory restrita ao processo). Poderia atribuir o commit de um ancestral a um ZIP extraído. Correção mínima: verificar `git rev-parse --show-toplevel` e retornar None se não for a própria pasta fonte.

Não houve alteração de API do compilador ou contratos entre eixos. `git_head` mantém tipo/assinatura; melhora a precisão dos metadados de futuras importações. O filtro é uma lista de exclusões, **não detecção universal de segredos**: arquivos arbitrários de credenciais ou artefatos com outros nomes exigem inspeção da fonte antes de uma futura aplicação.

Resultado final das fixtures: **9 verificações PASS**, processo exit=0, sem cópias. Para fontes válidas de Git, o teste usa o HEAD atual apenas como oráculo do helper; isso não atribui esse HEAD à base histórica. O fluxo real de aplicação/serialização do manifesto não foi executado, por restrição expressa do card.

Uma primeira execução do harness de validação falhou por exigir uma ordem incorreta na lista dos arquivos reservados; os números já eram 6/9. Corrigida somente essa asserção do harness (verificar cada caminho), a repetição passou integralmente.

## 7. Arquivos alterados e divergências documentais corrigidas

| Arquivo | Alteração diretamente ligada ao SET-01 |
|---|---|
| `README.md` | Estado real da importação, estrutura ativa, créditos e limites da proveniência |
| `INICIO_AQUI.md` | Remove orientação de importar/inicializar novamente este workspace |
| `docs/08_ESTADO_DA_BASE_2026_1.md` | Separa auditorias externas de evidência estrutural executada aqui |
| `docs/10_GUIA_SETUP_REPOSITORIO.md` | Setup novo condicionado à ausência de base; simulação primeiro; conflitos preservados; nome real de dependências |
| `docs/04_BACKLOG.md` | Somente ficha SET-01: estado/readiness/evidência e interpretação autorizada do status limpo |
| `planning/cards.json` | Somente SET-01: IN_PROGRESS, ready=true, evidência e aceite consistente com o Markdown |
| `scripts/importar_base.py` | Duas correções mínimas da seção 6 |
| `docs/auditorias/SET-01_VALIDACAO_ESTRUTURAL.md` | Novo relatório e handoff reproduzível |

A conferência semântica do JSON confirmou **metadados e outros 42 cards inalterados**. A regra genérica de docs/04 sobre regenerar todo o Markdown foi atendida por atualização limitada e consistente da ficha SET-01, sem reformatar/regerar cards de outros eixos. Os finais de linha dos sete arquivos existentes alterados foram preservados.

Não foi modificado código herdado, programa de teste, runtime, Web, contrato ou AGENTS. Não houve instalação, mudança de PATH, porta aberta, commit, push, merge ou criação de PR.

## 8. Comandos, reprodução e saídas

### 8.1 Git e planejamento

Executar na raiz. Os nomes de função/variável abaixo apenas abreviam os mesmos argumentos por comando usados nesta execução; não alteram configuração persistente:

~~~powershell
$repoGitPath = (Get-Location).Path.Replace('\','/')
function gitlocal { & git -c "safe.directory=$repoGitPath" -c core.excludesFile= @args }
$pySet01 = 'C:\Users\victo\AppData\Local\Programs\Python\Python312\python.exe'
gitlocal branch --show-current
gitlocal status --short
gitlocal log --oneline -5
# Exibir remotos somente depois de sanitizar eventuais credenciais:
gitlocal remote -v | ForEach-Object {
    $_ -replace '(https?://)[^/\s]+@', '$1[REDACTED]@' -replace '([?&](?:token|access_token|key|password)=)[^&\s]+', '$1[REDACTED]'
}
gitlocal rev-parse HEAD
& $pySet01 --version
& $pySet01 scripts/validar_planejamento.py
~~~

O comando solicitado `python scripts/validar_planejamento.py` foi tentado e falhou antes de iniciar Python: alias WindowsApps com erro de sessão de logon. `Get-Command python, python3, py -All` e `py -0p` ajudaram a localizar a instalação. O executável absoluto acima rodou o script real com sucesso antes e depois da alteração de planejamento.

Saída efetivamente obtida (exit=0 em ambas as execuções do validador):

~~~text
Python 3.12.4
Cards: 43. Por eixo: {'A': 12, 'A+B': 2, 'A+C': 1, 'B': 12, 'C': 13, 'EQUIPE': 3}
OK: IDs únicos, datas válidas, dependências existentes e DAG sem ciclos.
~~~

Esse validador verifica IDs, datas, dependências e DAG; não testa compilação, execução, autorização de contratos ou aceite funcional.

Outras inspeções realizadas: `rg --files` (incluindo busca de AGENTS aninhados: somente o AGENTS da raiz fora do legado), `Get-Content` das leituras citadas, listagem recursiva incluindo ocultos, busca de autoria/licença, `git ls-tree -r --name-only HEAD legacy`, `git ls-files --others --exclude-standard`, `git diff HEAD --name-only -- legacy` e revisão integral do diff dos arquivos alterados.

### 8.2 Reproduzir hashes, preservação local e consistência do planejamento

Este comando inclui arquivos ocultos e confere o snapshot contra os hashes desta auditoria. Não importa módulos do compilador e não gera artefatos em legacy.

~~~powershell
@'
from pathlib import Path
import hashlib, json, re, subprocess
root = Path.cwd()
snapshot = root / "legacy/minipar-2026.1"
report = (root / "docs/auditorias/SET-01_VALIDACAO_ESTRUTURAL.md").read_text(encoding="utf-8")
recorded = dict(re.findall(r"^\| `([^`]+)` \| `([0-9a-f]{64})` \|", report, re.M))
historical = {p.relative_to(snapshot).as_posix(): p for p in snapshot.rglob("*") if p.is_file()}
assert set(historical) == set(recorded)
counts = {"MATCH": 0, "DIFF": 0, "MISSING": 0}
for rel, path in sorted(historical.items()):
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    assert digest == recorded[rel], rel + ": snapshot mudou"
    active = root / rel
    status = "MISSING" if not active.is_file() else (
        "MATCH" if active.read_bytes() == path.read_bytes() else "DIFF")
    counts[status] += 1
    print(status, rel, digest)
assert counts == {"MATCH": 34, "DIFF": 2, "MISSING": 0}, counts
git = ["git", "-c", "safe.directory=" + root.as_posix(), "-c", "core.excludesFile="]
assert not subprocess.check_output(git + ["diff", "HEAD", "--name-only", "--", "legacy"], text=True).strip()
old = json.loads(subprocess.check_output(git + ["show", "HEAD:planning/cards.json"]))
new = json.loads((root / "planning/cards.json").read_text(encoding="utf-8"))
assert {k:v for k,v in old.items() if k != "items"} == {k:v for k,v in new.items() if k != "items"}
assert [i for i in old["items"] if i["id"] != "SET-01"] == [i for i in new["items"] if i["id"] != "SET-01"]
print("PASS:", len(historical), "historicos;", counts, "; outros 42 cards inalterados")
'@ | & $pySet01 -B -
~~~

### 8.3 Reproduzir a validação segura do importador

Fixtures fictícias no temporário do sistema; não acessa credenciais reais. Nenhum `--apply`. O `unlink` remove somente o arquivo de conflito que o próprio harness acabou de criar no temporário.

~~~powershell
@'
from pathlib import Path
from unittest.mock import patch
import contextlib, hashlib, io, os, runpy, subprocess, sys, tempfile

root = Path.cwd()
ns = runpy.run_path("scripts/importar_base.py")
main = ns["main"]
passed = 0

def tree(directory):
    return sorted((p.relative_to(directory).as_posix(),
                   hashlib.sha256(p.read_bytes()).hexdigest() if p.is_file() else "DIR")
                  for p in directory.rglob("*"))

def invoke(source, target, legacy):
    main.__globals__.update(ROOT=target, LEGACY=legacy)
    out, err = io.StringIO(), io.StringIO()
    before = tree(target)
    with patch.object(sys, "argv", ["importar_base.py", "--source", str(source)]):
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            try:
                main()
                rc = 0
            except SystemExit as exc:
                rc = exc.code
    assert tree(target) == before, "dry-run alterou destinos"
    return rc, out.getvalue(), err.getvalue()

def ok(label):
    global passed
    passed += 1
    print("PASS:", label)

with tempfile.TemporaryDirectory(prefix="minipar-set01-") as td:
    base = Path(td)
    source, target = base / "source", base / "target"
    legacy = target / "legacy/minipar-2026.1"
    legacy.mkdir(parents=True)
    eligible = ("main.py", "src/lexer.py", "src/nested/helper.py",
                "README.md", ".gitignore", "docs/guide.md")
    excluded = (".env", ".env.local", ".env.production", ".env.staging",
                "src/.env.test", ".git/config", ".venv/file.py",
                "__pycache__/file.pyc", "output/file.cpp", "temp_code/file.cpp",
                "cache.pyc", "binary.exe", "trace.log")
    for rel in eligible + excluded:
        path = source / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("fixture\n", encoding="utf-8")
    rc, out, err = invoke(source, target, legacy)
    assert rc == 0 and not err
    assert "eleg" in out and ": 6" in out and ": 9" in out, out
    assert all(str(Path(rel)) in out for rel in ("README.md", ".gitignore", "docs/guide.md")), out
    print(out.replace(str(source), "<source>").replace(str(target), "<target>").strip())
    ok("exclusoes .env.*, caches, binarios e artefatos; 6 fontes / 9 copias")
    ok("caminhos aninhados e arquivos reservados preservados no plano; nenhuma copia")

    cases = (
        (target / "main.py", "conflito na raiz ativa"),
        (legacy / "src/lexer.py", "conflito no snapshot"),
        (legacy / "ORIGEM_SNAPSHOT.json", "manifesto existente"),
    )
    for conflict, label in cases:
        conflict.parent.mkdir(parents=True, exist_ok=True)
        conflict.write_text("preservar\n", encoding="utf-8")
        rc, out, err = invoke(source, target, legacy)
        assert rc == 2 and "ABORTADO" in out and str(conflict) in out
        ok(label + " aborta antes de copiar (exit=2)")
        conflict.unlink()

    for invalid in (target, target / "child", base):
        invalid.mkdir(exist_ok=True)
        rc, out, err = invoke(invalid, target, legacy)
        assert rc == 2 and "ancestral" in err
    ok("fonte igual, filha ou ancestral rejeitada (exit=2)")

    invalid = base / "invalid"
    invalid.mkdir()
    rc, out, err = invoke(invalid, target, legacy)
    assert rc == 2 and "lexer.py" in err
    ok("fonte sem estrutura MiniPar rejeitada (exit=2)")

    with patch.dict(os.environ, {
        "GIT_CONFIG_COUNT": "1",
        "GIT_CONFIG_KEY_0": "safe.directory",
        "GIT_CONFIG_VALUE_0": root.as_posix(),
    }):
        assert ns["git_head"](root) == subprocess.check_output(
            ["git", "-C", str(root), "rev-parse", "HEAD"], text=True).strip()
        assert ns["git_head"](root / "src") is None
        assert ns["git_head"](source) is None
    ok("HEAD apenas da raiz Git propria; subdiretorio e pasta sem Git retornam None")

    with patch.object(ns["git_head"].__globals__["subprocess"], "run", side_effect=OSError):
        assert ns["git_head"](source) is None
    ok("Git indisponivel retorna None")

print(f"PASS: {passed} verificacoes; nenhum --apply, copia ou commit executado.")
'@ | & $pySet01 -B -
~~~

Saída observada:

~~~text
Fonte:      <source>
Novo repo:  <target>
Arquivos fonte elegíveis: 6
Cópias previstas (snapshot + raiz): 9
Mantidos SOMENTE no snapshot (por segurança): .gitignore, docs\guide.md, README.md
Estado: DRY-RUN (nenhum arquivo será copiado)
Confirme os caminhos e execute novamente com --apply.
PASS: exclusoes .env.*, caches, binarios e artefatos; 6 fontes / 9 copias
PASS: caminhos aninhados e arquivos reservados preservados no plano; nenhuma copia
PASS: conflito na raiz ativa aborta antes de copiar (exit=2)
PASS: conflito no snapshot aborta antes de copiar (exit=2)
PASS: manifesto existente aborta antes de copiar (exit=2)
PASS: fonte igual, filha ou ancestral rejeitada (exit=2)
PASS: fonte sem estrutura MiniPar rejeitada (exit=2)
PASS: HEAD apenas da raiz Git propria; subdiretorio e pasta sem Git retornam None
PASS: Git indisponivel retorna None
PASS: 9 verificacoes; nenhum --apply, copia ou commit executado.
~~~

### 8.4 Verificação final do diff

~~~powershell
gitlocal diff --check
gitlocal diff --stat
gitlocal status --short --untracked-files=all
gitlocal ls-files --others --exclude-standard
gitlocal diff --no-index --check -- NUL docs/auditorias/SET-01_VALIDACAO_ESTRUTURAL.md
# Neste diff de arquivo novo, exit=1 indica diferen?a; n?o houve diagn?stico de whitespace.
gitlocal diff HEAD --name-only -- legacy src main.py app.py menu.py templates static tests runtime web_didatica
~~~

Resultado final: `git diff --check` **PASS, exit=0, sem erros de whitespace** (houve apenas avisos LF/CRLF da configura??o existente do Git). Sete arquivos rastreados alterados (60 inserções / 27 remoções) e este relatório novo, ainda não rastreado. `git diff --stat` não inclui o relatório novo; ele foi lido e verificado separadamente, incluindo seu comando de reprodução. A enumeração final mostrou somente os oito caminhos autorizados da seção 7. O último comando acima não apresentou linhas.

## 9. Critérios de aceite individuais

Os estados abaixo avaliam o recorte autorizado do **SET-01**, sem aprovar funcionalmente o compilador.

| # | Critério pedido | Estado | Justificativa |
|---|---|---|---|
| 1 | Estrutura ativa verificada | PASS | Arquivos/pastas e papéis da seção 3 inspecionados |
| 2 | Integridade do snapshot comprovada | PASS | 36 hashes locais registrados e reconferidos; legado sem mudanças no Git/inventário. Limite: não prova commit upstream |
| 3 | Importação não repetida | PASS | Somente leitura da base real; testes em simulação com fixtures; nenhum --apply |
| 4 | Diferenças snapshot/raiz explicadas | PASS | 34 iguais, README/.gitignore reservados e divergentes, zero ausentes |
| 5 | Proveniência registrada com lacunas | PASS | Origem/créditos locais e HEAD 2026.2 registrados; commit original/licença/autorização explicitamente não comprovados |
| 6 | Importador inspecionado | PASS | Inspeção e nove verificações seguras, duas correções mínimas; aplicação real fora do escopo |
| 7 | Informações desatualizadas corrigidas | PASS | Quatro documentos autorizados atualizados e backlogs SET-01 consistentes |
| 8 | Validador executado | PASS | Script real, Python 3.12.4, 43 cards sem erros, repetido após planejamento |
| 9 | Auditoria reproduzível | PASS | Comandos/hashes/oráculos/harness e saídas incluídos e conferidos |
| 10 | Ausência de modificações indevidas | PASS | Diff/inventário restritos aos oito arquivos; legado/código/testes/eixos preservados |

Condições complementares, sem confundir com os dez critérios:

| Item | Estado | Pendência/dono |
|---|---|---|
| Commit original e vínculo a checkout upstream | BLOCKED | Manifesto/histórico de origem ausentes; coordenação deve obter evidência confiável |
| Licença/autorização de redistribuição | BLOCKED | Nenhum comprovante local e consulta online indisponível; coordenação |
| Compilação nativa, smoke e regressão T01–T07 | UNTESTED | Não executados no SET-01; SET-02/CORE-01 |
| Aplicação real do importador/manifesto gerado | UNTESTED | --apply proibido neste card; inspeção e simulação apenas |
| Revisão humana e integração | Pendente | Coordenador revisa diff, evidências e abre PR; ainda não DONE |

## 10. Handoff para SET-02

**Próximo consumidor:** Pessoa A/coordenador, SET-02 — padronizar Python/G++20 e executar smoke, depois da revisão e integração deste card. SET-02 e SET-03 não foram implementados nem liberados automaticamente.

**Entregue:** raiz ativa e snapshot verificados, 36 hashes históricos, contagem 34/2/0, documentação coerente com cópia existente, importador corrigido e simulado, backlog estrutural válido.

**Interface:** nenhuma API de compilação/runtime/Web foi alterada. Assinaturas e contratos permanecem os existentes. A correção afeta apenas exclusões e precisão de metadados de futuras importações.

**Entrada real para o próximo trabalho:** `requeriments.txt` com Flask 3.0.0; Python local 3.12.4 no caminho da seção 8; `main.py` como entrada e G++ com C++20 solicitado pelo codegen. O alias `python` falhou neste sandbox. Não foi verificada a versão atual de G++ nem instalado ambiente/Flask.

**Validação a executar no SET-02:** definir ambiente isolado e ferramentas suportadas, registrar versões/comandos, realizar smoke MiniPar → C++ → binário → resultado com oráculo. A presença de código e a aprovação do validador de planejamento não substituem isso. Levar limitações conhecidas de TAC/T07/strings descritas em docs/08 para os cards próprios, sem copiar patches experimentais indiscriminadamente.

**Pendências para coordenação:** obter commit/autorizações de origem; revisar os oito caminhos e evidências; providenciar PR e integração antes de DONE. Não reconstruir manifesto por suposição ou editar legacy. Permissões de Git/hosts/colegas são SET-03.

**Avaliação:** PRONTO PARA REVISÃO, com lacunas de proveniência/direitos registradas e aceite funcional do compilador ainda não realizado.
