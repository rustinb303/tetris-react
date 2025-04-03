"""Custom LLM implementation for CrewAI that uses OpenRouter for all models."""
import os
from typing import Any, Dict, List, Optional, Union

from langchain.callbacks.manager import CallbackManagerForLLMRun
from langchain.chat_models.base import BaseChatModel
from langchain.schema import ChatResult, AIMessage, HumanMessage, SystemMessage
from langchain.schema.messages import BaseMessage
from openai import OpenAI

from .env_loader import load_env_vars
from .openrouter_utils import get_openrouter_model_name


class OpenRouterChatModel(BaseChatModel):
    """Custom LLM implementation that uses OpenRouter for all models."""
    
    client: Any = None
    model_name: str = "openai/gpt-4o-mini"
    temperature: float = 0.7
    
    def __init__(
        self,
        model: str = "openai:gpt-4o-mini",
        temperature: float = 0.7,
        **kwargs
    ):
        """
        Initialize the OpenRouter chat model.
        
        Args:
            model: Model identifier in format "provider:model_name"
            temperature: Temperature parameter for the model
        """
        super().__init__(**kwargs)
        
        load_env_vars()
        
        openrouter_api_key = os.getenv("OPENROUTER_API_KEY")
        if not openrouter_api_key:
            raise ValueError("OPENROUTER_API_KEY environment variable not set")
        
        self.client = OpenAI(
            api_key=openrouter_api_key,
            base_url="https://openrouter.ai/api/v1",
            default_headers={
                "HTTP-Referer": "https://github.com/mattxlarson/crewai-multi-agent",
                "X-Title": "CrewAI Multi-Agent Project"
            }
        )
        
        if ":" in model:
            provider, model_name = model.split(":", 1)
            self.model_name = get_openrouter_model_name(provider, model_name)
        else:
            self.model_name = model
        
        self.temperature = temperature
    
    def _generate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs
    ) -> ChatResult:
        """Generate a response from the model."""
        openai_messages = []
        
        for message in messages:
            if isinstance(message, SystemMessage):
                openai_messages.append({"role": "system", "content": message.content})
            elif isinstance(message, HumanMessage):
                openai_messages.append({"role": "user", "content": message.content})
            elif isinstance(message, AIMessage):
                openai_messages.append({"role": "assistant", "content": message.content})
            else:
                openai_messages.append({"role": "user", "content": str(message.content)})
        
        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=openai_messages,
            temperature=self.temperature,
            stop=stop,
            **kwargs
        )
        
        message = AIMessage(content=response.choices[0].message.content)
        
        return ChatResult(generations=[{"message": message}])
    
    @property
    def _llm_type(self) -> str:
        """Return the type of LLM."""
        return "openrouter"
