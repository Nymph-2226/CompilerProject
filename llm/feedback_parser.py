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
    反馈格式解析器（大小写不敏感）
    """

    def __init__(self):
        # (?i) 表示不区分大小写
        self.patterns = {
            'score': r'(?i)score\s*:\s*(\d+)\s*;',
            'level': r'(?i)level\s*:\s*(\w+)\s*;',
            'text': r'(?i)text\s*:\s*"([^"]*)"\s*;',
            'suggestion': r'(?i)suggestion\s*:\s*"([^"]*)"\s*;',
            'error': r'(?i)error\s*\(\s*line\s*:\s*(\d+)\s*,\s*type\s*:\s*(\w+)\s*,\s*msg\s*:\s*"([^"]*)"\s*\)',
        }

    def parse(self, text: str) -> ParsedFeedback:
        """
        解析反馈文本
        """
        result = ParsedFeedback(success=False, raw_text=text)

        try:
            # 方法1：尝试使用正则直接提取所有字段（更简单可靠）
            
            # 提取 score
            score_match = re.search(r'(?i)score\s*:\s*(\d+)\s*;', text)
            if score_match:
                result.score = int(score_match.group(1))
            
            # 提取 level
            level_match = re.search(r'(?i)level\s*:\s*(\w+)\s*;', text)
            if level_match:
                result.level = level_match.group(1)
            
            # 提取 comment 中的 text
            text_match = re.search(r'(?i)text\s*:\s*"([^"]*)"\s*;', text)
            if text_match:
                result.comment = text_match.group(1)
            
            # 提取 comment 中的 suggestion
            suggestion_match = re.search(r'(?i)suggestion\s*:\s*"([^"]*)"\s*;', text)
            if suggestion_match:
                result.suggestion = suggestion_match.group(1)
            
            # 提取所有 errors
            error_matches = re.findall(self.patterns['error'], text, re.IGNORECASE)
            for match in error_matches:
                result.errors.append({
                    'line': int(match[0]),
                    'type': match[1],
                    'msg': match[2]
                })
            
            # 检查是否至少提取到了必要字段
            if result.score is not None or result.level is not None or result.errors:
                result.success = True
            else:
                # 如果直接提取失败，尝试提取 feedback 块后再提取
                feedback_match = re.search(r'feedback\s*\{', text, re.DOTALL | re.IGNORECASE)
                if feedback_match:
                    start = feedback_match.end()
                    brace_count = 1
                    end = start
                    for i, ch in enumerate(text[start:], start):
                        if ch == '{':
                            brace_count += 1
                        elif ch == '}':
                            brace_count -= 1
                            if brace_count == 0:
                                end = i
                                break
                    
                    feedback_content = text[start:end]
                    
                    # 在 feedback_content 中重新提取
                    score_match = re.search(self.patterns['score'], feedback_content, re.IGNORECASE)
                    if score_match:
                        result.score = int(score_match.group(1))
                    
                    level_match = re.search(self.patterns['level'], feedback_content, re.IGNORECASE)
                    if level_match:
                        result.level = level_match.group(1)
                    
                    text_match = re.search(self.patterns['text'], feedback_content, re.IGNORECASE)
                    if text_match:
                        result.comment = text_match.group(1)
                    
                    suggestion_match = re.search(self.patterns['suggestion'], feedback_content, re.IGNORECASE)
                    if suggestion_match:
                        result.suggestion = suggestion_match.group(1)
                    
                    error_matches = re.findall(self.patterns['error'], feedback_content, re.IGNORECASE)
                    for match in error_matches:
                        result.errors.append({
                            'line': int(match[0]),
                            'type': match[1],
                            'msg': match[2]
                        })
                    
                    if result.score is not None or result.level is not None or result.errors:
                        result.success = True
                    else:
                        result.error_message = "未能提取到有效的反馈数据"
                else:
                    result.error_message = "未找到 feedback 块"

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