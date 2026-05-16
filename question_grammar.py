"""问题文法解析器和智能问答引擎"""
from typing import List, Dict
from knowledge_base import KnowledgeBase  # 添加这行

class QuestionGrammar:
    """问题文法解析器"""

    def __init__(self):
        self.Vn = {"Q", "Q_Type", "Q_Content", "Word"}
        self.Vt = {"什么", "是", "定义", "解释"}

    def parse_question(self, question: str) -> Dict:
        result = {"success": False, "topic": "", "original": question}

        if "什么" in question or "定义" in question or "解释" in question:
            for topic in ["编译器", "DFA", "LL(1)", "词法分析", "语法分析", "句柄"]:
                if topic in question:
                    result["success"] = True
                    result["topic"] = topic
                    break

        return result


class IntelligentQA:
    """智能问答引擎"""

    def __init__(self):
        self.question_parser = QuestionGrammar()
        self.knowledge_base = KnowledgeBase()

    def answer(self, question: str) -> str:
        parse_result = self.question_parser.parse_question(question)

        if not parse_result["success"]:
            return "无法理解问题。请尝试：什么是编译器？什么是DFA？"

        topic = parse_result["topic"]
        answer = self.knowledge_base.search_by_topic(topic)

        if answer:
            return f"【问题】{question}\n\n【答案】\n{answer}"
        else:
            return f"暂无关于「{topic}」的详细解释。"