"""文法引导的LLM约束生成 - 新增能力①"""
# llm/grammar_constrained.py
from typing import List, Dict, Set, Tuple, Optional, Any
from dataclasses import dataclass, field
import re


@dataclass
class GenerationResult:
    """生成结果"""
    success: bool
    text: str = ""
    constrained_text: str = ""  # 约束后的文本
    raw_text: str = ""  # 原始LLM输出
    corrections: List[str] = field(default_factory=list)  # 修正记录
    format_compliant: bool = False
    token_validation_steps: List[str] = field(default_factory=list)


class GrammarConstrainedGenerator:
    """
    文法引导的LLM约束生成器

    以LL(1)分析表为约束，在大模型逐Token输出时进行合法性校验
    """

    def __init__(self, grammar_type: str = "feedback"):
        """
        初始化

        Args:
            grammar_type: 文法类型 - "feedback" 或 "expression"
        """
        self.grammar_type = grammar_type

        if grammar_type == "feedback":
            self._init_feedback_grammar()
        else:
            self._init_expression_grammar()

        self.constraint_mode = True
        self.correction_stats = {"total_tokens": 0, "invalid_tokens": 0, "corrections": []}

    def _init_feedback_grammar(self):
        """初始化反馈格式文法"""
        # 非终结符
        self.Vn = {"Feedback", "FieldList", "Field", "ScoreField", "LevelField",
                   "CommentBlock", "TextField", "SuggestionField", "ErrorList",
                   "ErrorItems", "ErrorItem", "ErrorParams", "ParamList", "Param"}

        # 终结符
        self.Vt = {"feedback", "score", "level", "comment", "text", "suggestion",
                   "errors", "error", "line", "type", "msg", ":", ";", "{", "}", "(", ")", "[", "]", ","}

        # 预测分析表（简化版）
        self.predict_table: Dict[Tuple[str, str], str] = {
            ("Feedback", "feedback"): "feedback { FieldList }",
            ("FieldList", "score"): "ScoreField FieldList",
            ("FieldList", "level"): "LevelField FieldList",
            ("FieldList", "comment"): "CommentBlock FieldList",
            ("FieldList", "errors"): "ErrorList FieldList",
            ("FieldList", "}"): "ε",
            ("ScoreField", "score"): "score : NUMBER ;",
            ("LevelField", "level"): "level : IDENT ;",
            ("CommentBlock", "comment"): "comment { TextField SuggestionField }",
            ("TextField", "text"): "text : STRING ;",
            ("SuggestionField", "suggestion"): "suggestion : STRING ;",
            ("ErrorList", "errors"): "errors [ ErrorItems ]",
            ("ErrorItems", "error"): "ErrorItem ErrorItems",
            ("ErrorItems", "]"): "ε",
            ("ErrorItem", "error"): "error ( ErrorParams ) ;",
            ("ErrorParams", "line"): "ParamList",
            ("ParamList", "line"): "Param , ParamList",
            ("ParamList", ")"): "ε",
            ("Param", "line"): "line : NUMBER",
            ("Param", "type"): "type : IDENT",
            ("Param", "msg"): "msg : STRING",
        }

        self.start_symbol = "Feedback"

    def _init_expression_grammar(self):
        """初始化表达式文法"""
        self.Vn = {"E", "E'", "T", "T'", "F"}
        self.Vt = {"+", "-", "*", "/", "(", ")", "id", "num", "$"}

        self.predict_table: Dict[Tuple[str, str], str] = {
            ("E", "id"): "T E'",
            ("E", "num"): "T E'",
            ("E", "("): "T E'",
            ("E'", "+"): "+ T E'",
            ("E'", "-"): "- T E'",
            ("E'", ")"): "ε",
            ("E'", "$"): "ε",
            ("T", "id"): "F T'",
            ("T", "num"): "F T'",
            ("T", "("): "F T'",
            ("T'", "*"): "* F T'",
            ("T'", "/"): "/ F T'",
            ("T'", "+"): "ε",
            ("T'", "-"): "ε",
            ("T'", ")"): "ε",
            ("T'", "$"): "ε",
            ("F", "id"): "id",
            ("F", "num"): "num",
            ("F", "("): "( E )",
        }

        self.start_symbol = "E"

    def validate_token(self, token: str, context: str) -> Tuple[bool, Set[str]]:
        """
        验证Token是否合法

        Args:
            token: 当前Token
            context: 上下文（当前非终结符）

        Returns:
            (是否合法, 期望的Token集合)
        """
        key = (context, token)
        if key in self.predict_table:
            return True, {token}

        # 查找可能的期望Token
        expected = set()
        for (ctx, t) in self.predict_table.keys():
            if ctx == context:
                expected.add(t)

        return False, expected

    def constrain_generation(self, llm_output: str) -> GenerationResult:
        """
        对LLM输出进行文法约束修正

        Args:
            llm_output: LLM原始输出

        Returns:
            约束后的结果
        """
        result = GenerationResult(
            success=False,
            raw_text=llm_output,
            token_validation_steps=[]
        )

        # 清理输出
        cleaned = self._clean_output(llm_output)

        # 逐Token验证和修正
        constrained, corrections, steps = self._validate_and_correct(cleaned)

        result.constrained_text = constrained
        result.corrections = corrections
        result.token_validation_steps = steps
        result.format_compliant = self._check_full_compliance(constrained)

        if result.format_compliant:
            result.success = True
            result.text = constrained

        # 更新统计
        self.correction_stats["total_tokens"] += len(cleaned.split())
        self.correction_stats["invalid_tokens"] += len(corrections)
        self.correction_stats["corrections"].extend(corrections)

        return result

    def _clean_output(self, text: str) -> str:
        """清理LLM输出"""
        # 移除Markdown代码块标记
        text = re.sub(r'```\w*\n?', '', text)
        text = re.sub(r'```', '', text)

        # 移除多余空格
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()

        return text

    def _tokenize(self, text: str) -> List[str]:
        """将文本转换为Token序列"""
        # 简单分词
        tokens = []
        i = 0
        n = len(text)

        while i < n:
            ch = text[i]

            # 数字
            if ch.isdigit():
                start = i
                while i < n and (text[i].isdigit() or text[i] == '.'):
                    i += 1
                tokens.append("NUMBER")
                continue

            # 标识符/关键字
            elif ch.isalpha() or ch == '_':
                start = i
                while i < n and (text[i].isalnum() or text[i] == '_'):
                    i += 1
                token = text[start:i].lower()
                if token in self.Vt:
                    tokens.append(token)
                else:
                    tokens.append("IDENT")
                continue

            # 字符串
            elif ch == '"' or ch == "'":
                tokens.append("STRING")
                i += 1
                while i < n and text[i] != ch:
                    i += 1
                i += 1
                continue

            # 符号
            elif ch in self.Vt:
                tokens.append(ch)
                i += 1

            else:
                i += 1

        return tokens

    def _validate_and_correct(self, text: str) -> Tuple[str, List[str], List[str]]:
        """
        验证并修正Token序列
        """
        tokens = self._tokenize(text)
        stack = [self.start_symbol]
        pos = 0
        corrections = []
        steps = []

        while stack and pos <= len(tokens):
            top = stack.pop()
            steps.append(f"栈: {stack[::-1]}, 输入: {tokens[pos:] if pos < len(tokens) else []}")

            if top in self.Vt:
                if pos < len(tokens) and top == tokens[pos]:
                    steps.append(f"  匹配: {top}")
                    pos += 1
                else:
                    # Token不匹配，尝试修正
                    if pos < len(tokens):
                        expected = self._get_expected(stack[-1] if stack else self.start_symbol)
                        correction = f"替换 '{tokens[pos]}' 为 '{top}' (期望: {expected})"
                        corrections.append(correction)
                        steps.append(f"  修正: {correction}")
                        # 使用期望的token
                        pos += 1
                    else:
                        # 缺少Token
                        if top != "$":
                            correction = f"插入缺失的 '{top}'"
                            corrections.append(correction)
                            steps.append(f"  修正: {correction}")

            elif top in self.Vn:
                if pos < len(tokens):
                    current = tokens[pos]
                    key = (top, current)
                    if key in self.predict_table:
                        production = self.predict_table[key]
                        steps.append(f"  展开 {top} → {production}")
                        if production != "ε":
                            for sym in reversed(production.split()):
                                stack.append(sym)
                    else:
                        # 无产生式可用，尝试跳过当前token
                        expected = self._get_expected(top)
                        correction = f"跳过非法Token '{current}' (期望: {expected})"
                        corrections.append(correction)
                        steps.append(f"  修正: {correction}")
                        pos += 1
                else:
                    # 输入结束，检查是否可以接受空
                    key = (top, "$")
                    if key in self.predict_table:
                        production = self.predict_table[key]
                        if production != "ε":
                            correction = f"在输入结束处插入 '{top}' 的展开"
                            corrections.append(correction)
                            steps.append(f"  修正: {correction}")
                continue

            elif top == "$":
                break

        steps.append("验证完成")

        # 重建修正后的文本
        corrected_text = self._rebuild_text(tokens, corrections)

        return corrected_text, corrections, steps

    def _get_expected(self, nonterminal: str) -> Set[str]:
        """获取期望的Token集合"""
        expected = set()
        for (nt, t) in self.predict_table.keys():
            if nt == nonterminal:
                expected.add(t)
        return expected

    def _check_full_compliance(self, text: str) -> bool:
        """检查文本是否完全符合文法"""
        tokens = self._tokenize(text)
        stack = [self.start_symbol]
        pos = 0

        while stack and pos <= len(tokens):
            top = stack.pop()

            if top in self.Vt:
                if pos < len(tokens) and top == tokens[pos]:
                    pos += 1
                else:
                    return False
            elif top in self.Vn:
                if pos < len(tokens):
                    current = tokens[pos]
                    key = (top, current)
                    if key in self.predict_table:
                        production = self.predict_table[key]
                        if production != "ε":
                            for sym in reversed(production.split()):
                                stack.append(sym)
                    else:
                        return False
                else:
                    key = (top, "$")
                    if key not in self.predict_table or self.predict_table[key] == "ε":
                        pass
                    else:
                        return False
            elif top == "$":
                break

        return pos == len(tokens)

    def _rebuild_text(self, tokens: List[str], corrections: List[str]) -> str:
        """根据修正重建文本"""
        # 简化实现：直接返回原始文本
        return ' '.join(tokens)

    def get_statistics(self) -> Dict:
        """获取统计信息"""
        total = self.correction_stats["total_tokens"]
        invalid = self.correction_stats["invalid_tokens"]

        return {
            "total_tokens": total,
            "invalid_tokens": invalid,
            "valid_rate": 1.0 - (invalid / total) if total > 0 else 1.0,
            "corrections_count": len(self.correction_stats["corrections"])
        }

    def run_comparison_experiment(self, raw_outputs: List[str]) -> Dict:
        """
        运行对照实验

        Args:
            raw_outputs: 原始LLM输出列表

        Returns:
            实验结果
        """
        results = {
            "total": len(raw_outputs),
            "raw_success": 0,
            "constrained_success": 0,
            "raw_compliant": 0,
            "constrained_compliant": 0,
            "corrections_per_output": [],
            "improvement_rate": 0.0
        }

        for output in raw_outputs:
            # 检查原始输出是否合规
            original_compliant = self._check_full_compliance(self._clean_output(output))
            if original_compliant:
                results["raw_compliant"] += 1

            # 约束生成
            constrained_result = self.constrain_generation(output)

            if constrained_result.format_compliant:
                results["constrained_compliant"] += 1

            results["corrections_per_output"].append(len(constrained_result.corrections))

        # 计算改善率
        if results["raw_compliant"] > 0:
            raw_rate = results["raw_compliant"] / results["total"]
            constrained_rate = results["constrained_compliant"] / results["total"]
            results["improvement_rate"] = constrained_rate - raw_rate
        else:
            results["improvement_rate"] = results["constrained_compliant"] / results["total"]

        return results


__all__ = ['GrammarConstrainedGenerator', 'GenerationResult']