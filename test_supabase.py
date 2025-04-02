"""Test script for Supabase integration."""
import os
from src.utils.database_tools import SupabaseTool
from src.utils.env_loader import load_env_vars

def test_supabase_integration():
    """Test the Supabase integration directly."""
    load_env_vars()
    
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")
    
    if not supabase_url or not supabase_key:
        print("Error: Supabase credentials not found in environment variables.")
        return
    
    print(f"Testing Supabase integration with URL: {supabase_url}")
    
    supabase_tool = SupabaseTool(
        table_name="test_data",
        url=supabase_url,
        key=supabase_key
    )
    
    print("\nTesting INSERT operation...")
    insert_data = {
        "topic": "test_topic",
        "content": "This is a test entry",
        "created_at": "2025-04-02"
    }
    
    insert_result = supabase_tool._run("insert", data=insert_data)
    print(f"Insert result: {insert_result}")
    
    print("\nTesting SELECT operation...")
    select_result = supabase_tool._run("select", filters={"topic": "test_topic"})
    print(f"Select result: {select_result}")
    
    print("\nTesting UPDATE operation...")
    update_data = {
        "content": "This is an updated test entry"
    }
    update_result = supabase_tool._run("update", data=update_data, filters={"topic": "test_topic"})
    print(f"Update result: {update_result}")
    
    print("\nTesting SELECT after UPDATE...")
    select_after_update = supabase_tool._run("select", filters={"topic": "test_topic"})
    print(f"Select after update result: {select_after_update}")
    
    print("\nTesting DELETE operation...")
    delete_result = supabase_tool._run("delete", filters={"topic": "test_topic"})
    print(f"Delete result: {delete_result}")
    
    print("\nAll tests completed!")

if __name__ == "__main__":
    test_supabase_integration()
