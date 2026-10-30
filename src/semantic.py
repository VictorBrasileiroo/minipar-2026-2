from __future__ import annotations
import sys
from dataclasses import dataclass, field, replace
from typing import Dict, List, Optional
from ast_nodes import (
    ASTNode, Program, VarDecl, Assignment, PrintStmt, IdentifierExpr, BinaryExpr,
    UnaryExpr, NumberExpr, StringExpr, BoolExpr, SeqBlock, ParBlock, IfStmt, WhileStmt,
    DoWhileStmt, ForStmt, BreakStmt, ContinueStmt, InputExpr,
    ClassDecl, FuncDecl, ReturnStmt, MethodCall, FuncCallExpr, PropertyAccess, PropertyAssign, NewExpr, ThisExpr,
    CChannelExpr, SendStmt, ReceiveExpr, ListLiteral, MatrixCreateExpr, IndexExpr, IndexAssign,
    ForkExpr, JoinExpr, find_fork_join, iter_child_nodes
)

@dataclass(frozen=True)
class ValueType:
    """Informacao parcial para a fronteira de tarefas; unknown nao e prova de tipo."""
    kind: str = "unknown"
    elements: tuple[ValueType, ...] = ()
    result: Optional[ValueType] = None

    def __post_init__(self) -> None:
        # elements describes possible types, never positions or cardinality.
        # Keep every distinct alternative (including unknown/forbidden types),
        # in first-seen order, without coarsening any contextual cache key.
        if len(self.elements) > 1:
            object.__setattr__(self, "elements", tuple(dict.fromkeys(self.elements)))

@dataclass
class Symbol:
    name: str
    type: str
    params: List[str] = field(default_factory=list)
    attributes: Dict[str, str] = field(default_factory=dict)
    methods: Dict[str, List[str]] = field(default_factory=dict)
    value_type: Optional[ValueType] = None

NATIVE_FUNCTIONS = frozenset(("exp", "random", "range", "len", "to_number", "parse_ints", "substr", "to_string"))

class SemanticAnalyzer:
    def __init__(self) -> None:
        self._scopes: List[Dict[str, Symbol]] = []
        self._has_errors = False
        self._current_function: Optional[str] = None
        self._current_class: Optional[str] = None
        self._classes: Dict[str, Symbol] = {}
        self._superclasses: Dict[str, str] = {}
        self._functions: Dict[str, Symbol] = {}
        self._loop_depth = 0
        self.expression_types: Dict[int, ValueType] = {}
        # Contextos especializados permanecem separados: um no pode ter tipos
        # distintos em chamadas diferentes. Nao mesclar no mapa do chamador.
        self.function_contexts = {}
        self.analyzed_program = None
        self.fork_signatures: Dict[int, list[tuple[tuple[ValueType, ...], ValueType]]] = {}
        self.unresolved_fj: List[str] = []
        self._function_nodes: Dict[str, FuncDecl] = {}
        self._class_nodes: Dict[str, ClassDecl] = {}
        self._class_initializers: Dict[str, FuncDecl] = {}
        self._global_symbols: Dict[str, Symbol] = {}
        self._isolated = False
        self._fj_enabled = False
        self._checking_functions = set()
        self._function_cache = {}
        self._specialized = False
        self._fj_functions = set()
        self._fj_diagnostics = set()
        self._provisional_signatures = {}
        self._provisional_context = False
        self._class_chains = {}
        self._return_types: Optional[List[ValueType]] = None
        self._enter_scope()

    def _enter_scope(self) -> None: self._scopes.append({})
    def _exit_scope(self) -> None:
        if len(self._scopes) > 1: self._scopes.pop()

    def _get_context(self) -> str:
        return f" (Funcao: {self._current_function})" if self._current_function else ""

    def _define_symbol(self, name: str, type_: str, line: int, params: Optional[List[str]] = None) -> None:
        if name in self._scopes[-1]:
            self._report(line, f"Variavel '{name}' ja declarada.")
        else: self._scopes[-1][name] = Symbol(name=name, type=type_, params=params or [])

    def _lookup(self, name: str) -> Optional[Symbol]:
        for scope in reversed(self._scopes):
            if name in scope: return scope[name]
        return None

    def _report(self, line: int, message: str) -> None:
        # A passada normal e a unica fonte de diagnosticos ordinarios.
        if self._specialized and not message.startswith("FJ-"): return
        if message.startswith("FJ-"):
            key = (line, self._current_class, self._current_function, message)
            if key in self._fj_diagnostics: return
            self._fj_diagnostics.add(key)
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
            if sym and sym.value_type and (self._specialized or sym.value_type.kind == "task"):
                return sym.value_type.kind
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
            attrs = self._attributes_for(obj_type)
            if node.property_name in attrs: return attrs[node.property_name]
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
        if declared in ("var", "unknown") or actual in ("var", "unknown"): return True
        if declared == "int" and actual == "number": return True
        if declared == "number" and actual == "int": return True
        return declared == actual

    def _index_object_type(self, node: ASTNode) -> str:
        # Resolve inherited attributes for the index guard without changing
        # the existing general member/type inference policy.
        if isinstance(node, PropertyAccess):
            owner = self._infer_type(node.object)
            seen = set()
            while owner in self._classes and owner not in seen:
                seen.add(owner)
                attrs = self._classes[owner].attributes
                if node.property_name in attrs:
                    return attrs[node.property_name]
                owner = self._superclasses.get(owner)
        return self._infer_type(node)

    def _collect_declarations(self, program: Program) -> None:
        for stmt in program.statements:
            if isinstance(stmt, FuncDecl):
                if stmt.name in NATIVE_FUNCTIONS:
                    self._report(stmt.line, f"Nome nativo reservado: '{stmt.name}'.")
                self._functions[stmt.name] = Symbol(stmt.name, "FUNC", params=stmt.params)
                self._function_nodes[stmt.name] = stmt
            elif isinstance(stmt, ClassDecl):
                self._class_nodes[stmt.name] = stmt
                self._class_initializers[stmt.name] = FuncDecl(
                    "<inicializacao>", [], SeqBlock(stmt.attributes), line=stmt.line)
                self._superclasses[stmt.name] = stmt.superclass
                attrs = {a.name: self._infer_type(a.init_value) if a.type == "var" else a.type
                         for a in stmt.attributes}
                methods = {m.name: m.params for m in stmt.methods}
                self._classes[stmt.name] = Symbol(stmt.name, "CLASS", attributes=attrs, methods=methods)

    def _class_chain(self, name: str) -> tuple[str, ...]:
        if name in self._class_chains: return self._class_chains[name]
        chain = []
        current = name
        while current in self._class_nodes:
            if current in chain:
                self._report(self._class_nodes[current].line, f"Heranca ciclica em '{current}'.")
                break
            chain.append(current)
            current = self._class_nodes[current].superclass
        self._class_chains[name] = tuple(chain)
        return tuple(chain)

    def _attributes_for(self, name: str) -> Dict[str, str]:
        attrs = {}
        for owner in reversed(self._class_chain(name)):
            attrs.update(self._classes[owner].attributes)
        return attrs

    def _method_for(self, name: str, method_name: str):
        for owner in self._class_chain(name):
            method = next((m for m in self._class_nodes[owner].methods if m.name == method_name), None)
            if method: return owner, method
        return None, None

    def _collect_fj_functions(self) -> None:
        # Somente funcoes que contem FJ ou chamam essas funcoes exigem
        # especializacao fora das tarefas. O fecho das tarefas e percorrido isolado.
        nodes = list(self._function_nodes.values())
        nodes += [m for cls in self._class_nodes.values() for m in cls.methods]
        edges = {}
        by_name = {}
        for function in nodes:
            by_name.setdefault(function.name, set()).add(id(function))
            if find_fork_join(function.body) is not None:
                self._fj_functions.add(id(function))
            pending, calls = [function.body], set()
            while pending:
                node = pending.pop()
                if isinstance(node, FuncCallExpr): calls.add(node.name)
                if isinstance(node, MethodCall): calls.add(node.method_name)
                pending.extend(iter_child_nodes(node))
            edges[id(function)] = calls
        changed = True
        while changed:
            changed = False
            for function, calls in edges.items():
                if function not in self._fj_functions and any(
                        by_name.get(name, set()) & self._fj_functions for name in calls):
                    self._fj_functions.add(function)
                    changed = True

    def _value_type(self, node: Optional[ASTNode], resolve_calls: bool = False) -> ValueType:
        if node is None: return ValueType("void")
        if isinstance(node, IdentifierExpr):
            symbol = self._lookup(node.name)
            if symbol: return symbol.value_type or ValueType(symbol.type)
        if isinstance(node, ListLiteral):
            return ValueType("list", tuple(self._value_type(e, resolve_calls) for e in node.elements))
        if isinstance(node, BinaryExpr) and node.op == "+":
            left, right = self._value_type(node.left, resolve_calls), self._value_type(node.right, resolve_calls)
            if left.kind == right.kind == "list":
                return ValueType("list", left.elements + right.elements)
        if resolve_calls and isinstance(node, FuncCallExpr) and node.name in self._function_nodes:
            function = self._function_nodes[node.name]
            if len(function.params) == len(node.arguments):
                info = self._check_function(function, tuple(self._value_type(a, True) for a in node.arguments), self._isolated)
                self.expression_types[id(node)] = info
                return info
        if resolve_calls and isinstance(node, MethodCall):
            owner, method = self._method_for(self._infer_type(node.object), node.method_name)
            if method and len(method.params) == len(node.arguments):
                info = self._check_function(method, tuple(self._value_type(a, True) for a in node.arguments), self._isolated, owner)
                self.expression_types[id(node)] = info
                return info
        if isinstance(node, MatrixCreateExpr):
            return ValueType("matrix", (self._value_type(node.init_value),))
        if isinstance(node, IndexExpr):
            collection = self._value_type(node.object, resolve_calls)
            if collection.kind == "matrix":
                # matrix(r,c,v)[i] e uma linha; so o proximo indice e celula.
                return ValueType("list", collection.elements)
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
    def _contains_task(info: ValueType) -> bool:
        return info.kind == "task" or any(SemanticAnalyzer._contains_task(e) for e in info.elements)

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
            old = (symbol.value_type or ValueType(symbol.type)) if symbol else ValueType()
            if symbol and old.kind in ("list", "matrix"):
                # Listas MiniPar sao valores copiados, inclusive em atribuicoes.
                symbol.value_type = ValueType(old.kind, tuple(dict.fromkeys(old.elements + infos)))

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
        # Inclui assinatura, isolamento, dono e estado de tipos globais no contexto.
        globals_key = tuple((n, sym.type, sym.value_type) for n, sym in sorted(self._global_symbols.items()))
        provisional = self._provisional_context or (self._current_function is not None and not self._specialized)
        key = (id(function), arguments, isolated, owner, globals_key, provisional)
        if key in self._function_cache: return self._function_cache[key]
        active = (id(function), isolated, owner)
        if active in self._checking_functions:
            note = f"Linha {function.line}: retorno recursivo de {function.name} nao comprovado."
            if note not in self.unresolved_fj: self.unresolved_fj.append(note)
            return ValueType()
        self._checking_functions.add(active)
        saved = (self._scopes, self._current_function, self._current_class,
                 self._isolated, self._return_types, self._loop_depth, self.expression_types,
                 self._specialized, self._provisional_context)
        self.expression_types = {}
        self._scopes = [{n: replace(sym) for n, sym in self._global_symbols.items()}]
        self._current_function, self._current_class = function.name, owner
        self._isolated, self._return_types, self._loop_depth = isolated, [], 0
        self._specialized = True
        self._provisional_context = provisional
        try:
            if owner:
                self._enter_scope()
                attrs = self._attributes_for(owner)
                if function is self._class_initializers.get(owner):
                    # Atributos proprios entram na ordem de inicializacao, sem
                    # permitir que descendentes escondam acessos de ancestrais.
                    attrs = {n: t for n, t in attrs.items() if n not in self._classes[owner].attributes}
                for name, kind in attrs.items():
                    self._define_symbol(name, kind, function.line)
            self._enter_scope()
            for name, info in zip(function.params, arguments):
                self._define_symbol(name, info.kind, function.line)
                self._lookup(name).value_type = info
            self.validate_node(function.body, value_required=False)
            result = self._merge_value_types(tuple(self._return_types)) if self._return_types else ValueType("void")
            self._function_cache[key] = result
            self.function_contexts[key] = dict(self.expression_types)
            return result
        finally:
            (self._scopes, self._current_function, self._current_class,
             self._isolated, self._return_types, self._loop_depth, self.expression_types,
             self._specialized, self._provisional_context) = saved
            self._checking_functions.remove(active)

    def _validate_fork(self, node: ForkExpr) -> None:
        for arg in node.arguments: self.validate_node(arg)
        self.validate_node(node.destination)
        if node.destination and self._value_type(node.destination, True).kind not in ("string", "var", "unknown"):
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
        arguments = tuple(self._value_type(arg, True) for arg in node.arguments)
        for info in arguments: self._check_transport(info, node.line, "argumento")
        result = self._check_function(function, arguments, isolated=True)
        self._check_transport(result, node.line, "retorno")
        self.expression_types[id(node)] = ValueType("task", result=result)
        signature = (arguments, result)
        provisional = self._provisional_context or (self._current_function is not None and not self._specialized)
        table = self._provisional_signatures if provisional else self.fork_signatures
        signatures = table.setdefault(id(node), [])
        if signature not in signatures: signatures.append(signature)

    def _validate_join(self, node: JoinExpr, value_required: bool) -> None:
        self.validate_node(node.handle)
        self.validate_node(node.timeout)
        handle = self._value_type(node.handle, True)
        if handle.kind != "task":
            if handle.kind in ("var", "unknown"):
                alternatives = list(handle.elements)
                while alternatives:
                    info = alternatives.pop()
                    if info.kind in ("var", "unknown"):
                        alternatives.extend(info.elements)
                    elif info.kind != "task":
                        self._report(node.line, f"FJ-SEM-03: join pode receber tipo conhecido {info.kind}, diferente de task.")
                note = f"Linha {node.line}: join generico depende do tipo do argumento na chamada."
                if note not in self.unresolved_fj: self.unresolved_fj.append(note)
            else:
                self._report(node.line, f"FJ-SEM-03: join exige handle task reconhecido, recebeu {handle.kind}.")
        if node.timeout and self._value_type(node.timeout, True).kind not in ("number", "int", "var", "unknown"):
            self._report(node.line, "FJ-SEM-04: timeout de join deve ser numerico.")
        result = handle.result or ValueType()
        self.expression_types[id(node)] = result
        if value_required and result.kind == "void":
            self._report(node.line, "FJ-SEM-08: join com resultado none so pode ser comando isolado.")

    def validate_node(self, node: ASTNode, value_required: bool = True) -> None:
        if node is None: return

        if isinstance(node, ForkExpr):
            self._validate_fork(node)
            if not value_required:
                self._report(node.line, "FJ-SEM-07: handle de fork descartado; guarde-o para join.")
        elif isinstance(node, JoinExpr):
            self._validate_join(node, value_required)
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
        elif isinstance(node, PrintStmt):
            for arg in node.arguments: self.validate_node(arg)
        elif isinstance(node, SendStmt):
            if self._isolated: self._report(node.line, "FJ-SEM-05: send nao permitido em tarefa v1.")
            self.validate_node(node.channel)
            self.validate_node(node.message)
        elif isinstance(node, CChannelExpr):
            if self._isolated: self._report(node.line, "FJ-SEM-05: c_channel nao permitido em tarefa v1.")
            self.validate_node(node.ip)
            self.validate_node(node.port)
        elif isinstance(node, ReceiveExpr):
            if self._isolated: self._report(node.line, "FJ-SEM-05: receive nao permitido em tarefa v1.")
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
            if self._index_object_type(node.object) == "string":
                self._report(node.line, "Indexacao de string nao suportada; use substr(s, i, 1).")
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
            for stmt in node.statements: self.validate_node(stmt, value_required=False)
            self._exit_scope()
        elif isinstance(node, IfStmt):
            self.validate_node(node.condition)
            self.validate_node(node.then_branch, value_required=False)
            if node.else_branch: self.validate_node(node.else_branch, value_required=False)
        elif isinstance(node, WhileStmt):
            self.validate_node(node.condition)
            self._loop_depth += 1
            self.validate_node(node.body, value_required=False)
            self._loop_depth -= 1
        elif isinstance(node, DoWhileStmt):
            self._loop_depth += 1
            self.validate_node(node.body, value_required=False)
            self._loop_depth -= 1
            self.validate_node(node.condition)
        elif isinstance(node, ForStmt):
            self._enter_scope()
            if node.iterator_name:
                self.validate_node(node.iterable)
                self._define_symbol(node.iterator_name, "var", node.line)
                collection = self._value_type(node.iterable, True)
                self._lookup(node.iterator_name).value_type = self._merge_value_types(collection.elements)
            else:
                self.validate_node(node.initializer, value_required=False)
                self.validate_node(node.condition)
                self.validate_node(node.increment, value_required=False)
            self._loop_depth += 1
            self.validate_node(node.body, value_required=False)
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
            owner, method = self._method_for(obj_type, node.method_name)
            if cls and method is None:
                self._report(node.line, f"Metodo '{node.method_name}' nao declarado em '{obj_type}'.")
            elif method and len(method.params) != len(node.arguments):
                self._report(node.line, f"Metodo '{node.method_name}' espera {len(method.params)} argumento(s), recebeu {len(node.arguments)}.")
            if (obj_type == "list" and node.method_name in ("append", "push_back")
                    and any(self._infer_type(arg) == "string" for arg in node.arguments)):
                self._report(node.line, "Listas de strings ainda nao suportadas (C-T11-v1 3.4).")
            if self._fj_enabled:
                collection_kind = self._value_type(node.object).kind
                if collection_kind == "list" and node.method_name in ("append", "push_back"):
                    self._extend_collection(node.object, tuple(self._value_type(a) for a in node.arguments))
                if collection_kind == "list" and node.method_name == "pop":
                    self.expression_types[id(node)] = self._merge_value_types(self._value_type(node.object).elements)
                if node.method_name == "size" and obj_type in ("list", "matrix", "string"):
                    self.expression_types[id(node)] = ValueType("number")
                if self._isolated and obj_type in ("var", "unknown"):
                    self._report(node.line, "FJ-SEM-05: nao e possivel comprovar isolamento de chamada de metodo sem tipo conhecido.")
                if method and len(method.params) == len(node.arguments) and (
                        self._specialized or id(method) in self._fj_functions
                        or any(self._contains_task(self._value_type(a)) for a in node.arguments)):
                    self.expression_types[id(node)] = self._check_function(
                        method, tuple(self._value_type(a, True) for a in node.arguments), self._isolated, owner)
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
                if len(function.params) == len(node.arguments) and (
                        self._specialized or id(function) in self._fj_functions
                        or any(self._contains_task(self._value_type(a)) for a in node.arguments)):
                    self.expression_types[id(node)] = self._check_function(
                        function, tuple(self._value_type(a, True) for a in node.arguments), self._isolated)
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
            if cls and node.property_name not in self._attributes_for(obj_type):
                self._report(node.line, f"Atributo '{node.property_name}' nao declarado em '{obj_type}'.")
        elif isinstance(node, PropertyAssign):
            self.validate_node(node.object)
            self.validate_node(node.value)
            obj_type = self._infer_type(node.object)
            cls = self._classes.get(obj_type)
            if cls and node.property_name not in self._attributes_for(obj_type):
                self._report(node.line, f"Atributo '{node.property_name}' nao declarado em '{obj_type}'.")
            elif cls and not self._types_compatible(self._attributes_for(obj_type)[node.property_name], self._infer_type(node.value)):
                self._report(node.line, f"Tipo incompativel em atribuicao do atributo '{node.property_name}'.")
        elif isinstance(node, NewExpr):
            if node.class_name not in self._classes:
                self._report(node.line, f"Classe '{node.class_name}' nao declarada.")
            for arg in node.arguments: self.validate_node(arg)
            if self._isolated:
                for owner in reversed(self._class_chain(node.class_name)):
                    self._check_function(self._class_initializers[owner], (), True, owner)
        elif isinstance(node, ThisExpr):
            if self._isolated and self._current_class is None:
                self._report(node.line, "FJ-SEM-05: tarefa global nao pode capturar this.")
        elif isinstance(node, InputExpr):
            if self._isolated: self._report(node.line, "FJ-SEM-05: input nao permitido em tarefa v1.")
            if node.prompt: self.validate_node(node.prompt)

    def analyze(self, program: Program) -> bool:
        self.analyzed_program = program
        self._collect_declarations(program)
        self._class_chains.clear()
        for name in self._class_nodes: self._class_chain(name)
        self._collect_fj_functions()
        self._fj_enabled = find_fork_join(program) is not None
        self._global_symbols = dict(self._functions)
        for stmt in program.statements:
            if isinstance(stmt, VarDecl):
                kind = stmt.type if stmt.type != "var" else self._infer_type(stmt.init_value)
                self._global_symbols[stmt.name] = Symbol(stmt.name, kind)
        for stmt in program.statements: self.validate_node(stmt, value_required=False)
        for node, signatures in self._provisional_signatures.items():
            if node not in self.fork_signatures: self.fork_signatures[node] = signatures
        return not self._has_errors


@dataclass(frozen=True)
class CppType:
    """Representacao concreta do backend, separada do number da linguagem."""
    kind: str
    item: Optional[CppType] = None

    def cpp(self):
        if self.kind == "list": return f"std::vector<{self.item.cpp()}>"
        return {"string": "std::string", "task": "minipar_rt::TaskHandle",
                "size": "std::size_t", "length": "std::ptrdiff_t"}.get(self.kind, self.kind)

    def transportable(self):
        return self.kind in ("int", "double", "size", "length", "bool", "string", "void") or (
            self.kind == "list" and self.item is not None and self.item.kind != "void" and self.item.transportable())


class CppProofError(ValueError):
    pass


class CppTaskContext:
    """Prova conservadora sobre a mesma AST ja validada, por assinatura C++.

    Nao altera ValueType nem a semantica de programas sem FJ. Cada contexto
    guarda seus mapas de nos/declaracoes, inclusive especializacoes de helpers.
    Uma representacao incerta e erro, nunca Value dinamico ou double por padrao.
    """
    def __init__(self, program, semantic, float_return):
        if semantic.analyzed_program is not program or semantic._has_errors:
            raise CppProofError("CORE-07 exige analise semantica valida da mesma AST")
        self.functions = {n.name: n for n in program.statements if isinstance(n, FuncDecl)}
        self.contexts = {}
        self.forks = {}
        self.active = set()
        self.float_return = float_return
        self.main = self.new_context()
        scopes = [{}]
        for node in program.statements:
            if not isinstance(node, FuncDecl): self.stmt(node, scopes, self.main, [])
        self.finish(self.main)
        seen = set(self.main["types"])
        for context in self.contexts.values(): seen.update(context["types"])
        pending = [program]
        while pending:
            node = pending.pop()
            if isinstance(node, ForkExpr) and id(node) not in seen:
                self.fail(node, "fork sem contexto concreto de chamada comprovado")
            pending.extend(iter_child_nodes(node))

    @staticmethod
    def new_context():
        return {"types": {}, "decls": {}, "bindings": [], "calls": {}, "result": CppType("void")}

    @staticmethod
    def fail(node, message):
        raise CppProofError(f"CORE-07 linha {node.line}: {message}")

    def lookup(self, node, scopes, name):
        for scope in reversed(scopes):
            if name in scope: return scope[name]
        self.fail(node, f"tipo nao comprovado de '{name}' (global/captura nao suportada)")

    def bind(self, scopes, ctx, name, typ, node):
        binding = [typ, node]
        scopes[-1][name] = binding
        ctx["bindings"].append(binding)
        return binding

    def unify(self, old, new, node):
        if old == new: return old
        if old.kind == new.kind == "list":
            if old.item is None: return new
            if new.item is None: return old
            return CppType("list", self.unify(old.item, new.item, node))
        self.fail(node, f"representacoes incompativeis: {old} e {new}")

    def finish(self, ctx):
        for typ, node in ctx["bindings"]:
            if typ.kind == "list" and typ.item is None:
                self.fail(node, "conteudo da lista vazia nao comprovado")
            ctx["decls"][id(node)] = typ
            if isinstance(node, VarDecl) and isinstance(node.init_value, ListLiteral):
                ctx["types"][id(node.init_value)] = typ

    def function(self, node, name, args):
        key = (name, args)
        if any(active[0] == name for active in self.active):
            self.fail(node, f"retorno recursivo de {name} nao comprovado")
        if key in self.contexts: return self.contexts[key]
        fn = self.functions.get(name)
        if fn is None or len(args) != len(fn.params): self.fail(node, f"assinatura desconhecida de {name}")
        if any(t.kind == "void" or (t.kind == "list" and t.item is None) for t in args):
            self.fail(node, f"argumentos nao comprovados de {name}")
        ctx, returns, scopes = self.new_context(), [], [{}]
        self.active.add(key)
        try:
            for param, typ in zip(fn.params, args): scopes[0][param] = [typ, fn]
            complete = self.stmt(fn.body, scopes, ctx, returns)
            values = [t for t in returns if t.kind != "void"]
            if values:
                if not complete or len(values) != len(returns):
                    self.fail(fn, f"retorno de {name} nao comprovado em todos os caminhos")
                result = values[0]
                # Preserva o retorno double ja escolhido pelo backend legado
                # quando ha divisao/literal decimal no corpo (operandos intactos).
                if all(t.kind in ("int", "double", "size", "length") for t in values) and self.float_return(fn.body):
                    result = CppType("double")
                else:
                    for typ in values[1:]: result = self.unify(result, typ, fn)
                ctx["result"] = result
            self.finish(ctx)
            self.contexts[key] = ctx
            return ctx
        finally:
            self.active.remove(key)

    def expr(self, node, scopes, ctx, required=True):
        if node is None: return CppType("void")
        typ = None
        if isinstance(node, NumberExpr):
            typ = CppType("double" if any(c in node.value.lower() for c in ".e") else "int")
            if typ.kind == "int" and not (-2147483648 <= int(node.value) <= 2147483647):
                self.fail(node, "literal inteiro fora da representacao int comprovada")
        elif isinstance(node, StringExpr): typ = CppType("string")
        elif isinstance(node, BoolExpr): typ = CppType("bool")
        elif isinstance(node, IdentifierExpr): typ = self.lookup(node, scopes, node.name)[0]
        elif isinstance(node, UnaryExpr):
            value = self.expr(node.operand, scopes, ctx)
            typ = CppType("bool") if node.op == "!" else value
        elif isinstance(node, BinaryExpr):
            left, right = self.expr(node.left, scopes, ctx), self.expr(node.right, scopes, ctx)
            if node.op in ("==", "!=", "<", ">", "<=", ">=", "&&", "||"): typ = CppType("bool")
            elif left.kind == right.kind == "string" and node.op == "+": typ = left
            elif left.kind in ("int", "double", "size", "length") and right.kind in ("int", "double", "size", "length"):
                if node.op in ("%", "^", "&", "|") and "double" in (left.kind, right.kind):
                    self.fail(node, "operacao inteira com decimal")
                typ = CppType(next((k for k in ("double", "size", "length") if k in (left.kind, right.kind)), "int"))
            else: self.fail(node, "operacao sem representacao concreta comprovada")
        elif isinstance(node, ListLiteral):
            items = [self.expr(n, scopes, ctx) for n in node.elements]
            # Listas numericas legadas sao vector<double>, inclusive inteiros.
            if items and all(t.kind in ("int", "double", "size", "length") for t in items): item = CppType("double")
            else:
                item = items[0] if items else None
                for t in items[1:]: item = self.unify(item, t, node)
            typ = CppType("list", item)
        elif isinstance(node, MatrixCreateExpr):
            self.expr(node.rows, scopes, ctx); self.expr(node.cols, scopes, ctx)
            typ = CppType("list", CppType("list", self.expr(node.init_value, scopes, ctx)))
        elif isinstance(node, IndexExpr):
            collection = self.expr(node.object, scopes, ctx)
            self.expr(node.index, scopes, ctx)
            if collection.kind != "list" or collection.item is None: self.fail(node, "indexacao sem elemento comprovado")
            typ = collection.item
        elif isinstance(node, ForkExpr):
            args = tuple(self.expr(a, scopes, ctx) for a in node.arguments)
            if any(not t.transportable() or t.kind == "void" for t in args): self.fail(node, "tipo proibido/nao comprovado no transporte")
            if node.destination and self.expr(node.destination, scopes, ctx).kind != "string": self.fail(node, "destino nao comprovado como string")
            result = self.function(node, node.function_name, args)["result"]
            if not result.transportable(): self.fail(node, "retorno proibido/nao comprovado no transporte")
            signature = (args, result)
            if node.function_name in self.forks and self.forks[node.function_name] != signature:
                self.fail(node, f"assinaturas de fork incompativeis para {node.function_name}")
            self.forks[node.function_name] = signature
            typ = CppType("task", result)
        elif isinstance(node, JoinExpr):
            handle = self.expr(node.handle, scopes, ctx)
            if handle.kind != "task" or handle.item is None: self.fail(node, "join sem handle/retorno comprovado")
            if node.timeout:
                if self.expr(node.timeout, scopes, ctx).kind not in ("int", "double", "size", "length"):
                    self.fail(node, "timeout nao comprovado como numero")
            typ = handle.item
        elif isinstance(node, FuncCallExpr):
            args = tuple(self.expr(a, scopes, ctx) for a in node.arguments)
            if node.name in self.functions:
                callee = self.function(node, node.name, args)
                ctx["calls"][id(node)] = (node.name, args)
                typ = callee["result"]
            else:
                typ = {"exp": CppType("double"), "random": CppType("double"), "to_number": CppType("double"),
                       "len": CppType("length"), "substr": CppType("string"), "to_string": CppType("string"),
                       "range": CppType("list", CppType("int")), "parse_ints": CppType("list", CppType("double"))}.get(node.name)
        elif isinstance(node, MethodCall):
            obj = self.expr(node.object, scopes, ctx)
            args = [self.expr(a, scopes, ctx) for a in node.arguments]
            if node.method_name in ("append", "push_back") and obj.kind == "list" and len(args) == 1:
                if obj.item is None:
                    if not isinstance(node.object, IdentifierExpr): self.fail(node, "append sem armazenamento comprovado")
                    binding = self.lookup(node, scopes, node.object.name)
                    binding[0] = CppType("list", CppType("double") if args[0].kind in ("int", "double") else args[0])
                elif obj.item.kind in ("int", "double") and args[0].kind in ("int", "double"): pass
                else: self.unify(obj.item, args[0], node)
                typ = CppType("void")
            elif node.method_name == "pop" and obj.kind == "list" and obj.item: typ = obj.item
            elif node.method_name == "size" and obj.kind in ("list", "string"): typ = CppType("size")
        elif isinstance(node, PropertyAccess) and node.property_name == "size":
            self.expr(node.object, scopes, ctx); typ = CppType("size")
        elif isinstance(node, InputExpr):
            if node.prompt: self.expr(node.prompt, scopes, ctx)
            typ = CppType("string")
        if typ is None: self.fail(node, f"tipo/construcao nao comprovado: {type(node).__name__}")
        if required and typ.kind == "void": self.fail(node, "none so pode ser comando isolado")
        ctx["types"][id(node)] = typ
        return typ

    def stmt(self, node, scopes, ctx, returns):
        if node is None: return False
        if isinstance(node, VarDecl):
            if node.init_value is None and node.type == "var": self.fail(node, "variavel sem tipo/inicializador comprovado")
            typ = self.expr(node.init_value, scopes, ctx) if node.init_value else CppType("string" if node.type == "string" else "int")
            self.bind(scopes, ctx, node.name, typ, node)
        elif isinstance(node, Assignment):
            binding = self.lookup(node, scopes, node.name)
            value = self.expr(node.value, scopes, ctx)
            if binding[0].kind in ("int", "double", "size", "length") and value.kind in ("int", "double", "size", "length"): pass
            else: binding[0] = self.unify(binding[0], value, node)
        elif isinstance(node, IndexAssign):
            root = node.target.object
            while isinstance(root, IndexExpr): root = root.object
            if not isinstance(root, IdentifierExpr): self.fail(node, "atribuicao por indice exige armazenamento comprovado")
            target = self.expr(node.target, scopes, ctx); value = self.expr(node.value, scopes, ctx)
            if not (target.kind in ("int", "double") and value.kind in ("int", "double")): self.unify(target, value, node)
        elif isinstance(node, PrintStmt):
            for arg in node.arguments: self.expr(arg, scopes, ctx)
        elif isinstance(node, ReturnStmt):
            returns.append(self.expr(node.value, scopes, ctx) if node.value else CppType("void"))
            return True
        elif isinstance(node, (SeqBlock, ParBlock)):
            scopes.append({})
            complete = False
            # par returns pertencem a lambda da branch, nao a funcao externa.
            branch_returns = [] if isinstance(node, ParBlock) else returns
            for stmt in node.statements:
                done = self.stmt(stmt, scopes, ctx, branch_returns)
                complete = complete or done
            scopes.pop()
            return complete if isinstance(node, SeqBlock) else False
        elif isinstance(node, IfStmt):
            self.expr(node.condition, scopes, ctx)
            left = self.stmt(node.then_branch, scopes, ctx, returns)
            right = self.stmt(node.else_branch, scopes, ctx, returns)
            return left and right
        elif isinstance(node, (ForStmt, WhileStmt, DoWhileStmt)):
            scopes.append({})
            if isinstance(node, ForStmt):
                if node.iterator_name:
                    collection = self.expr(node.iterable, scopes, ctx)
                    if collection.kind != "list" or collection.item is None: self.fail(node, "for-in sem elemento comprovado")
                    self.bind(scopes, ctx, node.iterator_name, collection.item, node)
                else:
                    self.stmt(node.initializer, scopes, ctx, returns)
                    self.expr(node.condition, scopes, ctx)
                    self.stmt(node.increment, scopes, ctx, returns)
            else: self.expr(node.condition, scopes, ctx)
            self.stmt(node.body, scopes, ctx, returns)
            scopes.pop()
            return False  # laços nunca provam retorno total
        elif isinstance(node, (BreakStmt, ContinueStmt)): pass
        else: self.expr(node, scopes, ctx, required=False)
        return False
