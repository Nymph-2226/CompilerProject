# 编译原理AI助学系统 - LLM增强的词法-语法分析综合平台

## 项目简介

本项目是编译原理课程的综合实验作业，实现了一个面向教育场景的AI助学系统。系统集成了词法分析、语法分析、语义分析等编译技术，并结合大语言模型（LLM）提供智能辅助功能。

### 主要功能

| 功能模块 | 说明 |
|----------|------|
| DFA词法分析器 | 基于确定有限自动机的词法分析 |
| 文法分析模块 | Chomsky文法分类、句型判定、句柄定位、推导归约 |
| LL(1)语法分析器 | 自动计算FIRST/FOLLOW集、构造预测分析表、检测LL(1)冲突 |
| 递归下降解析器 | 生成抽象语法树(AST) |
| LLM接入层 | 调用大模型API进行代码批改和错误诊断 |
| 语义分析器 | 变量重定义、未声明引用、未初始化使用检测 |
| AST相似度评分 | 基于树编辑距离的语法树比较 |
| 智能问答系统 | 编译原理知识库问答 |

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
│ ├── ll1_parser.py # LL(1)预测分析器
│ └── recursive_descent.py # 递归下降解析器
│
├── llm/ # LLM接入模块
│ ├── init.py
│ ├── llm_client.py # LLM API客户端
│ ├── grammar_constrained.py # 文法约束生成
│ ├── error_diagnosis.py # 教学型错误诊断
│ └── feedback_parser.py # 反馈格式解析器
│
├── semantic/ # 语义分析模块
│ ├── init.py
│ └── symbol_table.py # 符号表与语义分析
│
├── ui/ # UI模块
│ ├── init.py
│ └── main_window.py # 主窗口
│
├── knowledge_base.py # 知识库
├── question_grammar.py # 智能问答引擎
├── main.py # 程序入口
├── requirements.txt # 依赖文件
└── README.md # 项目说明

## 环境要求
- Python 3.8+
- PyQt5 >= 5.15.0
- requests >= 2.28.0（可选，用于LLM API调用）

## 安装与运行
1. 克隆或下载项目
git clone https://github.com/Nymph-2226/CompilerProject.git
cd CompilerProject

2. 创建虚拟环境（推荐）
python -m venv venv
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate

3. 安装依赖
pip install -r requirements.txt
或手动安装：
pip install PyQt5 requests

4. 运行程序
python main.py

功能使用说明
📚 智能问答
在"智能问答"标签页输入编译原理相关问题，系统会从知识库中检索答案。

支持的问题类型：
什么是编译器？
解释一下DFA
什么是词法分析？
解释LL(1)文法

📖 文法分析
查看文法定义和产生式
输入符号串判定是否为句型/句子
符号分类（终结符/非终结符）

✏️ 词法分析
基于DFA的词法分析器，支持：
关键字识别（if, else, while, int, float, return等）、标识符识别、常量识别（整数、浮点数、科学计数法、十六进制）、运算符识别（最长匹配原则）、界符识别、注释处理（// 和 /* */）

📊 LL(1)分析
选择预设文法（反馈格式文法/算术表达式文法）
自定义文法输入
自动计算FIRST集、FOLLOW集
构造预测分析表
检测LL(1)冲突

🤖 LLM增强功能
功能	说明
文法约束生成	对LLM输出进行格式约束和修正
语法错误诊断	生成面向初学者的错误解释
反馈格式解析	解析LLM返回的结构化反馈
AST相似度评分	比较学生答案与参考答案的语法树
AI代码批改	调用LLM批改学生代码

🔍 语义分析
检测以下语义错误：
变量重定义/未声明引用/未初始化使用

LLM API配置
方式一：环境变量
# Windows PowerShell
$env:LLM_API_KEY = "your-api-key"
$env:LLM_API_BASE_URL = "https://api.deepseek.com/v1"
$env:LLM_MODEL = "deepseek-chat"
$env:LLM_PROVIDER = "deepseek"

# Linux/Mac
export LLM_API_KEY="your-api-key"
export LLM_API_BASE_URL="https://api.deepseek.com/v1"
export LLM_MODEL="deepseek-chat"
export LLM_PROVIDER="deepseek"

方式二：程序界面配置
点击LLM增强功能标签页中的"⚙️ API配置"按钮进行配置。

方式三：模拟模式
如果未配置API Key，程序会自动使用模拟模式，返回示例数据。

AST相似度评分示例
# 学生答案
a + b * c
# 参考答案
(a + b) * c
# 输出相似度：约80%

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
新增④ - 语义分析预研（选做+5分）	✅ 完成

常见问题:
Q: 程序启动后没有窗口？
pip install PyQt5

Q: AI代码批改没有反应？
检查是否正确选择了"AI代码批改"功能
检查是否输入了代码
查看终端是否有错误信息

Q: LLM API调用失败？
检查API Key是否正确配置
检查网络连接
可先使用模拟模式测试

Q: libpng警告是怎么回事？
这些警告不影响程序功能，可以安全忽略。如需消除：
import os
os.environ["QT_LOGGING_RULES"] = "qt.qpa.gl=false"

Q: 语义分析未检测到未初始化变量？
确保代码中变量先声明后使用，例如：
int a;        // 声明但未初始化
int b = a;    // 这里会报未初始化错误

Q: AST相似度总是100%？
确保输入格式正确：
// 学生答案
a + b * c
// 参考答案
(a + b) * c

版本历史
版本	日期	更新内容
v1.0	2026-04	初始版本，完成基础功能
v1.1	2026-05	修复LLM约束生成、AST相似度评分、语义分析等模块

作者
Nymph-2226

参考资料
《编译原理》（龙书）
DeepSeek API文档
PyQt5文档