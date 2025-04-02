"""Base task implementation for the CrewAI multi-agent system."""
from typing import List, Optional, Any, Dict

from crewai import Task
from crewai.tools.base_tool import BaseTool as Tool

from ..config.config import TaskConfig


class BaseTask:
    """Base task class that wraps CrewAI's Task with additional functionality."""
    
    def __init__(
        self, 
        config: TaskConfig, 
        agent: Any,  # BaseAgent.agent
        tools: Optional[List[Tool]] = None
    ):
        """
        Initialize a base task with the given configuration.
        
        Args:
            config: The task configuration
            agent: The agent that will perform this task
            tools: Optional list of tools for this task
        """
        self.config = config
        self.agent = agent
        self.tools = tools or []
        self._task = self._create_task()
    
    def _create_task(self) -> Task:
        """Create a CrewAI task based on the configuration."""
        return Task(
            description=self.config.description,
            expected_output=self.config.expected_output,
            agent=self.agent,
            tools=self.tools,
            context=self.config.context,
            async_execution=self.config.async_execution
        )
    
    @property
    def task(self) -> Task:
        """Get the underlying CrewAI task."""
        return self._task
    
    def update_config(self, **kwargs) -> None:
        """
        Update the task's configuration.
        
        Args:
            **kwargs: Configuration parameters to update
        """
        for key, value in kwargs.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)
        
        self._task = self._create_task()
