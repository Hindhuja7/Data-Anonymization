"""
LLM client with sequential model fallback mechanism (GitHub models only).

Tries GitHub models in priority order.
Fails over to next model if current one fails.
"""

import os
import logging
from typing import Optional, Dict, Any, List
from dotenv import load_dotenv

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class LLMClient:
    """LLM client with sequential model fallback (GitHub models only)."""
    
    # Priority order for GitHub models (highest quality first)
    GITHUB_MODELS = [
        "gpt-4o",           # Highest quality
        "gpt-4o-mini",      # Faster, cheaper
        "gpt-4-turbo",      # Fallback
    ]
    
    def __init__(self, provider: str = "github", model: Optional[str] = None):
        """
        Initialize LLM client with fallback support.
        
        Args:
            provider: Must be 'github' (only GitHub models supported)
            model: Specific model to try first (must be in GITHUB_MODELS)
        """
        if provider != "github":
            raise ValueError("Only GitHub models are supported. Provider must be 'github'.")
        
        if model and model not in self.GITHUB_MODELS:
            raise ValueError(f"Model '{model}' not available. Available models: {self.GITHUB_MODELS}")
        
        self.primary_provider = provider
        self.primary_model = model
        self.current_client = None
        self.current_model = None
        self.current_provider = None
    
    def _initialize_client(self, provider: str, model: str) -> Any:
        """
        Initialize GitHub client.
        
        Args:
            provider: Provider name (must be 'github')
            model: Model name
            
        Returns:
            Client instance
        """
        if provider != "github":
            raise ValueError(f"Unsupported provider: {provider}. Only 'github' is supported.")
        
        api_key = os.getenv("GITHUB_API_KEY")
        if not api_key:
            raise ValueError("GITHUB_API_KEY not found in environment variables")
        
        return OpenAI(
            base_url="https://models.inference.ai.azure.com",
            api_key=api_key
        )
    
    def get_models_to_try(self) -> List[tuple]:
        """
        Get list of (provider, model) tuples to try in priority order.
        
        Returns:
            List of (provider, model) tuples (GitHub only)
        """
        models_to_try = []
        
        # If primary model specified, try it first
        if self.primary_model:
            models_to_try.append((self.primary_provider, self.primary_model))
        
        # Then try remaining GitHub models in priority order
        for model in self.GITHUB_MODELS:
            if model != self.primary_model:
                models_to_try.append(("github", model))
        
        return models_to_try
    
    def chat_completion(
        self, 
        messages: List[Dict[str, str]], 
        max_tokens: int = 1024,
        temperature: Optional[float] = None,
        response_format: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Perform chat completion with model fallback.
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            max_tokens: Maximum tokens in response
            temperature: Sampling temperature
            response_format: OpenAI response format dictionary
            
        Returns:
            Response text from successful model
        """
        models_to_try = self.get_models_to_try()
        last_error = None
        
        for provider, model in models_to_try:
            try:
                logger.info(f"Trying {provider} model: {model}")
                client = self._initialize_client(provider, model)
                
                # Build completion parameters
                kwargs = {
                    "model": model,
                    "messages": messages,
                    "max_tokens": max_tokens
                }
                if temperature is not None:
                    kwargs["temperature"] = temperature
                if response_format is not None:
                    kwargs["response_format"] = response_format
                    
                response = client.chat.completions.create(**kwargs)
                response_text = response.choices[0].message.content
                
                # Success - cache current client
                self.current_client = client
                self.current_model = model
                self.current_provider = provider
                
                logger.info(f"Successfully used {provider} model: {model}")
                return response_text
                
            except Exception as e:
                last_error = e
                logger.warning(f"Failed with {provider} model {model}: {e}")
                continue
        
        # All models failed
        raise RuntimeError(f"All models failed. Last error: {last_error}")
    
    def get_current_model(self) -> tuple:
        """
        Get current provider and model being used.
        
        Returns:
            Tuple of (provider, model)
        """
        return (self.current_provider, self.current_model)
