"""Test the structure of the CrewAI multi-agent system without running LLM calls."""
import os
import sys
from unittest.mock import patch, MagicMock
from src.config.config import AgentConfig, TaskConfig, SubgroupConfig, CrewConfig
from src.agents.agent_factory import AgentFactory
from src.tasks.task_factory import TaskFactory
from src.models.crew_manager import CrewManager
from src.utils.config_loader import ConfigLoader
from pathlib import Path

os.environ["OPENAI_API_KEY"] = "sk-mock-api-key-for-testing-only"

sys.modules['crewai.crew'] = MagicMock()
sys.modules['crewai'] = MagicMock()


def test_config_loading():
    """Test loading configuration from a file."""
    config_path = Path(__file__).parent / "example_config.yaml"
    config_data = ConfigLoader.load_config(config_path)
    crew_config = ConfigLoader.create_crew_config(config_data)
    
    print("Configuration loaded successfully!")
    print(f"Crew name: {crew_config.name}")
    print(f"Number of agents: {len(crew_config.agents)}")
    print(f"Number of tasks: {len(crew_config.tasks)}")
    print(f"Number of subgroups: {len(crew_config.subgroups)}")
    
    return crew_config

def test_agent_creation(crew_config):
    """Test creating agents from configuration."""
    agents = AgentFactory.create_agents_from_config(crew_config.agents)
    
    print("\nAgents created successfully!")
    for name, agent in agents.items():
        print(f"Agent: {name}, Model: {agent.config.model}")
    
    return agents

def test_task_creation(crew_config, agents):
    """Test creating tasks from configuration."""
    tasks = TaskFactory.create_tasks_from_config(
        crew_config.tasks,
        {name: agent for name, agent in agents.items()}
    )
    
    print("\nTasks created successfully!")
    for name, task in tasks.items():
        print(f"Task: {name}, Agent: {task.config.agent}")
    
    return tasks

def test_crew_creation(crew_config, agents, tasks):
    """Test creating a crew from configuration."""
    with patch('src.models.crew_manager.CrewManager._create_crew', return_value=MagicMock()):
        crew_manager = CrewManager(crew_config, agents, tasks)
        
        print("\nCrew created successfully!")
        print(f"Crew name: {crew_config.name}")
        
        # Create subgroups
        with patch('src.models.crew_manager.Crew', MagicMock()):
            subgroups = crew_manager.create_all_subgroups()
        
        print("\nSubgroups created successfully!")
        for name in subgroups:
            print(f"Subgroup: {name}")
        
        return crew_manager

if __name__ == "__main__":
    crew_config = test_config_loading()
    agents = test_agent_creation(crew_config)
    tasks = test_task_creation(crew_config, agents)
    crew_manager = test_crew_creation(crew_config, agents, tasks)
    
    print("\nAll tests passed successfully!")
