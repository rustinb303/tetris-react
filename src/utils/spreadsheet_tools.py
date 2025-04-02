"""Spreadsheet tools for CrewAI agents."""
from typing import Dict, List, Any, Optional, Union
import os
import json
from googleapiclient.discovery import build
from google.oauth2.service_account import Credentials
from crewai.tools import BaseTool

from ..utils.env_loader import get_api_key


class GoogleSheetsTool(BaseTool):
    """Tool for interacting with Google Sheets."""
    
    name: str = "GoogleSheetsTool"
    description: str = "Tool for reading and writing data to a Google Sheets spreadsheet."
    
    def __init__(self, spreadsheet_id: str, credentials_path: Optional[str] = None, credentials_json: Optional[str] = None):
        """
        Initialize the Google Sheets tool.
        
        Args:
            spreadsheet_id: The ID of the spreadsheet to interact with
            credentials_path: Path to the service account credentials JSON file
            credentials_json: JSON string of the service account credentials
        """
        super().__init__()
        self.spreadsheet_id = spreadsheet_id
        
        if credentials_path:
            self.credentials = Credentials.from_service_account_file(
                credentials_path, 
                scopes=["https://www.googleapis.com/auth/spreadsheets"]
            )
        elif credentials_json:
            self.credentials = Credentials.from_service_account_info(
                json.loads(credentials_json),
                scopes=["https://www.googleapis.com/auth/spreadsheets"]
            )
        elif os.getenv("GOOGLE_SHEETS_CREDENTIALS"):
            credentials_str = os.getenv("GOOGLE_SHEETS_CREDENTIALS")
            if credentials_str:
                self.credentials = Credentials.from_service_account_info(
                    json.loads(credentials_str),
                    scopes=["https://www.googleapis.com/auth/spreadsheets"]
                )
            else:
                raise ValueError("GOOGLE_SHEETS_CREDENTIALS environment variable is empty")
        else:
            raise ValueError(
                "Google Sheets credentials must be provided via credentials_path, "
                "credentials_json, or GOOGLE_SHEETS_CREDENTIALS environment variable"
            )
        
        self.service = build("sheets", "v4", credentials=self.credentials)
        self.sheets = self.service.spreadsheets()
    
    def _run(self, operation: str, **kwargs) -> Any:
        """
        Run a Google Sheets operation.
        
        Args:
            operation: The operation to perform (read, write, append, clear)
            **kwargs: Additional arguments for the operation
                - For read: range
                - For write: range, values
                - For append: range, values
                - For clear: range
                
        Returns:
            The result of the operation
        """
        operation = operation.lower()
        
        if operation == "read":
            sheet_range = kwargs.get("range")
            if not sheet_range:
                return "Error: No range provided for read operation"
            
            result = self.sheets.values().get(
                spreadsheetId=self.spreadsheet_id,
                range=sheet_range
            ).execute()
            
            return result.get("values", [])
        
        elif operation == "write":
            sheet_range = kwargs.get("range")
            values = kwargs.get("values", [])
            
            if not sheet_range:
                return "Error: No range provided for write operation"
            
            if not values:
                return "Error: No values provided for write operation"
            
            body = {
                "values": values
            }
            
            result = self.sheets.values().update(
                spreadsheetId=self.spreadsheet_id,
                range=sheet_range,
                valueInputOption="USER_ENTERED",
                body=body
            ).execute()
            
            return f"Updated {result.get('updatedCells')} cells"
        
        elif operation == "append":
            sheet_range = kwargs.get("range")
            values = kwargs.get("values", [])
            
            if not sheet_range:
                return "Error: No range provided for append operation"
            
            if not values:
                return "Error: No values provided for append operation"
            
            body = {
                "values": values
            }
            
            result = self.sheets.values().append(
                spreadsheetId=self.spreadsheet_id,
                range=sheet_range,
                valueInputOption="USER_ENTERED",
                insertDataOption="INSERT_ROWS",
                body=body
            ).execute()
            
            return f"Appended {result.get('updates', {}).get('updatedCells')} cells"
        
        elif operation == "clear":
            sheet_range = kwargs.get("range")
            
            if not sheet_range:
                return "Error: No range provided for clear operation"
            
            result = self.sheets.values().clear(
                spreadsheetId=self.spreadsheet_id,
                range=sheet_range,
                body={}
            ).execute()
            
            return f"Cleared {result.get('clearedRange')}"
        
        else:
            return f"Error: Unsupported operation '{operation}'. Use 'read', 'write', 'append', or 'clear'."
    
    def read(self, sheet_range: str) -> Union[List[List[Any]], str]:
        """
        Read data from the Google Sheet.
        
        Args:
            sheet_range: The range to read (e.g., "Sheet1!A1:D10")
            
        Returns:
            List of rows, where each row is a list of values, or error message
        """
        return self._run("read", range=sheet_range)
    
    def write(self, sheet_range: str, values: List[List[Any]]) -> Union[str, List[List[Any]]]:
        """
        Write data to the Google Sheet.
        
        Args:
            sheet_range: The range to write to (e.g., "Sheet1!A1:D10")
            values: List of rows, where each row is a list of values
            
        Returns:
            Status message or error message
        """
        return self._run("write", range=sheet_range, values=values)
    
    def append(self, sheet_range: str, values: List[List[Any]]) -> Union[str, List[List[Any]]]:
        """
        Append data to the Google Sheet.
        
        Args:
            sheet_range: The range to append to (e.g., "Sheet1!A1")
            values: List of rows, where each row is a list of values
            
        Returns:
            Status message or error message
        """
        return self._run("append", range=sheet_range, values=values)
    
    def clear(self, sheet_range: str) -> Union[str, List[List[Any]]]:
        """
        Clear data from the Google Sheet.
        
        Args:
            sheet_range: The range to clear (e.g., "Sheet1!A1:D10")
            
        Returns:
            Status message or error message
        """
        return self._run("clear", range=sheet_range)
