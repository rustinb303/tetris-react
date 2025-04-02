"""Demo script using langchain_community tools for database operations."""
import os
import sys
import json
from pathlib import Path
from typing import Dict, Any, List, Optional

from crewai import Agent, Task, Crew, Process
from langchain_openai import ChatOpenAI
from langchain.tools import BaseTool

from src.utils.env_loader import load_env_vars


class DatabaseTool(BaseTool):
    """Database tool using langchain_community BaseTool."""
    
    name = "DatabaseTool"
    description = "Tool for reading and writing data to a simple database."
    return_direct = False
    
    def __init__(self, table_name: str):
        """Initialize the database tool."""
        self.name = "DatabaseTool"
        self.description = f"Tool for reading and writing data to the {table_name} table in a simple database."
        self._table_name = table_name
        self._data_dir = os.path.join(os.getcwd(), "mock_data")
        Path(self._data_dir).mkdir(parents=True, exist_ok=True)
        
        self._table_file = os.path.join(self._data_dir, f"{table_name}.json")
        if not os.path.exists(self._table_file):
            with open(self._table_file, "w") as f:
                json.dump([], f)
        
        self._data = self._load_data()
    
    def _load_data(self):
        """Load data from the database file."""
        try:
            with open(self._table_file, "r") as f:
                return json.load(f)
        except Exception:
            return []
    
    def _save_data(self):
        """Save data to the database file."""
        with open(self._table_file, "w") as f:
            json.dump(self._data, f, indent=2)
    
    def _run(self, query: str) -> str:
        """Run a database operation."""
        print(f"DEBUG - Tool input: {query}")
        
        query = str(query).lower()
        
        if "insert" in query or "add" in query or "store" in query or "save" in query:
            import re
            
            topic_match = re.search(r'topic[:\s]+["\'](.*?)["\']', query)
            topic = topic_match.group(1) if topic_match else "Unknown"
            
            subtopic_match = re.search(r'subtopic[:\s]+["\'](.*?)["\']', query)
            subtopic = subtopic_match.group(1) if subtopic_match else "General"
            
            content_match = re.search(r'content[:\s]+["\'](.*?)["\']', query)
            content = content_match.group(1) if content_match else ""
            
            source_match = re.search(r'source[:\s]+["\'](.*?)["\']', query)
            source = source_match.group(1) if source_match else ""
            
            new_record = {
                "id": f"record-{len(self._data) + 1}",
                "topic": topic,
                "subtopic": subtopic,
                "content": content,
                "source": source
            }
            
            self._data.append(new_record)
            self._save_data()
            
            return f"Successfully inserted data: {new_record}"
            
        elif "select" in query or "find" in query or "get" in query or "retrieve" in query:
            import re
            
            topic_match = re.search(r'topic[:\s]+["\'](.*?)["\']', query)
            topic_filter = topic_match.group(1) if topic_match else None
            
            subtopic_match = re.search(r'subtopic[:\s]+["\'](.*?)["\']', query)
            subtopic_filter = subtopic_match.group(1) if subtopic_match else None
            
            filtered_data = self._data
            
            if topic_filter:
                filtered_data = [item for item in filtered_data if item.get("topic") == topic_filter]
            
            if subtopic_filter:
                filtered_data = [item for item in filtered_data if item.get("subtopic") == subtopic_filter]
            
            return f"Found {len(filtered_data)} records: {filtered_data}"
            
        elif "update" in query or "modify" in query or "change" in query:
            import re
            
            topic_match = re.search(r'where\s+topic[:\s]+["\'](.*?)["\']', query)
            topic_filter = topic_match.group(1) if topic_match else None
            
            subtopic_match = re.search(r'where\s+subtopic[:\s]+["\'](.*?)["\']', query)
            subtopic_filter = subtopic_match.group(1) if subtopic_match else None
            
            content_match = re.search(r'set\s+content[:\s]+["\'](.*?)["\']', query)
            new_content = content_match.group(1) if content_match else None
            
            updated_records = []
            
            for item in self._data:
                if (topic_filter and item.get("topic") == topic_filter) or \
                   (subtopic_filter and item.get("subtopic") == subtopic_filter):
                    if new_content:
                        item["content"] = new_content
                    updated_records.append(item)
            
            self._save_data()
            
            return f"Updated {len(updated_records)} records: {updated_records}"
            
        elif "delete" in query or "remove" in query:
            import re
            
            topic_match = re.search(r'where\s+topic[:\s]+["\'](.*?)["\']', query)
            topic_filter = topic_match.group(1) if topic_match else None
            
            subtopic_match = re.search(r'where\s+subtopic[:\s]+["\'](.*?)["\']', query)
            subtopic_filter = subtopic_match.group(1) if subtopic_match else None
            
            deleted_records = []
            new_data = []
            
            for item in self._data:
                if (topic_filter and item.get("topic") == topic_filter) or \
                   (subtopic_filter and item.get("subtopic") == subtopic_filter):
                    deleted_records.append(item)
                else:
                    new_data.append(item)
            
            self._data = new_data
            self._save_data()
            
            return f"Deleted {len(deleted_records)} records: {deleted_records}"
            
        else:
            return "Error: Unsupported operation. Use 'insert', 'select', 'update', or 'delete'."


def run_langchain_demo(topic="AI trends"):
    """
    Run a demo with agents that can access and manipulate data using langchain tools.
    
    Args:
        topic: The topic to research and store data about
    """
    load_env_vars()
    
    print(f"Running langchain demo with topic: {topic}")
    
    print("Setting up database tool...")
    db_tool = DatabaseTool(table_name="research_data")
    
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
        tools=[db_tool]
    )
    
    analyst = Agent(
        name="Analyst",
        role="Data Analyst",
        goal=f"Analyze research data about {topic} from the database and provide insights",
        backstory="You are a skilled analyst who can extract meaningful insights from data.",
        verbose=True,
        llm=llm,
        tools=[db_tool]
    )
    
    print("Creating tasks...")
    
    research_task = Task(
        description=f"""
        Research {topic} thoroughly and store your findings in the database.
        
        To store your findings, use the DatabaseTool with natural language queries like:
        
        ```
        Action: DatabaseTool
        Action Input: Insert a new record with topic: "{topic}", subtopic: "History", content: "Content about history...", source: "Source URL or reference"
        ```
        
        Store at least 3 different subtopics with detailed information.
        """,
        expected_output=f"Confirmation that research data about {topic} has been stored in the database",
        agent=researcher
    )
    
    analysis_task = Task(
        description=f"""
        Retrieve the research data about {topic} from the database and analyze it to provide insights.
        
        To retrieve the data, use the DatabaseTool with natural language queries like:
        ```
        Action: DatabaseTool
        Action Input: Select all records where topic: "{topic}"
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
        process=Process.sequential
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
    
    run_langchain_demo(topic)
