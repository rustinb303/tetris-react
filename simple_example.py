"""Simple example of using the CrewAI multi-agent system."""
import os
from pathlib import Path

os.environ["OPENAI_API_KEY"] = "your-api-key-here"

from src.config.config import AgentConfig, TaskConfig, SubgroupConfig, CrewConfig
from src.agents.agent_factory import AgentFactory
from src.tasks.task_factory import TaskFactory
from src.models.crew_manager import CrewManager

def run_simple_example():
    """Run a simple example with a research crew."""
    researcher_config = AgentConfig(
        name="Researcher",
        role="Research Specialist",
        goal="Find accurate information about the topic",
        backstory="You are an expert researcher who excels at finding information.",
        model="gpt-3.5-turbo"  # Using a less expensive model for testing
    )
    
    writer_config = AgentConfig(
        name="Writer",
        role="Content Writer",
        goal="Create a concise summary of the research",
        backstory="You are a skilled writer who can explain complex topics clearly.",
        model="gpt-3.5-turbo"  # Using a less expensive model for testing
    )
    
    agents = {
        "researcher": AgentFactory.create_agent(researcher_config),
        "writer": AgentFactory.create_agent(writer_config)
    }
    
    research_task_config = TaskConfig(
        name="Research AI Ethics",
        description="Research the current state of AI ethics and regulation",
        expected_output="A comprehensive overview of AI ethics and regulation",
        agent="researcher"
    )
    
    write_task_config = TaskConfig(
        name="Write Summary",
        description="Write a concise summary of the research on AI ethics",
        expected_output="A clear, engaging summary of AI ethics and regulation",
        agent="writer"
    )
    
    tasks = TaskFactory.create_tasks_from_config(
        {
            "research": research_task_config,
            "write": write_task_config
        },
        {name: agent for name, agent in agents.items()}
    )
    
    crew_config = CrewConfig(
        name="AI Ethics Research Crew",
        description="A crew that researches AI ethics and creates a summary",
        agents={name: agent.config for name, agent in agents.items()},
        tasks={name: task.config for name, task in tasks.items()},
        process="sequential"
    )
    
    crew_manager = CrewManager(crew_config, agents, tasks)
    
    print("Running AI Ethics Research Crew...")
    result = crew_manager.run()
    print(f"\nFinal result: {result}")

if __name__ == "__main__":
    run_simple_example()
