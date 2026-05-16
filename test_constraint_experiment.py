"""
文法约束生成对照实验
对比"无约束"和"文法约束"的格式合规率
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 修改导入路径
from llm.grammar_constrained import GrammarConstrainedGenerator
from llm.llm_client import LLMClient


def run_constraint_experiment():
    """运行约束生成对照实验"""
    print("=" * 70)
    print("文法约束生成对照实验")
    print("=" * 70)
    
    # 测试数据：各种格式错误的LLM输出
    test_outputs = [
        # 正确格式
        """FEEDBACK {
    SCORE: 85;
    LEVEL: medium;
    COMMENT {
        TEXT: "代码逻辑清晰";
        SUGGESTION: "增加注释";
    }
    ERRORS [];
}""",
        # 缺少分号
        """FEEDBACK {
    SCORE: 85
    LEVEL: medium
    COMMENT {
        TEXT: "代码逻辑清晰"
        SUGGESTION: "增加注释"
    }
    ERRORS []
}""",
        # 缺少括号
        """FEEDBACK {
    SCORE: 85;
    LEVEL: medium;
    COMMENT
        TEXT: "代码逻辑清晰";
        SUGGESTION: "增加注释";
    ERRORS [];
}""",
        # 随机文字
        """这段代码写得不错，分数85分，建议增加注释。""",
        # 混合格式
        """好的，我来分析一下代码：
FEEDBACK {
    SCORE: 92
    LEVEL: high
    COMMENT {
        TEXT: "算法正确"
        SUGGESTION: "优化性能"
    }
    ERRORS []
}
以上就是我的评价。"""
    ]
    
    generator = GrammarConstrainedGenerator(grammar_type="feedback")
    
    results = {
        "raw_compliant": 0,
        "constrained_compliant": 0,
        "corrections_total": 0
    }
    
    print("\n📊 测试结果:")
    print("-" * 50)
    
    for i, output in enumerate(test_outputs, 1):
        print(f"\n测试用例 {i}:")
        print(f"  原始输出长度: {len(output)}")
        
        # 约束生成
        result = generator.constrain_generation(output)
        
        print(f"  格式合规: {'✅' if result.format_compliant else '❌'}")
        print(f"  修正次数: {len(result.corrections)}")
        
        if result.format_compliant:
            results["constrained_compliant"] += 1
        
        results["corrections_total"] += len(result.corrections)
    
    print("\n" + "=" * 50)
    print("📊 对照实验结果汇总")
    print("=" * 50)
    print(f"  测试总数: {len(test_outputs)}")
    print(f"  约束后合规数: {results['constrained_compliant']}")
    print(f"  格式合规率: {results['constrained_compliant']/len(test_outputs)*100:.1f}%")
    print(f"  平均修正次数: {results['corrections_total']/len(test_outputs):.1f}")


def compare_with_without_constraint():
    """对比有无约束的效果"""
    print("\n" + "=" * 70)
    print("有无约束对比实验")
    print("=" * 70)
    
    llm_client = LLMClient(mock_mode=True)
    
    test_code = """
def add(a, b):
    return a + b
"""
    
    # 获取原始LLM输出
    raw_output, _ = llm_client.call_with_retry(
        "你是AI助教，请批改代码。",
        f"请批改代码:\n{test_code}"
    )
    
    print(f"原始LLM输出:\n{raw_output[:200]}...")
    
    # 应用约束
    generator = GrammarConstrainedGenerator()
    constrained_result = generator.constrain_generation(raw_output)
    
    print(f"\n约束后输出:\n{constrained_result.constrained_text[:200]}...")
    print(f"\n格式合规: {'✅' if constrained_result.format_compliant else '❌'}")


if __name__ == "__main__":
    run_constraint_experiment()
    compare_with_without_constraint()