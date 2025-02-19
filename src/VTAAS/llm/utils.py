from VTAAS.llm.anthropic_client import AnthropicLLMClient
from VTAAS.llm.google_client import GoogleLLMClient
from VTAAS.llm.llm_client import LLMClient, LLMProvider
from VTAAS.llm.mistral_client import MistralLLMClient
from VTAAS.llm.openai_client import OpenAILLMClient
from VTAAS.llm.openrouter_client import OpenRouterLLMClient


def create_llm_client(
    provider: LLMProvider, start_time: float, output_folder: str
) -> LLMClient:
    """Instantiates the correct LLM client based on the provider."""
    match provider:
        case LLMProvider.GOOGLE:
            return GoogleLLMClient(start_time, output_folder)
        case LLMProvider.OPENAI:
            return OpenAILLMClient(start_time, output_folder)
        case LLMProvider.ANTHROPIC:
            return AnthropicLLMClient(start_time, output_folder)
        case LLMProvider.OPENROUTER:
            return OpenRouterLLMClient(start_time, output_folder)
        case LLMProvider.MISTRAL:
            return MistralLLMClient(start_time, output_folder)
