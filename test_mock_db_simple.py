"""Simple test script for the MockDatabaseTool."""
import json
from src.utils.mock_database import MockDatabaseTool

def test_simple_insert():
    """Test a simple insert operation with the MockDatabaseTool."""
    print("Testing simple insert operation...")
    
    mock_db = MockDatabaseTool(table_name="test_simple")
    
    json_str = '{"operation": "insert", "data": {"topic": "Test", "content": "Test content"}}'
    print(f"Input JSON string: {json_str}")
    
    result = mock_db._run(json_str)
    print(f"Result: {result}")
    
    data = {"topic": "Test Direct", "content": "Test content direct"}
    print(f"Direct method call with data: {data}")
    
    result = mock_db.insert(data)
    print(f"Result: {result}")

if __name__ == "__main__":
    test_simple_insert()
