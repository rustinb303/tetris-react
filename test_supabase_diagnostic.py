"""Diagnostic script for Supabase integration."""
import os
import json
from supabase import create_client
from src.utils.env_loader import load_env_vars

def test_supabase_connection():
    """Test the direct Supabase connection and diagnose issues."""
    load_env_vars()
    
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")
    
    if not supabase_url or not supabase_key:
        print("Error: Supabase credentials not found in environment variables.")
        return
    
    print(f"Testing Supabase connection with URL: {supabase_url}")
    
    try:
        supabase = create_client(supabase_url, supabase_key)
        print("Successfully connected to Supabase!")
        
        try:
            print("\nAttempting to list tables...")
            response = supabase.rpc('get_tables').execute()
            print(f"Tables: {response}")
        except Exception as e:
            print(f"Could not list tables: {str(e)}")
            print("This is expected if using an anon key with limited permissions.")
        
        table_name = "research_data"
        print(f"\nChecking if table '{table_name}' exists...")
        
        try:
            response = supabase.table(table_name).select("*").limit(1).execute()
            print(f"Table exists! Sample data: {response.data}")
            
            print(f"\nTrying to insert data into '{table_name}'...")
            
            test_data = {
                "topic": "test_topic",
                "subtopic": "test_subtopic",
                "content": "This is a test entry",
                "source": "Diagnostic test"
            }
            
            try:
                insert_response = supabase.table(table_name).insert(test_data).execute()
                print(f"Insert successful! Response: {insert_response.data}")
                
                print(f"\nVerifying inserted data...")
                select_response = supabase.table(table_name).select("*").eq("topic", "test_topic").execute()
                print(f"Select result: {select_response.data}")
                
                print(f"\nTrying to update data...")
                update_data = {"content": "This is an updated test entry"}
                update_response = supabase.table(table_name).update(update_data).eq("topic", "test_topic").execute()
                print(f"Update result: {update_response.data}")
                
                print(f"\nTrying to delete test data...")
                delete_response = supabase.table(table_name).delete().eq("topic", "test_topic").execute()
                print(f"Delete result: {delete_response.data}")
                
            except Exception as e:
                print(f"Error during data operations: {str(e)}")
                print("This might be due to table structure or permission issues.")
                
                print(f"\nAttempting to get table structure...")
                try:
                    structure_response = supabase.rpc('get_table_structure', {'table_name': table_name}).execute()
                    print(f"Table structure: {structure_response}")
                except Exception as e:
                    print(f"Could not get table structure: {str(e)}")
                    print("Let's try a simple insert with an ID field...")
                    
                    test_data_with_id = {
                        "id": "test-id-1",
                        "topic": "test_topic",
                        "subtopic": "test_subtopic",
                        "content": "This is a test entry",
                        "source": "Diagnostic test"
                    }
                    
                    try:
                        insert_response = supabase.table(table_name).insert(test_data_with_id).execute()
                        print(f"Insert with ID successful! Response: {insert_response.data}")
                    except Exception as e:
                        print(f"Insert with ID also failed: {str(e)}")
                        print("This suggests more fundamental permission or structure issues.")
            
        except Exception as e:
            print(f"Error accessing table '{table_name}': {str(e)}")
            print(f"The table might not exist or you might not have permission to access it.")
            
            print(f"\nAttempting to create table '{table_name}'...")
            try:
                create_table_response = supabase.rpc('create_table', {'table_name': table_name}).execute()
                print(f"Create table response: {create_table_response}")
            except Exception as e:
                print(f"Could not create table: {str(e)}")
                print("This is expected if using an anon key with limited permissions.")
                print("You may need to create the table through the Supabase dashboard.")
    
    except Exception as e:
        print(f"Error connecting to Supabase: {str(e)}")
        print("Please check your credentials and network connection.")
    
    print("\nDiagnostic test completed!")

if __name__ == "__main__":
    test_supabase_connection()
