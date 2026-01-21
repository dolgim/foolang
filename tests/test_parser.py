"""Tests for the Foolang parser."""

import pytest

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
    ReturnStatement,
    StringLiteral,
    UnaryOp,
)
from foolang.lexer import Lexer
from foolang.parser import ParseError, Parser


def parse(source: str):
    lexer = Lexer(source)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    return parser.parse()


class TestParserLiterals:
    def test_number(self):
        program = parse("42")
        assert len(program.statements) == 1
        stmt = program.statements[0]
        assert isinstance(stmt, ExpressionStatement)
        assert isinstance(stmt.expression, NumberLiteral)
        assert stmt.expression.value == 42.0

    def test_string(self):
        program = parse('"hello"')
        stmt = program.statements[0]
        assert isinstance(stmt.expression, StringLiteral)
        assert stmt.expression.value == "hello"

    def test_bool_true(self):
        program = parse("true")
        stmt = program.statements[0]
        assert isinstance(stmt.expression, BoolLiteral)
        assert stmt.expression.value is True

    def test_bool_false(self):
        program = parse("false")
        stmt = program.statements[0]
        assert isinstance(stmt.expression, BoolLiteral)
        assert stmt.expression.value is False

    def test_identifier(self):
        program = parse("foo")
        stmt = program.statements[0]
        assert isinstance(stmt.expression, Identifier)
        assert stmt.expression.name == "foo"


class TestParserOperators:
    def test_binary_add(self):
        program = parse("1 + 2")
        stmt = program.statements[0]
        expr = stmt.expression
        assert isinstance(expr, BinaryOp)
        assert expr.operator == "+"
        assert isinstance(expr.left, NumberLiteral)
        assert isinstance(expr.right, NumberLiteral)

    def test_precedence_mul_over_add(self):
        program = parse("1 + 2 * 3")
        stmt = program.statements[0]
        expr = stmt.expression
        # Should be (1 + (2 * 3))
        assert isinstance(expr, BinaryOp)
        assert expr.operator == "+"
        assert isinstance(expr.right, BinaryOp)
        assert expr.right.operator == "*"

    def test_comparison(self):
        program = parse("a < b")
        stmt = program.statements[0]
        expr = stmt.expression
        assert isinstance(expr, BinaryOp)
        assert expr.operator == "<"

    def test_equality(self):
        program = parse("a == b")
        stmt = program.statements[0]
        expr = stmt.expression
        assert isinstance(expr, BinaryOp)
        assert expr.operator == "=="

    def test_unary_minus(self):
        program = parse("-5")
        stmt = program.statements[0]
        expr = stmt.expression
        assert isinstance(expr, UnaryOp)
        assert expr.operator == "-"
        assert isinstance(expr.operand, NumberLiteral)

    def test_grouped_expression(self):
        program = parse("(1 + 2) * 3")
        stmt = program.statements[0]
        expr = stmt.expression
        # Should be ((1 + 2) * 3)
        assert isinstance(expr, BinaryOp)
        assert expr.operator == "*"
        assert isinstance(expr.left, BinaryOp)
        assert expr.left.operator == "+"


class TestParserStatements:
    def test_let_statement(self):
        program = parse("let x = 10")
        assert len(program.statements) == 1
        stmt = program.statements[0]
        assert isinstance(stmt, LetStatement)
        assert stmt.name == "x"
        assert isinstance(stmt.value, NumberLiteral)
        assert stmt.value.value == 10.0

    def test_let_with_expression(self):
        program = parse("let result = 1 + 2")
        stmt = program.statements[0]
        assert isinstance(stmt, LetStatement)
        assert isinstance(stmt.value, BinaryOp)

    def test_return_statement(self):
        program = parse("fn test() { return 42 }")
        fn = program.statements[0]
        ret = fn.body.statements[0]
        assert isinstance(ret, ReturnStatement)
        assert isinstance(ret.value, NumberLiteral)


class TestParserFunctions:
    def test_fn_no_params(self):
        program = parse("fn greet() { }")
        assert len(program.statements) == 1
        fn = program.statements[0]
        assert isinstance(fn, FnDeclaration)
        assert fn.name == "greet"
        assert fn.params == []

    def test_fn_with_params(self):
        program = parse("fn add(a, b) { return a + b }")
        fn = program.statements[0]
        assert isinstance(fn, FnDeclaration)
        assert fn.name == "add"
        assert fn.params == ["a", "b"]
        assert len(fn.body.statements) == 1

    def test_call_no_args(self):
        program = parse("greet()")
        stmt = program.statements[0]
        expr = stmt.expression
        assert isinstance(expr, CallExpression)
        assert isinstance(expr.callee, Identifier)
        assert expr.callee.name == "greet"
        assert expr.arguments == []

    def test_call_with_args(self):
        program = parse("add(1, 2)")
        stmt = program.statements[0]
        expr = stmt.expression
        assert isinstance(expr, CallExpression)
        assert len(expr.arguments) == 2


class TestParserControlFlow:
    def test_if_statement(self):
        program = parse("if (x > 0) { return x }")
        stmt = program.statements[0]
        assert isinstance(stmt, IfStatement)
        assert isinstance(stmt.condition, BinaryOp)
        assert isinstance(stmt.then_branch, Block)
        assert stmt.else_branch is None

    def test_if_else(self):
        program = parse("if (x > 0) { return x } else { return 0 }")
        stmt = program.statements[0]
        assert isinstance(stmt, IfStatement)
        assert stmt.else_branch is not None
        assert isinstance(stmt.else_branch, Block)


class TestParserErrors:
    def test_missing_closing_paren(self):
        with pytest.raises(ParseError):
            parse("(1 + 2")

    def test_missing_function_name(self):
        with pytest.raises(ParseError):
            parse("fn () { }")
