"""Tool registry for the CrewAI multi-agent system."""
from typing import Dict, List, Optional, Callable, Any, Union

from crewai.tools.base_tool import BaseTool as Tool
from .database_tools import SupabaseTool
from .spreadsheet_tools import GoogleSheetsTool


class ToolRegistry:
    """Registry for managing tools that agents can use."""
    
    def __init__(self):
        """Initialize an empty tool registry."""
        self.tools: Dict[str, Tool] = {}
    
    def register_tool(self, name: str, tool: Tool) -> None:
        """
        Register a tool with the given name.
        
        Args:
            name: The name of the tool
            tool: The tool instance
        """
        self.tools[name] = tool
    
    def register_function_as_tool(
        self, 
        name: str, 
        func: Callable, 
        description: str
    ) -> Tool:
        """
        Register a function as a tool.
        
        Args:
            name: The name of the tool
            func: The function to wrap as a tool
            description: Description of what the tool does
            
        Returns:
            The created tool
        """
        tool = Tool(
            name=name,
            func=func,
            description=description
        )
        self.register_tool(name, tool)
        return tool
    
    def get_tool(self, name: str) -> Optional[Tool]:
        """
        Get a tool by name.
        
        Args:
            name: The name of the tool
            
        Returns:
            The tool if found, None otherwise
        """
        return self.tools.get(name)
    
    def get_tools(self, names: List[str]) -> List[Tool]:
        """
        Get multiple tools by name.
        
        Args:
            names: List of tool names
            
        Returns:
            List of tools that were found
        """
        return [self.tools[name] for name in names if name in self.tools]
    
    def get_all_tools(self) -> List[Tool]:
        """
        Get all registered tools.
        
        Returns:
            List of all tools
        """
        return list(self.tools.values())
