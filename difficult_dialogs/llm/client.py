"""Simple HTTP client for OpenAI-compatible LLM APIs."""
from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError


@dataclass
class LLMResponse:
    """Response from an LLM API."""
    text: str
    model: str
    usage: dict[str, int] | None = None


class LLMClient:
    """HTTP client for OpenAI-compatible APIs (Llama.cpp, Ollama, etc.).
    
    Args:
        base_url: Base URL of the LLM server (e.g., "http://localhost:8000")
        model: Model name to use (optional, server may have default)
        timeout: Request timeout in seconds
    
    Example:
        >>> client = LLMClient("http://192.168.1.200:8000", model="qwen-72b")
        >>> response = client.generate("Explain quantum computing")
        >>> print(response.text)
    """
    
    def __init__(
        self,
        base_url: str,
        model: str | None = None,
        timeout: float = 120.0
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = timeout
    
    def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        stop: list[str] | None = None
    ) -> LLMResponse:
        """Generate text from a prompt.
        
        Args:
            prompt: User prompt text
            system_prompt: Optional system instruction
            temperature: Sampling temperature (0.0-1.0)
            max_tokens: Maximum tokens to generate
            stop: Stop sequences
        
        Returns:
            LLMResponse with generated text
        
        Raises:
            URLError: If server is unreachable
            HTTPError: If server returns an error
        """
        messages = []
        
        if system_prompt:
            messages.append({
                "role": "system",
                "content": system_prompt
            })
        
        messages.append({
            "role": "user",
            "content": prompt
        })
        
        payload = {
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": False
        }
        
        if self.model:
            payload["model"] = self.model
        
        if stop:
            payload["stop"] = stop
        
        url = f"{self.base_url}/v1/chat/completions"
        
        request = Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        
        with urlopen(request, timeout=self.timeout) as response:
            data = json.loads(response.read().decode("utf-8"))
        
        return LLMResponse(
            text=data["choices"][0]["message"]["content"],
            model=data.get("model", self.model or "unknown"),
            usage=data.get("usage")
        )
    
    def generate_json(
        self,
        prompt: str,
        system_prompt: str | None = None,
        schema: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Generate structured JSON output.
        
        Args:
            prompt: User prompt describing desired JSON
            system_prompt: Optional system instruction
            schema: Optional JSON schema hint
        
        Returns:
            Parsed JSON object
        
        Raises:
            ValueError: If response is not valid JSON
        """
        if schema:
            system_instruction = (
                f"{system_prompt or ''}\n\n"
                f"Respond ONLY with valid JSON matching this schema:\n"
                f"{json.dumps(schema, indent=2)}\n\n"
                f"Do not include any other text."
            )
        else:
            system_instruction = (
                f"{system_prompt or ''}\n\n"
                f"Respond ONLY with valid JSON. No other text."
            )
        
        response = self.generate(
            prompt=prompt,
            system_prompt=system_instruction.strip(),
            temperature=0.1  # Low temperature for deterministic JSON
        )
        
        # Strip markdown code fences that many models add around JSON.
        # Handles: ```json\n...\n``` , ```\n...\n``` , and bare JSON.
        text = response.text.strip()
        if text.startswith("```"):
            # Remove opening fence line (``` or ```json or ```python etc.)
            first_newline = text.find("\n")
            if first_newline != -1:
                text = text[first_newline + 1:]
            # Remove closing fence
            if text.rstrip().endswith("```"):
                text = text.rstrip()[:-3]

        try:
            return json.loads(text.strip())
        except json.JSONDecodeError as e:
            raise ValueError(f"LLM returned invalid JSON: {text[:200]}") from e
    
    def health_check(self) -> bool:
        """Check if the LLM server is reachable.
        
        Returns:
            True if server responds, False otherwise
        """
        try:
            url = f"{self.base_url}/health"
            request = Request(url, method="GET")
            with urlopen(request, timeout=5.0) as response:
                return response.status == 200
        except (URLError, HTTPError, TimeoutError):
            # Try alternative endpoint
            try:
                url = f"{self.base_url}/v1/models"
                request = Request(url, method="GET")
                with urlopen(request, timeout=5.0) as response:
                    return response.status == 200
            except (URLError, HTTPError, TimeoutError):
                return False
