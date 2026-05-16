"""
语义分析预研接口
符号表与类型检查 - 选做+5分
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set
from enum import Enum, auto


class SymbolKind(Enum):
    """符号类型"""
    VARIABLE = auto()
    FUNCTION = auto()
    PARAMETER = auto()
    CLASS = auto()


class DataType(Enum):
    """数据类型"""
    INT = auto()
    FLOAT = auto()
    STRING = auto()
    BOOL = auto()
    VOID = auto()
    UNKNOWN = auto()


@dataclass
class Symbol:
    """符号表条目"""
    name: str
    kind: SymbolKind
    data_type: DataType
    line: int
    column: int
    scope: str = "global"
    initialized: bool = False
    references: List[int] = field(default_factory=list)


class SymbolTable:
    """符号表"""
    
    def __init__(self):
        self.symbols: Dict[str, Symbol] = {}
        self.scopes: Dict[str, List[str]] = {"global": []}
        self.current_scope = "global"
        self.errors: List[str] = []
    
    def enter_scope(self, scope_name: str):
        """进入新作用域"""
        self.current_scope = scope_name
        if scope_name not in self.scopes:
            self.scopes[scope_name] = []
    
    def exit_scope(self):
        """退出作用域"""
        self.current_scope = "global"
    
    def declare(self, name: str, kind: SymbolKind, data_type: DataType, 
                line: int, column: int) -> bool:
        """声明符号"""
        full_name = f"{self.current_scope}:{name}"
        
        # 检查是否已存在
        if full_name in self.symbols:
            self.errors.append(
                f"变量重定义错误: '{name}' 已在第 {self.symbols[full_name].line} 行定义"
            )
            return False
        
        # 在当前作用域检查同名变量
        for sym_name in self.scopes.get(self.current_scope, []):
            if sym_name == name:
                self.errors.append(
                    f"变量重定义错误: '{name}' 在当前作用域已存在"
                )
                return False
        
        symbol = Symbol(
            name=name,
            kind=kind,
            data_type=data_type,
            line=line,
            column=column,
            scope=self.current_scope
        )
        self.symbols[full_name] = symbol
        self.scopes[self.current_scope].append(name)
        return True
    
    def lookup(self, name: str, line: int, column: int) -> Optional[Symbol]:
        """查找符号（支持作用域链）"""
        # 先在当前作用域查找
        full_name = f"{self.current_scope}:{name}"
        if full_name in self.symbols:
            self.symbols[full_name].references.append(line)
            return self.symbols[full_name]
        
        # 在全局作用域查找
        global_name = f"global:{name}"
        if global_name in self.symbols:
            self.symbols[global_name].references.append(line)
            return self.symbols[global_name]
        
        # 未找到
        self.errors.append(
            f"未声明引用错误: 变量 '{name}' 在第 {line} 行未声明"
        )
        return None
    
    def check_initialized(self, name: str, line: int) -> bool:
        """检查变量是否已初始化"""
        symbol = self.lookup(name, line, line)
        if symbol and not symbol.initialized:
            self.errors.append(
                f"未初始化错误: 变量 '{name}' 在第 {line} 行使用前未初始化"
            )
            return False
        return True
    
    def set_initialized(self, name: str, line: int):
        """标记变量已初始化"""
        full_name = f"{self.current_scope}:{name}"
        if full_name in self.symbols:
            self.symbols[full_name].initialized = True
        
        global_name = f"global:{name}"
        if global_name in self.symbols:
            self.symbols[global_name].initialized = True
    
    def print_table(self) -> str:
        """打印符号表"""
        output = []
        output.append("=" * 70)
        output.append("符号表 (Symbol Table)")
        output.append("=" * 70)
        output.append(f"{'名称':<15} {'类型':<12} {'数据类型':<10} {'行号':<6} {'作用域':<10} {'已初始化'}")
        output.append("-" * 70)
        
        for full_name, sym in self.symbols.items():
            name = sym.name
            kind = sym.kind.name
            data_type = sym.data_type.name
            output.append(
                f"{name:<15} {kind:<12} {data_type:<10} {sym.line:<6} "
                f"{sym.scope:<10} {'是' if sym.initialized else '否'}"
            )
        
        return "\n".join(output)


class SemanticAnalyzer:
    """语义分析器 - 预研接口"""
    
    def __init__(self):
        self.symbol_table = SymbolTable()
        self.errors: List[str] = []
    
    def analyze(self, ast) -> bool:
        """
        分析AST，进行语义检查
        
        支持的检查：
        1. 变量重定义
        2. 未声明引用
        3. 类型检查（基础）
        """
        self.errors = []
        self._visit(ast)
        return len(self.errors) == 0
    
    def _visit(self, node):
        """遍历AST节点"""
        if node is None:
            return
        
        node_type = node.node_type if hasattr(node, 'node_type') else node.type
        
        if node_type in ['VariableDeclaration', 'DeclStmt']:
            self._check_declaration(node)
        elif node_type in ['Identifier', 'id', 'Ident']:
            self._check_reference(node)
        elif node_type in ['Assignment', 'AssignStmt']:
            self._check_assignment(node)
        
        # 递归遍历子节点
        children = node.children if hasattr(node, 'children') else []
        for child in children:
            self._visit(child)
    
    def _check_declaration(self, node):
        """检查变量声明"""
        name = self._get_name(node)
        line = self._get_line(node)
        col = self._get_column(node)
        
        if name:
            self.symbol_table.declare(
                name=name,
                kind=SymbolKind.VARIABLE,
                data_type=DataType.INT,
                line=line,
                column=col
            )
    
    def _check_reference(self, node):
        """检查变量引用"""
        name = self._get_name(node)
        line = self._get_line(node)
        col = self._get_column(node)
        
        if name:
            self.symbol_table.lookup(name, line, col)
    
    def _check_assignment(self, node):
        """检查赋值语句"""
        # 获取左值
        lhs = self._get_lhs(node)
        line = self._get_line(node)
        
        if lhs:
            # 标记变量已初始化
            self.symbol_table.set_initialized(lhs, line)
    
    def _get_name(self, node) -> str:
        """获取节点名称"""
        if hasattr(node, 'value') and node.value:
            return str(node.value)
        if hasattr(node, 'name'):
            return node.name
        return None
    
    def _get_line(self, node) -> int:
        """获取行号"""
        if hasattr(node, 'line'):
            return node.line
        return 0
    
    def _get_column(self, node) -> int:
        """获取列号"""
        if hasattr(node, 'column'):
            return node.column
        return 0
    
    def _get_lhs(self, node):
        """获取赋值左值"""
        if hasattr(node, 'children') and node.children:
            first_child = node.children[0]
            return self._get_name(first_child)
        return None
    
    def get_report(self) -> str:
        """获取分析报告"""
        report = []
        report.append("\n" + "=" * 70)
        report.append("语义分析报告")
        report.append("=" * 70)
        
        if self.errors:
            report.append("\n❌ 发现的语义错误:")
            for err in self.errors:
                report.append(f"  • {err}")
        else:
            report.append("\n✅ 未发现语义错误")
        
        report.append("\n" + self.symbol_table.print_table())
        
        return "\n".join(report)