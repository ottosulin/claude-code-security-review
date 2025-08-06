"""Claude API client for direct Anthropic API calls.

This module provides backward compatibility by importing the new Anthropic client implementation.
"""

from claudecode.anthropic_client import AnthropicAPIClient, get_claude_api_client

# Maintain backward compatibility with the original class name
ClaudeAPIClient = AnthropicAPIClient

# Re-export the convenience function
__all__ = ['ClaudeAPIClient', 'get_claude_api_client']


