"""Environment variable loader for the CrewAI multi-agent system."""
import os
from pathlib import Path
from dotenv import load_dotenv

def load_env_vars(env_file: str = ".env") -> None:
    """
    Load environment variables from a .env file.
    
    Args:
        env_file: Path to the .env file
    """
    env_path = Path(env_file)
    if env_path.exists():
        load_dotenv(env_path)
        print(f"Loaded environment variables from {env_path}")
        return
    
    project_root = Path(__file__).parent.parent.parent
    env_path = project_root / env_file
    if env_path.exists():
        load_dotenv(env_path)
        print(f"Loaded environment variables from {env_path}")
        return
    
    example_env_path = project_root / ".env.example"
    if example_env_path.exists():
        print(f"No .env file found. Please create one based on the .env.example file.")
    else:
        print(f"No .env file found. Please create one with your API keys.")

def get_api_key(provider: str) -> str:
    """
    Get the API key for a specific provider.
    
    Args:
        provider: The provider name (openai, anthropic, google, grok)
        
    Returns:
        The API key for the provider
    """
    provider_map = {
        "openai": "OPENAI_API_KEY",
        "anthropic": "ANTHROPIC_API_KEY",
        "google": "GOOGLE_API_KEY",
        "gemini": "GOOGLE_API_KEY",  # Alias for google
        "grok": "GROK_API_KEY",
        "xai": "GROK_API_KEY",  # Alias for grok
    }
    
    env_var = provider_map.get(provider.lower())
    if not env_var:
        raise ValueError(f"Unknown provider: {provider}")
    
    api_key = os.environ.get(env_var)
    if not api_key:
        raise ValueError(f"API key for {provider} not found. Please set the {env_var} environment variable.")
    
    return api_key
