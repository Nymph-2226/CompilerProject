"""
LL(1)文法分析器
自动计算FIRST集、FOLLOW集、构造预测分析表、检测LL(1)冲突
"""

from typing import Dict, List, Set, Tuple, Optional
from dataclasses import dataclass, field


@dataclass
class LL1AnalysisResult:
    """LL(1)分析结果"""
    success: bool
    first_sets: Dict[str, Set[str]] = field(default_factory=dict)
    follow_sets: Dict[str, Set[str]] = field(default_factory=dict)
    predict_table: Dict[Tuple[str, str], List[str]] = field(default_factory=dict)
    is_ll1: bool = False
    conflicts: List[str] = field(default_factory=list)
    grammar_info: str = ""


class LL1Analyzer:
    """
    LL(1)文法分析器
    
    功能：
    1. 自动计算FIRST集
    2. 自动计算FOLLOW集
    3. 构造预测分析表
    4. 检测LL(1)冲突
    """
    
    def __init__(self):
        # 非终结符集合
        self.non_terminals: Set[str] = set()
        # 终结符集合
        self.terminals: Set[str] = set()
        # 产生式 {左部: [[右部1], [右部2], ...]}
        self.productions: Dict[str, List[List[str]]] = {}
        # 开始符号
        self.start_symbol: str = ""
        
        # FIRST集
        self.first: Dict[str, Set[str]] = {}
        # FOLLOW集
        self.follow: Dict[str, Set[str]] = {}
        # 预测分析表
        self.predict_table: Dict[Tuple[str, str], List[str]] = {}
    
    def set_grammar(self, productions_text: str, start_symbol: str = "Feedback"):
        """
        设置文法
        
        Args:
            productions_text: 产生式文本，每行格式 "左部 -> 右部1 右部2 ..."
            start_symbol: 开始符号
        """
        self.productions.clear()
        self.non_terminals.clear()
        self.terminals.clear()
        self.start_symbol = start_symbol
        
        lines = [line.strip() for line in productions_text.strip().split('\n') if line.strip()]
        
        for line in lines:
            # 跳过注释
            if line.startswith('#'):
                continue
            
            # 解析产生式
            if '->' in line:
                left, right = line.split('->', 1)
            elif '→' in line:
                left, right = line.split('→', 1)
            else:
                continue
            
            left = left.strip()
            right = right.strip()
            
            # 添加非终结符
            self.non_terminals.add(left)
            
            # 解析右部（支持 | 分隔的多个产生式）
            if '|' in right:
                right_parts = [r.strip() for r in right.split('|')]
            else:
                right_parts = [right]
            
            for part in right_parts:
                if part == 'ε' or part == '':
                    symbols = []
                else:
                    symbols = part.split()
                
                if left not in self.productions:
                    self.productions[left] = []
                self.productions[left].append(symbols)
        
        # 识别终结符
        self._identify_terminals()
        
        # 初始化FIRST集
        self._init_first()
        
        # 初始化FOLLOW集
        self._init_follow()
    
    def set_feedback_grammar(self):
        """设置反馈格式文法 - 符合作业规范的 LL(1) 版本"""
        grammar_text = """
# 反馈格式文法（右递归版本，消除左递归）
Feedback -> FEEDBACK LBRACE FieldList RBRACE

# 字段列表（零个或多个字段）
FieldList -> Field FieldRest
FieldRest -> Field FieldRest | EPSILON

# 字段类型
Field -> ScoreField
Field -> LevelField
Field -> CommentField
Field -> ErrorsField

# 简单字段
ScoreField -> SCORE COLON NUMBER SEMICOLON
LevelField -> LEVEL COLON IDENT SEMICOLON

# 评论块
CommentField -> COMMENT LBRACE CommentContent RBRACE
CommentContent -> TextField SuggestionField
TextField -> TEXT COLON STRING SEMICOLON
SuggestionField -> SUGGESTION COLON STRING SEMICOLON

# 错误列表
ErrorsField -> ERRORS LBRACKET ErrorItems RBRACKET
ErrorItems -> ErrorItem ErrorItemsRest
ErrorItemsRest -> ErrorItem ErrorItemsRest | EPSILON

# 单个错误项
ErrorItem -> ERROR LPAREN ErrorParams RPAREN SEMICOLON

# 错误参数（用逗号分隔）- 右递归形式
ErrorParams -> Param ParamRest
ParamRest -> COMMA Param ParamRest | EPSILON

# 参数类型
Param -> LINE COLON NUMBER
Param -> TYPE COLON IDENT
Param -> MSG COLON STRING

# 终结符定义
LBRACE -> '{'
RBRACE -> '}'
LBRACKET -> '['
RBRACKET -> ']'
LPAREN -> '('
RPAREN -> ')'
COLON -> ':'
SEMICOLON -> ';'
COMMA -> ','
EPSILON -> ε
"""
        self.set_grammar(grammar_text, "Feedback")
    
    def set_expression_grammar(self):
        """设置算术表达式文法（经典LL(1)示例）"""
        grammar_text = """
E -> T E'
E' -> + T E' | - T E' | ε
T -> F T'
T' -> * F T' | / F T' | ε
F -> ( E ) | id | num
"""
        self.set_grammar(grammar_text, "E")
    
    def _identify_terminals(self):
        """识别终结符"""
        self.terminals.clear()
        
        # 收集所有出现的符号
        all_symbols = set()
        for left, right_list in self.productions.items():
            all_symbols.add(left)
            for right in right_list:
                for sym in right:
                    all_symbols.add(sym)
        
        # 非终结符已知，剩下的就是终结符
        for sym in all_symbols:
            if sym not in self.non_terminals and sym != 'ε':
                self.terminals.add(sym)
        
        # 添加结束符
        self.terminals.add('$')
    
    def _init_first(self):
        """初始化FIRST集"""
        # 初始化：终结符的FIRST集是自己
        for t in self.terminals:
            self.first[t] = {t}
        
        # 初始化非终结符的FIRST集为空
        for nt in self.non_terminals:
            self.first[nt] = set()
        
        # 迭代计算
        changed = True
        max_iterations = 100
        iteration = 0
        
        while changed and iteration < max_iterations:
            iteration += 1
            changed = False
            
            for nt in self.non_terminals:
                for production in self.productions.get(nt, []):
                    first_prod = self._compute_first_of_sequence(production)
                    
                    # 更新FIRST集
                    new_symbols = first_prod - self.first[nt]
                    if new_symbols:
                        self.first[nt].update(new_symbols)
                        changed = True
    
    def _compute_first_of_sequence(self, symbols: List[str]) -> Set[str]:
        """计算符号串的FIRST集"""
        result = set()
        all_have_epsilon = True
        
        for sym in symbols:
            if sym in self.non_terminals:
                result.update(self.first.get(sym, set()) - {'ε'})
                if 'ε' not in self.first.get(sym, set()):
                    all_have_epsilon = False
                    break
            elif sym in self.terminals:
                result.add(sym)
                all_have_epsilon = False
                break
            elif sym == 'ε':
                continue
            else:
                all_have_epsilon = False
                break
        
        if all_have_epsilon:
            result.add('ε')
        
        return result
    
    def _init_follow(self):
        """初始化FOLLOW集"""
        # 初始化所有非终结符的FOLLOW集为空
        for nt in self.non_terminals:
            self.follow[nt] = set()
        
        # 开始符号的FOLLOW集包含$
        self.follow[self.start_symbol].add('$')
        
        # 迭代计算
        changed = True
        max_iterations = 100
        iteration = 0
        
        while changed and iteration < max_iterations:
            iteration += 1
            changed = False
            
            for nt in self.non_terminals:
                for production in self.productions.get(nt, []):
                    # 遍历产生式右部的每个位置
                    for i, sym in enumerate(production):
                        if sym in self.non_terminals:
                            # 计算 β 的FIRST集
                            beta = production[i + 1:]
                            first_beta = self._compute_first_of_sequence(beta)
                            
                            # 添加FIRST(β) - {ε} 到 FOLLOW(sym)
                            to_add = first_beta - {'ε'}
                            if not to_add.issubset(self.follow[sym]):
                                self.follow[sym].update(to_add)
                                changed = True
                            
                            # 如果 ε ∈ FIRST(β)，则添加 FOLLOW(nt) 到 FOLLOW(sym)
                            if 'ε' in first_beta or not beta:
                                if not self.follow[nt].issubset(self.follow[sym]):
                                    self.follow[sym].update(self.follow[nt])
                                    changed = True
    
    def build_predict_table(self):
        """构造预测分析表"""
        self.predict_table.clear()
        
        for nt in self.non_terminals:
            for production in self.productions.get(nt, []):
                # 计算产生式的FIRST集
                first_prod = self._compute_first_of_sequence(production)
                
                # 对于每个终结符a ∈ FIRST(production)
                for a in first_prod:
                    if a != 'ε':
                        key = (nt, a)
                        if key in self.predict_table:
                            # 冲突检测
                            print(f"警告: 预测分析表冲突 M[{nt}, {a}]")
                        self.predict_table[key] = production
                
                # 如果 ε ∈ FIRST(production)
                if 'ε' in first_prod:
                    for b in self.follow.get(nt, set()):
                        key = (nt, b)
                        if key in self.predict_table:
                            # 冲突检测
                            print(f"警告: 预测分析表冲突 M[{nt}, {b}]")
                        self.predict_table[key] = []
    
    def check_ll1(self) -> Tuple[bool, List[str]]:
        """
        检查文法是否为LL(1)文法
        
        Returns:
            (是否为LL(1), 冲突列表)
        """
        conflicts = []
        
        for nt in self.non_terminals:
            productions = self.productions.get(nt, [])
            
            # 收集所有产生式的FIRST集
            first_sets = []
            epsilon_production = None
            
            for i, prod in enumerate(productions):
                first_prod = self._compute_first_of_sequence(prod)
                first_sets.append((i, first_prod))
                
                if 'ε' in first_prod:
                    epsilon_production = i
            
            # 检查FIRST集之间的冲突
            for i in range(len(first_sets)):
                for j in range(i + 1, len(first_sets)):
                    intersection = first_sets[i][1] & first_sets[j][1]
                    intersection.discard('ε')
                    if intersection:
                        conflicts.append(
                            f"非终结符 '{nt}' 的产生式 {i+1} 和 {j+1} 的FIRST集存在交集: {intersection}"
                        )
            
            # 检查ε产生式与FOLLOW集的冲突
            if epsilon_production is not None:
                for a in self.follow.get(nt, set()):
                    for i, (_, first_set) in enumerate(first_sets):
                        if i != epsilon_production and a in first_set:
                            conflicts.append(
                                f"非终结符 '{nt}' 的ε产生式与产生式 {i+1} 在终结符 '{a}' 上冲突"
                            )
        
        return len(conflicts) == 0, conflicts
    
    def analyze(self) -> LL1AnalysisResult:
        """执行完整的LL(1)分析"""
        # 计算FIRST和FOLLOW
        self._init_first()
        self._init_follow()
        
        # 构造预测分析表
        self.build_predict_table()
        
        # 检查LL(1)条件
        is_ll1, conflicts = self.check_ll1()
        
        # 生成文法信息
        grammar_info = self._generate_grammar_info()
        
        return LL1AnalysisResult(
            success=True,
            first_sets=self.first.copy(),
            follow_sets=self.follow.copy(),
            predict_table=self.predict_table.copy(),
            is_ll1=is_ll1,
            conflicts=conflicts,
            grammar_info=grammar_info
        )
    
    def _generate_grammar_info(self) -> str:
        """生成文法信息字符串"""
        info = []
        info.append("=" * 60)
        info.append("文法定义")
        info.append("=" * 60)
        
        for left, right_list in self.productions.items():
            for right in right_list:
                if right:
                    info.append(f"{left} → {' '.join(right)}")
                else:
                    info.append(f"{left} → ε")
        
        info.append("\n" + "=" * 60)
        info.append("非终结符")
        info.append("=" * 60)
        info.append(f"Vn = {{{', '.join(sorted(self.non_terminals))}}}")
        
        info.append("\n" + "=" * 60)
        info.append("终结符")
        info.append("=" * 60)
        info.append(f"Vt = {{{', '.join(sorted(self.terminals - {'$'}))}}}")
        
        info.append(f"\n开始符号: {self.start_symbol}")
        
        return "\n".join(info)
    
    def print_first_sets(self) -> str:
        """打印FIRST集"""
        output = []
        output.append("=" * 60)
        output.append("FIRST 集")
        output.append("=" * 60)
        
        for nt in sorted(self.non_terminals):
            first_set = self.first.get(nt, set())
            output.append(f"FIRST({nt}) = {{{', '.join(sorted(first_set))}}}")
        
        return "\n".join(output)
    
    def print_follow_sets(self) -> str:
        """打印FOLLOW集"""
        output = []
        output.append("=" * 60)
        output.append("FOLLOW 集")
        output.append("=" * 60)
        
        for nt in sorted(self.non_terminals):
            follow_set = self.follow.get(nt, set())
            output.append(f"FOLLOW({nt}) = {{{', '.join(sorted(follow_set))}}}")
        
        return "\n".join(output)
    
    def print_predict_table(self) -> str:
        """打印预测分析表"""
        output = []
        output.append("=" * 60)
        output.append("LL(1) 预测分析表")
        output.append("=" * 60)
        
        # 按非终结符分组
        for nt in sorted(self.non_terminals):
            output.append(f"\n{nt}:")
            for (n, t), prod in sorted(self.predict_table.items()):
                if n == nt:
                    if prod:
                        prod_str = ' '.join(prod) if prod else 'ε'
                    else:
                        prod_str = 'ε'
                    output.append(f"    M[{nt}, {t}] = {nt} → {prod_str}")
        
        return "\n".join(output)
    
    def print_full_analysis(self) -> str:
        """打印完整的LL(1)分析结果"""
        output = []
        
        output.append(self.print_first_sets())
        output.append("")
        output.append(self.print_follow_sets())
        output.append("")
        output.append(self.print_predict_table())
        output.append("")
        
        output.append("=" * 60)
        output.append("LL(1) 文法检测")
        output.append("=" * 60)
        
        is_ll1, conflicts = self.check_ll1()
        if is_ll1:
            output.append("✅ 该文法是 LL(1) 文法！")
        else:
            output.append("❌ 该文法不是 LL(1) 文法！")
            output.append("\n冲突信息:")
            for c in conflicts:
                output.append(f"  • {c}")
        
        return "\n".join(output)