from __future__ import annotations
from dataclasses import dataclass, field, fields
from typing import List, Optional

class ASTNode:
    line: int = 1

@dataclass
class NumberExpr(ASTNode):
    value: str
    line: int = 1

@dataclass
class StringExpr(ASTNode):
    value: str
    line: int = 1

@dataclass
class BoolExpr(ASTNode):
    value: bool
    line: int = 1

@dataclass
class IdentifierExpr(ASTNode):
    name: str
    line: int = 1

@dataclass
class BinaryExpr(ASTNode):
    op: str
    left: ASTNode
    right: ASTNode
    line: int = 1

@dataclass
class UnaryExpr(ASTNode):
    op: str
    operand: ASTNode
    line: int = 1

@dataclass
class VarDecl(ASTNode):
    name: str
    init_value: Optional[ASTNode] = None
    type: str = "var"
    line: int = 1

@dataclass
class Assignment(ASTNode):
    name: str
    value: ASTNode = None
    line: int = 1

@dataclass
class PrintStmt(ASTNode):
    arguments: List[ASTNode] = field(default_factory=list)
    line: int = 1

@dataclass
class SeqBlock(ASTNode):
    statements: List[ASTNode] = field(default_factory=list)
    line: int = 1

@dataclass
class ParBlock(ASTNode):
    statements: List[ASTNode] = field(default_factory=list)
    line: int = 1

@dataclass
class IfStmt(ASTNode):
    condition: ASTNode
    then_branch: ASTNode
    else_branch: Optional[ASTNode] = None
    line: int = 1

@dataclass
class WhileStmt(ASTNode):
    condition: ASTNode
    body: ASTNode
    line: int = 1

@dataclass
class DoWhileStmt(ASTNode):
    body: ASTNode
    condition: ASTNode
    line: int = 1

@dataclass
class ForStmt(ASTNode):
    initializer: Optional[ASTNode]
    condition: Optional[ASTNode]
    increment: Optional[ASTNode]
    body: ASTNode
    iterator_name: Optional[str] = None
    iterable: Optional[ASTNode] = None
    line: int = 1

@dataclass
class BreakStmt(ASTNode):
    line: int = 1

@dataclass
class ContinueStmt(ASTNode):
    line: int = 1

@dataclass
class ClassDecl(ASTNode):
    name: str
    superclass: Optional[str]
    attributes: List[VarDecl]
    methods: List[FuncDecl]
    line: int = 1

@dataclass
class FuncDecl(ASTNode):
    name: str
    params: List[str]
    body: ASTNode
    line: int = 1

@dataclass
class ReturnStmt(ASTNode):
    value: Optional[ASTNode]
    line: int = 1

@dataclass
class MethodCall(ASTNode):
    object: ASTNode
    method_name: str
    arguments: List[ASTNode]
    line: int = 1

@dataclass
class FuncCallExpr(ASTNode):
    name: str
    arguments: List[ASTNode]
    line: int = 1

@dataclass
class ForkExpr(ASTNode):
    function_name: str
    arguments: List[ASTNode]
    destination: Optional[ASTNode] = None
    line: int = 1
    column: int = 1

@dataclass
class JoinExpr(ASTNode):
    handle: ASTNode
    timeout: Optional[ASTNode] = None
    line: int = 1
    column: int = 1

@dataclass
class PropertyAccess(ASTNode):
    object: ASTNode
    property_name: str
    line: int = 1

@dataclass
class PropertyAssign(ASTNode):
    object: ASTNode
    property_name: str
    value: ASTNode
    line: int = 1

@dataclass
class NewExpr(ASTNode):
    class_name: str
    arguments: List[ASTNode]
    line: int = 1

@dataclass
class ThisExpr(ASTNode):
    line: int = 1

@dataclass
class CChannelExpr(ASTNode):
    ip: ASTNode
    port: ASTNode
    line: int = 1

@dataclass
class SendStmt(ASTNode):
    channel: ASTNode
    message: ASTNode
    line: int = 1

@dataclass
class ReceiveExpr(ASTNode):
    channel: ASTNode
    line: int = 1

@dataclass
class InputExpr(ASTNode):
    prompt: Optional[ASTNode] = None
    line: int = 1

@dataclass
class ListLiteral(ASTNode):
    elements: List[ASTNode]
    line: int = 1

@dataclass
class MatrixCreateExpr(ASTNode):
    rows: ASTNode
    cols: ASTNode
    init_value: ASTNode
    line: int = 1

@dataclass
class IndexExpr(ASTNode):
    object: ASTNode
    index: ASTNode
    line: int = 1

@dataclass
class IndexAssign(ASTNode):
    target: ASTNode
    value: ASTNode
    line: int = 1

@dataclass
class Program(ASTNode):
    statements: List[ASTNode] = field(default_factory=list)
    line: int = 1

def iter_child_nodes(node: ASTNode):
    """Percorre apenas os campos estruturais da AST (sem metadados semanticos)."""
    for item in fields(node):
        value = getattr(node, item.name)
        if isinstance(value, ASTNode):
            yield value
        elif isinstance(value, list):
            yield from (child for child in value if isinstance(child, ASTNode))

def find_fork_join(node: ASTNode) -> Optional[ASTNode]:
    pending = [node]
    while pending:
        current = pending.pop()
        if isinstance(current, (ForkExpr, JoinExpr)):
            return current
        pending.extend(iter_child_nodes(current))
    return None
