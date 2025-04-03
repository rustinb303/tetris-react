"""Test script for OpenRouter integration with different model providers."""
import os
import sys
from typing import Dict, Any

from src.utils.env_loader import load_env_vars
from src.utils.openrouter_utils import get_openrouter_llm, get_openrouter_model_name

def test_openrouter_integration():
    """Test OpenRouter integration with different model providers."""
    load_env_vars()
    
    openrouter_api_key = os.getenv("OPENROUTER_API_KEY")
    if not openrouter_api_key:
        print("Error: OPENROUTER_API_KEY environment variable not set.")
        print("Please add your OpenRouter API key to the .env file.")
        sys.exit(1)
    
    test_models = [
        ("openai", "gpt-4o-mini"),
        ("anthropic", "claude-3-7-sonnet-20250219"),
        ("gemini", "gemini-2.0-flash"),
        ("grok", "grok-1")
    ]
    
    for provider, model in test_models:
        print(f"\n{'='*50}")
        print(f"Testing OpenRouter with {provider}/{model}")
        print(f"{'='*50}")
        
        try:
            openrouter_model = get_openrouter_model_name(provider, model)
            print(f"OpenRouter model name: {openrouter_model}")
            
            llm = get_openrouter_llm(openrouter_model)
            
            prompt = "Write a short haiku about artificial intelligence."
            print(f"Sending prompt: '{prompt}'")
            
            response = llm.invoke(prompt)
            print(f"Response from {provider}/{model}:")
            print(response.content)
            print(f"{'='*50}")
            print("Test successful!")
        except Exception as e:
            print(f"Error testing {provider}/{model}: {e}")
            print("Test failed.")

if __name__ == "__main__":
    test_openrouter_integration()
