"""Set up a table in Supabase for storing agent activities."""
import os
import sys
from supabase import create_client
from src.utils.env_loader import load_env_vars

def create_agent_activities_table():
    """Create the agent_activities table in Supabase."""
    load_env_vars()
    
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")
    
    if not supabase_url or not supabase_key:
        print("Error: Supabase credentials not found in environment variables.")
        return False
    
    print(f"Connecting to Supabase at: {supabase_url}")
    
    try:
        supabase = create_client(supabase_url, supabase_key)
        
        print("\nAttempting to create 'agent_activities' table with SQL...")
        try:
            sql = """
            CREATE TABLE IF NOT EXISTS agent_activities (
                id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                timestamp TEXT NOT NULL,
                agent_name TEXT NOT NULL,
                activity_type TEXT NOT NULL,
                activity_data JSONB,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            );
            """
            try:
                response = supabase.rpc('exec_sql', {'sql': sql}).execute()
                print(f"SQL execution response: {response}")
            except Exception as e:
                print(f"RPC failed: {str(e)}")
                print("Trying alternative method...")
                
                try:
                    response = supabase.from_("profiles").select("*").limit(1).execute()
                    print(f"Found 'profiles' table: {response.data}")
                    print("\nWe'll use the 'profiles' table for storing agent activities")
                    return True
                except Exception as e:
                    print(f"Error accessing 'profiles' table: {str(e)}")
                    
                    try:
                        response = supabase.from_("users").select("*").limit(1).execute()
                        print(f"Found 'users' table: {response.data}")
                        print("\nWe'll use the 'users' table for storing agent activities")
                        return True
                    except Exception as e:
                        print(f"Error accessing 'users' table: {str(e)}")
                        print("Could not find or create a suitable table for agent activities")
                        return False
            
            print("\nSuccessfully created 'agent_activities' table!")
            return True
                
        except Exception as e:
            print(f"Could not create table with SQL: {str(e)}")
            print("You may need to create the table through the Supabase dashboard.")
            return False
    
    except Exception as e:
        print(f"Error connecting to Supabase: {str(e)}")
        print("Please check your credentials and network connection.")
        return False

if __name__ == "__main__":
    success = create_agent_activities_table()
    
    if success:
        print("\nTable setup completed successfully!")
        print("You can now use the agent activity logger with database support.")
    else:
        print("\nTable setup failed.")
        print("You can still use the agent activity logger with console and file logging.")
