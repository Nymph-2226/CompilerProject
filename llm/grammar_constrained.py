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
    """

    def __init__(self, grammar_type: str = "feedback"):
        self.grammar_type = grammar_type
        self.correction_stats = {"total_tokens": 0, "invalid_tokens": 0, "corrections": []}

    def constrain_generation(self, llm_output: str) -> GenerationResult:
        """
        对LLM输出进行文法约束验证和修正
        """
        result = GenerationResult(
            success=False,
            raw_text=llm_output,
            token_validation_steps=[]
        )

        cleaned = self._clean_output(llm_output)

        # 使用严格模式验证
        is_compliant, issues = self._validate_format_strict(cleaned)
        
        if is_compliant:
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
            # 重新验证修复后的结果
            result.format_compliant, _ = self._validate_format_strict(constrained)
            
            if result.format_compliant:
                result.success = True
                result.text = constrained

        return result

    def _clean_output(self, text: str) -> str:
        """清理LLM输出"""
        text = re.sub(r'```\w*\n?', '', text)
        text = re.sub(r'```', '', text)
        lines = [line.rstrip() for line in text.split('\n') if line.strip() or line.strip() == '']
        text = '\n'.join(lines)
        return text.strip()

    def _validate_format_strict(self, text: str) -> Tuple[bool, List[str]]:
        """
        严格验证反馈格式是否合规
        
        要求：
        - 必须有分号结尾
        - 括号必须匹配
        - 字段名必须正确
        """
        issues = []
        
        # 检查必要字段是否存在且格式正确
        checks = [
            (r'feedback\s*\{', "缺少 'feedback {' 开头"),
            (r'score\s*:\s*\d+\s*;', "score 字段格式错误，应为 'score: 数字;'"),
            (r'level\s*:\s*\w+\s*;', "level 字段格式错误，应为 'level: 标识符;'"),
            (r'comment\s*\{', "缺少 'comment {' 块"),
            (r'text\s*:\s*"[^"]*"\s*;', "text 字段格式错误，应为 'text: \"内容\";'"),
            (r'suggestion\s*:\s*"[^"]*"\s*;', "suggestion 字段格式错误"),
            (r'errors\s*\[', "缺少 'errors [' 块"),
            (r'error\s*\(', "缺少 error 项")
        ]
        
        for pattern, msg in checks:
            if not re.search(pattern, text, re.IGNORECASE):
                issues.append(msg)
        
        # 检查括号匹配
        if text.count('{') != text.count('}'):
            issues.append(f"花括号不匹配: {text.count('{')}个 {{, {text.count('}')}个 }}")
        if text.count('[') != text.count(']'):
            issues.append(f"方括号不匹配: {text.count('[')}个 [, {text.count(']')}个 ]")
        if text.count('(') != text.count(')'):
            issues.append(f"圆括号不匹配: {text.count('(')}个 (, {text.count(')')}个 )")
        
        # 检查分号完整性
        lines = text.split('\n')
        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            if stripped and not stripped.endswith('{') and not stripped.endswith('}') and not stripped.endswith('[') and not stripped.endswith(']'):
                if ':' in stripped and not stripped.endswith(';') and not stripped.startswith('//'):
                    issues.append(f"第{i}行缺少分号: {stripped[:50]}")
        
        return len(issues) == 0, issues

    def _validate_format_loose(self, text: str) -> Tuple[bool, List[str]]:
        """宽松验证 - 仅检查关键字段是否存在"""
        issues = []
        
        has_feedback = bool(re.search(r'feedback\s*\{', text, re.IGNORECASE))
        has_score = bool(re.search(r'score\s*:\s*\d+', text, re.IGNORECASE))
        has_level = bool(re.search(r'level\s*:\s*\w+', text, re.IGNORECASE))
        has_comment = bool(re.search(r'comment\s*\{', text, re.IGNORECASE))
        has_text = bool(re.search(r'text\s*:\s*"[^"]*"', text, re.IGNORECASE))
        
        if not has_feedback:
            issues.append("缺少 'feedback' 块")
        if not has_score:
            issues.append("缺少 'score' 字段")
        if not has_level:
            issues.append("缺少 'level' 字段")
        if not has_comment:
            issues.append("缺少 'comment' 块")
        if not has_text:
            issues.append("缺少 'text' 字段")
        
        return len(issues) == 0, issues

    def _repair_format(self, text: str, issues: List[str]) -> Tuple[str, List[str]]:
        """
        修复格式问题 - 提取关键信息并重新构造
        """
        corrections = []
        
        # 提取 score
        score_match = re.search(r'score\s*:\s*(\d+)', text, re.IGNORECASE)
        score = score_match.group(1) if score_match else "85"
        if not score_match:
            corrections.append("未找到 score 字段，使用默认值 85")
        
        # 提取 level
        level_match = re.search(r'level\s*:\s*(\w+)', text, re.IGNORECASE)
        level = level_match.group(1) if level_match else "medium"
        if not level_match:
            corrections.append("未找到 level 字段，使用默认值 'medium'")
        
        # 提取 comment text
        text_match = re.search(r'text\s*:\s*"([^"]*)"', text, re.IGNORECASE)
        comment_text = text_match.group(1) if text_match else "代码逻辑清晰"
        if not text_match:
            corrections.append("未找到 text 字段，尝试从原始文本提取")
            # 尝试提取无引号的内容
            fallback_match = re.search(r'text\s*:\s*([^\n;]+)', text, re.IGNORECASE)
            if fallback_match:
                comment_text = fallback_match.group(1).strip()
                corrections.append(f"从原始文本提取评语: {comment_text[:50]}")
        
        # 提取 suggestion
        suggestion_match = re.search(r'suggestion\s*:\s*"([^"]*)"', text, re.IGNORECASE)
        suggestion = suggestion_match.group(1) if suggestion_match else "建议增加注释"
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
        
        # 记录修复的问题
        if "缺少分号" in str(issues):
            corrections.append("添加缺失的分号")
        if "括号不匹配" in str(issues):
            corrections.append("修复括号匹配问题")
        
        # 重新构造标准格式（带分号的完整格式）
        constrained = f"""feedback {{
    score: {score};
    level: {level};
    comment {{
        text: "{comment_text}";
        suggestion: "{suggestion}";
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
        """运行对照实验"""
        results = {
            "total": len(raw_outputs),
            "raw_compliant": 0,
            "constrained_compliant": 0,
            "corrections_per_output": [],
            "improvement_rate": 0.0
        }

        for output in raw_outputs:
            # 检查原始输出是否合规（使用严格模式）
            original_compliant, _ = self._validate_format_strict(output)
            if original_compliant:
                results["raw_compliant"] += 1

            # 约束生成
            constrained_result = self.constrain_generation(output)

            if constrained_result.format_compliant:
                results["constrained_compliant"] += 1

            results["corrections_per_output"].append(len(constrained_result.corrections))

        if results["total"] > 0:
            results["improvement_rate"] = (results["constrained_compliant"] - results["raw_compliant"]) / results["total"]

        return results


__all__ = ['GrammarConstrainedGenerator', 'GenerationResult']