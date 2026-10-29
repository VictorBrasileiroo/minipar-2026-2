from __future__ import annotations
import os
import json
from typing import Optional
from ast_nodes import (
    ASTNode, Program, VarDecl, Assignment, PrintStmt, SeqBlock, ParBlock, BinaryExpr,
    UnaryExpr, NumberExpr, StringExpr, BoolExpr, IdentifierExpr, IfStmt, WhileStmt,
    DoWhileStmt, ForStmt, BreakStmt, ContinueStmt, InputExpr,
    ClassDecl, FuncDecl, ReturnStmt, MethodCall, FuncCallExpr, PropertyAccess, PropertyAssign, NewExpr, ThisExpr,
    CChannelExpr, SendStmt, ReceiveExpr, ListLiteral, MatrixCreateExpr, IndexExpr, IndexAssign,
    ForkExpr, JoinExpr, iter_child_nodes, find_fork_join
)


class TACGenerator:
    """Textual AST lowering; concurrent op semantics are documented in CORE-06's handoff."""
    def __init__(self) -> None:
        self.lines: list[str] = []
        self.temp_count = 0
        self.label_count = 0
        self.break_stack: list[str] = []
        self.continue_stack: list[str] = []
        self.reserved: set[str] = set()
        self.has_fork_join = False

    def _temp(self) -> str:
        while True:
            name = f"t{self.temp_count}"
            self.temp_count += 1
            if name not in self.reserved:
                break
        return name

    def _label(self, prefix: str) -> str:
        while True:
            name = f"{prefix}_{self.label_count}"
            self.label_count += 1
            if name not in self.reserved:
                break
        return name

    def _emit(self, line: str = "") -> None:
        self.lines.append(line)

    def _save(self, value: str, operation: str = "") -> str:
        tmp = self._temp()
        self._emit(f"{tmp} = {operation}{value}")
        return tmp

    def _has_effect(self, node: ASTNode) -> bool:
        if isinstance(node, (FuncCallExpr, MethodCall, ForkExpr, JoinExpr,
                             InputExpr, ReceiveExpr, CChannelExpr, NewExpr)):
            return True
        return any(self._has_effect(child) for child in iter_child_nodes(node))

    def _arguments(self, arguments: list[ASTNode]) -> list[str]:
        # Finish nested calls before opening the caller's param sequence.
        values = []
        for arg in arguments:
            value = self._expr(arg)
            values.append(self._save(value) if isinstance(arg, IdentifierExpr) else value)
        return values

    def _join(self, node: JoinExpr, value_required: bool) -> str:
        if node.handle is None:
            raise NotImplementedError("TAC: join sem handle")
        handle = self._expr(node.handle)
        # A timeout expression can change the original handle variable.
        if node.timeout is not None:
            handle = self._save(handle)
        timeout = f", timeout {self._expr(node.timeout)}" if node.timeout is not None else ""
        instruction = f"join {handle}{timeout}"
        if value_required:
            return self._save(instruction)
        self._emit(instruction)
        return ""

    def _par(self, node: ParBlock) -> None:
        region = self._label("PAR")
        barrier = self._label("PAR_WAIT")
        branches = [self._label("PAR_BRANCH") for _ in node.statements]
        self._emit(f"par_begin {region}, {len(branches)}")
        for index, label in enumerate(branches):
            self._emit(f"par_spawn {region}, {index}, {label}")
        self._emit(f"goto {barrier}")
        for index, (label, stmt) in enumerate(zip(branches, node.statements)):
            self._emit(f"{label}:")
            self._emit(f"par_branch {region}, {index}")
            outer_break, outer_continue = self.break_stack, self.continue_stack
            self.break_stack, self.continue_stack = [], []
            try:
                self._stmt(stmt)
            finally:
                self.break_stack, self.continue_stack = outer_break, outer_continue
            # Terminal in the branch context: never falls into the next body.
            self._emit(f"par_end_branch {region}, {index}")
        self._emit(f"{barrier}:")
        self._emit(f"par_barrier {region}")
        self._emit(f"par_end {region}")

    def _expr(self, node: Optional[ASTNode]) -> str:
        if node is None:
            raise NotImplementedError("TAC: expressao ausente")
        if isinstance(node, NumberExpr): return node.value
        if isinstance(node, StringExpr): return json.dumps(node.value, ensure_ascii=False)
        if isinstance(node, BoolExpr): return "true" if node.value else "false"
        if isinstance(node, IdentifierExpr): return node.name
        if isinstance(node, ThisExpr): return "this"
        if isinstance(node, ForkExpr):
            if not node.function_name or any(arg is None for arg in node.arguments):
                raise NotImplementedError("TAC: fork invalido")
            # capture is a value snapshot, recursively copying transportable lists.
            args = [self._save(self._expr(arg), "capture ") for arg in node.arguments]
            destination = '"local"' if node.destination is None else self._save(self._expr(node.destination))
            return self._save(f"fork {node.function_name}({', '.join(args)}) on {destination}")
        if isinstance(node, JoinExpr):
            return self._join(node, True)
        if isinstance(node, UnaryExpr):
            value = self._expr(node.operand)
            tmp = self._temp()
            self._emit(f"{tmp} = {node.op}{value}")
            return tmp
        if isinstance(node, BinaryExpr):
            left = self._expr(node.left)
            if node.op in ("&&", "||"):
                tmp, end = self._temp(), self._label("BOOL_END")
                self._emit(f"{tmp} = {'false' if node.op == '&&' else 'true'}")
                self._emit(f"{'ifFalse' if node.op == '&&' else 'if'} {left} goto {end}")
                right = self._expr(node.right)
                self._emit(f"{tmp} = !!{right}")
                self._emit(f"{end}:")
                return tmp
            if isinstance(node.left, IdentifierExpr) and self._has_effect(node.right):
                left = self._save(left)
            right = self._expr(node.right)
            tmp = self._temp()
            self._emit(f"{tmp} = {left} {node.op} {right}")
            return tmp
        if isinstance(node, ListLiteral):
            tmp = self._temp()
            values = ", ".join(self._arguments(node.elements))
            self._emit(f"{tmp} = [{values}]")
            return tmp
        if isinstance(node, MatrixCreateExpr):
            tmp = self._temp()
            values = self._arguments([node.rows, node.cols, node.init_value])
            self._emit(f"{tmp} = matrix({', '.join(values)})")
            return tmp
        if isinstance(node, IndexExpr):
            tmp = self._temp()
            self._emit(f"{tmp} = {self._expr(node.object)}[{self._expr(node.index)}]")
            return tmp
        if isinstance(node, PropertyAccess):
            tmp = self._temp()
            self._emit(f"{tmp} = {self._expr(node.object)}.{node.property_name}")
            return tmp
        if isinstance(node, (FuncCallExpr, MethodCall)):
            args = node.arguments
            name = node.name if isinstance(node, FuncCallExpr) else f"{self._expr(node.object)}.{node.method_name}"
            values = self._arguments(args)
            for value in values:
                self._emit(f"param {value}")
            tmp = self._temp()
            self._emit(f"{tmp} = call {name}, {len(args)}")
            return tmp
        if isinstance(node, NewExpr):
            if node.arguments:
                raise NotImplementedError("TAC: argumentos de construtor ainda nao representados")
            tmp = self._temp()
            self._emit(f"{tmp} = new {node.class_name}")
            return tmp
        if isinstance(node, CChannelExpr):
            tmp = self._temp()
            self._emit(f"{tmp} = c_channel({self._expr(node.ip)}, {self._expr(node.port)})")
            return tmp
        if isinstance(node, ReceiveExpr):
            tmp = self._temp()
            self._emit(f"{tmp} = receive {self._expr(node.channel)}")
            return tmp
        if isinstance(node, InputExpr):
            tmp = self._temp()
            if node.prompt:
                self._emit(f"{tmp} = input({self._expr(node.prompt)})")
            else:
                self._emit(f"{tmp} = input()")
            return tmp
        raise NotImplementedError(f"TAC: expressao nao suportada: {type(node).__name__}")

    def _stmt(self, node: Optional[ASTNode]) -> None:
        if node is None: return
        if isinstance(node, VarDecl):
            self._emit(f"{node.name} = {self._expr(node.init_value) if node.init_value is not None else '0'}")
        elif isinstance(node, Assignment):
            self._emit(f"{node.name} = {self._expr(node.value)}")
        elif isinstance(node, PropertyAssign):
            self._emit(f"{self._expr(node.object)}.{node.property_name} = {self._expr(node.value)}")
        elif isinstance(node, IndexAssign):
            self._emit(f"{self._expr(node.target.object)}[{self._expr(node.target.index)}] = {self._expr(node.value)}")
        elif isinstance(node, PrintStmt):
            for arg in node.arguments:
                self._emit(f"print {self._expr(arg)}")
        elif isinstance(node, SendStmt):
            self._emit(f"send {self._expr(node.channel)}, {self._expr(node.message)}")
        elif isinstance(node, SeqBlock):
            for stmt in node.statements: self._stmt(stmt)
        elif isinstance(node, ParBlock):
            self._par(node)
        elif isinstance(node, IfStmt):
            end = self._label("ENDIF")
            else_label = self._label("ELSE") if node.else_branch else end
            self._emit(f"ifFalse {self._expr(node.condition)} goto {else_label}")
            self._stmt(node.then_branch)
            if node.else_branch:
                self._emit(f"goto {end}")
                self._emit(f"{else_label}:")
                self._stmt(node.else_branch)
            self._emit(f"{end}:")
        elif isinstance(node, WhileStmt):
            start, end = self._label("WHILE"), self._label("ENDWHILE")
            self.break_stack.append(end); self.continue_stack.append(start)
            self._emit(f"{start}:")
            self._emit(f"ifFalse {self._expr(node.condition)} goto {end}")
            self._stmt(node.body)
            self._emit(f"goto {start}")
            self._emit(f"{end}:")
            self.break_stack.pop(); self.continue_stack.pop()
        elif isinstance(node, DoWhileStmt):
            start, condition, end = self._label("DO"), self._label("DO_TEST"), self._label("ENDDO")
            self.break_stack.append(end); self.continue_stack.append(condition)
            self._emit(f"{start}:")
            self._stmt(node.body)
            self._emit(f"{condition}:")
            self._emit(f"if {self._expr(node.condition)} goto {start}")
            self._emit(f"{end}:")
            self.break_stack.pop(); self.continue_stack.pop()
        elif isinstance(node, ForStmt):
            if node.iterator_name:
                iterator = self._save(self._expr(node.iterable), "iter_begin ")
                start, step, end = self._label("FOR_IN"), self._label("FOR_STEP"), self._label("ENDFOR")
                self.break_stack.append(end); self.continue_stack.append(step)
                self._emit(f"{start}:")
                condition = self._save(iterator, "iter_has_next ")
                self._emit(f"ifFalse {condition} goto {end}")
                value = self._save(iterator, "iter_value ")
                self._emit(f"{node.iterator_name} = {value}")
                self._stmt(node.body)
                self._emit(f"{step}:")
                self._emit(f"iter_next {iterator}")
                self._emit(f"goto {start}")
                self._emit(f"{end}:")
                self.break_stack.pop(); self.continue_stack.pop()
                return
            start, step, end = self._label("FOR"), self._label("FOR_STEP"), self._label("ENDFOR")
            self._stmt(node.initializer)
            self.break_stack.append(end); self.continue_stack.append(step)
            self._emit(f"{start}:")
            if node.condition:
                self._emit(f"ifFalse {self._expr(node.condition)} goto {end}")
            self._stmt(node.body)
            self._emit(f"{step}:")
            self._stmt(node.increment)
            self._emit(f"goto {start}")
            self._emit(f"{end}:")
            self.break_stack.pop(); self.continue_stack.pop()
        elif isinstance(node, BreakStmt):
            if not self.break_stack:
                raise NotImplementedError("TAC: break sem laco na branch atual")
            self._emit(f"goto {self.break_stack[-1]}")
        elif isinstance(node, ContinueStmt):
            if not self.continue_stack:
                raise NotImplementedError("TAC: continue sem laco na branch atual")
            self._emit(f"goto {self.continue_stack[-1]}")
        elif isinstance(node, ReturnStmt):
            self._emit(f"return {self._expr(node.value)}" if node.value else "return")
        elif isinstance(node, (FuncCallExpr, MethodCall)):
            self._expr(node)
        elif isinstance(node, JoinExpr):
            self._join(node, False)
        elif isinstance(node, ForkExpr):
            raise NotImplementedError("TAC: fork descartado; requer handle (FJ-SEM-07)")
        elif isinstance(node, ClassDecl):
            # Legacy class metadata does not lower deferred field initializers.
            # In an FJ program, calls here could hide a transitive fork/join too.
            if self.has_fork_join and any(attr.init_value is not None and self._has_effect(attr.init_value)
                                          for attr in node.attributes):
                raise NotImplementedError("TAC: inicializador Fork/Join de atributo ainda nao representado")
            self._emit(f"# class {node.name}")
            for method in node.methods: self._stmt(method)
        elif isinstance(node, FuncDecl):
            self._emit(f"func {node.name}:")
            outer_break, outer_continue = self.break_stack, self.continue_stack
            self.break_stack, self.continue_stack = [], []
            try:
                self._stmt(node.body)
            finally:
                self.break_stack, self.continue_stack = outer_break, outer_continue
            self._emit(f"endfunc {node.name}")
        else:
            raise NotImplementedError(f"TAC: comando nao suportado: {type(node).__name__}")

    def generate_text(self, program: Program) -> str:
        if not isinstance(program, Program):
            raise NotImplementedError("TAC: raiz deve ser Program")
        self.lines.clear()
        self.temp_count = self.label_count = 0
        self.break_stack.clear(); self.continue_stack.clear()
        self.reserved.clear()
        pending = [program]
        while pending:
            node = pending.pop()
            for name in (getattr(node, "name", None), getattr(node, "iterator_name", None)):
                if name: self.reserved.add(name)
            if isinstance(node, FuncDecl): self.reserved.update(node.params)
            try:
                pending.extend(iter_child_nodes(node))
            except TypeError as exc:
                raise NotImplementedError(f"TAC: no nao suportado: {type(node).__name__}") from exc
        self.has_fork_join = find_fork_join(program) is not None
        for stmt in program.statements:
            self._stmt(stmt)
        return "\n".join(self.lines) + ("\n" if self.lines else "")

    def generate(self, program: Program, output_name: str) -> str:
        os.makedirs("output", exist_ok=True)
        tac_path = os.path.join("output", f"{output_name}.tac")
        text = self.generate_text(program)
        with open(tac_path, "w", encoding="utf-8") as f:
            f.write(text)
        return tac_path
