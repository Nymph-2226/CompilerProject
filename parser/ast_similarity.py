"""AST相似度评分 - 优化成本 + 规范化预处理"""
# parser/ast_similarity.py
from typing import List, Tuple, Dict, Optional, Any
from dataclasses import dataclass, field
from .ast_node import ASTNode


@dataclass
class ComparisonResult:
    similarity: float
    distance: int
    differences: List[str] = field(default_factory=list)
    is_similar: bool = False


class TreeNode:
    def __init__(self, label: str, children: List['TreeNode'] = None, value: Any = None):
        self.label = label
        self.value = value
        self.children = children or []

    def __repr__(self):
        return f"TreeNode({self.label}, value={self.value}, children={len(self.children)})"

    @classmethod
    def from_ast_node(cls, ast_node) -> 'TreeNode':
        return cls(
            label=ast_node.type,
            value=ast_node.value,
            children=[cls.from_ast_node(child) for child in ast_node.children]
        )


class ASTSimilarity:
    def __init__(self):
        # 调整插入/删除成本，降低对增加节点的惩罚
        self.cost_insert = 0.6
        self.cost_delete = 0.6
        self.cost_replace = 1.0
        self.cost_leaf_value_diff = 0.3
        self.cost_operator_diff = 1.0
        self.cost_structure_penalty = 0.1        # 子节点数量差异轻量惩罚

    def compare(self, tree1: TreeNode, tree2: TreeNode, threshold: float = 0.7) -> ComparisonResult:
        # 规范化：处理交换律和结合律
        norm_tree1 = self._normalize(tree1)
        norm_tree2 = self._normalize(tree2)
        distance = self._tree_edit_distance(norm_tree1, norm_tree2)
        size1 = self._tree_size(norm_tree1)
        size2 = self._tree_size(norm_tree2)
        max_size = max(size1, size2)
        similarity = 1.0 - (distance / max_size) if max_size > 0 else 1.0
        similarity = max(0.0, min(1.0, similarity))
        differences = self._find_differences(norm_tree1, norm_tree2)
        return ComparisonResult(
            similarity=similarity,
            distance=int(distance),
            differences=differences,
            is_similar=similarity >= threshold
        )

    def _normalize(self, node: TreeNode) -> TreeNode:
        """规范化：交换律排序子节点，结合律左结合"""
        # 先递归规范化子节点
        new_children = [self._normalize(child) for child in node.children]
        # 对于加法或乘法节点，按子节点标签排序（忽略顺序，处理交换律）
        if node.label in ['+', '*']:
            # 对子节点排序：按标签的字符串顺序，保持稳定性
            new_children.sort(key=lambda x: (x.label, str(x.value)))
        # 处理结合律：将右结合的加法/乘法转为左结合（这里简化：不改变树结构，因为 DP 已考虑顺序；排序已足够）
        # 如果需要，可以进一步展平同层节点，但会增加复杂度，先不做。
        return TreeNode(node.label, new_children, node.value)

    def _tree_size(self, node: TreeNode) -> int:
        if node is None:
            return 0
        size = 1
        for child in node.children:
            size += self._tree_size(child)
        return size

    def _tree_edit_distance(self, t1: Optional[TreeNode], t2: Optional[TreeNode]) -> float:
        if t1 is None and t2 is None:
            return 0
        if t1 is None:
            return self.cost_insert * self._tree_size(t2)
        if t2 is None:
            return self.cost_delete * self._tree_size(t1)

        replace_cost = self._node_cost(t1, t2)
        children_cost = self._children_edit_distance(t1.children, t2.children)
        structure_penalty = self.cost_structure_penalty * abs(len(t1.children) - len(t2.children))
        return replace_cost + children_cost + structure_penalty

    def _node_cost(self, n1: TreeNode, n2: TreeNode) -> float:
        leaf_types = {'id', 'num', 'string', 'const', 'IDENT', 'NUMBER', 'STRING'}
        if n1.label != n2.label:
            return self.cost_replace
        if n1.label in leaf_types:
            return 0.0 if n1.value == n2.value else self.cost_leaf_value_diff
        if n1.label in ['+', '-', '*', '/']:
            return 0.0 if n1.value == n2.value else self.cost_operator_diff
        return 0.0

    def _children_edit_distance(self, children1: List[TreeNode], children2: List[TreeNode]) -> float:
        m, n = len(children1), len(children2)
        dp = [[0.0] * (n + 1) for _ in range(m + 1)]
        for i in range(1, m + 1):
            dp[i][0] = dp[i-1][0] + self.cost_delete
        for j in range(1, n + 1):
            dp[0][j] = dp[0][j-1] + self.cost_insert
        for i in range(1, m + 1):
            for j in range(1, n + 1):
                replace = dp[i-1][j-1] + self._tree_edit_distance(children1[i-1], children2[j-1])
                delete = dp[i-1][j] + self.cost_delete
                insert = dp[i][j-1] + self.cost_insert
                dp[i][j] = min(replace, delete, insert)
        return dp[m][n]

    def _find_differences(self, t1: TreeNode, t2: TreeNode, path: str = "") -> List[str]:
        differences = []
        if t1 is None and t2 is None:
            return differences
        if t1 is None:
            differences.append(f"+ {path}: 插入节点 {t2.label}")
            return differences
        if t2 is None:
            differences.append(f"- {path}: 删除节点 {t1.label}")
            return differences

        leaf_types = {'id', 'num', 'string', 'const', 'IDENT', 'NUMBER', 'STRING'}
        if t1.label != t2.label:
            differences.append(f"~ {path}: {t1.label} → {t2.label}")
        elif t1.label in leaf_types and t1.value != t2.value:
            differences.append(f"~ {path}: {t1.value} → {t2.value}")
        elif t1.value != t2.value and t1.value and t2.value:
            differences.append(f"~ {path}: {t1.value} → {t2.value}")

        max_len = max(len(t1.children), len(t2.children))
        for i in range(max_len):
            child1 = t1.children[i] if i < len(t1.children) else None
            child2 = t2.children[i] if i < len(t2.children) else None
            child_path = f"{path}/{i}" if path else f"[{i}]"
            differences.extend(self._find_differences(child1, child2, child_path))
        return differences

    def get_similarity_report(self, student_ast, reference_ast) -> str:
        tree1 = TreeNode.from_ast_node(reference_ast)
        tree2 = TreeNode.from_ast_node(student_ast)
        result = self.compare(tree1, tree2)

        report = f"""
╔═══════════════════════════════════════════════════════════════════════════════╗
║                         AST相似度分析报告                                      ║
╚═══════════════════════════════════════════════════════════════════════════════╝

📊 相似度评分: {result.similarity:.2%}
📏 编辑距离: {result.distance}
🎯 相似性判断: {'✅ 相似' if result.is_similar else '❌ 不相似'}

{'─' * 70}

📝 差异节点列表:
"""
        if result.differences:
            for diff in result.differences[:20]:
                report += f"  {diff}\n"
            if len(result.differences) > 20:
                report += f"  ... 还有 {len(result.differences) - 20} 个差异\n"
        else:
            report += "  ✅ 无差异，两棵树完全匹配\n"

        report += f"""
{'─' * 70}

💡 评分说明:
• 相似度 90% - 100%: 优秀，表达式结构完全正确
• 相似度 70% - 89%: 良好，有小部分差异
• 相似度 50% - 69%: 一般，存在较多差异
• 相似度 0% - 49%: 需改进，表达式结构差异较大

参考阈值: {'相似' if result.is_similar else '不相似'}
"""
        return report


__all__ = ['ASTSimilarity', 'TreeNode', 'ComparisonResult']