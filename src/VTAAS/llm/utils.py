from VTAAS.llm.google_client import GoogleLLMClient
from VTAAS.llm.llm_client import LLMClient, LLMProviders
from VTAAS.llm.openai_client import OpenAILLMClient


def create_llm_client(provider: LLMProviders) -> LLMClient:
    """Instantiates the correct LLM client based on the provider."""
    match provider:
        case LLMProviders.GOOGLE:
            return GoogleLLMClient()
        case LLMProviders.OPENAI:
            return OpenAILLMClient()
        # case LLMProviders.ANTHROPIC:
        #     return AnthropicLLMClient()
        case _:
            raise ValueError(f"Unknown LLM provider: {provider}")
