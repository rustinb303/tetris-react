"""
File system integration for the Model Context Protocol (MCP).

This module provides an MCP server implementation for accessing and
manipulating files on the local file system.
"""
import os
import json
import shutil
from pathlib import Path
from typing import Dict, Any, List, Optional, Union

from ..core import MCPServer, MCPContext


class FileSystemServer(MCPServer):
    """
    MCP server for interacting with the local file system.
    
    This server provides context from files and directories on the
    local file system.
    """
    
    def __init__(self, name: str = "filesystem", root_dir: Optional[str] = None):
        """
        Initialize a new file system server.
        
        Args:
            name: The name of the server
            root_dir: The root directory to restrict file access to (optional)
        """
        super().__init__(
            name=name,
            description="MCP server for accessing and manipulating files on the local file system"
        )
        self.root_dir = root_dir or os.getcwd()
    
    def _resolve_path(self, path: str) -> str:
        """
        Resolve a path relative to the root directory.
        
        Args:
            path: The path to resolve
            
        Returns:
            The resolved absolute path
            
        Raises:
            ValueError: If the path is outside the root directory
        """
        if os.path.isabs(path):
            abs_path = path
        else:
            abs_path = os.path.abspath(os.path.join(self.root_dir, path))
        
        if not abs_path.startswith(self.root_dir):
            raise ValueError(f"Path '{path}' is outside the root directory '{self.root_dir}'")
        
        return abs_path
    
    async def get_context(self, query: str, params: Optional[Dict[str, Any]] = None) -> MCPContext:
        """
        Get context from the file system based on a query and optional parameters.
        
        Args:
            query: The query string (file or directory path)
            params: Optional parameters to customize the context retrieval
                - operation: The operation to perform (read, list, exists, info)
                - encoding: The encoding to use for reading text files (default: utf-8)
                - recursive: Whether to list directories recursively (default: False)
                - pattern: A glob pattern to filter files (default: None)
            
        Returns:
            An MCPContext object containing the requested context
            
        Raises:
            ValueError: If the path is outside the root directory
            FileNotFoundError: If the file or directory does not exist
        """
        params = params or {}
        operation = params.get("operation", "read")
        
        try:
            path = self._resolve_path(query)
            
            if operation == "read":
                if not os.path.exists(path):
                    raise FileNotFoundError(f"File '{query}' does not exist")
                
                if os.path.isdir(path):
                    return MCPContext(
                        data={"error": f"Cannot read directory '{query}'"},
                        metadata={"success": False, "path": query, "operation": operation}
                    )
                
                encoding = params.get("encoding", "utf-8")
                try:
                    with open(path, "r", encoding=encoding) as f:
                        content = f.read()
                    
                    return MCPContext(
                        data={"content": content},
                        metadata={"success": True, "path": query, "operation": operation}
                    )
                except UnicodeDecodeError:
                    with open(path, "rb") as f:
                        content = f.read()
                    
                    return MCPContext(
                        data={"content": str(content), "binary": True},
                        metadata={"success": True, "path": query, "operation": operation}
                    )
            
            elif operation == "list":
                if not os.path.exists(path):
                    raise FileNotFoundError(f"Directory '{query}' does not exist")
                
                if not os.path.isdir(path):
                    return MCPContext(
                        data={"error": f"'{query}' is not a directory"},
                        metadata={"success": False, "path": query, "operation": operation}
                    )
                
                recursive = params.get("recursive", False)
                pattern = params.get("pattern", None)
                
                if recursive:
                    if pattern:
                        files = list(Path(path).rglob(pattern))
                    else:
                        files = list(Path(path).rglob("*"))
                else:
                    if pattern:
                        files = list(Path(path).glob(pattern))
                    else:
                        files = list(Path(path).glob("*"))
                
                files = [str(f.relative_to(path)) for f in files]
                
                return MCPContext(
                    data={"files": files},
                    metadata={"success": True, "path": query, "operation": operation}
                )
            
            elif operation == "exists":
                exists = os.path.exists(path)
                
                return MCPContext(
                    data={"exists": exists},
                    metadata={"success": True, "path": query, "operation": operation}
                )
            
            elif operation == "info":
                if not os.path.exists(path):
                    raise FileNotFoundError(f"File or directory '{query}' does not exist")
                
                stat = os.stat(path)
                
                info = {
                    "path": query,
                    "absolute_path": path,
                    "exists": True,
                    "is_file": os.path.isfile(path),
                    "is_dir": os.path.isdir(path),
                    "size": stat.st_size,
                    "created": stat.st_ctime,
                    "modified": stat.st_mtime,
                    "accessed": stat.st_atime
                }
                
                return MCPContext(
                    data=info,
                    metadata={"success": True, "path": query, "operation": operation}
                )
            
            else:
                return MCPContext(
                    data={"error": f"Unsupported operation '{operation}'"},
                    metadata={"success": False, "path": query, "operation": operation}
                )
        
        except (ValueError, FileNotFoundError) as e:
            return MCPContext(
                data={"error": str(e)},
                metadata={"success": False, "path": query, "operation": operation}
            )
    
    async def update_context(self, context: MCPContext, params: Optional[Dict[str, Any]] = None) -> MCPContext:
        """
        Update context on the file system based on the provided context and optional parameters.
        
        Args:
            context: The context to update
            params: Optional parameters to customize the context update
                - operation: The operation to perform (write, append, mkdir, delete, copy, move)
                - path: The path to write to or perform operations on
                - target_path: The target path for copy and move operations
                - encoding: The encoding to use for writing text files (default: utf-8)
                - create_dirs: Whether to create parent directories (default: False)
            
        Returns:
            An updated MCPContext object
            
        Raises:
            ValueError: If the path is outside the root directory
        """
        params = params or {}
        operation = params.get("operation", "write")
        path = params.get("path", "")
        
        try:
            resolved_path = self._resolve_path(path)
            
            if operation == "write":
                content = context.data.get("content", "")
                encoding = params.get("encoding", "utf-8")
                create_dirs = params.get("create_dirs", False)
                
                if create_dirs:
                    os.makedirs(os.path.dirname(resolved_path), exist_ok=True)
                
                with open(resolved_path, "w", encoding=encoding) as f:
                    f.write(content)
                
                return MCPContext(
                    data={"path": path},
                    metadata={"success": True, "path": path, "operation": operation}
                )
            
            elif operation == "append":
                content = context.data.get("content", "")
                encoding = params.get("encoding", "utf-8")
                create_dirs = params.get("create_dirs", False)
                
                if create_dirs:
                    os.makedirs(os.path.dirname(resolved_path), exist_ok=True)
                
                with open(resolved_path, "a", encoding=encoding) as f:
                    f.write(content)
                
                return MCPContext(
                    data={"path": path},
                    metadata={"success": True, "path": path, "operation": operation}
                )
            
            elif operation == "mkdir":
                create_parents = params.get("create_parents", True)
                
                if create_parents:
                    os.makedirs(resolved_path, exist_ok=True)
                else:
                    os.mkdir(resolved_path)
                
                return MCPContext(
                    data={"path": path},
                    metadata={"success": True, "path": path, "operation": operation}
                )
            
            elif operation == "delete":
                if not os.path.exists(resolved_path):
                    return MCPContext(
                        data={"error": f"File or directory '{path}' does not exist"},
                        metadata={"success": False, "path": path, "operation": operation}
                    )
                
                if os.path.isdir(resolved_path):
                    recursive = params.get("recursive", False)
                    
                    if recursive:
                        shutil.rmtree(resolved_path)
                    else:
                        os.rmdir(resolved_path)
                else:
                    os.remove(resolved_path)
                
                return MCPContext(
                    data={"path": path},
                    metadata={"success": True, "path": path, "operation": operation}
                )
            
            elif operation == "copy":
                target_path = params.get("target_path", "")
                
                if not target_path:
                    return MCPContext(
                        data={"error": "Target path is required for copy operation"},
                        metadata={"success": False, "path": path, "operation": operation}
                    )
                
                resolved_target_path = self._resolve_path(target_path)
                
                if not os.path.exists(resolved_path):
                    return MCPContext(
                        data={"error": f"Source path '{path}' does not exist"},
                        metadata={"success": False, "path": path, "operation": operation}
                    )
                
                if os.path.isdir(resolved_path):
                    shutil.copytree(resolved_path, resolved_target_path)
                else:
                    shutil.copy2(resolved_path, resolved_target_path)
                
                return MCPContext(
                    data={"source_path": path, "target_path": target_path},
                    metadata={"success": True, "path": path, "operation": operation}
                )
            
            elif operation == "move":
                target_path = params.get("target_path", "")
                
                if not target_path:
                    return MCPContext(
                        data={"error": "Target path is required for move operation"},
                        metadata={"success": False, "path": path, "operation": operation}
                    )
                
                resolved_target_path = self._resolve_path(target_path)
                
                if not os.path.exists(resolved_path):
                    return MCPContext(
                        data={"error": f"Source path '{path}' does not exist"},
                        metadata={"success": False, "path": path, "operation": operation}
                    )
                
                shutil.move(resolved_path, resolved_target_path)
                
                return MCPContext(
                    data={"source_path": path, "target_path": target_path},
                    metadata={"success": True, "path": path, "operation": operation}
                )
            
            else:
                return MCPContext(
                    data={"error": f"Unsupported operation '{operation}'"},
                    metadata={"success": False, "path": path, "operation": operation}
                )
        
        except Exception as e:
            return MCPContext(
                data={"error": str(e)},
                metadata={"success": False, "path": path, "operation": operation}
            )
