"""词法单元类型定义"""
from enum import Enum, auto
from dataclasses import dataclass
from typing import List, Dict, Set, Tuple, Optional


class TokenType(Enum):
    """词法单元类型枚举"""
    KEYWORD = auto()      # 关键字
    IDENTIFIER = auto()   # 标识符
    CONSTANT = auto()     # 常数（整数/浮点数）
    OPERATOR = auto()     # 运算符
    DELIMITER = auto()    # 界符
    ERROR = auto()        # 错误


@dataclass
class Token:
    """词法单元数据结构"""
    type: TokenType
    value: str
    line: int
    column: int
    description: str = ""


@dataclass
class LexicalError:
    """词法错误数据结构"""
    message: str
    line: int
    column: int
    char: str = ""


__all__ = ['Token', 'TokenType', 'LexicalError']