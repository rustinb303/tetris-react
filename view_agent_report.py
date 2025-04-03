"""Script to view the agent activities report."""
import os
import sys
import glob
import json
from datetime import datetime
from pathlib import Path

def view_latest_report():
    """View the latest agent activities report."""
    logs_dir = Path("./agent_logs")
    
    if not logs_dir.exists():
        print("Error: Agent logs directory not found.")
        print("Run a demo with detailed reporting first.")
        return
    
    log_files = glob.glob(str(logs_dir / "agent_activities_*.jsonl"))
    
    if not log_files:
        print("Error: No agent activity logs found.")
        print("Run a demo with detailed reporting first.")
        return
    
    latest_log_file = max(log_files, key=os.path.getctime)
    print(f"Viewing activities from: {latest_log_file}")
    
    activities = []
    with open(latest_log_file, "r") as f:
        for line in f:
            try:
                activity = json.loads(line)
                activities.append(activity)
            except json.JSONDecodeError:
                continue
    
    if not activities:
        print("No activities found in the log file.")
        return
    
    activities_by_agent = {}
    for activity in activities:
        agent_name = activity["agent_name"]
        if agent_name not in activities_by_agent:
            activities_by_agent[agent_name] = []
        
        activities_by_agent[agent_name].append(activity)
    
    print("=" * 100)
    print("AGENT ACTIVITY REPORT")
    print("=" * 100)
    
    for agent_name, agent_activities in activities_by_agent.items():
        print(f"\nAGENT: {agent_name}")
        print("-" * 100)
        
        current_task = None
        
        for activity in agent_activities:
            timestamp = activity["timestamp"]
            activity_type = activity["activity_type"]
            data = activity["activity_data"]
            
            if activity_type == "task_start":
                task_name = data.get("task_name", "Unknown Task")
                current_task = task_name
                print(f"\nTASK: {task_name}")
                print(f"DESCRIPTION: {data.get('description', '')}")
                print("-" * 80)
            
            elif activity_type == "prompt":
                print(f"\n[{timestamp}] PROMPT:")
                print(f"{data.get('prompt', '')}")
            
            elif activity_type == "response":
                print(f"\n[{timestamp}] RESPONSE:")
                print(f"{data.get('response', '')}")
            
            elif activity_type == "task_end":
                print(f"\n[{timestamp}] TASK RESULT:")
                print(f"{data.get('result', '')}")
                print("-" * 80)
            
            else:
                print(f"\n[{timestamp}] {activity_type.upper()}:")
                print(json.dumps(data, indent=2))
        
        print("\n" + "=" * 100)

if __name__ == "__main__":
    view_latest_report()
