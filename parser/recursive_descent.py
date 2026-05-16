"""递归下降解析器"""
# parser/recursive_descent.py
from typing import List, Optional
from lexer.token import Token, TokenType
from .ast_node import ASTNode, ParseResult


class RecursiveDescentParser:
    """
    递归下降语法分析器

    文法：
    E  → T E'
    E' → + T E' | - T E' | ε
    T  → F T'
    T' → * F T' | / F T' | ε
    F  → ( E ) | id | num
    """

    def __init__(self):
        self.tokens: List[Token] = []
        self.pos: int = 0
        self.errors: List[str] = []

    def parse(self, tokens: List[Token]) -> ParseResult:
        """执行语法分析"""
        self.tokens = tokens
        self.pos = 0
        self.errors = []

        try:
            ast = self._parse_E()
            if self.pos < len(self.tokens) and self.errors:
                return ParseResult(success=False, ast=ast, errors=self.errors)
            return ParseResult(success=len(self.errors) == 0, ast=ast, errors=self.errors)
        except Exception as e:
            self.errors.append(str(e))
            return ParseResult(success=False, errors=self.errors)

    def _current_token(self) -> Optional[Token]:
        """获取当前Token"""
        if self.pos < len(self.tokens):
            return self.tokens[self.pos]
        return None

    def _advance(self) -> None:
        """前进到下一个Token"""
        self.pos += 1

    def _match(self, expected_type: TokenType, expected_value: Optional[str] = None) -> bool:
        """匹配当前Token"""
        token = self._current_token()
        if token is None:
            self.errors.append(f"期望 {expected_type}，但遇到文件结束")
            return False

        if token.type != expected_type:
            self.errors.append(f"期望 {expected_type}，但遇到 {token.type} (值: {token.value})")
            return False

        if expected_value is not None and token.value != expected_value:
            self.errors.append(f"期望 '{expected_value}'，但遇到 '{token.value}'")
            return False

        return True

    def _expect(self, expected_type: TokenType, expected_value: Optional[str] = None) -> Optional[Token]:
        """期望并消费当前Token"""
        if self._match(expected_type, expected_value):
            token = self._current_token()
            self._advance()
            return token
        return None

    def _parse_E(self) -> ASTNode:
        """E → T E'"""
        t_node = self._parse_T()
        e_prime_node = self._parse_E_prime()
        return ASTNode(type="E", children=[t_node, e_prime_node])

    def _parse_E_prime(self) -> ASTNode:
        """E' → + T E' | - T E' | ε"""
        token = self._current_token()
        if token and token.type == TokenType.OPERATOR:
            if token.value == '+':
                self._advance()
                t_node = self._parse_T()
                e_prime_node = self._parse_E_prime()
                return ASTNode(type="E'", value="+", children=[t_node, e_prime_node])
            elif token.value == '-':
                self._advance()
                t_node = self._parse_T()
                e_prime_node = self._parse_E_prime()
                return ASTNode(type="E'", value="-", children=[t_node, e_prime_node])

        # ε产生式
        return ASTNode(type="E'", value="ε")

    def _parse_T(self) -> ASTNode:
        """T → F T'"""
        f_node = self._parse_F()
        t_prime_node = self._parse_T_prime()
        return ASTNode(type="T", children=[f_node, t_prime_node])

    def _parse_T_prime(self) -> ASTNode:
        """T' → * F T' | / F T' | ε"""
        token = self._current_token()
        if token and token.type == TokenType.OPERATOR:
            if token.value == '*':
                self._advance()
                f_node = self._parse_F()
                t_prime_node = self._parse_T_prime()
                return ASTNode(type="T'", value="*", children=[f_node, t_prime_node])
            elif token.value == '/':
                self._advance()
                f_node = self._parse_F()
                t_prime_node = self._parse_T_prime()
                return ASTNode(type="T'", value="/", children=[f_node, t_prime_node])

        # ε产生式
        return ASTNode(type="T'", value="ε")

    def _parse_F(self) -> ASTNode:
        """F → ( E ) | id | num"""
        token = self._current_token()
        if token is None:
            self.errors.append("期望 '(', id 或 num，但遇到文件结束")
            return ASTNode(type="F", value="error")

        if token.type == TokenType.DELIMITER and token.value == '(':
            self._advance()
            e_node = self._parse_E()
            if not self._expect(TokenType.DELIMITER, ')'):
                self.errors.append("期望 ')'")
            return ASTNode(type="F", value="()", children=[e_node])
        elif token.type == TokenType.IDENTIFIER:
            self._advance()
            return ASTNode(type="F", value="id", children=[ASTNode(type="id", value=token.value)])
        elif token.type == TokenType.CONSTANT:
            # 判断是否为数字
            val = token.value
            if val.replace('.', '').replace('-', '').isdigit():
                self._advance()
                return ASTNode(type="F", value="num", children=[ASTNode(type="num", value=val)])
            else:
                # 字符串常量或其他
                self._advance()
                return ASTNode(type="F", value="const", children=[ASTNode(type="const", value=val)])
        else:
            self.errors.append(f"期望 '(', id 或 num，但遇到 {token.type} (值: {token.value})")
            return ASTNode(type="F", value="error")


__all__ = ['RecursiveDescentParser']