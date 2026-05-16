"""教学型语法错误诊断 - 新增能力②"""
# llm/error_diagnosis.py
from typing import List, Dict, Set, Optional, Any, Tuple
from dataclasses import dataclass, field
from parser.error_recovery import ParseErrorInfo


@dataclass
class StructuredErrorInfo:
    """结构化的错误信息"""
    position: Tuple[int, int]  # (行, 列)
    error_type: str  # 错误类型: syntax, semantic, lexical
    expected: List[str]  # 期望的Token
    found: str  # 实际找到的内容
    context: str  # 上下文代码
    possible_causes: List[str] = field(default_factory=list)  # 可能原因
    fix_examples: List[str] = field(default_factory=list)  # 修正示例
    error_message: str = ""  # 面向初学者的错误消息


class ErrorDiagnosis:
    """
    教学型语法错误诊断器

    将结构化错误信息发送给LLM，生成面向初学者的自然语言讲解
    """

    def __init__(self, llm_client=None):
        self.llm_client = llm_client

    def diagnose(self, error_info: ParseErrorInfo, code_context: str = "") -> StructuredErrorInfo:
        """
        诊断错误并生成结构化信息

        Args:
            error_info: 解析器产生的错误信息
            code_context: 代码上下文

        Returns:
            结构化的错误信息
        """
        structured = StructuredErrorInfo(
            position=(error_info.line, error_info.column),
            error_type=self._classify_error(error_info),
            expected=list(error_info.expected),
            found=error_info.found,
            context=error_info.context if error_info.context else code_context,
            error_message=error_info.message
        )

        # 生成可能原因
        structured.possible_causes = self._generate_possible_causes(structured)

        # 生成修正示例
        structured.fix_examples = self._generate_fix_examples(structured)

        return structured

    def _classify_error(self, error_info: ParseErrorInfo) -> str:
        """分类错误类型"""
        msg = error_info.message.lower()

        if "syntax" in msg or "期望" in msg:
            return "syntax"
        elif "lexical" in msg or "非法字符" in msg:
            return "lexical"
        elif "semantic" in msg or "未声明" in msg or "重定义" in msg:
            return "semantic"
        else:
            return "syntax"

    def _generate_possible_causes(self, error: StructuredErrorInfo) -> List[str]:
        """生成可能的原因"""
        causes = []

        if error.error_type == "syntax":
            if ";" in error.expected:
                causes.append("缺少语句结束符（分号）")
            if ")" in error.expected:
                causes.append("括号不匹配或缺少右括号")
            if "}" in error.expected:
                causes.append("代码块未正确关闭，缺少右花括号")
            if "id" in error.expected or "num" in error.expected:
                causes.append("表达式结构不完整，缺少操作数")
            if "+" in error.expected or "-" in error.expected or "*" in error.expected or "/" in error.expected:
                causes.append("表达式结构不完整，缺少运算符")
            causes.append(f"在第 {error.position[0]} 行遇到了意外的 '{error.found}'")

        elif error.error_type == "lexical":
            causes.append(f"字符 '{error.found}' 不是有效的语法元素")
            causes.append("可能是拼写错误或使用了不支持的符号")

        elif error.error_type == "semantic":
            causes.append("变量或函数未在作用域内声明")
            causes.append("类型不匹配")

        if not causes:
            causes.append(f"在 '{error.found}' 处语法不符合预期")

        return causes

    def _generate_fix_examples(self, error: StructuredErrorInfo) -> List[str]:
        """生成修正示例"""
        examples = []

        if ";" in error.expected:
            examples.append(f"在第 {error.position[0]} 行末尾添加分号")
        if ")" in error.expected:
            examples.append("检查括号是否成对出现，添加缺失的右括号")
        if "}" in error.expected:
            examples.append("检查代码块边界，确保每个 { 都有对应的 }")
        if "id" in error.expected:
            examples.append("在运算符两侧添加变量名或数值")
        if "+" in error.expected or "-" in error.expected:
            examples.append("添加运算符连接两个表达式")

        if not examples:
            examples.append(f"检查第 {error.position[0]} 行的代码，确保语法正确")

        return examples

    def generate_llm_diagnostic_prompt(self, structured_error: StructuredErrorInfo) -> str:
        """
        生成发送给LLM的诊断提示

        用于生成面向初学者的自然语言讲解
        """
        prompt = f"""
请根据以下语法错误信息，生成一份面向编程初学者的友好错误解释和修正建议。

【错误信息】
- 错误位置: 第 {structured_error.position[0]} 行，第 {structured_error.position[1]} 列
- 错误类型: {structured_error.error_type}
- 错误描述: {structured_error.error_message}
- 实际内容: '{structured_error.found}'
- 期望内容: {', '.join(structured_error.expected)}

【可能原因】
{chr(10).join(f'- {c}' for c in structured_error.possible_causes)}

【代码上下文】
{structured_error.context if structured_error.context else '(未提供上下文)'}

请以自然语言回答，要求：
1. 用通俗易懂的语言解释错误含义
2. 说明为什么会出现这个错误
3. 给出具体的修正步骤和示例代码
4. 建议如何避免类似错误

请直接输出解释内容，不要添加额外格式。
"""
        return prompt

    def get_diagnostic_message(self, error_info: ParseErrorInfo) -> str:
        """
        获取教学型诊断信息（不依赖LLM的版本）
        """
        structured = self.diagnose(error_info)

        msg = f"""
╔═══════════════════════════════════════════════════════════════════════════════╗
║                          语法错误诊断报告                                      ║
╚═══════════════════════════════════════════════════════════════════════════════╝

📍 错误位置: 第 {structured.position[0]} 行，第 {structured.position[1]} 列

❌ 错误类型: {self._get_error_type_name(structured.error_type)}

📝 错误描述:
{structured.error_message}

🔍 实际内容: '{structured.found}'
💡 期望内容: {', '.join(structured.expected)}

{'─' * 70}

🔎 可能原因:
"""
        for cause in structured.possible_causes:
            msg += f"  • {cause}\n"

        msg += "\n🔧 修正建议:\n"
        for fix in structured.fix_examples:
            msg += f"  • {fix}\n"

        msg += """
{'─' * 70}

💡 学习提示:
1. 仔细检查括号、分号等符号是否完整
2. 确保表达式格式正确（操作数-运算符-操作数）
3. 遇到错误时，先从错误位置附近开始排查
"""
        return msg

    def _get_error_type_name(self, error_type: str) -> str:
        """获取错误类型的中文名称"""
        names = {
            "syntax": "语法错误",
            "lexical": "词法错误",
            "semantic": "语义错误"
        }
        return names.get(error_type, "未知错误")


__all__ = ['ErrorDiagnosis', 'StructuredErrorInfo']