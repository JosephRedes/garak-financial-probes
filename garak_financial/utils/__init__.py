"""
Secure LLM Client for OpenAI-compatible endpoints.

Security features:
- No credentials in code (environment variables only)
- Request timeout enforcement
- Response size limits
- Input validation
- Structured error handling
- No sensitive data in logs
"""


import logging
import os
from dataclasses import dataclass
from typing import Optional

import httpx

# Configure logging to avoid leaking sensitive data
logger = logging.getLogger(__name__)


@dataclass
class LLMResponse:
    """Structured response from LLM."""
    content: str
    model: str
    usage: dict
    raw_response: Optional[dict] = None


class LLMClientError(Exception):
    """Base exception for LLM client errors."""
    pass


class LLMAuthenticationError(LLMClientError):
    """Authentication failed."""
    pass


class LLMRateLimitError(LLMClientError):
    """Rate limit exceeded."""
    pass


class LLMTimeoutError(LLMClientError):
    """Request timed out."""
    pass


class LLMResponseError(LLMClientError):
    """Invalid or malformed response."""
    pass


class SecureLLMClient:
    """
    Secure client for OpenAI-compatible LLM endpoints.

    Security considerations:
    - API keys loaded from environment only
    - Timeouts prevent hanging connections
    - Response size limits prevent memory exhaustion
    - No sensitive data logged
    """

    # Security limits
    MAX_RESPONSE_SIZE = 1024 * 1024  # 1MB max response
    DEFAULT_TIMEOUT = 60.0  # 60 second timeout
    MAX_RETRIES = 3

    def __init__(
        self,
        base_url: str,
        api_key_env_var: str = "LLM_API_KEY",
        timeout: float = DEFAULT_TIMEOUT,
        max_retries: int = MAX_RETRIES,
    ):
        """
        Initialize secure LLM client.

        Args:
            base_url: API endpoint (e.g., https://api.example.com/v1)
            api_key_env_var: Environment variable name containing API key
            timeout: Request timeout in seconds
            max_retries: Number of retry attempts
        """
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.max_retries = max_retries

        # Load API key from environment (never hardcode!)
        self._api_key = os.environ.get(api_key_env_var)
        if self._api_key:
            logger.debug("API key loaded from environment")
        else:
            logger.warning(
                f"No API key found in {api_key_env_var}. "
                "Proceeding without authentication."
            )

        # Configure HTTP client with security settings
        self._client = httpx.Client(
            timeout=httpx.Timeout(timeout),
            limits=httpx.Limits(
                max_connections=10,
                max_keepalive_connections=5,
            ),
            follow_redirects=False,  # Security: don't follow redirects
        )

    def _get_headers(self) -> dict:
        """Build request headers with authentication."""
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "garak-financial-probes/0.1.0",
        }
        if self._api_key:
            headers["Authorization"] = f"Bearer {self._api_key}"
        return headers

    def _validate_response_size(self, response: httpx.Response) -> None:
        """Validate response size to prevent memory exhaustion."""
        content_length = response.headers.get("content-length")
        if content_length and int(content_length) > self.MAX_RESPONSE_SIZE:
            raise LLMResponseError(
                f"Response too large: {content_length} bytes "
                f"(max: {self.MAX_RESPONSE_SIZE})"
            )

    def chat_completion(
        self,
        messages: list[dict],
        model: str,
        temperature: float = 0.0,
        max_tokens: int = 1024,
        response_format: Optional[dict] = None,
    ) -> LLMResponse:
        """
        Send chat completion request.

        Args:
            messages: List of message dicts with 'role' and 'content'
            model: Model identifier
            temperature: Sampling temperature (0.0 for deterministic)
            max_tokens: Maximum response tokens
            response_format: Optional response format (e.g., {"type": "json_object"})

        Returns:
            LLMResponse with content and metadata

        Raises:
            LLMClientError: On any API error
        """
        # Validate inputs
        if not messages:
            raise ValueError("Messages list cannot be empty")

        for msg in messages:
            if "role" not in msg or "content" not in msg:
                raise ValueError("Each message must have 'role' and 'content'")

        # Build request payload
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        if response_format:
            payload["response_format"] = response_format

        # Make request with retries
        last_error = None
        for attempt in range(self.max_retries):
            try:
                response = self._client.post(
                    f"{self.base_url}/chat/completions",
                    headers=self._get_headers(),
                    json=payload,
                )

                # Handle HTTP errors
                if response.status_code == 401:
                    raise LLMAuthenticationError("Invalid API key")
                elif response.status_code == 429:
                    raise LLMRateLimitError("Rate limit exceeded")
                elif response.status_code >= 500:
                    # Server error - retry
                    logger.warning(f"Server error {response.status_code}, retrying...")
                    continue
                elif response.status_code != 200:
                    raise LLMClientError(
                        f"API error: {response.status_code}"
                    )

                # Validate response size
                self._validate_response_size(response)

                # Parse response
                data = response.json()

                if "choices" not in data or not data["choices"]:
                    raise LLMResponseError("No choices in response")

                content = data["choices"][0].get("message", {}).get("content", "")

                return LLMResponse(
                    content=content,
                    model=data.get("model", model),
                    usage=data.get("usage", {}),
                    raw_response=data,
                )

            except httpx.TimeoutException:
                last_error = LLMTimeoutError(f"Request timed out after {self.timeout}s")
                logger.warning(f"Timeout on attempt {attempt + 1}")
            except httpx.RequestError as e:
                last_error = LLMClientError(f"Request failed: {e}")
                logger.warning(f"Request error on attempt {attempt + 1}")

        raise last_error or LLMClientError("All retry attempts failed")

    def close(self) -> None:
        """Close the HTTP client."""
        self._client.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()


def create_client_from_env() -> SecureLLMClient:
    """
    Create LLM client from environment variables.

    Environment variables:
    - LLM_BASE_URL: API endpoint
    - LLM_API_KEY: API key (optional for some endpoints)
    - LLM_TIMEOUT: Request timeout in seconds (optional)
    """
    base_url = os.environ.get("LLM_BASE_URL")
    if not base_url:
        raise ValueError("LLM_BASE_URL environment variable required")

    timeout = float(os.environ.get("LLM_TIMEOUT", "60"))

    return SecureLLMClient(
        base_url=base_url,
        timeout=timeout,
    )


def mask_url(url: str) -> str:
    """Mask sensitive parts of a URL for display in reports and logs."""
    if "://" in url:
        parts = url.split("/")
        if len(parts) > 3:
            return "/".join(parts[:3]) + "/..."
    return url
