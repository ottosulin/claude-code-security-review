"""Tests for individual LLM client implementations."""

import pytest
from unittest.mock import patch, MagicMock

from claudecode.anthropic_client import AnthropicAPIClient
from claudecode.vertex_client import VertexAIClient
from claudecode.bedrock_client import BedrockClient


class TestAnthropicClient:
    """Test Anthropic API client."""
    
    @patch('claudecode.anthropic_client.Anthropic')
    def test_init_with_api_key(self, mock_anthropic_class):
        """Test initialization with API key."""
        client = AnthropicAPIClient(
            model="claude-3-sonnet-20240229",
            api_key="test-key"
        )
        
        assert client.model == "claude-3-sonnet-20240229"
        assert client.api_key == "test-key"
        assert client.provider_name == "anthropic"
        mock_anthropic_class.assert_called_once_with(api_key="test-key")
    
    def test_init_missing_api_key(self):
        """Test initialization without API key raises error."""
        with patch.dict('os.environ', {}, clear=True):
            with pytest.raises(ValueError, match="No Anthropic API key found"):
                AnthropicAPIClient(model="claude-3-sonnet-20240229")
    
    @patch('claudecode.anthropic_client.Anthropic')
    def test_validate_api_access_success(self, mock_anthropic_class):
        """Test successful API validation."""
        mock_client = MagicMock()
        mock_anthropic_class.return_value = mock_client
        
        client = AnthropicAPIClient(api_key="test-key")
        success, error = client.validate_api_access()
        
        assert success
        assert error == ""
        mock_client.messages.create.assert_called_once()
    
    @patch('claudecode.anthropic_client.Anthropic')
    def test_validate_api_access_failure(self, mock_anthropic_class):
        """Test failed API validation."""
        mock_client = MagicMock()
        mock_client.messages.create.side_effect = Exception("API Error")
        mock_anthropic_class.return_value = mock_client
        
        client = AnthropicAPIClient(api_key="test-key")
        success, error = client.validate_api_access()
        
        assert not success
        assert "API validation failed" in error
    
    @patch('claudecode.anthropic_client.Anthropic')
    def test_call_with_retry_success(self, mock_anthropic_class):
        """Test successful API call."""
        # Setup mock response
        mock_content = MagicMock()
        mock_content.text = "Test response"
        mock_response = MagicMock()
        mock_response.content = [mock_content]
        
        mock_client = MagicMock()
        mock_client.messages.create.return_value = mock_response
        mock_anthropic_class.return_value = mock_client
        
        client = AnthropicAPIClient(api_key="test-key")
        success, response, error = client.call_with_retry("Test prompt")
        
        assert success
        assert response == "Test response"
        assert error == ""
    
    @patch('claudecode.anthropic_client.Anthropic')
    def test_call_with_retry_failure(self, mock_anthropic_class):
        """Test failed API call with retries."""
        mock_client = MagicMock()
        mock_client.messages.create.side_effect = Exception("API Error")
        mock_anthropic_class.return_value = mock_client
        
        client = AnthropicAPIClient(api_key="test-key", max_retries=1)
        success, response, error = client.call_with_retry("Test prompt")
        
        assert not success
        assert response == ""
        assert "API call failed after" in error


class TestVertexAIClient:
    """Test Vertex AI client."""
    
    @patch('claudecode.vertex_client.AnthropicVertex')
    def test_init_with_project(self, mock_vertex_class):
        """Test initialization with project ID."""
        client = VertexAIClient(
            model="claude-3-sonnet-20240229",
            project_id="test-project",
            region="us-central1"
        )
        
        assert client.original_model == "claude-3-sonnet-20240229"
        assert client.model == "claude-3-sonnet@20240229"  # Converted format
        assert client.project_id == "test-project"
        assert client.region == "us-central1"
        assert client.provider_name == "vertex"
        mock_vertex_class.assert_called_once_with(
            region="us-central1",
            project_id="test-project"
        )
    
    def test_init_missing_project(self):
        """Test initialization without project ID raises error."""
        with patch.dict('os.environ', {}, clear=True):
            with pytest.raises(ValueError, match="No Google Cloud project ID found"):
                VertexAIClient(model="claude-3-sonnet-20240229")
    
    def test_convert_model_name(self):
        """Test model name conversion to Vertex AI format."""
        with patch('claudecode.vertex_client.AnthropicVertex'):
            client = VertexAIClient(
                model="claude-opus-4-20250514",
                project_id="test-project"
            )
            
            assert client.model == "claude-opus-4@20250514"
    
    def test_convert_model_name_v2(self):
        """Test model name conversion for v2 models."""
        with patch('claudecode.vertex_client.AnthropicVertex'):
            client = VertexAIClient(
                model="claude-3-5-sonnet-v2-20241022",
                project_id="test-project"
            )
            
            # Should convert to claude-3-5-sonnet@20241022 (removes v2)
            assert client.model == "claude-3-5-sonnet@20241022"


class TestBedrockClient:
    """Test Bedrock client."""
    
    @patch('claudecode.bedrock_client.AnthropicBedrock')
    def test_init_with_region(self, mock_bedrock_class):
        """Test initialization with AWS region."""
        client = BedrockClient(
            model="claude-3-sonnet-20240229",
            aws_region="us-west-2"
        )
        
        assert client.original_model == "claude-3-sonnet-20240229"
        assert client.model == "anthropic.claude-3-sonnet-20240229-v1:0"  # Converted format
        assert client.aws_region == "us-west-2"
        assert client.provider_name == "bedrock"
        mock_bedrock_class.assert_called_once_with(aws_region="us-west-2")
    
    def test_convert_model_name(self):
        """Test model name conversion to Bedrock format."""
        with patch('claudecode.bedrock_client.AnthropicBedrock'):
            client = BedrockClient(
                model="claude-opus-4-20250514",
                aws_region="us-east-1"
            )
            
            assert client.model == "anthropic.claude-opus-4-20250514-v1:0"
    
    def test_convert_model_name_v2(self):
        """Test model name conversion for v2 models."""
        with patch('claudecode.bedrock_client.AnthropicBedrock'):
            client = BedrockClient(
                model="claude-3-5-sonnet-v2-20241022",
                aws_region="us-east-1"
            )
            
            # Should convert to anthropic.claude-3-5-sonnet-20241022-v2:0
            assert client.model == "anthropic.claude-3-5-sonnet-20241022-v2:0"
    
    def test_convert_model_name_already_formatted(self):
        """Test model name conversion when already in Bedrock format."""
        with patch('claudecode.bedrock_client.AnthropicBedrock'):
            client = BedrockClient(
                model="anthropic.claude-3-sonnet-20240229-v1:0",
                aws_region="us-east-1"
            )
            
            # Should remain unchanged
            assert client.model == "anthropic.claude-3-sonnet-20240229-v1:0"


class TestClientInterfaces:
    """Test that all clients implement the same interface."""
    
    @patch('claudecode.anthropic_client.Anthropic')
    @patch('claudecode.vertex_client.AnthropicVertex')
    @patch('claudecode.bedrock_client.AnthropicBedrock')
    def test_all_clients_implement_interface(self, mock_bedrock, mock_vertex, mock_anthropic):
        """Test that all clients implement the same methods."""
        clients = [
            AnthropicAPIClient(api_key="test-key"),
            VertexAIClient(project_id="test-project"),
            BedrockClient(aws_region="us-east-1")
        ]
        
        for client in clients:
            # Check all required methods exist
            assert hasattr(client, 'validate_api_access')
            assert hasattr(client, 'call_with_retry')
            assert hasattr(client, 'analyze_single_finding')
            assert hasattr(client, 'provider_name')
            
            # Check methods are callable
            assert callable(client.validate_api_access)
            assert callable(client.call_with_retry)
            assert callable(client.analyze_single_finding)
            
            # Check provider_name returns string
            assert isinstance(client.provider_name, str)
    
    @patch('claudecode.anthropic_client.Anthropic')
    @patch('claudecode.vertex_client.AnthropicVertex')
    @patch('claudecode.bedrock_client.AnthropicBedrock')
    def test_analyze_single_finding_interface(self, mock_bedrock, mock_vertex, mock_anthropic):
        """Test that analyze_single_finding has consistent interface across clients."""
        clients = [
            AnthropicAPIClient(api_key="test-key"),
            VertexAIClient(project_id="test-project"),
            BedrockClient(aws_region="us-east-1")
        ]
        
        test_finding = {
            "file": "test.py",
            "line": 10,
            "severity": "HIGH",
            "description": "Test finding"
        }
        
        test_context = {
            "repo_name": "test/repo",
            "pr_number": 123
        }
        
        for client in clients:
            # Mock the internal API calls to avoid actual network requests
            with patch.object(client, 'call_with_retry') as mock_call:
                mock_call.return_value = (True, '{"keep_finding": true, "confidence_score": 8}', "")
                
                with patch.object(client, '_read_file') as mock_read:
                    mock_read.return_value = (True, "test content", "")
                    
                    # Test method signature is consistent
                    success, result, error = client.analyze_single_finding(
                        finding=test_finding,
                        pr_context=test_context,
                        custom_filtering_instructions="test instructions"
                    )
                    
                    # Check return types
                    assert isinstance(success, bool)
                    assert isinstance(result, dict)
                    assert isinstance(error, str)


if __name__ == "__main__":
    pytest.main([__file__])