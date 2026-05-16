# llm/llm_client.py
import os
import json
import time
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field

# 尝试导入requests
try:
    import requests
except ImportError:
    requests = None
    print("警告: requests库未安装，请运行: pip install requests")


@dataclass
class LLMConfig:
    """LLM配置"""
    api_key: str = ""
    api_base_url: str = "https://api.deepseek.com/v1"
    model: str = "deepseek-chat"
    provider: str = "deepseek"  # deepseek, openai, qwen, zhipu
    temperature: float = 0.3
    max_tokens: int = 2000


@dataclass
class LLMResponse:
    """LLM响应"""
    success: bool
    content: str = ""
    raw_response: Any = None
    error: str = ""
    usage: Dict[str, int] = field(default_factory=dict)


class LLMClient:
    """
    LLM API客户端
    支持多个提供商：DeepSeek, OpenAI, 通义千问, 智谱
    """

    def __init__(self, config: Optional[LLMConfig] = None, mock_mode: bool = False):
        self.mock_mode = mock_mode
        if config:
            self.config = config
        else:
            self.config = self._load_config_from_env()

    def _load_config_from_env(self) -> LLMConfig:
        """从环境变量加载配置"""
        return LLMConfig(
            api_key=os.environ.get("LLM_API_KEY", ""),
            api_base_url=os.environ.get("LLM_API_BASE_URL", "https://api.deepseek.com/v1"),
            model=os.environ.get("LLM_MODEL", "deepseek-chat"),
            provider=os.environ.get("LLM_PROVIDER", "deepseek")
        )

    def is_available(self) -> bool:
        """检查API是否可用"""
        if self.mock_mode:
            return True
        return bool(self.config.api_key) and requests is not None

    def call(self, system_prompt: str, user_prompt: str, temperature: float = None) -> str:
        """调用LLM API"""
        if self.mock_mode:
            return self._mock_generate(system_prompt, user_prompt)

        if not self.is_available():
            raise Exception("API不可用，请检查配置或启用mock_mode")

        headers = {
            "Authorization": f"Bearer {self.config.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": self.config.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": temperature or self.config.temperature,
            "max_tokens": self.config.max_tokens,
        }

        url = f"{self.config.api_base_url}/chat/completions"

        try:
            response = requests.post(url, headers=headers, json=payload, timeout=30)
            response.raise_for_status()
            result = response.json()
            return result["choices"][0]["message"]["content"]
        except Exception as e:
            raise Exception(f"LLM API调用失败: {e}")

    def call_with_retry(self, system_prompt: str, user_prompt: str, max_retries: int = 2) -> Tuple[str, bool]:
        """带重试的API调用"""
        for attempt in range(max_retries):
            try:
                result = self.call(system_prompt, user_prompt)
                return result, True
            except Exception as e:
                print(f"API调用失败 (尝试 {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(2)
        return "", False

    def _mock_generate(self, system_prompt: str, user_prompt: str) -> str:
        """模拟生成响应"""
        if "批改" in user_prompt or "代码" in user_prompt:
            return '''FEEDBACK {
    SCORE: 85;
    LEVEL: medium;
    COMMENT {
        TEXT: "代码逻辑清晰，但可以增加输入验证";
        SUGGESTION: "建议添加对边界条件的检查";
    }
    ERRORS [
        ERROR(line:5, type:logic, msg:"未处理负数输入");
    ]
}'''
        else:
            return '''FEEDBACK {
    SCORE: 90;
    LEVEL: high;
    COMMENT {
        TEXT: "代码结构良好，算法正确";
        SUGGESTION: "可以考虑进一步优化性能";
    }
    ERRORS []
}'''

    def get_config_info(self) -> str:
        """获取配置信息"""
        return f"""
LLM配置信息:
  提供商: {self.config.provider}
  模型: {self.config.model}
  API地址: {self.config.api_base_url}
  API Key: {'已配置' if self.config.api_key else '未配置'}
  模拟模式: {'是' if self.mock_mode else '否'}
"""


# 反馈解析器（用于解析LLM输出）
class FeedbackParser:
    """反馈格式解析器"""

    def __init__(self, llm_client: LLMClient = None):
        self.llm_client = llm_client or LLMClient(mock_mode=True)
        self.stats = {
            "total_attempts": 0,
            "parse_success": 0,
            "retry_success": 0,
            "retry_failed": 0
        }

    def parse_feedback_text(self, text: str) -> Dict:
        """解析反馈文本"""
        result = {
            "score": None,
            "level": None,
            "comment": None,
            "suggestion": None,
            "errors": [],
            "parse_success": False
        }

        try:
            # 查找FEEDBACK块
            start_idx = text.find("FEEDBACK")
            if start_idx == -1:
                return result

            # 找到匹配的括号
            brace_count = 0
            end_idx = start_idx
            found_feedback = False

            for i, ch in enumerate(text[start_idx:], start_idx):
                if ch == '{':
                    brace_count += 1
                    found_feedback = True
                elif ch == '}':
                    brace_count -= 1
                    if brace_count == 0 and found_feedback:
                        end_idx = i + 1
                        break

            if end_idx <= start_idx:
                return result

            feedback_text = text[start_idx:end_idx]

            # 提取各个字段
            import re

            # 提取分数
            score_match = re.search(r'SCORE\s*:\s*(\d+)\s*;', feedback_text)
            if score_match:
                result["score"] = int(score_match.group(1))

            # 提取等级
            level_match = re.search(r'LEVEL\s*:\s*(\w+)\s*;', feedback_text)
            if level_match:
                result["level"] = level_match.group(1)

            # 提取评语
            text_match = re.search(r'TEXT\s*:\s*"([^"]*)"\s*;', feedback_text)
            if text_match:
                result["comment"] = text_match.group(1)

            # 提取建议
            sug_match = re.search(r'SUGGESTION\s*:\s*"([^"]*)"\s*;', feedback_text)
            if sug_match:
                result["suggestion"] = sug_match.group(1)

            # 提取错误
            error_matches = re.findall(r'ERROR\s*\(\s*line\s*:\s*(\d+)\s*,\s*type\s*:\s*(\w+)\s*,\s*msg\s*:\s*"([^"]*)"\s*\)', feedback_text)
            for match in error_matches:
                result["errors"].append({
                    "line": int(match[0]),
                    "type": match[1],
                    "msg": match[2]
                })

            result["parse_success"] = True

        except Exception as e:
            print(f"解析错误: {e}")

        return result

    def evaluate_submission(self, code_snippet: str) -> Dict:
        """评估提交的代码"""
        self.stats["total_attempts"] += 1

        system_prompt = """你是一个编程课程的AI助教，专门负责批改学生的编程作业。

你必须严格按照以下格式输出批改反馈：

FEEDBACK {
    SCORE: <0-100的数字>;
    LEVEL: <low/medium/high>;
    COMMENT {
        TEXT: "<评语>";
        SUGGESTION: "<建议>";
    }
    ERRORS [
        ERROR(line:<行号>, type:<syntax/runtime/logic>, msg:"<描述>");
    ]
}"""

        user_prompt = f'请批改以下学生代码，并按照指定格式输出反馈：\n\n```python\n{code_snippet}\n```\n\n请分析代码的正确性、效率和代码质量。'

        llm_output, success = self.llm_client.call_with_retry(system_prompt, user_prompt)

        if not success:
            return {
                "score": None,
                "level": None,
                "comment": "LLM API调用失败",
                "suggestion": "请检查网络连接和API配置",
                "errors": [],
                "parse_success": False,
                "raw_output": ""
            }

        result = self.parse_feedback_text(llm_output)
        result["raw_output"] = llm_output

        if result["parse_success"]:
            self.stats["parse_success"] += 1

        return result

    def get_stats(self) -> Dict:
        """获取统计信息"""
        success_rate = self.stats["parse_success"] / self.stats["total_attempts"] if self.stats["total_attempts"] > 0 else 0
        return {**self.stats, "success_rate": success_rate}