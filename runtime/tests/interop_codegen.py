"""RUN-04 — interop real MiniPar -> C++ gerado (CORE-07) -> runtime minipar_rt, pela CLI oficial.

Uso (da raiz do repositório):
    python runtime/tests/interop_codegen.py [--port-base 7100] [--seed N]

Compila `runtime/tests/fixtures/run04_interop.minipar` com `python main.py <fonte> <nome>` e executa o
binário gerado em três cenários:
  (a) destino "local";
  (b) worker no loopback: o MESMO executável com `--minipar-worker <porta> --bind 127.0.0.1`, destino
      `127.0.0.1:<porta>` lido do stdin; o log do worker tem de mostrar TASK/RESULT de cada função com o
      PID do processo worker;
  (c) worker encerrado (kill pelo PID) antes do join -> o join tem de falhar com WORKER_LOST, exit 1, sem
      travar (limite de tempo).
Os valores esperados são calculados aqui em Python a partir de entradas sorteadas (semente impressa);
nenhuma saída é copiada de uma execução anterior.

Antes, sonda a capacidade: se a CLI não compila um programa mínimo com fork (backend sem CORE-07),
imprime `BLOCKED: backend CORE-07 ausente` e sai com 2. Nunca vira PASS.
Exit: 0 = todos PASS; 1 = algum FAIL; 2 = BLOCKED.
Portas: só [port-base, port-base + 9] (padrão 7100–7109). Processos criados aqui são encerrados pelo PID.
Isto é loopback: prova a integração e o protocolo, NÃO prova execução em dois computadores (RUN-03).
"""
from __future__ import annotations

import argparse
import os
import random
import re
import shutil
import socket
import string
import subprocess
import sys
import time
from pathlib import Path

RUNTIME = Path(__file__).resolve().parent.parent
REPO = RUNTIME.parent
FIXTURE = RUNTIME / "tests" / "fixtures" / "run04_interop.minipar"
WORK = REPO / "output" / "run04-interop"
PROBE_NAME = "run04_probe"
PROG_NAME = "run04_interop"
DEFAULT_GPP = Path(r"C:\msys64\ucrt64\bin\g++.exe")
FUNCOES = ("soma_quadrados", "escala", "eco", "eh_par", "traco", "marca")
PROBE_SRC = "func mais_um(x) { return x + 1; }\nvar h = fork mais_um(41);\nprint(join(h));\n"


class Blocked(Exception):
    pass


def make_env() -> dict:
    env = dict(os.environ)
    if not env.get("CXX") and not shutil.which("g++") and DEFAULT_GPP.is_file():
        env["CXX"] = str(DEFAULT_GPP)
    cxx = env.get("CXX") or shutil.which("g++") or ""
    parent = Path(cxx).parent if cxx else None
    if parent and parent.is_dir():  # DLLs do compilador só no PATH deste processo e dos filhos
        env["PATH"] = str(parent) + os.pathsep + env.get("PATH", "")
    env["PYTHONIOENCODING"] = "utf-8"
    return env


def cli_compile(src: Path, name: str, env: dict) -> tuple[int, str, Path]:
    exe = REPO / "output" / f"{name}.exe"
    p = subprocess.run([sys.executable, "-B", "main.py", str(src), name], cwd=REPO, capture_output=True, text=True,
                       encoding="utf-8", errors="replace", env=env, stdin=subprocess.DEVNULL, timeout=300)
    return p.returncode, p.stdout + p.stderr, exe


def probe_backend(env: dict, log: list[str]) -> Path:
    """Programa mínimo com fork. Sem CORE-07 -> Blocked; com CORE-07 e resultado errado -> AssertionError."""
    WORK.mkdir(parents=True, exist_ok=True)
    src = WORK / "probe.minipar"
    src.write_text(PROBE_SRC, encoding="utf-8")
    rc, out, exe = cli_compile(src, PROBE_NAME, env)
    cpp = REPO / "output" / f"{PROBE_NAME}.cpp"
    log.append(f"sonda: python main.py {src.relative_to(REPO)} {PROBE_NAME} -> exit={rc}")
    if rc != 0 or not exe.is_file():
        tail = "\n".join(out.strip().splitlines()[-6:])
        if "Compilador C++ nao encontrado" in out:
            raise Blocked(f"g++ ausente para a CLI\n{tail}")
        raise Blocked(f"backend CORE-07 ausente (a CLI nao compila fork)\n{tail}")
    text = cpp.read_text(encoding="utf-8", errors="replace") if cpp.is_file() else ""
    if "minipar_rt::register_function" not in text or "minipar_rt::worker_main_if_requested" not in text:
        raise Blocked("backend CORE-07 ausente (C++ gerado nao usa minipar_rt)")
    p = subprocess.run([str(exe)], input="", capture_output=True, text=True, encoding="utf-8", errors="replace",
                       env=env, timeout=30)
    log.append(f"sonda: {exe.name} -> exit={p.returncode} stdout={p.stdout.strip()!r} stderr={p.stderr.strip()!r}")
    assert p.returncode == 0 and p.stdout.strip() == str(41 + 1), "sonda local nao devolveu 41 + 1"
    return exe


# ---- oráculo independente (mesma semântica do fixture, escrita em Python) -----------------------

def fmt_num(x: float) -> str:
    # print do MiniPar em C++ = ostream padrão = %g com 6 dígitos significativos
    return format(float(x), "g")


def fmt_list(xs) -> str:
    return "[" + ", ".join(fmt_list(x) if isinstance(x, list) else (fmt_num(x) if isinstance(x, float) else str(x))
                           for x in xs) + "]"


def gerar_entrada(rng: random.Random) -> tuple[list[float], str]:
    n0 = rng.randint(200, 1500)  # soma de i^2 com i < n0 cabe em int (C++ do backend)
    resto = [rng.randint(-99999, 99999) for _ in range(rng.randint(2, 6))]  # *3 < 1e6: %g exato
    texto = "".join(rng.choice(string.ascii_letters + string.digits) for _ in range(rng.randint(3, 17)))
    return [float(n0)] + [float(v) for v in resto], texto


def esperado(nums: list[float], texto: str) -> list[str]:
    n0 = int(nums[0])
    sq = sum(i * i for i in range(n0))
    escala = [v * 3 for v in nums]
    eco = texto + "|" + texto[:1]
    par = "sim" if len(texto) % 2 == 0 else "nao"
    k = len(texto) % 5 + 2
    m = [[2] * k for _ in range(k)]
    traco = sum(m[i][i] for i in range(k))
    marcada = [row[:] for row in m]
    marcada[0][1] = 7
    return [f"SQ {sq}", f"ESCALA {fmt_list(escala)}", f"ECO {eco}", f"PAR {par}", f"TRACO {traco}",
            f"MARCA {fmt_list(marcada)} {fmt_list(m)}"]


def stdin_normal(destino: str, nums: list[float], texto: str) -> str:
    return f"{destino}\nnormal\n{' '.join(str(int(v)) for v in nums)}\n{texto}\n"


# ---- portas e worker ----------------------------------------------------------------------------

def porta_livre(base: int, usadas: set[int]) -> int:
    for port in range(base, base + 10):
        if port in usadas:
            continue
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            s.bind(("127.0.0.1", port))
        except OSError:
            continue
        finally:
            s.close()
        usadas.add(port)
        return port
    raise RuntimeError(f"nenhuma porta livre em {base}..{base + 9}")


def subir_worker(exe: Path, port: int, log: Path, env: dict) -> tuple[subprocess.Popen, str]:
    fh = open(log, "w", encoding="utf-8")
    proc = subprocess.Popen([str(exe), "--minipar-worker", str(port), "--bind", "127.0.0.1"],
                            stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=fh, env=env)
    fh.close()
    deadline = time.time() + 15
    while time.time() < deadline:
        txt = log.read_text(encoding="utf-8", errors="replace")
        m = re.search(r"\[minipar_worker (\S+)\] escutando em 127\.0\.0\.1:(\d+) \(host=(\S+) pid=(\d+)", txt)
        if m:
            return proc, m.group(1)
        if proc.poll() is not None:
            break
        time.sleep(0.05)
    encerrar(proc)
    raise RuntimeError(f"worker na porta {port} nao ficou pronto; log:\n{log.read_text(errors='replace')}")


def encerrar(proc: subprocess.Popen | None) -> None:
    if proc is not None and proc.poll() is None:
        proc.kill()  # só o processo criado por este script, pelo handle/PID
        try:
            proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            pass


# ---- cenários -----------------------------------------------------------------------------------

def rodar(exe: Path, entrada: str, env: dict, timeout: int = 60) -> subprocess.CompletedProcess:
    return subprocess.run([str(exe)], input=entrada, capture_output=True, text=True, encoding="utf-8",
                          errors="replace", env=env, timeout=timeout)


def cenario_local(exe: Path, env: dict, rng: random.Random) -> tuple[bool, str]:
    nums, texto = gerar_entrada(rng)
    p = rodar(exe, stdin_normal("local", nums, texto), env)
    exp = esperado(nums, texto)
    got = p.stdout.splitlines()
    ok = p.returncode == 0 and got == exp and p.stderr == ""
    return ok, (f"entrada: nums={[int(v) for v in nums]} texto={texto!r}\nexit={p.returncode} stderr={p.stderr.strip()!r}\n"
                + comparar(exp, got))


def cenario_loopback(exe: Path, env: dict, rng: random.Random, port: int) -> tuple[bool, str]:
    log = WORK / "worker_loopback.log"
    worker, worker_id = subir_worker(exe, port, log, env)
    try:
        nums, texto = gerar_entrada(rng)
        t0 = time.perf_counter()
        p = rodar(exe, stdin_normal(f"127.0.0.1:{port}", nums, texto), env)
        dur = time.perf_counter() - t0
        time.sleep(0.3)  # deixa o worker gravar a última linha RESULT
        vivo = worker.poll() is None
    finally:
        encerrar(worker)
    txt = log.read_text(encoding="utf-8", errors="replace")
    exp = esperado(nums, texto)
    got = p.stdout.splitlines()
    pid = worker.pid
    prefixo = re.escape(f"[minipar_worker {worker_id}]")
    tasks = re.findall(prefixo + r" TASK (task-\d+) fn=(\w+) de 127\.0\.0\.1:\d+: inicio", txt)
    results = re.findall(prefixo + r" RESULT (task-\d+) fn=(\w+) ok em \d+ ms", txt)
    checks = {
        "saida igual ao oraculo": p.returncode == 0 and got == exp and p.stderr == "",
        f"worker_id termina com o PID do processo worker ({pid})": worker_id.endswith(f":{pid}"),
        "worker nao e o coordenador": worker_id.endswith(f":{pid}") and pid != os.getpid(),
        "uma linha TASK por funcao do fork": sorted(f for _, f in tasks) == sorted(FUNCOES),
        "uma linha RESULT ok por TASK": sorted(results) == sorted(tasks),
        "worker continua vivo apos o programa": vivo,
    }
    rel = (f"worker {worker_id} (pid {pid}) em 127.0.0.1:{port}; coordenador terminou em {dur:.2f} s\n"
           f"entrada: nums={[int(v) for v in nums]} texto={texto!r}\nexit={p.returncode} stderr={p.stderr.strip()!r}\n"
           + comparar(exp, got) + "\n" + "\n".join(f"  [{'ok' if v else 'X'}] {k}" for k, v in checks.items())
           + "\nlog do worker:\n" + "\n".join("  " + ln for ln in txt.splitlines()[:16]))
    return all(checks.values()), rel


def cenario_queda(exe: Path, env: dict, port: int) -> tuple[bool, str]:
    """fork lento -> espera o TASK no log do worker -> mata o worker -> libera o join."""
    log = WORK / "worker_queda.log"
    worker, worker_id = subir_worker(exe, port, log, env)
    coord = None
    try:
        coord = subprocess.Popen([str(exe)], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                 text=True, encoding="utf-8", errors="replace", env=env)
        assert coord.stdin is not None
        coord.stdin.write(f"127.0.0.1:{port}\nlento\n")
        coord.stdin.flush()
        deadline = time.time() + 15
        task = None
        while time.time() < deadline and task is None:
            m = re.search(r"TASK (task-\d+) fn=lento de 127\.0\.0\.1:\d+: inicio", log.read_text(errors="replace"))
            task = m.group(1) if m else None
            if task is None:
                time.sleep(0.05)
        if task is None:
            raise RuntimeError("o worker nao recebeu o TASK de lento em 15 s")
        time.sleep(0.2)
        encerrar(worker)  # queda do worker antes do join
        w_exit = worker.returncode
        t0 = time.perf_counter()
        try:
            out, err = coord.communicate("\n", timeout=30)  # libera o join
            rc = coord.returncode
        except subprocess.TimeoutExpired:
            encerrar(coord)
            out, err = coord.communicate()
            rc = None
        dur = time.perf_counter() - t0
    finally:
        encerrar(worker)
        encerrar(coord)
    txt = log.read_text(encoding="utf-8", errors="replace")
    msg = f"[minipar_rt] join {task} falhou: WORKER_LOST: "
    checks = {
        "coordenador terminou (sem travar) em menos de 15 s": rc is not None and dur < 15,
        "exit 1": rc == 1,
        f"stderr contem '{msg.strip()}'": msg in err,
        "nenhum resultado impresso": out.strip() == "",
        "worker nao chegou a responder (sem RESULT de lento)": "RESULT " + task not in txt,
    }
    rel = (f"worker {worker_id} (pid {worker.pid}) em 127.0.0.1:{port} encerrado pelo PID depois de '{task} inicio' "
           f"(exit do worker={w_exit}); join liberado e concluido em {dur:.2f} s\n"
           f"exit={rc} stdout={out.strip()!r}\nstderr={err.strip()!r}\n"
           + "\n".join(f"  [{'ok' if v else 'X'}] {k}" for k, v in checks.items()))
    return all(checks.values()), rel


def comparar(exp: list[str], got: list[str]) -> str:
    linhas = []
    for i in range(max(len(exp), len(got))):
        e = exp[i] if i < len(exp) else "<nada>"
        g = got[i] if i < len(got) else "<nada>"
        linhas.append(f"  {'=' if e == g else 'X'} esperado: {e}" + ("" if e == g else f"\n    obtido:   {g}"))
    return "\n".join(linhas)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--port-base", type=int, default=7100, help="usa só portas de port-base a port-base+9")
    ap.add_argument("--seed", type=int, default=None, help="semente das entradas (padrão: aleatória, impressa)")
    args = ap.parse_args()
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    seed = args.seed if args.seed is not None else random.SystemRandom().randrange(1, 2**31)
    rng = random.Random(seed)
    env = make_env()
    print(f"# RUN-04 interop CLI (MiniPar -> C++ -> runtime) — semente {seed}, portas {args.port_base}..{args.port_base + 9}")

    log: list[str] = []
    try:
        probe_backend(env, log)
    except Blocked as exc:
        print("\n".join(log))
        print(f"BLOCKED: {exc}")
        print("# Resumo\n- BLOCKED: (a) local\n- BLOCKED: (b) worker no loopback\n- BLOCKED: (c) queda do worker")
        return 2
    except (AssertionError, subprocess.TimeoutExpired) as exc:
        print("\n".join(log))
        print(f"FAIL: sonda do backend: {exc}")
        return 1
    print("\n".join(log))

    t0 = time.perf_counter()
    rc, out, exe = cli_compile(FIXTURE, PROG_NAME, env)
    print(f"compilar {FIXTURE.relative_to(REPO)} pela CLI: exit={rc} ({time.perf_counter() - t0:.1f} s)")
    if rc != 0 or not exe.is_file():
        print(out)
        print("FAIL: a CLI compilou a sonda mas nao o fixture")
        return 1

    usadas: set[int] = set()
    resultados = []
    cenarios = [
        ("(a) local", lambda: cenario_local(exe, env, rng)),
        ("(b) worker no loopback (mesmo executavel)", lambda: cenario_loopback(exe, env, rng, porta_livre(args.port_base, usadas))),
        ("(c) queda do worker antes do join -> WORKER_LOST", lambda: cenario_queda(exe, env, porta_livre(args.port_base, usadas))),
    ]
    for titulo, fn in cenarios:
        try:
            ok, rel = fn()
        except (subprocess.TimeoutExpired, RuntimeError, AssertionError) as exc:
            ok, rel = False, f"erro: {exc}"
        print(f"\n## {titulo}: {'PASS' if ok else 'FAIL'}\n{rel.rstrip()}")
        resultados.append((titulo, ok))

    print("\n# Resumo (loopback: nao prova dois computadores)")
    for titulo, ok in resultados:
        print(f"- {'PASS' if ok else 'FAIL'}: {titulo}")
    return 0 if all(ok for _, ok in resultados) else 1


if __name__ == "__main__":
    sys.exit(main())
