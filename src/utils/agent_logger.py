"""Logging utilities for CrewAI agent activities."""
import json
import os
from datetime import datetime
from typing import Dict, Any, List, Optional
from supabase import create_client

class AgentActivityLogger:
    """Logger for CrewAI agent activities."""
    
    def __init__(
        self, 
        log_to_console: bool = True, 
        log_to_file: bool = True,
        log_to_db: bool = False,
        log_dir: str = "./agent_logs",
        supabase_url: Optional[str] = None,
        supabase_key: Optional[str] = None,
        table_name: str = "agent_activities"
    ):
        """
        Initialize the agent activity logger.
        
        Args:
            log_to_console: Whether to log activities to console
            log_to_file: Whether to log activities to file
            log_to_db: Whether to log activities to database
            log_dir: Directory for log files
            supabase_url: Supabase URL for database logging
            supabase_key: Supabase API key for database logging
            table_name: Supabase table name for storing agent activities
        """
        self.log_to_console = log_to_console
        self.log_to_file = log_to_file
        self.log_to_db = log_to_db
        self.log_dir = log_dir
        self.table_name = table_name
        self.activities = []
        
        if log_to_file and not os.path.exists(log_dir):
            os.makedirs(log_dir)
        
        self.supabase = None
        if log_to_db and supabase_url and supabase_key:
            self.supabase = create_client(supabase_url, supabase_key)
    
    def log_activity(self, agent_name: str, activity_type: str, activity_data: Dict[str, Any]) -> None:
        """
        Log an agent activity.
        
        Args:
            agent_name: Name of the agent
            activity_type: Type of activity (e.g., 'prompt', 'response', 'task_start', 'task_end')
            activity_data: Data associated with the activity
        """
        timestamp = datetime.now().isoformat()
        
        activity = {
            "timestamp": timestamp,
            "agent_name": agent_name,
            "activity_type": activity_type,
            "activity_data": activity_data
        }
        
        self.activities.append(activity)
        
        if self.log_to_console:
            self._log_to_console(activity)
        
        if self.log_to_file:
            self._log_to_file(activity)
        
        if self.log_to_db and self.supabase:
            self._log_to_db(activity)
    
    def _log_to_console(self, activity: Dict[str, Any]) -> None:
        """Log activity to console."""
        agent_name = activity["agent_name"]
        activity_type = activity["activity_type"]
        
        print(f"\n{'=' * 80}")
        print(f"AGENT: {agent_name} | ACTIVITY: {activity_type} | TIME: {activity['timestamp']}")
        print(f"{'-' * 80}")
        
        if activity_type == "prompt":
            print(f"PROMPT: {activity['activity_data'].get('prompt', '')}")
        elif activity_type == "response":
            print(f"RESPONSE: {activity['activity_data'].get('response', '')}")
        elif activity_type == "task_start":
            print(f"STARTING TASK: {activity['activity_data'].get('task_name', '')}")
            print(f"DESCRIPTION: {activity['activity_data'].get('description', '')}")
        elif activity_type == "task_end":
            print(f"COMPLETED TASK: {activity['activity_data'].get('task_name', '')}")
            print(f"RESULT: {activity['activity_data'].get('result', '')}")
        else:
            print(json.dumps(activity["activity_data"], indent=2))
        
        print(f"{'=' * 80}\n")
    
    def _log_to_file(self, activity: Dict[str, Any]) -> None:
        """Log activity to file."""
        log_file = os.path.join(self.log_dir, f"agent_activities_{datetime.now().strftime('%Y%m%d')}.jsonl")
        
        with open(log_file, "a") as f:
            f.write(json.dumps(activity) + "\n")
    
    def _log_to_db(self, activity: Dict[str, Any]) -> None:
        """Log activity to database."""
        try:
            if self.supabase is not None:
                self.supabase.table(self.table_name).insert(activity).execute()
            else:
                print("Error: Supabase client is not initialized")
        except Exception as e:
            print(f"Error logging to database: {str(e)}")
    
    def get_activities(self, agent_name: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get all logged activities, optionally filtered by agent name.
        
        Args:
            agent_name: Optional agent name to filter by
            
        Returns:
            List of activity records
        """
        if agent_name:
            return [a for a in self.activities if a["agent_name"] == agent_name]
        
        return self.activities
    
    def generate_report(self) -> str:
        """
        Generate a formatted report of all agent activities.
        
        Returns:
            Formatted report as a string
        """
        if not self.activities:
            return "No agent activities recorded."
        
        activities_by_agent = {}
        for activity in self.activities:
            agent_name = activity["agent_name"]
            if agent_name not in activities_by_agent:
                activities_by_agent[agent_name] = []
            
            activities_by_agent[agent_name].append(activity)
        
        report = []
        report.append("=" * 100)
        report.append("AGENT ACTIVITY REPORT")
        report.append("=" * 100)
        
        for agent_name, activities in activities_by_agent.items():
            report.append(f"\nAGENT: {agent_name}")
            report.append("-" * 100)
            
            current_task = None
            
            for activity in activities:
                timestamp = activity["timestamp"]
                activity_type = activity["activity_type"]
                data = activity["activity_data"]
                
                if activity_type == "task_start":
                    task_name = data.get("task_name", "Unknown Task")
                    current_task = task_name
                    report.append(f"\nTASK: {task_name}")
                    report.append(f"DESCRIPTION: {data.get('description', '')}")
                    report.append("-" * 80)
                
                elif activity_type == "prompt":
                    report.append(f"\n[{timestamp}] PROMPT:")
                    report.append(f"{data.get('prompt', '')}")
                
                elif activity_type == "response":
                    report.append(f"\n[{timestamp}] RESPONSE:")
                    report.append(f"{data.get('response', '')}")
                
                elif activity_type == "task_end":
                    report.append(f"\n[{timestamp}] TASK RESULT:")
                    report.append(f"{data.get('result', '')}")
                    report.append("-" * 80)
                
                else:
                    report.append(f"\n[{timestamp}] {activity_type.upper()}:")
                    report.append(json.dumps(data, indent=2))
            
            report.append("\n" + "=" * 100)
        
        return "\n".join(report)
