"""AST Optimizer for Foolang - applies optimization passes."""

from abc import ABC, abstractmethod
from dataclasses import dataclass

from foolang.ast import (
    BinaryOp,
    Block,
    BoolLiteral,
    CallExpression,
    Expression,
    ExpressionStatement,
    FnDeclaration,
    Identifier,
    IfStatement,
    LetStatement,
    Node,
    NumberLiteral,
    Program,
    ReturnStatement,
    Statement,
    StringLiteral,
    UnaryOp,
    Visitor,
)


class OptimizationPass(ABC):
    """Base class for optimization passes."""

    @abstractmethod
    def optimize(self, program: Program) -> Program:
        pass


class ConstantFolder(Visitor):
    """Folds constant expressions at compile time.

    Examples:
        1 + 2 -> 3
        "hello" + " world" -> "hello world"
        true == false -> false
    """

    def optimize(self, program: Program) -> Program:
        return self.visit_program(program)

    def visit_program(self, node: Program) -> Program:
        optimized_stmts = [self._optimize_stmt(stmt) for stmt in node.statements]
        return Program(optimized_stmts)

    def _optimize_stmt(self, stmt: Statement) -> Statement:
        return stmt.accept(self)

    def _optimize_expr(self, expr: Expression) -> Expression:
        return expr.accept(self)

    def visit_number(self, node: NumberLiteral) -> Expression:
        return node

    def visit_string(self, node: StringLiteral) -> Expression:
        return node

    def visit_bool(self, node: BoolLiteral) -> Expression:
        return node

    def visit_identifier(self, node: Identifier) -> Expression:
        return node

    def visit_binary_op(self, node: BinaryOp) -> Expression:
        left = self._optimize_expr(node.left)
        right = self._optimize_expr(node.right)

        # Try to fold numeric operations
        if isinstance(left, NumberLiteral) and isinstance(right, NumberLiteral):
            result = self._fold_numeric(left.value, node.operator, right.value)
            if result is not None:
                if isinstance(result, bool):
                    return BoolLiteral(result)
                return NumberLiteral(result)

        # Try to fold string concatenation
        if isinstance(left, StringLiteral) and isinstance(right, StringLiteral):
            if node.operator == "+":
                return StringLiteral(left.value + right.value)

        # Try to fold boolean operations
        if isinstance(left, BoolLiteral) and isinstance(right, BoolLiteral):
            result = self._fold_bool(left.value, node.operator, right.value)
            if result is not None:
                return BoolLiteral(result)

        return BinaryOp(left, node.operator, right)

    def _fold_numeric(self, left: float, op: str, right: float) -> float | bool | None:
        try:
            match op:
                case "+":
                    return left + right
                case "-":
                    return left - right
                case "*":
                    return left * right
                case "/":
                    if right != 0:
                        return left / right
                    return None
                case "<":
                    return left < right
                case ">":
                    return left > right
                case "<=":
                    return left <= right
                case ">=":
                    return left >= right
                case "==":
                    return left == right
                case "!=":
                    return left != right
                case _:
                    return None
        except Exception:
            return None

    def _fold_bool(self, left: bool, op: str, right: bool) -> bool | None:
        match op:
            case "==":
                return left == right
            case "!=":
                return left != right
            case _:
                return None

    def visit_unary_op(self, node: UnaryOp) -> Expression:
        operand = self._optimize_expr(node.operand)

        if isinstance(operand, NumberLiteral) and node.operator == "-":
            return NumberLiteral(-operand.value)

        return UnaryOp(node.operator, operand)

    def visit_call(self, node: CallExpression) -> Expression:
        callee = self._optimize_expr(node.callee)
        args = [self._optimize_expr(arg) for arg in node.arguments]
        return CallExpression(callee, args)

    def visit_let(self, node: LetStatement) -> Statement:
        return LetStatement(node.name, self._optimize_expr(node.value))

    def visit_return(self, node: ReturnStatement) -> Statement:
        value = self._optimize_expr(node.value) if node.value else None
        return ReturnStatement(value)

    def visit_expression_stmt(self, node: ExpressionStatement) -> Statement:
        return ExpressionStatement(self._optimize_expr(node.expression))

    def visit_block(self, node: Block) -> Block:
        return Block([self._optimize_stmt(stmt) for stmt in node.statements])

    def visit_if(self, node: IfStatement) -> Statement:
        condition = self._optimize_expr(node.condition)
        then_branch = self.visit_block(node.then_branch)
        else_branch = self.visit_block(node.else_branch) if node.else_branch else None

        # If condition is constant, we can eliminate the branch
        if isinstance(condition, BoolLiteral):
            if condition.value:
                return then_branch
            elif else_branch:
                return else_branch
            else:
                return Block([])  # Empty block if no else and condition is false

        return IfStatement(condition, then_branch, else_branch)

    def visit_fn(self, node: FnDeclaration) -> Statement:
        body = self.visit_block(node.body)
        return FnDeclaration(node.name, node.params, body)


@dataclass
class UsageInfo:
    """Tracks variable/function usage information."""

    defined: bool = False
    used: bool = False


class DeadCodeEliminator(Visitor):
    """Removes unused variables and functions.

    First pass: collect all definitions and usages
    Second pass: remove unused definitions
    """

    def __init__(self):
        self.usages: dict[str, UsageInfo] = {}
        self.in_collection_phase = True

    def optimize(self, program: Program) -> Program:
        # First pass: collect usage info
        self.in_collection_phase = True
        self.usages = {}
        self.visit_program(program)

        # Second pass: eliminate dead code
        self.in_collection_phase = False
        return self.visit_program(program)

    def _mark_defined(self, name: str):
        if name not in self.usages:
            self.usages[name] = UsageInfo()
        self.usages[name].defined = True

    def _mark_used(self, name: str):
        if name not in self.usages:
            self.usages[name] = UsageInfo()
        self.usages[name].used = True

    def _is_used(self, name: str) -> bool:
        # Built-in functions are always considered used
        if name in ("print", "console"):
            return True
        info = self.usages.get(name)
        return info is not None and info.used

    def visit_program(self, node: Program) -> Program:
        if self.in_collection_phase:
            for stmt in node.statements:
                stmt.accept(self)
            return node
        else:
            optimized = []
            for stmt in node.statements:
                result = stmt.accept(self)
                if result is not None:
                    optimized.append(result)
            return Program(optimized)

    def visit_number(self, node: NumberLiteral) -> Expression:
        return node

    def visit_string(self, node: StringLiteral) -> Expression:
        return node

    def visit_bool(self, node: BoolLiteral) -> Expression:
        return node

    def visit_identifier(self, node: Identifier) -> Expression:
        if self.in_collection_phase:
            self._mark_used(node.name)
        return node

    def visit_binary_op(self, node: BinaryOp) -> Expression:
        node.left.accept(self)
        node.right.accept(self)
        return BinaryOp(node.left, node.operator, node.right)

    def visit_unary_op(self, node: UnaryOp) -> Expression:
        node.operand.accept(self)
        return node

    def visit_call(self, node: CallExpression) -> Expression:
        node.callee.accept(self)
        for arg in node.arguments:
            arg.accept(self)
        return node

    def visit_let(self, node: LetStatement) -> Statement | None:
        if self.in_collection_phase:
            self._mark_defined(node.name)
            node.value.accept(self)
            return node
        else:
            if not self._is_used(node.name):
                return None
            return node

    def visit_return(self, node: ReturnStatement) -> Statement:
        if node.value:
            node.value.accept(self)
        return node

    def visit_expression_stmt(self, node: ExpressionStatement) -> Statement:
        node.expression.accept(self)
        return node

    def visit_block(self, node: Block) -> Block:
        if self.in_collection_phase:
            for stmt in node.statements:
                stmt.accept(self)
            return node
        else:
            optimized = []
            for stmt in node.statements:
                result = stmt.accept(self)
                if result is not None:
                    optimized.append(result)
            return Block(optimized)

    def visit_if(self, node: IfStatement) -> Statement:
        node.condition.accept(self)
        node.then_branch.accept(self)
        if node.else_branch:
            node.else_branch.accept(self)

        if not self.in_collection_phase:
            then_branch = self.visit_block(node.then_branch)
            else_branch = self.visit_block(node.else_branch) if node.else_branch else None
            return IfStatement(node.condition, then_branch, else_branch)
        return node

    def visit_fn(self, node: FnDeclaration) -> Statement | None:
        if self.in_collection_phase:
            self._mark_defined(node.name)
            # Mark parameters as defined within function scope
            for param in node.params:
                self._mark_defined(param)
                self._mark_used(param)  # Assume params are used
            node.body.accept(self)
            return node
        else:
            if not self._is_used(node.name):
                return None
            body = self.visit_block(node.body)
            return FnDeclaration(node.name, node.params, body)


class Optimizer:
    """Main optimizer that runs all optimization passes."""

    def __init__(self, enable_constant_folding: bool = True, enable_dead_code: bool = True):
        self.passes: list[OptimizationPass] = []
        if enable_constant_folding:
            self.passes.append(ConstantFolder())
        if enable_dead_code:
            self.passes.append(DeadCodeEliminator())

    def optimize(self, program: Program) -> Program:
        result = program
        for opt_pass in self.passes:
            result = opt_pass.optimize(result)
        return result
