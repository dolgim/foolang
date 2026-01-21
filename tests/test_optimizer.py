"""Tests for the Foolang optimizer."""

from foolang.ast import (
    BinaryOp,
    Block,
    BoolLiteral,
    ExpressionStatement,
    FnDeclaration,
    Identifier,
    LetStatement,
    NumberLiteral,
    StringLiteral,
)
from foolang.lexer import Lexer
from foolang.optimizer import ConstantFolder, DeadCodeEliminator, Optimizer
from foolang.parser import Parser


def parse(source: str):
    lexer = Lexer(source)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    return parser.parse()


class TestConstantFolding:
    def test_fold_addition(self):
        program = parse("1 + 2")
        optimizer = ConstantFolder()
        result = optimizer.optimize(program)

        stmt = result.statements[0]
        assert isinstance(stmt.expression, NumberLiteral)
        assert stmt.expression.value == 3.0

    def test_fold_subtraction(self):
        program = parse("10 - 3")
        optimizer = ConstantFolder()
        result = optimizer.optimize(program)

        stmt = result.statements[0]
        assert isinstance(stmt.expression, NumberLiteral)
        assert stmt.expression.value == 7.0

    def test_fold_multiplication(self):
        program = parse("4 * 5")
        optimizer = ConstantFolder()
        result = optimizer.optimize(program)

        stmt = result.statements[0]
        assert isinstance(stmt.expression, NumberLiteral)
        assert stmt.expression.value == 20.0

    def test_fold_division(self):
        program = parse("15 / 3")
        optimizer = ConstantFolder()
        result = optimizer.optimize(program)

        stmt = result.statements[0]
        assert isinstance(stmt.expression, NumberLiteral)
        assert stmt.expression.value == 5.0

    def test_no_fold_division_by_zero(self):
        program = parse("10 / 0")
        optimizer = ConstantFolder()
        result = optimizer.optimize(program)

        stmt = result.statements[0]
        assert isinstance(stmt.expression, BinaryOp)

    def test_fold_nested_expression(self):
        program = parse("1 + 2 * 3")
        optimizer = ConstantFolder()
        result = optimizer.optimize(program)

        stmt = result.statements[0]
        assert isinstance(stmt.expression, NumberLiteral)
        assert stmt.expression.value == 7.0

    def test_fold_comparison(self):
        program = parse("5 > 3")
        optimizer = ConstantFolder()
        result = optimizer.optimize(program)

        stmt = result.statements[0]
        assert isinstance(stmt.expression, BoolLiteral)
        assert stmt.expression.value is True

    def test_fold_equality(self):
        program = parse("5 == 5")
        optimizer = ConstantFolder()
        result = optimizer.optimize(program)

        stmt = result.statements[0]
        assert isinstance(stmt.expression, BoolLiteral)
        assert stmt.expression.value is True

    def test_fold_string_concat(self):
        program = parse('"hello" + " world"')
        optimizer = ConstantFolder()
        result = optimizer.optimize(program)

        stmt = result.statements[0]
        assert isinstance(stmt.expression, StringLiteral)
        assert stmt.expression.value == "hello world"

    def test_fold_unary_minus(self):
        program = parse("-5")
        optimizer = ConstantFolder()
        result = optimizer.optimize(program)

        stmt = result.statements[0]
        assert isinstance(stmt.expression, NumberLiteral)
        assert stmt.expression.value == -5.0

    def test_fold_let_value(self):
        program = parse("let x = 1 + 2")
        optimizer = ConstantFolder()
        result = optimizer.optimize(program)

        stmt = result.statements[0]
        assert isinstance(stmt, LetStatement)
        assert isinstance(stmt.value, NumberLiteral)
        assert stmt.value.value == 3.0

    def test_no_fold_with_variable(self):
        program = parse("x + 1")
        optimizer = ConstantFolder()
        result = optimizer.optimize(program)

        stmt = result.statements[0]
        assert isinstance(stmt.expression, BinaryOp)

    def test_fold_if_true_condition(self):
        program = parse("if (true) { 1 } else { 2 }")
        optimizer = ConstantFolder()
        result = optimizer.optimize(program)

        stmt = result.statements[0]
        assert isinstance(stmt, Block)
        assert len(stmt.statements) == 1

    def test_fold_if_false_condition(self):
        program = parse("if (false) { 1 } else { 2 }")
        optimizer = ConstantFolder()
        result = optimizer.optimize(program)

        stmt = result.statements[0]
        assert isinstance(stmt, Block)


class TestDeadCodeElimination:
    def test_remove_unused_variable(self):
        program = parse("let x = 10")
        optimizer = DeadCodeEliminator()
        result = optimizer.optimize(program)

        # x is never used, so it should be removed
        assert len(result.statements) == 0

    def test_keep_used_variable(self):
        program = parse("let x = 10\nprint(x)")
        optimizer = DeadCodeEliminator()
        result = optimizer.optimize(program)

        # x is used, so it should be kept
        assert len(result.statements) == 2
        assert isinstance(result.statements[0], LetStatement)

    def test_remove_unused_function(self):
        program = parse("fn unused() { return 1 }")
        optimizer = DeadCodeEliminator()
        result = optimizer.optimize(program)

        # Function is never called, so it should be removed
        assert len(result.statements) == 0

    def test_keep_used_function(self):
        program = parse("fn add(a, b) { return a + b }\nadd(1, 2)")
        optimizer = DeadCodeEliminator()
        result = optimizer.optimize(program)

        # Function is called, so it should be kept
        assert len(result.statements) == 2
        assert isinstance(result.statements[0], FnDeclaration)

    def test_keep_print_call(self):
        program = parse('print("hello")')
        optimizer = DeadCodeEliminator()
        result = optimizer.optimize(program)

        assert len(result.statements) == 1


class TestFullOptimizer:
    def test_combined_optimizations(self):
        source = """
let unused = 100
let x = 1 + 2
print(x)
"""
        program = parse(source)
        optimizer = Optimizer()
        result = optimizer.optimize(program)

        # unused should be removed, x should have folded value
        assert len(result.statements) == 2
        let_stmt = result.statements[0]
        assert isinstance(let_stmt, LetStatement)
        assert let_stmt.name == "x"
        assert isinstance(let_stmt.value, NumberLiteral)
        assert let_stmt.value.value == 3.0

    def test_disable_constant_folding(self):
        program = parse("1 + 2")
        optimizer = Optimizer(enable_constant_folding=False)
        result = optimizer.optimize(program)

        stmt = result.statements[0]
        assert isinstance(stmt.expression, BinaryOp)

    def test_disable_dead_code(self):
        program = parse("let x = 10")
        optimizer = Optimizer(enable_dead_code=False)
        result = optimizer.optimize(program)

        assert len(result.statements) == 1
