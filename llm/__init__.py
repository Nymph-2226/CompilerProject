"""LLM接入模块"""
from .llm_client import LLMClient, LLMConfig
from .grammar_constrained import GrammarConstrainedGenerator, GenerationResult
from .error_diagnosis import ErrorDiagnosis, StructuredErrorInfo
from .feedback_parser import FeedbackParser, ParsedFeedback

__all__ = [
    'LLMClient', 'LLMConfig', 'GrammarConstrainedGenerator',
    'GenerationResult', 'ErrorDiagnosis', 'StructuredErrorInfo',
    'FeedbackParser', 'ParsedFeedback'
]