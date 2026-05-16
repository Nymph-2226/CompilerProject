"""知识库模块"""
from typing import Dict, List


class KnowledgeBase:
    """计算机专业课知识库"""

    def __init__(self):
        self.knowledge = {
            "编译原理": {
                "什么是编译器？": "编译器是一种将高级编程语言源代码转换为目标代码（通常是机器码）的程序。\n主要阶段包括：词法分析、语法分析、语义分析、中间代码生成、代码优化和目标代码生成。",
                "什么是词法分析？": "词法分析是编译过程的第一阶段，它将源代码的字符流转换为记号（Token）流。\n词法分析器会识别出关键字、标识符、常量、运算符、界符等基本语法单元。",
                "什么是DFA？": "确定有限自动机（DFA）是一种计算模型，包含有限个状态，根据输入进行状态转移，用于识别正则语言。",
                "什么是LL(1)文法？": "LL(1)文法是一种自顶向下的语法分析方法，L表示从左到右扫描输入，L表示最左推导，1表示每次向前看一个符号。",
                "什么是句柄？": "句柄（Handle）是句型中最左边的直接短语（最左简单短语）。在自底向上语法分析中，句柄是归约操作的基本单位。",
                "什么是0型文法？": "0型文法（无限制文法）是最一般的文法，对产生式没有任何限制，形式为 α → β。",
                "什么是1型文法？": "1型文法（上下文有关文法）要求产生式满足 |α| ≤ |β|，形式为 αAβ → αγβ。",
                "什么是2型文法？": "2型文法（上下文无关文法）要求产生式左边是单个非终结符，形式为 A → γ。",
                "什么是3型文法？": "3型文法（正则文法）产生式形式为 A → aB 或 A → a，识别正则语言。",
            }
        }

    def search(self, question: str) -> str:
        question_lower = question.lower().strip()
        for category, qa_dict in self.knowledge.items():
            for q, a in qa_dict.items():
                if q.lower() == question_lower:
                    return a
        return "抱歉，知识库中暂无相关内容。您可以尝试询问：什么是编译器？什么是DFA？"

    def search_by_topic(self, topic: str) -> str:
        for category, qa_dict in self.knowledge.items():
            for q, a in qa_dict.items():
                if topic in q:
                    return a
        return None

    def get_all_topics(self) -> List[str]:
        return list(self.knowledge.keys())

    def get_topic_stats(self) -> Dict[str, int]:
        stats = {}
        for topic, qa_dict in self.knowledge.items():
            stats[topic] = len(qa_dict)
        return stats