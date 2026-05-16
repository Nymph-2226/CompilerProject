"""LL(1)语法分析器 - 包含FIRST/FOLLOW/预测分析表构造"""
# parser/ll1_parser.py
from typing import Dict, List, Set, Tuple, Optional, TYPE_CHECKING
from dataclasses import dataclass, field

# 改为绝对导入
from lexer.token import Token, TokenType

if TYPE_CHECKING:
    from .ast_node import ASTNode


@dataclass
class LL1ParseResult:
    success: bool
    ast_root: Optional['ASTNode'] = None
    errors: List[str] = field(default_factory=list)
    parse_steps: List[str] = field(default_factory=list)
    first_sets: Dict[str, Set[str]] = field(default_factory=dict)
    follow_sets: Dict[str, Set[str]] = field(default_factory=dict)
    predict_table: Dict[Tuple[str, str], List[str]] = field(default_factory=dict)

class ParseError(Exception):
    """解析异常"""
    pass


class LL1Parser:
    """
    LL(1)语法分析器

    文法定义（算术表达式）：
    E  → T E'
    E' → + T E' | - T E' | ε
    T  → F T'
    T' → * F T' | / F T' | ε
    F  → ( E ) | id | num
    """

    def __init__(self):
        # 非终结符
        self.non_terminals: Set[str] = {"E", "E'", "T", "T'", "F"}

        # 终结符
        self.terminals: Set[str] = {"+", "-", "*", "/", "(", ")", "id", "num", "$"}

        # 产生式
        self.productions: Dict[str, List[List[str]]] = {
            "E": [["T", "E'"]],
            "E'": [["+", "T", "E'"], ["-", "T", "E'"], []],  # [] 表示 ε
            "T": [["F", "T'"]],
            "T'": [["*", "F", "T'"], ["/", "F", "T'"], []],
            "F": [["(", "E", ")"], ["id"], ["num"]]
        }

        self.start_symbol: str = "E"

        # FIRST和FOLLOW集
        self.first: Dict[str, Set[str]] = {}
        self.follow: Dict[str, Set[str]] = {}

        # 预测分析表
        self.predict_table: Dict[Tuple[str, str], List[str]] = {}

        # 初始化
        self._compute_first_sets()
        self._compute_follow_sets()
        self._build_predict_table()

    def _compute_first_sets(self) -> None:
        """计算FIRST集"""
        # 初始化
        for nt in self.non_terminals:
            self.first[nt] = set()
        for t in self.terminals:
            if t != "$":
                self.first[t] = {t}

        changed = True
        max_iterations = 50  # 添加最大迭代次数
        iteration = 0
    
        while changed and iteration < max_iterations:
            iteration += 1
            changed = False
            for nt in self.non_terminals:
                for production in self.productions[nt]:
                    current_first = self._compute_first_of_sequence(production)
                    if not current_first.issubset(self.first[nt]):
                        self.first[nt].update(current_first)
                        changed = True

    def _compute_first_of_sequence(self, symbols: List[str]) -> Set[str]:
        """计算符号串的FIRST集"""
        result = set()
        all_have_epsilon = True

        for sym in symbols:
            if sym in self.non_terminals:
                result.update(self.first[sym] - {"ε"})
                if "ε" not in self.first[sym]:
                    all_have_epsilon = False
                    break
            elif sym in self.terminals:
                result.add(sym)
                all_have_epsilon = False
                break
            else:
                all_have_epsilon = False
                break

        if all_have_epsilon:
            result.add("ε")

        return result

    def _compute_follow_sets(self) -> None:
        """计算FOLLOW集"""
        for nt in self.non_terminals:
            self.follow[nt] = set()
        self.follow[self.start_symbol].add("$")

        changed = True
        max_iterations = 50  # 添加最大迭代次数
        iteration = 0
    
        while changed and iteration < max_iterations:
            iteration += 1
            changed = False
            for nt in self.non_terminals:
                for production in self.productions[nt]:
                    for i, sym in enumerate(production):
                        if sym in self.non_terminals:
                            beta = production[i + 1:]
                            first_beta = self._compute_first_of_sequence(beta)
                        
                            if not first_beta.issubset(self.follow[sym]):
                                self.follow[sym].update(first_beta - {"ε"})
                                changed = True
                        
                            if "ε" in first_beta or not beta:
                                if not self.follow[nt].issubset(self.follow[sym]):
                                    self.follow[sym].update(self.follow[nt])
                                    changed = True

    def _build_predict_table(self) -> None:
        """构造预测分析表"""
        self.predict_table.clear()

        for nt in self.non_terminals:
            for production in self.productions[nt]:
                # 计算产生式的FIRST集
                first_prod = self._compute_first_of_sequence(production)

                # 对于每个终结符a ∈ FIRST(production)
                for a in first_prod:
                    if a != "ε":
                        self.predict_table[(nt, a)] = production

                # 如果 ε ∈ FIRST(production)
                if "ε" in first_prod:
                    for b in self.follow[nt]:
                        self.predict_table[(nt, b)] = production

    def get_first_set(self, symbol: str) -> Set[str]:
        """获取指定符号的FIRST集"""
        if symbol in self.first:
            return self.first[symbol]
        elif symbol in self.terminals:
            return {symbol}
        return set()

    def get_follow_set(self, symbol: str) -> Set[str]:
        """获取指定符号的FOLLOW集"""
        if symbol in self.follow:
            return self.follow[symbol]
        return set()

    def get_predict_table(self) -> Dict[Tuple[str, str], List[str]]:
        """获取预测分析表"""
        return self.predict_table

    def check_ll1(self) -> Tuple[bool, List[str]]:
        """
        检查文法是否为LL(1)文法
        返回: (是否LL(1), 冲突信息列表)
        """
        conflicts = []

        for nt in self.non_terminals:
            # 检查每个非终结符的产生式
            productions = self.productions[nt]
            for i, prod1 in enumerate(productions):
                first1 = self._compute_first_of_sequence(prod1)
                for j, prod2 in enumerate(productions):
                    if i >= j:
                        continue
                    first2 = self._compute_first_of_sequence(prod2)

                    # 检查FIRST集冲突
                    intersection = first1 & first2
                    if intersection and "ε" not in intersection:
                        conflicts.append(
                            f"非终结符 '{nt}' 的产生式 {i+1} 和 {j+1} 的FIRST集存在交集: {intersection}")

                    # 检查 ε 产生式与FOLLOW集冲突
                    if "ε" in first1:
                        for a in self.follow[nt]:
                            if a in first2 and a != "ε":
                                conflicts.append(
                                    f"非终结符 '{nt}' 的 ε 产生式与产生式 {j+1} 在终结符 '{a}' 上冲突")

        return len(conflicts) == 0, conflicts

    def parse(self, tokens: List[Token]) -> LL1ParseResult:
        """
        执行LL(1)语法分析
        """
        result = LL1ParseResult(success=False)
        result.first_sets = self.first.copy()
        result.follow_sets = self.follow.copy()
        result.predict_table = self.predict_table.copy()

        # 获取token值列表
        token_values = [self._token_to_terminal(tok) for tok in tokens]
        token_values.append("$")

        # 解析栈
        stack = ["$", self.start_symbol]
        pos = 0
        steps = []

        steps.append(f"初始栈: {' '.join(stack[::-1])}")
        steps.append(f"输入: {' '.join(token_values)}")
        steps.append("-" * 40)

        while stack:
            top = stack.pop()
            current = token_values[pos] if pos < len(token_values) else "$"

            steps.append(f"栈顶: {top}, 当前输入: {current}")

            if top in self.terminals:
                if top == current:
                    steps.append(f"匹配: {top}")
                    pos += 1
                else:
                    error_msg = f"语法错误: 期望 '{top}'，但遇到 '{current}'"
                    steps.append(f"❌ {error_msg}")
                    result.errors.append(error_msg)
                    result.parse_steps = steps
                    return result
            elif top in self.non_terminals:
                # 查预测分析表
                key = (top, current)
                if key in self.predict_table:
                    production = self.predict_table[key]
                    if production:
                        steps.append(f"展开 {top} → {' '.join(production)}")
                        # 逆序压栈
                        for sym in reversed(production):
                            if sym != "ε":
                                stack.append(sym)
                    else:
                        steps.append(f"展开 {top} → ε")
                else:
                    error_msg = f"语法错误: 在输入 '{current}' 处无法为 '{top}' 选择产生式"
                    steps.append(f"❌ {error_msg}")
                    result.errors.append(error_msg)
                    result.parse_steps = steps
                    return result
            else:
                error_msg = f"语法错误: 非法符号 '{top}'"
                steps.append(f"❌ {error_msg}")
                result.errors.append(error_msg)
                result.parse_steps = steps
                return result

            steps.append(f"栈: {' '.join(stack[::-1])}")

        if pos == len(token_values) - 1:
            steps.append("✅ 语法分析成功！")
            result.success = True
        else:
            steps.append(f"❌ 语法分析失败: 输入未完全消耗，剩余 {token_values[pos:]}")

        result.parse_steps = steps
        return result

    def _token_to_terminal(self, token: Token) -> str:
        """将Token转换为终结符"""
        if token.type == TokenType.IDENTIFIER:
            return "id"
        elif token.type == TokenType.CONSTANT:
            # 判断是否为数字
            if token.value.replace('.', '').replace('-', '').isdigit():
                return "num"
            # 字符串常量
            return "str"
        elif token.type == TokenType.KEYWORD:
            return token.value
        elif token.type == TokenType.OPERATOR:
            return token.value
        elif token.type == TokenType.DELIMITER:
            return token.value
        else:
            return token.value

    def print_first_follow(self) -> str:
        """打印FIRST和FOLLOW集"""
        output = []
        output.append("=" * 50)
        output.append("FIRST 集")
        output.append("=" * 50)

        for nt in sorted(self.non_terminals):
            first_set = self.first.get(nt, set())
            output.append(f"FIRST({nt}) = {{{', '.join(sorted(first_set))}}}")

        output.append("\n" + "=" * 50)
        output.append("FOLLOW 集")
        output.append("=" * 50)

        for nt in sorted(self.non_terminals):
            follow_set = self.follow.get(nt, set())
            output.append(f"FOLLOW({nt}) = {{{', '.join(sorted(follow_set))}}}")

        output.append("\n" + "=" * 50)
        output.append("预测分析表")
        output.append("=" * 50)

        for (nt, term), prod in sorted(self.predict_table.items()):
            if prod:
                prod_str = ' '.join(prod)
            else:
                prod_str = "ε"
            output.append(f"M[{nt}, {term}] = {nt} → {prod_str}")

        return "\n".join(output)

    def get_grammar_info(self) -> str:
        """获取文法信息"""
        info = []
        info.append("算术表达式文法（已消除左递归）:")
        info.append("")
        info.append("E  → T E'")
        info.append("E' → + T E' | - T E' | ε")
        info.append("T  → F T'")
        info.append("T' → * F T' | / F T' | ε")
        info.append("F  → ( E ) | id | num")
        info.append("")
        info.append("说明:")
        info.append("- id: 标识符（变量名）")
        info.append("- num: 数字常量")
        info.append("- ε: 空产生式")

        return "\n".join(info)


__all__ = ['LL1Parser', 'LL1ParseResult', 'ParseError']