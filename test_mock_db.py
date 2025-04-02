"""Test script for the MockDatabaseTool."""
import json
from src.utils.mock_database import MockDatabaseTool

def test_mock_database():
    """Test the MockDatabaseTool directly."""
    print("Testing MockDatabaseTool...")
    
    mock_db = MockDatabaseTool(table_name="test_data")
    
    print("\n1. Testing direct method calls:")
    
    print("\nInserting data...")
    insert_data = {
        "topic": "Test Topic",
        "subtopic": "Test Subtopic",
        "content": "This is test content",
        "source": "Test Source"
    }
    insert_result = mock_db.insert(insert_data)
    print(f"Insert result: {insert_result}")
    
    print("\nSelecting data...")
    select_result = mock_db.select({"topic": "Test Topic"})
    print(f"Select result: {select_result}")
    
    print("\nUpdating data...")
    update_data = {
        "content": "This is updated test content"
    }
    update_result = mock_db.update(update_data, {"topic": "Test Topic"})
    print(f"Update result: {update_result}")
    
    print("\nSelecting after update...")
    select_after_update = mock_db.select({"topic": "Test Topic"})
    print(f"Select after update result: {select_after_update}")
    
    print("\n2. Testing _run method with JSON string input:")
    
    print("\nInserting with JSON string...")
    json_insert = json.dumps({
        "operation": "insert",
        "data": {
            "topic": "JSON Test Topic",
            "subtopic": "JSON Test Subtopic",
            "content": "This is JSON test content",
            "source": "JSON Test Source"
        }
    })
    json_insert_result = mock_db._run(json_insert)
    print(f"JSON insert result: {json_insert_result}")
    
    print("\nSelecting with JSON string...")
    json_select = json.dumps({
        "operation": "select",
        "filters": {"topic": "JSON Test Topic"}
    })
    json_select_result = mock_db._run(json_select)
    print(f"JSON select result: {json_select_result}")
    
    print("\n3. Testing with escaped JSON string (simulating agent input):")
    
    print("\nInserting with escaped JSON string...")
    escaped_json_insert = "{\\\"operation\\\": \\\"insert\\\", \\\"data\\\": {\\\"topic\\\": \\\"Escaped JSON Test\\\", \\\"subtopic\\\": \\\"Escaped JSON Subtopic\\\", \\\"content\\\": \\\"This is escaped JSON test content\\\", \\\"source\\\": \\\"Escaped JSON Test Source\\\"}}"
    escaped_json_insert_result = mock_db._run(escaped_json_insert)
    print(f"Escaped JSON insert result: {escaped_json_insert_result}")
    
    print("\nCleaning up...")
    delete_result = mock_db.delete({"topic": "Test Topic"})
    print(f"Delete result: {delete_result}")
    delete_result = mock_db.delete({"topic": "JSON Test Topic"})
    print(f"Delete result: {delete_result}")
    delete_result = mock_db.delete({"topic": "Escaped JSON Test"})
    print(f"Delete result: {delete_result}")
    
    print("\nTest completed!")

if __name__ == "__main__":
    test_mock_database()
