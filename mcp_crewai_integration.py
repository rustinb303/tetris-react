"""Integration of MCP with CrewAI agents for file system and Google Drive access."""
import os
import asyncio
import json
from typing import Dict, Any, List, Optional, Union

from crewai import Agent, Task, Crew, Process
from langchain_openai import ChatOpenAI
from langchain.tools import BaseTool

from src.utils.env_loader import load_env_vars
from src.mcp import MCPContext, MCPClient, MCPRegistry
from src.mcp.integrations import FileSystemServer, GoogleDriveServer


class MCPFileTool(BaseTool):
    """Tool for CrewAI agents to access files using MCP."""
    
    name = "MCPFileTool"
    description = "Tool for reading and writing files using the Model Context Protocol."
    return_direct = False
    
    def __init__(self, mcp_client: MCPClient, server_name: str = "filesystem"):
        """
        Initialize the MCP file tool.
        
        Args:
            mcp_client: The MCP client to use
            server_name: The name of the MCP server to use
        """
        super().__init__()
        self.mcp_client = mcp_client
        self.server_name = server_name
    
    def _run(self, query: str) -> str:
        """
        Run a file operation using MCP.
        
        Args:
            query: The query string from the agent
            
        Returns:
            The result of the operation as a string
        """
        query = query.lower()
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            if "read" in query or "get" in query or "open" in query:
                import re
                path_match = re.search(r'file[:\s]+["\'](.*?)["\']', query)
                path = path_match.group(1) if path_match else None
                
                if not path:
                    return "Error: No file path provided. Please specify a file path."
                
                context = loop.run_until_complete(
                    self.mcp_client.get_context(self.server_name, path)
                )
                
                if context.metadata.get("success", False):
                    return f"File content: {context.data.get('content')}"
                else:
                    return f"Error: {context.data.get('error')}"
            
            elif "write" in query or "save" in query or "create" in query:
                import re
                path_match = re.search(r'file[:\s]+["\'](.*?)["\']', query)
                path = path_match.group(1) if path_match else None
                
                content_match = re.search(r'content[:\s]+["\'](.*?)["\']', query)
                content = content_match.group(1) if content_match else ""
                
                if not path:
                    return "Error: No file path provided. Please specify a file path."
                
                context = MCPContext(data={"content": content})
                
                result = loop.run_until_complete(
                    self.mcp_client.update_context(
                        self.server_name,
                        context,
                        params={"operation": "write", "path": path}
                    )
                )
                
                if result.metadata.get("success", False):
                    return f"Successfully wrote to file: {path}"
                else:
                    return f"Error: {result.data.get('error')}"
            
            elif "list" in query or "directory" in query or "folder" in query:
                import re
                path_match = re.search(r'directory[:\s]+["\'](.*?)["\']', query)
                if not path_match:
                    path_match = re.search(r'folder[:\s]+["\'](.*?)["\']', query)
                path = path_match.group(1) if path_match else "."
                
                context = loop.run_until_complete(
                    self.mcp_client.get_context(
                        self.server_name,
                        path,
                        params={"operation": "list"}
                    )
                )
                
                if context.metadata.get("success", False):
                    files = context.data.get("files", [])
                    return f"Files in directory: {files}"
                else:
                    return f"Error: {context.data.get('error')}"
            
            else:
                return "Error: Unsupported operation. Use 'read', 'write', or 'list'."
        
        finally:
            loop.close()


class MCPGoogleDriveTool(BaseTool):
    """Tool for CrewAI agents to access Google Drive using MCP."""
    
    name = "MCPGoogleDriveTool"
    description = "Tool for reading, writing, and searching files on Google Drive using the Model Context Protocol."
    return_direct = False
    
    def __init__(self, mcp_client: MCPClient, server_name: str = "googledrive"):
        """
        Initialize the MCP Google Drive tool.
        
        Args:
            mcp_client: The MCP client to use
            server_name: The name of the MCP server to use
        """
        super().__init__()
        self.mcp_client = mcp_client
        self.server_name = server_name
    
    def _run(self, query: str) -> str:
        """
        Run a Google Drive operation using MCP.
        
        Args:
            query: The query string from the agent
            
        Returns:
            The result of the operation as a string
        """
        query = query.lower()
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            if "search" in query:
                import re
                search_match = re.search(r'query[:\s]+["\'](.*?)["\']', query)
                search_query = search_match.group(1) if search_match else ""
                
                if not search_query:
                    return "Error: No search query provided. Please specify a search query."
                
                context = loop.run_until_complete(
                    self.mcp_client.get_context(
                        self.server_name,
                        search_query,
                        params={"operation": "search", "max_results": 5}
                    )
                )
                
                if context.metadata.get("success", False):
                    files = context.data.get("files", [])
                    if files:
                        result = f"Found {len(files)} files:\n"
                        for file in files:
                            result += f"- {file.get('name')} (ID: {file.get('id')})\n"
                        return result
                    else:
                        return "No files found matching the search query."
                else:
                    return f"Error: {context.data.get('error')}"
            
            elif "read" in query or "get" in query or "open" in query:
                import re
                id_match = re.search(r'id[:\s]+["\'](.*?)["\']', query)
                file_id = id_match.group(1) if id_match else None
                
                if not file_id:
                    return "Error: No file ID provided. Please specify a file ID."
                
                context = loop.run_until_complete(
                    self.mcp_client.get_context(
                        self.server_name,
                        file_id,
                        params={"operation": "read", "file_id": file_id}
                    )
                )
                
                if context.metadata.get("success", False):
                    content = context.data.get("content", "")
                    if len(content) > 1000:
                        content = content[:1000] + "... (content truncated)"
                    return f"File content: {content}"
                else:
                    return f"Error: {context.data.get('error')}"
            
            elif "create" in query or "write" in query or "save" in query:
                import re
                content_match = re.search(r'content[:\s]+["\'](.*?)["\']', query)
                content = content_match.group(1) if content_match else ""
                
                name_match = re.search(r'name[:\s]+["\'](.*?)["\']', query)
                name = name_match.group(1) if name_match else "Untitled Document"
                
                context = MCPContext(data={"content": content})
                
                result = loop.run_until_complete(
                    self.mcp_client.update_context(
                        self.server_name,
                        context,
                        params={"operation": "write", "name": name}
                    )
                )
                
                if result.metadata.get("success", False):
                    file_id = result.data.get("file_id")
                    return f"Successfully created file: {name} (ID: {file_id})"
                else:
                    return f"Error: {result.data.get('error')}"
            
            else:
                return "Error: Unsupported operation. Use 'search', 'read', or 'create'."
        
        finally:
            loop.close()


async def setup_mcp():
    """Set up MCP with file system and Google Drive servers."""
    client = MCPClient()
    
    fs_server = FileSystemServer(name="filesystem", root_dir=os.getcwd())
    client.register_server(fs_server)
    
    credentials_path = os.path.join(os.getcwd(), "credentials.json")
    if os.path.exists(credentials_path):
        drive_server = GoogleDriveServer(
            name="googledrive",
            credentials_path=credentials_path
        )
        client.register_server(drive_server)
    
    return client


def run_mcp_crewai_demo(topic="AI research"):
    """
    Run a demo with CrewAI agents using MCP for file access.
    
    Args:
        topic: The topic to research and write about
    """
    load_env_vars()
    
    print(f"Running MCP CrewAI demo with topic: {topic}")
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    mcp_client = loop.run_until_complete(setup_mcp())
    loop.close()
    
    file_tool = MCPFileTool(mcp_client, server_name="filesystem")
    
    credentials_path = os.path.join(os.getcwd(), "credentials.json")
    google_drive_tool = None
    if os.path.exists(credentials_path):
        google_drive_tool = MCPGoogleDriveTool(mcp_client, server_name="googledrive")
    
    openai_api_key = os.getenv("OPENAI_API_KEY")
    if not openai_api_key:
        print("Error: OpenAI API key not found in environment variables.")
        return
    
    llm = ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0.7,
        api_key=openai_api_key
    )
    
    print("Creating agents...")
    
    tools = [file_tool]
    if google_drive_tool:
        tools.append(google_drive_tool)
    
    researcher = Agent(
        name="Researcher",
        role="Research Specialist",
        goal=f"Research {topic} and save findings to files",
        backstory="You are an expert researcher who excels at finding and organizing information.",
        verbose=True,
        llm=llm,
        tools=tools
    )
    
    writer = Agent(
        name="Writer",
        role="Content Writer",
        goal=f"Write a comprehensive article about {topic} based on research",
        backstory="You are a skilled writer who can create engaging and informative content.",
        verbose=True,
        llm=llm,
        tools=tools
    )
    
    print("Creating tasks...")
    
    research_task = Task(
        description=f"""
        Research {topic} thoroughly and save your findings to files.
        
        To save your findings, use the MCPFileTool with queries like:
        
        ```
        Action: MCPFileTool
        Action Input: Write file: "research/{topic.lower().replace(' ', '_')}_findings.txt" with content: "Your research findings here"
        ```
        
        Research at least 3 different aspects of {topic} and save each to a separate file.
        """,
        expected_output=f"Confirmation that research data about {topic} has been saved to files",
        agent=researcher
    )
    
    writing_task = Task(
        description=f"""
        Read the research findings and write a comprehensive article about {topic}.
        
        To read the research files, use the MCPFileTool with queries like:
        ```
        Action: MCPFileTool
        Action Input: Read file: "research/{topic.lower().replace(' ', '_')}_findings.txt"
        ```
        
        Write a comprehensive article that includes:
        1. An introduction to {topic}
        2. Key aspects and findings from the research
        3. Implications and future directions
        
        Save your article to a file named "{topic.lower().replace(' ', '_')}_article.txt".
        """,
        expected_output=f"A comprehensive article about {topic} saved to a file",
        agent=writer
    )
    
    print("Creating crew...")
    crew = Crew(
        agents=[researcher, writer],
        tasks=[research_task, writing_task],
        verbose=True,
        process=Process.sequential
    )
    
    os.makedirs("research", exist_ok=True)
    
    print(f"\nRunning {topic} Research and Writing Crew...")
    print("This may take a few minutes...\n")
    
    result = crew.kickoff()
    
    print("\n" + "="*50)
    print(f"RESEARCH AND WRITING RESULTS FOR {topic.upper()}:")
    print(result)
    print("="*50)
    
    article_file = f"{topic.lower().replace(' ', '_')}_article.txt"
    if os.path.exists(article_file):
        with open(article_file, "r") as f:
            article_content = f.read()
        
        print("\n" + "="*50)
        print(f"ARTICLE CONTENT:")
        print(article_content)
        print("="*50)
    
    return result


if __name__ == "__main__":
    import sys
    topic = sys.argv[1] if len(sys.argv) > 1 else "Quantum Computing"
    
    run_mcp_crewai_demo(topic)
