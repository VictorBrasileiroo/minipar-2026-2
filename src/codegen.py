from __future__ import annotations
import os
import subprocess
import sys
from typing import Optional
if __package__:
    from .ast_nodes import (
        ASTNode, Program, VarDecl, Assignment, PrintStmt, SeqBlock, ParBlock, BinaryExpr,
        UnaryExpr, NumberExpr, StringExpr, BoolExpr, IdentifierExpr, IfStmt, WhileStmt,
        DoWhileStmt, ForStmt, BreakStmt, ContinueStmt, InputExpr,
        ClassDecl, FuncDecl, ReturnStmt, MethodCall, FuncCallExpr, PropertyAccess, PropertyAssign, NewExpr, ThisExpr,
        CChannelExpr, SendStmt, ReceiveExpr, ListLiteral, MatrixCreateExpr, IndexExpr, IndexAssign, find_fork_join
    )
else:
    from ast_nodes import (
        ASTNode, Program, VarDecl, Assignment, PrintStmt, SeqBlock, ParBlock, BinaryExpr,
        UnaryExpr, NumberExpr, StringExpr, BoolExpr, IdentifierExpr, IfStmt, WhileStmt,
        DoWhileStmt, ForStmt, BreakStmt, ContinueStmt, InputExpr,
        ClassDecl, FuncDecl, ReturnStmt, MethodCall, FuncCallExpr, PropertyAccess, PropertyAssign, NewExpr, ThisExpr,
        CChannelExpr, SendStmt, ReceiveExpr, ListLiteral, MatrixCreateExpr, IndexExpr, IndexAssign, find_fork_join
    )
if __package__:
    from .cpp_template import _CPP_HEADER
else:
    from cpp_template import _CPP_HEADER

class CppCodeGenerator:
    @staticmethod
    def _validate_output_name(output_name: str) -> bool:
        """Aceita um nome simples e impede artefatos fora de output/."""
        reserved = {"CON", "PRN", "AUX", "NUL", "CONIN$", "CONOUT$"}
        reserved.update(f"{prefix}{digit}" for prefix in ("COM", "LPT") for digit in "123456789\u00b9\u00b2\u00b3")
        if (not isinstance(output_name, str) or not output_name
                or output_name.endswith((" ", "."))
                or any(ch in '<>:"/\\|?*' or ord(ch) < 32 for ch in output_name)
                or output_name.split(".", 1)[0].rstrip().upper() in reserved):
            print("[ERRO] output_name invalido: use apenas um nome de arquivo, sem caminhos ou caracteres reservados.", file=sys.stderr)
            return False
        try:
            output_dir = os.path.join(os.path.realpath(os.curdir), "output")
            if os.path.normcase(os.path.realpath("output")) != os.path.normcase(output_dir):
                raise ValueError("diretorio output redirecionado")
            for extension in ("exe", "cpp", "tac"):
                path = os.path.join("output", f"{output_name}.{extension}")
                if os.path.normcase(os.path.dirname(os.path.realpath(path))) != os.path.normcase(output_dir):
                    raise ValueError("artefato redirecionado para fora de output")
        except (OSError, ValueError) as exc:
            print(f"[ERRO] Destino de saida inseguro: {exc}", file=sys.stderr)
            return False
        return True

    @staticmethod
    def _escape_string(value: str) -> str:
        res = []
        for ch in value:
            if ch == "\n": res.append("\\n")
            elif ch == "\t": res.append("\\t")
            elif ch == '"': res.append('\\"')
            elif ch == "\\": res.append("\\\\")
            else: res.append(ch)
        return "".join(res)

    def _translate_expression(self, node: Optional[ASTNode]) -> str:
        if node is None: return "0"
        if isinstance(node, NumberExpr): return node.value
        if isinstance(node, StringExpr): return f'std::string("{self._escape_string(node.value)}")'
        if isinstance(node, BoolExpr): return "true" if node.value else "false"
        if isinstance(node, IdentifierExpr): return node.name
        if isinstance(node, UnaryExpr): return f"({node.op}{self._translate_expression(node.operand)})"
        if isinstance(node, BinaryExpr):
            return f"({self._translate_expression(node.left)} {node.op} {self._translate_expression(node.right)})"
        
        if isinstance(node, NewExpr):
            args = ", ".join(self._translate_expression(a) for a in node.arguments)
            return f"std::make_shared<{node.class_name}>({args})"
        if isinstance(node, ThisExpr): return "this"
        if isinstance(node, PropertyAccess):
            if node.property_name == "size": return f"{self._translate_expression(node.object)}.size()"
            return f"{self._translate_expression(node.object)}->{node.property_name}"
        
        if isinstance(node, MethodCall):
            args = ", ".join(self._translate_expression(a) for a in node.arguments)
            m_name = node.method_name
            if m_name in ("append", "push_back"): return f"{self._translate_expression(node.object)}.push_back({args})"
            if m_name == "pop": return f"__array_pop({self._translate_expression(node.object)})"
            if m_name == "size": return f"{self._translate_expression(node.object)}.size()"
            return f"{self._translate_expression(node.object)}->{m_name}({args})"
        
        if isinstance(node, FuncCallExpr):
            args = ", ".join(self._translate_expression(a) for a in node.arguments)
            if node.name == "exp":
                return f"std::exp({args})"
            if node.name == "random":
                return "random_val()"
            if node.name == "len":
                return f"__minipar_len({args})"
            if node.name == "substr":
                return f"__minipar_substr({args})"
            if node.name == "to_string":
                return f"__minipar_to_string({args})"
            if node.name == "range":
                return f"__minipar_range({args})"
            if node.name == "to_number":
                return f"std::stod({args})"
            if node.name == "parse_ints":
                return f"__parse_ints({args})"
            return f"{node.name}({args})"

        if isinstance(node, CChannelExpr):
            ip = self._translate_expression(node.ip)
            port = self._translate_expression(node.port)
            return f"std::make_shared<MiniParChannel>({ip}, {port})"
        if isinstance(node, ReceiveExpr):
            return f"{self._translate_expression(node.channel)}->receiveData()"
        if isinstance(node, InputExpr):
            if node.prompt:
                return f"input({self._translate_expression(node.prompt)})"
            return "input()"

        if isinstance(node, ListLiteral):
            elems = ", ".join(self._translate_expression(e) for e in node.elements)
            return f"std::vector<double>{{{elems}}}"
        if isinstance(node, MatrixCreateExpr):
            r = self._translate_expression(node.rows)
            c = self._translate_expression(node.cols)
            v = self._translate_expression(node.init_value)
            return f"__make_matrix({r}, {c}, {v})"
        if isinstance(node, IndexExpr):
            obj = self._translate_expression(node.object)
            idx = self._translate_expression(node.index)
            return f"__minipar_index<{node.line}>({obj}, {idx})"

        return "0"

    def _has_value_return(self, node: Optional[ASTNode]) -> bool:
        if node is None: return False
        if isinstance(node, ReturnStmt): return node.value is not None
        if isinstance(node, (SeqBlock, ParBlock)):
            return any(self._has_value_return(stmt) for stmt in node.statements)
        if isinstance(node, IfStmt):
            return self._has_value_return(node.then_branch) or self._has_value_return(node.else_branch)
        if isinstance(node, (WhileStmt, DoWhileStmt, ForStmt)):
            return self._has_value_return(node.body)
        return False

    def _uses_float_return(self, node: Optional[ASTNode]) -> bool:
        """Detecta aritmética de ponto flutuante no corpo da função."""
        if node is None:
            return False
        if isinstance(node, BinaryExpr):
            if node.op == "/":
                return True
            return self._uses_float_return(node.left) or self._uses_float_return(node.right)
        if isinstance(node, NumberExpr):
            return "." in node.value
        if isinstance(node, (SeqBlock, ParBlock)):
            return any(self._uses_float_return(stmt) for stmt in node.statements)
        if isinstance(node, IfStmt):
            return self._uses_float_return(node.then_branch) or self._uses_float_return(node.else_branch)
        if isinstance(node, (WhileStmt, DoWhileStmt, ForStmt)):
            return self._uses_float_return(node.body)
        if isinstance(node, ReturnStmt):
            return self._uses_float_return(node.value)
        return False

    def _return_type(self, body: Optional[ASTNode]) -> str:
        if not self._has_value_return(body):
            return "void"
        # auto falha no g++ quando há return double e return 0 (int) na mesma função
        if self._uses_float_return(body):
            return "double"
        return "auto"

    def _translate_statement(self, node: Optional[ASTNode], indent: str = "") -> str:
        if node is None: return ""
        if isinstance(node, VarDecl):
            expr = self._translate_expression(node.init_value) if node.init_value else ('std::string()' if node.type == "string" else "0")
            return f"{indent}auto {node.name} = {expr};\n"
        if isinstance(node, Assignment):
            return f"{indent}__minipar_assign({node.name}, {self._translate_expression(node.value)});\n"
        if isinstance(node, PropertyAssign):
            obj = self._translate_expression(node.object)
            return f"{indent}__minipar_assign({obj}->{node.property_name}, {self._translate_expression(node.value)});\n"
        if isinstance(node, IndexAssign):
            tgt = self._translate_expression(node.target)
            return f"{indent}{tgt} = {self._translate_expression(node.value)};\n"
        
        if isinstance(node, (MethodCall, FuncCallExpr)):
            return f"{indent}{self._translate_expression(node)};\n"
        if isinstance(node, ReturnStmt):
            val = self._translate_expression(node.value) if node.value else ""
            return f"{indent}return {val};\n"
        if isinstance(node, BreakStmt):
            return f"{indent}break;\n"
        if isinstance(node, ContinueStmt):
            return f"{indent}continue;\n"
        
        if isinstance(node, SendStmt):
            chan = self._translate_expression(node.channel)
            msg = self._translate_expression(node.message)
            return f"{indent}{chan}->sendData(__to_string({msg}));\n"

        if isinstance(node, PrintStmt):
            parts = []
            for i, arg in enumerate(node.arguments):
                if i > 0:
                    parts.append(' << " "')
                parts.append(f" << {self._translate_expression(arg)}")
            return f"{indent}std::cout{ ''.join(parts) } << std::endl;\n"
        
        if isinstance(node, SeqBlock):
            lines = [f"{indent}{{\n"]
            for stmt in node.statements: lines.append(self._translate_statement(stmt, indent + "    "))
            lines.append(f"{indent}}}\n")
            return "".join(lines)
        if isinstance(node, ParBlock):
            lines = [f"{indent}{{\n", f"{indent}    std::vector<std::thread> __m_thr;\n"]
            for stmt in node.statements:
                lines.append(f"{indent}    __m_thr.emplace_back([&]() {{\n{self._translate_statement(stmt, indent + '        ')}{indent}    }});\n")
            lines.append(f"{indent}    for (auto& t : __m_thr) t.join();\n{indent}}}\n")
            return "".join(lines)
        if isinstance(node, WhileStmt):
            res = f"{indent}while ({self._translate_expression(node.condition)})\n"
            res += self._translate_statement(node.body, indent if isinstance(node.body, (SeqBlock, ParBlock)) else indent + "    ")
            return res
        if isinstance(node, DoWhileStmt):
            res = f"{indent}do\n"
            res += self._translate_statement(node.body, indent if isinstance(node.body, (SeqBlock, ParBlock)) else indent + "    ").rstrip()
            res += f"\n{indent}while ({self._translate_expression(node.condition)});\n"
            return res
        if isinstance(node, ForStmt):
            if node.iterator_name and node.iterable:
                res = f"{indent}for (auto {node.iterator_name} : {self._translate_expression(node.iterable)})\n"
                res += self._translate_statement(node.body, indent if isinstance(node.body, (SeqBlock, ParBlock)) else indent + "    ")
                return res
            init = self._translate_for_part(node.initializer)
            cond = self._translate_expression(node.condition) if node.condition else "true"
            inc = self._translate_for_part(node.increment)
            res = f"{indent}for ({init}; {cond}; {inc})\n"
            res += self._translate_statement(node.body, indent if isinstance(node.body, (SeqBlock, ParBlock)) else indent + "    ")
            return res
        if isinstance(node, IfStmt):
            res = f"{indent}if ({self._translate_expression(node.condition)})\n"
            res += self._translate_statement(node.then_branch, indent if isinstance(node.then_branch, (SeqBlock, ParBlock)) else indent + "    ")
            if node.else_branch:
                res = res.rstrip() + f"\n{indent}else\n"
                if isinstance(node.else_branch, IfStmt):
                    res = res.rstrip() + " " + self._translate_statement(node.else_branch, indent).lstrip()
                else:
                    res += self._translate_statement(node.else_branch, indent if isinstance(node.else_branch, (SeqBlock, ParBlock)) else indent + "    ")
            return res
        return ""

    def _translate_for_part(self, node: Optional[ASTNode]) -> str:
        if node is None: return ""
        if isinstance(node, VarDecl):
            expr = self._translate_expression(node.init_value) if node.init_value else ('std::string()' if node.type == "string" else "0")
            return f"auto {node.name} = {expr}"
        if isinstance(node, Assignment):
            return f"__minipar_assign({node.name}, {self._translate_expression(node.value)})"
        if isinstance(node, PropertyAssign):
            return f"__minipar_assign({self._translate_expression(node.object)}->{node.property_name}, {self._translate_expression(node.value)})"
        if isinstance(node, IndexAssign):
            return f"{self._translate_expression(node.target)} = {self._translate_expression(node.value)}"
        return self._translate_expression(node)

    def generate_text(self, program: Program) -> str:
        """Translate only: no filesystem writes and no compiler invocation."""
        unsupported = find_fork_join(program)
        if unsupported is not None:
            raise NotImplementedError(f"Linha {unsupported.line}: Fork/Join requer CORE-07; C++ nao gerado.")
        cpp_code = _CPP_HEADER

        for node in program.statements:
            if isinstance(node, ClassDecl):
                cpp_code += f"class {node.name}" + (f" : public {node.superclass}" if node.superclass else "") + " {\npublic:\n"
                for attr in node.attributes:
                    if attr.init_value:
                        init = self._translate_expression(attr.init_value)
                        cpp_code += f"    decltype({init}) {attr.name} = {init};\n"
                    else:
                        cpp_code += f"    double {attr.name} = 0;\n"
                for method in node.methods:
                    params = ", ".join(f"auto {p}" for p in method.params)
                    ret = self._return_type(method.body)
                    cpp_code += f"    {ret} {method.name}({params}) {{\n"
                    if isinstance(method.body, SeqBlock):
                        for stmt in method.body.statements: cpp_code += self._translate_statement(stmt, "        ")
                    else: cpp_code += self._translate_statement(method.body, "        ")
                    cpp_code += "    }\n"
                cpp_code += "};\n\n"
            elif isinstance(node, FuncDecl):
                params = ", ".join(f"auto {p}" for p in node.params)
                ret = self._return_type(node.body)
                cpp_code += f"{ret} {node.name}({params}) {{\n"
                if isinstance(node.body, SeqBlock):
                    for stmt in node.body.statements: cpp_code += self._translate_statement(stmt, "    ")
                else: cpp_code += self._translate_statement(node.body, "    ")
                cpp_code += "}\n\n"

        cpp_code += "int main() {\n    #ifdef _WIN32\n        WSADATA wsa;\n        WSAStartup(MAKEWORD(2,2), &wsa);\n    #endif\n\n"
        for node in program.statements:
            if not isinstance(node, (ClassDecl, FuncDecl)):
                if isinstance(node, SeqBlock):
                    for stmt in node.statements: cpp_code += self._translate_statement(stmt, "    ")
                else: cpp_code += self._translate_statement(node, "    ")
        cpp_code += "\n    return 0;\n}\n"

        return cpp_code

    @staticmethod
    def compile_cpp(cpp_path, exe_path):
        """Shared native build, explicit paths and bounded diagnostic streams."""
        from pathlib import Path
        if __package__:
            from .service_process import run_bounded
        else:
            from service_process import run_bounded
        cpp_path, exe_path = Path(cpp_path).absolute(), Path(exe_path).absolute()
        compiler = os.environ.get("CXX") or "g++"
        command = [compiler, "-std=c++20", "-O3", str(cpp_path), "-o", str(exe_path), "-pthread"]
        if sys.platform == "win32": command.append("-lws2_32")
        env = os.environ.copy()
        # A configured MinGW toolchain needs its own DLL directory for this child.
        if os.path.isabs(compiler):
            env["PATH"] = str(Path(compiler).parent) + os.pathsep + env.get("PATH", "")
        payload = dict(status="error", command=command, returncode=None, stdout="", stderr="", duration_ms=0)
        code = None
        try:
            result = run_bounded(command, cwd=cpp_path.parent, timeout=120, limit=65536, env=env)
            timed_out = result.pop("timed_out")
            payload.update(result)
            if timed_out: code = "GPP_TIMEOUT"
            elif result["returncode"] != 0: code = "GPP_FAILED"
            elif not exe_path.is_file() or exe_path.is_symlink() or exe_path.stat().st_size == 0: code = "GPP_NO_BINARY"
            else: payload["status"] = "ok"
        except FileNotFoundError:
            code = "GPP_NOT_FOUND"
        if code and exe_path.is_file() and not exe_path.is_symlink(): exe_path.unlink()
        return payload, code

    def generate(self, program: Program, output_name: str) -> bool:
        if not self._validate_output_name(output_name):
            return False
        cpp_path = os.path.join("output", f"{output_name}.cpp")
        exe_path = os.path.join("output", f"{output_name}.exe")
        try:
            os.makedirs("output", exist_ok=True)
            if os.path.lexists(exe_path):
                os.remove(exe_path)
        except OSError as exc:
            print(f"[ERRO] Nao foi possivel preparar saida: {exc}", file=sys.stderr)
            return False

        unsupported = find_fork_join(program)
        if unsupported is not None:
            print(f"[ERRO BACKEND] Linha {unsupported.line}: Fork/Join requer CORE-07; C++ nao gerado.", file=sys.stderr)
            return False

        cpp_code = self.generate_text(program)

        with open(cpp_path, "w", encoding="utf-8") as f: f.write(cpp_code)

        try:
            payload, code = self.compile_cpp(cpp_path, exe_path)
        except OSError as exc:
            print(f"[ERRO] Nao foi possivel executar compilador C++: {exc}", file=sys.stderr)
            return False
        print(f"[CODEGEN] Comando: {payload['command']!r}")
        if payload["stdout"]: print(payload["stdout"], end="")
        if payload["stderr"]: print(payload["stderr"], end="", file=sys.stderr)
        if code:
            print(f"[ERRO] {code}: falha na compilacao C++.", file=sys.stderr)
            return False
        print(f"[SUCESSO] Executavel: {exe_path}")
        return True
