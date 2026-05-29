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
    """

    def __init__(self):
        self.cost_insert = 1.0
        self.cost_delete = 1.0
        self.cost_replace = 1.0

    def compare(self, tree1: TreeNode, tree2: TreeNode, threshold: float = 0.7) -> ComparisonResult:
        """比较两棵AST树的相似度"""
        # 计算编辑距离
        distance = self._tree_edit_distance(tree1, tree2)
        
        # 计算最大可能距离
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
        计算树编辑距离 - 修正版
        
        使用后序遍历和动态规划
        """
        if t1 is None and t2 is None:
            return 0
        if t1 is None:
            # 插入 t2 的所有节点
            return self.cost_insert * self._tree_size(t2)
        if t2 is None:
            # 删除 t1 的所有节点
            return self.cost_delete * self._tree_size(t1)
        
        # 获取后序遍历序列
        nodes1 = self._postorder(t1)
        nodes2 = self._postorder(t2)
        
        # 获取每个节点的子节点范围
        range1 = self._get_subtree_range(t1)
        range2 = self._get_subtree_range(t2)
        
        m, n = len(nodes1), len(nodes2)
        dp = [[0.0] * (n + 1) for _ in range(m + 1)]
        
        # 初始化
        for i in range(1, m + 1):
            dp[i][0] = dp[i-1][0] + self.cost_delete
        for j in range(1, n + 1):
            dp[0][j] = dp[0][j-1] + self.cost_insert
        
        # 动态规划
        for i in range(1, m + 1):
            for j in range(1, n + 1):
                node1 = nodes1[i-1]
                node2 = nodes2[j-1]
                
                # 获取子树范围
                l1 = range1[node1]
                l2 = range2[node2]
                
                if l1[0] == l1[1] or l2[0] == l2[1]:
                    # 叶子节点或单节点子树
                    if self._nodes_equal(node1, node2):
                        # 节点相同，不需要替换成本
                        replace_cost = dp[i-1][j-1]
                    else:
                        replace_cost = dp[i-1][j-1] + self.cost_replace
                    
                    delete_cost = dp[i-1][j] + self.cost_delete
                    insert_cost = dp[i][j-1] + self.cost_insert
                    dp[i][j] = min(replace_cost, delete_cost, insert_cost)
                else:
                    # 计算子树编辑距离
                    forest_dist = self._forest_distance(
                        nodes1[l1[0]:l1[1]], 
                        nodes2[l2[0]:l2[1]],
                        range1, range2
                    )
                    dp[i][j] = min(
                        dp[l1[0]-1][l2[0]-1] + forest_dist,
                        dp[i-1][j] + self.cost_delete,
                        dp[i][j-1] + self.cost_insert
                    )
        
        return dp[m][n]
    
    def _forest_distance(self, forest1: List[TreeNode], forest2: List[TreeNode],
                         range1: Dict, range2: Dict) -> float:
        """计算森林编辑距离"""
        m, n = len(forest1), len(forest2)
        dp = [[0.0] * (n + 1) for _ in range(m + 1)]
        
        for i in range(1, m + 1):
            dp[i][0] = dp[i-1][0] + self.cost_delete
        for j in range(1, n + 1):
            dp[0][j] = dp[0][j-1] + self.cost_insert
        
        for i in range(1, m + 1):
            for j in range(1, n + 1):
                node1 = forest1[i-1]
                node2 = forest2[j-1]
                
                l1 = range1[node1]
                l2 = range2[node2]
                
                if self._nodes_equal(node1, node2):
                    replace_cost = dp[i-1][j-1]
                else:
                    replace_cost = dp[i-1][j-1] + self.cost_replace
                
                delete_cost = dp[i-1][j] + self.cost_delete
                insert_cost = dp[i][j-1] + self.cost_insert
                dp[i][j] = min(replace_cost, delete_cost, insert_cost)
        
        return dp[m][n]
    
    def _postorder(self, node: TreeNode) -> List[TreeNode]:
        """后序遍历"""
        result = []
        for child in node.children:
            result.extend(self._postorder(child))
        result.append(node)
        return result
    
    def _get_subtree_range(self, node: TreeNode) -> Dict[TreeNode, Tuple[int, int]]:
        """获取每个节点的子树范围（后序遍历中的起始和结束索引）"""
        nodes = self._postorder(node)
        range_map = {}
        
        for i, n in enumerate(nodes):
            # 找到以 n 为根的子树的所有节点
            subtree_nodes = self._get_subtree_nodes(n)
            indices = [nodes.index(x) for x in subtree_nodes if x in nodes]
            if indices:
                range_map[n] = (min(indices), max(indices) + 1)
            else:
                range_map[n] = (i, i + 1)
        
        return range_map
    
    def _get_subtree_nodes(self, node: TreeNode) -> List[TreeNode]:
        """获取子树的所有节点"""
        result = [node]
        for child in node.children:
            result.extend(self._get_subtree_nodes(child))
        return result

    def _nodes_equal(self, n1: TreeNode, n2: TreeNode) -> bool:
        """判断两个节点是否相等"""
        if n1.label != n2.label:
            return False
        # 比较值（如果存在）
        if n1.value is not None and n2.value is not None:
            # 对于叶子节点，比较值
            if n1.label in ['id', 'num', 'string', 'const']:
                return n1.value == n2.value
            # 对于运算符，比较值
            if n1.label in ['+', '-', '*', '/']:
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
            diff_msg = f"~ {path}: {t1.label} → {t2.label}"
            if t1.value != t2.value and t1.value and t2.value:
                diff_msg += f" (值: {t1.value} → {t2.value})"
            differences.append(diff_msg)

        # 递归比较子节点
        max_len = max(len(t1.children), len(t2.children))
        for i in range(max_len):
            child1 = t1.children[i] if i < len(t1.children) else None
            child2 = t2.children[i] if i < len(t2.children) else None
            child_path = f"{path}/{i}" if path else f"[{i}]"
            differences.extend(self._find_differences(child1, child2, child_path))

        return differences

    def get_similarity_report(self, student_ast, reference_ast) -> str:
        """生成相似度分析报告"""
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