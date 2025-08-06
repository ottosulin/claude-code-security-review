"""Abstract base class for Large Language Model API clients."""

from abc import ABC, abstractmethod
from typing import Dict, Any, Tuple, Optional
from enum import Enum


class CloudProvider(Enum):
    """Supported cloud providers for LLM APIs."""
    ANTHROPIC = "anthropic"
    VERTEX_AI = "vertex"
    BEDROCK = "bedrock"


class LLMAPIClient(ABC):
    """Abstract base class for Large Language Model API clients.
    
    Defines the common interface that all provider-specific clients must implement.
    This allows the system to work with different cloud providers (Anthropic, Vertex AI, Bedrock)
    while maintaining a consistent interface.
    """
    
    def __init__(self, 
                 model: Optional[str] = None,
                 timeout_seconds: Optional[int] = None,
                 max_retries: Optional[int] = None):
        """Initialize the LLM API client.
        
        Args:
            model: Model identifier (will be converted to provider-specific format)
            timeout_seconds: Request timeout in seconds
            max_retries: Maximum retry attempts for API calls
        """
        self.model = model
        self.timeout_seconds = timeout_seconds
        self.max_retries = max_retries
    
    @abstractmethod
    def validate_api_access(self) -> Tuple[bool, str]:
        """Validate that API access is working.
        
        Tests the API credentials and connectivity by making a simple test call.
        
        Returns:
            Tuple of (success, error_message)
            - success: True if API access is valid, False otherwise
            - error_message: Description of error if validation failed, empty string if successful
        """
        pass
    
    @abstractmethod
    def call_with_retry(self, 
                       prompt: str,
                       system_prompt: Optional[str] = None,
                       max_tokens: int = 16384) -> Tuple[bool, str, str]:
        """Make LLM API call with retry logic.
        
        Executes the API call with automatic retry handling for transient failures,
        rate limiting, and timeouts.
        
        Args:
            prompt: User prompt to send to the model
            system_prompt: Optional system prompt to set model behavior
            max_tokens: Maximum tokens to generate in response
            
        Returns:
            Tuple of (success, response_text, error_message)
            - success: True if call succeeded, False otherwise
            - response_text: Generated text response from the model
            - error_message: Description of error if call failed, empty string if successful
        """
        pass
    
    @abstractmethod
    def analyze_single_finding(self, 
                              finding: Dict[str, Any], 
                              pr_context: Optional[Dict[str, Any]] = None,
                              custom_filtering_instructions: Optional[str] = None) -> Tuple[bool, Dict[str, Any], str]:
        """Analyze a single security finding to filter false positives.
        
        Uses the LLM to determine if a security finding is a true positive or false positive,
        providing confidence scoring and justification.
        
        Args:
            finding: Single security finding dictionary to analyze
            pr_context: Optional PR context for better analysis (repo, PR number, title, etc.)
            custom_filtering_instructions: Optional custom filtering rules to apply
            
        Returns:
            Tuple of (success, analysis_result, error_message)
            - success: True if analysis completed, False otherwise
            - analysis_result: Dictionary containing:
                - confidence_score: Float from 1-10
                - keep_finding: Boolean whether to keep the finding
                - exclusion_reason: String reason if excluded
                - justification: String explanation of the decision
            - error_message: Description of error if analysis failed, empty string if successful
        """
        pass
    
    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Get the name of the cloud provider.
        
        Returns:
            String identifier for the provider (e.g., "anthropic", "vertex", "bedrock")
        """
        pass