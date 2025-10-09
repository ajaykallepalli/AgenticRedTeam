"""Target LLM interface using LiteLLM for universal API support."""

from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field
import litellm
from litellm import completion, acompletion
import asyncio


class Message(BaseModel):
    """Chat message."""
    role: str = Field(..., description="Role: system, user, or assistant")
    content: str = Field(..., description="Message content")


class LLMResponse(BaseModel):
    """Response from LLM."""
    content: str = Field(..., description="Response content")
    model: str = Field(..., description="Model name")
    tokens_used: Optional[int] = Field(None, description="Total tokens used")
    finish_reason: Optional[str] = Field(None, description="Finish reason")


class LLMTarget:
    """Universal LLM target using LiteLLM.

    Supports OpenAI, Anthropic, Google, Azure, and more via unified interface.
    """

    def __init__(
        self,
        model: str,
        provider: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 500,
        **kwargs
    ):
        """Initialize LLM target.

        Args:
            model: Model name (e.g., "gpt-4", "claude-3-5-sonnet-20241022")
            provider: Optional provider prefix (e.g., "openai/", "anthropic/")
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            **kwargs: Additional parameters for litellm
        """
        self.model = f"{provider}/{model}" if provider else model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.kwargs = kwargs

        # Set litellm configuration
        litellm.drop_params = True  # Drop unsupported params instead of erroring
        litellm.set_verbose = False  # Disable verbose logging

    def chat(
        self,
        messages: List[Message],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        """Send chat messages to target LLM (synchronous).

        Args:
            messages: List of chat messages
            temperature: Override default temperature
            max_tokens: Override default max tokens

        Returns:
            LLMResponse object
        """
        messages_dict = [{"role": msg.role, "content": msg.content} for msg in messages]

        response = completion(
            model=self.model,
            messages=messages_dict,
            temperature=temperature or self.temperature,
            max_tokens=max_tokens or self.max_tokens,
            **self.kwargs
        )

        return LLMResponse(
            content=response.choices[0].message.content,
            model=response.model,
            tokens_used=response.usage.total_tokens if hasattr(response, 'usage') else None,
            finish_reason=response.choices[0].finish_reason
        )

    async def achat(
        self,
        messages: List[Message],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        """Send chat messages to target LLM (asynchronous).

        Args:
            messages: List of chat messages
            temperature: Override default temperature
            max_tokens: Override default max tokens

        Returns:
            LLMResponse object
        """
        messages_dict = [{"role": msg.role, "content": msg.content} for msg in messages]

        response = await acompletion(
            model=self.model,
            messages=messages_dict,
            temperature=temperature or self.temperature,
            max_tokens=max_tokens or self.max_tokens,
            **self.kwargs
        )

        return LLMResponse(
            content=response.choices[0].message.content,
            model=response.model,
            tokens_used=response.usage.total_tokens if hasattr(response, 'usage') else None,
            finish_reason=response.choices[0].finish_reason
        )

    def simple_query(self, prompt: str) -> str:
        """Simple query with single user message.

        Args:
            prompt: User prompt

        Returns:
            Response content as string
        """
        messages = [Message(role="user", content=prompt)]
        response = self.chat(messages)
        return response.content

    async def asimple_query(self, prompt: str) -> str:
        """Async simple query with single user message.

        Args:
            prompt: User prompt

        Returns:
            Response content as string
        """
        messages = [Message(role="user", content=prompt)]
        response = await self.achat(messages)
        return response.content
