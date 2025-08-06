"""Factory for creating LLM API clients based on provider."""

import os
from typing import Optional, Dict, Any
from dataclasses import dataclass

from claudecode.llm_client_base import LLMAPIClient, CloudProvider
from claudecode.constants import DEFAULT_CLAUDE_MODEL, DEFAULT_TIMEOUT_SECONDS, DEFAULT_MAX_RETRIES
from claudecode.logger import get_logger

logger = get_logger(__name__)


@dataclass
class LLMConfig:
    """Configuration for LLM API clients."""
    provider: CloudProvider
    model: str
    timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS
    max_retries: int = DEFAULT_MAX_RETRIES
    
    # Provider-specific configs
    api_key: Optional[str] = None  # Anthropic
    project_id: Optional[str] = None  # Vertex AI
    region: Optional[str] = None  # Vertex AI  
    aws_region: Optional[str] = None  # Bedrock


class LLMClientFactory:
    """Factory for creating LLM API clients based on provider."""
    
    @staticmethod
    def create_client(config: LLMConfig) -> LLMAPIClient:
        """Create an LLM API client based on configuration.
        
        Args:
            config: LLM configuration object
            
        Returns:
            Initialized LLMAPIClient instance
            
        Raises:
            ValueError: If unsupported provider or invalid configuration
        """
        if config.provider == CloudProvider.ANTHROPIC:
            from claudecode.anthropic_client import AnthropicAPIClient
            return AnthropicAPIClient(
                model=config.model,
                api_key=config.api_key,
                timeout_seconds=config.timeout_seconds,
                max_retries=config.max_retries
            )
        elif config.provider == CloudProvider.VERTEX_AI:
            from claudecode.vertex_client import VertexAIClient
            return VertexAIClient(
                model=config.model,
                project_id=config.project_id,
                region=config.region,
                timeout_seconds=config.timeout_seconds,
                max_retries=config.max_retries
            )
        elif config.provider == CloudProvider.BEDROCK:
            from claudecode.bedrock_client import BedrockClient
            return BedrockClient(
                model=config.model,
                aws_region=config.aws_region,
                timeout_seconds=config.timeout_seconds,
                max_retries=config.max_retries
            )
        else:
            raise ValueError(f"Unsupported provider: {config.provider}")
    
    @staticmethod
    def create_client_from_dict(provider: str, **kwargs) -> LLMAPIClient:
        """Create client from provider string and keyword arguments.
        
        Args:
            provider: Provider name string ('anthropic', 'vertex', 'bedrock')
            **kwargs: Additional configuration parameters
            
        Returns:
            Initialized LLMAPIClient instance
        """
        try:
            provider_enum = CloudProvider(provider.lower())
        except ValueError:
            raise ValueError(f"Unsupported provider: {provider}. Supported: {[p.value for p in CloudProvider]}")
        
        config = LLMConfig(
            provider=provider_enum,
            model=kwargs.get('model', DEFAULT_CLAUDE_MODEL),
            timeout_seconds=kwargs.get('timeout_seconds', DEFAULT_TIMEOUT_SECONDS),
            max_retries=kwargs.get('max_retries', DEFAULT_MAX_RETRIES),
            api_key=kwargs.get('api_key'),
            project_id=kwargs.get('project_id'),
            region=kwargs.get('region'),
            aws_region=kwargs.get('aws_region')
        )
        
        return LLMClientFactory.create_client(config)
    
    @staticmethod
    def from_environment() -> LLMAPIClient:
        """Create client from environment variables.
        
        Environment variables:
        - LLM_PROVIDER: Provider name ('anthropic', 'vertex', 'bedrock')
        - CLAUDE_MODEL: Model name (optional, defaults to DEFAULT_CLAUDE_MODEL)
        - LLM_TIMEOUT_SECONDS: Timeout in seconds (optional)
        - LLM_MAX_RETRIES: Max retry attempts (optional)
        
        Provider-specific:
        - ANTHROPIC_API_KEY: Anthropic API key
        - GOOGLE_CLOUD_PROJECT: GCP project ID
        - GOOGLE_CLOUD_REGION: GCP region
        - AWS_REGION: AWS region
        
        Returns:
            Initialized LLMAPIClient instance
            
        Raises:
            ValueError: If invalid provider or missing required configuration
        """
        provider_str = os.environ.get('LLM_PROVIDER', 'anthropic').lower()
        
        try:
            provider = CloudProvider(provider_str)
        except ValueError:
            raise ValueError(f"Invalid LLM_PROVIDER: {provider_str}. Supported: {[p.value for p in CloudProvider]}")
        
        config = LLMConfig(
            provider=provider,
            model=os.environ.get('CLAUDE_MODEL', DEFAULT_CLAUDE_MODEL),
            timeout_seconds=int(os.environ.get('LLM_TIMEOUT_SECONDS', DEFAULT_TIMEOUT_SECONDS)),
            max_retries=int(os.environ.get('LLM_MAX_RETRIES', DEFAULT_MAX_RETRIES)),
            api_key=os.environ.get('ANTHROPIC_API_KEY'),
            project_id=os.environ.get('GOOGLE_CLOUD_PROJECT'),
            region=os.environ.get('GOOGLE_CLOUD_REGION', 'us-central1'),
            aws_region=os.environ.get('AWS_REGION', 'us-east-1')
        )
        
        logger.info(f"Creating LLM client for provider: {provider.value}")
        return LLMClientFactory.create_client(config)
    
    @staticmethod
    def get_supported_providers() -> list[str]:
        """Get list of supported provider names.
        
        Returns:
            List of supported provider strings
        """
        return [provider.value for provider in CloudProvider]
    
    @staticmethod 
    def validate_config(config: LLMConfig) -> tuple[bool, str]:
        """Validate LLM configuration.
        
        Args:
            config: LLM configuration to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if config.provider == CloudProvider.ANTHROPIC:
            if not config.api_key:
                return False, "Anthropic API key is required (ANTHROPIC_API_KEY)"
        elif config.provider == CloudProvider.VERTEX_AI:
            if not config.project_id:
                return False, "Google Cloud project ID is required (GOOGLE_CLOUD_PROJECT)"
            if not config.region:
                return False, "Google Cloud region is required (GOOGLE_CLOUD_REGION)"
        elif config.provider == CloudProvider.BEDROCK:
            if not config.aws_region:
                return False, "AWS region is required (AWS_REGION)"
        
        return True, ""


# Convenience functions for backward compatibility
def get_llm_client(provider: str = "anthropic", **kwargs) -> LLMAPIClient:
    """Get LLM client with specified provider.
    
    Args:
        provider: Provider name ('anthropic', 'vertex', 'bedrock')
        **kwargs: Additional configuration parameters
        
    Returns:
        Initialized LLMAPIClient instance
    """
    return LLMClientFactory.create_client_from_dict(provider, **kwargs)


def get_client_from_env() -> LLMAPIClient:
    """Get LLM client from environment variables.
    
    Returns:
        Initialized LLMAPIClient instance
    """
    return LLMClientFactory.from_environment()


# For backward compatibility with existing claude_api_client usage
def get_claude_api_client_multi_provider(model: str = DEFAULT_CLAUDE_MODEL,
                                        api_key: Optional[str] = None,
                                        timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS,
                                        provider: Optional[str] = None) -> LLMAPIClient:
    """Get Claude API client with multi-provider support.
    
    This function provides backward compatibility while enabling multi-provider support.
    If provider is not specified, it uses environment variables or defaults to Anthropic.
    
    Args:
        model: Claude model identifier
        api_key: Optional API key (for Anthropic)
        timeout_seconds: API call timeout
        provider: Optional provider name
        
    Returns:
        Initialized LLMAPIClient instance
    """
    if provider:
        return get_llm_client(
            provider=provider,
            model=model,
            api_key=api_key,
            timeout_seconds=timeout_seconds
        )
    else:
        # Check if environment specifies a provider
        env_provider = os.environ.get('LLM_PROVIDER')
        if env_provider and env_provider.lower() != 'anthropic':
            return LLMClientFactory.from_environment()
        else:
            # Default to Anthropic for backward compatibility
            return get_llm_client(
                provider='anthropic',
                model=model,
                api_key=api_key,
                timeout_seconds=timeout_seconds
            )