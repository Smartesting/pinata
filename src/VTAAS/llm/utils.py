from VTAAS.llm.anthropic_client import AnthropicLLMClient
from VTAAS.llm.google_client import GoogleLLMClient
from VTAAS.llm.llm_client import LLMClient, LLMProviders
from VTAAS.llm.openai_client import OpenAILLMClient


def create_llm_client(provider: LLMProviders, start_time: float) -> LLMClient:
    """Instantiates the correct LLM client based on the provider."""
    match provider:
        case LLMProviders.GOOGLE:
            return GoogleLLMClient(start_time)
        case LLMProviders.OPENAI:
            return OpenAILLMClient(start_time)
        case LLMProviders.ANTHROPIC:
            return AnthropicLLMClient(start_time)
