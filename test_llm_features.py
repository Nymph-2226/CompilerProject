#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
LLM新增功能测试脚本

测试内容：
1. 文法引导的LLM约束生成 - 对照实验
2. 教学型语法错误诊断
3. AST相似度评分
"""

import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from llm.grammar_constrained import GrammarConstrainedGenerator
from llm.error_diagnosis import ErrorDiagnosis
from llm.feedback_parser import FeedbackParser
from parser.ast_similarity import ASTSimilarity
from parser.ast_node import ASTNode
from lexer.lexical_analyzer import LexicalAnalyzer
from parser.recursive_descent import RecursiveDescentParser


def test_grammar_constrained():
    """测试1: 文法约束生成 - 对照实验"""
    print("=" * 70)
    print("测试1: 文法引导的LLM约束生成 - 对照实验")
    print("=" * 70)

    generator = GrammarConstrainedGenerator(grammar_type="feedback")

    # 测试数据：包含格式错误的LLM输出
    test_outputs = [
        # 正确输出
        """
feedback {
    score: 85;
    level: medium;
    comment {
        text: "代码逻辑清晰";
        suggestion: "增加注释";
    }
}
""",
        # 缺少分号
        """
feedback {
    score: 85
    level: medium
    comment {
        text: "代码逻辑清晰"
        suggestion: "增加注释"
    }
}
""",
        # 缺少括号
        """
feedback {
    score: 85;
    level: medium;
    comment
        text: "代码逻辑清晰";
        suggestion: "增加注释";
}
""",
        # 随机文本
        "这是一个随机的LLM输出，不包含任何格式",
    ]

    print("\n📊 对照实验结果:")
    print("-" * 50)

    for i, output in enumerate(test_outputs, 1):
        print(f"\n测试用例 {i}:")
        print(f"原始输出长度: {len(output)} 字符")

        # 约束生成
        result = generator.constrain_generation(output)

        print(f"  格式合规: {'✅' if result.format_compliant else '❌'}")
        print(f"  修正次数: {len(result.corrections)}")

        if result.corrections:
            for corr in result.corrections[:3]:
                print(f"    - {corr}")

    # 运行对照实验
    print("\n" + "-" * 50)
    print("📊 批量对照实验:")
    experiment_result = generator.run_comparison_experiment(test_outputs)
    print(f"  总测试数: {experiment_result['total']}")
    print(f"  原始合规数: {experiment_result['raw_compliant']}")
    print(f"  约束后合规数: {experiment_result['constrained_compliant']}")
    print(f"  格式合规率提升: {experiment_result['improvement_rate']:.1%}")
    print(f"  平均修正次数: {sum(experiment_result['corrections_per_output']) / len(experiment_result['corrections_per_output']):.1f}")


def test_error_diagnosis():
    """测试2: 教学型语法错误诊断"""
    print("\n" + "=" * 70)
    print("测试2: 教学型语法错误诊断")
    print("=" * 70)

    from parser.error_recovery import ParseErrorInfo

    diagnosis = ErrorDiagnosis()

    # 模拟解析器错误信息
    error_info = ParseErrorInfo(
        position=0,
        line=5,
        column=12,
        expected={"id", "num", "("},
        found=")",
        message="语法错误：意外的右括号")