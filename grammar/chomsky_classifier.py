"""乔姆斯基文法自动判定器"""
# grammar/chomsky_classifier.py
from typing import List, Tuple, Set, Dict, Optional


class ChomskyClassifier:
    """乔姆斯基文法自动判定器"""

    def __init__(self):
        self.grammar_types = {
            0: {
                "name": "0型文法（无限制文法）",
                "rule": "α → β，其中 α 至少包含一个非终结符",
                "restriction": "无任何限制",
                "examples": ["AB → CD", "aAb → bBa"],
                "applications": "图灵机、自然语言处理",
                "automaton": "图灵机 (Turing Machine)",
                "language": "递归可枚举语言"
            },
            1: {
                "name": "1型文法（上下文有关文法）",
                "rule": "αAβ → αγβ，其中 γ ≠ ε",
                "restriction": "|α| ≤ |β|，左部长度不超过右部",
                "examples": ["aAb → aBcb", "AB → CDE"],
                "applications": "自然语言语法分析、DNA序列分析",
                "automaton": "线性有界自动机 (LBA)",
                "language": "上下文有关语言"
            },
            2: {
                "name": "2型文法（上下文无关文法）",
                "rule": "A → γ，A是单个非终结符",
                "restriction": "左部必须是单个非终结符",
                "examples": ["E → E+T | T", "S → aSb | ε"],
                "applications": "程序设计语言语法、JSON/XML解析",
                "automaton": "下推自动机 (PDA)",
                "language": "上下文无关语言"
            },
            3: {
                "name": "3型文法（正则文法）",
                "rule": "A → aB 或 A → a（右线性）",
                "restriction": "右部只能有一个非终结符且在末尾",
                "examples": ["S → aS | b", "A → aB, B → b"],
                "applications": "词法分析、正则表达式引擎",
                "automaton": "有限自动机 (FA/DFA/NFA)",
                "language": "正则语言"
            }
        }

    def _parse_production(self, production: str) -> Tuple[str, str]:
        production = production.strip()
        if "→" in production:
            left, right = production.split("→", 1)
        elif "->" in production:
            left, right = production.split("->", 1)
        else:
            raise ValueError("产生式格式错误，请使用 → 或 ->")
        return left.strip(), right.strip()

    def _is_nonterminal(self, symbol: str, nonterminals: Set[str]) -> bool:
        if symbol in nonterminals:
            return True
        if symbol.isupper():
            return True
        if symbol.startswith('<') and symbol.endswith('>'):
            return True
        return False

    def classify_grammar(self, productions_text: str) -> Dict:
        """判定文法类型"""
        result = {
            "success": False,
            "type": None,
            "type_name": "",
            "reasoning": [],
            "productions": [],
            "message": "",
            "detailed_info": None
        }

        try:
            lines = [line.strip() for line in productions_text.strip().split('\n') if line.strip()]
            productions = []

            for line in lines:
                if line.startswith('#'):
                    continue
                left, right = self._parse_production(line)
                productions.append((left, right))

            if not productions:
                result["message"] = "未输入有效的产生式"
                return result

            result["productions"] = productions
            result["reasoning"].append(f"共输入 {len(productions)} 条产生式")
            result["reasoning"].append("")

            nonterminals = set()
            for left, _ in productions:
                for char in left:
                    if char.isupper() or (char.startswith('<') and char.endswith('>')):
                        nonterminals.add(char)

            result["reasoning"].append(f"识别到的非终结符: {nonterminals if nonterminals else '{默认大写字母}'}")
            result["reasoning"].append("")

            is_type3 = self._check_type3(productions, nonterminals)
            if is_type3:
                result["type"] = 3
                result["type_name"] = "3型文法（正则文法）"
                result["detailed_info"] = self.grammar_types[3]
                result["reasoning"].append("【判定结果】3型文法（正则文法）")
                result["success"] = True
                return result

            is_type2 = self._check_type2(productions, nonterminals)
            if is_type2:
                result["type"] = 2
                result["type_name"] = "2型文法（上下文无关文法）"
                result["detailed_info"] = self.grammar_types[2]
                result["reasoning"].append("【判定结果】2型文法（上下文无关文法）")
                result["success"] = True
                return result

            is_type1 = self._check_type1(productions)
            if is_type1:
                result["type"] = 1
                result["type_name"] = "1型文法（上下文有关文法）"
                result["detailed_info"] = self.grammar_types[1]
                result["reasoning"].append("【判定结果】1型文法（上下文有关文法）")
                result["success"] = True
                return result

            result["type"] = 0
            result["type_name"] = "0型文法（无限制文法）"
            result["detailed_info"] = self.grammar_types[0]
            result["reasoning"].append("【判定结果】0型文法（无限制文法）")
            result["success"] = True

        except Exception as e:
            result["message"] = f"解析错误: {str(e)}"

        return result

    def _check_type3(self, productions: List[Tuple[str, str]], nonterminals: Set[str]) -> bool:
        for left, right in productions:
            if len(left) != 1 or not self._is_nonterminal(left, nonterminals):
                return False

            if right == "ε" or right == "":
                continue

            if len(right) == 1:
                if self._is_nonterminal(right, nonterminals):
                    return False
            elif len(right) == 2:
                if self._is_nonterminal(right[0], nonterminals) and not self._is_nonterminal(right[1], nonterminals):
                    continue
                elif not self._is_nonterminal(right[0], nonterminals) and self._is_nonterminal(right[1], nonterminals):
                    continue
                else:
                    return False
            else:
                return False
        return True

    def _check_type2(self, productions: List[Tuple[str, str]], nonterminals: Set[str]) -> bool:
        for left, _ in productions:
            if len(left) != 1 or not self._is_nonterminal(left, nonterminals):
                return False
        return True

    def _check_type1(self, productions: List[Tuple[str, str]]) -> bool:
        for left, right in productions:
            if right == "ε" or right == "":
                continue
            if len(left) > len(right):
                return False
        return True

    def get_grammar_info(self) -> str:
        """获取文法体系信息"""
        return """
╔═══════════════════════════════════════════════════════════════════════════════╗
║                        乔姆斯基文法体系 (Chomsky Hierarchy)                    ║
╚═══════════════════════════════════════════════════════════════════════════════╝

┌─────────────────────────────────────────────────────────────────────────────┐
│                          0型文法（无限制文法）                                │
├─────────────────────────────────────────────────────────────────────────────┤
│ 规则：α → β，其中 α 至少包含一个非终结符                                     │
│ 自动机：图灵机 (Turing Machine)                                              │
└─────────────────────────────────────────────────────────────────────────────┘
                                    ↓
┌─────────────────────────────────────────────────────────────────────────────┐
│                        1型文法（上下文有关文法）                              │
├─────────────────────────────────────────────────────────────────────────────┤
│ 规则：αAβ → αγβ，其中 γ ≠ ε                                                │
│ 限制：|α| ≤ |β|，左部长度不超过右部                                          │
│ 自动机：线性有界自动机 (LBA)                                                 │
└─────────────────────────────────────────────────────────────────────────────┘
                                    ↓
┌─────────────────────────────────────────────────────────────────────────────┐
│                      2型文法（上下文无关文法）                                │
├─────────────────────────────────────────────────────────────────────────────┤
│ 规则：A → γ，A是单个非终结符                                                │
│ 限制：左部必须是单个非终结符                                                 │
│ 自动机：下推自动机 (PDA)                                                     │
└─────────────────────────────────────────────────────────────────────────────┘
                                    ↓
┌─────────────────────────────────────────────────────────────────────────────┐
│                          3型文法（正则文法）                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│ 规则：A → aB 或 A → a（右线性）                                              │
│ 限制：右部只能有一个非终结符且在末尾                                         │
│ 自动机：有限自动机 (FA/DFA/NFA)                                              │
└─────────────────────────────────────────────────────────────────────────────┘

【包含关系】3型文法 ⊂ 2型文法 ⊂ 1型文法 ⊂ 0型文法
"""

    def get_comparison_table(self) -> str:
        """获取四类文法对比表"""
        return """
╔══════╦════════════════════╦════════════════════╦════════════════════╦════════════════════╗
║ 类型 ║      0型文法       ║      1型文法       ║      2型文法       ║      3型文法       ║
╠══════╬════════════════════╬════════════════════╬════════════════════╬════════════════════╣
║ 名称 ║    无限制文法      ║   上下文有关文法   ║   上下文无关文法   ║      正则文法      ║
╠══════╬════════════════════╬════════════════════╬════════════════════╬════════════════════╣
║ 规则 ║    α → β          ║   αAβ → αγβ      ║     A → γ         ║  A → aB 或 A → a  ║
║ 形式 ║  α至少1个非终结符  ║     γ ≠ ε         ║                    ║    右线性文法     ║
╠══════╬════════════════════╬════════════════════╬════════════════════╬════════════════════╣
║ 自动 ║      图灵机        ║   线性有界自动机   ║     下推自动机     ║    有限自动机     ║
║ 机   ║     (TM)           ║       (LBA)        ║       (PDA)        ║     (FA/NFA)      ║
╠══════╬════════════════════╬════════════════════╬════════════════════╬════════════════════╣
║ 语言 ║   递归可枚举语言   ║   上下文有关语言   ║   上下文无关语言   ║     正则语言      ║
╠══════╬════════════════════╬════════════════════╬════════════════════╬════════════════════╣
║ 应用 ║   图灵机理论       ║   自然语言处理     ║   程序设计语言     ║    词法分析       ║
╚══════╩════════════════════╩════════════════════╩════════════════════╩════════════════════╝
"""


__all__ = ['ChomskyClassifier']