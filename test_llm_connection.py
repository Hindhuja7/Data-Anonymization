"""
Test LLM connection and fallback mechanism
"""

import os
import sys
from dotenv import load_dotenv

# Add PII_Detection to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "PII_Detection"))

from llm_client import LLMClient

load_dotenv()

def test_llm_connection():
    """Test LLM connection and fallback"""
    print("="*60)
    print("LLM CONNECTION TEST")
    print("="*60)
    
    # Check for API key
    api_key = os.getenv("GITHUB_API_KEY")
    if api_key:
        print(f"✓ GITHUB_API_KEY is set (length: {len(api_key)})")
    else:
        print("✗ GITHUB_API_KEY not found in environment")
        print("  LLM will not work without this key")
        return False
    
    # Check LLM configuration
    provider = os.getenv("LLM_PROVIDER", "github")
    model = os.getenv("LLM_MODEL", "gpt-4o")
    
    print(f"\nLLM Configuration:")
    print(f"  Provider: {provider}")
    print(f"  Model: {model}")
    
    # Test LLM client
    try:
        print("\n" + "="*60)
        print("Testing LLM Client")
        print("="*60)
        
        client = LLMClient(provider=provider, model=model)
        
        # Simple test message
        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Say 'Hello' in exactly one word."}
        ]
        
        print(f"Trying {provider} model: {model}")
        response = client.chat_completion(messages=messages, max_tokens=10)
        
        print(f"✓ LLM response successful: {response.strip()}")
        print(f"  Current model: {client.get_current_model()}")
        
        return True
        
    except Exception as e:
        print(f"✗ LLM connection failed: {e}")
        print("\nFallback mechanism:")
        print("  - LLMClient will try models in priority order:")
        print("    1. gpt-4o")
        print("    2. gpt-4o-mini") 
        print("    3. gpt-4-turbo")
        print("  - If all fail, CombinedPIIDetector will use regex-only detection")
        return False

if __name__ == "__main__":
    import sys
    sys.exit(0 if test_llm_connection() else 1)
