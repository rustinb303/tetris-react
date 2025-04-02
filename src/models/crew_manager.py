"""Crew manager for the CrewAI multi-agent system."""
from typing import Dict, List, Optional, Any, Union

from crewai import Crew, Process
from crewai.tools.base_tool import BaseTool as Tool

from ..config.config import CrewConfig, SubgroupConfig
from ..agents.base_agent import BaseAgent
from ..tasks.base_task import BaseTask


class CrewManager:
    """Manager for creating and running crews of agents."""
    
    def __init__(
        self, 
        config: CrewConfig,
        agents: Dict[str, BaseAgent],
        tasks: Dict[str, BaseTask]
    ):
        """
        Initialize a crew manager with the given configuration.
        
        Args:
            config: The crew configuration
            agents: Dictionary mapping agent names to their BaseAgent instances
            tasks: Dictionary mapping task names to their BaseTask instances
        """
        self.config = config
        self.agents = agents
        self.tasks = tasks
        self.subgroups = {}
        self._crew = self._create_crew()
    
    def _get_process(self, process_name: str) -> Process:
        """Convert process name to CrewAI Process enum."""
        process_map = {
            "sequential": Process.sequential,
            "hierarchical": Process.hierarchical
        }
        return process_map.get(process_name.lower(), Process.sequential)
    
    def _create_crew(self) -> Crew:
        """Create a CrewAI crew based on the configuration."""
        return Crew(
            agents=[agent.agent for agent in self.agents.values()],
            tasks=[task.task for task in self.tasks.values()],
            process=self._get_process(self.config.process),
            verbose=self.config.verbose,
            memory=self.config.memory,
            cache=self.config.cache,
            step_callback=self.config.step_callback
        )
    
    def create_subgroup(self, config: SubgroupConfig) -> Crew:
        """
        Create a subgroup crew based on the configuration.
        
        Args:
            config: The subgroup configuration
            
        Returns:
            A CrewAI Crew instance for the subgroup
        """
        subgroup_agents = [self.agents[name].agent for name in config.agents]
        subgroup_tasks = [self.tasks[name].task for name in config.tasks]
        
        crew = Crew(
            agents=subgroup_agents,
            tasks=subgroup_tasks,
            process=self._get_process(config.process),
            verbose=self.config.verbose,
            memory=self.config.memory,
            cache=self.config.cache,
            step_callback=self.config.step_callback
        )
        
        self.subgroups[config.name] = crew
        return crew
    
    def create_all_subgroups(self) -> Dict[str, Crew]:
        """
        Create all subgroups defined in the configuration.
        
        Returns:
            Dictionary mapping subgroup names to their Crew instances
        """
        for name, config in self.config.subgroups.items():
            self.create_subgroup(config)
        
        return self.subgroups
    
    @property
    def crew(self) -> Crew:
        """Get the main CrewAI crew."""
        return self._crew
    
    def run(self) -> Any:
        """
        Run the main crew.
        
        Returns:
            The result of running the crew
        """
        return self.crew.kickoff()
    
    def run_subgroup(self, name: str) -> Any:
        """
        Run a specific subgroup.
        
        Args:
            name: The name of the subgroup to run
            
        Returns:
            The result of running the subgroup
        """
        if name not in self.subgroups:
            raise ValueError(f"Subgroup '{name}' does not exist")
        
        return self.subgroups[name].kickoff()
