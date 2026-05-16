"""句柄分析器"""
from typing import List, Tuple, Dict, Optional


class HandleAnalyzer:
    """句柄分析器"""

    def __init__(self):
        self.productions = [
            (["(", "E", ")"], "F"),
            (["T", "*", "F"], "T"),
            (["T", "/", "F"], "T"),
            (["E", "+", "T"], "E"),
            (["E", "-", "T"], "E"),
            (["id"], "F"),
            (["num"], "F"),
            (["F"], "T"),
            (["T"], "E"),
        ]

        self.Vn = {"E", "T", "F"}
        self.Vt = {"+", "-", "*", "/", "(", ")", "id", "num"}

    def _tokenize(self, symbol_string: str) -> List[str]:
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
                tokens.append(symbol_string[i])
                i += 1
            elif symbol_string[i].isdigit():
                tokens.append("num")
                i += 1
            else:
                i += 1
        return tokens

    def _tokens_to_string(self, tokens: List[str]) -> str:
        return ' '.join(tokens)

    def _find_match(self, tokens: List[str]) -> Tuple[Optional[int], Optional[int], Optional[List[str]], Optional[str]]:
        n = len(tokens)

        for pattern, result in self.productions:
            lp = len(pattern)
            for i in range(n - lp + 1):
                if tokens[i:i + lp] == pattern:
                    return i, i + lp, pattern, result
        return None, None, None, None

    def find_handle(self, sentential_form: str) -> Dict:
        """查找句型中的句柄"""
        result = {
            "success": False,
            "sentential_form": sentential_form,
            "handle": None,
            "handle_text": "",
            "handle_type": "",
            "message": "",
            "analysis_steps": []
        }

        try:
            tokens = self._tokenize(sentential_form)

            if not tokens:
                result["message"] = "句型为空"
                return result

            result["analysis_steps"].append(f"句型: {sentential_form}")
            result["analysis_steps"].append(f"Token序列: {' '.join(tokens)}")
            result["analysis_steps"].append("")

            start, end, pattern, reduced_symbol = self._find_match(tokens)

            if start is not None and end is not None:
                handle_text = self._tokens_to_string(tokens[start:end])
                result["handle"] = (start, end)
                result["handle_text"] = handle_text
                result["handle_type"] = reduced_symbol
                result["success"] = True
                result["message"] = "✓ 成功找到句柄"

                result["analysis_steps"].append(f"句柄（最左直接短语）:")
                result["analysis_steps"].append(f"  • 位置: [{start}:{end}]")
                result["analysis_steps"].append(f"  • 内容: '{handle_text}'")
                result["analysis_steps"].append(f"  • 匹配模式: {pattern} → {reduced_symbol}")
                result["analysis_steps"].append("")
                result["analysis_steps"].append("句柄标注:")
                annotated = self._annotate_handle(tokens, start, end)
                result["analysis_steps"].append(f"  {annotated}")
            else:
                if len(tokens) == 1 and tokens[0] == "E":
                    result["success"] = True
                    result["message"] = "✓ 已归约到开始符号 E"
                    result["analysis_steps"].append("归约完成！已到达开始符号 E")
                else:
                    result["message"] = "未找到句柄，可能不是有效的句型"

        except Exception as e:
            result["message"] = f"分析错误: {str(e)}"

        return result

    def _annotate_handle(self, tokens: List[str], start: int, end: int) -> str:
        annotated_tokens = []
        for i, token in enumerate(tokens):
            if start <= i < end:
                annotated_tokens.append(f"[{token}]")
            else:
                annotated_tokens.append(token)
        return " ".join(annotated_tokens)

    def reduce_by_handle(self, sentence: str) -> Dict:
        """基于句柄的最左归约步骤可视化"""
        result = {
            "success": False,
            "original_sentence": sentence,
            "reduce_steps": [],
            "message": ""
        }

        try:
            tokens = self._tokenize(sentence)

            for token in tokens:
                if token not in self.Vt and token not in ["id", "num"]:
                    result["message"] = f"句子包含非法符号: {token}"
                    return result

            current = tokens.copy()
            step_num = 1
            max_steps = 50

            result["reduce_steps"].append({
                "step": 0,
                "current": self._tokens_to_string(current),
                "handle": None,
                "action": "初始句子",
                "is_start": True
            })

            while step_num <= max_steps:
                start, end, pattern, reduced_symbol = self._find_match(current)

                if start is None:
                    if len(current) == 1 and current[0] == "E":
                        result["reduce_steps"].append({
                            "step": step_num,
                            "current": self._tokens_to_string(current),
                            "action": f"✓ 归约完成！最终归约到 {current[0]}",
                            "is_final": True
                        })
                        result["success"] = True
                        break
                    else:
                        result["message"] = f"归约失败：无法找到匹配的产生式"
                        break

                handle_text = self._tokens_to_string(current[start:end])
                pattern_str = self._tokens_to_string(pattern)

                new_current = current[:start] + [reduced_symbol] + current[end:]

                result["reduce_steps"].append({
                    "step": step_num,
                    "current": self._tokens_to_string(current),
                    "handle": handle_text,
                    "handle_pos": (start, end),
                    "pattern": pattern_str,
                    "reduced_to": reduced_symbol,
                    "action": f"归约 '{handle_text}' → {reduced_symbol} (匹配: {pattern_str} → {reduced_symbol})",
                    "new_current": self._tokens_to_string(new_current)
                })

                current = new_current
                step_num += 1

                if len(current) == 1 and current[0] == "E":
                    result["reduce_steps"].append({
                        "step": step_num,
                        "current": self._tokens_to_string(current),
                        "action": f"🎉 归约成功！最终归约到 {current[0]}",
                        "is_final": True
                    })
                    result["success"] = True
                    break

            if not result["success"] and not result["message"]:
                if len(current) == 1 and current[0] == "E":
                    result["success"] = True
                else:
                    result["message"] = f"归约未能到达开始符号，当前: {self._tokens_to_string(current)}"

        except Exception as e:
            result["message"] = f"归约错误: {str(e)}"

        return result

    def get_handle_explanation(self) -> str:
        """获取句柄知识讲解"""
        return """
【句柄（Handle）详解】

定义：
  句柄是句型中最左边的直接短语（最左简单短语）。

【id+id*id 的完整归约过程】

文法：
  E → E + T | T
  T → T * F | F
  F → (E) | id | num

句子: id + id * id

归约步骤：
  步骤0: id + id * id           (初始句子)
  步骤1: 归约 id → F            → F + id * id
  步骤2: 归约 F → T             → T + id * id
  步骤3: 归约 id → F            → T + F * id
  步骤4: 归约 F → T             → T + T * id
  步骤5: 归约 id → F            → T + T * F
  步骤6: 归约 T * F → T         → T + T
  步骤7: 归约 T → E             → E + T
  步骤8: 归约 E + T → E         → E

句柄的作用：
  • 自底向上语法分析中，每次归约的对象就是句柄
  • 移进-归约分析器通过反复寻找和归约句柄来完成分析
"""


__all__ = ['HandleAnalyzer']