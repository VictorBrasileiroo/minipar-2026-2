"""T09-01: harness do Teste 9 (160 avaliacoes + Mandelbrot ASCII).

Executar da raiz do repositorio:
    python tests/2026_2/test09/run_t09.py [--carga N] [--port-base 7300] [--no-remote]

Compila tests/2026_2/test09/teste9_mandelbrot.minipar pela CLI (main.py), roda os
cenarios seq, par local e par remoto (5 workers no loopback) e confere a saida
contra um oraculo Python independente (formula fechada do LCG e Mandelbrot
recalculado). Resultado em output/test09/results.json.

Saida: exit 0 somente se todas as verificacoes derem PASS; 1 se alguma FAIL;
2 se BLOCKED (backend Fork/Join CORE-07 ausente ou portas indisponiveis).
"""
from __future__ import annotations

import argparse
import json
import os
import platform
import re
import socket
import subprocess
import sys
import threading
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SOURCE = Path("tests/2026_2/test09/teste9_mandelbrot.minipar")
EXE_NAME = "teste9"
EXE = ROOT / "output" / f"{EXE_NAME}.exe"
OUT_DIR = ROOT / "output" / "test09"
PORT_MIN, PORT_MAX = 7300, 7319          # unica faixa de portas permitida a este teste
RUN_TIMEOUT = 300                        # s por execucao do programa
NOMES = ["Professor", "Monitor 1", "Monitor 2", "Monitor 3"]
CARACTERES = " .:-=+#%@"
PARAMS_REF = (50, 20, 100)               # parametros da referencia Python
PARAMS_ALT = (30, 12, 60)                # segundo conjunto: prova que a saida nao e fixa

CHECKS: list[dict] = []


def check(nome: str, ok: bool, detalhe: str = "") -> bool:
    CHECKS.append({"check": nome, "status": "PASS" if ok else "FAIL", "detalhe": detalhe})
    print(f"[{'PASS' if ok else 'FAIL'}] {nome}" + (f" -- {detalhe}" if detalhe else ""))
    return ok


# ---------------------------------------------------------------- oraculo
A, C, M = 75, 74, 65537                  # LCG s' = (75 s + 74) mod 65537 (m primo)


def lcg(s: int) -> int:
    return (s * A + C) % M


def lcg_salto(s0: int, n: int) -> int:
    """s_n = a^n s0 + c (a^n - 1)/(a - 1) mod m, sem iterar."""
    an = pow(A, n, M)
    return (an * s0 + C * (an - 1) * pow(A - 1, -1, M)) % M


def nota_fechada(i: int, carga: int) -> int:
    s0 = lcg(i + 1)
    return lcg_salto(s0, carga + s0 % carga) % 101


def nota_ingenua(i: int, carga: int) -> int:
    s = lcg(i + 1)
    passos = carga + s % carga
    for _ in range(passos):
        s = lcg(s)
    return s % 101


def indice_inteiro(it: int, max_iter: int) -> int:
    return (it * 8 - (it * 8) % max_iter) // max_iter


def indice_referencia(it: int, max_iter: int) -> int:
    return int((it / max_iter) * (len(CARACTERES) - 1))


def mandelbrot_oraculo(largura: int, altura: int, max_iter: int, indice=indice_inteiro) -> list[str]:
    linhas = []
    for y in range(altura):
        cy = (y / altura) * 2.4 - 1.2
        linha = []
        for x in range(largura):
            cx = (x / largura) * 3.0 - 2.0
            zx, zy, it = 0.0, 0.0, 0
            while zx * zx + zy * zy <= 4.0 and it < max_iter:
                tmp = zx * zx - zy * zy + cx
                zy = 2.0 * zx * zy + cy
                zx = tmp
                it += 1
            linha.append(CARACTERES[indice(it, max_iter)])
        linhas.append("".join(linha))
    return linhas


# ---------------------------------------------------------------- execucao
def compilar() -> tuple[bool, str]:
    codegen = (ROOT / "src" / "codegen.py").read_text(encoding="utf-8", errors="replace")
    if "minipar_rt::start" not in codegen or not (ROOT / "runtime" / "include" / "minipar_rt").is_dir():
        return False, "BLOCKED"
    proc = subprocess.run([sys.executable, "main.py", str(SOURCE), EXE_NAME], cwd=ROOT,
                          capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=600)
    log = proc.stdout + proc.stderr
    (OUT_DIR / "compile.log").write_text(log, encoding="utf-8")
    if EXE.exists() and "[SUCESSO]" in proc.stdout:
        return True, log
    if "CORE-07" in log or "NotImplemented" in log or "pendente" in log:
        return False, "BLOCKED"
    return False, log


def entrada(modo: str, carga: int, params: tuple[int, int, int], destinos: list[str]) -> bytes:
    linhas = [modo, str(carga), *map(str, params), *destinos]
    return ("\n".join(linhas) + "\n").encode("ascii")   # bytes: sem CRLF do modo texto


def executar(nome: str, modo: str, carga: int, params, destinos) -> dict:
    stdin = entrada(modo, carga, params, destinos)
    t0 = time.perf_counter()
    try:
        proc = subprocess.run([str(EXE)], input=stdin, capture_output=True, timeout=RUN_TIMEOUT, cwd=ROOT)
        rc, out, err = proc.returncode, proc.stdout.decode("utf-8", "replace"), proc.stderr.decode("utf-8", "replace")
    except subprocess.TimeoutExpired as exc:
        rc, out, err = "TIMEOUT", (exc.stdout or b"").decode("utf-8", "replace"), (exc.stderr or b"").decode("utf-8", "replace")
    dt = time.perf_counter() - t0
    out = out.replace("\r\n", "\n")
    (OUT_DIR / f"{nome}.stdout.txt").write_text(out, encoding="utf-8")
    (OUT_DIR / f"{nome}.stderr.txt").write_text(err, encoding="utf-8")
    print(f"--- {nome}: exit={rc} tempo={dt:.3f}s")
    return {"cenario": nome, "modo": modo, "carga": carga, "params": list(params), "destinos": destinos,
            "exit": rc, "tempo_s": round(dt, 4), "stdout": out, "stderr": err}


def analisar(run: dict) -> dict | None:
    """Faz o parse estrito do contrato de saida; devolve campos ou None."""
    linhas = run["stdout"].split("\n")
    if linhas and linhas[-1] == "":
        linhas.pop()
    largura, altura, max_iter = run["params"]
    if len(linhas) < 13 + altura:        # 12 linhas fixas + altura linhas + rodape
        return None
    r = {"cabecalho": linhas[0], "modo": linhas[1], "avaliadores": [], "contadores": {}}
    for k in range(4):
        m = re.fullmatch(r"AVALIADOR (\d+) (.+) (\d+)", linhas[2 + k])
        if not m:
            return None
        r["avaliadores"].append((int(m.group(1)), m.group(2), int(m.group(3))))
    for j, chave in enumerate(["TOTAL", "UNICOS", "DUPLICADOS", "PERDIDOS", "SOMA_NOTAS"]):
        m = re.fullmatch(chave + r" (-?\d+)", linhas[6 + j])
        if not m:
            return None
        r["contadores"][chave] = int(m.group(1))
    r["cab_mandel"] = linhas[11]
    r["fractal"] = linhas[12:12 + altura]
    r["fim"] = linhas[12 + altura]
    r["sobra"] = linhas[13 + altura:]
    return r


def primeira_diferenca(obtido: list[str], esperado: list[str]) -> str:
    for y, (a, b) in enumerate(zip(obtido, esperado)):
        if a != b:
            for x in range(max(len(a), len(b))):
                ca = a[x] if x < len(a) else "<fim>"
                cb = b[x] if x < len(b) else "<fim>"
                if ca != cb:
                    return f"linha {y} coluna {x}: obtido {ca!r}, esperado {cb!r}"
    if len(obtido) != len(esperado):
        return f"quantidade de linhas {len(obtido)} != {len(esperado)}"
    return ""


def verificar_cenario(run: dict, soma_esperada: int) -> dict | None:
    n = run["cenario"]
    largura, altura, max_iter = run["params"]
    if not check(f"{n}: exit 0 e stderr vazio", run["exit"] == 0 and run["stderr"] == "",
                 f"exit={run['exit']} stderr={run['stderr'][:200]!r}"):
        return None
    r = analisar(run)
    if not check(f"{n}: formato da saida (contrato de linhas)", r is not None,
                 "" if r else f"saida: {run['stdout'][:400]!r}"):
        return None
    check(f"{n}: cabecalho e MODO",
          r["cabecalho"] == "=== TESTE 9: 160 avaliacoes + Mandelbrot ===" and r["modo"] == f"MODO {run['modo']}",
          f"{r['cabecalho']!r} / {r['modo']!r}")
    esperado_av = [(k, NOMES[k], 40) for k in range(4)]
    check(f"{n}: 4 avaliadores com 40 atividades cada", r["avaliadores"] == esperado_av, str(r["avaliadores"]))
    c = r["contadores"]
    check(f"{n}: TOTAL 160 / UNICOS 160 / DUPLICADOS 0 / PERDIDOS 0",
          (c["TOTAL"], c["UNICOS"], c["DUPLICADOS"], c["PERDIDOS"]) == (160, 160, 0, 0), str(c))
    check(f"{n}: SOMA_NOTAS = oraculo (formula fechada)", c["SOMA_NOTAS"] == soma_esperada,
          f"obtido {c['SOMA_NOTAS']}, oraculo {soma_esperada}")
    check(f"{n}: cabecalho/rodape do Mandelbrot e nada sobrando",
          r["cab_mandel"] == f"=== MANDELBROT {largura}x{altura} max_iter={max_iter} ==="
          and r["fim"] == "=== FIM MANDELBROT ===" and r["sobra"] == [],
          f"{r['cab_mandel']!r} / {r['fim']!r} / sobra={r['sobra']!r}")
    esperado = mandelbrot_oraculo(largura, altura, max_iter)
    diff = primeira_diferenca(r["fractal"], esperado)
    check(f"{n}: fractal {largura}x{altura}x{max_iter} = oraculo Python, caractere a caractere",
          diff == "", diff or f"{altura} linhas x {largura} colunas identicas")
    return r


# ---------------------------------------------------------------- workers
class Worker:
    def __init__(self, porta: int):
        self.porta = porta
        self.linhas: list[tuple[float, str]] = []
        self.proc = subprocess.Popen([str(EXE), "--minipar-worker", str(porta), "--bind", "127.0.0.1"],
                                     cwd=ROOT, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                                     stderr=subprocess.PIPE)
        self.leitor = threading.Thread(target=self._ler, daemon=True)
        self.leitor.start()

    def _ler(self):
        for raw in self.proc.stderr:
            self.linhas.append((time.monotonic(), raw.decode("utf-8", "replace").rstrip("\r\n")))

    def espera(self, padrao: str, limite: float) -> bool:
        fim = time.monotonic() + limite
        while time.monotonic() < fim:
            if any(re.search(padrao, l) for _, l in list(self.linhas)):
                return True
            if self.proc.poll() is not None:
                time.sleep(0.2)
                return any(re.search(padrao, l) for _, l in list(self.linhas))
            time.sleep(0.05)
        return False

    def encerrar(self):
        if self.proc.poll() is None:
            self.proc.kill()                  # somente o PID deste processo
        try:
            self.proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            pass
        self.leitor.join(timeout=5)


def porta_livre(porta: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind(("127.0.0.1", porta))
            return True
        except OSError:
            return False


LOG_RE = re.compile(r"^\[minipar_worker (\S+):(\d+)\] (TASK|RESULT) (\S+) fn=(\S+) (.*)$")


def cenario_remoto(carga: int, params, port_base: int, soma: int) -> dict:
    portas = [port_base + i for i in range(1, 6)]
    if not all(PORT_MIN <= p <= PORT_MAX for p in portas):
        check("remoto: portas na faixa 7300-7319", False, str(portas))
        return {}
    ocupadas = [p for p in portas if not porta_livre(p)]
    if ocupadas:
        CHECKS.append({"check": "remoto: portas livres", "status": "BLOCKED", "detalhe": f"ocupadas: {ocupadas}"})
        print(f"[BLOCKED] remoto: portas ocupadas {ocupadas}")
        return {}
    workers = [Worker(p) for p in portas]
    try:
        prontos = [w.espera(r"escutando em", 15) for w in workers]
        if not check("remoto: 5 workers escutando em 127.0.0.1", all(prontos), str(prontos)):
            return {}
        destinos = [f"127.0.0.1:{p}" for p in portas]
        run = executar("par_remoto_" + "x".join(map(str, params)), "par", carga, params, destinos)
        r = verificar_cenario(run, soma)
        for w in workers:
            w.espera(r"RESULT", 10)
    finally:
        for w in workers:
            w.encerrar()
    eventos = []
    for w in workers:
        for ts, linha in w.linhas:
            m = LOG_RE.match(linha)
            if m:
                eventos.append({"porta": w.porta, "t": ts, "host": m.group(1), "pid": int(m.group(2)),
                                "tipo": m.group(3), "task": m.group(4), "fn": m.group(5), "resto": m.group(6)})
    logs = {w.porta: [f"{ts:.4f} {l}" for ts, l in w.linhas] for w in workers}
    (OUT_DIR / "workers.log").write_text(
        "\n".join(f"--- porta {p}\n" + "\n".join(ls) for p, ls in logs.items()) + "\n", encoding="utf-8")

    por_porta = {p: [e for e in eventos if e["porta"] == p] for p in portas}
    pids = {e["pid"] for e in eventos}
    um_por_worker = all(sum(e["tipo"] == "TASK" for e in ev) == 1 and sum(e["tipo"] == "RESULT" for e in ev) == 1
                        for ev in por_porta.values())
    check("remoto: 5 PIDs de worker distintos", len(pids) == 5 and len({w.proc.pid for w in workers}) == 5,
          f"pids={sorted(pids)}")
    check("remoto: cada worker com exatamente 1 TASK e 1 RESULT", um_por_worker,
          str({p: [(e['tipo'], e['fn']) for e in ev] for p, ev in por_porta.items()}))
    fns = sorted(e["fn"] for e in eventos if e["tipo"] == "TASK")
    check("remoto: 4 avaliar_lote + 1 mandelbrot", fns == ["avaliar_lote"] * 4 + ["mandelbrot"], str(fns))
    resultados_ok = all(e["resto"].startswith("ok ") for e in eventos if e["tipo"] == "RESULT")
    check("remoto: todos os RESULT com status ok", resultados_ok)
    tasks = [e["t"] for e in eventos if e["tipo"] == "TASK"]
    res_av = [e["t"] for e in eventos if e["tipo"] == "RESULT" and e["fn"] == "avaliar_lote"]
    concorrente = len(tasks) == 5 and res_av and max(tasks) < min(res_av)
    check("remoto: concorrencia -- os 5 TASK chegam antes do primeiro RESULT de avaliar_lote",
          bool(concorrente),
          f"ultimo TASK +{(max(tasks) - min(tasks)) * 1000:.1f} ms; primeiro RESULT avaliar_lote "
          f"+{(min(res_av) - min(tasks)) * 1000:.1f} ms (relativo ao primeiro TASK)" if tasks and res_av else "sem eventos")
    duracoes = {f"{e['porta']}:{e['fn']}": e["resto"] for e in eventos if e["tipo"] == "RESULT"}
    return {"run": run, "resumo": r and r["contadores"], "eventos": [
        {k: (round(v - min(tasks), 4) if k == "t" and tasks else v) for k, v in e.items()} for e in eventos],
        "duracoes_worker": duracoes}


# ---------------------------------------------------------------- main
def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--carga", type=int, default=2000000, help="passos minimos do LCG por atividade (padrao 2000000)")
    ap.add_argument("--port-base", type=int, default=7300, help="workers em port-base+1..+5 (faixa 7300-7319)")
    ap.add_argument("--no-remote", action="store_true", help="pula o cenario com 5 workers no loopback")
    args = ap.parse_args()
    if args.carga < 1 or args.carga > 2147483647 // 2:
        print("carga deve estar entre 1 e 1073741823 (int do backend)")
        return 1
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    # 0) auto-checagem do oraculo: formula fechada == laco ingenuo
    ok_oraculo = all(nota_fechada(i, c) == nota_ingenua(i, c) for c in (1, 2, 3, 7, 50, 333) for i in range(160))
    check("oraculo: formula fechada do LCG == laco ingenuo (cargas 1,2,3,7,50,333)", ok_oraculo)
    soma = sum(nota_fechada(i, args.carga) for i in range(160))
    for params in (PARAMS_REF, PARAMS_ALT):
        m = params[2]
        iguais = all(indice_inteiro(it, m) == indice_referencia(it, m) for it in range(m + 1))
        check(f"oraculo: indice inteiro == int((it/{m})*8) da referencia para it=0..{m}", iguais)
        igual_ref = mandelbrot_oraculo(*params) == mandelbrot_oraculo(*params, indice=indice_referencia)
        check(f"oraculo: fractal {'x'.join(map(str, params))} com indice inteiro == com formula da referencia",
              igual_ref)
    check("oraculo: os dois conjuntos de parametros geram fractais diferentes",
          mandelbrot_oraculo(*PARAMS_REF) != mandelbrot_oraculo(*PARAMS_ALT))

    try:
        ok, log = compilar()
    except subprocess.TimeoutExpired:
        ok, log = False, "timeout na compilacao"
    if not ok:
        if log == "BLOCKED":
            print("BLOCKED: backend CORE-07 ausente")
            salvar(args, [], None, "BLOCKED")
            return 2
        check("compilacao via CLI (main.py)", False, log[-800:])
        salvar(args, [], None, "FAIL")
        return 1
    check("compilacao via CLI (main.py)", True, str(EXE.relative_to(ROOT)))

    locais = "local local local local local".split()
    runs, resumos = [], {}
    for nome, modo, params in [("seq_50x20x100", "seq", PARAMS_REF), ("par_local_50x20x100", "par", PARAMS_REF),
                               ("seq_30x12x60", "seq", PARAMS_ALT), ("par_local_30x12x60", "par", PARAMS_ALT)]:
        run = executar(nome, modo, args.carga, params, locais)
        r = verificar_cenario(run, soma)
        runs.append(run)
        if r:
            resumos[nome] = (r["avaliadores"], r["contadores"])
    remoto = None
    if not args.no_remote:
        remoto = cenario_remoto(args.carga, PARAMS_REF, args.port_base, soma)
        if remoto.get("run"):
            runs.append(remoto["run"])
            if remoto.get("resumo"):
                resumos[remoto["run"]["cenario"]] = (None, remoto["resumo"])
    agregados = {n: c for n, (_, c) in resumos.items()}
    check("mesmo agregado (contadores e SOMA_NOTAS) em todos os cenarios",
          len(agregados) == len(runs) and len({json.dumps(c, sort_keys=True) for c in agregados.values()}) == 1,
          json.dumps(agregados))
    estado = "PASS" if all(c["status"] == "PASS" for c in CHECKS) else (
        "BLOCKED" if any(c["status"] == "BLOCKED" for c in CHECKS) else "FAIL")
    salvar(args, runs, remoto, estado, soma)
    print("\nTempos (informativos; maquina compartilhada, medicao ruidosa):")
    for run in runs:
        print(f"  {run['cenario']:<26} exit={run['exit']} {run['tempo_s']:.3f} s")
    print(f"\nRESULTADO T09: {estado}  ({sum(c['status'] == 'PASS' for c in CHECKS)}/{len(CHECKS)} PASS)")
    return {"PASS": 0, "BLOCKED": 2}.get(estado, 1)


def salvar(args, runs, remoto, estado, soma=None):
    dados = {
        "card": "T09-01", "estado": estado, "carga": args.carga, "soma_notas_oraculo": soma,
        "ambiente": {"python": sys.version.split()[0], "plataforma": platform.platform(),
                     "processador": platform.processor(), "cpus_logicas": os.cpu_count()},
        "checks": CHECKS,
        "cenarios": [{k: v for k, v in r.items() if k != "stdout"} | {"stdout_linhas": r["stdout"].split("\n")[:13]}
                     for r in runs],
        "remoto": remoto and {k: v for k, v in remoto.items() if k != "run"},
    }
    (OUT_DIR / "results.json").write_text(json.dumps(dados, indent=2, ensure_ascii=False), encoding="utf-8")


if __name__ == "__main__":
    sys.exit(main())
