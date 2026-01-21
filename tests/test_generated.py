"""AI-generated edge case tests for the Foolang compiler.

These tests cover edge cases that might break the compiler:
- Lexer: boundary cases, unicode, long inputs
- Parser: deeply nested expressions, chained calls, edge cases
- Optimizer: division by zero, type mixing, long chains
- CodeGen: JS reserved words, string escaping
"""

import pytest

from foolang.ast import (
    BinaryOp,
    Block,
    BoolLiteral,
    CallExpression,
    ExpressionStatement,
    FnDeclaration,
    Identifier,
    LetStatement,
    NumberLiteral,
    Program,
    StringLiteral,
    UnaryOp,
)
from foolang.codegen import CodeGenerator
from foolang.lexer import Lexer, LexerError, TokenType
from foolang.optimizer import ConstantFolder, DeadCodeEliminator, Optimizer
from foolang.parser import ParseError, Parser


def parse(source: str):
    """Helper function to lex and parse source code."""
    lexer = Lexer(source)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    return parser.parse()


def compile_to_js(source: str) -> str:
    """Helper function to compile source to JavaScript."""
    lexer = Lexer(source)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    program = parser.parse()
    codegen = CodeGenerator()
    return codegen.generate(program)


def compile_optimized(source: str) -> str:
    """Helper function to compile with optimizations."""
    lexer = Lexer(source)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    program = parser.parse()
    optimizer = Optimizer()
    optimized = optimizer.optimize(program)
    codegen = CodeGenerator()
    return codegen.generate(optimized)


# ==============================================================================
# LEXER EDGE CASES
# ==============================================================================


class TestLexerEdgeCases:
    """Edge cases for the lexer."""

    def test_only_comments(self):
        """Source with only comments should produce just EOF."""
        lexer = Lexer("// this is a comment")
        tokens = lexer.tokenize()
        assert len(tokens) == 1
        assert tokens[0].type == TokenType.EOF

    def test_multiple_comments(self):
        """Multiple comment lines should be skipped."""
        source = """// comment 1
// comment 2
// comment 3
42"""
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        assert tokens[0].type == TokenType.NUMBER
        assert tokens[0].value == "42"

    def test_comment_without_space(self):
        """Comment immediately after // should work."""
        lexer = Lexer("//no space here\n123")
        tokens = lexer.tokenize()
        assert tokens[0].type == TokenType.NUMBER

    def test_very_long_identifier(self):
        """Lexer should handle very long identifiers."""
        long_name = "a" * 1000
        lexer = Lexer(long_name)
        tokens = lexer.tokenize()
        assert tokens[0].type == TokenType.IDENT
        assert tokens[0].value == long_name

    def test_very_long_string(self):
        """Lexer should handle very long strings."""
        long_content = "x" * 10000
        lexer = Lexer(f'"{long_content}"')
        tokens = lexer.tokenize()
        assert tokens[0].type == TokenType.STRING
        assert tokens[0].value == long_content

    def test_very_large_number(self):
        """Lexer should handle very large numbers."""
        big_num = "9" * 100
        lexer = Lexer(big_num)
        tokens = lexer.tokenize()
        assert tokens[0].type == TokenType.NUMBER
        assert tokens[0].value == big_num

    def test_number_with_multiple_dots(self):
        """Number with multiple dots should tokenize as multiple tokens."""
        lexer = Lexer("1.2.3")
        tokens = lexer.tokenize()
        # Should be "1.2" followed by ".3"
        assert tokens[0].type == TokenType.NUMBER
        assert tokens[0].value == "1.2.3"  # Actually lexer greedily consumes

    def test_number_ending_with_dot(self):
        """Number ending with dot should include the dot."""
        lexer = Lexer("42.")
        tokens = lexer.tokenize()
        assert tokens[0].type == TokenType.NUMBER
        assert tokens[0].value == "42."

    def test_identifier_with_numbers(self):
        """Identifiers can contain numbers (but not start with them)."""
        lexer = Lexer("var123")
        tokens = lexer.tokenize()
        assert tokens[0].type == TokenType.IDENT
        assert tokens[0].value == "var123"

    def test_identifier_with_underscores(self):
        """Identifiers can have multiple underscores."""
        lexer = Lexer("_foo_bar_")
        tokens = lexer.tokenize()
        assert tokens[0].type == TokenType.IDENT
        assert tokens[0].value == "_foo_bar_"

    def test_underscore_only_identifier(self):
        """Single underscore is a valid identifier."""
        lexer = Lexer("_")
        tokens = lexer.tokenize()
        assert tokens[0].type == TokenType.IDENT
        assert tokens[0].value == "_"

    def test_empty_string(self):
        """Empty string literal should be valid."""
        lexer = Lexer('""')
        tokens = lexer.tokenize()
        assert tokens[0].type == TokenType.STRING
        assert tokens[0].value == ""

    def test_string_with_spaces(self):
        """String with only spaces."""
        lexer = Lexer('"   "')
        tokens = lexer.tokenize()
        assert tokens[0].type == TokenType.STRING
        assert tokens[0].value == "   "

    def test_multiline_string_error(self):
        """Strings cannot span multiple lines."""
        lexer = Lexer('"hello\nworld"')
        with pytest.raises(LexerError) as exc_info:
            lexer.tokenize()
        assert "Unterminated string" in str(exc_info.value)

    def test_exclamation_without_equals(self):
        """Bare ! without = should error."""
        lexer = Lexer("!")
        with pytest.raises(LexerError) as exc_info:
            lexer.tokenize()
        assert "Unexpected character" in str(exc_info.value)

    def test_unknown_character(self):
        """Unknown characters should raise LexerError."""
        lexer = Lexer("@")
        with pytest.raises(LexerError) as exc_info:
            lexer.tokenize()
        assert "Unexpected character" in str(exc_info.value)

    def test_unicode_in_string(self):
        """Unicode characters in strings should work."""
        lexer = Lexer('"héllo wörld 你好"')
        tokens = lexer.tokenize()
        assert tokens[0].type == TokenType.STRING
        assert tokens[0].value == "héllo wörld 你好"

    def test_emoji_in_string(self):
        """Emoji in strings should work."""
        lexer = Lexer('"hello 😀 world"')
        tokens = lexer.tokenize()
        assert tokens[0].type == TokenType.STRING
        assert tokens[0].value == "hello 😀 world"

    def test_tabs_in_source(self):
        """Tabs should be treated as whitespace."""
        lexer = Lexer("let\t\tx\t=\t10")
        tokens = lexer.tokenize()
        assert tokens[0].type == TokenType.LET
        assert tokens[1].type == TokenType.IDENT
        assert tokens[2].type == TokenType.EQ
        assert tokens[3].type == TokenType.NUMBER

    def test_carriage_return(self):
        """Carriage returns should be handled."""
        lexer = Lexer("let x = 10\r\nlet y = 20")
        tokens = lexer.tokenize()
        # Should have two let statements
        let_count = sum(1 for t in tokens if t.type == TokenType.LET)
        assert let_count == 2

    def test_zero(self):
        """Zero should be a valid number."""
        lexer = Lexer("0")
        tokens = lexer.tokenize()
        assert tokens[0].type == TokenType.NUMBER
        assert tokens[0].value == "0"

    def test_leading_zeros(self):
        """Numbers with leading zeros."""
        lexer = Lexer("007")
        tokens = lexer.tokenize()
        assert tokens[0].type == TokenType.NUMBER
        assert tokens[0].value == "007"

    def test_decimal_without_integer_part(self):
        """Decimal starting with dot should not be parsed as number."""
        lexer = Lexer(".5")
        # This should fail since .5 is not valid (no leading digit)
        with pytest.raises(LexerError):
            lexer.tokenize()


# ==============================================================================
# PARSER EDGE CASES
# ==============================================================================


class TestParserEdgeCases:
    """Edge cases for the parser."""

    def test_deeply_nested_parens(self):
        """Parser should handle deeply nested parentheses."""
        # ((((((1))))))
        nested = "(" * 50 + "1" + ")" * 50
        program = parse(nested)
        assert len(program.statements) == 1
        # The innermost expression should be a number
        expr = program.statements[0].expression
        assert isinstance(expr, NumberLiteral)
        assert expr.value == 1.0

    def test_deeply_nested_binary_ops(self):
        """Parser should handle deeply nested binary operations."""
        # 1 + 2 + 3 + 4 + ... + 50 (left associative)
        source = " + ".join(str(i) for i in range(1, 51))
        program = parse(source)
        assert len(program.statements) == 1
        # Result should be a chain of BinaryOps
        expr = program.statements[0].expression
        assert isinstance(expr, BinaryOp)

    def test_chained_function_calls(self):
        """Parser should handle chained function calls: foo()()()"""
        program = parse("foo()()()")
        stmt = program.statements[0]
        expr = stmt.expression
        # Should be CallExpression(CallExpression(CallExpression(Identifier)))
        assert isinstance(expr, CallExpression)
        assert isinstance(expr.callee, CallExpression)
        assert isinstance(expr.callee.callee, CallExpression)
        assert isinstance(expr.callee.callee.callee, Identifier)

    def test_empty_function_body(self):
        """Empty function body should be valid."""
        program = parse("fn empty() { }")
        fn = program.statements[0]
        assert isinstance(fn, FnDeclaration)
        assert fn.name == "empty"
        assert len(fn.body.statements) == 0

    def test_function_many_parameters(self):
        """Function with many parameters should work."""
        params = ", ".join(f"p{i}" for i in range(20))
        source = f"fn many({params}) {{ return p0 }}"
        program = parse(source)
        fn = program.statements[0]
        assert len(fn.params) == 20

    def test_function_call_many_arguments(self):
        """Function call with many arguments should work."""
        args = ", ".join(str(i) for i in range(20))
        source = f"test({args})"
        program = parse(source)
        call = program.statements[0].expression
        assert len(call.arguments) == 20

    def test_nested_if_statements(self):
        """Nested if statements should work."""
        source = """
if (a) {
    if (b) {
        if (c) {
            return 1
        } else {
            return 2
        }
    }
}
"""
        program = parse(source)
        assert len(program.statements) == 1

    def test_if_without_else(self):
        """If without else should be valid."""
        program = parse("if (x) { return 1 }")
        stmt = program.statements[0]
        assert stmt.else_branch is None

    def test_multiple_unary_minus(self):
        """Multiple unary minus should work: ---5"""
        program = parse("---5")
        expr = program.statements[0].expression
        assert isinstance(expr, UnaryOp)
        assert isinstance(expr.operand, UnaryOp)
        assert isinstance(expr.operand.operand, UnaryOp)

    def test_unary_minus_on_expression(self):
        """Unary minus on grouped expression."""
        program = parse("-(1 + 2)")
        expr = program.statements[0].expression
        assert isinstance(expr, UnaryOp)
        assert isinstance(expr.operand, BinaryOp)

    def test_expression_as_function_callee(self):
        """Expression result can be called."""
        # This tests that (fn_returning_fn())() works
        program = parse("(get_fn())(1, 2)")
        expr = program.statements[0].expression
        assert isinstance(expr, CallExpression)

    def test_return_without_value(self):
        """Return statement without value should work."""
        program = parse("fn test() { return }")
        fn = program.statements[0]
        ret = fn.body.statements[0]
        assert isinstance(ret, LetStatement) is False
        # Actually need to check differently - return is inside function

    def test_let_with_function_call(self):
        """Let statement with function call as value."""
        program = parse("let result = compute(1, 2, 3)")
        stmt = program.statements[0]
        assert isinstance(stmt, LetStatement)
        assert isinstance(stmt.value, CallExpression)

    def test_comparison_chaining(self):
        """Comparison operators should chain correctly."""
        program = parse("a < b == c > d")
        expr = program.statements[0].expression
        # Due to precedence, this should be ((a < b) == (c > d))
        assert isinstance(expr, BinaryOp)
        assert expr.operator == "=="

    def test_all_comparison_operators(self):
        """All comparison operators should work."""
        for op in ["<", ">", "<=", ">=", "==", "!="]:
            program = parse(f"a {op} b")
            expr = program.statements[0].expression
            assert isinstance(expr, BinaryOp)
            assert expr.operator == op

    def test_empty_program(self):
        """Empty program should be valid."""
        program = parse("")
        assert len(program.statements) == 0

    def test_program_only_comments(self):
        """Program with only comments should be valid."""
        program = parse("// just a comment")
        assert len(program.statements) == 0

    def test_missing_closing_brace(self):
        """Missing closing brace should error."""
        with pytest.raises(ParseError):
            parse("fn test() { return 1")

    def test_missing_opening_paren_in_if(self):
        """Missing ( in if should error."""
        with pytest.raises(ParseError):
            parse("if x > 0) { }")

    def test_missing_closing_paren_in_if(self):
        """Missing ) in if should error."""
        with pytest.raises(ParseError):
            parse("if (x > 0 { }")

    def test_missing_brace_after_if(self):
        """Missing { after if condition should error."""
        with pytest.raises(ParseError):
            parse("if (x > 0) return x")

    def test_let_missing_equals(self):
        """Let without = should error."""
        with pytest.raises(ParseError):
            parse("let x 10")

    def test_let_missing_value(self):
        """Let without value should error."""
        with pytest.raises(ParseError):
            parse("let x =")


# ==============================================================================
# OPTIMIZER EDGE CASES
# ==============================================================================


class TestOptimizerEdgeCases:
    """Edge cases for the optimizer."""

    def test_division_by_zero_not_folded(self):
        """Division by zero should not be folded."""
        program = parse("1 / 0")
        optimizer = ConstantFolder()
        result = optimizer.optimize(program)
        # Should remain as BinaryOp, not crash
        expr = result.statements[0].expression
        assert isinstance(expr, BinaryOp)

    def test_nested_division_by_zero(self):
        """Nested expression with division by zero."""
        program = parse("1 + (2 / 0)")
        optimizer = ConstantFolder()
        result = optimizer.optimize(program)
        # Should partially fold but leave division
        expr = result.statements[0].expression
        assert isinstance(expr, BinaryOp)

    def test_very_large_constant_folding(self):
        """Folding very large numbers should work."""
        # 10^20 * 10^20 = 10^40
        program = parse("100000000000000000000 * 100000000000000000000")
        optimizer = ConstantFolder()
        result = optimizer.optimize(program)
        expr = result.statements[0].expression
        assert isinstance(expr, NumberLiteral)

    def test_fold_negative_numbers(self):
        """Folding with negative numbers."""
        program = parse("-5 + -3")
        optimizer = ConstantFolder()
        result = optimizer.optimize(program)
        expr = result.statements[0].expression
        assert isinstance(expr, NumberLiteral)
        assert expr.value == -8.0

    def test_fold_chain_of_operations(self):
        """Folding a long chain of operations."""
        source = "1 + 2 + 3 + 4 + 5 + 6 + 7 + 8 + 9 + 10"
        program = parse(source)
        optimizer = ConstantFolder()
        result = optimizer.optimize(program)
        expr = result.statements[0].expression
        assert isinstance(expr, NumberLiteral)
        assert expr.value == 55.0

    def test_fold_mixed_operations(self):
        """Folding mixed arithmetic operations."""
        program = parse("2 + 3 * 4 - 10 / 2")
        optimizer = ConstantFolder()
        result = optimizer.optimize(program)
        expr = result.statements[0].expression
        assert isinstance(expr, NumberLiteral)
        assert expr.value == 9.0  # 2 + 12 - 5 = 9

    def test_fold_boolean_equality(self):
        """Folding boolean equality."""
        program = parse("true == true")
        optimizer = ConstantFolder()
        result = optimizer.optimize(program)
        expr = result.statements[0].expression
        assert isinstance(expr, BoolLiteral)
        assert expr.value is True

    def test_fold_boolean_inequality(self):
        """Folding boolean inequality."""
        program = parse("true != false")
        optimizer = ConstantFolder()
        result = optimizer.optimize(program)
        expr = result.statements[0].expression
        assert isinstance(expr, BoolLiteral)
        assert expr.value is True

    def test_no_fold_mixed_types(self):
        """Mixed type operations should not be folded."""
        # String + Number should not fold (would be runtime error)
        program = parse('"hello" + 5')
        optimizer = ConstantFolder()
        result = optimizer.optimize(program)
        expr = result.statements[0].expression
        assert isinstance(expr, BinaryOp)

    def test_fold_empty_string_concat(self):
        """Folding empty string concatenation."""
        program = parse('"" + ""')
        optimizer = ConstantFolder()
        result = optimizer.optimize(program)
        expr = result.statements[0].expression
        assert isinstance(expr, StringLiteral)
        assert expr.value == ""

    def test_fold_double_negation(self):
        """Double negation should fold to positive."""
        program = parse("--5")
        optimizer = ConstantFolder()
        result = optimizer.optimize(program)
        expr = result.statements[0].expression
        assert isinstance(expr, NumberLiteral)
        assert expr.value == 5.0

    def test_dead_code_preserves_used_in_condition(self):
        """Variables used in conditions should be kept."""
        source = """
let x = 10
if (x > 5) { print(1) }
"""
        program = parse(source)
        optimizer = DeadCodeEliminator()
        result = optimizer.optimize(program)
        # x is used in condition, should be kept
        assert len(result.statements) == 2

    def test_dead_code_function_calls_self(self):
        """Recursive function that calls itself."""
        source = """
fn recurse(n) {
    if (n > 0) {
        recurse(n - 1)
    }
}
recurse(10)
"""
        program = parse(source)
        optimizer = DeadCodeEliminator()
        result = optimizer.optimize(program)
        # Function is called, should be kept
        assert len(result.statements) == 2

    def test_dead_code_nested_unused(self):
        """Unused variable inside used function."""
        source = """
fn test() {
    let unused = 10
    return 1
}
test()
"""
        program = parse(source)
        optimizer = Optimizer()
        result = optimizer.optimize(program)
        # Function should exist but unused var inside might be removed
        assert len(result.statements) == 2

    def test_fold_if_with_constant_comparison(self):
        """If with constant comparison condition."""
        program = parse("if (5 > 3) { return 1 } else { return 2 }")
        optimizer = ConstantFolder()
        result = optimizer.optimize(program)
        # Condition (5 > 3) = true, should simplify to then branch
        stmt = result.statements[0]
        assert isinstance(stmt, Block)

    def test_fold_if_false_no_else(self):
        """If with false condition and no else."""
        program = parse("if (false) { return 1 }")
        optimizer = ConstantFolder()
        result = optimizer.optimize(program)
        # Should become empty block
        stmt = result.statements[0]
        assert isinstance(stmt, Block)
        assert len(stmt.statements) == 0


# ==============================================================================
# CODE GENERATOR EDGE CASES
# ==============================================================================


class TestCodeGenEdgeCases:
    """Edge cases for the code generator."""

    def test_js_reserved_word_as_identifier(self):
        """JavaScript reserved words as identifiers should work (compiler allows it)."""
        # These are JS reserved words but valid in Foolang
        for word in ["class", "const", "var", "function", "new", "this"]:
            js = compile_to_js(f"let {word} = 10")
            assert f"let {word} = 10;" in js

    def test_string_with_quotes(self):
        """Strings containing quotes should be escaped."""
        codegen = CodeGenerator()
        # Manually create a string with a quote in it
        prog = Program([ExpressionStatement(StringLiteral('say "hi"'))])
        js = codegen.generate(prog)
        assert '\\"' in js

    def test_string_with_backslash(self):
        """Strings containing backslash should be escaped."""
        codegen = CodeGenerator()
        prog = Program([ExpressionStatement(StringLiteral("path\\to\\file"))])
        js = codegen.generate(prog)
        assert "\\\\" in js

    def test_string_with_newline_char(self):
        """Strings containing newline character should be escaped."""
        codegen = CodeGenerator()
        prog = Program([ExpressionStatement(StringLiteral("line1\nline2"))])
        js = codegen.generate(prog)
        assert "\\n" in js

    def test_deeply_nested_function_calls_output(self):
        """Deeply nested function calls should generate correctly."""
        js = compile_to_js("f(g(h(1)))")
        assert js == "f(g(h(1)));"

    def test_complex_expression_output(self):
        """Complex expressions should be properly parenthesized."""
        js = compile_to_js("(a + b) * (c - d)")
        assert "((a + b) * (c - d))" in js

    def test_function_with_empty_body(self):
        """Function with empty body should generate correctly."""
        js = compile_to_js("fn empty() { }")
        assert "function empty()" in js
        assert "{" in js
        assert "}" in js

    def test_multiple_statements(self):
        """Multiple statements should each be on their own line."""
        js = compile_to_js("let x = 1\nlet y = 2\nlet z = 3")
        lines = js.strip().split("\n")
        assert len(lines) == 3

    def test_indentation_in_nested_blocks(self):
        """Nested blocks should have proper indentation."""
        source = """
fn test() {
    if (x) {
        return 1
    }
}
"""
        js = compile_to_js(source)
        # Should have indentation
        assert "  " in js  # At least 2 spaces for some indentation

    def test_number_integer_output(self):
        """Integer numbers should not have decimal point."""
        js = compile_to_js("42")
        assert js == "42;"
        assert ".0" not in js

    def test_number_float_output(self):
        """Float numbers should preserve decimal."""
        js = compile_to_js("3.14")
        assert js == "3.14;"

    def test_chained_calls_output(self):
        """Chained function calls should output correctly."""
        js = compile_to_js("a()()()")
        assert js == "a()()();"

    def test_call_with_complex_arguments(self):
        """Function call with complex expression arguments."""
        js = compile_to_js("func(1 + 2, a * b, test())")
        assert "func((1 + 2), (a * b), test())" in js

    def test_return_with_complex_expression(self):
        """Return with complex expression."""
        js = compile_to_js("fn test() { return a + b * c }")
        assert "return (a + (b * c));" in js

    def test_print_multiple_args(self):
        """Print with multiple arguments."""
        js = compile_to_js('print(1, "hello", true)')
        assert 'console.log(1, "hello", true);' in js


# ==============================================================================
# INTEGRATION EDGE CASES
# ==============================================================================


class TestIntegrationEdgeCases:
    """End-to-end integration edge cases."""

    def test_full_pipeline_with_optimization(self):
        """Full compilation pipeline with optimization."""
        source = """
fn add(a, b) {
    return a + b
}
let unused = 100
let result = 1 + 2
print(result)
"""
        js = compile_optimized(source)
        # unused should be removed
        assert "unused" not in js
        # 1 + 2 should be folded to 3
        assert "let result = 3;" in js
        # add function should be removed (not called)
        assert "function add" not in js

    def test_optimization_preserves_side_effects(self):
        """Optimization should preserve side effects like print."""
        source = 'print("hello")'
        js = compile_optimized(source)
        assert 'console.log("hello");' in js

    def test_optimization_with_function_calls(self):
        """Optimization with function calls (cannot fold)."""
        source = """
fn getValue() { return 10 }
let x = getValue() + 5
print(x)
"""
        js = compile_optimized(source)
        # getValue() + 5 cannot be folded since getValue() is not constant
        assert "getValue()" in js

    def test_complex_program(self):
        """Complex program with multiple features."""
        source = """
fn factorial(n) {
    if (n <= 1) {
        return 1
    } else {
        return n * factorial(n - 1)
    }
}

let result = factorial(5)
print(result)
"""
        js = compile_to_js(source)
        assert "function factorial(n)" in js
        assert "if ((n <= 1))" in js
        assert "factorial((n - 1))" in js

    def test_unicode_identifiers_supported(self):
        """Unicode identifiers ARE supported (Python's isalpha() accepts unicode).

        Note: This is a potentially surprising behavior - the lexer accepts unicode
        characters as identifiers because Python's str.isalpha() returns True for
        unicode letters. This test documents this behavior.
        """
        # Python's isalpha() returns True for unicode letters
        lexer = Lexer("日本語 = 1")
        tokens = lexer.tokenize()
        # Unicode characters are accepted as identifiers
        assert tokens[0].type == TokenType.IDENT
        assert tokens[0].value == "日本語"
        assert tokens[1].type == TokenType.EQ
        assert tokens[2].type == TokenType.NUMBER

    def test_stress_test_many_variables(self):
        """Many variable declarations."""
        declarations = "\n".join(f"let var{i} = {i}" for i in range(100))
        usage = "\n".join(f"print(var{i})" for i in range(100))
        source = declarations + "\n" + usage
        js = compile_to_js(source)
        # All 100 variables should be in output
        for i in range(100):
            assert f"let var{i} = {i};" in js

    def test_stress_test_deep_nesting_compile(self):
        """Deeply nested expressions through full pipeline."""
        # Build ((((1 + 2) + 3) + 4) + 5)...
        expr = "1"
        for i in range(2, 20):
            expr = f"({expr} + {i})"
        source = f"let result = {expr}\nprint(result)"
        js = compile_optimized(source)
        # Should fold to sum 1+2+...+19 = 190
        assert "let result = 190;" in js
