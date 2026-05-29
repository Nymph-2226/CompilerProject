# semantic/symbol_table.py - 完整修复版

import re
from typing import Dict, List, Optional, Set, Tuple
from dataclasses import dataclass, field
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
    initialized: bool = False


class SemanticAnalyzer:
    """语义分析器 - 检测变量重定义、未声明引用、未初始化使用"""
    
    def __init__(self):
        self.symbols: Dict[str, Symbol] = {}
        self.errors: List[str] = []
        self.in_function = False
        self.current_function = None
        self.has_return = False
    
    def analyze_code(self, code: str) -> bool:
        """分析代码字符串"""
        self.symbols.clear()
        self.errors.clear()
        self.in_function = False
        self.current_function = None
        self.has_return = False
        
        lines = code.split('\n')
        
        # 第一遍：收集所有变量声明
        for line_num, line in enumerate(lines, 1):
            line = line.strip()
            if not line or line.startswith('//'):
                continue
            
            # 匹配声明语句: int x, int x = 1, int x=1
            declare_match = re.match(r'(int|float|var|double|char|bool)\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*(?:=.*)?', line)
            if declare_match:
                var_type = declare_match.group(1)
                var_name = declare_match.group(2)
                
                # 检查变量名是否合法
                if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', var_name):
                    self.errors.append(
                        f"语法错误: 变量名 '{var_name}' 在第 {line_num} 行不合法"
                    )
                    continue
                
                # 检查是否包含非法运算符
                operators = ['+', '-', '*', '/', '%', '&', '|', '^', '~']
                for op in operators:
                    if op in var_name:
                        self.errors.append(
                            f"语法错误: 第 {line_num} 行变量名 '{var_name}' 包含非法运算符 '{op}'"
                        )
                        break
                
                # 检查重定义
                if var_name in self.symbols:
                    existing = self.symbols[var_name]
                    self.errors.append(
                        f"变量重定义错误: '{var_name}' 已在第 {existing.line} 行定义"
                    )
                else:
                    # 确定数据类型
                    dt_map = {
                        'int': DataType.INT, 'float': DataType.FLOAT,
                        'double': DataType.FLOAT, 'bool': DataType.BOOL,
                        'char': DataType.STRING, 'var': DataType.UNKNOWN
                    }
                    dt = dt_map.get(var_type, DataType.UNKNOWN)
                    
                    # 检查是否有初始化
                    initialized = '=' in line
                    
                    self.symbols[var_name] = Symbol(
                        name=var_name,
                        kind=SymbolKind.VARIABLE,
                        data_type=dt,
                        line=line_num,
                        column=1,
                        initialized=initialized
                    )
        
        # 第二遍：检查变量使用（包括声明语句右侧的变量）
        for line_num, line in enumerate(lines, 1):
            line = line.strip()
            if not line or line.startswith('//'):
                continue
            
            keywords = self._get_keywords()
            
            # 处理带初始化的声明语句：int x = expr
            # 检查右侧表达式中的变量是否已声明
            init_declare_match = re.match(r'(int|float|var|double|char|bool)\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*=\s*(.+)$', line)
            if init_declare_match:
                var_name = init_declare_match.group(2)
                right_expr = init_declare_match.group(3).rstrip(';')
                
                # 提取右侧表达式中的所有标识符
                identifiers = re.findall(r'\b([a-zA-Z_][a-zA-Z0-9_]*)\b', right_expr)
                
                for ident in identifiers:
                    # 跳过关键字和自身变量
                    if ident in keywords or ident == var_name:
                        continue
                    # 检查变量是否已声明
                    if ident not in self.symbols:
                        self.errors.append(
                            f"未声明引用错误: 变量 '{ident}' 在第 {line_num} 行未声明"
                        )
                continue  # 处理完初始化声明，跳过后续检查
            
            # 跳过无初始化的普通声明语句（int x;）
            if re.match(r'(int|float|var|double|char|bool)\s+[a-zA-Z_][a-zA-Z0-9_]*\s*;?$', line):
                continue
            
            # 处理普通语句（赋值、表达式、return等）
            # 提取所有标识符
            identifiers = re.findall(r'\b([a-zA-Z_][a-zA-Z0-9_]*)\b', line)
            
            for ident in identifiers:
                if ident in keywords:
                    continue
                
                # 检查是否是赋值语句的左边（左值不需要检查未声明，因为会被第一遍收集）
                is_left_side = False
                if re.match(rf'^{ident}\s*=', line):
                    is_left_side = True
                if re.match(rf'^{ident}\s*[+\-*/%]=', line):
                    is_left_side = True
                
                # 检查是否是 return 语句中的变量
                is_return = line.startswith('return')
                
                # 查找变量
                if ident not in self.symbols:
                    self.errors.append(
                        f"未声明引用错误: 变量 '{ident}' 在第 {line_num} 行未声明"
                    )
                elif not is_left_side and not is_return and not self.symbols[ident].initialized:
                    self.errors.append(
                        f"未初始化错误: 变量 '{ident}' 在第 {line_num} 行使用前未初始化"
                    )
        
        return len(self.errors) == 0
    
    def _get_keywords(self) -> Set[str]:
        """获取关键字集合"""
        return {
            'int', 'float', 'var', 'double', 'char', 'bool', 'void',
            'if', 'else', 'while', 'for', 'do', 'break', 'continue',
            'return', 'include', 'using', 'namespace', 'std', 'cout', 
            'cin', 'main', 'true', 'false', 'NULL', 'nullptr',
            'printf', 'scanf', 'sizeof', 'struct', 'class', 'public',
            'private', 'protected', 'virtual', 'static', 'const'
        }
    
    def get_report(self) -> str:
        """获取分析报告"""
        report = []
        report.append("\n" + "=" * 70)
        report.append("语义分析报告")
        report.append("=" * 70)
        
        if self.errors:
            report.append("\n❌ 发现的语义错误:")
            # 去重
            unique_errors = []
            for err in self.errors:
                if err not in unique_errors:
                    unique_errors.append(err)
            for err in unique_errors:
                report.append(f"  • {err}")
        else:
            report.append("\n✅ 未发现语义错误")
        
        report.append("\n" + "=" * 70)
        report.append("符号表 (Symbol Table)")
        report.append("=" * 70)
        report.append(f"{'名称':<15} {'数据类型':<12} {'行号':<8} {'已初始化'}")
        report.append("-" * 50)
        
        for name, sym in self.symbols.items():
            data_type = sym.data_type.name
            report.append(
                f"{name:<15} {data_type:<12} {sym.line:<8} {'是' if sym.initialized else '否'}"
            )
        
        return "\n".join(report)


# 兼容旧代码的别名
SymbolTable = SemanticAnalyzer


def analyze_semantic(code: str) -> Tuple[bool, str, List[str]]:
    """便捷函数：分析代码语义"""
    analyzer = SemanticAnalyzer()
    is_valid = analyzer.analyze_code(code)
    report = analyzer.get_report()
    return is_valid, report, analyzer.errors


__all__ = ['SemanticAnalyzer', 'Symbol', 'SymbolKind', 'DataType', 'SymbolTable', 'analyze_semantic']