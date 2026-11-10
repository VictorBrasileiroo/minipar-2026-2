# RUN-06 — Reprodução do deploy em dois computadores

**Card:** `RUN-06` · **Eixo:** C (Erasmo) · **Data desta versão:** 09/11/2026
**Critério de aceite:** outro integrante reproduz a execução em dois PCs **seguindo só as instruções**; logs sem dados pessoais.
**Instruções avaliadas:** [`runtime/README.md` §7](../../runtime/README.md#7-deploy-em-dois-computadores) (deploy), §4 (topologia), §5 (protocolo e erros) e §6 (testes).

## 1. Estado

| Item | Status | Observação |
|---|---|---|
| README do runtime com protocolo, topologia, deploy, testes e problemas comuns | **pronto para revisão** | `runtime/README.md` §4–§7. Os 6 ajustes apontados em 09/11 foram aplicados no §7 (seção 4) |
| Ferramenta para mascarar logs | **PASS** | `runtime/tools/mascarar_log.py`, conferida com um log sintético (05/11) e usada nos logs reais de 09/11 |
| Ensaio dos comandos do §7.2, §7.4 e §7.5 no loopback, pelo autor (05/11) | **PASS como ensaio** | Confere a sintaxe do roteiro; **não** prova duas máquinas |
| **Execução em dois computadores** (09/11) | **PASS** | Coordenador em A (`192.168.x.105`), 4 workers em B (`192.168.x.22`): resultado igual ao `seq` e cada worker com `TASK`/`RESULT ok` vindo do IP de A (seção 3) |
| Queda de worker em rede → `WORKER_LOST` | **PARTIAL** | O worker 7201 já estava fora do ar quando a queda foi rodada: o `join` deu `WORKER_UNAVAILABLE` em 3 s, sem travar. O `WORKER_LOST` com a tarefa em andamento não foi demonstrado entre computadores (seção 3, item 6) |
| Logs dos dois lados anexados | **PASS** | Coordenador (A) e os 4 workers (B), mascarados (seção 5). Fecha a lacuna do `RUN-03`, que só anexou o log do worker |
| `par_rede` do `RUN-05` na mesma sessão | **PASS** | 7 rodadas iguais ao oráculo; ver [`RUN-05_BENCHMARKS.md`](RUN-05_BENCHMARKS.md) §3.1 |
| Ensaio do novo §7 no loopback, pelo autor (09/11) | **PASS como ensaio** | Blocos do README copiados como estão (só os IPs trocados por `127.0.0.1`), em sequência, no Windows PowerShell 5.1: `par` igual ao `seq`, 4 workers com `conexao ... aceita` e `RESULT ok`, queda com `WORKER_LOST` e exit 1, logs mascarados. **Não** prova duas máquinas |
| Reprodução **seguindo só o README** e por outro integrante | **PENDENTE** | Em 09/11 os comandos usados foram um roteiro passado à parte (seção 6), que virou o novo §7. Falta uma execução em dois PCs só com o README atualizado. Quem operou não foi registrado |

O card continua `IN_PROGRESS`. A execução entre dois computadores está provada e o README já tem os ajustes da seção 4, mas o critério de aceite pede uma reprodução feita **só com o README**, e a queda com a tarefa em andamento ainda não foi demonstrada entre computadores. Uma nova execução do §7 em dois PCs fecha as duas pendências.

## 2. Roteiro da reprodução

Quem reproduz **não é o autor do README** e opera a máquina A (coordenador). A máquina B (workers) pode ser de qualquer integrante.

1. Seguir o `runtime/README.md` §7.1 a §7.5 **sem ajuda verbal**. Cada passo que precisar de explicação fora do README é um defeito do README: registre na seção 4.
2. Rodar o §7.6 (queda de worker).
3. Opcional, com tempo: `run_bench.py --destinos-rede` (bench README §4), que preenche o cenário `par_rede` do `RUN-05`.
4. Mascarar os logs (§7.7) e anexar em `docs/evidencias/RUN-06/`.

## 3. Registro da execução

*Campo sem dado fica "não registrado".* Horários tirados dos arquivos de A e do `bench.json`.

| Campo | Máquina A (coordenador) | Máquina B (workers) |
|---|---|---|
| Data/hora | 09/11/2026: `par` às 14:27, bench às 14:29–14:30, queda às 14:36 | 09/11/2026, mesmos horários (data dos logs no zip de B) |
| Quem operou | não registrado | não registrado |
| Hostname (apelido) | `pc-A` | `pc-B` |
| IP mascarado (`192.168.x.N`) | `192.168.x.105` | `192.168.x.22` |
| SO e G++ | Windows 11 10.0.26300, G++ 16.2.0 (MSYS2 UCRT64) | não registrado |
| Commit (`git rev-parse --short HEAD`) | `43a7c34` (sem diferença para `dev` `249afaa` em `src/`, `runtime/` e `tests/2026_2/test08/`) | não registrado; o `build_id` dos workers (`69d0f55f…`) é o mesmo do fonte de A, então o programa é o mesmo |
| SHA-256 do `teste8.exe` (16 primeiros) | não registrado (o do `bench_t08.exe` é `23f213322dbed10a`) | não registrado |

| # | Verificação | Status | Evidência |
|---|---|---|---|
| 1 | Os 4 workers de B escutam no IP de B (`escutando em <IP-de-B>:720N`) | **PASS** | 1ª linha de cada `worker_720N_B.log`: `escutando em 192.168.x.22:720N`, mesmo `build_id` |
| 2 | Cada worker aceita conexão vinda do IP de A | **PASS** | `conexao de 192.168.x.105:... aceita (build_id ok)` nos 4 logs. IPs diferentes nos dois lados |
| 3 | Coordenador em A: `TOTAL 160`, `UNICOS 160`, `DUPLICADOS 0`, `PERDIDOS 0` | **PASS** | `coordenador_A.txt`, com `MODO par` |
| 4 | `SOMA_NOTAS` do `par` remoto igual à do `seq` em A | **PASS** | `SOMA_NOTAS 7630` em `coordenador_A.txt` e em `coordenador_A_seq.txt` |
| 5 | Cada worker registra 1 `TASK` e 1 `RESULT ok` de `avaliar_lote` | **PASS** | 1ª conexão de cada log: `task-1` a `task-4`, `RESULT ... ok` em 255–415 ms. As 8 conexões seguintes (todas `ok`) são o aquecimento e as 7 rodadas do bench `par_rede` |
| 6 | Queda de um worker → `WORKER_LOST`, exit 1, sem travar | **PARTIAL** | `coordenador_A_queda.txt`: `join task-1 falhou: WORKER_UNAVAILABLE: worker 192.168.x.22:7201 indisponivel: tempo de conexao esgotado (3000 ms)`. Ver a nota abaixo |
| 7 | Logs anexados sem IP completo, hostname real ou pasta de usuário | **PASS** | `mascarar_log.py` nos dois lados; conferido de novo nos arquivos anexados: só sobra `127.0.0.1` (no bench), nenhum hostname real nem nome de usuário |
| 8 | Regra de firewall removida no fim | **não registrado** | sem declaração de quem operou |

**Nota sobre o item 6.** O log do worker 7201 termina na última rodada do bench (14:30), com `RESULT ... ok` e a conexão fechada normalmente; ele não recebeu a conexão da queda (14:36). O processo já tinha sido encerrado antes: a causa mais provável é o comando que mata o worker no próximo `TASK` ter sido armado enquanto o bench ainda rodava. Na queda, o coordenador:

- tentou conectar ao 7201 e desistiu em 3 s (`tempo de conexao esgotado`: B descarta pacotes para uma porta fechada, por isso não aparece `conexao recusada` como no loopback);
- saiu com erro claro, sem travar;
- os workers 7202–7204 receberam a tarefa, viram a conexão fechar e registraram `RESULT ... ok em 3128–3188 ms (nao entregue: conexao fechada ou parada)`, sem cair.

Isso demonstra entre computadores a falha "worker indisponível" (a mesma do F1 do `RUN-05`) e que os outros workers sobrevivem a ela. Não demonstra o `WORKER_LOST` com a tarefa em andamento, que só foi provado no loopback (F2 do `RUN-05`, 15/15, e `interop_codegen.py` cenário c).

## 4. Ajustes no README apontados na reprodução

Problemas encontrados ao preparar e rodar a execução de 09/11. Todos foram corrigidos no `runtime/README.md` §7 em 09/11, mantendo a numeração 7.1–7.8 (a auditoria `INT-02` cita esses números).

| Passo | Problema encontrado | Contorno usado em 09/11 | Correção no README (09/11) |
|---|---|---|---|
| §7.2 em diante | Os comandos falham fora da raiz do repositório (`fatal: not a git repository` nos dois PCs) | `cd` para a pasta do projeto antes do 1º comando | aplicada: `cd` no bloco do §7.1 e linha na tabela do §7.8 |
| §7.5 e §7.6 | **Falso positivo no Windows PowerShell 5.1.** Com o console em UTF-8 (página 65001), o texto passado por `\|` ao `.exe` chega com BOM. O programa lê `\ufeffpar`, não reconhece `par` e roda **sequencial sem erro**: sai `TOTAL 160` e `SOMA_NOTAS` certos sem nenhum worker usado. Reproduzido no ensaio do autor em 09/11 | `$OutputEncoding = [Console]::InputEncoding = [System.Text.UTF8Encoding]::new($false)` no início de cada janela; conferir `MODO par` e `conexao ... aceita` nos logs de B | aplicada: linha no bloco do §7.1, conferência em B no §7.5, sintoma no §7.8 |
| §7.5, §7.6 e §7.7 | No PowerShell 5.1, `Tee-Object` e `>` gravam UTF-16, e o `mascarar_log.py` lê só UTF-8 | `2>&1 \| ForEach-Object { "$_" } \| Out-File -Encoding utf8 <arquivo>` (também tira o prefixo `NativeCommandError` da linha de erro) | aplicada: §7.5 e §7.6; o §7.8 avisa que um arquivo UTF-16 passa pelo `mascarar_log.py` **sem mascarar os IPs** e com exit 0 (conferido em 09/11) |
| §7.4 | Quatro terminais, um por worker; um Ctrl+C na janela errada derruba o worker | os 4 workers numa janela só, com `Start-Process -WindowStyle Hidden -RedirectStandardError`, guardando os PIDs | aplicada: §7.4 (com a variante Linux) |
| §7.6 | O Ctrl+C manual na hora certa é uma corrida entre duas máquinas | comando em B que espera um `TASK ... inicio` novo no log e encerra o worker pelo PID. **Precisa ser armado só depois do bench**; em 09/11 isso causou o item 6 PARTIAL | aplicada: §7.6, com o aviso e o sintoma no §7.8 |
| §7.4 a §7.7 | Logs espalhados em `output\` de cada máquina, difíceis de juntar | tudo em `Downloads\minipar-evidencias\RUN-06\` de cada PC; B mandou a pasta `publicar` zipada para A | aplicada: `$EVID` no §7.1 e passos de junção no §7.7 |

## 5. Anexos

Todos mascarados com `runtime/tools/mascarar_log.py` (hostnames → `pc-A`/`pc-B`, 3º octeto → `x`).

- [`RUN-06/coordenador_A.txt`](RUN-06/coordenador_A.txt): `par` com os 4 workers de B
- [`RUN-06/coordenador_A_seq.txt`](RUN-06/coordenador_A_seq.txt): `seq` em A, para comparar a `SOMA_NOTAS`
- [`RUN-06/coordenador_A_queda.txt`](RUN-06/coordenador_A_queda.txt): queda (item 6, PARTIAL)
- [`RUN-06/worker_7201_B.log`](RUN-06/worker_7201_B.log) … [`worker_7204_B.log`](RUN-06/worker_7204_B.log): os 4 workers de B (os `.log` estão no `.gitignore` e foram adicionados com `git add -f`)
- [`RUN-05/rede_20261109-142925.json`](RUN-05/rede_20261109-142925.json) e [`.md`](RUN-05/rede_20261109-142925.md): bench `par_rede` da mesma sessão

## 6. Comandos usados em 09/11

Roteiro passado à parte, **não** o README da época. Foi a base do novo §7 do `runtime/README.md`, que é a versão a seguir daqui em diante. PowerShell 5.1 ou 7, na raiz do repositório.

Nas duas máquinas, em toda janela nova:

```powershell
$IP_A = "<IP-de-A>"; $IP_B = "<IP-de-B>"
$env:PATH = "C:\msys64\ucrt64\bin;$env:PATH"
$OutputEncoding = [Console]::InputEncoding = [System.Text.UTF8Encoding]::new($false)
$EVID = Join-Path (New-Object -ComObject Shell.Application).NameSpace('shell:Downloads').Self.Path 'minipar-evidencias\RUN-06'
New-Item -ItemType Directory -Force $EVID | Out-Null
$DEST = 7201..7204 | ForEach-Object { "${IP_B}:$_" }
python main.py tests/2026_2/test08/teste8_avaliadores.minipar teste8
```

B (firewall como no §7.3), depois os workers:

```powershell
$W = foreach ($p in 7201..7204) {
  Start-Process output\teste8.exe -ArgumentList "--minipar-worker $p --bind $IP_B" `
    -RedirectStandardError "$EVID\worker_${p}_B.log" -WindowStyle Hidden -PassThru }
```

A:

```powershell
"seq`n2000000`nlocal`nlocal`nlocal`nlocal" | output\teste8.exe 2>&1 | ForEach-Object { "$_" } | Out-File -Encoding utf8 "$EVID\coordenador_A_seq.txt"
(@("par", "2000000") + $DEST) -join "`n" | output\teste8.exe 2>&1 | ForEach-Object { "$_" } | Out-File -Encoding utf8 "$EVID\coordenador_A.txt"
python tests/2026_2/bench/run_bench.py --carga 5000000 --reps 7 --reps-falhas 5 --destinos-rede ($DEST -join ",")
```

Queda: em B, só depois do bench terminar,

```powershell
$log = "$EVID\worker_7201_B.log"; $n = (Select-String $log -Pattern "inicio").Count
while ((Select-String $log -Pattern "inicio").Count -eq $n) { Start-Sleep -Milliseconds 200 }
Stop-Process -Id $W[0].Id
```

e em A:

```powershell
(@("par", "20000000") + $DEST) -join "`n" | output\teste8.exe 2>&1 | ForEach-Object { "$_" } | Out-File -Encoding utf8 "$EVID\coordenador_A_queda.txt"
```

Fim, em cada máquina (em B, apelido `pc-B`; em A, `pc-A` e mais `--host <hostname-de-B>=pc-B`):

```powershell
Get-ChildItem $EVID -File | ForEach-Object {
  python runtime/tools/mascarar_log.py $_.FullName "$EVID\publicar\$($_.Name)" --host "$env:COMPUTERNAME=pc-A" }
```

O ensaio desses comandos no loopback (09/11, Windows PowerShell 5.1 e PowerShell 7) deu `par` igual ao `seq`, `par_rede` PASS e a queda com `WORKER_LOST` e exit 1, com o vigia armado depois do bench.
