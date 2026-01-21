"""JavaScript code generator for Foolang."""

from foolang.ast import (
    BinaryOp,
    Block,
    BoolLiteral,
    CallExpression,
    ExpressionStatement,
    FnDeclaration,
    Identifier,
    IfStatement,
    LetStatement,
    NumberLiteral,
    Program,
    ReturnStatement,
    StringLiteral,
    UnaryOp,
    Visitor,
)


class CodeGenerator(Visitor):
    """Generates JavaScript code from Foolang AST."""

    def __init__(self):
        self.indent_level = 0
        self.indent_str = "  "

    def generate(self, program: Program) -> str:
        return self.visit_program(program)

    def _indent(self) -> str:
        return self.indent_str * self.indent_level

    def visit_program(self, node: Program) -> str:
        lines = []
        for stmt in node.statements:
            code = stmt.accept(self)
            if code:
                lines.append(code)
        return "\n".join(lines)

    def visit_number(self, node: NumberLiteral) -> str:
        # Output integers without decimal point
        if node.value == int(node.value):
            return str(int(node.value))
        return str(node.value)

    def visit_string(self, node: StringLiteral) -> str:
        # Use JSON-style escaping for the string
        escaped = node.value.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")
        return f'"{escaped}"'

    def visit_bool(self, node: BoolLiteral) -> str:
        return "true" if node.value else "false"

    def visit_identifier(self, node: Identifier) -> str:
        return node.name

    def visit_binary_op(self, node: BinaryOp) -> str:
        left = node.left.accept(self)
        right = node.right.accept(self)
        return f"({left} {node.operator} {right})"

    def visit_unary_op(self, node: UnaryOp) -> str:
        operand = node.operand.accept(self)
        return f"({node.operator}{operand})"

    def visit_call(self, node: CallExpression) -> str:
        callee = node.callee.accept(self)

        # Map print to console.log
        if callee == "print":
            callee = "console.log"

        args = ", ".join(arg.accept(self) for arg in node.arguments)
        return f"{callee}({args})"

    def visit_let(self, node: LetStatement) -> str:
        value = node.value.accept(self)
        return f"{self._indent()}let {node.name} = {value};"

    def visit_return(self, node: ReturnStatement) -> str:
        if node.value:
            value = node.value.accept(self)
            return f"{self._indent()}return {value};"
        return f"{self._indent()}return;"

    def visit_expression_stmt(self, node: ExpressionStatement) -> str:
        expr = node.expression.accept(self)
        return f"{self._indent()}{expr};"

    def visit_block(self, node: Block) -> str:
        lines = []
        for stmt in node.statements:
            code = stmt.accept(self)
            if code:
                lines.append(code)
        return "\n".join(lines)

    def visit_if(self, node: IfStatement) -> str:
        condition = node.condition.accept(self)

        self.indent_level += 1
        then_body = self.visit_block(node.then_branch)
        self.indent_level -= 1

        base_indent = self._indent()
        result = f"{base_indent}if ({condition}) {{\n{then_body}\n{base_indent}}}"

        if node.else_branch:
            self.indent_level += 1
            else_body = self.visit_block(node.else_branch)
            self.indent_level -= 1
            result += f" else {{\n{else_body}\n{base_indent}}}"

        return result

    def visit_fn(self, node: FnDeclaration) -> str:
        params = ", ".join(node.params)

        self.indent_level += 1
        body = self.visit_block(node.body)
        self.indent_level -= 1

        base_indent = self._indent()
        return f"{base_indent}function {node.name}({params}) {{\n{body}\n{base_indent}}}"
