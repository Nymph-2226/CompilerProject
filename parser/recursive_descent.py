"""递归下降解析器 - 修正版（构建正确的AST）"""
# parser/recursive_descent.py
from typing import List, Optional
from lexer.token import Token, TokenType
from .ast_node import ASTNode, ParseResult


class RecursiveDescentParser:
    """
    递归下降语法分析器 - 构建反映运算符优先级的AST

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

    def _expect(self, expected_type: TokenType, expected_value: Optional[str] = None) -> Optional[Token]:
        """期望并消费当前Token"""
        token = self._current_token()
        if token is None:
            self.errors.append(f"期望 {expected_type}，但遇到文件结束")
            return None

        if token.type != expected_type:
            self.errors.append(f"期望 {expected_type}，但遇到 {token.type} (值: {token.value})")
            return None

        if expected_value is not None and token.value != expected_value:
            self.errors.append(f"期望 '{expected_value}'，但遇到 '{token.value}'")
            return None

        self._advance()
        return token

    def _parse_E(self) -> ASTNode:
        """
        E → T E'
        
        返回左结合的AST，如 a + b + c → ((a + b) + c)
        """
        node = self._parse_T()
        
        while True:
            token = self._current_token()
            if token and token.type == TokenType.OPERATOR:
                if token.value == '+':
                    self._advance()
                    right = self._parse_T()
                    node = ASTNode(type="+", value="+", children=[node, right])
                elif token.value == '-':
                    self._advance()
                    right = self._parse_T()
                    node = ASTNode(type="-", value="-", children=[node, right])
                else:
                    break
            else:
                break
        
        return node

    def _parse_T(self) -> ASTNode:
        """
        T → F T'
        
        返回左结合的AST，如 a * b * c → ((a * b) * c)
        """
        node = self._parse_F()
        
        while True:
            token = self._current_token()
            if token and token.type == TokenType.OPERATOR:
                if token.value == '*':
                    self._advance()
                    right = self._parse_F()
                    node = ASTNode(type="*", value="*", children=[node, right])
                elif token.value == '/':
                    self._advance()
                    right = self._parse_F()
                    node = ASTNode(type="/", value="/", children=[node, right])
                else:
                    break
            else:
                break
        
        return node

    def _parse_F(self) -> ASTNode:
        """F → ( E ) | id | num"""
        token = self._current_token()
        if token is None:
            self.errors.append("期望 '(', id 或 num，但遇到文件结束")
            return ASTNode(type="error", value="error")

        if token.type == TokenType.DELIMITER and token.value == '(':
            self._advance()
            node = self._parse_E()
            if not self._expect(TokenType.DELIMITER, ')'):
                self.errors.append("期望 ')'")
            return node  # 直接返回子节点，不包装 F 节点
        elif token.type == TokenType.IDENTIFIER:
            self._advance()
            return ASTNode(type="id", value=token.value)
        elif token.type == TokenType.CONSTANT:
            val = token.value
            if val.replace('.', '').replace('-', '').isdigit():
                self._advance()
                return ASTNode(type="num", value=val)
            else:
                self._advance()
                return ASTNode(type="string", value=val)
        else:
            self.errors.append(f"期望 '(', id 或 num，但遇到 {token.type} (值: {token.value})")
            return ASTNode(type="error", value="error")


__all__ = ['RecursiveDescentParser']