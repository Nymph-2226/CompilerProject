"""Panic-mode错误恢复模块 - 新增能力②"""
# parser/error_recovery.py
from typing import List, Set, Tuple, Optional, Dict
from dataclasses import dataclass, field
from lexer.token import Token, TokenType


@dataclass
class ParseErrorInfo:
    """解析错误信息"""
    position: int
    line: int
    column: int
    expected: Set[str]
    found: str
    message: str
    context: str = ""


@dataclass
class RecoveryResult:
    """错误恢复结果"""
    success: bool
    recovered_at: int
    skipped_tokens: List[Token]
    error_info: Optional[ParseErrorInfo] = None


class ErrorRecovery:
    """
    Panic-mode错误恢复器

    策略：
    1. 当遇到语法错误时，跳过输入直到找到同步符号
    2. 同步符号包括：分号、右括号、右花括号等
    3. 恢复后继续解析
    """

    def __init__(self):
        # 同步符号集合
        self.sync_set: Set[str] = {
            ';',           # 语句结束
            '}',           # 块结束
            ')',           # 括号结束
            'else',        # 控制语句
            'while',       # 循环
            'for',
            'return'
        }

        # 期望Token集合
        self.expected_tokens: Dict[str, Set[str]] = {
            'E': {'id', 'num', '('},
            'T': {'id', 'num', '('},
            'F': {'id', 'num', '('},
            'E\'': {'+', '-', ')', '$'},
            'T\'': {'*', '/', '+', '-', ')', '$'}
        }

    def recover(self, tokens: List[Token], error_pos: int, nonterminal: str) -> RecoveryResult:
        """
        执行错误恢复

        Args:
            tokens: Token列表
            error_pos: 错误位置
            nonterminal: 当前正在解析的非终结符

        Returns:
            恢复结果
        """
        # 获取同步符号
        sync_tokens = self._get_sync_tokens(nonterminal)

        # 查找同步符号
        recovered_pos = error_pos
        skipped_tokens = []

        while recovered_pos < len(tokens):
            token = tokens[recovered_pos]
            token_value = self._token_to_str(token)

            if token_value in sync_tokens:
                break

            skipped_tokens.append(token)
            recovered_pos += 1

        # 生成错误信息
        error_info = ParseErrorInfo(
            position=error_pos,
            line=tokens[error_pos].line if error_pos < len(tokens) else 0,
            column=tokens[error_pos].column if error_pos < len(tokens) else 0,
            expected=self.expected_tokens.get(nonterminal, set()),
            found=self._token_to_str(tokens[error_pos]) if error_pos < len(tokens) else "EOF",
            message=self._generate_error_message(nonterminal, tokens[error_pos] if error_pos < len(tokens) else None),
            context=self._get_error_context(tokens, error_pos)
        )

        return RecoveryResult(
            success=recovered_pos < len(tokens),
            recovered_at=recovered_pos,
            skipped_tokens=skipped_tokens,
            error_info=error_info
        )

    def _get_sync_tokens(self, nonterminal: str) -> Set[str]:
        """获取同步符号"""
        sync_map = {
            'E': {'id', 'num', '(', '$'},
            'E\'': {')', '$'},
            'T': {'id', 'num', '('},
            'T\'': {'+', '-', ')', '$'},
            'F': {'(', 'id', 'num'}
        }
        return sync_map.get(nonterminal, self.sync_set)

    def _token_to_str(self, token: Token) -> str:
        """将Token转换为字符串"""
        if token.type == TokenType.IDENTIFIER:
            return "id"
        elif token.type == TokenType.CONSTANT:
            if token.value.replace('.', '').replace('-', '').isdigit():
                return "num"
            return "str"
        elif token.type == TokenType.KEYWORD:
            return token.value
        else:
            return token.value

    def _generate_error_message(self, nonterminal: str, token: Optional[Token]) -> str:
        """生成面向初学者的错误信息"""
        expected = self.expected_tokens.get(nonterminal, set())

        if token is None:
            return f"语法错误：在文件末尾，期望 {expected}"

        found = self._token_to_str(token)

        if found in expected:
            return f"语法错误：意外的 '{found}'"

        # 生成详细的错误说明
        if nonterminal == 'E':
            return f"语法错误：期望表达式开始，但遇到了 '{found}'。表达式应以标识符、数字或 '(' 开头。"
        elif nonterminal == 'T':
            return f"语法错误：期望项开始，但遇到了 '{found}'。项应以标识符、数字或 '(' 开头。"
        elif nonterminal == 'F':
            return f"语法错误：期望因子，但遇到了 '{found}'。因子可以是标识符、数字或括号表达式。"
        else:
            return f"语法错误：在 '{found}' 处解析失败，期望 {expected}"

    def _get_error_context(self, tokens: List[Token], error_pos: int) -> str:
        """获取错误上下文"""
        start = max(0, error_pos - 3)
        end = min(len(tokens), error_pos + 3)

        context_tokens = []
        for i in range(start, end):
            if i == error_pos:
                context_tokens.append(f">>>{self._token_to_str(tokens[i])}<<<")
            else:
                context_tokens.append(self._token_to_str(tokens[i]))

        return " ".join(context_tokens)

    def get_diagnostic_message(self, error_info: ParseErrorInfo) -> str:
        """
        生成教学型诊断信息

        这个信息可以发送给LLM生成更友好的解释
        """
        msg = f"""
【语法错误诊断】

📍 错误位置: 第 {error_info.line} 行，第 {error_info.column} 列

❌ 错误描述:
{error_info.message}

🔍 错误上下文:
... {error_info.context} ...

💡 期望的内容:
{', '.join(error_info.expected)}

📝 可能的原因:
1. 缺少必要的运算符或操作数
2. 括号不匹配
3. 使用了错误的语法结构

🔧 修正建议:
"""
        return msg


__all__ = ['ErrorRecovery', 'ParseErrorInfo', 'RecoveryResult']