from __future__ import annotations
import os
import subprocess
import sys
import hashlib
from typing import Optional
from ast_nodes import (
    ASTNode, Program, VarDecl, Assignment, PrintStmt, SeqBlock, ParBlock, BinaryExpr, 
    UnaryExpr, NumberExpr, StringExpr, BoolExpr, IdentifierExpr, IfStmt, WhileStmt,
    DoWhileStmt, ForStmt, BreakStmt, ContinueStmt, InputExpr,
    ClassDecl, FuncDecl, ReturnStmt, MethodCall, FuncCallExpr, PropertyAccess, PropertyAssign, NewExpr, ThisExpr,
    CChannelExpr, SendStmt, ReceiveExpr, ListLiteral, MatrixCreateExpr, IndexExpr, IndexAssign, find_fork_join,
    ForkExpr, JoinExpr, iter_child_nodes
)
from cpp_template import _CPP_HEADER, _FJ_HEADER
from semantic import SemanticAnalyzer, CppTaskContext, CppProofError

class CppCodeGenerator:
    def __init__(self):
        self.fj = None
        self.context = None
        self._serial = 0
        self._prefix = "__fj"

    def _ordered(self, expressions, call, returns=True):
        """Snapshots sequenciais; a lambda so usa referencias durante a expressao."""
        self._serial += 1
        names = [f"{self._prefix}_{self._serial}_{i}" for i in range(len(expressions))]
        setup = " ".join(f"auto {n} = {e};" for n, e in zip(names, expressions))
        action = ("return " if returns else "") + call(names) + ";"
        return f"([&]() {{ {setup} {action} }}())"

    def _fj_index(self, node, target=False):
        self._serial += 1
        obj, idx = f"{self._prefix}_obj_{self._serial}", f"{self._prefix}_idx_{self._serial}"
        # Uma indexacao so preserva armazenamento se toda a cadeia termina
        # numa variavel. IndexExpr sobre chamada/join ainda pertence a um
        # temporario: copiar o resultado antes de destruir seu proprietario.
        storage = node.object
        while isinstance(storage, IndexExpr): storage = storage.object
        ret = " -> decltype(auto)" if isinstance(storage, IdentifierExpr) else ""
        value = f"__fj_index<{node.line}>({obj}, {idx})"
        if not target and self.context["types"][id(node)].kind == "bool":
            value = f"static_cast<bool>({value})" # materializa antes de destruir temporarios
            ret = ""
        result = (f"([&](){ret} {{ auto&& {obj} = {self._translate_expression(node.object)}; "
                  f"auto {idx} = {self._translate_expression(node.index)}; return {value}; }}())")
        return result

    def _fj_expression(self, node):
        expr = self._translate_expression
        typ = self.context["types"].get(id(node))
        if isinstance(node, ForkExpr):
            args = [f"minipar_rt::to_value({expr(a)})" for a in node.arguments]
            args.append(expr(node.destination) if node.destination else 'std::string("local")')
            return self._ordered(args, lambda ns: f'minipar_rt::start("{node.function_name}", '
                                 + "{" + ", ".join(ns[:-1]) + "}, minipar_rt::Destination::parse(" + ns[-1] + "))")
        if isinstance(node, JoinExpr):
            args = [expr(node.handle)]
            args.append(f"__fj_timeout({expr(node.timeout)})" if node.timeout else "-1")
            call = lambda ns: f"__fj_join({ns[0]}, {ns[1]})"
            if typ.kind != "void":
                call = lambda ns: f"minipar_rt::value_cast<{typ.cpp()}>(__fj_join({ns[0]}, {ns[1]}))"
            return self._ordered(args, call)
        if isinstance(node, ListLiteral):
            if typ is None or typ.item is None: raise CppProofError("CORE-07 lista sem representacao")
            return typ.cpp() + "{" + ", ".join(expr(e) for e in node.elements) + "}"
        if isinstance(node, FuncCallExpr):
            if id(node) in self.context["calls"]:
                name = self.function_names[self.context["calls"][id(node)]]
            else:
                name = {"exp": "std::exp", "random": "random_val", "len": "__minipar_len",
                        "substr": "__minipar_substr", "to_string": "__minipar_to_string",
                        "range": "__minipar_range", "to_number": "std::stod", "parse_ints": "__parse_ints"}[node.name]
            return self._ordered([expr(a) for a in node.arguments], lambda ns: f"{name}({', '.join(ns)})", typ.kind != "void")
        if isinstance(node, BinaryExpr) and node.op not in ("&&", "||"):
            return self._ordered([expr(node.left), expr(node.right)], lambda ns: f"({ns[0]} {node.op} {ns[1]})")
        if isinstance(node, IndexExpr):
            return self._fj_index(node)
        if isinstance(node, MatrixCreateExpr):
            return self._ordered([expr(node.rows), expr(node.cols), expr(node.init_value)],
                                 lambda ns: f"__make_matrix({', '.join(ns)})")
        if isinstance(node, MethodCall) and node.method_name == "pop":
            return f"__fj_pop({expr(node.object)})"
        return None

    def _fj_program(self, program, semantic, source):
        if source is None: raise CppProofError("CORE-07 exige source para SHA-256 do fonte MiniPar")
        if semantic is None:
            semantic = SemanticAnalyzer()
            if not semantic.analyze(program): raise CppProofError("CORE-07 analise semantica falhou")
        self.fj = CppTaskContext(program, semantic, self._uses_float_return)
        identifiers, pending = set(), [program]
        while pending:
            node = pending.pop()
            identifiers.update(getattr(node, "params", []))
            for field in ("name", "iterator_name"):
                name = getattr(node, field, None)
                if name: identifiers.add(name)
            pending.extend(iter_child_nodes(node))
        self._prefix = "__fj"
        while any(n.startswith(self._prefix) for n in identifiers): self._prefix += "_"
        self.function_names = {key: f"{self._prefix}_fn_{i}" for i, key in enumerate(self.fj.contexts)}
        code = _CPP_HEADER + _FJ_HEADER
        signatures = {}
        for key, ctx in self.fj.contexts.items():
            name, args = key
            fn = self.fj.functions[name]
            params = ", ".join(f"{t.cpp()} {p}" for p, t in zip(fn.params, args))
            signatures[key] = f"{ctx['result'].cpp()} {self.function_names[key]}({params})"
            code += signatures[key] + ";\n"
        for key, ctx in self.fj.contexts.items():
            self.context = ctx
            code += signatures[key] + " {\n" + self._translate_statement(self.fj.functions[key[0]].body, "    ") + "}\n"
        for name, (args, result) in self.fj.forks.items():
            fn = self.function_names[(name, args)]
            conversions = ", ".join(f"minipar_rt::value_cast<{t.cpp()}>(a.at({i}))" for i, t in enumerate(args))
            code += f"minipar_rt::Value __fj_wrap_{name}(const minipar_rt::TaskArgs& a) {{\n"
            code += f'    if (a.size() != {len(args)}) throw std::invalid_argument("aridade de {name}");\n    __fj_scope scope(true);\n'
            call = f"{fn}({conversions})"
            code += (f"    {call}; return minipar_rt::Value();\n" if result.kind == "void"
                     else f"    return minipar_rt::to_value({call});\n") + "}\n"
        code += 'int main(int argc, char** argv) {\n'
        code += f'    minipar_rt::set_build_id("{hashlib.sha256(source.encode("utf-8")).hexdigest()}");\n'
        for name in self.fj.forks:
            code += f'    minipar_rt::register_function("{name}", __fj_wrap_{name});\n'
        code += "    if (int rc = minipar_rt::worker_main_if_requested(argc, argv); rc >= 0) return rc;\n"
        code += "    try {\n"
        self.context = self.fj.main
        for node in program.statements:
            if not isinstance(node, FuncDecl): code += self._translate_statement(node, "    ")
        # Nao espera tarefas nao coletadas. Evita destrutores estaticos enquanto
        # executor/conexoes do runtime continuam vivos (mesmo padrao dos probes).
        code += '    std::cout.flush(); std::cerr.flush(); std::_Exit(0);\n'
        code += '    } catch (const std::exception& e) { std::cerr << "[CORE-07] " << e.what() << std::endl; std::cout.flush(); std::_Exit(1); }\n}\n'
        return code

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
        if self.fj:
            translated = self._fj_expression(node)
            if translated is not None: return translated
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
        if self.fj and isinstance(node, (ForkExpr, JoinExpr)):
            return f"{indent}{self._translate_expression(node)};\n"
        if isinstance(node, VarDecl):
            expr = self._translate_expression(node.init_value) if node.init_value else ('std::string()' if node.type == "string" else "0")
            return f"{indent}auto {node.name} = {expr};\n"
        if isinstance(node, Assignment):
            return f"{indent}__minipar_assign({node.name}, {self._translate_expression(node.value)});\n"
        if isinstance(node, PropertyAssign):
            obj = self._translate_expression(node.object)
            return f"{indent}__minipar_assign({obj}->{node.property_name}, {self._translate_expression(node.value)});\n"
        if isinstance(node, IndexAssign):
            tgt = self._fj_index(node.target, target=True) if self.fj else self._translate_expression(node.target)
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
            if self.fj:
                threads, errors, task = (self._prefix + suffix for suffix in ("_threads", "_errors", "_task"))
                lines = [f"{indent}{{\n", f"{indent}    std::vector<std::thread> {threads};\n",
                         f"{indent}    std::vector<std::exception_ptr> {errors}({len(node.statements)});\n",
                         f"{indent}    bool {task} = __fj_in_task;\n"]
                for i, stmt in enumerate(node.statements):
                    lines.append(f"{indent}    {threads}.emplace_back([&, {task}]() {{ __fj_scope scope({task}); try {{\n"
                                 + self._translate_statement(stmt, indent + "        ")
                                 + f"{indent}    }} catch (...) {{ {errors}[{i}] = std::current_exception(); }} }});\n")
                lines.append(f"{indent}    for (auto& t : {threads}) t.join();\n"
                             f"{indent}    for (auto& e : {errors}) if (e) std::rethrow_exception(e);\n{indent}}}\n")
                return "".join(lines)
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
                item_type = self.context["decls"][id(node)].cpp() if self.fj else "auto"
                res = f"{indent}for ({item_type} {node.iterator_name} : {self._translate_expression(node.iterable)})\n"
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
            target = self._fj_index(node.target, target=True) if self.fj else self._translate_expression(node.target)
            return f"{target} = {self._translate_expression(node.value)}"
        return self._translate_expression(node)

    def generate_text(self, program: Program, semantic=None, source=None) -> str:
        self.fj = None
        self.context = None
        self._serial = 0
        if find_fork_join(program) is not None:
            return self._fj_program(program, semantic, source)
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

    def generate(self, program: Program, output_name: str, semantic=None, source=None) -> bool:
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

        try:
            cpp_code = self.generate_text(program, semantic, source)
        except CppProofError as exc:
            print(f"[ERRO BACKEND] {exc}", file=sys.stderr)
            return False

        with open(cpp_path, "w", encoding="utf-8") as f: f.write(cpp_code)
        
        # CXX e um executavel (nome ou caminho), sem flags ou aspas embutidas.
        compiler = os.environ.get("CXX") or "g++"
        command = [compiler, "-std=c++20", "-O3", cpp_path, "-o", exe_path, "-pthread"]
        if self.fj:
            command.extend(["-I", os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "runtime", "include")])
        if sys.platform == "win32":
            command.append("-lws2_32")
        print(f"[CODEGEN] Comando: {command!r}")
        try:
            result = subprocess.run(
                command, capture_output=True, text=True, encoding="utf-8",
                errors="replace", stdin=subprocess.DEVNULL, timeout=120,
            )
        except FileNotFoundError:
            print(f"[ERRO] Compilador C++ nao encontrado: {compiler}. Configure CXX com o caminho do g++.", file=sys.stderr)
        except subprocess.TimeoutExpired as exc:
            print("[ERRO] Timeout na compilacao C++ (120 s).", file=sys.stderr)
            for diagnostic in (exc.stdout, exc.stderr):
                if diagnostic:
                    print(diagnostic.decode("utf-8", errors="replace") if isinstance(diagnostic, bytes) else diagnostic, file=sys.stderr)
        except OSError as exc:
            print(f"[ERRO] Nao foi possivel executar compilador C++: {exc}", file=sys.stderr)
        else:
            if result.stdout:
                print(result.stdout, end="")
            if result.stderr:
                print(result.stderr, end="", file=sys.stderr)
            if result.returncode != 0:
                print(f"[ERRO] Falha na compilacao C++ (exit={result.returncode}).", file=sys.stderr)
            elif not os.path.isfile(exe_path) or os.path.getsize(exe_path) == 0:
                print("[ERRO] Compilador retornou sucesso sem gerar binario valido nesta execucao.", file=sys.stderr)
            else:
                print(f"[SUCESSO] Executavel: {exe_path}")
                return True

        # Um compilador que falhou pode ter deixado uma saida parcial.
        try:
            if os.path.lexists(exe_path):
                os.remove(exe_path)
        except OSError as exc:
            print(f"[ERRO] Nao foi possivel remover saida parcial: {exc}", file=sys.stderr)
        return False
