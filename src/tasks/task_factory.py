"""Factory for creating tasks in the CrewAI multi-agent system."""
from typing import Dict, List, Optional, Any

from crewai.tools.base_tool import BaseTool as Tool

from ..config.config import TaskConfig
from .base_task import BaseTask


class TaskFactory:
    """Factory for creating tasks based on configuration."""
    
    @staticmethod
    def create_task(
        config: TaskConfig, 
        agent: Any,  # BaseAgent.agent
        tools: Optional[List[Tool]] = None
    ) -> BaseTask:
        """
        Create a task with the given configuration.
        
        Args:
            config: The task configuration
            agent: The agent that will perform this task
            tools: Optional list of tools for this task
            
        Returns:
            A BaseTask instance
        """
        return BaseTask(config, agent, tools)
    
    @staticmethod
    def create_tasks_from_config(
        configs: Dict[str, TaskConfig], 
        agents_map: Dict[str, Any],  # Dict[str, BaseAgent.agent]
        tools_map: Optional[Dict[str, List[Tool]]] = None
    ) -> Dict[str, BaseTask]:
        """
        Create multiple tasks from a dictionary of configurations.
        
        Args:
            configs: Dictionary mapping task names to their configurations
            agents_map: Dictionary mapping agent names to their agent instances
            tools_map: Optional dictionary mapping task names to their tools
            
        Returns:
            Dictionary mapping task names to their BaseTask instances
        """
        tools_map = tools_map or {}
        tasks = {}
        
        for name, config in configs.items():
            agent = agents_map[config.agent].agent  # Get the CrewAI agent from our BaseAgent
            tools = tools_map.get(name, [])
            tasks[name] = TaskFactory.create_task(config, agent, tools)
        
        return tasks
