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

    核心思想：不强制修改LLM输出，而是验证格式并给出修正建议
    """

    def __init__(self, grammar_type: str = "feedback"):
        self.grammar_type = grammar_type
        self.correction_stats = {"total_tokens": 0, "invalid_tokens": 0, "corrections": []}

    def constrain_generation(self, llm_output: str) -> GenerationResult:
        """
        对LLM输出进行文法约束验证和修正

        策略：
        1. 先验证格式是否合规
        2. 如果不合规，提取关键信息并重新构造标准格式
        3. 保留原始值，只修正结构问题
        """
        result = GenerationResult(
            success=False,
            raw_text=llm_output,
            token_validation_steps=[]
        )

        # 清理输出
        cleaned = self._clean_output(llm_output)

        # 验证格式合规性
        is_compliant, issues = self._validate_format(cleaned)
        
        if is_compliant:
            # 格式已经合规，直接返回
            result.constrained_text = cleaned
            result.format_compliant = True
            result.success = True
            result.text = cleaned
            result.corrections = []
        else:
            # 格式不合规，尝试修复
            constrained, corrections = self._repair_format(cleaned, issues)
            result.constrained_text = constrained
            result.corrections = corrections
            result.format_compliant = self._validate_format(constrained)[0]
            
            if result.format_compliant:
                result.success = True
                result.text = constrained

        return result

    def _clean_output(self, text: str) -> str:
        """清理LLM输出"""
        # 移除Markdown代码块标记
        text = re.sub(r'```\w*\n?', '', text)
        text = re.sub(r'```', '', text)
        
        # 保留换行但移除多余空行
        lines = [line.rstrip() for line in text.split('\n') if line.strip() or line.strip() == '']
        text = '\n'.join(lines)
        
        return text.strip()

    def _validate_format(self, text: str) -> Tuple[bool, List[str]]:
        """
        验证反馈格式是否合规
        
        Returns:
            (是否合规, 问题列表)
        """
        issues = []
        
        # 必需的组件及其正则表达式
        required_patterns = [
            (r'feedback\s*\{', "缺少 'feedback {' 开头"),
            (r'score\s*:\s*\d+\s*;?', "缺少或格式错误的 score 字段 (应为 'score: 数字;')"),
            (r'level\s*:\s*\w+\s*;?', "缺少或格式错误的 level 字段 (应为 'level: 标识符;')"),
            (r'comment\s*\{', "缺少 'comment {' 块"),
            (r'text\s*:\s*"[^"]*"\s*;?', "缺少或格式错误的 text 字段 (应为 'text: \"内容\";')"),
            (r'suggestion\s*:\s*"[^"]*"\s*;?', "缺少或格式错误的 suggestion 字段 (应为 'suggestion: \"内容\";')"),
            (r'\}\s*\]?\s*\}?', "缺少结尾的 '}' (可能多个)"),
            (r'errors\s*\[', "缺少或格式错误的 errors 块 (应为 'errors [')"),
            (r'error\s*\(', "缺少 error 项 (应为 'error(')"),
            (r'line\s*:\s*\d+', "缺少 line 参数 (应为 'line: 数字')"),
            (r'type\s*:\s*\w+', "缺少 type 参数 (应为 'type: 标识符')"),
            (r'msg\s*:\s*"[^"]*"', "缺少 msg 参数 (应为 'msg: \"内容\"')"),
        ]
        
        for pattern, message in required_patterns:
            if not re.search(pattern, text, re.IGNORECASE):
                issues.append(message)
        
        # 检查括号匹配
        brace_count = text.count('{') - text.count('}')
        bracket_count = text.count('[') - text.count(']')
        paren_count = text.count('(') - text.count(')')
        
        if brace_count > 0:
            issues.append(f"缺少 {brace_count} 个右花括号 '}}'")
        if brace_count < 0:
            issues.append(f"多余的右花括号")
        if bracket_count > 0:
            issues.append(f"缺少 {bracket_count} 个右方括号 ']'")
        if bracket_count < 0:
            issues.append(f"多余的右方括号")
        if paren_count > 0:
            issues.append(f"缺少 {paren_count} 个右括号 ')'")
        if paren_count < 0:
            issues.append(f"多余的右括号")
        
        return len(issues) == 0, issues

    def _repair_format(self, text: str, issues: List[str]) -> Tuple[str, List[str]]:
        """
        修复格式问题
        
        策略：提取关键信息，重新构造标准格式
        """
        corrections = []
        
        # 提取 score
        score_match = re.search(r'score\s*:\s*(\d+)', text, re.IGNORECASE)
        score = score_match.group(1) if score_match else "0"
        if not score_match:
            corrections.append("未找到 score 字段，使用默认值 0")
        
        # 提取 level
        level_match = re.search(r'level\s*:\s*(\w+)', text, re.IGNORECASE)
        level = level_match.group(1) if level_match else "medium"
        if not level_match:
            corrections.append("未找到 level 字段，使用默认值 'medium'")
        
        # 提取 comment text
        text_match = re.search(r'text\s*:\s*"([^"]*)"', text, re.IGNORECASE)
        comment_text = text_match.group(1) if text_match else "评语"
        if not text_match:
            corrections.append("未找到 text 字段，使用默认评语")
        
        # 提取 suggestion
        suggestion_match = re.search(r'suggestion\s*:\s*"([^"]*)"', text, re.IGNORECASE)
        suggestion = suggestion_match.group(1) if suggestion_match else "建议"
        if not suggestion_match:
            corrections.append("未找到 suggestion 字段，使用默认建议")
        
        # 提取 errors
        errors = []
        error_pattern = r'error\s*\(\s*line\s*:\s*(\d+)\s*,\s*type\s*:\s*(\w+)\s*,\s*msg\s*:\s*"([^"]*)"\s*\)'
        error_matches = re.findall(error_pattern, text, re.IGNORECASE)
        
        for line_num, error_type, msg in error_matches:
            errors.append(f"    error(line: {line_num}, type: {error_type}, msg: \"{msg}\")")
        
        if not errors:
            corrections.append("未找到 errors 列表，使用空列表")
        
        # 重新构造标准格式
        constrained = f"""feedback {{
    score: {score}
    level: {level}
    comment {{
        text: "{comment_text}"
        suggestion: "{suggestion}"
    }}
    errors [
{chr(10).join(errors) if errors else "        // 无错误"
    }
    ]
}}"""
        
        return constrained, corrections

    def get_statistics(self) -> Dict:
        """获取统计信息"""
        return {
            "total_tokens": self.correction_stats["total_tokens"],
            "invalid_tokens": self.correction_stats["invalid_tokens"],
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
            "raw_compliant": 0,
            "constrained_compliant": 0,
            "corrections_per_output": [],
            "improvement_rate": 0.0
        }

        for output in raw_outputs:
            # 检查原始输出是否合规
            original_compliant, _ = self._validate_format(output)
            if original_compliant:
                results["raw_compliant"] += 1

            # 约束生成
            constrained_result = self.constrain_generation(output)

            if constrained_result.format_compliant:
                results["constrained_compliant"] += 1

            results["corrections_per_output"].append(len(constrained_result.corrections))

        # 计算改善率
        if results["total"] > 0:
            results["improvement_rate"] = (results["constrained_compliant"] - results["raw_compliant"]) / results["total"]

        return results


__all__ = ['GrammarConstrainedGenerator', 'GenerationResult']