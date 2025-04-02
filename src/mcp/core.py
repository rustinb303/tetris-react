"""
Core implementation of the Model Context Protocol (MCP).

This module provides the base classes and interfaces for implementing
the Model Context Protocol, which standardizes how applications provide
context to LLMs.
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Union
import json
import os


class MCPContext:
    """
    Represents a context object in the Model Context Protocol.
    
    This class encapsulates the context data that is passed between
    clients and servers in the MCP ecosystem.
    """
    
    def __init__(self, data: Dict[str, Any], metadata: Optional[Dict[str, Any]] = None):
        """
        Initialize a new context object.
        
        Args:
            data: The main context data
            metadata: Optional metadata about the context
        """
        self.data = data
        self.metadata = metadata or {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the context to a dictionary representation."""
        return {
            "data": self.data,
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MCPContext':
        """Create a context object from a dictionary."""
        return cls(
            data=data.get("data", {}),
            metadata=data.get("metadata", {})
        )
    
    def to_json(self) -> str:
        """Convert the context to a JSON string."""
        return json.dumps(self.to_dict())
    
    @classmethod
    def from_json(cls, json_str: str) -> 'MCPContext':
        """Create a context object from a JSON string."""
        data = json.loads(json_str)
        return cls.from_dict(data)


class MCPServer(ABC):
    """
    Abstract base class for MCP servers.
    
    MCP servers provide context to clients by implementing specific
    data sources or tools.
    """
    
    def __init__(self, name: str, description: str):
        """
        Initialize a new MCP server.
        
        Args:
            name: The name of the server
            description: A description of the server's functionality
        """
        self.name = name
        self.description = description
    
    @abstractmethod
    async def get_context(self, query: str, params: Optional[Dict[str, Any]] = None) -> MCPContext:
        """
        Get context based on a query and optional parameters.
        
        Args:
            query: The query string
            params: Optional parameters to customize the context retrieval
            
        Returns:
            An MCPContext object containing the requested context
        """
        pass
    
    @abstractmethod
    async def update_context(self, context: MCPContext, params: Optional[Dict[str, Any]] = None) -> MCPContext:
        """
        Update context based on the provided context and optional parameters.
        
        Args:
            context: The context to update
            params: Optional parameters to customize the context update
            
        Returns:
            An updated MCPContext object
        """
        pass


class MCPClient:
    """
    Client for interacting with MCP servers.
    
    This class provides methods for connecting to and interacting with
    MCP servers to retrieve and update context.
    """
    
    def __init__(self):
        """Initialize a new MCP client."""
        self.servers: Dict[str, MCPServer] = {}
    
    def register_server(self, server: MCPServer) -> None:
        """
        Register a server with the client.
        
        Args:
            server: The server to register
        """
        self.servers[server.name] = server
    
    def unregister_server(self, server_name: str) -> None:
        """
        Unregister a server from the client.
        
        Args:
            server_name: The name of the server to unregister
        """
        if server_name in self.servers:
            del self.servers[server_name]
    
    async def get_context(self, server_name: str, query: str, params: Optional[Dict[str, Any]] = None) -> MCPContext:
        """
        Get context from a specific server.
        
        Args:
            server_name: The name of the server to get context from
            query: The query string
            params: Optional parameters to customize the context retrieval
            
        Returns:
            An MCPContext object containing the requested context
            
        Raises:
            ValueError: If the server is not registered
        """
        if server_name not in self.servers:
            raise ValueError(f"Server '{server_name}' is not registered")
        
        server = self.servers[server_name]
        return await server.get_context(query, params)
    
    async def update_context(self, server_name: str, context: MCPContext, params: Optional[Dict[str, Any]] = None) -> MCPContext:
        """
        Update context on a specific server.
        
        Args:
            server_name: The name of the server to update context on
            context: The context to update
            params: Optional parameters to customize the context update
            
        Returns:
            An updated MCPContext object
            
        Raises:
            ValueError: If the server is not registered
        """
        if server_name not in self.servers:
            raise ValueError(f"Server '{server_name}' is not registered")
        
        server = self.servers[server_name]
        return await server.update_context(context, params)


class MCPRegistry:
    """
    Registry for MCP servers and clients.
    
    This class provides a centralized registry for MCP servers and clients,
    making it easier to discover and connect to available servers.
    """
    
    _instance = None
    
    def __new__(cls):
        """Create a new registry instance or return the existing one."""
        if cls._instance is None:
            cls._instance = super(MCPRegistry, cls).__new__(cls)
            cls._instance._servers = {}
            cls._instance._clients = {}
        return cls._instance
    
    def __init__(self):
        """Initialize the registry."""
        if not hasattr(self, "_servers"):
            self._servers = {}
        if not hasattr(self, "_clients"):
            self._clients = {}
    
    def register_server(self, server: MCPServer) -> None:
        """
        Register a server with the registry.
        
        Args:
            server: The server to register
        """
        self._servers[server.name] = server
    
    def unregister_server(self, server_name: str) -> None:
        """
        Unregister a server from the registry.
        
        Args:
            server_name: The name of the server to unregister
        """
        if server_name in self._servers:
            del self._servers[server_name]
    
    def get_server(self, server_name: str) -> Optional[MCPServer]:
        """
        Get a server from the registry.
        
        Args:
            server_name: The name of the server to get
            
        Returns:
            The server if found, None otherwise
        """
        return self._servers.get(server_name)
    
    def list_servers(self) -> List[str]:
        """
        List all registered servers.
        
        Returns:
            A list of server names
        """
        return list(self._servers.keys())
    
    def register_client(self, client_id: str, client: MCPClient) -> None:
        """
        Register a client with the registry.
        
        Args:
            client_id: The ID of the client
            client: The client to register
        """
        self._clients[client_id] = client
    
    def unregister_client(self, client_id: str) -> None:
        """
        Unregister a client from the registry.
        
        Args:
            client_id: The ID of the client to unregister
        """
        if client_id in self._clients:
            del self._clients[client_id]
    
    def get_client(self, client_id: str) -> Optional[MCPClient]:
        """
        Get a client from the registry.
        
        Args:
            client_id: The ID of the client to get
            
        Returns:
            The client if found, None otherwise
        """
        return self._clients.get(client_id)
    
    def list_clients(self) -> List[str]:
        """
        List all registered clients.
        
        Returns:
            A list of client IDs
        """
        return list(self._clients.keys())
