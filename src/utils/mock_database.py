"""Mock database implementation for CrewAI agents."""
from typing import Dict, List, Any, Optional, Union
import os
import json
from pathlib import Path
from crewai.tools import BaseTool

class MockDatabaseTool(BaseTool):
    """Tool for interacting with a mock database (file-based)."""
    
    name: str = "MockDatabaseTool"
    description: str = "Tool for reading and writing data to a mock database."
    
    def __init__(self, table_name: str, data_dir: Optional[str] = None):
        """
        Initialize the mock database tool.
        
        Args:
            table_name: The name of the table to interact with
            data_dir: Directory to store the mock database files (defaults to ./mock_data)
        """
        super().__init__(
            name="MockDatabaseTool",
            description=f"Tool for reading and writing data to the {table_name} table in a mock database."
        )
        
        self._table_name = table_name
        self._data_dir = data_dir or os.path.join(os.getcwd(), "mock_data")
        
        Path(self._data_dir).mkdir(parents=True, exist_ok=True)
        
        self._table_file = os.path.join(self._data_dir, f"{self._table_name}.json")
        if not os.path.exists(self._table_file):
            with open(self._table_file, "w") as f:
                json.dump([], f)
    
    def _run(self, operation: str, **kwargs) -> Any:
        """
        Run a database operation.
        
        Args:
            operation: The operation to perform (select, insert, update, delete)
            **kwargs: Additional arguments for the operation
                - For select: filters
                - For insert: data
                - For update: data, filters
                - For delete: filters
                
        Returns:
            The result of the operation
        """
        if isinstance(operation, str) and '{' in operation:
            try:
                try:
                    params = json.loads(operation)
                except json.JSONDecodeError:
                    cleaned_op = operation.replace('\\"', '"').replace('\\\\', '\\')
                    
                    if cleaned_op.startswith('"') and cleaned_op.endswith('"'):
                        cleaned_op = cleaned_op[1:-1]
                    
                    try:
                        params = json.loads(cleaned_op)
                    except json.JSONDecodeError:
                        import re
                        json_pattern = r'(\{.*\})'
                        match = re.search(json_pattern, operation)
                        if match:
                            json_str = match.group(1)
                            params = json.loads(json_str)
                        else:
                            raise
                
                print(f"DEBUG - Parsed params: {params}")
                
                if isinstance(params, dict):
                    if 'operation' in params:
                        op = params.get('operation')
                        if op is not None:
                            operation = str(op)
                    
                    if 'data' in params:
                        kwargs['data'] = params.get('data')
                    
                    if 'filters' in params:
                        kwargs['filters'] = params.get('filters')
            except Exception as e:
                print(f"Error parsing JSON: {str(e)}")
                print(f"Original input: {operation}")
                return "Error: Invalid JSON format. Please provide a valid JSON object."
        
        if isinstance(operation, str):
            operation = operation.lower()
        
        try:
            with open(self._table_file, "r") as f:
                data = json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            data = []
        
        if operation == "select":
            filters = kwargs.get("filters", {})
            
            if not filters:
                return data
            
            result = []
            for item in data:
                match = True
                for key, value in filters.items():
                    if key not in item or item[key] != value:
                        match = False
                        break
                if match:
                    result.append(item)
            
            return result
        
        elif operation == "insert":
            new_data = kwargs.get("data", {})
            print(f"DEBUG - Insert operation with kwargs: {kwargs}")
            print(f"DEBUG - Data field: {new_data}")
            
            if not new_data:
                return "Error: No data provided for insert operation"
            
            if "id" not in new_data:
                new_data["id"] = f"mock-{len(data) + 1}"
            
            data.append(new_data)
            
            with open(self._table_file, "w") as f:
                json.dump(data, f, indent=2)
            
            return [new_data]
        
        elif operation == "update":
            update_data = kwargs.get("data", {})
            filters = kwargs.get("filters", {})
            
            if not update_data:
                return "Error: No data provided for update operation"
            
            if not filters:
                return "Error: No filters provided for update operation"
            
            updated = []
            for item in data:
                match = True
                for key, value in filters.items():
                    if key not in item or item[key] != value:
                        match = False
                        break
                
                if match:
                    for key, value in update_data.items():
                        item[key] = value
                    updated.append(item)
            
            with open(self._table_file, "w") as f:
                json.dump(data, f, indent=2)
            
            return updated
        
        elif operation == "delete":
            filters = kwargs.get("filters", {})
            
            if not filters:
                return "Error: No filters provided for delete operation"
            
            deleted = []
            new_data = []
            
            for item in data:
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
            
            return deleted
        
        else:
            return f"Error: Unsupported operation '{operation}'. Use 'select', 'insert', 'update', or 'delete'."
    
    def select(self, filters: Optional[Dict[str, Any]] = None) -> Union[List[Dict[str, Any]], str]:
        """
        Select data from the mock database.
        
        Args:
            filters: Dictionary of column-value pairs to filter by
            
        Returns:
            List of records matching the query or error message
        """
        return self._run("select", filters=filters or {})
    
    def insert(self, data: Dict[str, Any]) -> Union[Dict[str, Any], str]:
        """
        Insert data into the mock database.
        
        Args:
            data: Dictionary of column-value pairs to insert
            
        Returns:
            The inserted record or error message
        """
        return self._run("insert", data=data)
    
    def update(self, data: Dict[str, Any], filters: Dict[str, Any]) -> Union[Dict[str, Any], str]:
        """
        Update data in the mock database.
        
        Args:
            data: Dictionary of column-value pairs to update
            filters: Dictionary of column-value pairs to filter by
            
        Returns:
            The updated record or error message
        """
        return self._run("update", data=data, filters=filters)
    
    def delete(self, filters: Dict[str, Any]) -> Union[Dict[str, Any], str]:
        """
        Delete data from the mock database.
        
        Args:
            filters: Dictionary of column-value pairs to filter by
            
        Returns:
            The deleted record or error message
        """
        return self._run("delete", filters=filters)
