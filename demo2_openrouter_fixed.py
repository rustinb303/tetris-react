"""Demo script for the CrewAI multi-agent system with direct OpenRouter integration."""
import os
import sys
from typing import Dict, Any, List, Optional
from pathlib import Path

from crewai import Agent, Task, Crew, Process
from langchain.callbacks.manager import CallbackManagerForLLMRun
from langchain.schema import ChatResult, AIMessage, HumanMessage, SystemMessage
from langchain.schema.messages import BaseMessage
from langchain.chat_models.base import BaseChatModel
from openai import OpenAI

from src.utils.env_loader import load_env_vars
from src.utils.openrouter_utils import get_openrouter_model_name

class OpenRouterLLM(BaseChatModel):
    """Custom LLM implementation that uses OpenRouter."""
    
    client: Any = None
    model_name: str = "openai/gpt-4o-mini"
    temperature: float = 0.7
    
    def __init__(
        self,
        provider: str = "openai",
        model: str = "gpt-4o-mini",
        temperature: float = 0.7,
        **kwargs
    ):
        """
        Initialize the OpenRouter LLM.
        
        Args:
            provider: The provider name (openai, anthropic, gemini, grok)
            model: The model name
            temperature: Temperature parameter for the model
        """
        super().__init__(**kwargs)
        
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
        
        self.model_name = get_openrouter_model_name(provider, model)
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

def run_poetry_demo(theme="nature"):
    """
    Run a poetry creation demo with multiple LLM providers through OpenRouter.
    
    Args:
        theme: The theme for the poem
    """
    load_env_vars()
    
    print(f"Running poetry demo with theme: {theme}")
    print("Creating agents with different LLM providers through OpenRouter...")
    
    idea_generator = Agent(
        name="IdeaGenerator",
        role="Creative Thinker",
        goal=f"Generate creative ideas for a poem about {theme}",
        backstory="You are a visionary thinker who excels at generating unique and inspiring ideas.",
        verbose=True,
        llm=OpenRouterLLM(provider="openai", model="gpt-4o-mini")
    )
    
    poet = Agent(
        name="Poet",
        role="Master Poet",
        goal=f"Create a SHORT poem (4 lines max) about {theme} based on the provided idea",
        backstory="You are a skilled poet with a talent for crafting evocative and moving poetry.",
        verbose=True,
        llm=OpenRouterLLM(provider="openai", model="gpt-4o-mini")  # Fallback to OpenAI for now
    )
    
    editor = Agent(
        name="Editor",
        role="Poetry Editor",
        goal=f"Make minor refinements to the short poem about {theme} to improve it",
        backstory="You are a meticulous editor with an eye for detail and a passion for perfection.",
        verbose=True,
        llm=OpenRouterLLM(provider="openai", model="gpt-4o-mini")  # Fallback to OpenAI for now
    )
    
    critic = Agent(
        name="Critic",
        role="Literary Critic",
        goal=f"Provide BRIEF constructive feedback (2-3 sentences max) on the poem about {theme}",
        backstory="You are an insightful critic who can identify strengths and areas for improvement.",
        verbose=True,
        llm=OpenRouterLLM(provider="openai", model="gpt-4o-mini")  # Fallback to OpenAI for now
    )
    
    generate_ideas_task = Task(
        description=f"Generate creative ideas, concepts, and imagery for a poem about {theme}. Be brief and focused.",
        expected_output=f"A list of creative ideas, concepts, and imagery for a poem about {theme}",
        agent=idea_generator
    )
    
    write_poem_task = Task(
        description=f"Write a beautiful poem about {theme} based on the provided ideas. Keep it to 4 lines maximum.",
        expected_output=f"A draft poem about {theme}",
        agent=poet,
        context=[generate_ideas_task]
    )
    
    edit_poem_task = Task(
        description=f"Refine and polish the poem about {theme} to make it more impactful. Maintain the brevity.",
        expected_output=f"A refined poem about {theme}",
        agent=editor,
        context=[write_poem_task]
    )
    
    critique_poem_task = Task(
        description=f"Provide constructive feedback on the poem about {theme}. Keep your feedback to 2-3 sentences.",
        expected_output=f"Constructive feedback on the poem about {theme}",
        agent=critic,
        context=[edit_poem_task]
    )
    
    crew = Crew(
        agents=[idea_generator, poet, editor, critic],
        tasks=[generate_ideas_task, write_poem_task, edit_poem_task, critique_poem_task],
        verbose=True,
        process=Process.sequential
    )
    
    print(f"\nRunning {theme.title()} Poetry Crew...")
    print("This may take a few minutes...\n")
    
    result = crew.kickoff()
    
    print("\n" + "="*50)
    print(f"FINAL RESULT FOR {theme.upper()} POEM:")
    print(result)
    print("="*50)
    
    return result

if __name__ == "__main__":
    if not os.environ.get("OPENROUTER_API_KEY"):
        print("Error: OPENROUTER_API_KEY environment variable not set.")
        print("Please add your OpenRouter API key to the .env file.")
        sys.exit(1)
    
    print("Using OpenRouter for all model providers")
    
    theme = sys.argv[1] if len(sys.argv) > 1 else "nature"
    
    run_poetry_demo(theme)
