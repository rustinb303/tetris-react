"""
Google Drive integration for the Model Context Protocol (MCP).

This module provides an MCP server implementation for accessing and
manipulating files on Google Drive.
"""
import os
import json
import io
from typing import Dict, Any, List, Optional, Union

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload

from ..core import MCPServer, MCPContext


class GoogleDriveServer(MCPServer):
    """
    MCP server for interacting with Google Drive.
    
    This server provides context from files and folders on Google Drive.
    """
    
    SCOPES = [
        'https://www.googleapis.com/auth/drive.metadata.readonly',
        'https://www.googleapis.com/auth/drive.file',
        'https://www.googleapis.com/auth/drive'
    ]
    
    def __init__(self, name: str = "googledrive", credentials_path: Optional[str] = None, token_path: Optional[str] = None):
        """
        Initialize a new Google Drive server.
        
        Args:
            name: The name of the server
            credentials_path: Path to the credentials.json file
            token_path: Path to the token.json file
        """
        super().__init__(
            name=name,
            description="MCP server for accessing and manipulating files on Google Drive"
        )
        self.credentials_path = credentials_path or os.path.join(os.getcwd(), 'credentials.json')
        self.token_path = token_path or os.path.join(os.getcwd(), 'token.json')
        self.service = None
    
    def _authenticate(self) -> None:
        """
        Authenticate with Google Drive API.
        
        Raises:
            FileNotFoundError: If the credentials file does not exist
            Exception: If authentication fails
        """
        creds = None
        
        if os.path.exists(self.token_path):
            creds = Credentials.from_authorized_user_info(
                json.load(open(self.token_path)), self.SCOPES
            )
        
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                if not os.path.exists(self.credentials_path):
                    raise FileNotFoundError(f"Credentials file '{self.credentials_path}' does not exist")
                
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_path, self.SCOPES
                )
                creds = flow.run_local_server(port=0)
            
            with open(self.token_path, 'w') as token:
                token.write(creds.to_json())
        
        self.service = build('drive', 'v3', credentials=creds)
    
    def _ensure_authenticated(self) -> None:
        """
        Ensure that the server is authenticated with Google Drive API.
        
        Raises:
            Exception: If authentication fails
        """
        if not self.service:
            self._authenticate()
    
    async def get_context(self, query: str, params: Optional[Dict[str, Any]] = None) -> MCPContext:
        """
        Get context from Google Drive based on a query and optional parameters.
        
        Args:
            query: The query string (file or folder ID or name)
            params: Optional parameters to customize the context retrieval
                - operation: The operation to perform (read, list, exists, info, search)
                - file_id: The ID of the file or folder (if not provided in query)
                - mime_type: The MIME type to filter files by
                - recursive: Whether to list folders recursively (default: False)
                - max_results: Maximum number of results to return (default: 100)
            
        Returns:
            An MCPContext object containing the requested context
            
        Raises:
            Exception: If authentication fails or the operation fails
        """
        params = params or {}
        operation = params.get("operation", "read")
        
        try:
            self._ensure_authenticated()
            
            if operation == "read":
                file_id = params.get("file_id", query)
                
                file_metadata = self.service.files().get(fileId=file_id).execute()
                
                mime_type = file_metadata.get('mimeType', '')
                
                if mime_type == 'application/vnd.google-apps.document':
                    content = self.service.files().export(
                        fileId=file_id, mimeType='text/plain'
                    ).execute().decode('utf-8')
                elif mime_type == 'application/vnd.google-apps.spreadsheet':
                    content = self.service.files().export(
                        fileId=file_id, mimeType='text/csv'
                    ).execute().decode('utf-8')
                elif mime_type == 'application/vnd.google-apps.presentation':
                    content = self.service.files().export(
                        fileId=file_id, mimeType='text/plain'
                    ).execute().decode('utf-8')
                else:
                    request = self.service.files().get_media(fileId=file_id)
                    fh = io.BytesIO()
                    downloader = MediaIoBaseDownload(fh, request)
                    done = False
                    while not done:
                        status, done = downloader.next_chunk()
                    
                    content = fh.getvalue().decode('utf-8', errors='replace')
                
                return MCPContext(
                    data={"content": content, "metadata": file_metadata},
                    metadata={"success": True, "file_id": file_id, "operation": operation}
                )
            
            elif operation == "list":
                folder_id = params.get("file_id", query)
                recursive = params.get("recursive", False)
                max_results = params.get("max_results", 100)
                
                folder_metadata = self.service.files().get(fileId=folder_id).execute()
                
                if folder_metadata.get('mimeType') != 'application/vnd.google-apps.folder':
                    return MCPContext(
                        data={"error": f"'{folder_id}' is not a folder"},
                        metadata={"success": False, "file_id": folder_id, "operation": operation}
                    )
                
                query = f"'{folder_id}' in parents"
                mime_type = params.get("mime_type")
                if mime_type:
                    query += f" and mimeType='{mime_type}'"
                
                results = []
                page_token = None
                
                while True:
                    response = self.service.files().list(
                        q=query,
                        spaces='drive',
                        fields='nextPageToken, files(id, name, mimeType, createdTime, modifiedTime, size)',
                        pageToken=page_token,
                        pageSize=min(max_results, 1000)
                    ).execute()
                    
                    results.extend(response.get('files', []))
                    page_token = response.get('nextPageToken')
                    
                    if not page_token or len(results) >= max_results:
                        break
                
                if recursive:
                    subfolders = [f for f in results if f.get('mimeType') == 'application/vnd.google-apps.folder']
                    
                    for subfolder in subfolders:
                        subfolder_params = params.copy()
                        subfolder_params["file_id"] = subfolder.get('id')
                        subfolder_context = await self.get_context(subfolder.get('id'), subfolder_params)
                        
                        if subfolder_context.metadata.get("success", False):
                            subfolder_files = subfolder_context.data.get("files", [])
                            results.extend(subfolder_files)
                
                return MCPContext(
                    data={"files": results[:max_results]},
                    metadata={"success": True, "folder_id": folder_id, "operation": operation}
                )
            
            elif operation == "exists":
                file_id = params.get("file_id", query)
                
                try:
                    self.service.files().get(fileId=file_id).execute()
                    exists = True
                except Exception:
                    exists = False
                
                return MCPContext(
                    data={"exists": exists},
                    metadata={"success": True, "file_id": file_id, "operation": operation}
                )
            
            elif operation == "info":
                file_id = params.get("file_id", query)
                
                try:
                    file_metadata = self.service.files().get(
                        fileId=file_id,
                        fields='id, name, mimeType, createdTime, modifiedTime, size, parents, webViewLink'
                    ).execute()
                    
                    return MCPContext(
                        data=file_metadata,
                        metadata={"success": True, "file_id": file_id, "operation": operation}
                    )
                except Exception as e:
                    return MCPContext(
                        data={"error": str(e)},
                        metadata={"success": False, "file_id": file_id, "operation": operation}
                    )
            
            elif operation == "search":
                search_query = query
                max_results = params.get("max_results", 100)
                mime_type = params.get("mime_type")
                
                query = f"name contains '{search_query}'"
                if mime_type:
                    query += f" and mimeType='{mime_type}'"
                
                results = []
                page_token = None
                
                while True:
                    response = self.service.files().list(
                        q=query,
                        spaces='drive',
                        fields='nextPageToken, files(id, name, mimeType, createdTime, modifiedTime, size)',
                        pageToken=page_token,
                        pageSize=min(max_results, 1000)
                    ).execute()
                    
                    results.extend(response.get('files', []))
                    page_token = response.get('nextPageToken')
                    
                    if not page_token or len(results) >= max_results:
                        break
                
                return MCPContext(
                    data={"files": results[:max_results]},
                    metadata={"success": True, "query": search_query, "operation": operation}
                )
            
            else:
                return MCPContext(
                    data={"error": f"Unsupported operation '{operation}'"},
                    metadata={"success": False, "query": query, "operation": operation}
                )
        
        except Exception as e:
            return MCPContext(
                data={"error": str(e)},
                metadata={"success": False, "query": query, "operation": operation}
            )
    
    async def update_context(self, context: MCPContext, params: Optional[Dict[str, Any]] = None) -> MCPContext:
        """
        Update context on Google Drive based on the provided context and optional parameters.
        
        Args:
            context: The context to update
            params: Optional parameters to customize the context update
                - operation: The operation to perform (write, create, update, delete, copy, move)
                - file_id: The ID of the file or folder to update
                - name: The name of the file or folder to create or update
                - mime_type: The MIME type of the file to create or update
                - parent_id: The ID of the parent folder
                - local_path: The local path to the file to upload
            
        Returns:
            An updated MCPContext object
            
        Raises:
            Exception: If authentication fails or the operation fails
        """
        params = params or {}
        operation = params.get("operation", "write")
        
        try:
            self._ensure_authenticated()
            
            if operation == "write":
                content = context.data.get("content", "")
                name = params.get("name", "Untitled")
                mime_type = params.get("mime_type", "text/plain")
                parent_id = params.get("parent_id")
                
                temp_file = os.path.join(os.getcwd(), "temp_file")
                with open(temp_file, "w", encoding="utf-8") as f:
                    f.write(content)
                
                file_metadata = {
                    'name': name,
                    'mimeType': mime_type
                }
                
                if parent_id:
                    file_metadata['parents'] = [parent_id]
                
                media = MediaFileUpload(temp_file, mimetype=mime_type)
                file = self.service.files().create(
                    body=file_metadata,
                    media_body=media,
                    fields='id'
                ).execute()
                
                os.remove(temp_file)
                
                return MCPContext(
                    data={"file_id": file.get('id')},
                    metadata={"success": True, "name": name, "operation": operation}
                )
            
            elif operation == "update":
                file_id = params.get("file_id")
                content = context.data.get("content", "")
                
                if not file_id:
                    return MCPContext(
                        data={"error": "File ID is required for update operation"},
                        metadata={"success": False, "operation": operation}
                    )
                
                file_metadata = self.service.files().get(fileId=file_id).execute()
                mime_type = file_metadata.get('mimeType')
                
                temp_file = os.path.join(os.getcwd(), "temp_file")
                with open(temp_file, "w", encoding="utf-8") as f:
                    f.write(content)
                
                media = MediaFileUpload(temp_file, mimetype=mime_type)
                file = self.service.files().update(
                    fileId=file_id,
                    media_body=media,
                    fields='id'
                ).execute()
                
                os.remove(temp_file)
                
                return MCPContext(
                    data={"file_id": file.get('id')},
                    metadata={"success": True, "file_id": file_id, "operation": operation}
                )
            
            elif operation == "create_folder":
                name = params.get("name", "Untitled Folder")
                parent_id = params.get("parent_id")
                
                folder_metadata = {
                    'name': name,
                    'mimeType': 'application/vnd.google-apps.folder'
                }
                
                if parent_id:
                    folder_metadata['parents'] = [parent_id]
                
                folder = self.service.files().create(
                    body=folder_metadata,
                    fields='id'
                ).execute()
                
                return MCPContext(
                    data={"folder_id": folder.get('id')},
                    metadata={"success": True, "name": name, "operation": operation}
                )
            
            elif operation == "delete":
                file_id = params.get("file_id")
                
                if not file_id:
                    return MCPContext(
                        data={"error": "File ID is required for delete operation"},
                        metadata={"success": False, "operation": operation}
                    )
                
                self.service.files().delete(fileId=file_id).execute()
                
                return MCPContext(
                    data={"file_id": file_id},
                    metadata={"success": True, "file_id": file_id, "operation": operation}
                )
            
            elif operation == "copy":
                file_id = params.get("file_id")
                name = params.get("name")
                parent_id = params.get("parent_id")
                
                if not file_id:
                    return MCPContext(
                        data={"error": "File ID is required for copy operation"},
                        metadata={"success": False, "operation": operation}
                    )
                
                file_metadata = {}
                
                if name:
                    file_metadata['name'] = name
                
                if parent_id:
                    file_metadata['parents'] = [parent_id]
                
                file = self.service.files().copy(
                    fileId=file_id,
                    body=file_metadata,
                    fields='id'
                ).execute()
                
                return MCPContext(
                    data={"file_id": file.get('id')},
                    metadata={"success": True, "source_file_id": file_id, "operation": operation}
                )
            
            elif operation == "move":
                file_id = params.get("file_id")
                parent_id = params.get("parent_id")
                
                if not file_id or not parent_id:
                    return MCPContext(
                        data={"error": "File ID and parent ID are required for move operation"},
                        metadata={"success": False, "operation": operation}
                    )
                
                file = self.service.files().get(
                    fileId=file_id,
                    fields='parents'
                ).execute()
                
                previous_parents = ",".join(file.get('parents', []))
                
                file = self.service.files().update(
                    fileId=file_id,
                    addParents=parent_id,
                    removeParents=previous_parents,
                    fields='id, parents'
                ).execute()
                
                return MCPContext(
                    data={"file_id": file.get('id'), "parents": file.get('parents')},
                    metadata={"success": True, "file_id": file_id, "operation": operation}
                )
            
            else:
                return MCPContext(
                    data={"error": f"Unsupported operation '{operation}'"},
                    metadata={"success": False, "operation": operation}
                )
        
        except Exception as e:
            return MCPContext(
                data={"error": str(e)},
                metadata={"success": False, "operation": operation}
            )
