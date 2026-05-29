# ui/main_window.py
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

# 导入各个模块
from lexer.lexical_analyzer import LexicalAnalyzer
from grammar.improved_grammar import ImprovedGrammar
from grammar.chomsky_classifier import ChomskyClassifier
from grammar.handle_analyzer import HandleAnalyzer
from parser.recursive_descent import RecursiveDescentParser
from parser.error_recovery import ErrorRecovery, ParseErrorInfo  # ✅ 从这里导入
from parser.ast_similarity import ASTSimilarity
from parser.ll1_analyzer import LL1Analyzer
from llm.llm_client import LLMClient
from llm.grammar_constrained import GrammarConstrainedGenerator
from llm.error_diagnosis import ErrorDiagnosis  # ✅ 使用你的 error_diagnosis.py
from knowledge_base import KnowledgeBase
from question_grammar import IntelligentQA

# 语义分析模块
from semantic.symbol_table import SemanticAnalyzer, analyze_semantic

class MainWindow(QMainWindow):
    """主窗口"""

    def __init__(self):
        print("1. MainWindow __init__ 开始")
        super().__init__()
        print("2. 调用 init_components")
        self.init_components()
        print("3. 调用 init_ui")
        self.init_ui()
        print("4. MainWindow __init__ 完成")
        self.current_analyzer = None

    def init_components(self):
        """初始化各个组件"""
        print("  - 初始化词法分析器...")
        self.lexical_analyzer = LexicalAnalyzer()
        
        print("  - 初始化文法...")
        self.grammar = ImprovedGrammar()
        self.handle_analyzer = HandleAnalyzer()
        self.chomsky_classifier = ChomskyClassifier()
        
        print("  - 初始化解析器...")
        self.recursive_parser = RecursiveDescentParser()
        self.error_recovery = ErrorRecovery()
        self.ast_similarity = ASTSimilarity()
        
        print("  - 初始化LLM模块...")
        self.llm_client = LLMClient(mock_mode=False)
        self.grammar_constrained = GrammarConstrainedGenerator()
        self.error_diagnosis = ErrorDiagnosis(self.llm_client)
        
        print("  - 初始化问答模块...")
        self.knowledge_base = KnowledgeBase()
        self.qa_engine = IntelligentQA()
        
        print("  - 所有组件初始化完成")

    def init_ui(self):
        """初始化UI"""
        print("  - 初始化UI...")
        self.setWindowTitle("编译原理AI助学系统 - LLM增强的词法-语法分析综合平台")
        self.setGeometry(100, 100, 1600, 1000)
        
        # 设置样式
        self.setStyleSheet("""
            QMainWindow { background-color: #f0f2f5; }
            QTabWidget::pane { border: 1px solid #ddd; border-radius: 8px; background-color: white; }
            QTabBar::tab { padding: 10px 20px; font-size: 14px; font-weight: bold; font-family: 'Microsoft YaHei'; }
            QTabBar::tab:selected { background-color: #667eea; color: white; }
            QTabBar::tab:hover:!selected { background-color: #e0e7ff; }
            QTextEdit, QPlainTextEdit {
                border: 1px solid #ddd;
                border-radius: 6px;
                padding: 10px;
                font-family: 'Consolas', monospace;
                font-size: 12px;
                background-color: #fafafa;
            }
            QLineEdit {
                border: 1px solid #ddd;
                border-radius: 6px;
                padding: 8px 12px;
                font-size: 12px;
            }
            QPushButton {
                background-color: #667eea;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-size: 12px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #5a67d8; }
            QGroupBox {
                font-weight: bold;
                font-size: 13px;
                border: 2px solid #e2e8f0;
                border-radius: 8px;
                margin-top: 12px;
                padding-top: 12px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 8px;
                background-color: white;
            }
            QLabel { color: #2d3748; }
            QStatusBar { background-color: #2d3748; color: white; }
        """)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout()
        central_widget.setLayout(main_layout)
        
        # 标题
        title_label = QLabel("📚 编译原理AI助学系统 - LLM增强的词法-语法分析综合平台")
        title_label.setStyleSheet("font-size: 20px; font-weight: bold; color: #667eea; padding: 10px; background-color: #f8fafc; border-radius: 8px;")
        title_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title_label)
        
        # 标签页
        tabs = QTabWidget()
        tabs.setTabPosition(QTabWidget.North)
        
        # 添加各个功能页面
        tabs.addTab(self.create_qa_tab(), "📚 智能问答")
        tabs.addTab(self.create_grammar_tab(), "📖 文法分析")
        tabs.addTab(self.create_lexical_tab(), "✏️ 词法分析")
        tabs.addTab(self.create_ll1_tab(), "📊 LL(1)分析")
        tabs.addTab(self.create_llm_tab(), "🤖 LLM增强功能")
        tabs.addTab(self.create_semantic_tab(), "🔍 语义分析")
        
        main_layout.addWidget(tabs)
        
        # 状态栏
        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)
        self.statusBar.showMessage("✅ 系统就绪 | LLM模式: " + ("真实API" if not self.llm_client.mock_mode else "模拟模式"))
        
        print("  - UI初始化完成")

    # ==================== 智能问答标签页 ====================
    def create_qa_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()
        
        input_group = QGroupBox("💬 输入问题")
        input_layout = QVBoxLayout()
        self.qa_input = QTextEdit()
        self.qa_input.setMaximumHeight(100)
        self.qa_input.setPlaceholderText(
            "请输入您的问题，支持多种问法：\n"
            "• 什么是编译器？\n"
            "• 解释一下数据结构\n"
            "• 什么是DFA？\n"
            "• 什么是词法分析？"
        )
        ask_btn = QPushButton("🔍 智能问答")
        ask_btn.clicked.connect(self.ask_question)
        input_layout.addWidget(self.qa_input)
        input_layout.addWidget(ask_btn)
        input_group.setLayout(input_layout)
        
        output_group = QGroupBox("📝 答案")
        output_layout = QVBoxLayout()
        self.qa_output = QTextEdit()
        self.qa_output.setReadOnly(True)
        output_layout.addWidget(self.qa_output)
        output_group.setLayout(output_layout)
        
        layout.addWidget(input_group)
        layout.addWidget(output_group)
        widget.setLayout(layout)
        return widget

    def ask_question(self):
        question = self.qa_input.toPlainText().strip()
        if not question:
            QMessageBox.warning(self, "提示", "请输入问题！")
            return
        self.statusBar.showMessage("🤔 正在分析问题...")
        answer = self.qa_engine.answer(question)
        self.qa_output.setText(answer)
        self.statusBar.showMessage("✅ 问答完成")

    # ==================== 文法分析标签页 ====================
    def create_grammar_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()
        
        # 文法信息显示
        info_group = QGroupBox("📖 文法信息")
        info_layout = QVBoxLayout()
        self.grammar_info = QTextEdit()
        self.grammar_info.setReadOnly(True)
        self.grammar_info.setFont(QFont("Consolas", 11))
        self.grammar_info.setText(self.grammar.get_grammar_info())
        info_layout.addWidget(self.grammar_info)
        info_group.setLayout(info_layout)
        
        # 句型/句子判定
        check_group = QGroupBox("🔍 句型/句子判定")
        check_layout = QHBoxLayout()
        self.string_input = QLineEdit()
        self.string_input.setPlaceholderText("输入符号串，如: id+id*id")
        check_btn = QPushButton("判定")
        check_btn.clicked.connect(self.check_string)
        check_layout.addWidget(self.string_input)
        check_layout.addWidget(check_btn)
        check_group.setLayout(check_layout)
        
        self.check_result = QTextEdit()
        self.check_result.setReadOnly(True)
        self.check_result.setMaximumHeight(80)
        
        # 符号分类
        symbol_group = QGroupBox("🔤 符号分类器")
        symbol_layout = QHBoxLayout()
        self.symbol_input = QLineEdit()
        self.symbol_input.setPlaceholderText("输入符号，如: E, T, +, id")
        classify_btn = QPushButton("分类")
        classify_btn.clicked.connect(self.classify_symbol)
        symbol_layout.addWidget(self.symbol_input)
        symbol_layout.addWidget(classify_btn)
        symbol_group.setLayout(symbol_layout)
        
        self.symbol_result = QTextEdit()
        self.symbol_result.setReadOnly(True)
        self.symbol_result.setMaximumHeight(60)
        
        layout.addWidget(info_group)
        layout.addWidget(check_group)
        layout.addWidget(self.check_result)
        layout.addWidget(symbol_group)
        layout.addWidget(self.symbol_result)
        
        widget.setLayout(layout)
        return widget

    def check_string(self):
        s = self.string_input.text().strip()
        if not s:
            QMessageBox.warning(self, "提示", "请输入符号串！")
            return
        sent, sent_msg = self.grammar.is_sentential_form(s)
        sent_msg = "✅ " + sent_msg if sent else "❌ " + sent_msg
        self.check_result.setText(sent_msg)

    def classify_symbol(self):
        symbol = self.symbol_input.text().strip()
        if not symbol:
            QMessageBox.warning(self, "提示", "请输入符号！")
            return
        result = self.grammar.classify_symbol(symbol)
        self.symbol_result.setText(result)

    # ==================== 词法分析标签页 ====================
    def create_lexical_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()
        
        input_group = QGroupBox("✏️ 输入代码或表达式")
        input_layout = QVBoxLayout()
        self.lexical_input = QPlainTextEdit()
        self.lexical_input.setMaximumHeight(200)
        self.lexical_input.setPlaceholderText(
            "请输入需要词法分析的代码或表达式，支持：\n\n"
            "1. 关键字: if, else, while, for, int, float, return 等\n"
            "2. 标识符: 变量名、函数名\n"
            "3. 常量: 整数(123)、浮点数(3.14)\n"
            "4. 运算符: +, -, *, /, =, ==, += 等\n"
            "5. 界符: ;, ,, (, ), {, }\n\n"
            "示例:\n"
            "int x = 42;\n"
            "if (x > 0) { return x; }"
        )
        analyze_btn = QPushButton("🔍 DFA词法分析")
        analyze_btn.clicked.connect(self.analyze_lexical)
        input_layout.addWidget(self.lexical_input)
        input_layout.addWidget(analyze_btn)
        input_group.setLayout(input_layout)
        
        output_group = QGroupBox("📊 词法分析结果")
        output_layout = QVBoxLayout()
        self.lexical_output = QTextEdit()
        self.lexical_output.setReadOnly(True)
        output_layout.addWidget(self.lexical_output)
        output_group.setLayout(output_layout)
        
        layout.addWidget(input_group)
        layout.addWidget(output_group)
        widget.setLayout(layout)
        return widget

    def analyze_lexical(self):
        code = self.lexical_input.toPlainText().strip()
        if not code:
            QMessageBox.warning(self, "提示", "请输入代码！")
            return
        
        self.statusBar.showMessage("✏️ 正在进行DFA词法分析...")
        tokens, errors = self.lexical_analyzer.analyze(code)
        
        output = f"输入: {code}\n\n"
        output += "=" * 80 + "\n"
        output += "【词法单元列表】\n"
        output += "-" * 80 + "\n"
        output += f"{'序号':<6} {'类型':<14} {'值':<25} {'行':<6} {'列':<6}\n"
        output += "-" * 80 + "\n"
        
        for i, token in enumerate(tokens, 1):
            output += f"{i:<6} {token.type.name:<14} {token.value:<25} {token.line:<6} {token.column:<6}\n"
        
        output += "-" * 80 + "\n\n"
        
        if errors:
            output += "【错误信息】\n"
            for err in errors:
                output += f"  ⚠️ 行 {err.line}, 列 {err.column}: {err.message}\n"
            output += f"\n共发现 {len(errors)} 个错误\n"
        else:
            output += f"✅ 共识别 {len(tokens)} 个词法单元，无错误\n"
        
        self.lexical_output.setText(output)
        
        if errors:
            self.statusBar.showMessage(f"⚠️ 词法分析完成，发现 {len(errors)} 个错误")
        else:
            self.statusBar.showMessage(f"✅ 词法分析完成，共识别 {len(tokens)} 个词法单元")

    # ==================== LL(1)分析标签页 ====================
    def create_ll1_tab(self):
        """创建LL(1)分析标签页"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # 文法选择
        select_group = QGroupBox("📖 选择文法")
        select_layout = QHBoxLayout()
        
        self.grammar_combo = QComboBox()
        self.grammar_combo.addItems([
            "反馈格式文法（作业）",
            "算术表达式文法"
        ])
        self.grammar_combo.currentTextChanged.connect(self.on_grammar_changed)
        
        select_layout.addWidget(QLabel("文法类型:"))
        select_layout.addWidget(self.grammar_combo)
        select_layout.addStretch()
        select_group.setLayout(select_layout)
        
        # 自定义文法输入
        custom_group = QGroupBox("✏️ 自定义文法（可选）")
        custom_layout = QVBoxLayout()
        self.custom_grammar_input = QPlainTextEdit()
        self.custom_grammar_input.setPlaceholderText(
            "请输入文法产生式，每行一条，使用 -> 或 →\n"
            "示例：\n"
            "S -> a S | b\n"
            "E -> E + T | T\n"
            "T -> F\n"
            "F -> ( E ) | id"
        )
        self.custom_grammar_input.setMaximumHeight(150)
        use_custom_btn = QPushButton("使用自定义文法")
        use_custom_btn.clicked.connect(self.use_custom_grammar)
        custom_layout.addWidget(self.custom_grammar_input)
        custom_layout.addWidget(use_custom_btn)
        custom_group.setLayout(custom_layout)
        
        # 分析按钮
        analyze_btn = QPushButton("🔍 执行LL(1)分析")
        analyze_btn.setStyleSheet("background-color: #48bb78; font-size: 14px; padding: 10px;")
        analyze_btn.clicked.connect(self.run_ll1_analysis)
        
        # 结果显示区域
        result_group = QGroupBox("📊 分析结果")
        result_layout = QVBoxLayout()
        self.ll1_result = QTextEdit()
        self.ll1_result.setReadOnly(True)
        self.ll1_result.setFont(QFont("Consolas", 11))
        result_layout.addWidget(self.ll1_result)
        result_group.setLayout(result_layout)
        
        # 布局
        layout.addWidget(select_group)
        layout.addWidget(custom_group)
        layout.addWidget(analyze_btn)
        layout.addWidget(result_group)
        
        widget.setLayout(layout)
        
        # 默认加载反馈格式文法
        self.current_analyzer = LL1Analyzer()
        self.current_analyzer.set_feedback_grammar()
        self.display_ll1_result()
        
        return widget

    def on_grammar_changed(self, grammar_type: str):
        """文法类型改变时的处理"""
        self.current_analyzer = LL1Analyzer()
        
        if grammar_type == "反馈格式文法（作业）":
            self.current_analyzer.set_feedback_grammar()
        else:
            self.current_analyzer.set_expression_grammar()
        
        self.display_ll1_result()

    def use_custom_grammar(self):
        """使用自定义文法"""
        grammar_text = self.custom_grammar_input.toPlainText().strip()
        if not grammar_text:
            QMessageBox.warning(self, "提示", "请输入文法产生式！")
            return
        
        try:
            self.current_analyzer = LL1Analyzer()
            first_line = grammar_text.split('\n')[0]
            if '->' in first_line:
                start = first_line.split('->')[0].strip()
            elif '→' in first_line:
                start = first_line.split('→')[0].strip()
            else:
                start = "S"
            
            self.current_analyzer.set_grammar(grammar_text, start)
            self.display_ll1_result()
            
            self.grammar_combo.blockSignals(True)
            self.grammar_combo.setCurrentText("自定义文法")
            self.grammar_combo.blockSignals(False)
            
        except Exception as e:
            QMessageBox.critical(self, "错误", f"文法解析失败: {str(e)}")

    def run_ll1_analysis(self):
        """执行LL(1)分析"""
        self.statusBar.showMessage("🔄 正在执行LL(1)分析...")
        
        grammar_type = self.grammar_combo.currentText()
        
        self.current_analyzer = LL1Analyzer()
        
        if grammar_type == "反馈格式文法（作业）":
            self.current_analyzer.set_feedback_grammar()
        elif grammar_type == "算术表达式文法":
            self.current_analyzer.set_expression_grammar()
        else:
            custom_text = self.custom_grammar_input.toPlainText().strip()
            if custom_text:
                try:
                    first_line = custom_text.split('\n')[0]
                    if '->' in first_line:
                        start = first_line.split('->')[0].strip()
                    elif '→' in first_line:
                        start = first_line.split('→')[0].strip()
                    else:
                        start = "S"
                    self.current_analyzer.set_grammar(custom_text, start)
                except Exception as e:
                    self.ll1_result.setText(f"❌ 文法解析失败: {str(e)}")
                    self.statusBar.showMessage("❌ 文法解析失败")
                    return
            else:
                self.current_analyzer.set_feedback_grammar()
        
        self.display_ll1_result()
        self.statusBar.showMessage("✅ LL(1)分析完成")

    def display_ll1_result(self):
        """显示LL(1)分析结果"""
        result = self.current_analyzer.analyze()
        
        output = []
        
        # 文法信息
        output.append(result.grammar_info)
        output.append("")
        
        # FIRST集
        output.append(self.current_analyzer.print_first_sets())
        output.append("")
        
        # FOLLOW集
        output.append(self.current_analyzer.print_follow_sets())
        output.append("")
        
        # 预测分析表
        output.append(self.current_analyzer.print_predict_table())
        output.append("")
        
        # LL(1)检测结果
        output.append("=" * 60)
        output.append("LL(1) 文法检测")
        output.append("=" * 60)
        
        if result.is_ll1:
            output.append("✅ 该文法是 LL(1) 文法！")
            output.append("\n验证条件：")
            output.append("  • 无左递归")
            output.append("  • 无公共左因子")
            output.append("  • 对于每个含ε产生式的非终结符，FIRST(A) ∩ FOLLOW(A) = ∅")
        else:
            output.append("❌ 该文法不是 LL(1) 文法！")
            output.append("\n冲突信息:")
            for c in result.conflicts:
                output.append(f"  • {c}")
        
        self.ll1_result.setText("\n".join(output))

    # ==================== LLM增强功能标签页 ====================
    def create_llm_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()
        
        # 功能选择
        func_group = QGroupBox("🤖 LLM增强功能")
        func_layout = QHBoxLayout()
        
        self.func_combo = QComboBox()
        self.func_combo.addItems([
            "文法约束生成",
            "语法错误诊断", 
            "反馈格式解析",
            "AST相似度评分",
            "AI代码批改"
        ])
        
        run_btn = QPushButton("🚀 运行")
        run_btn.clicked.connect(self.run_llm_function)
        
        func_layout.addWidget(QLabel("选择功能:"))
        func_layout.addWidget(self.func_combo)
        func_layout.addWidget(run_btn)
        func_layout.addStretch()
        func_group.setLayout(func_layout)
        
        # 输入区域
        input_group = QGroupBox("📝 输入")
        input_layout = QVBoxLayout()
        self.llm_input = QPlainTextEdit()
        self.llm_input.setPlaceholderText("请输入LLM输出或测试内容，或者输入代码进行批改...")
        self.llm_input.setMaximumHeight(200)
        input_layout.addWidget(self.llm_input)
        input_group.setLayout(input_layout)
        
        # 输出区域
        output_group = QGroupBox("📊 输出")
        output_layout = QVBoxLayout()
        self.llm_output = QTextEdit()
        self.llm_output.setReadOnly(True)
        output_layout.addWidget(self.llm_output)
        output_group.setLayout(output_layout)
        
        # 示例按钮
        example_group = QGroupBox("📋 示例")
        example_layout = QHBoxLayout()
        
        examples = [
            ("约束生成示例", self.set_constraint_example),
            ("错误诊断示例", self.set_diagnosis_example),
            ("反馈解析示例", self.set_feedback_example),
            ("代码批改示例", self.set_code_example),
        ]
        
        for name, func in examples:
            btn = QPushButton(name)
            btn.clicked.connect(func)
            example_layout.addWidget(btn)
        
        # API配置按钮
        api_btn = QPushButton("⚙️ API配置")
        api_btn.clicked.connect(self.show_api_config)
        example_layout.addWidget(api_btn)
        
        example_group.setLayout(example_layout)
        
        layout.addWidget(func_group)
        layout.addWidget(input_group)
        layout.addWidget(output_group)
        layout.addWidget(example_group)
        
        widget.setLayout(layout)
        return widget

    def run_llm_function(self):
        """运行选中的LLM功能"""
        func = self.func_combo.currentText()
        input_text = self.llm_input.toPlainText().strip()
        
        print(f"选中的功能: '{func}'")
        
        if not input_text:
            QMessageBox.warning(self, "提示", "请输入内容！")
            return
        
        self.statusBar.showMessage(f"🔄 正在执行 {func}...")
        
        if "文法约束" in func:
            self._run_constraint_generation(input_text)
        elif "语法错误诊断" in func:
            self._run_error_diagnosis(input_text)
        elif "反馈格式解析" in func:
            self._run_feedback_parsing(input_text)
        elif "AST" in func:
            self._run_ast_similarity(input_text)
        elif "AI代码批改" in func or "批改" in func:
            print("进入 AI代码批改 分支")
            self._run_ai_grading(input_text)
        else:
            print(f"未匹配的功能: {func}")

    def _run_constraint_generation(self, input_text: str):
        result = self.grammar_constrained.constrain_generation(input_text)
        
        output = f"""
╔═══════════════════════════════════════════════════════════════════════════════╗
║                         文法约束生成结果                                        ║
╚═══════════════════════════════════════════════════════════════════════════════╝

📝 原始输出:
{input_text[:500]}{'...' if len(input_text) > 500 else ''}

{'─' * 70}

✅ 约束后输出:
{result.constrained_text[:500] if result.constrained_text else '(空)'}

{'─' * 70}

📊 验证结果:
• 格式合规: {'✅ 是' if result.format_compliant else '❌ 否'}
• 修正次数: {len(result.corrections)}

{'─' * 70}

🔧 修正记录:
"""
        for corr in result.corrections[:10]:
            output += f"  • {corr}\n"
        
        if not result.corrections:
            output += "  无修正记录\n"
        
        self.llm_output.setText(output)
        self.statusBar.showMessage("✅ 文法约束生成完成")

    def _run_error_diagnosis(self, input_text: str):
            """运行教学型语法错误诊断"""
            # 创建错误信息
            error_info = ParseErrorInfo(
                position=0,
                line=5,
                column=12,
                expected={"id", "num", "("},
                found=")",
                message="语法错误：意外的 ')'",
                context=input_text[:200]
            )
        
            # 诊断错误
            diagnostic = self.error_diagnosis.diagnose(error_info)
        
            # 获取诊断消息（来自 error_diagnosis.py）
            message = self.error_diagnosis.get_diagnostic_message(error_info)
        
            # 尝试调用LLM生成更友好的解释
            llm_explanation = ""
            if self.llm_client and self.llm_client.is_available():
                try:
                    prompt = self.error_diagnosis.generate_llm_diagnostic_prompt(diagnostic)
                    llm_response, success = self.llm_client.call_with_retry(
                        "你是一个编程课程的助教，擅长用通俗易懂的语言解释语法错误。请直接给出解释，不要添加额外格式。",
                        prompt
                    )
                    if success:
                        llm_explanation = f"""
{'─' * 70}

🤖 AI助教详解:

{llm_response}
"""
                except Exception as e:
                    print(f"LLM调用失败: {e}")
        
            output = f"""
╔═══════════════════════════════════════════════════════════════════════════════╗
║                     📚 教学型语法错误诊断                                      ║
╚═══════════════════════════════════════════════════════════════════════════════╝

{message}
{llm_explanation}

{'─' * 70}

📊 结构化错误信息:
• 错误位置: 第 {diagnostic.position[0]} 行，第 {diagnostic.position[1]} 列
• 错误类型: {diagnostic.error_type}
• 期望内容: {', '.join(diagnostic.expected)}
• 实际内容: '{diagnostic.found}'
"""
            self.llm_output.setText(output)
            self.statusBar.showMessage("✅ 语法错误诊断完成")

    def _run_feedback_parsing(self, input_text: str):
        """解析LLM反馈格式 - 使用 llm/feedback_parser.py"""
        from llm.feedback_parser import FeedbackParser
        
        parser = FeedbackParser()
        parsed = parser.parse(input_text)
        
        output = f"""
╔═══════════════════════════════════════════════════════════════════════════════╗
║                         反馈格式解析结果                                        ║
╚═══════════════════════════════════════════════════════════════════════════════╝

📝 原始输入:
{input_text[:500]}{'...' if len(input_text) > 500 else ''}

{'─' * 70}

📊 解析结果:
• 解析成功: {'✅ 是' if parsed.success else '❌ 否'}
• 分数: {parsed.score if parsed.score else '未识别'}
• 等级: {parsed.level if parsed.level else '未识别'}
• 评语: {parsed.comment if parsed.comment else '未识别'}
• 建议: {parsed.suggestion if parsed.suggestion else '未识别'}

{'─' * 70}

📝 错误列表:
"""
        for err in parsed.errors:
            output += f"  • 行 {err.get('line', '?')}: {err.get('type', 'unknown')} - {err.get('msg', '')}\n"
        if not parsed.errors:
            output += "  无错误信息\n"
        
        if not parsed.success and parsed.error_message:
            output += f"\n⚠️ 解析错误: {parsed.error_message}\n"
        
        self.llm_output.setText(output)
        self.statusBar.showMessage("✅ 反馈解析完成")

    def _run_ast_similarity(self, input_text: str):
        """运行AST相似度评分"""
        from parser.ast_node import ASTNode
    
        # 分割学生答案和参考答案
        student_code = input_text
        reference_code = input_text
    
        # 方法1：按 "// 参考答案" 分割
        if "// 参考答案" in input_text:
            parts = input_text.split("// 参考答案")
            student_part = parts[0].strip()
            reference_part = parts[1].strip() if len(parts) > 1 else student_part
        
            # 移除 "// 学生答案" 标记
            student_code = student_part.replace("// 学生答案", "").strip()
            reference_code = reference_part.strip()
        else:
            # 方法2：如果没有标记，尝试按空行分割
            blocks = input_text.strip().split('\n\n')
            if len(blocks) >= 2:
                student_code = blocks[0].strip()
                reference_code = blocks[1].strip()
            else:
                # 方法3：如果只有一个表达式，用自身作为参考（测试用）
                student_code = input_text.strip()
                reference_code = input_text.strip()
    
        # 提取表达式（去除花括号和return语句）
        def extract_expr(code: str) -> str:
            """提取表达式"""
            # 移除花括号
            code = code.replace('{', ' ').replace('}', ' ')
            # 提取 return 后的内容
            if 'return' in code:
                import re
                match = re.search(r'return\s+([^;]+);', code)
                if match:
                    return match.group(1).strip()
            return code.strip()
    
        student_expr = extract_expr(student_code)
        reference_expr = extract_expr(reference_code)
    
        self.llm_output.setText(f"🔄 正在分析...\n\n学生: {student_expr}\n参考: {reference_expr}")
        self.llm_output.repaint()
        QApplication.processEvents()
    
        # 构建学生AST
        student_tokens, student_errors = self.lexical_analyzer.analyze(student_expr)
        if student_errors:
            self.llm_output.setText(f"❌ 学生代码词法分析失败:\n{student_errors}")
            return
    
        student_parse = self.recursive_parser.parse(student_tokens)
        if not student_parse.success:
            self.llm_output.setText(f"❌ 学生代码解析失败:\n{student_parse.errors}")
            return
    
        # 构建参考AST
        reference_tokens, ref_errors = self.lexical_analyzer.analyze(reference_expr)
        if ref_errors:
            self.llm_output.setText(f"❌ 参考答案词法分析失败:\n{ref_errors}")
            return
    
        reference_parse = self.recursive_parser.parse(reference_tokens)
        if not reference_parse.success:
            self.llm_output.setText(f"❌ 参考答案解析失败:\n{reference_parse.errors}")
            return
    
        # 计算相似度 - 注意参数顺序：学生答案在前，参考答案在后
        report = self.ast_similarity.get_similarity_report(student_parse.ast, reference_parse.ast)
    
        output = f"""
╔═══════════════════════════════════════════════════════════════════════════════╗
║                         AST相似度评分                                           ║
╚═══════════════════════════════════════════════════════════════════════════════╝

📝 学生表达式: {student_expr}
📝 参考表达式: {reference_expr}

{report}
    """
        self.llm_output.setText(output)
        self.statusBar.showMessage("✅ AST相似度评分完成")
    def _run_ai_grading(self, input_text: str):
        """运行AI代码批改"""
        print("=" * 50)
        print(">>> _run_ai_grading 被调用 <<<")
        print(f">>> 输入文本长度: {len(input_text)}")
        print("=" * 50)
        
        # 使用 llm/llm_client.py 中的 FeedbackParser
        from llm.llm_client import FeedbackParser
        
        parser = FeedbackParser(self.llm_client)
        print(f">>> 解析器创建成功, mock_mode={self.llm_client.mock_mode}")
        
        self.llm_output.setText("🔄 正在调用AI批改代码，请稍候...\n\n这可能需要几秒钟时间。")
        self.llm_output.repaint()
        QApplication.processEvents()
        
        try:
            print(">>> 开始调用 evaluate_submission...")
            result = parser.evaluate_submission(input_text)
            print(f">>> 调用完成")
            print(f">>> 评分: {result.get('score')}")
            print(f">>> 解析成功: {result.get('parse_success')}")
            
            output = f"""
╔═══════════════════════════════════════════════════════════════════════════════╗
║                         🤖 AI代码批改结果                                       ║
╚═══════════════════════════════════════════════════════════════════════════════╝

📊 评分: {result.get('score', 'N/A')} / 100
🏷️ 等级: {result.get('level', 'N/A')}

{'─' * 70}

💬 评语:
{result.get('comment', '无')}

{'─' * 70}

💡 改进建议:
{result.get('suggestion', '无')}

{'─' * 70}

📝 发现的问题:
"""
            if result.get('errors'):
                for err in result['errors']:
                    output += f"  • 行 {err.get('line', '?')}: {err.get('type', 'unknown')} - {err.get('msg', '')}\n"
            else:
                output += "  未发现问题，代码质量良好！\n"

            output += f"""
{'─' * 70}

📋 解析状态: {'✅ 成功' if result.get('parse_success') else '❌ 失败'}

{'─' * 70}

🔧 LLM原始输出:
{result.get('raw_output', '')[:800]}{'...' if len(result.get('raw_output', '')) > 800 else ''}
"""
            self.llm_output.setText(output)
            
            if result.get('parse_success'):
                self.statusBar.showMessage("✅ AI代码批改完成")
            else:
                self.statusBar.showMessage("⚠️ AI批改完成但格式解析失败")
            
        except Exception as e:
            import traceback
            error_detail = traceback.format_exc()
            print(f">>> 错误: {e}")
            print(error_detail)
            self.llm_output.setText(f"❌ 批改失败: {str(e)}\n\n详细信息:\n{error_detail}")
            self.statusBar.showMessage("❌ AI批改失败")

    def set_constraint_example(self):
        self.func_combo.setCurrentText("文法约束生成")
        self.llm_input.setPlainText("""
feedback {
    score: 85
    level: medium
    comment {
        text: "代码逻辑清晰"
        suggestion: "增加注释"
    }
    errors [
        error(line: 12, type: runtime, msg: "错误")
    ]
}
""")

    def set_diagnosis_example(self):
        self.func_combo.setCurrentText("语法错误诊断")
        self.llm_input.setPlainText("""
int main() {
    int x = 10;
    if (x > 0 {
        printf("x is positive");
    }
    return 0;
}
""")

    def set_feedback_example(self):
        self.func_combo.setCurrentText("反馈格式解析")
        self.llm_input.setPlainText("""
FEEDBACK {
    SCORE: 92;
    LEVEL: high;
    COMMENT {
        TEXT: "代码结构清晰，算法正确。";
        SUGGESTION: "考虑添加更多的边界测试用例。";
    }
    ERRORS [
        ERROR(line: 15, type: warning, msg: "未使用的变量");
        ERROR(line: 28, type: style, msg: "缩进不一致");
    ]
}
""")

    def set_code_example(self):
        self.func_combo.setCurrentText("AI代码批改")
        self.llm_input.setPlainText("""
def factorial(n):
    if n == 0:
        return 1
    result = 1
    for i in range(1, n+1):
        result = result * i
    return result
""")

    def show_api_config(self):
        """显示API配置对话框"""
        dialog = QDialog(self)
        dialog.setWindowTitle("LLM API配置")
        dialog.setGeometry(400, 300, 500, 300)
        
        layout = QVBoxLayout()
        
        provider_layout = QHBoxLayout()
        provider_layout.addWidget(QLabel("API提供商:"))
        provider_combo = QComboBox()
        provider_combo.addItems(["deepseek", "openai", "qwen", "zhipu"])
        provider_combo.setCurrentText(self.llm_client.config.provider)
        provider_layout.addWidget(provider_combo)
        layout.addLayout(provider_layout)
        
        key_layout = QHBoxLayout()
        key_layout.addWidget(QLabel("API Key:"))
        key_input = QLineEdit()
        key_input.setEchoMode(QLineEdit.Password)
        key_input.setText(self.llm_client.config.api_key)
        key_layout.addWidget(key_input)
        layout.addLayout(key_layout)
        
        url_layout = QHBoxLayout()
        url_layout.addWidget(QLabel("API地址:"))
        url_input = QLineEdit()
        url_input.setText(self.llm_client.config.api_base_url)
        url_layout.addWidget(url_input)
        layout.addLayout(url_layout)
        
        model_layout = QHBoxLayout()
        model_layout.addWidget(QLabel("模型:"))
        model_input = QLineEdit()
        model_input.setText(self.llm_client.config.model)
        model_layout.addWidget(model_input)
        layout.addLayout(model_layout)
        
        btn_layout = QHBoxLayout()
        save_btn = QPushButton("保存")
        cancel_btn = QPushButton("取消")
        test_btn = QPushButton("测试连接")
        
        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(test_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)
        
        status_label = QLabel("")
        layout.addWidget(status_label)
        
        dialog.setLayout(layout)
        
        def save_config():
            self.llm_client.config.provider = provider_combo.currentText()
            self.llm_client.config.api_key = key_input.text()
            self.llm_client.config.api_base_url = url_input.text()
            self.llm_client.config.model = model_input.text()
            os.environ["LLM_API_KEY"] = key_input.text()
            os.environ["LLM_API_BASE_URL"] = url_input.text()
            os.environ["LLM_MODEL"] = model_input.text()
            os.environ["LLM_PROVIDER"] = provider_combo.currentText()
            status_label.setText("✅ 配置已保存")
            self.statusBar.showMessage("API配置已更新")
        
        def test_connection():
            status_label.setText("🔄 测试中...")
            if key_input.text():
                status_label.setText("✅ API Key已配置，可进行测试")
            else:
                status_label.setText("⚠️ 请先配置API Key")
        
        save_btn.clicked.connect(save_config)
        test_btn.clicked.connect(test_connection)
        cancel_btn.clicked.connect(dialog.reject)
        
        dialog.exec_()

    # ==================== 语义分析标签页（选做+5分）====================
    def create_semantic_tab(self):
        """创建语义分析标签页（选做+5分）"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        input_group = QGroupBox("📝 输入代码")
        input_layout = QVBoxLayout()
        self.semantic_input = QPlainTextEdit()
        self.semantic_input.setPlaceholderText(
            "请输入代码进行语义分析，检测：\n\n"
            "1. 变量重定义错误\n"
            "2. 未声明引用错误\n"
            "3. 未初始化使用错误\n\n"
            "示例代码：\n"
            "int x = 10;\n"
            "int x = 20;  // 重定义错误\n"
            "int a;       // 声明未初始化\n"
            "int b = a;   // 使用未初始化的变量\n"
            "y = x + 5;   // 未声明引用错误"
        )
        analyze_btn = QPushButton("🔍 语义分析")
        analyze_btn.clicked.connect(self.run_semantic_analysis)
        input_layout.addWidget(self.semantic_input)
        input_layout.addWidget(analyze_btn)
        input_group.setLayout(input_layout)
        
        output_group = QGroupBox("📊 分析结果")
        output_layout = QVBoxLayout()
        self.semantic_output = QTextEdit()
        self.semantic_output.setReadOnly(True)
        output_layout.addWidget(self.semantic_output)
        output_group.setLayout(output_layout)
        
        layout.addWidget(input_group)
        layout.addWidget(output_group)
        widget.setLayout(layout)
        return widget

    def run_semantic_analysis(self):
        """运行语义分析"""
        code = self.semantic_input.toPlainText().strip()
        if not code:
            QMessageBox.warning(self, "提示", "请输入代码！")
            return
        
        self.statusBar.showMessage("🔍 正在执行语义分析...")
        
        analyzer = SemanticAnalyzer()
        analyzer.analyze_code(code)
        output = analyzer.get_report()
        self.semantic_output.setText(output)
        
        if analyzer.errors:
            self.statusBar.showMessage(f"⚠️ 发现 {len(set(analyzer.errors))} 个语义错误")
        else:
            self.statusBar.showMessage("✅ 语义分析完成，无错误")
