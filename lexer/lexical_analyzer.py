"""词法分析器接口"""
from typing import List, Tuple
from .token import Token, LexicalError
from .dfa_lexer import DFALexicalAnalyzer


class LexicalAnalyzer:
    """词法分析器封装类"""

    def __init__(self):
        self._analyzer = DFALexicalAnalyzer()

    def analyze(self, code: str) -> Tuple[List[Token], List[LexicalError]]:
        """执行词法分析"""
        return self._analyzer.tokenize(code)

    def get_token_types_info(self) -> str:
        """获取词法单元类型说明"""
        return self._analyzer.get_token_types_info()

    def get_dfa_info(self) -> str:
        """获取DFA设计说明"""
        return self._analyzer.get_dfa_info()


__all__ = ['LexicalAnalyzer']