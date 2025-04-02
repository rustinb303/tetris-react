"""Test script to run the CrewAI multi-agent system."""
import os
import sys
from pathlib import Path

os.environ["OPENAI_API_KEY"] = "your-api-key-here"

from src.main import setup_crew_from_config

def main():
    """Run the CrewAI multi-agent system with a configuration file."""
    if len(sys.argv) < 2:
        print("Usage: python test_run.py <config_file>")
        print("Example: python test_run.py example_config.yaml")
        return
    
    config_path = Path(sys.argv[1])
    if not config_path.exists():
        print(f"Error: Config file '{config_path}' not found.")
        return
    
    print(f"Setting up crew from config: {config_path}")
    crew_manager = setup_crew_from_config(config_path)
    
    print("\nRunning main crew...")
    result = crew_manager.run()
    print(f"Main crew result: {result}")

if __name__ == "__main__":
    main()
