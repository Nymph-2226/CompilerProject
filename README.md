# 编译原理AI助学系统 - LLM增强的词法-语法分析综合平台

## 项目简介

本项目是编译原理课程的综合实验作业，实现了一个面向教育场景的AI助学系统。系统集成了词法分析、语法分析、语义分析等编译技术，并结合大语言模型（LLM）提供智能辅助功能。

### 主要功能

1. **DFA词法分析器** - 基于确定有限自动机的词法分析
2. **文法分析模块** - Chomsky文法分类、句型判定、句柄定位、推导归约
3. **LL(1)语法分析器** - 自动计算FIRST/FOLLOW集、构造预测分析表、检测LL(1)冲突
4. **递归下降解析器** - 生成抽象语法树(AST)
5. **LLM接入层** - 调用大模型API进行代码批改和错误诊断
6. **语义分析器** - 变量重定义、未声明引用、未初始化使用检测
7. **AST相似度评分** - 基于树编辑距离的语法树比较
8. **智能问答系统** - 编译原理知识库问答

## 项目结构
CompilerProject/
├── lexer/ # 词法分析模块
│ ├── init.py
│ ├── token.py # Token类型定义
│ ├── dfa_lexer.py # DFA词法分析器
│ └── lexical_analyzer.py # 词法分析器接口
│
├── grammar/ # 文法模块
│ ├── init.py
│ ├── chomsky_classifier.py # 乔姆斯基文法判定
│ ├── improved_grammar.py # 上下文无关文法类
│ └── handle_analyzer.py # 句柄分析器
│
├── parser/ # 语法分析模块
│ ├── init.py
│ ├── ast_node.py # AST节点定义
│ ├── ast_similarity.py # AST相似度评分
│ ├── error_recovery.py # Panic-mode错误恢复
│ ├── ll1_analyzer.py # LL(1)分析器
│ └── recursive_descent.py # 递归下降解析器
│
├── llm/ # LLM接入模块
│ ├── init.py
│ ├── llm_client.py # LLM API客户端
│ ├── grammar_constrained.py # 文法约束生成
│ └── error_diagnosis.py # 教学型错误诊断
│
├── semantic/ # 语义分析模块（选做）
│ ├── init.py
│ └── symbol_table.py # 符号表与语义分析
│
├── ui/ # UI模块
│ ├── init.py
│ └── main_window.py # 主窗口
│
├── knowledge_base.py # 知识库
├── question_grammar.py # 问题文法解析
├── evaluate.py # LLM端到端评估
├── parser.py # 反馈格式解析器
├── lexer.py # 反馈格式词法分析
├── my_token.py # Token定义
├── ast_node.py # AST节点
├── main.py # 程序入口
├── test_constraint_experiment.py # 约束生成对照实验
├── test_semantic.py # 语义分析测试
├── requirements.txt # 依赖文件
└── README.md # 项目说明

## 环境要求

- Python 3.8+
- PyQt5
- requests（可选，用于LLM API调用）

## 安装与运行

### 1. 克隆或下载项目
cd E:\PycharmProjects\CompilerProject
2. 创建虚拟环境（推荐）
bash
python -m venv venv
venv\Scripts\activate
3. 安装依赖
bash
pip install PyQt5 requests
4. 运行程序
python main.py

功能使用说明
智能问答
在"📚 智能问答"标签页输入编译原理相关问题，系统会从知识库中检索答案。

文法分析
查看文法定义和产生式,输入符号串判定是否为句型/句子,符号分类（终结符/非终结符）

词法分析
基于DFA的词法分析器，支持：关键字识别（if, else, while, int, float等）

标识符识别
常量识别（整数、浮点数、科学计数法、十六进制）,运算符识别（最长匹配原则）,界符识别,注释处理（// 和 /* */）

LLM增强功能
文法约束生成：对LLM输出进行格式约束和修正
语法错误诊断：生成面向初学者的错误解释
反馈格式解析：解析LLM返回的结构化反馈
AST相似度评分：比较学生答案与参考答案的语法树
AI代码批改：调用LLM批改学生代码

LL(1)分析
选择预设文法（反馈格式文法/算术表达式文法）,自定义文法输入,自动计算FIRST集、FOLLOW集,构造预测分析表,检测LL(1)冲突

语义分析（选做）
检测：
变量重定义、未声明引用、未初始化使用、作用域错误、除零错误、if条件中误用赋值

LLM API配置
方式一：环境变量
# Windows PowerShell
$env:LLM_API_KEY = "your-api-key"
$env:LLM_API_BASE_URL = "https://api.deepseek.com/v1"
$env:LLM_MODEL = "deepseek-chat"
$env:LLM_PROVIDER = "deepseek"

方式二：程序界面配置
点击LLM增强功能标签页中的"⚙️ API配置"按钮进行配置。

方式三：模拟模式
如果未配置API Key，程序会自动使用模拟模式，返回示例数据。

测试
测试LLM连接
python test_api.py

测试语义分析
python test_semantic.py

测试约束生成对照实验
python test_constraint_experiment.py

任务完成情况
任务	状态
① 词法层 - DFA词法分析器	✅ 完成
② 文法层 - Chomsky文法判定	✅ 完成
② 文法层 - 句型/句子判定	✅ 完成
② 文法层 - 句柄定位	✅ 完成
② 文法层 - 最左推导/归约	✅ 完成
② 文法层 - 文本式语法树	✅ 完成
③ 语法层 - LL(1)模块	✅ 完成
③ 语法层 - 递归下降Parser	✅ 完成
④ LLM接入层	✅ 完成
新增① - 文法约束生成	✅ 完成
新增② - 教学型语法错误诊断	✅ 完成
新增③ - AST相似度评分	✅ 完成
新增④ - 语义分析预研（选做）	✅ 完成

常见问题
Q: 程序启动后没有窗口？
A: 检查PyQt5是否正确安装：pip install PyQt5

Q: AI代码批改没有反应？
A:
检查是否正确选择了"AI代码批改"功能
检查是否输入了代码
查看终端是否有错误信息

Q: LLM API调用失败？
A:
检查API Key是否正确配置
检查网络连接
可先使用模拟模式测试

Q: 语义分析未检测到未初始化变量？
A: 确保代码中变量先声明后使用，例如：
int a;        // 声明但未初始化
int b = a;    // 这里会报未初始化错误

作者信息
name:Nymph-2226

参考资料
《编译原理》（龙书）
DeepSeek API文档：https://platform.deepseek.com/docs
PyQt5文档：https://www.riverbankcomputing.com/static/Docs/PyQt5/