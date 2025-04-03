"""Configuration module for the CrewAI multi-agent system."""
from typing import Dict, List, Optional, Union, Any
from pydantic import BaseModel, Field


class AgentConfig(BaseModel):
    """Configuration for an individual agent."""
    name: str
    role: str
    goal: str
    backstory: str
    verbose: bool = True
    allow_delegation: bool = False
    model: str = "gpt-4"  # Can use provider:model format like "openai:gpt-4", "anthropic:claude-3-sonnet", "gemini:gemini-1.5-pro", "grok:grok-2"
    max_iterations: int = 15
    max_rpm: Optional[int] = None
    temperature: float = 0.7
    system_prompt: Optional[str] = None
    human_input_mode: str = "NEVER"
    tools: List[str] = Field(default_factory=list)


class SubgroupConfig(BaseModel):
    """Configuration for a subgroup of agents."""
    name: str
    agents: List[str]
    tasks: List[str]
    process: str = "sequential"  # sequential, hierarchical


class TaskConfig(BaseModel):
    """Configuration for a task."""
    name: str
    description: str
    expected_output: str
    agent: str
    tools: List[str] = Field(default_factory=list)
    context: Optional[str] = None
    async_execution: bool = False


class CrewConfig(BaseModel):
    """Configuration for the entire crew."""
    name: str
    description: str
    agents: Dict[str, AgentConfig]
    tasks: Dict[str, TaskConfig]
    subgroups: Dict[str, SubgroupConfig] = Field(default_factory=dict)
    process: str = "sequential"  # sequential, hierarchical
    verbose: bool = True
    memory: bool = True
    cache: bool = False
    step_callback: Any = False
