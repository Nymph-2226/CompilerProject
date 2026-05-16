"""基于DFA的词法分析器"""
from typing import List, Tuple, Set, Dict, Optional
from .token import Token, TokenType, LexicalError


class DFALexicalAnalyzer:
    """
    基于确定有限自动机(DFA)的词法分析器

    DFA设计：
    1. 标识符/关键字DFA
    2. 整数常量DFA
    3. 浮点数常量DFA
    4. 运算符/界符DFA
    """

    def __init__(self):
        # ==================== 关键字集合 ====================
        self.keywords: Set[str] = {
            'if', 'else', 'while', 'for', 'do', 'break', 'continue',
            'switch', 'case', 'default', 'goto', 'return',
            'int', 'float', 'double', 'char', 'void',
            'short', 'long', 'unsigned', 'signed',
            'struct', 'union', 'enum', 'typedef',
            'auto', 'static', 'register', 'extern', 'const', 'volatile',
            'class', 'public', 'private', 'protected',
            'virtual', 'friend', 'inline', 'operator',
            'new', 'delete', 'this', 'namespace', 'using',
            'true', 'false', 'null', 'NULL'
        }

        # ==================== 运算符集合 ====================
        self.operators: Set[str] = {
            '+', '-', '*', '/', '%', '=', '!', '<', '>', '&', '|', '^', '~', '?',
            '==', '!=', '<=', '>=', '&&', '||', '++', '--',
            '+=', '-=', '*=', '/=', '%=', '&=', '|=', '^=', '<<=', '>>=',
            '<<', '>>', '->', '::',
            '<<=', '>>='
        }

        # ==================== 界符集合 ====================
        self.delimiters: Set[str] = {
            ';', ',', '.', '(', ')', '{', '}', '[', ']', ':', '#', '@'
        }

        # ==================== DFA状态定义 ====================
        self.STATE_START = 0
        self.STATE_IDENT = 1
        self.STATE_NUMBER = 2
        self.STATE_FLOAT = 3
        self.STATE_FLOAT_EXP = 4
        self.STATE_FLOAT_EXP_SIGN = 5
        self.STATE_FLOAT_EXP_NUM = 6
        self.STATE_HEX = 7
        self.STATE_OPERATOR = 8
        self.STATE_STRING = 9
        self.STATE_CHAR = 10
        self.STATE_COMMENT_LINE = 11
        self.STATE_COMMENT_BLOCK = 12
        self.STATE_ERROR = 13

        # ==================== 合法运算符集合 ====================
        self.valid_operators: Set[str] = self.operators.copy()

        # ==================== 禁止的运算符组合 ====================
        self.invalid_operator_patterns: List[str] = [
            '=+', '=-', '=*', '=/', '=%',
            '!+', '!-', '!*', '!/', '!%',
            '<+', '<-', '<*', '</', '<%',
            '>+', '>-', '>*', '>/', '>%',
            '&+', '&-', '&*', '&/', '&%',
            '|+', '|-', '|*', '|/', '|%',
            '+++', '---', '**', '//',
            '+=+', '-=-', '*=*', '/=/',
        ]

        # ==================== 可疑模式提示 ====================
        self.suspicious_patterns: Dict[str, str] = {
            '=+': '可能为赋值后接正号，建议使用 += 或分开写',
            '=-': '可能为赋值后接负号，建议使用 -= 或分开写',
            '=*': '可能为赋值后接乘号，建议使用 *=',
            '=/': '可能为赋值后接除号，建议使用 /=',
            '+++': '运算符重复，可能为自增后接正号',
            '---': '运算符重复，可能为自减后接负号',
        }

    # ==================== 主入口方法 ====================
    def tokenize(self, code: str) -> Tuple[List[Token], List[LexicalError]]:
        """对源代码进行词法分析"""
        tokens: List[Token] = []
        errors: List[LexicalError] = []

        if not code or not code.strip():
            return tokens, errors

        i = 0
        n = len(code)
        line = 1
        col = 1

        while i < n:
            ch = code[i]

            if ch == '\n':
                line += 1
                col = 1
                i += 1
                continue

            if ch.isspace():
                i += 1
                col += 1
                continue

            # 注释处理
            if ch == '/':
                if i + 1 < n and code[i + 1] == '/':
                    i, col, line = self._skip_line_comment(code, i, col, line)
                    continue
                elif i + 1 < n and code[i + 1] == '*':
                    result = self._skip_block_comment(code, i, col, line)
                    i, col, line, err = result
                    if err:
                        errors.append(err)
                    continue

            # 字符串常量
            if ch == '"':
                token, err, new_i, new_col, new_line = self._scan_string(code, i, col, line)
                if token:
                    tokens.append(token)
                if err:
                    errors.append(err)
                i, col, line = new_i, new_col, new_line
                continue

            # 字符常量
            if ch == "'":
                token, err, new_i, new_col, new_line = self._scan_char(code, i, col, line)
                if token:
                    tokens.append(token)
                if err:
                    errors.append(err)
                i, col, line = new_i, new_col, new_line
                continue

            # 标识符或关键字
            if ch.isalpha() or ch == '_':
                token, new_i, new_col = self._scan_identifier_or_keyword(code, i, col, line)
                tokens.append(token)
                i, col = new_i, new_col
                continue

            # 数字常量
            if ch.isdigit():
                token, err, new_i, new_col, new_line = self._scan_number(code, i, col, line)
                if token:
                    tokens.append(token)
                if err:
                    errors.append(err)
                i, col, line = new_i, new_col, new_line
                continue

            # 运算符和界符
            result = self._scan_operator_or_delimiter(code, i, col, line)
            if result[0] is not None:
                tokens.append(result[0])
                i, col = result[1], result[2]
                continue
            if result[3] is not None:
                errors.append(result[3])
                i, col = result[1], result[2]
                continue

            # 无法识别的字符
            errors.append(LexicalError(
                message=f"非法字符: '{ch}' (ASCII: {ord(ch)})",
                line=line,
                column=col,
                char=ch
            ))
            i += 1
            col += 1

        # 后处理检查相邻运算符
        errors.extend(self._check_adjacent_operators(tokens, code))

        return tokens, errors

    def _skip_line_comment(self, code: str, start: int, col: int, line: int) -> Tuple[int, int, int]:
        i = start
        n = len(code)
        while i < n and code[i] != '\n':
            i += 1
        return i, col, line

    def _skip_block_comment(self, code: str, start: int, col: int, line: int) -> Tuple[int, int, int, Optional[LexicalError]]:
        i = start + 2
        n = len(code)
        current_line = line

        while i + 1 < n:
            if code[i] == '*' and code[i + 1] == '/':
                i += 2
                return i, col, current_line, None
            if code[i] == '\n':
                current_line += 1
            i += 1

        error = LexicalError(
            message="未终止的多行注释",
            line=line,
            column=col,
            char='/*'
        )
        return i, col, current_line, error

    def _scan_string(self, code: str, start: int, col: int, line: int) -> Tuple[Optional[Token], Optional[LexicalError], int, int, int]:
        i = start + 1
        n = len(code)
        current_line = line

        while i < n:
            ch = code[i]

            if ch == '\n':
                current_line += 1
                i += 1
                continue

            if ch == '\\':
                i += 1
                if i < n:
                    i += 1
                continue

            if ch == '"':
                lexeme = code[start:i + 1]
                token = Token(
                    type=TokenType.CONSTANT,
                    value=lexeme,
                    line=line,
                    column=col,
                    description=f"字符串常量: {lexeme}"
                )
                return token, None, i + 1, col + (i - start + 1), current_line

            i += 1

        error = LexicalError(
            message="未终止的字符串常量",
            line=line,
            column=col,
            char='"'
        )
        return None, error, i, col, current_line

    def _scan_char(self, code: str, start: int, col: int, line: int) -> Tuple[Optional[Token], Optional[LexicalError], int, int, int]:
        i = start + 1
        n = len(code)
        current_line = line

        if i >= n:
            error = LexicalError(
                message="未终止的字符常量",
                line=line,
                column=col,
                char="'"
            )
            return None, error, i, col, current_line

        if code[i] == '\\':
            i += 1
            if i >= n:
                error = LexicalError(
                    message="未终止的字符常量",
                    line=line,
                    column=col,
                    char="'"
                )
                return None, error, i, col, current_line
            i += 1
        else:
            i += 1

        if i < n and code[i] == "'":
            lexeme = code[start:i + 1]
            token = Token(
                type=TokenType.CONSTANT,
                value=lexeme,
                line=line,
                column=col,
                description=f"字符常量: {lexeme}"
            )
            return token, None, i + 1, col + (i - start + 1), current_line

        error = LexicalError(
            message="未终止的字符常量",
            line=line,
            column=col,
            char="'"
        )
        return None, error, i, col, current_line

    def _scan_identifier_or_keyword(self, code: str, start: int, col: int, line: int) -> Tuple[Token, int, int]:
        i = start
        n = len(code)

        while i < n:
            ch = code[i]
            if ch.isalnum() or ch == '_':
                i += 1
            else:
                break

        lexeme = code[start:i]

        if lexeme in self.keywords:
            token_type = TokenType.KEYWORD
            desc = f"关键字: {lexeme}"
        else:
            token_type = TokenType.IDENTIFIER
            desc = f"标识符: {lexeme}"

        token = Token(
            type=token_type,
            value=lexeme,
            line=line,
            column=col,
            description=desc
        )

        return token, i, col + (i - start)

    def _scan_number(self, code: str, start: int, col: int, line: int) -> Tuple[Optional[Token], Optional[LexicalError], int, int, int]:
        i = start
        n = len(code)
        state = self.STATE_NUMBER
        is_float = False
        has_exp = False
        current_line = line

        # 十六进制
        if code[i] == '0' and i + 1 < n and code[i + 1] in ('x', 'X'):
            state = self.STATE_HEX
            i += 2
            if i >= n or not (code[i].isdigit() or code[i] in 'abcdefABCDEF'):
                error = LexicalError(
                    message="无效的十六进制数",
                    line=line,
                    column=col,
                    char=code[start:i]
                )
                return None, error, i, col, current_line

            while i < n and (code[i].isdigit() or code[i] in 'abcdefABCDEF'):
                i += 1

            lexeme = code[start:i]
            token = Token(
                type=TokenType.CONSTANT,
                value=lexeme,
                line=line,
                column=col,
                description=f"十六进制常量: {lexeme}"
            )
            return token, None, i, col + (i - start), current_line

        # 普通数字
        while i < n:
            ch = code[i]

            if state == self.STATE_NUMBER:
                if ch.isdigit():
                    i += 1
                elif ch == '.':
                    state = self.STATE_FLOAT
                    is_float = True
                    i += 1
                elif ch in ('e', 'E'):
                    state = self.STATE_FLOAT_EXP
                    has_exp = True
                    is_float = True
                    i += 1
                else:
                    break

            elif state == self.STATE_FLOAT:
                if ch.isdigit():
                    i += 1
                elif ch in ('e', 'E'):
                    state = self.STATE_FLOAT_EXP
                    has_exp = True
                    i += 1
                else:
                    break

            elif state == self.STATE_FLOAT_EXP:
                if ch in ('+', '-'):
                    state = self.STATE_FLOAT_EXP_SIGN
                    i += 1
                elif ch.isdigit():
                    state = self.STATE_FLOAT_EXP_NUM
                    i += 1
                else:
                    error = LexicalError(
                        message="无效的数字格式: 指数部分格式错误",
                        line=line,
                        column=col,
                        char=code[start:i]
                    )
                    return None, error, i, col, current_line

            elif state == self.STATE_FLOAT_EXP_SIGN:
                if ch.isdigit():
                    state = self.STATE_FLOAT_EXP_NUM
                    i += 1
                else:
                    error = LexicalError(
                        message="无效的数字格式: 指数后缺少数字",
                        line=line,
                        column=col,
                        char=code[start:i]
                    )
                    return None, error, i, col, current_line

            elif state == self.STATE_FLOAT_EXP_NUM:
                if ch.isdigit():
                    i += 1
                else:
                    break

        lexeme = code[start:i]

        # 验证格式
        if is_float and lexeme.endswith('.'):
            error = LexicalError(
                message=f"无效的浮点数格式: '{lexeme}' 不能以小数点结尾",
                line=line,
                column=col,
                char=lexeme
            )
            return None, error, i, col, current_line

        if has_exp:
            exp_pos = lexeme.lower().find('e')
            if exp_pos + 1 >= len(lexeme):
                error = LexicalError(
                    message="无效的指数格式: 指数后缺少数字",
                    line=line,
                    column=col,
                    char=lexeme
                )
                return None, error, i, col, current_line

            after_e = lexeme[exp_pos + 1:]
            if after_e in ('+', '-') or not after_e:
                error = LexicalError(
                    message="无效的指数格式: 指数后缺少数字",
                    line=line,
                    column=col,
                    char=lexeme
                )
                return None, error, i, col, current_line

        desc = f"浮点常量: {lexeme}" if is_float else f"整数常量: {lexeme}"
        token = Token(
            type=TokenType.CONSTANT,
            value=lexeme,
            line=line,
            column=col,
            description=desc
        )

        return token, None, i, col + (i - start), current_line

    def _scan_operator_or_delimiter(self, code: str, start: int, col: int, line: int) -> Tuple[Optional[Token], int, int, Optional[LexicalError]]:
        i = start
        n = len(code)

        # 首先检查非法运算符组合
        for pattern in self.invalid_operator_patterns:
            if i + len(pattern) <= n and code[i:i + len(pattern)] == pattern:
                error = LexicalError(
                    message=f"非法运算符组合: '{pattern}' - {self.suspicious_patterns.get(pattern, '无效的运算符序列')}",
                    line=line,
                    column=col,
                    char=pattern
                )
                return None, i + len(pattern), col + len(pattern), error

        # 匹配合法运算符（最长匹配）
        for length in [3, 2, 1]:
            if i + length <= n:
                candidate = code[i:i + length]
                if candidate in self.valid_operators:
                    token = Token(
                        type=TokenType.OPERATOR,
                        value=candidate,
                        line=line,
                        column=col,
                        description=f"运算符: {candidate}"
                    )
                    return token, i + length, col + length, None

        # 检查界符
        if code[i] in self.delimiters:
            token = Token(
                type=TokenType.DELIMITER,
                value=code[i],
                line=line,
                column=col,
                description=f"界符: {code[i]}"
            )
            return token, i + 1, col + 1, None

        return None, i, col, None

    def _check_adjacent_operators(self, tokens: List[Token], original_code: str) -> List[LexicalError]:
        errors = []

        for i in range(len(tokens) - 1):
            curr = tokens[i]
            next_tok = tokens[i + 1]

            if curr.type == TokenType.OPERATOR and next_tok.type == TokenType.OPERATOR:
                combined = curr.value + next_tok.value

                if combined not in self.valid_operators:
                    error = LexicalError(
                        message=f"非法运算符组合: '{curr.value}{next_tok.value}' - 两个运算符不能直接相邻",
                        line=curr.line,
                        column=curr.column,
                        char=curr.value + next_tok.value
                    )
                    errors.append(error)

            if curr.type == TokenType.OPERATOR and curr.value == '=':
                if next_tok.type == TokenType.OPERATOR and next_tok.value != '=':
                    error = LexicalError(
                        message=f"非法运算符组合: '={next_tok.value}' - 赋值运算符后不能直接跟其他运算符",
                        line=curr.line,
                        column=curr.column,
                        char=f"={next_tok.value}"
                    )
                    errors.append(error)

        return errors

    def get_token_types_info(self) -> str:
        """获取词法单元类型说明"""
        return """
╔═══════════════════════════════════════════════════════════════════════════════╗
║                          词法单元类型详细说明                                  ║
╚═══════════════════════════════════════════════════════════════════════════════╝

┌─────────────────────────────────────────────────────────────────────────────┐
│ 1. 关键字 (Keyword)                                                          │
├─────────────────────────────────────────────────────────────────────────────┤
│ 程序设计语言中具有特殊含义的保留字，不能用作标识符                           │
│ 示例：if, else, while, for, int, float, return, class, struct               │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│ 2. 标识符 (Identifier)                                                       │
├─────────────────────────────────────────────────────────────────────────────┤
│ 用户定义的名称，用于表示变量、函数、类等                                     │
│ 规则：以字母或下划线开头，后跟字母、数字或下划线                             │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│ 3. 常量 (Constant)                                                           │
├─────────────────────────────────────────────────────────────────────────────┤
│ 固定不变的值：整数常量、浮点常量、字符串常量、字符常量                       │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│ 4. 运算符 (Operator)                                                         │
├─────────────────────────────────────────────────────────────────────────────┤
│ 用于运算的符号：算术、关系、逻辑、位运算、赋值等                             │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│ 5. 界符 (Delimiter)                                                          │
├─────────────────────────────────────────────────────────────────────────────┤
│ 用于分隔程序结构的符号：; , ( ) { } [ ] . :                                   │
└─────────────────────────────────────────────────────────────────────────────┘
"""

    def get_dfa_info(self) -> str:
        """获取DFA设计说明"""
        return """
╔═══════════════════════════════════════════════════════════════════════════════╗
║                         DFA词法分析器设计说明                                  ║
╚═══════════════════════════════════════════════════════════════════════════════╝

【DFA定义】DFA = (Q, Σ, δ, q0, F)

【状态定义】
    STATE_START = 0              # 起始状态
    STATE_IDENT = 1              # 标识符状态
    STATE_NUMBER = 2             # 整数状态
    STATE_FLOAT = 3              # 浮点数状态
    STATE_FLOAT_EXP = 4          # 科学计数法状态
    STATE_HEX = 7                # 十六进制状态
    STATE_STRING = 9             # 字符串状态
    STATE_CHAR = 10              # 字符状态

【最长匹配原则】优先匹配更长的运算符（如 ++ 优先于 +）
"""


__all__ = ['DFALexicalAnalyzer']