"""Demo script using the DirectMockDBTool for more reliable database operations."""
import os
import sys
from pathlib import Path
from typing import Dict, Any, List

from crewai import Agent, Task, Crew
from langchain_openai import ChatOpenAI

from src.utils.env_loader import load_env_vars
from src.utils.direct_mock_db import DirectMockDBTool


def run_direct_db_demo(topic="AI trends"):
    """
    Run a demo with agents that can access and manipulate data in a mock database.
    
    Args:
        topic: The topic to research and store data about
    """
    load_env_vars()
    
    print(f"Running direct database demo with topic: {topic}")
    
    print("Setting up direct mock database...")
    mock_db = DirectMockDBTool(table_name="research_data")
    
    openai_api_key = os.getenv("OPENAI_API_KEY")
    if not openai_api_key:
        print("Error: OpenAI API key not found in environment variables.")
        sys.exit(1)
    
    llm = ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0.7,
        api_key=openai_api_key
    )
    
    print("Creating agents...")
    
    researcher = Agent(
        name="Researcher",
        role="Research Specialist",
        goal=f"Research {topic} and store findings in the database",
        backstory="You are an expert researcher who excels at finding and organizing information.",
        verbose=True,
        llm=llm,
        tools=[mock_db]
    )
    
    analyst = Agent(
        name="Analyst",
        role="Data Analyst",
        goal=f"Analyze research data about {topic} from the database and provide insights",
        backstory="You are a skilled analyst who can extract meaningful insights from data.",
        verbose=True,
        llm=llm,
        tools=[mock_db]
    )
    
    print("Creating tasks...")
    
    research_task = Task(
        description=f"""
        Research {topic} thoroughly and store your findings in the database.
        
        To store your findings, use the DirectMockDBTool with the following format:
        
        ```
        Action: DirectMockDBTool
        Action Input: {{
            "operation": "insert",
            "data": {{
                "topic": "{topic}",
                "subtopic": "History",
                "content": "Content about history...",
                "source": "Source URL or reference"
            }}
        }}
        ```
        
        Store at least 3 different subtopics with detailed information.
        """,
        expected_output=f"Confirmation that research data about {topic} has been stored in the database",
        agent=researcher
    )
    
    analysis_task = Task(
        description=f"""
        Retrieve the research data about {topic} from the database and analyze it to provide insights.
        
        To retrieve the data, use the DirectMockDBTool with the following format:
        ```
        Action: DirectMockDBTool
        Action Input: {{
            "operation": "select",
            "filters": {{
                "topic": "{topic}"
            }}
        }}
        ```
        
        Analyze the data and provide:
        1. A summary of the key findings
        2. Connections between different subtopics
        3. Potential implications or applications
        """,
        expected_output=f"Analysis and insights about {topic} based on the database data",
        agent=analyst
    )
    
    print("Creating crew...")
    crew = Crew(
        agents=[researcher, analyst],
        tasks=[research_task, analysis_task],
        verbose=True,
        process="sequential"
    )
    
    print(f"\nRunning {topic} Research Crew...")
    print("This may take a few minutes...\n")
    
    result = crew.kickoff()
    
    print("\n" + "="*50)
    print(f"RESEARCH AND ANALYSIS RESULTS FOR {topic.upper()}:")
    print(result)
    print("="*50)
    
    return result


if __name__ == "__main__":
    topic = sys.argv[1] if len(sys.argv) > 1 else "AI trends"
    
    run_direct_db_demo(topic)
