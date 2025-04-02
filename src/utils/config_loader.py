"""Configuration loader for the CrewAI multi-agent system."""
import json
import yaml
from typing import Dict, Any, Union
from pathlib import Path

from ..config.config import CrewConfig, AgentConfig, TaskConfig, SubgroupConfig


class ConfigLoader:
    """Loader for configuration files."""
    
    @staticmethod
    def load_yaml(file_path: Union[str, Path]) -> Dict[str, Any]:
        """
        Load a YAML configuration file.
        
        Args:
            file_path: Path to the YAML file
            
        Returns:
            Dictionary containing the configuration
        """
        with open(file_path, 'r') as file:
            return yaml.safe_load(file)
    
    @staticmethod
    def load_json(file_path: Union[str, Path]) -> Dict[str, Any]:
        """
        Load a JSON configuration file.
        
        Args:
            file_path: Path to the JSON file
            
        Returns:
            Dictionary containing the configuration
        """
        with open(file_path, 'r') as file:
            return json.load(file)
    
    @staticmethod
    def load_config(file_path: Union[str, Path]) -> Dict[str, Any]:
        """
        Load a configuration file (YAML or JSON).
        
        Args:
            file_path: Path to the configuration file
            
        Returns:
            Dictionary containing the configuration
        """
        file_path = Path(file_path)
        if file_path.suffix.lower() in ['.yaml', '.yml']:
            return ConfigLoader.load_yaml(file_path)
        elif file_path.suffix.lower() == '.json':
            return ConfigLoader.load_json(file_path)
        else:
            raise ValueError(f"Unsupported file format: {file_path.suffix}")
    
    @staticmethod
    def create_crew_config(config_data: Dict[str, Any]) -> CrewConfig:
        """
        Create a CrewConfig from a dictionary.
        
        Args:
            config_data: Dictionary containing the configuration
            
        Returns:
            CrewConfig instance
        """
        agents = {}
        for name, agent_data in config_data.get('agents', {}).items():
            agents[name] = AgentConfig(**agent_data)
        
        tasks = {}
        for name, task_data in config_data.get('tasks', {}).items():
            tasks[name] = TaskConfig(**task_data)
        
        subgroups = {}
        for name, subgroup_data in config_data.get('subgroups', {}).items():
            subgroups[name] = SubgroupConfig(**subgroup_data)
        
        crew_data = config_data.copy()
        crew_data['agents'] = agents
        crew_data['tasks'] = tasks
        crew_data['subgroups'] = subgroups
        
        return CrewConfig(**crew_data)
