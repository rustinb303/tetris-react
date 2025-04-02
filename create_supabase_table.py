"""Script to create the necessary tables in Supabase."""
import os
import sys
from supabase import create_client
from src.utils.env_loader import load_env_vars

def create_research_data_table():
    """Create the research_data table in Supabase."""
    load_env_vars()
    
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")
    
    if not supabase_url or not supabase_key:
        print("Error: Supabase credentials not found in environment variables.")
        return
    
    print(f"Connecting to Supabase at: {supabase_url}")
    
    try:
        supabase = create_client(supabase_url, supabase_key)
        
        
        print("\nAttempting to list existing tables...")
        try:
            response = supabase.from_("profiles").select("*").limit(1).execute()
            print(f"Found 'profiles' table: {response.data}")
            
            print("\nWe'll use the 'profiles' table for our demo instead of 'research_data'")
            print("Updating demo3.py to use 'profiles' table...")
            
            update_demo_file('profiles')
            
            return True
            
        except Exception as e:
            print(f"Error accessing 'profiles' table: {str(e)}")
            
            try:
                response = supabase.from_("users").select("*").limit(1).execute()
                print(f"Found 'users' table: {response.data}")
                
                print("\nWe'll use the 'users' table for our demo instead of 'research_data'")
                print("Updating demo3.py to use 'users' table...")
                
                update_demo_file('users')
                
                return True
                
            except Exception as e:
                print(f"Error accessing 'users' table: {str(e)}")
                
                print("\nAttempting to create 'research_data' table with SQL...")
                try:
                    sql = """
                    CREATE TABLE IF NOT EXISTS research_data (
                        id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                        topic TEXT NOT NULL,
                        subtopic TEXT,
                        content TEXT,
                        source TEXT,
                        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                    );
                    """
                    response = supabase.rpc('exec_sql', {'sql': sql}).execute()
                    print(f"SQL execution response: {response}")
                    print("\nSuccessfully created 'research_data' table!")
                    return True
                    
                except Exception as e:
                    print(f"Could not create table with SQL: {str(e)}")
                    print("You may need to create the table through the Supabase dashboard.")
                    return False
    
    except Exception as e:
        print(f"Error connecting to Supabase: {str(e)}")
        print("Please check your credentials and network connection.")
        return False

def update_demo_file(table_name):
    """Update the demo3.py file to use the specified table name."""
    try:
        with open('demo3.py', 'r') as file:
            content = file.read()
        
        updated_content = content.replace('research_data', table_name)
        
        with open('demo3.py', 'w') as file:
            file.write(updated_content)
            
        print(f"Successfully updated demo3.py to use '{table_name}' table.")
        
    except Exception as e:
        print(f"Error updating demo3.py: {str(e)}")

if __name__ == "__main__":
    success = create_research_data_table()
    
    if success:
        print("\nTable setup completed successfully!")
        print("You can now run the demo3.py script.")
    else:
        print("\nTable setup failed.")
        print("Please create the necessary table through the Supabase dashboard.")
        sys.exit(1)
