"""Tests for the Foolang code generator."""

from foolang.codegen import CodeGenerator
from foolang.lexer import Lexer
from foolang.parser import Parser


def compile_to_js(source: str) -> str:
    lexer = Lexer(source)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    program = parser.parse()
    codegen = CodeGenerator()
    return codegen.generate(program)


class TestCodeGenLiterals:
    def test_number_integer(self):
        js = compile_to_js("42")
        assert js == "42;"

    def test_number_float(self):
        js = compile_to_js("3.14")
        assert js == "3.14;"

    def test_string(self):
        js = compile_to_js('"hello"')
        assert js == '"hello";'

    def test_string_with_escape(self):
        js = compile_to_js('"hello\\nworld"')
        assert "\\n" in js

    def test_bool_true(self):
        js = compile_to_js("true")
        assert js == "true;"

    def test_bool_false(self):
        js = compile_to_js("false")
        assert js == "false;"

    def test_identifier(self):
        js = compile_to_js("foo")
        assert js == "foo;"


class TestCodeGenExpressions:
    def test_binary_add(self):
        js = compile_to_js("1 + 2")
        assert js == "(1 + 2);"

    def test_binary_complex(self):
        js = compile_to_js("1 + 2 * 3")
        assert js == "(1 + (2 * 3));"

    def test_comparison(self):
        js = compile_to_js("a > b")
        assert js == "(a > b);"

    def test_unary_minus(self):
        js = compile_to_js("-5")
        assert js == "(-5);"


class TestCodeGenStatements:
    def test_let_statement(self):
        js = compile_to_js("let x = 10")
        assert js == "let x = 10;"

    def test_let_with_expression(self):
        js = compile_to_js("let sum = 1 + 2")
        assert js == "let sum = (1 + 2);"


class TestCodeGenFunctions:
    def test_function_no_params(self):
        js = compile_to_js("fn greet() { }")
        assert "function greet()" in js

    def test_function_with_params(self):
        js = compile_to_js("fn add(a, b) { return a + b }")
        assert "function add(a, b)" in js
        assert "return (a + b);" in js

    def test_call_no_args(self):
        js = compile_to_js("greet()")
        assert js == "greet();"

    def test_call_with_args(self):
        js = compile_to_js("add(1, 2)")
        assert js == "add(1, 2);"

    def test_print_maps_to_console_log(self):
        js = compile_to_js('print("hello")')
        assert js == 'console.log("hello");'


class TestCodeGenControlFlow:
    def test_if_statement(self):
        js = compile_to_js("if (x > 0) { return x }")
        assert "if ((x > 0))" in js
        assert "return x;" in js

    def test_if_else(self):
        js = compile_to_js("if (x > 0) { return x } else { return 0 }")
        assert "if ((x > 0))" in js
        assert "} else {" in js
        assert "return 0;" in js


class TestCodeGenComplete:
    def test_complete_program(self):
        source = """
fn add(a, b) {
    return a + b
}

let result = add(1, 2)
print(result)
"""
        js = compile_to_js(source)
        assert "function add(a, b)" in js
        assert "return (a + b);" in js
        assert "let result = add(1, 2);" in js
        assert "console.log(result);" in js
