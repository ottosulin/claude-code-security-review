"""Tests for LLM client factory and multi-provider support."""

import os
import pytest
from unittest.mock import patch, MagicMock

from claudecode.llm_client_factory import (
    LLMClientFactory, LLMConfig, get_llm_client, get_client_from_env,
    get_claude_api_client_multi_provider
)
from claudecode.llm_client_base import CloudProvider, LLMAPIClient
from claudecode.constants import DEFAULT_CLAUDE_MODEL


class TestLLMConfig:
    """Test LLM configuration class."""
    
    def test_config_creation(self):
        """Test basic config creation."""
        config = LLMConfig(
            provider=CloudProvider.ANTHROPIC,
            model="claude-3-sonnet-20240229",
            api_key="test-key"
        )
        
        assert config.provider == CloudProvider.ANTHROPIC
        assert config.model == "claude-3-sonnet-20240229"
        assert config.api_key == "test-key"
        assert config.timeout_seconds == 180  # default
        assert config.max_retries == 3  # default


class TestLLMClientFactory:
    """Test LLM client factory."""
    
    @patch('claudecode.anthropic_client.Anthropic')
    def test_create_anthropic_client(self, mock_anthropic):
        """Test creating Anthropic client."""
        config = LLMConfig(
            provider=CloudProvider.ANTHROPIC,
            model="claude-3-sonnet-20240229",
            api_key="test-key"
        )
        
        client = LLMClientFactory.create_client(config)
        
        assert client is not None
        assert client.provider_name == "anthropic"
        mock_anthropic.assert_called_once_with(api_key="test-key")
    
    @patch('claudecode.vertex_client.AnthropicVertex')
    def test_create_vertex_client(self, mock_vertex):
        """Test creating Vertex AI client."""
        config = LLMConfig(
            provider=CloudProvider.VERTEX_AI,
            model="claude-3-sonnet-20240229",
            project_id="test-project",
            region="us-central1"
        )
        
        client = LLMClientFactory.create_client(config)
        
        assert client is not None
        assert client.provider_name == "vertex"
        mock_vertex.assert_called_once_with(
            region="us-central1",
            project_id="test-project"
        )
    
    @patch('claudecode.bedrock_client.AnthropicBedrock')
    def test_create_bedrock_client(self, mock_bedrock):
        """Test creating Bedrock client."""
        config = LLMConfig(
            provider=CloudProvider.BEDROCK,
            model="claude-3-sonnet-20240229",
            aws_region="us-east-1"
        )
        
        client = LLMClientFactory.create_client(config)
        
        assert client is not None
        assert client.provider_name == "bedrock"
        mock_bedrock.assert_called_once_with(aws_region="us-east-1")
    
    def test_create_client_invalid_provider(self):
        """Test creating client with invalid provider."""
        config = LLMConfig(
            provider="invalid",  # type: ignore
            model="claude-3-sonnet-20240229"
        )
        
        with pytest.raises(ValueError, match="Unsupported provider"):
            LLMClientFactory.create_client(config)
    
    def test_create_client_from_dict_anthropic(self):
        """Test creating client from dictionary for Anthropic."""
        with patch('claudecode.anthropic_client.Anthropic'):
            client = LLMClientFactory.create_client_from_dict(
                provider="anthropic",
                model="claude-3-sonnet-20240229",
                api_key="test-key"
            )
            
            assert client.provider_name == "anthropic"
    
    def test_create_client_from_dict_invalid_provider(self):
        """Test creating client from dictionary with invalid provider."""
        with pytest.raises(ValueError, match="Unsupported provider"):
            LLMClientFactory.create_client_from_dict(
                provider="invalid",
                model="claude-3-sonnet-20240229"
            )
    
    @patch.dict(os.environ, {
        'LLM_PROVIDER': 'anthropic',
        'ANTHROPIC_API_KEY': 'test-key',
        'CLAUDE_MODEL': 'claude-3-sonnet-20240229'
    })
    @patch('claudecode.anthropic_client.Anthropic')
    def test_from_environment_anthropic(self, mock_anthropic):
        """Test creating client from environment variables for Anthropic."""
        client = LLMClientFactory.from_environment()
        
        assert client.provider_name == "anthropic"
        mock_anthropic.assert_called_once_with(api_key="test-key")
    
    @patch.dict(os.environ, {
        'LLM_PROVIDER': 'vertex',
        'GOOGLE_CLOUD_PROJECT': 'test-project',
        'GOOGLE_CLOUD_REGION': 'us-central1',
        'CLAUDE_MODEL': 'claude-3-sonnet-20240229'
    })
    @patch('claudecode.vertex_client.AnthropicVertex')
    def test_from_environment_vertex(self, mock_vertex):
        """Test creating client from environment variables for Vertex AI."""
        client = LLMClientFactory.from_environment()
        
        assert client.provider_name == "vertex"
        mock_vertex.assert_called_once_with(
            region="us-central1",
            project_id="test-project"
        )
    
    @patch.dict(os.environ, {
        'LLM_PROVIDER': 'bedrock',
        'AWS_REGION': 'us-west-2',
        'CLAUDE_MODEL': 'claude-3-sonnet-20240229'
    })
    @patch('claudecode.bedrock_client.AnthropicBedrock')
    def test_from_environment_bedrock(self, mock_bedrock):
        """Test creating client from environment variables for Bedrock."""
        client = LLMClientFactory.from_environment()
        
        assert client.provider_name == "bedrock"
        mock_bedrock.assert_called_once_with(aws_region="us-west-2")
    
    @patch.dict(os.environ, {'LLM_PROVIDER': 'invalid'})
    def test_from_environment_invalid_provider(self):
        """Test creating client from environment with invalid provider."""
        with pytest.raises(ValueError, match="Invalid LLM_PROVIDER"):
            LLMClientFactory.from_environment()
    
    def test_get_supported_providers(self):
        """Test getting list of supported providers."""
        providers = LLMClientFactory.get_supported_providers()
        
        assert "anthropic" in providers
        assert "vertex" in providers
        assert "bedrock" in providers
        assert len(providers) == 3
    
    def test_validate_config_anthropic_valid(self):
        """Test validating valid Anthropic config."""
        config = LLMConfig(
            provider=CloudProvider.ANTHROPIC,
            model="claude-3-sonnet-20240229",
            api_key="test-key"
        )
        
        is_valid, error = LLMClientFactory.validate_config(config)
        
        assert is_valid
        assert error == ""
    
    def test_validate_config_anthropic_invalid(self):
        """Test validating invalid Anthropic config."""
        config = LLMConfig(
            provider=CloudProvider.ANTHROPIC,
            model="claude-3-sonnet-20240229"
            # Missing api_key
        )
        
        is_valid, error = LLMClientFactory.validate_config(config)
        
        assert not is_valid
        assert "API key is required" in error
    
    def test_validate_config_vertex_valid(self):
        """Test validating valid Vertex AI config."""
        config = LLMConfig(
            provider=CloudProvider.VERTEX_AI,
            model="claude-3-sonnet-20240229",
            project_id="test-project",
            region="us-central1"
        )
        
        is_valid, error = LLMClientFactory.validate_config(config)
        
        assert is_valid
        assert error == ""
    
    def test_validate_config_vertex_invalid(self):
        """Test validating invalid Vertex AI config."""
        config = LLMConfig(
            provider=CloudProvider.VERTEX_AI,
            model="claude-3-sonnet-20240229"
            # Missing project_id and region
        )
        
        is_valid, error = LLMClientFactory.validate_config(config)
        
        assert not is_valid
        assert "project ID is required" in error
    
    def test_validate_config_bedrock_valid(self):
        """Test validating valid Bedrock config."""
        config = LLMConfig(
            provider=CloudProvider.BEDROCK,
            model="claude-3-sonnet-20240229",
            aws_region="us-east-1"
        )
        
        is_valid, error = LLMClientFactory.validate_config(config)
        
        assert is_valid
        assert error == ""


class TestConvenienceFunctions:
    """Test convenience functions."""
    
    @patch('claudecode.anthropic_client.Anthropic')
    def test_get_llm_client(self, mock_anthropic):
        """Test get_llm_client convenience function."""
        client = get_llm_client(
            provider="anthropic",
            model="claude-3-sonnet-20240229",
            api_key="test-key"
        )
        
        assert client.provider_name == "anthropic"
        mock_anthropic.assert_called_once_with(api_key="test-key")
    
    @patch.dict(os.environ, {
        'LLM_PROVIDER': 'anthropic',
        'ANTHROPIC_API_KEY': 'test-key'
    })
    @patch('claudecode.anthropic_client.Anthropic')
    def test_get_client_from_env(self, mock_anthropic):
        """Test get_client_from_env convenience function."""
        client = get_client_from_env()
        
        assert client.provider_name == "anthropic"
        mock_anthropic.assert_called_once_with(api_key="test-key")
    
    @patch('claudecode.anthropic_client.Anthropic')
    def test_get_claude_api_client_multi_provider_explicit(self, mock_anthropic):
        """Test backward compatibility function with explicit provider."""
        client = get_claude_api_client_multi_provider(
            model="claude-3-sonnet-20240229",
            api_key="test-key",
            provider="anthropic"
        )
        
        assert client.provider_name == "anthropic"
        mock_anthropic.assert_called_once_with(api_key="test-key")
    
    @patch.dict(os.environ, {'LLM_PROVIDER': 'vertex', 'GOOGLE_CLOUD_PROJECT': 'test-project'})
    @patch('claudecode.vertex_client.AnthropicVertex')
    def test_get_claude_api_client_multi_provider_env(self, mock_vertex):
        """Test backward compatibility function with environment provider."""
        client = get_claude_api_client_multi_provider(
            model="claude-3-sonnet-20240229"
        )
        
        assert client.provider_name == "vertex"
    
    @patch('claudecode.anthropic_client.Anthropic')
    def test_get_claude_api_client_multi_provider_default(self, mock_anthropic):
        """Test backward compatibility function defaults to Anthropic."""
        with patch.dict(os.environ, {}, clear=True):
            client = get_claude_api_client_multi_provider(
                model="claude-3-sonnet-20240229",
                api_key="test-key"
            )
            
            assert client.provider_name == "anthropic"
            mock_anthropic.assert_called_once_with(api_key="test-key")


if __name__ == "__main__":
    pytest.main([__file__])