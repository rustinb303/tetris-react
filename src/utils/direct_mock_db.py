"""Direct mock database implementation for CrewAI agents."""
from typing import Dict, List, Any, Optional, Union
import os
import json
from pathlib import Path
from crewai.tools import BaseTool

class DirectMockDBTool(BaseTool):
    """Tool for interacting with a mock database (file-based) with direct parsing."""
    
    name: str = "DirectMockDBTool"
    description: str = "Tool for reading and writing data to a mock database."
    
    def __init__(self, table_name: str, data_dir: Optional[str] = None):
        """
        Initialize the mock database tool.
        
        Args:
            table_name: The name of the table to interact with
            data_dir: Directory to store the mock database files (defaults to ./mock_data)
        """
        super().__init__(
            name="DirectMockDBTool",
            description=f"Tool for reading and writing data to the {table_name} table in a mock database."
        )
        
        self._table_name = table_name
        self._data_dir = data_dir or os.path.join(os.getcwd(), "mock_data")
        
        Path(self._data_dir).mkdir(parents=True, exist_ok=True)
        
        self._table_file = os.path.join(self._data_dir, f"{self._table_name}.json")
        if not os.path.exists(self._table_file):
            with open(self._table_file, "w") as f:
                json.dump([], f)
    
    def _run(self, tool_input: Any) -> str:
        """
        Run a database operation based on the tool input.
        
        Args:
            tool_input: Input from the agent, could be a string, dict, or other format
                
        Returns:
            The result of the operation as a string
        """
        print(f"DEBUG - Tool input type: {type(tool_input)}")
        print(f"DEBUG - Tool input: {tool_input}")
        
        try:
            try:
                params = json.loads(tool_input)
                print(f"DEBUG - Successfully parsed JSON: {params}")
            except json.JSONDecodeError:
                import re
                json_pattern = r'\{.*\}'
                match = re.search(json_pattern, tool_input)
                if match:
                    json_str = match.group(0)
                    params = json.loads(json_str)
                    print(f"DEBUG - Extracted JSON from string: {params}")
                else:
                    operation = None
                    data = {}
                    filters = {}
                    
                    if "insert" in tool_input.lower():
                        operation = "insert"
                    elif "select" in tool_input.lower():
                        operation = "select"
                    elif "update" in tool_input.lower():
                        operation = "update"
                    elif "delete" in tool_input.lower():
                        operation = "delete"
                    
                    kv_pattern = r'(\w+):\s*"([^"]*)"'
                    kv_matches = re.findall(kv_pattern, tool_input)
                    
                    for key, value in kv_matches:
                        if key == "topic" or key == "subtopic" or key == "source":
                            if operation == "select" or operation == "update" or operation == "delete":
                                filters[key] = value
                            else:
                                data[key] = value
                        elif key == "content":
                            data[key] = value
                    
                    params = {
                        "operation": operation,
                        "data": data,
                        "filters": filters
                    }
                    print(f"DEBUG - Manually parsed input: {params}")
        except Exception as e:
            print(f"DEBUG - Error parsing input: {str(e)}")
            return f"Error: Could not parse input. Please provide a valid input. Error: {str(e)}"
        
        operation = params.get("operation")
        data = params.get("data", {})
        filters = params.get("filters", {})
        
        if not operation:
            return "Error: No operation specified. Please specify 'insert', 'select', 'update', or 'delete'."
        
        try:
            with open(self._table_file, "r") as f:
                current_data = json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            current_data = []
        
        if operation.lower() == "insert":
            if not data:
                return "Error: No data provided for insert operation"
            
            if "id" not in data:
                data["id"] = f"mock-{len(current_data) + 1}"
            
            current_data.append(data)
            
            with open(self._table_file, "w") as f:
                json.dump(current_data, f, indent=2)
            
            return f"Successfully inserted data: {json.dumps(data)}"
        
        elif operation.lower() == "select":
            if not filters:
                return f"Found {len(current_data)} records: {json.dumps(current_data)}"
            
            result = []
            for item in current_data:
                match = True
                for key, value in filters.items():
                    if key not in item or item[key] != value:
                        match = False
                        break
                if match:
                    result.append(item)
            
            return f"Found {len(result)} records: {json.dumps(result)}"
        
        elif operation.lower() == "update":
            if not data:
                return "Error: No data provided for update operation"
            
            if not filters:
                return "Error: No filters provided for update operation"
            
            updated = []
            for item in current_data:
                match = True
                for key, value in filters.items():
                    if key not in item or item[key] != value:
                        match = False
                        break
                
                if match:
                    for key, value in data.items():
                        item[key] = value
                    updated.append(item)
            
            with open(self._table_file, "w") as f:
                json.dump(current_data, f, indent=2)
            
            return f"Updated {len(updated)} records: {json.dumps(updated)}"
        
        elif operation.lower() == "delete":
            if not filters:
                return "Error: No filters provided for delete operation"
            
            deleted = []
            new_data = []
            
            for item in current_data:
                match = True
                for key, value in filters.items():
                    if key not in item or item[key] != value:
                        match = False
                        break
                
                if match:
                    deleted.append(item)
                else:
                    new_data.append(item)
            
            with open(self._table_file, "w") as f:
                json.dump(new_data, f, indent=2)
            
            return f"Deleted {len(deleted)} records: {json.dumps(deleted)}"
        
        else:
            return f"Error: Unsupported operation '{operation}'. Use 'insert', 'select', 'update', or 'delete'."
