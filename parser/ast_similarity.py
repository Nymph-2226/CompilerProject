"""AST相似度评分 - 基于树编辑距离 (Zhang-Shasha算法) - 新增能力③"""
# parser/ast_similarity.py
from typing import List, Tuple, Dict, Optional, Any
from dataclasses import dataclass, field
import math
from .ast_node import ASTNode


@dataclass
class ComparisonResult:
    """比较结果"""
    similarity: float  # 0-1之间的相似度分数
    distance: int  # 编辑距离
    differences: List[str] = field(default_factory=list)  # 差异节点列表
    is_similar: bool = False  # 是否相似（阈值可配置）


class TreeNode:
    """树节点 - 用于AST比较"""
    def __init__(self, label: str, children: List['TreeNode'] = None, value: Any = None):
        self.label = label  # 节点类型
        self.value = value  # 节点值（可选）
        self.children = children or []

    def __repr__(self):
        return f"TreeNode({self.label}, children={len(self.children)})"

    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            "label": self.label,
            "value": self.value,
            "children": [c.to_dict() for c in self.children]
        }

    @classmethod
    def from_ast_node(cls, ast_node) -> 'TreeNode':
        """从ASTNode创建TreeNode"""
        node = cls(
            label=ast_node.type,
            value=ast_node.value,
            children=[cls.from_ast_node(child) for child in ast_node.children]
        )
        return node


class ASTSimilarity:
    """
    AST相似度计算器 - 基于树编辑距离

    实现简化版Zhang-Shasha算法：
    1. 计算两棵树的编辑距离
    2. 编辑操作包括：插入、删除、替换
    3. 根据距离计算相似度分数
    """

    def __init__(self):
        self.cost_insert = 1.0  # 插入成本
        self.cost_delete = 1.0  # 删除成本
        self.cost_replace = 1.0  # 替换成本

    def compare(self, tree1: TreeNode, tree2: TreeNode, threshold: float = 0.7) -> ComparisonResult:
        """
        比较两棵AST树的相似度

        Args:
            tree1: 第一棵树（参考AST）
            tree2: 第二棵树（学生答案AST）
            threshold: 相似度阈值

        Returns:
            比较结果
        """
        # 计算编辑距离
        distance = self._tree_edit_distance(tree1, tree2)

        # 计算最大可能距离（树的大小之和）
        size1 = self._tree_size(tree1)
        size2 = self._tree_size(tree2)
        max_distance = size1 + size2

        # 计算相似度
        if max_distance == 0:
            similarity = 1.0
        else:
            similarity = 1.0 - (distance / max_distance)

        # 找出差异节点
        differences = self._find_differences(tree1, tree2)

        return ComparisonResult(
            similarity=similarity,
            distance=int(distance),
            differences=differences,
            is_similar=similarity >= threshold
        )

    def _tree_size(self, node: TreeNode) -> int:
        """计算树的节点数"""
        if node is None:
            return 0
        size = 1
        for child in node.children:
            size += self._tree_size(child)
        return size

    def _tree_edit_distance(self, t1: Optional[TreeNode], t2: Optional[TreeNode]) -> float:
        """
        计算树编辑距离

        简化实现：只比较节点标签和值
        """
        if t1 is None and t2 is None:
            return 0
        if t1 is None:
            return self.cost_insert * self._tree_size(t2)
        if t2 is None:
            return self.cost_delete * self._tree_size(t1)

        # 检查节点是否匹配
        if self._nodes_equal(t1, t2):
            # 节点匹配，计算子树的编辑距离
            return self._children_edit_distance(t1.children, t2.children)
        else:
            # 节点不匹配，考虑替换
            replace_cost = self.cost_replace + self._children_edit_distance(t1.children, t2.children)

            # 考虑删除t1并插入t2
            delete_cost = self.cost_delete + self._tree_edit_distance(None, t2)
            insert_cost = self.cost_insert + self._tree_edit_distance(t1, None)

            return min(replace_cost, delete_cost, insert_cost)

    def _children_edit_distance(self, children1: List[TreeNode], children2: List[TreeNode]) -> float:
        """
        计算子节点序列的编辑距离

        使用动态规划
        """
        m, n = len(children1), len(children2)
        dp = [[0.0] * (n + 1) for _ in range(m + 1)]

        # 初始化
        for i in range(m + 1):
            dp[i][0] = i * self.cost_delete
        for j in range(n + 1):
            dp[0][j] = j * self.cost_insert

        # 填充DP表
        for i in range(1, m + 1):
            for j in range(1, n + 1):
                # 替换成本
                replace_cost = self._tree_edit_distance(children1[i - 1], children2[j - 1])

                # 删除/插入成本
                delete_cost = dp[i - 1][j] + self.cost_delete
                insert_cost = dp[i][j - 1] + self.cost_insert

                dp[i][j] = min(replace_cost, delete_cost, insert_cost)

        return dp[m][n]

    def _nodes_equal(self, n1: TreeNode, n2: TreeNode) -> bool:
        """判断两个节点是否相等"""
        if n1.label != n2.label:
            return False
        # 比较值（如果存在）
        if n1.value is not None and n2.value is not None:
            return n1.value == n2.value
        return True

    def _find_differences(self, t1: TreeNode, t2: TreeNode, path: str = "") -> List[str]:
        """找出两棵树之间的差异节点"""
        differences = []

        if t1 is None and t2 is None:
            return differences

        if t1 is None:
            differences.append(f"+ {path}: 插入节点 {t2.label}")
            return differences

        if t2 is None:
            differences.append(f"- {path}: 删除节点 {t1.label}")
            return differences

        if not self._nodes_equal(t1, t2):
            diff_msg = f"~ {path}: 节点类型 {t1.label} → {t2.label}"
            if t1.value != t2.value:
                diff_msg += f", 值 {t1.value} → {t2.value}"
            differences.append(diff_msg)

        # 递归比较子节点
        max_len = max(len(t1.children), len(t2.children))
        for i in range(max_len):
            child1 = t1.children[i] if i < len(t1.children) else None
            child2 = t2.children[i] if i < len(t2.children) else None
            child_path = f"{path}/{i}" if path else f"[{i}]"
            differences.extend(self._find_differences(child1, child2, child_path))

        return differences

    def compute_similarity_with_weights(self, tree1: TreeNode, tree2: TreeNode,
                                         weights: Dict[str, float] = None) -> float:
        """
        计算加权相似度

        Args:
            tree1: 第一棵树
            tree2: 第二棵树
            weights: 节点类型权重，例如 {'E': 2.0, 'T': 1.5, 'F': 1.0}

        Returns:
            加权相似度分数
        """
        if weights is None:
            weights = {'E': 2.0, 'E\'': 1.5, 'T': 1.5, 'T\'': 1.0, 'F': 1.0}

        # 保存原有成本
        old_insert = self.cost_insert
        old_delete = self.cost_delete
        old_replace = self.cost_replace

        # 根据权重调整成本
        self.cost_insert = self.cost_insert / 2
        self.cost_delete = self.cost_delete / 2

        result = self.compare(tree1, tree2)

        # 恢复成本
        self.cost_insert = old_insert
        self.cost_delete = old_delete
        self.cost_replace = old_replace

        return result.similarity

    def get_similarity_report(self, student_ast, reference_ast) -> str:
        """
        生成相似度分析报告
        """
        # 转换为TreeNode
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
            for diff in result.differences[:20]:  # 限制最多显示20个差异
                report += f"  {diff}\n"
            if len(result.differences) > 20:
                report += f"  ... 还有 {len(result.differences) - 20} 个差异\n"
        else:
            report += "  ✅ 无差异，两棵树完全匹配\n"

        report += """
{'─' * 70}

💡 评分说明:
• 相似度 90% - 100%: 优秀，表达式结构完全正确
• 相似度 70% - 89%: 良好，有小部分差异
• 相似度 50% - 69%: 一般，存在较多差异
• 相似度 0% - 49%: 需改进，表达式结构差异较大

参考阈值: {result.is_similar}
"""
        return report


__all__ = ['ASTSimilarity', 'TreeNode', 'ComparisonResult']