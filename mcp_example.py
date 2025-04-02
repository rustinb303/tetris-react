"""Example script demonstrating the use of MCP with file system and Google Drive."""
import os
import asyncio
from typing import Dict, Any, Optional

from src.mcp import MCPContext, MCPClient
from src.mcp.integrations import FileSystemServer, GoogleDriveServer


async def file_system_example():
    """Demonstrate the use of MCP with the file system."""
    print("=== File System Example ===")
    
    client = MCPClient()
    fs_server = FileSystemServer(name="fs", root_dir=os.getcwd())
    client.register_server(fs_server)
    
    test_dir = os.path.join(os.getcwd(), "mcp_test")
    os.makedirs(test_dir, exist_ok=True)
    test_file = os.path.join(test_dir, "test.txt")
    
    with open(test_file, "w") as f:
        f.write("Hello, MCP!")
    
    context = await client.get_context("fs", test_file)
    print(f"File content: {context.data.get('content')}")
    
    context = await client.get_context(
        "fs", 
        test_dir, 
        params={"operation": "list"}
    )
    print(f"Files in directory: {context.data.get('files')}")
    
    update_context = MCPContext(data={"content": "Updated content via MCP!"})
    context = await client.update_context(
        "fs", 
        update_context, 
        params={"operation": "write", "path": test_file}
    )
    
    context = await client.get_context("fs", test_file)
    print(f"Updated file content: {context.data.get('content')}")
    
    os.remove(test_file)
    os.rmdir(test_dir)


async def google_drive_example(credentials_path: Optional[str] = None):
    """
    Demonstrate the use of MCP with Google Drive.
    
    Args:
        credentials_path: Path to the Google Drive API credentials file
    """
    if not credentials_path:
        print("=== Google Drive Example (Skipped) ===")
        print("No credentials provided. Skipping Google Drive example.")
        return
    
    print("=== Google Drive Example ===")
    
    client = MCPClient()
    drive_server = GoogleDriveServer(
        name="gdrive", 
        credentials_path=credentials_path
    )
    client.register_server(drive_server)
    
    context = await client.get_context(
        "gdrive", 
        "test", 
        params={"operation": "search", "max_results": 5}
    )
    
    files = context.data.get("files", [])
    if files:
        print(f"Found {len(files)} files:")
        for file in files:
            print(f"- {file.get('name')} ({file.get('id')})")
        
        file_id = files[0].get("id")
        context = await client.get_context(
            "gdrive", 
            file_id, 
            params={"operation": "info"}
        )
        print(f"File info: {context.data}")
    else:
        print("No files found.")


async def main():
    """Run the MCP examples."""
    await file_system_example()
    print()
    
    credentials_path = os.path.join(os.getcwd(), "credentials.json")
    if os.path.exists(credentials_path):
        await google_drive_example(credentials_path)
    else:
        await google_drive_example()


if __name__ == "__main__":
    asyncio.run(main())
