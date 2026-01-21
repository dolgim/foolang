"""AST node definitions for Foolang."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field


class Node(ABC):
    """Base class for all AST nodes."""

    @abstractmethod
    def accept(self, visitor: "Visitor"):
        pass


class Expression(Node):
    """Base class for expression nodes."""

    pass


class Statement(Node):
    """Base class for statement nodes."""

    pass


# === Expressions ===


@dataclass
class NumberLiteral(Expression):
    value: float

    def accept(self, visitor: "Visitor"):
        return visitor.visit_number(self)


@dataclass
class StringLiteral(Expression):
    value: str

    def accept(self, visitor: "Visitor"):
        return visitor.visit_string(self)


@dataclass
class BoolLiteral(Expression):
    value: bool

    def accept(self, visitor: "Visitor"):
        return visitor.visit_bool(self)


@dataclass
class Identifier(Expression):
    name: str

    def accept(self, visitor: "Visitor"):
        return visitor.visit_identifier(self)


@dataclass
class BinaryOp(Expression):
    left: Expression
    operator: str
    right: Expression

    def accept(self, visitor: "Visitor"):
        return visitor.visit_binary_op(self)


@dataclass
class UnaryOp(Expression):
    operator: str
    operand: Expression

    def accept(self, visitor: "Visitor"):
        return visitor.visit_unary_op(self)


@dataclass
class CallExpression(Expression):
    callee: Expression
    arguments: list[Expression] = field(default_factory=list)

    def accept(self, visitor: "Visitor"):
        return visitor.visit_call(self)


# === Statements ===


@dataclass
class LetStatement(Statement):
    name: str
    value: Expression

    def accept(self, visitor: "Visitor"):
        return visitor.visit_let(self)


@dataclass
class ReturnStatement(Statement):
    value: Expression | None

    def accept(self, visitor: "Visitor"):
        return visitor.visit_return(self)


@dataclass
class ExpressionStatement(Statement):
    expression: Expression

    def accept(self, visitor: "Visitor"):
        return visitor.visit_expression_stmt(self)


@dataclass
class Block(Statement):
    statements: list[Statement] = field(default_factory=list)

    def accept(self, visitor: "Visitor"):
        return visitor.visit_block(self)


@dataclass
class IfStatement(Statement):
    condition: Expression
    then_branch: Block
    else_branch: Block | None = None

    def accept(self, visitor: "Visitor"):
        return visitor.visit_if(self)


@dataclass
class FnDeclaration(Statement):
    name: str
    params: list[str] = field(default_factory=list)
    body: Block = field(default_factory=Block)

    def accept(self, visitor: "Visitor"):
        return visitor.visit_fn(self)


@dataclass
class Program(Node):
    statements: list[Statement] = field(default_factory=list)

    def accept(self, visitor: "Visitor"):
        return visitor.visit_program(self)


# === Visitor Pattern ===


class Visitor(ABC):
    """Base visitor class for traversing AST."""

    @abstractmethod
    def visit_program(self, node: Program):
        pass

    @abstractmethod
    def visit_number(self, node: NumberLiteral):
        pass

    @abstractmethod
    def visit_string(self, node: StringLiteral):
        pass

    @abstractmethod
    def visit_bool(self, node: BoolLiteral):
        pass

    @abstractmethod
    def visit_identifier(self, node: Identifier):
        pass

    @abstractmethod
    def visit_binary_op(self, node: BinaryOp):
        pass

    @abstractmethod
    def visit_unary_op(self, node: UnaryOp):
        pass

    @abstractmethod
    def visit_call(self, node: CallExpression):
        pass

    @abstractmethod
    def visit_let(self, node: LetStatement):
        pass

    @abstractmethod
    def visit_return(self, node: ReturnStatement):
        pass

    @abstractmethod
    def visit_expression_stmt(self, node: ExpressionStatement):
        pass

    @abstractmethod
    def visit_block(self, node: Block):
        pass

    @abstractmethod
    def visit_if(self, node: IfStatement):
        pass

    @abstractmethod
    def visit_fn(self, node: FnDeclaration):
        pass
