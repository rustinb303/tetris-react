"""Test script for OpenRouter integration using the OpenAI library directly."""
import os
import sys
import json
from openai import OpenAI

from src.utils.env_loader import load_env_vars
from src.utils.openrouter_utils import get_openrouter_model_name

def test_openrouter_direct():
    """Test OpenRouter integration using the OpenAI library directly."""
    load_env_vars()
    
    openrouter_api_key = os.getenv("OPENROUTER_API_KEY")
    if not openrouter_api_key:
        print("Error: OPENROUTER_API_KEY environment variable not set.")
        print("Please add your OpenRouter API key to the .env file.")
        sys.exit(1)
    
    client = OpenAI(
        api_key=openrouter_api_key,
        base_url="https://openrouter.ai/api/v1",
        default_headers={
            "HTTP-Referer": "https://github.com/mattxlarson/crewai-multi-agent",
            "X-Title": "CrewAI Multi-Agent Project"
        }
    )
    
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
            
            prompt = "Write a short haiku about artificial intelligence."
            print(f"Sending prompt: '{prompt}'")
            
            response = client.chat.completions.create(
                model=openrouter_model,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7
            )
            
            print(f"Response from {provider}/{model}:")
            print(response.choices[0].message.content)
            print(f"{'='*50}")
            print("Test successful!")
        except Exception as e:
            print(f"Error testing {provider}/{model}: {e}")
            print("Test failed.")

if __name__ == "__main__":
    test_openrouter_direct()
