from __future__ import annotations
import sys
from dataclasses import dataclass, field
from typing import Dict, List, Optional
from ast_nodes import (
    ASTNode, Program, VarDecl, Assignment, PrintStmt, IdentifierExpr, BinaryExpr,
    UnaryExpr, NumberExpr, StringExpr, BoolExpr, SeqBlock, ParBlock, IfStmt, WhileStmt,
    DoWhileStmt, ForStmt, BreakStmt, ContinueStmt, InputExpr,
    ClassDecl, FuncDecl, ReturnStmt, MethodCall, FuncCallExpr, PropertyAccess, PropertyAssign, NewExpr, ThisExpr,
    CChannelExpr, SendStmt, ReceiveExpr, ListLiteral, MatrixCreateExpr, IndexExpr, IndexAssign,
    ForkExpr, JoinExpr, find_fork_join
)

@dataclass(frozen=True)
class ValueType:
    """Informacao parcial para a fronteira de tarefas; unknown nao e prova de tipo."""
    kind: str = "unknown"
    elements: tuple[ValueType, ...] = ()
    result: Optional[ValueType] = None

@dataclass
class Symbol:
    name: str
    type: str
    params: List[str] = field(default_factory=list)
    attributes: Dict[str, str] = field(default_factory=dict)
    methods: Dict[str, List[str]] = field(default_factory=dict)
    value_type: Optional[ValueType] = None

class SemanticAnalyzer:
    def __init__(self) -> None:
        self._scopes: List[Dict[str, Symbol]] = []
        self._has_errors = False
        self._current_function: Optional[str] = None
        self._current_class: Optional[str] = None
        self._classes: Dict[str, Symbol] = {}
        self._functions: Dict[str, Symbol] = {}
        self._loop_depth = 0
        self.expression_types: Dict[int, ValueType] = {}
        self.fork_signatures: Dict[int, list[tuple[tuple[ValueType, ...], ValueType]]] = {}
        self.unresolved_fj: List[str] = []
        self._function_nodes: Dict[str, FuncDecl] = {}
        self._class_nodes: Dict[str, ClassDecl] = {}
        self._class_initializers: Dict[str, FuncDecl] = {}
        self._global_symbols: Dict[str, Symbol] = {}
        self._isolated = False
        self._fj_enabled = False
        self._checking_functions = set()
        self._return_types: Optional[List[ValueType]] = None
        self._enter_scope()

    def _enter_scope(self) -> None: self._scopes.append({})
    def _exit_scope(self) -> None:
        if len(self._scopes) > 1: self._scopes.pop()

    def _get_context(self) -> str:
        return f" (Funcao: {self._current_function})" if self._current_function else ""

    def _define_symbol(self, name: str, type_: str, line: int, params: Optional[List[str]] = None) -> None:
        if name in self._scopes[-1]:
            print(f"[ERRO SEMANTICO] Linha {line}{self._get_context()}: Variavel '{name}' ja declarada.", file=sys.stderr)
            self._has_errors = True
        else: self._scopes[-1][name] = Symbol(name=name, type=type_, params=params or [])

    def _lookup(self, name: str) -> Optional[Symbol]:
        for scope in reversed(self._scopes):
            if name in scope: return scope[name]
        return None

    def _report(self, line: int, message: str) -> None:
        print(f"[ERRO SEMANTICO] Linha {line}{self._get_context()}: {message}", file=sys.stderr)
        self._has_errors = True

    def _infer_type(self, node: Optional[ASTNode]) -> str:
        if node is None: return "unknown"
        if isinstance(node, ForkExpr): return "task"
        if id(node) in self.expression_types: return self.expression_types[id(node)].kind
        if isinstance(node, NumberExpr): return "number"
        if isinstance(node, StringExpr): return "string"
        if isinstance(node, BoolExpr): return "bool"
        if isinstance(node, InputExpr): return "string"
        if isinstance(node, CChannelExpr): return "c_channel"
        if isinstance(node, ReceiveExpr): return "string"
        if isinstance(node, ListLiteral): return "list"
        if isinstance(node, MatrixCreateExpr): return "matrix"
        if isinstance(node, NewExpr): return node.class_name
        if isinstance(node, ThisExpr): return self._current_class or "unknown"
        if isinstance(node, IdentifierExpr):
            sym = self._lookup(node.name)
            return sym.type if sym else "unknown"
        if isinstance(node, UnaryExpr):
            return "bool" if node.op == "!" else self._infer_type(node.operand)
        if isinstance(node, BinaryExpr):
            lt, rt = self._infer_type(node.left), self._infer_type(node.right)
            if node.op in ("==", "!=", "<", ">", "<=", ">=", "&&", "||"): return "bool"
            if node.op == "+" and (lt == "string" or rt == "string"): return "string"
            if node.op == "+" and (lt == "list" or rt == "list"): return "list"
            return "number"
        if isinstance(node, PropertyAccess):
            obj_type = self._infer_type(node.object)
            cls = self._classes.get(obj_type)
            if cls and node.property_name in cls.attributes: return cls.attributes[node.property_name]
            return "unknown"
        if isinstance(node, MethodCall):
            return "unknown"
        if isinstance(node, FuncCallExpr):
            if node.name in ("random", "exp", "len", "to_number"): return "number"
            if node.name in ("substr", "to_string"): return "string"
            if node.name in ("range", "parse_ints"): return "list"
            return "unknown"
        if isinstance(node, IndexExpr):
            return "number" if self._infer_type(node.object) == "list" else "unknown"
        return "unknown"

    def _types_compatible(self, declared: str, actual: str) -> bool:
        if declared in ("var", "unknown") or actual == "unknown": return True
        if declared == "int" and actual == "number": return True
        if declared == "number" and actual == "int": return True
        return declared == actual

    def _collect_declarations(self, program: Program) -> None:
        for stmt in program.statements:
            if isinstance(stmt, FuncDecl):
                self._functions[stmt.name] = Symbol(stmt.name, "FUNC", params=stmt.params)
                self._function_nodes[stmt.name] = stmt
            elif isinstance(stmt, ClassDecl):
                self._class_nodes[stmt.name] = stmt
                self._class_initializers[stmt.name] = FuncDecl(
                    "<inicializacao>", [], SeqBlock(stmt.attributes), line=stmt.line)
                attrs = {a.name: self._infer_type(a.init_value) if a.type == "var" else a.type
                         for a in stmt.attributes}
                methods = {m.name: m.params for m in stmt.methods}
                self._classes[stmt.name] = Symbol(stmt.name, "CLASS", attributes=attrs, methods=methods)

    def _value_type(self, node: Optional[ASTNode]) -> ValueType:
        if node is None: return ValueType("void")
        if isinstance(node, IdentifierExpr):
            symbol = self._lookup(node.name)
            if symbol: return symbol.value_type or ValueType(symbol.type)
        if isinstance(node, ListLiteral):
            return ValueType("list", tuple(self._value_type(e) for e in node.elements))
        if isinstance(node, MatrixCreateExpr):
            return ValueType("matrix", (self._value_type(node.init_value),))
        if isinstance(node, IndexExpr):
            collection = self._value_type(node.object)
            if collection.kind in ("list", "matrix") and collection.elements:
                return self._merge_value_types(collection.elements)
        if isinstance(node, PropertyAccess):
            cls = self._class_nodes.get(self._infer_type(node.object))
            if cls:
                attr = next((a for a in cls.attributes if a.name == node.property_name), None)
                if attr and isinstance(attr.init_value, (ListLiteral, MatrixCreateExpr)):
                    return self._value_type(attr.init_value)
        return self.expression_types.get(id(node), ValueType(self._infer_type(node)))

    @staticmethod
    def _merge_value_types(infos: tuple[ValueType, ...]) -> ValueType:
        if not infos: return ValueType()
        if all(info == infos[0] for info in infos): return infos[0]
        if all(info.kind == "task" for info in infos):
            return ValueType("task", result=SemanticAnalyzer._merge_value_types(
                tuple(info.result or ValueType() for info in infos)))
        if all(info.kind == "list" for info in infos):
            return ValueType("list", tuple(e for info in infos for e in info.elements))
        return ValueType("unknown", infos)

    def _extend_collection(self, target: ASTNode, infos: tuple[ValueType, ...]) -> None:
        if isinstance(target, IndexExpr):
            # Escrita em lista aninhada: conservamos o tipo proibido em todos os niveis.
            self._extend_collection(target.object, (ValueType("list", infos),))
        elif isinstance(target, IdentifierExpr):
            symbol = self._lookup(target.name)
            if symbol and symbol.type in ("list", "matrix"):
                old = symbol.value_type or ValueType(symbol.type)
                # Listas MiniPar sao valores copiados, inclusive em atribuicoes.
                symbol.value_type = ValueType(symbol.type, old.elements + infos)

    def _check_transport(self, info: ValueType, line: int, role: str) -> None:
        if info.kind in ("unknown", "var"):
            for alternative in info.elements: self._check_transport(alternative, line, role)
            note = f"Linha {line}: {role} com tipo nao comprovado estaticamente."
            if note not in self.unresolved_fj: self.unresolved_fj.append(note)
        elif info.kind in ("list", "matrix"):
            # Uma lista sem elementos conhecidos nao comprova seu conteudo futuro.
            for element in info.elements: self._check_transport(element, line, role)
        elif info.kind not in ("number", "int", "bool", "string", "void"):
            self._report(line, f"FJ-SEM-06: {role} de tipo {info.kind} nao cruza tarefas.")

    def _check_global_access(self, name: str, line: int) -> None:
        if not self._isolated: return
        for index in range(len(self._scopes) - 1, -1, -1):
            if name in self._scopes[index]:
                if index == 0 and self._scopes[index][name].type not in ("FUNC", "CLASS"):
                    self._report(line, f"FJ-SEM-05: tarefa acessa global mutavel '{name}'.")
                return

    def _check_function(self, function: FuncDecl, arguments: tuple[ValueType, ...],
                        isolated: bool, owner: Optional[str] = None) -> ValueType:
        """Analisa cada chamada com escopo lexico global, nunca com locais do chamador."""
        key = (id(function), isolated)
        if key in self._checking_functions:
            return ValueType()  # Recursao generica nao comprova tipo de retorno.
        self._checking_functions.add(key)
        saved = (self._scopes, self._current_function, self._current_class,
                 self._isolated, self._return_types, self._loop_depth, self.expression_types)
        # Tipos de expressoes dependentes de parametros pertencem a esta chamada.
        self.expression_types = {}
        self._scopes = [dict(self._global_symbols)]
        self._current_function, self._current_class = function.name, owner
        self._isolated, self._return_types, self._loop_depth = isolated, [], 0
        try:
            if owner:
                self._enter_scope()
                for name, kind in self._classes[owner].attributes.items():
                    self._define_symbol(name, kind, function.line)
            self._enter_scope()
            for name, info in zip(function.params, arguments):
                self._define_symbol(name, info.kind, function.line)
                self._lookup(name).value_type = info
            self.validate_node(function.body)
            returns = self._return_types
            if not returns: return ValueType("void")
            known = [info for info in returns if info.kind not in ("var", "unknown")]
            if known and all(info == known[0] for info in known) and len(known) == len(returns):
                return known[0]
            return ValueType("unknown", tuple(returns))
        finally:
            (self._scopes, self._current_function, self._current_class,
             self._isolated, self._return_types, self._loop_depth, self.expression_types) = saved
            self._checking_functions.remove(key)

    def _validate_fork(self, node: ForkExpr) -> None:
        for arg in node.arguments: self.validate_node(arg)
        self.validate_node(node.destination)
        if node.destination and self._infer_type(node.destination) not in ("string", "var", "unknown"):
            self._report(node.line, "FJ-SEM-04: destino de fork deve ser string.")
        function = self._function_nodes.get(node.function_name)
        symbol = self._lookup(node.function_name)
        # A funcao global pode estar declarada depois deste ponto.
        if function is None or (symbol is not None and symbol is not self._scopes[0].get(node.function_name)):
            self._report(node.line, f"FJ-SEM-01: fork exige funcao global '{node.function_name}'.")
            return
        if symbol is not None and symbol.type != "FUNC":
            self._report(node.line, f"FJ-SEM-01: '{node.function_name}' nao e funcao global.")
            return
        if len(node.arguments) != len(function.params):
            self._report(node.line, f"FJ-SEM-02: '{node.function_name}' espera {len(function.params)} argumento(s), recebeu {len(node.arguments)}.")
            return
        arguments = tuple(self._value_type(arg) for arg in node.arguments)
        for info in arguments: self._check_transport(info, node.line, "argumento")
        result = self._check_function(function, arguments, isolated=True)
        self._check_transport(result, node.line, "retorno")
        self.expression_types[id(node)] = ValueType("task", result=result)
        signature = (arguments, result)
        signatures = self.fork_signatures.setdefault(id(node), [])
        if signature not in signatures: signatures.append(signature)

    def _validate_join(self, node: JoinExpr) -> None:
        self.validate_node(node.handle)
        self.validate_node(node.timeout)
        handle = self._value_type(node.handle)
        if handle.kind != "task":
            if handle.kind in ("var", "unknown") and self._current_function and self._return_types is None:
                note = f"Linha {node.line}: join generico depende do tipo do argumento na chamada."
                if note not in self.unresolved_fj: self.unresolved_fj.append(note)
            else:
                self._report(node.line, f"FJ-SEM-03: join exige handle task reconhecido, recebeu {handle.kind}.")
        if node.timeout and self._infer_type(node.timeout) not in ("number", "int", "var", "unknown"):
            self._report(node.line, "FJ-SEM-04: timeout de join deve ser numerico.")
        self.expression_types[id(node)] = handle.result or ValueType()

    def validate_node(self, node: ASTNode) -> None:
        if node is None: return

        if isinstance(node, ForkExpr):
            self._validate_fork(node)
        elif isinstance(node, JoinExpr):
            self._validate_join(node)
        elif isinstance(node, VarDecl):
            self.validate_node(node.init_value)
            actual_type = self._infer_type(node.init_value)
            declared_type = actual_type if node.type == "var" and actual_type != "unknown" else node.type
            if not self._types_compatible(declared_type, actual_type):
                self._report(node.line, f"Tipo incompativel em '{node.name}': esperado {declared_type}, recebido {actual_type}.")
            value_type = self._value_type(node.init_value) if node.init_value else ValueType(declared_type)
            self._define_symbol(node.name, declared_type, node.line)
            symbol = self._lookup(node.name)
            if symbol: symbol.value_type = value_type
        elif isinstance(node, Assignment):
            self._check_global_access(node.name, node.line)
            sym = self._lookup(node.name)
            if sym is None:
                self._report(node.line, f"Variavel '{node.name}' nao declarada.")
            self.validate_node(node.value)
            if sym and not self._types_compatible(sym.type, self._infer_type(node.value)):
                self._report(node.line, f"Tipo incompativel em atribuicao de '{node.name}'.")
            if sym and self._fj_enabled:
                sym.value_type = self._value_type(node.value)
                if sym.type in ("var", "unknown"): sym.type = sym.value_type.kind
        elif isinstance(node, PrintStmt):
            for arg in node.arguments: self.validate_node(arg)
        elif isinstance(node, SendStmt):
            self.validate_node(node.channel)
            self.validate_node(node.message)
        elif isinstance(node, CChannelExpr):
            self.validate_node(node.ip)
            self.validate_node(node.port)
        elif isinstance(node, ReceiveExpr):
            self.validate_node(node.channel)
        elif isinstance(node, ListLiteral):
            for e in node.elements:
                self.validate_node(e)
                if self._infer_type(e) == "string":
                    self._report(node.line, "Listas de strings ainda nao suportadas (C-T11-v1 3.4).")
        elif isinstance(node, MatrixCreateExpr):
            self.validate_node(node.rows)
            self.validate_node(node.cols)
            self.validate_node(node.init_value)
        elif isinstance(node, IndexExpr):
            self.validate_node(node.object)
            self.validate_node(node.index)
            if self._fj_enabled: self.expression_types[id(node)] = self._value_type(node)
        elif isinstance(node, IndexAssign):
            self.validate_node(node.target)
            self.validate_node(node.value)
            if self._fj_enabled:
                self._extend_collection(node.target.object, (self._value_type(node.value),))
        elif isinstance(node, IdentifierExpr):
            self._check_global_access(node.name, node.line)
            if self._lookup(node.name) is None:
                self._report(node.line, f"Variavel '{node.name}' nao declarada.")
        elif isinstance(node, BinaryExpr):
            self.validate_node(node.left)
            self.validate_node(node.right)
            lt, rt = self._infer_type(node.left), self._infer_type(node.right)
            if self._fj_enabled and node.op in ("+", "-", "*", "/", "%"):
                if any(t in ("task", "c_channel") or t in self._classes for t in (lt, rt)):
                    self._report(node.line, "FJ-SEM-06: objeto, canal ou handle nao admite operacao aritmetica.")
            if node.op in ("+", "==", "!=", "<", "<=", ">", ">="):
                if ((lt == "string" and rt not in ("string", "var", "unknown"))
                        or (rt == "string" and lt not in ("string", "var", "unknown"))):
                    self._report(node.line, f"Operador '{node.op}' entre string e outro tipo exige conversao explicita.")
            if node.op in ("+", "-", "*", "/", "%"):
                if node.op != "+" and (lt not in ("number", "int", "var", "unknown") or rt not in ("number", "int", "var", "unknown")):
                    self._report(node.line, f"Operador '{node.op}' exige operandos numericos.")
        elif isinstance(node, UnaryExpr):
            self.validate_node(node.operand)
            kind = self._infer_type(node.operand)
            if self._fj_enabled and node.op in ("+", "-") and (kind in ("task", "c_channel") or kind in self._classes):
                self._report(node.line, "FJ-SEM-06: objeto, canal ou handle nao admite operacao aritmetica.")
        elif isinstance(node, (SeqBlock, ParBlock)):
            self._enter_scope()
            for stmt in node.statements: self.validate_node(stmt)
            self._exit_scope()
        elif isinstance(node, IfStmt):
            self.validate_node(node.condition)
            self.validate_node(node.then_branch)
            if node.else_branch: self.validate_node(node.else_branch)
        elif isinstance(node, WhileStmt):
            self.validate_node(node.condition)
            self._loop_depth += 1
            self.validate_node(node.body)
            self._loop_depth -= 1
        elif isinstance(node, DoWhileStmt):
            self._loop_depth += 1
            self.validate_node(node.body)
            self._loop_depth -= 1
            self.validate_node(node.condition)
        elif isinstance(node, ForStmt):
            self._enter_scope()
            if node.iterator_name:
                self.validate_node(node.iterable)
                self._define_symbol(node.iterator_name, "var", node.line)
            else:
                self.validate_node(node.initializer)
                self.validate_node(node.condition)
                self.validate_node(node.increment)
            self._loop_depth += 1
            self.validate_node(node.body)
            self._loop_depth -= 1
            self._exit_scope()
        elif isinstance(node, (BreakStmt, ContinueStmt)):
            if self._loop_depth == 0:
                self._report(node.line, f"'{node.__class__.__name__.replace('Stmt', '').lower()}' usado fora de laco.")
        elif isinstance(node, ClassDecl):
            if node.superclass and node.superclass not in self._classes:
                self._report(node.line, f"Superclasse '{node.superclass}' nao declarada.")
            self._define_symbol(node.name, "CLASS", node.line)
            self._enter_scope()
            old_class = self._current_class
            self._current_class = node.name
            for attr in node.attributes:
                self.validate_node(attr)
                self._classes[node.name].attributes[attr.name] = self._lookup(attr.name).type
            for method in node.methods: self.validate_node(method)
            self._current_class = old_class
            self._exit_scope()
        elif isinstance(node, FuncDecl):
            self._define_symbol(node.name, "FUNC", node.line, node.params)
            self._enter_scope()
            old_function = self._current_function
            self._current_function = node.name
            for p in node.params: self._define_symbol(p, "var", node.line)
            self.validate_node(node.body)
            self._current_function = old_function
            self._exit_scope()
        elif isinstance(node, ReturnStmt):
            if node.value: self.validate_node(node.value)
            if self._return_types is not None:
                info = self._value_type(node.value)
                self._return_types.append(info)
        elif isinstance(node, MethodCall):
            self.validate_node(node.object)
            for arg in node.arguments: self.validate_node(arg)
            obj_type = self._infer_type(node.object)
            cls = self._classes.get(obj_type)
            if cls and node.method_name not in cls.methods:
                self._report(node.line, f"Metodo '{node.method_name}' nao declarado em '{obj_type}'.")
            elif cls and len(cls.methods[node.method_name]) != len(node.arguments):
                self._report(node.line, f"Metodo '{node.method_name}' espera {len(cls.methods[node.method_name])} argumento(s), recebeu {len(node.arguments)}.")
            if (obj_type == "list" and node.method_name in ("append", "push_back")
                    and any(self._infer_type(arg) == "string" for arg in node.arguments)):
                self._report(node.line, "Listas de strings ainda nao suportadas (C-T11-v1 3.4).")
            if self._fj_enabled:
                if obj_type == "list" and node.method_name in ("append", "push_back"):
                    self._extend_collection(node.object, tuple(self._value_type(a) for a in node.arguments))
                if obj_type == "list" and node.method_name == "pop":
                    self.expression_types[id(node)] = self._merge_value_types(self._value_type(node.object).elements)
                if node.method_name == "size" and obj_type in ("list", "matrix", "string"):
                    self.expression_types[id(node)] = ValueType("number")
                if self._isolated and obj_type in ("var", "unknown"):
                    self._report(node.line, "FJ-SEM-05: nao e possivel comprovar isolamento de chamada de metodo sem tipo conhecido.")
                if cls:
                    method = next((m for m in self._class_nodes[obj_type].methods if m.name == node.method_name), None)
                    if method and len(method.params) == len(node.arguments):
                        self.expression_types[id(node)] = self._check_function(
                            method, tuple(self._value_type(a) for a in node.arguments), self._isolated, obj_type)
        elif isinstance(node, FuncCallExpr):
            if self._isolated:
                symbol = self._lookup(node.name)
                if symbol is not None and (symbol.type != "FUNC" or symbol is not self._scopes[0].get(node.name)):
                    self._report(node.line, f"FJ-SEM-05: chamada '{node.name}' nao resolve funcao global isolada.")
            if node.name not in self._functions and node.name not in ("exp", "random", "range", "len", "to_number", "parse_ints", "substr", "to_string"):
                self._report(node.line, f"Funcao '{node.name}' nao declarada.")
            elif node.name in self._functions and len(self._functions[node.name].params) != len(node.arguments):
                self._report(node.line, f"Funcao '{node.name}' espera {len(self._functions[node.name].params)} argumento(s), recebeu {len(node.arguments)}.")
            for arg in node.arguments: self.validate_node(arg)
            if self._fj_enabled and node.name in self._function_nodes:
                function = self._function_nodes[node.name]
                if len(function.params) == len(node.arguments):
                    self.expression_types[id(node)] = self._check_function(
                        function, tuple(self._value_type(a) for a in node.arguments), self._isolated)
            native_types = {"substr": ("string", "number", "number"),
                            "to_string": ("number",), "len": ("collection",)}
            if node.name in native_types:
                expected = native_types[node.name]
                if len(node.arguments) != len(expected):
                    self._report(node.line, f"Funcao '{node.name}' espera {len(expected)} argumento(s), recebeu {len(node.arguments)}.")
                else:
                    for arg, required in zip(node.arguments, expected):
                        actual = self._infer_type(arg)
                        allowed = (("string", "list", "matrix") if required == "collection"
                                   else ("number", "int") if required == "number" else (required,))
                        if actual not in (*allowed, "var", "unknown"):
                            self._report(node.line, f"Funcao '{node.name}': esperado {required}, recebido {actual}.")
        elif isinstance(node, PropertyAccess):
            self.validate_node(node.object)
            obj_type = self._infer_type(node.object)
            cls = self._classes.get(obj_type)
            if cls and node.property_name not in cls.attributes:
                self._report(node.line, f"Atributo '{node.property_name}' nao declarado em '{obj_type}'.")
        elif isinstance(node, PropertyAssign):
            self.validate_node(node.object)
            self.validate_node(node.value)
            obj_type = self._infer_type(node.object)
            cls = self._classes.get(obj_type)
            if cls and node.property_name not in cls.attributes:
                self._report(node.line, f"Atributo '{node.property_name}' nao declarado em '{obj_type}'.")
        elif isinstance(node, NewExpr):
            if node.class_name not in self._classes:
                self._report(node.line, f"Classe '{node.class_name}' nao declarada.")
            for arg in node.arguments: self.validate_node(arg)
            if self._isolated and node.class_name in self._class_initializers:
                self._check_function(self._class_initializers[node.class_name], (), True, node.class_name)
        elif isinstance(node, ThisExpr):
            if self._isolated and self._current_class is None:
                self._report(node.line, "FJ-SEM-05: tarefa global nao pode capturar this.")
        elif isinstance(node, InputExpr):
            if node.prompt: self.validate_node(node.prompt)

    def analyze(self, program: Program) -> bool:
        self._collect_declarations(program)
        self._fj_enabled = find_fork_join(program) is not None
        self._global_symbols = dict(self._functions)
        for stmt in program.statements:
            if isinstance(stmt, VarDecl):
                kind = stmt.type if stmt.type != "var" else self._infer_type(stmt.init_value)
                self._global_symbols[stmt.name] = Symbol(stmt.name, kind)
        for stmt in program.statements: self.validate_node(stmt)
        return not self._has_errors
