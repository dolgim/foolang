"""Parser for Foolang - converts tokens into an AST."""

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
    NumberLiteral,
    Program,
    ReturnStatement,
    Statement,
    StringLiteral,
    UnaryOp,
)
from foolang.lexer import Token, TokenType


class ParseError(Exception):
    def __init__(self, message: str, token: Token):
        self.message = message
        self.token = token
        super().__init__(f"{message} at line {token.line}, column {token.column}")


class Parser:
    def __init__(self, tokens: list[Token]):
        self.tokens = tokens
        self.pos = 0

    def parse(self) -> Program:
        statements = []
        while not self._is_at_end():
            stmt = self._declaration()
            if stmt:
                statements.append(stmt)
        return Program(statements)

    def _declaration(self) -> Statement | None:
        if self._match(TokenType.FN):
            return self._fn_declaration()
        if self._match(TokenType.LET):
            return self._let_statement()
        return self._statement()

    def _fn_declaration(self) -> FnDeclaration:
        name_token = self._consume(TokenType.IDENT, "Expected function name")
        self._consume(TokenType.LPAREN, "Expected '(' after function name")

        params = []
        if not self._check(TokenType.RPAREN):
            params.append(self._consume(TokenType.IDENT, "Expected parameter name").value)
            while self._match(TokenType.COMMA):
                params.append(self._consume(TokenType.IDENT, "Expected parameter name").value)

        self._consume(TokenType.RPAREN, "Expected ')' after parameters")
        self._consume(TokenType.LBRACE, "Expected '{' before function body")
        body = self._block()

        return FnDeclaration(name_token.value, params, body)

    def _let_statement(self) -> LetStatement:
        name_token = self._consume(TokenType.IDENT, "Expected variable name")
        self._consume(TokenType.EQ, "Expected '=' after variable name")
        value = self._expression()
        return LetStatement(name_token.value, value)

    def _statement(self) -> Statement:
        if self._match(TokenType.RETURN):
            return self._return_statement()
        if self._match(TokenType.IF):
            return self._if_statement()
        if self._match(TokenType.LBRACE):
            return self._block()
        return self._expression_statement()

    def _return_statement(self) -> ReturnStatement:
        value = None
        if not self._check(TokenType.RBRACE) and not self._is_at_end():
            value = self._expression()
        return ReturnStatement(value)

    def _if_statement(self) -> IfStatement:
        self._consume(TokenType.LPAREN, "Expected '(' after 'if'")
        condition = self._expression()
        self._consume(TokenType.RPAREN, "Expected ')' after condition")

        self._consume(TokenType.LBRACE, "Expected '{' after if condition")
        then_branch = self._block()

        else_branch = None
        if self._match(TokenType.ELSE):
            self._consume(TokenType.LBRACE, "Expected '{' after 'else'")
            else_branch = self._block()

        return IfStatement(condition, then_branch, else_branch)

    def _block(self) -> Block:
        statements = []
        while not self._check(TokenType.RBRACE) and not self._is_at_end():
            stmt = self._declaration()
            if stmt:
                statements.append(stmt)
        self._consume(TokenType.RBRACE, "Expected '}' after block")
        return Block(statements)

    def _expression_statement(self) -> ExpressionStatement:
        expr = self._expression()
        return ExpressionStatement(expr)

    def _expression(self) -> Expression:
        return self._equality()

    def _equality(self) -> Expression:
        expr = self._comparison()

        while self._match(TokenType.EQEQ, TokenType.NEQ):
            operator = self._previous().value
            right = self._comparison()
            expr = BinaryOp(expr, operator, right)

        return expr

    def _comparison(self) -> Expression:
        expr = self._term()

        while self._match(TokenType.LT, TokenType.GT, TokenType.LTEQ, TokenType.GTEQ):
            operator = self._previous().value
            right = self._term()
            expr = BinaryOp(expr, operator, right)

        return expr

    def _term(self) -> Expression:
        expr = self._factor()

        while self._match(TokenType.PLUS, TokenType.MINUS):
            operator = self._previous().value
            right = self._factor()
            expr = BinaryOp(expr, operator, right)

        return expr

    def _factor(self) -> Expression:
        expr = self._unary()

        while self._match(TokenType.STAR, TokenType.SLASH):
            operator = self._previous().value
            right = self._unary()
            expr = BinaryOp(expr, operator, right)

        return expr

    def _unary(self) -> Expression:
        if self._match(TokenType.MINUS):
            operator = self._previous().value
            operand = self._unary()
            return UnaryOp(operator, operand)
        return self._call()

    def _call(self) -> Expression:
        expr = self._primary()

        while self._match(TokenType.LPAREN):
            expr = self._finish_call(expr)

        return expr

    def _finish_call(self, callee: Expression) -> CallExpression:
        arguments = []
        if not self._check(TokenType.RPAREN):
            arguments.append(self._expression())
            while self._match(TokenType.COMMA):
                arguments.append(self._expression())

        self._consume(TokenType.RPAREN, "Expected ')' after arguments")
        return CallExpression(callee, arguments)

    def _primary(self) -> Expression:
        if self._match(TokenType.TRUE):
            return BoolLiteral(True)
        if self._match(TokenType.FALSE):
            return BoolLiteral(False)
        if self._match(TokenType.NUMBER):
            return NumberLiteral(float(self._previous().value))
        if self._match(TokenType.STRING):
            return StringLiteral(self._previous().value)
        if self._match(TokenType.IDENT):
            return Identifier(self._previous().value)
        if self._match(TokenType.LPAREN):
            expr = self._expression()
            self._consume(TokenType.RPAREN, "Expected ')' after expression")
            return expr

        raise ParseError("Expected expression", self._peek())

    # === Helper methods ===

    def _match(self, *types: TokenType) -> bool:
        for t in types:
            if self._check(t):
                self._advance()
                return True
        return False

    def _check(self, type: TokenType) -> bool:
        if self._is_at_end():
            return False
        return self._peek().type == type

    def _advance(self) -> Token:
        if not self._is_at_end():
            self.pos += 1
        return self._previous()

    def _is_at_end(self) -> bool:
        return self._peek().type == TokenType.EOF

    def _peek(self) -> Token:
        return self.tokens[self.pos]

    def _previous(self) -> Token:
        return self.tokens[self.pos - 1]

    def _consume(self, type: TokenType, message: str) -> Token:
        if self._check(type):
            return self._advance()
        raise ParseError(message, self._peek())
