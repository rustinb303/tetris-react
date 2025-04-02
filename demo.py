"""Demo script for the CrewAI multi-agent system."""
import os
import sys
from pathlib import Path

from src.config.config import AgentConfig, TaskConfig, CrewConfig
from src.agents.agent_factory import AgentFactory
from src.tasks.task_factory import TaskFactory
from src.models.crew_manager import CrewManager

def run_demo(topic="artificial intelligence"):
    """
    Run a simple demo of the CrewAI multi-agent system.
    
    Args:
        topic: The topic to research and summarize
    """
    print(f"Running demo with topic: {topic}")
    print("Creating agents...")
    
    researcher_config = AgentConfig(
        name="Researcher",
        role="Research Specialist",
        goal=f"Find accurate information about {topic}",
        backstory="You are an expert researcher who excels at finding information.",
        model="gpt-4o-mini"  # Using gpt-4o-mini as requested
    )
    
    writer_config = AgentConfig(
        name="Writer",
        role="Content Writer",
        goal=f"Create a concise summary about {topic}",
        backstory="You are a skilled writer who can explain complex topics clearly.",
        model="gpt-4o-mini"  # Using gpt-4o-mini as requested
    )
    
    agents = {
        "researcher": AgentFactory.create_agent(researcher_config),
        "writer": AgentFactory.create_agent(writer_config)
    }
    
    print("Creating tasks...")
    research_task_config = TaskConfig(
        name=f"Research {topic}",
        description=f"Research the topic of {topic} and gather key information",
        expected_output=f"A comprehensive overview of {topic}",
        agent="researcher"
    )
    
    write_task_config = TaskConfig(
        name=f"Summarize {topic}",
        description=f"Write a concise summary about {topic} based on the research",
        expected_output=f"A clear, engaging summary of {topic}",
        agent="writer"
    )
    
    tasks = TaskFactory.create_tasks_from_config(
        {
            "research": research_task_config,
            "write": write_task_config
        },
        {name: agent for name, agent in agents.items()}
    )
    
    print("Creating crew...")
    crew_config = CrewConfig(
        name=f"{topic.title()} Research Crew",
        description=f"A crew that researches {topic} and creates a summary",
        agents={name: agent.config for name, agent in agents.items()},
        tasks={name: task.config for name, task in tasks.items()},
        process="sequential"
    )
    
    crew_manager = CrewManager(crew_config, agents, tasks)
    
    print(f"\nRunning {topic.title()} Research Crew...")
    print("This may take a few minutes...\n")
    result = crew_manager.run()
    
    print("\n" + "="*50)
    print(f"FINAL RESULT: {result}")
    print("="*50)
    
    return result

if __name__ == "__main__":
    if "OPENAI_API_KEY" not in os.environ or not os.environ["OPENAI_API_KEY"]:
        print("Error: OPENAI_API_KEY environment variable is not set.")
        print("Please set your OpenAI API key:")
        print("export OPENAI_API_KEY='your-api-key-here'")
        sys.exit(1)
    
    topic = sys.argv[1] if len(sys.argv) > 1 else "artificial intelligence"
    
    run_demo(topic)
