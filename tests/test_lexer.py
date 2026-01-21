"""Tests for the Foolang lexer."""

import pytest

from foolang.lexer import Lexer, LexerError, Token, TokenType


class TestLexerBasics:
    def test_empty_input(self):
        lexer = Lexer("")
        tokens = lexer.tokenize()
        assert len(tokens) == 1
        assert tokens[0].type == TokenType.EOF

    def test_whitespace_only(self):
        lexer = Lexer("   \t\n  ")
        tokens = lexer.tokenize()
        assert len(tokens) == 1
        assert tokens[0].type == TokenType.EOF


class TestLexerLiterals:
    def test_integer(self):
        lexer = Lexer("42")
        tokens = lexer.tokenize()
        assert tokens[0].type == TokenType.NUMBER
        assert tokens[0].value == "42"

    def test_float(self):
        lexer = Lexer("3.14")
        tokens = lexer.tokenize()
        assert tokens[0].type == TokenType.NUMBER
        assert tokens[0].value == "3.14"

    def test_string(self):
        lexer = Lexer('"hello world"')
        tokens = lexer.tokenize()
        assert tokens[0].type == TokenType.STRING
        assert tokens[0].value == "hello world"

    def test_unterminated_string(self):
        lexer = Lexer('"hello')
        with pytest.raises(LexerError) as exc_info:
            lexer.tokenize()
        assert "Unterminated string" in str(exc_info.value)


class TestLexerKeywords:
    @pytest.mark.parametrize(
        "keyword,expected_type",
        [
            ("let", TokenType.LET),
            ("fn", TokenType.FN),
            ("return", TokenType.RETURN),
            ("if", TokenType.IF),
            ("else", TokenType.ELSE),
            ("true", TokenType.TRUE),
            ("false", TokenType.FALSE),
        ],
    )
    def test_keywords(self, keyword: str, expected_type: TokenType):
        lexer = Lexer(keyword)
        tokens = lexer.tokenize()
        assert tokens[0].type == expected_type
        assert tokens[0].value == keyword


class TestLexerOperators:
    @pytest.mark.parametrize(
        "op,expected_type",
        [
            ("+", TokenType.PLUS),
            ("-", TokenType.MINUS),
            ("*", TokenType.STAR),
            ("/", TokenType.SLASH),
            ("=", TokenType.EQ),
            ("==", TokenType.EQEQ),
            ("!=", TokenType.NEQ),
            ("<", TokenType.LT),
            (">", TokenType.GT),
            ("<=", TokenType.LTEQ),
            (">=", TokenType.GTEQ),
        ],
    )
    def test_operators(self, op: str, expected_type: TokenType):
        lexer = Lexer(op)
        tokens = lexer.tokenize()
        assert tokens[0].type == expected_type


class TestLexerDelimiters:
    @pytest.mark.parametrize(
        "delim,expected_type",
        [
            ("(", TokenType.LPAREN),
            (")", TokenType.RPAREN),
            ("{", TokenType.LBRACE),
            ("}", TokenType.RBRACE),
            (",", TokenType.COMMA),
        ],
    )
    def test_delimiters(self, delim: str, expected_type: TokenType):
        lexer = Lexer(delim)
        tokens = lexer.tokenize()
        assert tokens[0].type == expected_type


class TestLexerComments:
    def test_single_line_comment(self):
        lexer = Lexer("// this is a comment\n42")
        tokens = lexer.tokenize()
        assert tokens[0].type == TokenType.NUMBER
        assert tokens[0].value == "42"

    def test_comment_at_end(self):
        lexer = Lexer("42 // comment")
        tokens = lexer.tokenize()
        assert tokens[0].type == TokenType.NUMBER
        assert tokens[1].type == TokenType.EOF


class TestLexerComplex:
    def test_let_statement(self):
        lexer = Lexer("let x = 10")
        tokens = lexer.tokenize()
        expected = [
            (TokenType.LET, "let"),
            (TokenType.IDENT, "x"),
            (TokenType.EQ, "="),
            (TokenType.NUMBER, "10"),
            (TokenType.EOF, ""),
        ]
        assert len(tokens) == len(expected)
        for token, (exp_type, exp_value) in zip(tokens, expected):
            assert token.type == exp_type
            assert token.value == exp_value

    def test_function_definition(self):
        source = """fn add(a, b) {
    return a + b
}"""
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        token_types = [t.type for t in tokens]
        assert TokenType.FN in token_types
        assert TokenType.RETURN in token_types
        assert TokenType.PLUS in token_types

    def test_position_tracking(self):
        lexer = Lexer("let x = 10")
        tokens = lexer.tokenize()
        assert tokens[0].line == 1
        assert tokens[0].column == 1  # 'let' starts at column 1