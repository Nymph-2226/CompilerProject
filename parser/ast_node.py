"""AST节点定义"""
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, field


@dataclass
class ASTNode:
    """抽象语法树节点"""
    type: str
    value: Any = None
    children: List['ASTNode'] = field(default_factory=list)
    line: int = 0
    column: int = 0

    def pprint(self, indent: int = 0, prefix: str = "") -> str:
        """打印AST结构"""
        lines = []
        node_name = f"{self.type}"
        if self.value is not None:
            node_name += f": {self.value}"

        if indent == 0:
            lines.append(node_name)
        else:
            lines.append(f"{prefix}└── {node_name}")

        new_prefix = prefix + ("    " if indent == 0 else "    ")
        for i, child in enumerate(self.children):
            is_last = (i == len(self.children) - 1)
            if is_last:
                child_prefix = new_prefix + "    "
            else:
                child_prefix = new_prefix + "│   "
            child_lines = child.pprint(indent + 1, child_prefix)
            lines.extend(child_lines)

        return "\n".join(lines)

    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            "type": self.type,
            "value": self.value,
            "children": [child.to_dict() for child in self.children]
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'ASTNode':
        """从字典创建节点"""
        node = cls(
            type=data["type"],
            value=data.get("value"),
            children=[cls.from_dict(child) for child in data.get("children", [])]
        )
        return node


@dataclass
class ParseResult:
    """解析结果"""
    success: bool
    ast: Optional[ASTNode] = None
    errors: List[str] = field(default_factory=list)
    recovered: bool = False


__all__ = ['ASTNode', 'ParseResult']