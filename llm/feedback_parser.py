"""反馈格式解析器"""
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
import re


@dataclass
class ParsedFeedback:
    """解析后的反馈数据"""
    success: bool
    score: Optional[int] = None
    level: Optional[str] = None
    comment: Optional[str] = None
    suggestion: Optional[str] = None
    errors: List[Dict] = field(default_factory=list)
    raw_text: str = ""
    error_message: str = ""


class FeedbackParser:
    """
    反馈格式解析器

    解析格式：
    feedback {
        score: 85;
        level: medium;
        comment {
            text: "评语内容";
            suggestion: "建议内容";
        }
        errors [
            error(line: 12, type: runtime, msg: "错误信息");
        ]
    }
    """

    def __init__(self):
        self.patterns = {
            'score': r'score\s*:\s*(\d+)\s*;',
            'level': r'level\s*:\s*(\w+)\s*;',
            'text': r'text\s*:\s*"([^"]*)"\s*;',
            'suggestion': r'suggestion\s*:\s*"([^"]*)"\s*;',
            'error': r'error\s*\(\s*line\s*:\s*(\d+)\s*,\s*type\s*:\s*(\w+)\s*,\s*msg\s*:\s*"([^"]*)"\s*\)',
        }

    def parse(self, text: str) -> ParsedFeedback:
        """
        解析反馈文本

        Args:
            text: LLM输出的反馈文本

        Returns:
            解析后的反馈数据
        """
        result = ParsedFeedback(success=False, raw_text=text)

        try:
            # 提取feedback块
            feedback_match = re.search(r'feedback\s*\{([^}]*)\}', text, re.DOTALL)
            if not feedback_match:
                result.error_message = "未找到 feedback 块"
                return result

            feedback_content = feedback_match.group(1)

            # 解析各个字段
            score_match = re.search(self.patterns['score'], feedback_content)
            if score_match:
                result.score = int(score_match.group(1))

            level_match = re.search(self.patterns['level'], feedback_content)
            if level_match:
                result.level = level_match.group(1)

            # 解析comment块
            comment_match = re.search(r'comment\s*\{([^}]*)\}', feedback_content, re.DOTALL)
            if comment_match:
                comment_content = comment_match.group(1)
                text_match = re.search(self.patterns['text'], comment_content)
                if text_match:
                    result.comment = text_match.group(1)
                suggestion_match = re.search(self.patterns['suggestion'], comment_content)
                if suggestion_match:
                    result.suggestion = suggestion_match.group(1)

            # 解析errors数组
            errors_match = re.search(r'errors\s*\[\s*([^\]]*)\s*\]', feedback_content, re.DOTALL)
            if errors_match:
                errors_content = errors_match.group(1)
                error_matches = re.findall(self.patterns['error'], errors_content)
                for match in error_matches:
                    result.errors.append({
                        'line': int(match[0]),
                        'type': match[1],
                        'msg': match[2]
                    })

            result.success = True

        except Exception as e:
            result.error_message = str(e)

        return result

    def to_json(self, parsed: ParsedFeedback) -> Dict:
        """转换为JSON格式"""
        return {
            "score": parsed.score,
            "level": parsed.level,
            "comment": parsed.comment,
            "suggestion": parsed.suggestion,
            "errors": parsed.errors
        }


__all__ = ['FeedbackParser', 'ParsedFeedback']