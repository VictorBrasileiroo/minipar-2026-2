"""C-WEB-v1 compiler library. No HTTP, global output capture or cwd mutation.

The registry is process-local and retains all successful registrations for the
process lifetime. No cleanup is performed; thus active operations cannot expire.
See docs/CR-CORE08-DIAGNOSTICOS.md for expected failures absent from v1's catalog.
"""
from __future__ import annotations
import hashlib
import os
from pathlib import Path
import re
import shutil
import threading
import time
import traceback
import uuid

# Both `import service` (legacy src on sys.path) and `from src import service`.
if __package__:
    from .lexer import Lexer, TokenType
    from .parser import Parser, ParseError
    from .semantic import SemanticAnalyzer
    from .tac import TACGenerator
    from .codegen import CppCodeGenerator
    from .service_ast import serialize_ast
    from .service_process import run_bounded
else:
    from lexer import Lexer, TokenType
    from parser import Parser, ParseError
    from semantic import SemanticAnalyzer
    from tac import TACGenerator
    from codegen import CppCodeGenerator
    from service_ast import serialize_ast
    from service_process import run_bounded

ROOT = Path(__file__).resolve().parents[1]
ARTIFACT_ROOT = ROOT / "output" / "web"
PHASES = ("lexer", "parser", "semantic", "tac", "cpp", "gpp")
_registry = {}
_execution_env = {}
_registry_lock = threading.RLock()


def _diag(phase, code, message, line=None, column=None):
    return dict(phase=phase, severity="error", code=code, message=message, line=line, column=column)


def _error(code, message):
    return dict(ok=False, error=dict(code=code, message=message))


def _valid_id(value):
    return isinstance(value, str) and re.fullmatch(r"[0-9a-fA-F]{32}", value) is not None


def _safe_directory(request_id):
    # Reject redirection of the managed root as well as request directories.
    base = ARTIFACT_ROOT.absolute()
    if base.resolve() != base: raise OSError("Managed root redirected")
    directory = base / request_id
    if directory.resolve() != directory: raise OSError("Request directory redirected")
    return directory


def _register(request_id, kind, path):
    directory = _safe_directory(request_id)
    if path.parent != directory or path.resolve() != path or not path.is_file():
        raise OSError("Unexpected artifact path")
    with _registry_lock:
        _registry.setdefault(request_id, {})[kind] = path


def _pipeline(source, operation):
    started = time.monotonic()
    request_id = uuid.uuid4().hex
    result = dict(contract="minipar.compile.v1", operation=operation, request_id=request_id,
        ok=False, source_hash=None, duration_ms=0,
        phases={p: dict(status="skipped", reason="not_requested" if p == "gpp" and operation == "analyze" else "previous_phase_failed") for p in PHASES},
        diagnostics=[], artifacts=dict(cpp_id=None, tac_id=None, binary_id=None))
    phase = "lexer"
    try:
        if not isinstance(source, str): raise TypeError("source must be str")
        result["source_hash"] = "sha256:" + hashlib.sha256(source.encode("utf-8")).hexdigest()
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        result["phases"][phase] = dict(status="error" if lexer.diagnostics else "ok", tokens=[
            dict(type=t.type.name, lexeme=t.lexeme, line=t.line, column=t.col) for t in tokens if t.type != TokenType.END_OF_FILE])
        result["diagnostics"].extend(lexer.diagnostics)
        if lexer.diagnostics: return result
        phase = "parser"
        parser = Parser(tokens, exit_on_error=False)
        try: program = parser.parse()
        except ParseError as exc:
            result["phases"][phase] = dict(status="error")
            result["diagnostics"].append(exc.diagnostic)
            return result
        ast, stats = serialize_ast(program)
        result["phases"][phase] = dict(status="ok", ast=ast, ast_stats=stats)
        phase = "semantic"
        semantic = SemanticAnalyzer(emit_diagnostics=False)
        valid = semantic.analyze(program)
        result["phases"][phase] = dict(status="ok" if valid else "error", scopes=semantic.scopes, symbols=semantic.symbols)
        # None means an expected diagnostic has no approved C-WEB code. Do not
        # relabel it INTERNAL_ERROR or publish an invented code (pending CR).
        result["diagnostics"].extend(sorted((d for d in semantic.diagnostics if d["code"] is not None), key=lambda d: d["line"]))
        if not valid: return result
        phase = "tac"
        try: tac = TACGenerator().generate_text(program)
        except NotImplementedError:
            result["phases"][phase] = dict(status="error")
            return result  # Missing CORE-06 and diagnostic catalog: pending CR.
        result["phases"][phase] = dict(status="ok", text=tac, lines=len(tac.splitlines()))
        phase = "cpp"
        generator = CppCodeGenerator()
        try: cpp = generator.generate_text(program)
        except NotImplementedError:
            result["phases"][phase] = dict(status="error")
            return result
        result["phases"][phase] = dict(status="ok", text=cpp)
        if operation == "analyze":
            result["ok"] = True
            return result
        phase = "gpp"
        directory = _safe_directory(request_id)
        directory.mkdir(parents=True, exist_ok=False)
        for kind, text in (("cpp", cpp), ("tac", tac)):
            path = directory / ("program." + kind)
            path.write_text(text, encoding="utf-8", newline="\n")
            _register(request_id, kind, path)
            result["artifacts"][kind + "_id"] = request_id
        binary = directory / ("program.exe" if os.name == "nt" else "program")
        payload, code = generator.compile_cpp(directory / "program.cpp", binary)
        result["phases"][phase] = payload
        if code:
            result["diagnostics"].append(_diag("gpp", code, code + ": compilacao C++ falhou"))
        elif payload["status"] == "ok":
            env = os.environ.copy()
            compiler = shutil.which(payload["command"][0])
            if compiler:
                env["PATH"] = str(Path(compiler).parent) + os.pathsep + env.get("PATH", "")
            with _registry_lock: _execution_env[request_id] = env
            _register(request_id, "binary", binary)
            result["artifacts"]["binary_id"] = request_id
            result["ok"] = True
    except Exception:
        result["phases"][phase] = dict(status="error")
        diagnostic = _diag("internal", "INTERNAL_ERROR", "Falha interna do compilador")
        diagnostic["detail"] = traceback.format_exc()
        result["diagnostics"].append(diagnostic)
    finally:
        result["duration_ms"] = round((time.monotonic()-started)*1000)
    return result


def analyze(source: str) -> dict:
    return _pipeline(source, "analyze")


def compile_program(source: str) -> dict:
    return _pipeline(source, "compile")


def get_artifact(artifact_id: str, kind: str) -> dict:
    if not _valid_id(artifact_id) or not isinstance(kind, str) or kind not in ("cpp", "tac", "binary"):
        return _error("INVALID_ARGUMENT", "ID ou tipo de artefato invalido")
    with _registry_lock:
        path = _registry.get(artifact_id, {}).get(kind)
        if path is None: return _error("ARTIFACT_NOT_FOUND", "Artefato nao encontrado")
        try:
            directory = _safe_directory(artifact_id)
            if path.parent != directory or path.resolve() != path or not path.is_file():
                return _error("ARTIFACT_NOT_FOUND", "Artefato indisponivel")
        except OSError:
            return _error("ARTIFACT_NOT_FOUND", "Artefato indisponivel")
        extension = {"cpp": ".cpp", "tac": ".tac", "binary": ".exe" if os.name == "nt" else ""}[kind]
        media = {"cpp": "text/x-c++src", "tac": "text/plain", "binary": "application/octet-stream"}[kind]
        return dict(ok=True, path=str(path), filename=f"minipar_{artifact_id[:8]}{extension}", media_type=media)


def execute(artifact_id: str, stdin: str = "", timeout_sec: int = 10) -> dict:
    started = time.monotonic()
    result = dict(contract="minipar.execute.v1", artifact_id=artifact_id if isinstance(artifact_id, str) else None,
        ok=False, exit_code=None, timed_out=False, duration_ms=0, stdout="", stderr="",
        stdout_truncated=False, stderr_truncated=False, error=None)
    if not _valid_id(artifact_id) or type(timeout_sec) is not int or not 1 <= timeout_sec <= 30 or not isinstance(stdin, str):
        result["error"] = dict(code="INVALID_ARGUMENT", message="ID, stdin ou timeout invalido")
        return result
    artifact = get_artifact(artifact_id, "binary")
    if not artifact["ok"]:
        result["error"] = artifact["error"]
        return result
    try:
        payload = run_bounded([artifact["path"]], cwd=str(Path(artifact["path"]).parent), stdin=stdin, timeout=timeout_sec, env=_execution_env[artifact_id])
        result["exit_code"] = payload.pop("returncode")
        result.update(payload)
        result["ok"] = result["exit_code"] == 0 and not result["timed_out"]
    except Exception as exc:
        result["error"] = dict(code="INTERNAL_ERROR", message="Nao foi possivel iniciar o binario", detail=str(exc))
    finally:
        result["duration_ms"] = round((time.monotonic()-started)*1000)
    return result
