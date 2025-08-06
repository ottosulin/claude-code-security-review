"""Tests for GitHub Action multi-provider functionality."""

import os
import pytest
from unittest.mock import patch, MagicMock
import tempfile
import json

from claudecode.github_action_audit import (
    initialize_findings_filter, get_environment_config, 
    initialize_clients
)


class TestGitHubActionMultiProvider:
    """Test GitHub Action with multiple LLM providers."""

    @patch.dict(os.environ, {
        'LLM_PROVIDER': 'anthropic',
        'ANTHROPIC_API_KEY': 'test-anthropic-key',
        'ENABLE_CLAUDE_FILTERING': 'true',
        'CLAUDE_MODEL': 'claude-3-sonnet-20240229'
    })
    @patch('claudecode.anthropic_client.Anthropic')
    def test_anthropic_provider_initialization(self, mock_anthropic):
        """Test findings filter initialization with Anthropic provider."""
        findings_filter = initialize_findings_filter()
        
        assert findings_filter.use_claude_filtering is True
        assert findings_filter.claude_client is not None
        assert findings_filter.claude_client.provider_name == "anthropic"
        mock_anthropic.assert_called_once_with(api_key='test-anthropic-key')

    @patch.dict(os.environ, {
        'LLM_PROVIDER': 'vertex',
        'GOOGLE_CLOUD_PROJECT': 'test-project',
        'GOOGLE_CLOUD_REGION': 'us-central1',
        'ENABLE_CLAUDE_FILTERING': 'true',
        'CLAUDE_MODEL': 'claude-3-sonnet-20240229'
    })
    @patch('claudecode.vertex_client.AnthropicVertex')
    def test_vertex_provider_initialization(self, mock_vertex):
        """Test findings filter initialization with Vertex AI provider."""
        findings_filter = initialize_findings_filter()
        
        assert findings_filter.use_claude_filtering is True
        assert findings_filter.claude_client is not None
        assert findings_filter.claude_client.provider_name == "vertex"
        mock_vertex.assert_called_once_with(
            region='us-central1',
            project_id='test-project'
        )

    @patch.dict(os.environ, {
        'LLM_PROVIDER': 'bedrock',
        'AWS_REGION': 'us-east-1',
        'ENABLE_CLAUDE_FILTERING': 'true',
        'CLAUDE_MODEL': 'claude-3-sonnet-20240229'
    })
    @patch('claudecode.bedrock_client.AnthropicBedrock')
    def test_bedrock_provider_initialization(self, mock_bedrock):
        """Test findings filter initialization with Bedrock provider."""
        findings_filter = initialize_findings_filter()
        
        assert findings_filter.use_claude_filtering is True
        assert findings_filter.claude_client is not None
        assert findings_filter.claude_client.provider_name == "bedrock"
        mock_bedrock.assert_called_once_with(aws_region='us-east-1')

    @patch.dict(os.environ, {
        'LLM_PROVIDER': 'invalid-provider',
        'ENABLE_CLAUDE_FILTERING': 'true'
    })
    def test_invalid_provider_fallback(self):
        """Test that invalid provider falls back to Anthropic with warning."""
        with patch('claudecode.anthropic_client.Anthropic') as mock_anthropic:
            findings_filter = initialize_findings_filter()
            
            # Should fall back to Anthropic despite invalid provider
            assert findings_filter.use_claude_filtering is True
            assert findings_filter.claude_client is not None

    @patch.dict(os.environ, {
        'LLM_PROVIDER': 'anthropic',
        'ENABLE_CLAUDE_FILTERING': 'false'
    })
    def test_filtering_disabled(self):
        """Test that filtering can be disabled regardless of provider."""
        findings_filter = initialize_findings_filter()
        
        assert findings_filter.use_claude_filtering is False
        assert findings_filter.claude_client is None

    @patch.dict(os.environ, {
        'LLM_PROVIDER': 'vertex',
        'GOOGLE_CLOUD_PROJECT': 'test-project',
        'ENABLE_CLAUDE_FILTERING': 'true'
    })
    def test_custom_filtering_instructions(self):
        """Test custom filtering instructions are passed through."""
        custom_instructions = "Custom filtering rules for this project"
        
        with patch('claudecode.vertex_client.AnthropicVertex'):
            findings_filter = initialize_findings_filter(custom_instructions)
            
            assert findings_filter.custom_filtering_instructions == custom_instructions

    @patch.dict(os.environ, {
        'GITHUB_REPOSITORY': 'test/repo',
        'PR_NUMBER': '123'
    })
    def test_environment_config_extraction(self):
        """Test that environment configuration is extracted correctly."""
        repo_name, pr_number = get_environment_config()
        
        assert repo_name == 'test/repo'
        assert pr_number == 123

    @patch.dict(os.environ, {
        'GITHUB_REPOSITORY': 'test/repo',
        'PR_NUMBER': 'invalid'
    })
    def test_invalid_pr_number(self):
        """Test that invalid PR number raises configuration error."""
        from claudecode.github_action_audit import ConfigurationError
        
        with pytest.raises(ConfigurationError, match='Invalid PR_NUMBER'):
            get_environment_config()

    @patch.dict(os.environ, {
        'PR_NUMBER': '123'
    })
    def test_missing_repository(self):
        """Test that missing repository raises configuration error."""
        from claudecode.github_action_audit import ConfigurationError
        
        # Clear GITHUB_REPOSITORY if it exists
        if 'GITHUB_REPOSITORY' in os.environ:
            del os.environ['GITHUB_REPOSITORY']
        
        with pytest.raises(ConfigurationError, match='GITHUB_REPOSITORY'):
            get_environment_config()


class TestActionYmlCompatibility:
    """Test that action.yml inputs work correctly with the multi-provider system."""

    def test_action_input_mapping(self):
        """Test that action inputs map correctly to environment variables."""
        # Simulate GitHub Actions environment variable mapping
        action_inputs = {
            'llm-provider': 'vertex',
            'google-cloud-project': 'my-project',
            'google-cloud-region': 'us-west1',
            'claude-model': 'claude-3-sonnet-20240229',
            'exclude-directories': 'node_modules,build'
        }
        
        # Convert to environment variables as GitHub Actions would
        env_vars = {
            'LLM_PROVIDER': action_inputs['llm-provider'],
            'GOOGLE_CLOUD_PROJECT': action_inputs['google-cloud-project'],
            'GOOGLE_CLOUD_REGION': action_inputs['google-cloud-region'],
            'CLAUDE_MODEL': action_inputs['claude-model'],
            'EXCLUDE_DIRECTORIES': action_inputs['exclude-directories'],
            'ENABLE_CLAUDE_FILTERING': 'true'
        }
        
        with patch.dict(os.environ, env_vars):
            with patch('claudecode.vertex_client.AnthropicVertex'):
                findings_filter = initialize_findings_filter()
                
                assert findings_filter.claude_client.provider_name == "vertex"

    def test_backward_compatibility(self):
        """Test that old action.yml configurations still work."""
        # Old-style configuration (pre-multi-provider)
        old_env = {
            'ANTHROPIC_API_KEY': 'test-key',
            'CLAUDE_MODEL': 'claude-3-sonnet-20240229',
            'ENABLE_CLAUDE_FILTERING': 'true'
            # No LLM_PROVIDER set - should default to anthropic
        }
        
        with patch.dict(os.environ, old_env, clear=True):
            with patch('claudecode.anthropic_client.Anthropic'):
                findings_filter = initialize_findings_filter()
                
                assert findings_filter.claude_client.provider_name == "anthropic"

    @patch('claudecode.github_action_audit.GitHubActionClient')
    @patch('claudecode.github_action_audit.SimpleClaudeRunner')
    def test_client_initialization_compatibility(self, mock_claude_runner, mock_github_client):
        """Test that client initialization works with all providers."""
        mock_github_client.return_value = MagicMock()
        mock_claude_runner.return_value = MagicMock()
        
        github_client, claude_runner = initialize_clients()
        
        assert github_client is not None
        assert claude_runner is not None
        mock_github_client.assert_called_once()
        mock_claude_runner.assert_called_once()


class TestProviderValidation:
    """Test provider validation and error handling."""

    def test_provider_validation_script(self):
        """Test the provider validation logic from action.yml script."""
        valid_providers = ['anthropic', 'vertex', 'bedrock']
        invalid_providers = ['openai', 'invalid', '', None]
        
        # Simulate the validation logic from action.yml
        def validate_provider(provider):
            if provider not in ['anthropic', 'vertex', 'bedrock']:
                return False, f"Invalid provider '{provider}'. Must be one of: anthropic, vertex, bedrock"
            return True, ""
        
        # Test valid providers
        for provider in valid_providers:
            is_valid, error = validate_provider(provider)
            assert is_valid, f"Provider {provider} should be valid"
            assert error == ""
        
        # Test invalid providers
        for provider in invalid_providers:
            is_valid, error = validate_provider(provider)
            assert not is_valid, f"Provider {provider} should be invalid"
            assert "Invalid provider" in error

    @patch.dict(os.environ, {
        'LLM_PROVIDER': 'vertex',
        'ENABLE_CLAUDE_FILTERING': 'true'
        # Missing GOOGLE_CLOUD_PROJECT
    })
    def test_missing_required_config(self):
        """Test that missing required configuration is handled gracefully."""
        # Should fall back to disabled filtering or raise appropriate error
        findings_filter = initialize_findings_filter()
        
        # Should either disable filtering or handle the error gracefully
        assert findings_filter is not None

    def test_environment_variable_precedence(self):
        """Test that environment variables take precedence correctly."""
        # Test that LLM_PROVIDER environment variable works
        with patch.dict(os.environ, {
            'LLM_PROVIDER': 'bedrock',
            'AWS_REGION': 'us-west-2',
            'ENABLE_CLAUDE_FILTERING': 'true'
        }):
            with patch('claudecode.bedrock_client.AnthropicBedrock'):
                findings_filter = initialize_findings_filter()
                
                assert findings_filter.claude_client.provider_name == "bedrock"
                assert findings_filter.claude_client.aws_region == "us-west-2"


if __name__ == "__main__":
    pytest.main([__file__])