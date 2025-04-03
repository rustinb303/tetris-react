"""Base agent implementation for the CrewAI multi-agent system."""
import os
from typing import List, Optional, Dict, Any, Union

from crewai import Agent
from crewai.tools.base_tool import BaseTool as Tool
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_google_genai import ChatGoogleGenerativeAI
import xai_grok

from ..config.config import AgentConfig
from ..utils.env_loader import load_env_vars, get_api_key
from ..utils.openrouter_utils import get_openrouter_llm, get_openrouter_model_name
from ..utils.crewai_openrouter import OpenRouterChatModel


class BaseAgent:
    """Base agent class that wraps CrewAI's Agent with additional functionality."""
    
    def __init__(self, config: AgentConfig, tools: Optional[List[Tool]] = None):
        """
        Initialize a base agent with the given configuration.
        
        Args:
            config: The agent configuration
            tools: Optional list of tools the agent can use
        """
        load_env_vars()
        
        self.config = config
        self.tools = tools or []
        self._agent = self._create_agent()
    
    def _get_llm(self, model_config: str) -> Any:
        """
        Create an LLM instance based on the model configuration.
        
        Args:
            model_config: The model configuration string (e.g., "openai:gpt-4", "anthropic:claude-3-sonnet")
            
        Returns:
            An LLM instance
        """
        if ":" not in model_config:
            return model_config
        
        openrouter_api_key = os.environ.get("OPENROUTER_API_KEY")
        
        if openrouter_api_key:
            try:
                print(f"Using OpenRouter for {model_config}")
                return OpenRouterChatModel(
                    model=model_config,
                    temperature=self.config.temperature
                )
            except Exception as e:
                print(f"Error initializing OpenRouter LLM: {e}")
                print("Falling back to direct provider API...")
        
        provider, model = model_config.split(":", 1)
        provider = provider.lower()
        
        if provider == "openai":
            return ChatOpenAI(
                model=model,
                temperature=self.config.temperature,
                api_key=get_api_key("openai")
            )
        elif provider == "anthropic":
            print("Note: Using OpenAI as a fallback for Anthropic model")
            return ChatOpenAI(
                model="gpt-4o-mini",
                temperature=self.config.temperature,
                api_key=get_api_key("openai")
            )
        elif provider in ["google", "gemini"]:
            print("Note: Using OpenAI as a fallback for Gemini model")
            return ChatOpenAI(
                model="gpt-4o-mini",
                temperature=self.config.temperature,
                api_key=get_api_key("openai")
            )
        elif provider in ["xai", "grok"]:
            print("Note: Using OpenAI as a fallback for Grok model")
            return ChatOpenAI(
                model="gpt-4o-mini",
                temperature=self.config.temperature,
                api_key=get_api_key("openai")
            )
        else:
            return model_config
    
    def _create_agent(self) -> Agent:
        """Create a CrewAI agent based on the configuration."""
        llm = self._get_llm(self.config.model)
        
        return Agent(
            name=self.config.name,
            role=self.config.role,
            goal=self.config.goal,
            backstory=self.config.backstory,
            verbose=self.config.verbose,
            allow_delegation=self.config.allow_delegation,
            llm=llm,
            max_iterations=self.config.max_iterations,
            max_rpm=self.config.max_rpm,
            temperature=self.config.temperature,
            system_prompt=self.config.system_prompt,
            human_input_mode=self.config.human_input_mode,
            tools=self.tools
        )
    
    @property
    def agent(self) -> Agent:
        """Get the underlying CrewAI agent."""
        return self._agent
    
    def update_config(self, **kwargs) -> None:
        """
        Update the agent's configuration.
        
        Args:
            **kwargs: Configuration parameters to update
        """
        for key, value in kwargs.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)
        
        self._agent = self._create_agent()
