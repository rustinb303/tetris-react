"""Demo script for the CrewAI multi-agent system with database and spreadsheet integration."""
import os
import sys
from pathlib import Path
from typing import Dict, Any, List

from src.config.config import AgentConfig, TaskConfig, CrewConfig, SubgroupConfig
from src.agents.agent_factory import AgentFactory
from src.tasks.task_factory import TaskFactory
from src.models.crew_manager import CrewManager
from src.utils.env_loader import load_env_vars
from src.utils.database_tools import SupabaseTool
from src.utils.spreadsheet_tools import GoogleSheetsTool
from src.utils.mock_database import MockDatabaseTool
from src.utils.tool_registry import ToolRegistry


def run_data_integration_demo(topic="AI trends"):
    """
    Run a demo with agents that can access and manipulate data in Supabase.
    
    Args:
        topic: The topic to research and store data about
    """
    load_env_vars()
    
    print(f"Running data integration demo with topic: {topic}")
    
    tool_registry = ToolRegistry()
    
    print("Using mock database for demonstration purposes...")
    research_db_tool = MockDatabaseTool(table_name="research_data")
    tool_registry.register_tool("research_db", research_db_tool)
    
    print("Creating agents with database access...")
    
    researcher_config = AgentConfig(
        name="Researcher",
        role="Research Specialist",
        goal=f"Research {topic} and store findings in the database",
        backstory="You are an expert researcher who excels at finding and organizing information.",
        model="openai:gpt-4o-mini",
        tools=["research_db"]
    )
    
    analyst_config = AgentConfig(
        name="Analyst",
        role="Data Analyst",
        goal=f"Analyze research data about {topic} from the database and provide insights",
        backstory="You are a skilled analyst who can extract meaningful insights from data.",
        model="openai:gpt-4o-mini",
        tools=["research_db"]
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
        
        Use the research_db tool to store your findings. When using the tool, provide a simple JSON object as input:
        
        ```
        Action: MockDatabaseTool
        Action Input: {{"operation": "insert", "data": {{"topic": "{topic}", "subtopic": "History", "content": "Content about history...", "source": "Source URL or reference"}}}}
        ```
        
        IMPORTANT: 
        - The tool name is "MockDatabaseTool"
        - For insert operations, provide a JSON object with "operation" and "data" fields
        - The "data" field should contain the content to store
        - Do not escape quotes or add extra backslashes
        
        Store at least 3 different subtopics with detailed information.
        """,
        expected_output=f"Confirmation that research data about {topic} has been stored in the database",
        agent="researcher"
    )
    
    analysis_task_config = TaskConfig(
        name=f"Analyze {topic} Data",
        description=f"""
        Retrieve the research data about {topic} from the database and analyze it to provide insights.
        
        Use the research_db tool to retrieve the data:
        ```
        Action: MockDatabaseTool
        Action Input: {{"operation": "select", "filters": {{"topic": "{topic}"}}}}
        ```
        
        IMPORTANT: 
        - The tool name is "MockDatabaseTool"
        - For select operations, provide a JSON object with "operation" and optional "filters" fields
        - Do not escape quotes or add extra backslashes
        
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
        description=f"A crew that researches and analyzes {topic} using a shared database",
        agents={name: agent.config for name, agent in agents.items()},
        tasks={name: task.config for name, task in tasks.items()},
        process="sequential"
    )
    
    crew_manager = CrewManager(crew_config, agents, tasks)
    
    print(f"\nRunning {topic} Research Crew...")
    print("This may take a few minutes...\n")
    
    result = crew_manager.run()
    
    print("\n" + "="*50)
    print(f"RESEARCH AND ANALYSIS RESULTS FOR {topic.upper()}:")
    print(result)
    print("="*50)
    
    return result


if __name__ == "__main__":
    topic = sys.argv[1] if len(sys.argv) > 1 else "AI trends"
    
    run_data_integration_demo(topic)
