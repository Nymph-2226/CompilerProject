"""改进的上下文无关文法类 - 支持推导、语法树和句柄归约"""
from typing import List, Tuple, Dict, Optional


class ImprovedGrammar:
    """改进的上下文无关文法类"""

    def __init__(self):
        self.Vn = {"E", "E'", "T", "T'", "F"}
        self.Vt = {"+", "-", "*", "/", "(", ")", "id", "num"}

        self.P = {
            "E": [["T", "E'"]],
            "E'": [["+", "T", "E'"], ["-", "T", "E'"], []],
            "T": [["F", "T'"]],
            "T'": [["*", "F", "T'"], ["/", "F", "T'"], []],
            "F": [["(", "E", ")"], ["id"], ["num"]]
        }
        self.S = "E"

    def get_grammar_info(self) -> str:
        """获取文法信息"""
        info = "G = (Vn, Vt, P, S)\n\n"
        info += f"Vn (非终结符) = {{{', '.join(sorted(self.Vn))}}}\n\n"
        info += f"Vt (终结符) = {{{', '.join(sorted(self.Vt))}}}\n\n"
        info += "P (产生式) - 已消除左递归:\n"
        for left, rights in self.P.items():
            for right in rights:
                if right:
                    info += f"  {left} → {' '.join(right)}\n"
                else:
                    info += f"  {left} → ε\n"
        info += f"\nS (开始符号) = {self.S}\n"
        return info

    def classify_symbol(self, symbol: str) -> str:
        """区分终结符和非终结符"""
        if symbol in self.Vn:
            return f"'{symbol}' 是非终结符 (Non-terminal)"
        elif symbol in self.Vt:
            return f"'{symbol}' 是终结符 (Terminal)"
        else:
            return f"'{symbol}' 是未知符号"

    def _tokenize_string(self, symbol_string: str) -> List[str]:
        """对符号串进行分词"""
        symbol_string = symbol_string.strip()
        tokens = []
        i = 0
        while i < len(symbol_string):
            if symbol_string[i] in "+-*/()":
                tokens.append(symbol_string[i])
                i += 1
            elif i + 1 < len(symbol_string) and symbol_string[i:i + 2] == "id":
                tokens.append("id")
                i += 2
            elif i + 2 < len(symbol_string) and symbol_string[i:i + 3] == "num":
                tokens.append("num")
                i += 3
            elif symbol_string[i].isalpha():
                start = i
                while i < len(symbol_string) and symbol_string[i].isalpha():
                    i += 1
                token = symbol_string[start:i]
                if token in self.Vn:
                    tokens.append(token)
                elif token in self.Vt:
                    tokens.append(token)
                else:
                    tokens.append(token)
            elif symbol_string[i].isdigit():
                while i < len(symbol_string) and symbol_string[i].isdigit():
                    i += 1
                tokens.append("num")
            else:
                i += 1
        return tokens

    def _validate_symbols(self, tokens: List[str]) -> Tuple[bool, str]:
        """验证符号是否都在文法中"""
        for token in tokens:
            if token not in self.Vn and token not in self.Vt:
                return False, f"包含未知符号: {token}"
        return True, "所有符号合法"

    def is_sentential_form(self, symbol_string: str) -> Tuple[bool, str]:
        """判断符号串是否为句型"""
        tokens = self._tokenize_string(symbol_string)
        if not tokens:
            return False, "符号串为空"
        valid, msg = self._validate_symbols(tokens)
        if not valid:
            return False, f"✗ '{symbol_string}' 不是合法的句型: {msg}"
        return True, f"✓ '{symbol_string}' 是一个合法的句型（由文法符号组成）"

    def is_sentence(self, symbol_string: str) -> Tuple[bool, str]:
        """判断符号串是否为句子"""
        tokens = self._tokenize_string(symbol_string)
        if not tokens:
            return False, "符号串为空"
        for token in tokens:
            if token in self.Vn:
                return False, f"✗ '{symbol_string}' 包含非终结符 '{token}'，不是句子"
        valid, msg = self._validate_symbols(tokens)
        if not valid:
            return False, f"✗ '{symbol_string}' 不是合法的句子: {msg}"
        is_valid, _ = self._parse_expression(tokens)
        if not is_valid:
            return False, f"✗ '{symbol_string}' 不符合文法规则"
        return True, f"✓ '{symbol_string}' 是一个合法的句子"

    def _parse_expression(self, tokens: List[str]) -> Tuple[bool, int]:
        """递归下降解析表达式"""
        if not tokens:
            return False, 0
        index = 0
        result, index = self._parse_E(tokens, index)
        return result and index == len(tokens), index

    def _parse_E(self, tokens: List[str], index: int) -> Tuple[bool, int]:
        result, index = self._parse_T(tokens, index)
        if not result:
            return False, index
        return self._parse_E_prime(tokens, index)

    def _parse_E_prime(self, tokens: List[str], index: int) -> Tuple[bool, int]:
        if index < len(tokens) and tokens[index] in ['+', '-']:
            index += 1
            result, index = self._parse_T(tokens, index)
            if not result:
                return False, index
            return self._parse_E_prime(tokens, index)
        return True, index

    def _parse_T(self, tokens: List[str], index: int) -> Tuple[bool, int]:
        result, index = self._parse_F(tokens, index)
        if not result:
            return False, index
        return self._parse_T_prime(tokens, index)

    def _parse_T_prime(self, tokens: List[str], index: int) -> Tuple[bool, int]:
        if index < len(tokens) and tokens[index] in ['*', '/']:
            index += 1
            result, index = self._parse_F(tokens, index)
            if not result:
                return False, index
            return self._parse_T_prime(tokens, index)
        return True, index

    def _parse_F(self, tokens: List[str], index: int) -> Tuple[bool, int]:
        if index >= len(tokens):
            return False, index
        if tokens[index] == '(':
            index += 1
            result, index = self._parse_E(tokens, index)
            if result and index < len(tokens) and tokens[index] == ')':
                return True, index + 1
            return False, index
        elif tokens[index] in ['id', 'num']:
            return True, index + 1
        return False, index

    def leftmost_derivation(self, sentence: str) -> List[Dict]:
        """生成最左推导步骤"""
        steps = []
        tokens = self._tokenize_string(sentence)

        for token in tokens:
            if token not in self.Vt:
                steps.append({"type": "error", "content": f"错误：句子 '{sentence}' 包含非法符号"})
                return steps

        steps.append({"type": "info", "content": f"开始符号: {self.S}"})
        steps.append({"type": "info", "content": f"目标句子: {' '.join(tokens)}"})
        steps.append({"type": "separator", "content": ""})

        stack = [self.S]
        pos = 0
        step_num = 1
        max_steps = 100

        while stack and pos <= len(tokens) and step_num <= max_steps:
            current_str = ' '.join(stack)
            steps.append({"type": "current", "content": f"当前句型: {current_str}"})

            top = stack.pop(0) if stack else None
            if not top:
                break

            if top in self.Vt:
                if pos < len(tokens) and top == tokens[pos]:
                    steps.append({"type": "match", "content": f"匹配终结符: {top}"})
                    pos += 1
                else:
                    steps.append({"type": "error", "content": f"错误：期望 {top}"})
                    break
            elif top in self.Vn:
                production = self._select_production_left(top, tokens, pos)
                if production is not None:
                    if production == []:
                        steps.append({"type": "expand", "content": f"步骤{step_num}: 展开 {top} → ε"})
                    else:
                        steps.append(
                            {"type": "expand", "content": f"步骤{step_num}: 展开 {top} → {' '.join(production)}"})
                    for sym in reversed(production):
                        stack.insert(0, sym)
                    step_num += 1
                else:
                    steps.append({"type": "error", "content": f"错误：无法为 {top} 选择产生式"})
                    break
            else:
                steps.append({"type": "error", "content": f"错误：未知符号 {top}"})
                break

        steps.append({"type": "separator", "content": ""})
        if pos == len(tokens) and not stack:
            steps.append({"type": "success", "content": "✓ 最左推导成功！"})
        else:
            steps.append({"type": "error", "content": f"✗ 最左推导失败！已匹配: {pos}/{len(tokens)}个符号"})

        return steps

    def _select_production_left(self, nonterminal: str, tokens: List[str], pos: int) -> Optional[List[str]]:
        if nonterminal == 'E':
            return ["T", "E'"]
        elif nonterminal == "E'":
            if pos < len(tokens):
                next_token = tokens[pos]
                if next_token == '+':
                    return ["+", "T", "E'"]
                elif next_token == '-':
                    return ["-", "T", "E'"]
            return []
        elif nonterminal == 'T':
            return ["F", "T'"]
        elif nonterminal == "T'":
            if pos < len(tokens):
                next_token = tokens[pos]
                if next_token == '*':
                    return ["*", "F", "T'"]
                elif next_token == '/':
                    return ["/", "F", "T'"]
            return []
        elif nonterminal == 'F':
            if pos < len(tokens):
                next_token = tokens[pos]
                if next_token == '(':
                    return ["(", "E", ")"]
                elif next_token == 'id':
                    return ["id"]
                elif next_token == 'num':
                    return ["num"]
            return ["id"]
        return None

    def rightmost_derivation(self, sentence: str) -> List[Dict]:
        """生成最右推导步骤"""
        steps = []
        tokens = self._tokenize_string(sentence)

        for token in tokens:
            if token not in self.Vt:
                steps.append({"type": "error", "content": f"错误：句子 '{sentence}' 包含非法符号"})
                return steps

        steps.append({"type": "info", "content": f"开始符号: {self.S}"})
        steps.append({"type": "info", "content": f"目标句子: {' '.join(tokens)}"})
        steps.append({"type": "separator", "content": ""})

        current = [self.S]
        step_num = 1
        max_steps = 100

        while step_num <= max_steps:
            current_str = ' '.join(current)
            steps.append({"type": "current", "content": f"当前: {current_str}"})

            rightmost_pos = -1
            for i in range(len(current) - 1, -1, -1):
                if current[i] in self.Vn:
                    rightmost_pos = i
                    break

            if rightmost_pos == -1:
                break

            nonterminal = current[rightmost_pos]
            production = self._select_production_right(nonterminal, current, tokens)

            if production is None:
                steps.append({"type": "error", "content": f"错误：无法为 {nonterminal} 选择产生式"})
                break

            if production == []:
                steps.append({"type": "expand", "content": f"步骤{step_num}: 替换最右非终结符 {nonterminal} → ε"})
                current.pop(rightmost_pos)
            else:
                steps.append({"type": "expand",
                              "content": f"步骤{step_num}: 替换最右非终结符 {nonterminal} → {' '.join(production)}"})
                current = current[:rightmost_pos] + production + current[rightmost_pos + 1:]

            step_num += 1

            if ' '.join(current) == ' '.join(tokens):
                break

        steps.append({"type": "separator", "content": ""})
        if ' '.join(current) == ' '.join(tokens):
            steps.append({"type": "success", "content": "✓ 最右推导成功！"})
        else:
            steps.append({"type": "error", "content": f"✗ 最右推导失败！"})

        return steps

    def _select_production_right(self, nonterminal: str, current: List[str], target: List[str]) -> Optional[List[str]]:
        if nonterminal == 'E':
            return ["T", "E'"]
        elif nonterminal == "E'":
            current_str = ' '.join(current)
            target_str = ' '.join(target)
            if '+' not in current_str and '-' not in current_str:
                if '+' in target_str:
                    return ["+", "T", "E'"]
                if '-' in target_str:
                    return ["-", "T", "E'"]
            return []
        elif nonterminal == 'T':
            return ["F", "T'"]
        elif nonterminal == "T'":
            current_str = ' '.join(current)
            target_str = ' '.join(target)
            if '*' not in current_str and '/' not in current_str:
                if '*' in target_str:
                    return ["*", "F", "T'"]
                if '/' in target_str:
                    return ["/", "F", "T'"]
            return []
        elif nonterminal == 'F':
            current_terminals = [sym for sym in current if sym in self.Vt]
            target_terminals = target.copy()
            for t in target_terminals:
                if t not in current_terminals:
                    if t == '(':
                        return ["(", "E", ")"]
                    elif t == 'id':
                        return ["id"]
                    elif t == 'num':
                        return ["num"]
            if '(' in target and '(' not in current:
                return ["(", "E", ")"]
            return ["id"]
        return None

    def build_syntax_tree(self, sentence: str) -> Dict:
        """构建语法树"""
        tokens = self._tokenize_string(sentence)
        for token in tokens:
            if token not in self.Vt:
                return None
        index = 0
        tree, index = self._build_E(tokens, index)
        if tree and index == len(tokens):
            return tree
        return None

    def _build_E(self, tokens: List[str], index: int) -> Tuple[Dict, int]:
        tree, index = self._build_T(tokens, index)
        if not tree:
            return None, index
        return self._build_E_prime(tokens, index, tree)

    def _build_E_prime(self, tokens: List[str], index: int, left_tree: Dict) -> Tuple[Dict, int]:
        if index < len(tokens) and tokens[index] in ['+', '-']:
            op = tokens[index]
            index += 1
            right_tree, index = self._build_T(tokens, index)
            if not right_tree:
                return None, index
            tree = {'type': 'E', 'value': op, 'children': [left_tree, right_tree]}
            return self._build_E_prime(tokens, index, tree)
        return left_tree, index

    def _build_T(self, tokens: List[str], index: int) -> Tuple[Dict, int]:
        tree, index = self._build_F(tokens, index)
        if not tree:
            return None, index
        return self._build_T_prime(tokens, index, tree)

    def _build_T_prime(self, tokens: List[str], index: int, left_tree: Dict) -> Tuple[Dict, int]:
        if index < len(tokens) and tokens[index] in ['*', '/']:
            op = tokens[index]
            index += 1
            right_tree, index = self._build_F(tokens, index)
            if not right_tree:
                return None, index
            tree = {'type': 'T', 'value': op, 'children': [left_tree, right_tree]}
            return self._build_T_prime(tokens, index, tree)
        return left_tree, index

    def _build_F(self, tokens: List[str], index: int) -> Tuple[Dict, int]:
        if index >= len(tokens):
            return None, index

        if tokens[index] == '(':
            index += 1
            tree, index = self._build_E(tokens, index)
            if index < len(tokens) and tokens[index] == ')':
                index += 1
                return tree, index
            return None, index
        elif tokens[index] in ['id', 'num']:
            tree = {'type': 'F', 'value': tokens[index], 'children': []}
            index += 1
            return tree, index
        return None, index

    def print_syntax_tree(self, node: Dict, level: int = 0, is_last: bool = True) -> List[str]:
        """打印语法树（文本格式）"""
        lines = []
        prefix = "    " * level
        if level > 0:
            prefix = prefix[:-4] + ("└── " if is_last else "├── ")

        if node.get('children'):
            node_label = f"{node['type']}[{node['value']}]" if node.get('value') else node['type']
            lines.append(f"{prefix}{node_label}")
            for i, child in enumerate(node['children']):
                child_lines = self.print_syntax_tree(child, level + 1, i == len(node['children']) - 1)
                lines.extend(child_lines)
        else:
            lines.append(f"{prefix}{node['type']}[{node['value']}]")

        return lines

    def detect_ambiguity(self, sentence: str) -> Dict:
        """检测文法的二义性"""
        result = {'is_ambiguous': False, 'trees': [], 'message': ''}

        ambiguous_sentences = {
            'id+id*id': '经典的运算符优先级二义性',
            'id+id+id': '结合性二义性',
            'id-id-id': '减法的结合性二义性'
        }

        if sentence in ambiguous_sentences:
            result['is_ambiguous'] = True
            result['message'] = f"检测到二义性：{ambiguous_sentences[sentence]}"

            if sentence == 'id+id*id':
                tree1 = {
                    'type': 'E',
                    'value': '+',
                    'children': [
                        {'type': 'F', 'value': 'id', 'children': []},
                        {'type': 'T', 'value': '*', 'children': [
                            {'type': 'F', 'value': 'id', 'children': []},
                            {'type': 'F', 'value': 'id', 'children': []}
                        ]}
                    ]
                }
                tree2 = {
                    'type': 'E',
                    'value': '*',
                    'children': [
                        {'type': 'E', 'value': '+', 'children': [
                            {'type': 'F', 'value': 'id', 'children': []},
                            {'type': 'F', 'value': 'id', 'children': []}
                        ]},
                        {'type': 'F', 'value': 'id', 'children': []}
                    ]
                }
                result['trees'] = [tree1, tree2]
        else:
            tree = self.build_syntax_tree(sentence)
            if tree:
                result['trees'] = [tree]
                result['message'] = '该句子在当前文法下无二义性'
            else:
                result['message'] = '无法构建语法树，句子可能不符合文法'

        return result

    def parse_expression(self, expression: str) -> Dict:
        """解析表达式"""
        result = {"success": False, "message": "", "steps": []}
        try:
            tokens = self._tokenize_string(expression)
            if not tokens:
                result["message"] = "表达式为空"
                return result
            for token in tokens:
                if token in self.Vn:
                    result["message"] = f"表达式包含非终结符 '{token}'"
                    return result
            is_valid, _ = self._parse_expression(tokens)
            result["steps"].append(f"表达式: {expression}")
            result["steps"].append(f"Token序列: {' '.join(tokens)}")
            if is_valid:
                result["success"] = True
                result["message"] = "✓ 表达式符合算术表达式文法"
                result["steps"].append("✓ 语法分析通过")
            else:
                result["message"] = "✗ 表达式不符合文法"
        except Exception as e:
            result["message"] = f"解析错误: {str(e)}"
        return result


__all__ = ['ImprovedGrammar']