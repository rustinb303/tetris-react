"""Demo script for the CrewAI multi-agent system with detailed reporting."""
import os
import sys
from pathlib import Path

from src.config.config import AgentConfig, TaskConfig, CrewConfig
from src.agents.agent_factory import AgentFactory
from src.tasks.task_factory import TaskFactory
from src.models.crew_manager import CrewManager
from src.utils.env_loader import load_env_vars
from src.utils.crew_callbacks import create_callback
from src.utils.mock_database import MockDatabaseTool
from src.utils.tool_registry import ToolRegistry


def run_detailed_reporting_demo(topic="AI trends"):
    """
    Run a demo with detailed reporting of agent activities.
    
    Args:
        topic: The topic to research and analyze
    """
    load_env_vars()
    
    print(f"Running detailed reporting demo with topic: {topic}")
    
    logs_dir = Path("./agent_logs")
    logs_dir.mkdir(exist_ok=True)
    
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")
    
    use_db = bool(supabase_url and supabase_key)
    callback = create_callback(
        log_to_console=True,
        log_to_file=True,
        log_to_db=use_db,
        supabase_url=supabase_url,
        supabase_key=supabase_key,
        table_name="agent_activities" if use_db else None
    )
    
    tool_registry = ToolRegistry()
    mock_db = MockDatabaseTool(table_name="research_data")
    tool_registry.register_tool("research_db", mock_db)
    
    print("Creating agents...")
    
    researcher_config = AgentConfig(
        name="Researcher",
        role="Research Specialist",
        goal=f"Research {topic} and store findings in the database",
        backstory="You are an expert researcher who excels at finding and organizing information.",
        model="openai:gpt-4o-mini",
        tools=["research_db"],
        verbose=True
    )
    
    analyst_config = AgentConfig(
        name="Analyst",
        role="Data Analyst",
        goal=f"Analyze research data about {topic} from the database and provide insights",
        backstory="You are a skilled analyst who can extract meaningful insights from data.",
        model="openai:gpt-4o-mini",
        tools=["research_db"],
        verbose=True
    )
    
    agents = {
        "researcher": AgentFactory.create_agent(
            researcher_config, 
            tools=tool_registry.get_tools(researcher_config.tools)
        ),
        "analyst": AgentFactory.create_agent(
            analyst_config,
            tools=tool_registry.get_tools(analyst_config.tools)
        )
    }
    
    print("Creating tasks...")
    
    research_task_config = TaskConfig(
        name=f"Research {topic}",
        description=f"""
        Research {topic} thoroughly and store your findings in the database.
        
        Use the research_db tool to store your findings.
        Store at least 3 different subtopics with detailed information.
        """,
        expected_output=f"Confirmation that research data about {topic} has been stored in the database",
        agent="researcher"
    )
    
    analysis_task_config = TaskConfig(
        name=f"Analyze {topic} Data",
        description=f"""
        Retrieve the research data about {topic} from the database and analyze it to provide insights.
        
        Analyze the data and provide:
        1. A summary of the key findings
        2. Connections between different subtopics
        3. Potential implications or applications
        """,
        expected_output=f"Analysis and insights about {topic} based on the database data",
        agent="analyst"
    )
    
    tasks = TaskFactory.create_tasks_from_config(
        {
            "research": research_task_config,
            "analyze": analysis_task_config
        },
        {name: agent for name, agent in agents.items()}
    )
    
    crew_config = CrewConfig(
        name=f"{topic} Research Crew",
        description=f"A crew that researches and analyzes {topic} with detailed activity reporting",
        agents={name: agent.config for name, agent in agents.items()},
        tasks={name: task.config for name, task in tasks.items()},
        process="sequential",
        verbose=True,
        step_callback=callback
    )
    
    crew_manager = CrewManager(crew_config, agents, tasks)
    
    print(f"\nRunning {topic} Research Crew with detailed reporting...")
    print("This may take a few minutes...\n")
    
    result = crew_manager.run()
    
    print("\n" + "="*80)
    print(f"RESEARCH AND ANALYSIS RESULTS FOR {topic.upper()}:")
    print(result)
    print("="*80)
    
    print("\nDetailed reports of agent activities have been saved to the agent_logs directory.")
    if use_db:
        print(f"Agent activities have also been logged to the 'agent_activities' table in Supabase.")
    else:
        print("Supabase logging was disabled because credentials were not available.")
    
    return result


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Run a demo with detailed agent activity reporting")
    parser.add_argument("topic", nargs="?", default="AI trends", help="Topic to research and analyze")
    parser.add_argument("--dry-run", action="store_true", help="Run in dry-run mode (no API calls)")
    args = parser.parse_args()
    
    if args.dry_run:
        print(f"\nDry run mode: Would research and analyze '{args.topic}' with detailed reporting")
        print("This would log agent activities to console, file, and optionally Supabase")
        
        logs_dir = Path("./agent_logs")
        logs_dir.mkdir(exist_ok=True)
        
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_KEY")
        
        use_db = bool(supabase_url and supabase_key)
        
        print("\nLogging configuration:")
        print(f"- Log to console: Yes")
        print(f"- Log to file: Yes (directory: {logs_dir})")
        print(f"- Log to database: {'Yes' if use_db else 'No'}")
        if use_db:
            print(f"  - Supabase URL: {supabase_url}")
            print(f"  - Table name: agent_activities")
        
        print("\nAgent configuration:")
        print("- Researcher: Using model openai:gpt-4o-mini")
        print("- Analyst: Using model openai:gpt-4o-mini")
        
        print("\nTo run with actual API calls, remove the --dry-run flag")
    else:
        run_detailed_reporting_demo(args.topic)
