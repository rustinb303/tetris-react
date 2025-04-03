"""Comprehensive test script for all model providers through OpenRouter."""
import os
import sys
from typing import Dict, Any, List
import time

from src.utils.env_loader import load_env_vars
from src.utils.openrouter_utils import get_openrouter_llm, get_openrouter_model_name

def test_all_models():
    """Test all model providers through OpenRouter."""
    load_env_vars()
    
    openrouter_api_key = os.getenv("OPENROUTER_API_KEY")
    if not openrouter_api_key:
        print("Error: OPENROUTER_API_KEY environment variable not set.")
        print("Please add your OpenRouter API key to the .env file.")
        sys.exit(1)
    
    test_models = [
        ("openai", "gpt-4o-mini"),
        ("openai", "gpt-3.5-turbo"),
        ("anthropic", "claude-3-sonnet-20240229"),
        ("anthropic", "claude-3-7-sonnet-20250219"),
        ("gemini", "gemini-pro"),  # Will use fallback
        ("grok", "grok-1")  # Will use fallback
    ]
    
    results = []
    
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
            
            start_time = time.time()
            response = llm.invoke(prompt)
            end_time = time.time()
            
            print(f"Response from {provider}/{model}:")
            print(response.content)
            print(f"Response time: {end_time - start_time:.2f} seconds")
            print(f"{'='*50}")
            print("Test successful!")
            
            results.append({
                "provider": provider,
                "model": model,
                "openrouter_model": openrouter_model,
                "success": True,
                "response": response.content,
                "response_time": end_time - start_time
            })
        except Exception as e:
            print(f"Error testing {provider}/{model}: {e}")
            print("Test failed.")
            
            results.append({
                "provider": provider,
                "model": model,
                "openrouter_model": openrouter_model if 'openrouter_model' in locals() else None,
                "success": False,
                "error": str(e)
            })
    
    print("\n\n" + "="*50)
    print("TEST SUMMARY")
    print("="*50)
    
    successful_tests = [r for r in results if r["success"]]
    failed_tests = [r for r in results if not r["success"]]
    
    print(f"Total tests: {len(results)}")
    print(f"Successful: {len(successful_tests)}")
    print(f"Failed: {len(failed_tests)}")
    
    if failed_tests:
        print("\nFailed tests:")
        for test in failed_tests:
            print(f"- {test['provider']}/{test['model']}: {test.get('error', 'Unknown error')}")
    
    return results

if __name__ == "__main__":
    test_all_models()
