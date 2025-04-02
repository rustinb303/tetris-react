"""Example usage of the CrewAI multi-agent system."""
import os
from pathlib import Path

from src.config.config import AgentConfig, TaskConfig, SubgroupConfig, CrewConfig
from src.agents.agent_factory import AgentFactory
from src.tasks.task_factory import TaskFactory
from src.models.crew_manager import CrewManager
from src.utils.tool_registry import ToolRegistry
from src.utils.config_loader import ConfigLoader


def run_from_config_file():
    """Run a crew from a configuration file."""
    from src.main import setup_crew_from_config
    
    config_path = Path(__file__).parent / "example_config.yaml"
    crew_manager = setup_crew_from_config(config_path)
    
    print("Running main crew...")
    result = crew_manager.run()
    print(f"Main crew result: {result}")
    
    print("\nRunning research team subgroup...")
    research_result = crew_manager.run_subgroup("research_team")
    print(f"Research team result: {research_result}")
    
    print("\nRunning content team subgroup...")
    content_result = crew_manager.run_subgroup("content_team")
    print(f"Content team result: {content_result}")


def run_programmatically():
    """Run a crew created programmatically."""
    tool_registry = ToolRegistry()
    
    researcher_config = AgentConfig(
        name="Researcher",
        role="Senior Research Analyst",
        goal="Find comprehensive information on the given topic",
        backstory="You are an expert researcher with a knack for finding relevant information quickly.",
        model="gpt-4"
    )
    
    analyst_config = AgentConfig(
        name="Analyst",
        role="Data Analyst",
        goal="Analyze the research data and extract meaningful insights",
        backstory="You are a skilled data analyst who can identify patterns and draw conclusions from complex information.",
        model="gpt-4",
        temperature=0.5
    )
    
    writer_config = AgentConfig(
        name="Writer",
        role="Content Writer",
        goal="Create a well-structured report based on the analysis",
        backstory="You are a talented writer who can communicate complex ideas clearly and engagingly.",
        model="gpt-3.5-turbo",
        temperature=0.8
    )
    
    agents = {
        "researcher": AgentFactory.create_agent(researcher_config),
        "analyst": AgentFactory.create_agent(analyst_config),
        "writer": AgentFactory.create_agent(writer_config)
    }
    
    research_task_config = TaskConfig(
        name="Research Topic",
        description="Research the given topic thoroughly and compile relevant information",
        expected_output="A comprehensive collection of information on the topic",
        agent="researcher"
    )
    
    analyze_task_config = TaskConfig(
        name="Analyze Research",
        description="Analyze the research data to identify key insights and patterns",
        expected_output="A detailed analysis of the research with key insights highlighted",
        agent="analyst"
    )
    
    write_task_config = TaskConfig(
        name="Write Report",
        description="Create a well-structured report based on the analysis",
        expected_output="A clear, engaging report that effectively communicates the findings",
        agent="writer"
    )
    
    tasks = TaskFactory.create_tasks_from_config(
        {
            "research": research_task_config,
            "analyze": analyze_task_config,
            "write": write_task_config
        },
        {name: agent for name, agent in agents.items()}
    )
    
    research_team_config = SubgroupConfig(
        name="Research Team",
        agents=["researcher", "analyst"],
        tasks=["research", "analyze"],
        process="sequential"
    )
    
    crew_config = CrewConfig(
        name="Research and Analysis Crew",
        description="A crew that researches a topic and provides analysis",
        agents={name: agent.config for name, agent in agents.items()},
        tasks={name: task.config for name, task in tasks.items()},
        subgroups={"research_team": research_team_config},
        process="sequential"
    )
    
    crew_manager = CrewManager(crew_config, agents, tasks)
    
    crew_manager.create_all_subgroups()
    
    print("Running main crew...")
    result = crew_manager.run()
    print(f"Main crew result: {result}")
    
    print("\nRunning research team subgroup...")
    research_result = crew_manager.run_subgroup("research_team")
    print(f"Research team result: {research_result}")


if __name__ == "__main__":
    os.environ["OPENAI_API_KEY"] = "your-api-key-here"
    
    run_from_config_file()
