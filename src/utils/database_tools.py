"""Database tools for CrewAI agents."""
from typing import Dict, List, Any, Optional, Union
import os
from supabase import create_client, Client
from crewai.tools import BaseTool

from ..utils.env_loader import get_api_key


class SupabaseTool(BaseTool):
    """Tool for interacting with Supabase database."""
    
    name: str = "SupabaseTool"
    description: str = "Tool for reading and writing data to a Supabase database."
    
    def __init__(self, table_name: str, url: Optional[str] = None, key: Optional[str] = None):
        """
        Initialize the Supabase tool.
        
        Args:
            table_name: The name of the table to interact with
            url: The Supabase URL (defaults to SUPABASE_URL env var)
            key: The Supabase key (defaults to SUPABASE_KEY env var)
        """
        super().__init__(
            name="SupabaseTool",
            description=f"Tool for reading and writing data to the {table_name} table in Supabase."
        )
        
        self._table_name = table_name
        self._url = url or os.getenv("SUPABASE_URL")
        self._key = key or os.getenv("SUPABASE_KEY") or get_api_key("supabase")
        
        if not self._url or not self._key:
            raise ValueError("Supabase URL and key must be provided or set in environment variables")
        
        self._supabase = create_client(self._url, self._key)
    
    def _run(self, operation: str, **kwargs) -> Any:
        """
        Run a Supabase operation.
        
        Args:
            operation: The operation to perform (select, insert, update, delete)
            **kwargs: Additional arguments for the operation
                - For select: columns, filters
                - For insert: data
                - For update: data, filters
                - For delete: filters
                
        Returns:
            The result of the operation
        """
        operation = operation.lower()
        
        if operation == "select":
            columns = kwargs.get("columns", "*")
            filters = kwargs.get("filters", {})
            
            query = self._supabase.table(self._table_name).select(columns)
            
            for key, value in filters.items():
                query = query.eq(key, value)
            
            result = query.execute()
            return result.data
        
        elif operation == "insert":
            data = kwargs.get("data", {})
            if not data:
                return "Error: No data provided for insert operation"
            
            result = self._supabase.table(self._table_name).insert(data).execute()
            return result.data
        
        elif operation == "update":
            data = kwargs.get("data", {})
            filters = kwargs.get("filters", {})
            
            if not data:
                return "Error: No data provided for update operation"
            
            if not filters:
                return "Error: No filters provided for update operation"
            
            query = self._supabase.table(self._table_name).update(data)
            
            for key, value in filters.items():
                query = query.eq(key, value)
            
            result = query.execute()
            return result.data
        
        elif operation == "delete":
            filters = kwargs.get("filters", {})
            
            if not filters:
                return "Error: No filters provided for delete operation"
            
            query = self._supabase.table(self._table_name).delete()
            
            for key, value in filters.items():
                query = query.eq(key, value)
            
            result = query.execute()
            return result.data
        
        else:
            return f"Error: Unsupported operation '{operation}'. Use 'select', 'insert', 'update', or 'delete'."
    
    def select(self, columns: str = "*", filters: Optional[Dict[str, Any]] = None) -> Union[List[Dict[str, Any]], str]:
        """
        Select data from the Supabase table.
        
        Args:
            columns: The columns to select (comma-separated string or "*" for all)
            filters: Dictionary of column-value pairs to filter by
            
        Returns:
            List of records matching the query or error message
        """
        return self._run("select", columns=columns, filters=filters or {})
    
    def insert(self, data: Dict[str, Any]) -> Union[Dict[str, Any], str]:
        """
        Insert data into the Supabase table.
        
        Args:
            data: Dictionary of column-value pairs to insert
            
        Returns:
            The inserted record or error message
        """
        return self._run("insert", data=data)
    
    def update(self, data: Dict[str, Any], filters: Dict[str, Any]) -> Union[Dict[str, Any], str]:
        """
        Update data in the Supabase table.
        
        Args:
            data: Dictionary of column-value pairs to update
            filters: Dictionary of column-value pairs to filter by
            
        Returns:
            The updated record or error message
        """
        return self._run("update", data=data, filters=filters)
    
    def delete(self, filters: Dict[str, Any]) -> Union[Dict[str, Any], str]:
        """
        Delete data from the Supabase table.
        
        Args:
            filters: Dictionary of column-value pairs to filter by
            
        Returns:
            The deleted record or error message
        """
        return self._run("delete", filters=filters)
