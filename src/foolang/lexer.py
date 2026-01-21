"""Lexer for Foolang - converts source code into tokens."""

from dataclasses import dataclass
from enum import Enum, auto


class TokenType(Enum):
    # Literals
    NUMBER = auto()
    STRING = auto()
    IDENT = auto()

    # Keywords
    LET = auto()
    FN = auto()
    RETURN = auto()
    IF = auto()
    ELSE = auto()
    TRUE = auto()
    FALSE = auto()

    # Operators
    PLUS = auto()
    MINUS = auto()
    STAR = auto()
    SLASH = auto()
    EQ = auto()
    EQEQ = auto()
    NEQ = auto()
    LT = auto()
    GT = auto()
    LTEQ = auto()
    GTEQ = auto()

    # Delimiters
    LPAREN = auto()
    RPAREN = auto()
    LBRACE = auto()
    RBRACE = auto()
    COMMA = auto()

    # Special
    EOF = auto()


KEYWORDS = {
    "let": TokenType.LET,
    "fn": TokenType.FN,
    "return": TokenType.RETURN,
    "if": TokenType.IF,
    "else": TokenType.ELSE,
    "true": TokenType.TRUE,
    "false": TokenType.FALSE,
}


@dataclass
class Token:
    type: TokenType
    value: str
    line: int
    column: int


class LexerError(Exception):
    def __init__(self, message: str, line: int, column: int):
        self.message = message
        self.line = line
        self.column = column
        super().__init__(f"{message} at line {line}, column {column}")


class Lexer:
    def __init__(self, source: str):
        self.source = source
        self.pos = 0
        self.line = 1
        self.column = 1

    def tokenize(self) -> list[Token]:
        tokens = []
        while not self._is_at_end():
            token = self._next_token()
            if token:
                tokens.append(token)
        tokens.append(Token(TokenType.EOF, "", self.line, self.column))
        return tokens

    def _next_token(self) -> Token | None:
        self._skip_whitespace_and_comments()

        if self._is_at_end():
            return None

        start_line = self.line
        start_column = self.column
        char = self._advance()

        # Single character tokens
        single_char_tokens = {
            "(": TokenType.LPAREN,
            ")": TokenType.RPAREN,
            "{": TokenType.LBRACE,
            "}": TokenType.RBRACE,
            ",": TokenType.COMMA,
            "+": TokenType.PLUS,
            "-": TokenType.MINUS,
            "*": TokenType.STAR,
            "/": TokenType.SLASH,
        }

        if char in single_char_tokens:
            return Token(single_char_tokens[char], char, start_line, start_column)

        # Two character tokens or single
        if char == "=":
            if self._match("="):
                return Token(TokenType.EQEQ, "==", start_line, start_column)
            return Token(TokenType.EQ, "=", start_line, start_column)

        if char == "!":
            if self._match("="):
                return Token(TokenType.NEQ, "!=", start_line, start_column)
            raise LexerError(f"Unexpected character: {char}", start_line, start_column)

        if char == "<":
            if self._match("="):
                return Token(TokenType.LTEQ, "<=", start_line, start_column)
            return Token(TokenType.LT, "<", start_line, start_column)

        if char == ">":
            if self._match("="):
                return Token(TokenType.GTEQ, ">=", start_line, start_column)
            return Token(TokenType.GT, ">", start_line, start_column)

        # String literal
        if char == '"':
            return self._string(start_line, start_column)

        # Number literal
        if char.isdigit():
            return self._number(char, start_line, start_column)

        # Identifier or keyword
        if char.isalpha() or char == "_":
            return self._identifier(char, start_line, start_column)

        raise LexerError(f"Unexpected character: {char}", start_line, start_column)

    def _string(self, start_line: int, start_column: int) -> Token:
        value = ""
        while not self._is_at_end() and self._peek() != '"':
            if self._peek() == "\n":
                raise LexerError("Unterminated string", start_line, start_column)
            value += self._advance()

        if self._is_at_end():
            raise LexerError("Unterminated string", start_line, start_column)

        self._advance()  # closing "
        return Token(TokenType.STRING, value, start_line, start_column)

    def _number(self, first_digit: str, start_line: int, start_column: int) -> Token:
        value = first_digit
        while not self._is_at_end() and (self._peek().isdigit() or self._peek() == "."):
            value += self._advance()
        return Token(TokenType.NUMBER, value, start_line, start_column)

    def _identifier(self, first_char: str, start_line: int, start_column: int) -> Token:
        value = first_char
        while not self._is_at_end() and (self._peek().isalnum() or self._peek() == "_"):
            value += self._advance()

        token_type = KEYWORDS.get(value, TokenType.IDENT)
        return Token(token_type, value, start_line, start_column)

    def _skip_whitespace_and_comments(self) -> None:
        while not self._is_at_end():
            char = self._peek()
            if char in " \t\r":
                self._advance()
            elif char == "\n":
                self._advance()
            elif char == "/" and self._peek_next() == "/":
                # Single line comment
                while not self._is_at_end() and self._peek() != "\n":
                    self._advance()
            else:
                break

    def _is_at_end(self) -> bool:
        return self.pos >= len(self.source)

    def _peek(self) -> str:
        if self._is_at_end():
            return "\0"
        return self.source[self.pos]

    def _peek_next(self) -> str:
        if self.pos + 1 >= len(self.source):
            return "\0"
        return self.source[self.pos + 1]

    def _advance(self) -> str:
        char = self.source[self.pos]
        self.pos += 1
        if char == "\n":
            self.line += 1
            self.column = 1
        else:
            self.column += 1
        return char

    def _match(self, expected: str) -> bool:
        if self._is_at_end() or self._peek() != expected:
            return False
        self._advance()
        return True