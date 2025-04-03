"""Utility functions for OpenRouter integration."""
import os
from typing import Dict, Any, Optional

from langchain.chat_models.base import BaseChatModel
from langchain_openai import ChatOpenAI

def get_openrouter_llm(model: str, temperature: float = 0.7) -> BaseChatModel:
    """
    Get a language model through OpenRouter.
    
    Args:
        model: The model name (e.g., 'openai/gpt-4o', 'anthropic/claude-3-opus', 'google/gemini-pro')
        temperature: The temperature parameter for the model
        
    Returns:
        A language model instance configured to use OpenRouter
    """
    openrouter_api_key = os.getenv("OPENROUTER_API_KEY")
    
    if not openrouter_api_key:
        raise ValueError("OPENROUTER_API_KEY environment variable not set")
    
    return ChatOpenAI(
        model=model,
        temperature=temperature,
        openai_api_key=openrouter_api_key,
        openai_api_base="https://openrouter.ai/api/v1",
        headers={
            "HTTP-Referer": "https://github.com/mattxlarson/crewai-multi-agent",  # Replace with your site URL
            "X-Title": "CrewAI Multi-Agent Project"  # Replace with your app name
        }
    )

def get_openrouter_model_name(provider: str, model: str) -> str:
    """
    Convert a provider and model name to the OpenRouter format.
    
    Args:
        provider: The provider name (openai, anthropic, gemini, grok)
        model: The model name
        
    Returns:
        The model name in OpenRouter format
    """
    provider = provider.lower()
    
    if provider == "openai":
        return f"openai/{model}"
    elif provider == "anthropic":
        return f"anthropic/{model}"
    elif provider == "gemini":
        if model.startswith("google/"):
            model = model[7:]
        return f"google/{model}"
    elif provider == "grok":
        return f"xai/{model}"
    else:
        return f"openai/{model}"

OPENROUTER_MODELS = {
    "openai": [
        "gpt-4o",
        "gpt-4o-mini",
        "gpt-4-turbo",
        "gpt-4",
        "gpt-3.5-turbo"
    ],
    "anthropic": [
        "claude-3-opus-20240229",
        "claude-3-sonnet-20240229",
        "claude-3-haiku-20240307",
        "claude-3-7-sonnet-20250219"
    ],
    "google": [
        "gemini-pro",
        "gemini-1.5-pro",
        "gemini-2.0-flash",
        "gemini-2.0-pro"
    ],
    "xai": [
        "grok-1",
        "grok-2"
    ]
}
