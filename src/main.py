"""Main module for the CrewAI multi-agent system."""
from typing import Dict, List, Optional, Any, Union
import argparse
from pathlib import Path

from .config.config import CrewConfig
from .agents.agent_factory import AgentFactory
from .tasks.task_factory import TaskFactory
from .models.crew_manager import CrewManager
from .utils.config_loader import ConfigLoader
from .utils.tool_registry import ToolRegistry


def setup_crew_from_config(config_path: Union[str, Path]) -> CrewManager:
    """
    Set up a crew from a configuration file.
    
    Args:
        config_path: Path to the configuration file
        
    Returns:
        CrewManager instance
    """
    config_data = ConfigLoader.load_config(config_path)
    crew_config = ConfigLoader.create_crew_config(config_data)
    
    tool_registry = ToolRegistry()
    
    agents = AgentFactory.create_agents_from_config(crew_config.agents)
    
    agent_tools_map = {}
    for name, agent_config in crew_config.agents.items():
        agent_tools_map[name] = tool_registry.get_tools(agent_config.tools)
    
    tasks = TaskFactory.create_tasks_from_config(
        crew_config.tasks,
        {name: agent for name, agent in agents.items()}
    )
    
    task_tools_map = {}
    for name, task_config in crew_config.tasks.items():
        task_tools_map[name] = tool_registry.get_tools(task_config.tools)
    
    crew_manager = CrewManager(crew_config, agents, tasks)
    
    crew_manager.create_all_subgroups()
    
    return crew_manager


def main():
    """Main entry point for the application."""
    parser = argparse.ArgumentParser(description='CrewAI Multi-Agent System')
    parser.add_argument('--config', type=str, required=True, help='Path to the configuration file')
    args = parser.parse_args()
    
    crew_manager = setup_crew_from_config(args.config)
    
    result = crew_manager.run()
    print(f"Crew result: {result}")


if __name__ == '__main__':
    main()
