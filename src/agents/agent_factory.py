"""Factory for creating agents in the CrewAI multi-agent system."""
from typing import Dict, List, Optional

from crewai.tools.base_tool import BaseTool as Tool

from ..config.config import AgentConfig
from .base_agent import BaseAgent


class AgentFactory:
    """Factory for creating agents based on configuration."""
    
    @staticmethod
    def create_agent(config: AgentConfig, tools: Optional[List[Tool]] = None) -> BaseAgent:
        """
        Create an agent with the given configuration.
        
        Args:
            config: The agent configuration
            tools: Optional list of tools the agent can use
            
        Returns:
            A BaseAgent instance
        """
        return BaseAgent(config, tools)
    
    @staticmethod
    def create_agents_from_config(
        configs: Dict[str, AgentConfig], 
        tools_map: Optional[Dict[str, List[Tool]]] = None
    ) -> Dict[str, BaseAgent]:
        """
        Create multiple agents from a dictionary of configurations.
        
        Args:
            configs: Dictionary mapping agent names to their configurations
            tools_map: Optional dictionary mapping agent names to their tools
            
        Returns:
            Dictionary mapping agent names to their BaseAgent instances
        """
        tools_map = tools_map or {}
        agents = {}
        
        for name, config in configs.items():
            tools = tools_map.get(name, [])
            agents[name] = AgentFactory.create_agent(config, tools)
        
        return agents
