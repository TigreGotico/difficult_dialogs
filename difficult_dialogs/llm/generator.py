"""LLM-powered argument generator."""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from difficult_dialogs.arguments import Argument
from difficult_dialogs.premises import Premise
from difficult_dialogs.llm.client import LLMClient


class ArgumentGenerator:
    """Generates structured arguments using an LLM.
    
    Args:
        base_url: URL of OpenAI-compatible LLM server
        model: Model name to use
        timeout: Request timeout in seconds
    
    Example:
        >>> gen = ArgumentGenerator("http://192.168.1.200:8000", "qwen-72b")
        >>> arg = gen.generate("Remote work increases productivity")
        >>> arg.save("arguments/remote_work")
    """
    
    def __init__(
        self,
        base_url: str,
        model: str | None = None,
        timeout: float = 300.0
    ) -> None:
        self.client = LLMClient(base_url, model, timeout)
    
    def generate(
        self,
        topic: str,
        stance: str = "pro",
        depth: int = 2,
        include_sources: bool = True,
        include_counterarguments: bool = True,
        language: str = "en"
    ) -> Argument:
        """Generate a complete argument structure.
        
        Args:
            topic: The topic to argue about
            stance: "pro" or "con"
            depth: Number of premise levels (1=simple, 3=complex)
            include_sources: Whether to generate source URLs
            include_counterarguments: Whether to anticipate objections
            language: Language code for generated content
        
        Returns:
            Generated Argument ready to save
        
        Raises:
            RuntimeError: If LLM server is unreachable
        """
        # Check server health
        if not self.client.health_check():
            raise RuntimeError(
                f"LLM server at {self.client.base_url} is not responding"
            )
        
        # Generate argument structure
        structure = self._generate_structure(
            topic, stance, depth, language
        )
        
        # Create argument
        arg = Argument(
            name=self._slugify(topic),
            intro=structure["intro"],
            conclusion=structure["conclusion"]
        )
        
        # Generate premises
        for premise_data in structure["premises"]:
            premise = self._generate_premise(
                premise_data,
                include_sources,
                include_counterarguments
            )
            arg.add_premise(premise)
        
        return arg
    
    def _generate_structure(
        self,
        topic: str,
        stance: str,
        depth: int,
        language: str
    ) -> dict[str, Any]:
        """Generate the high-level argument structure."""
        stance_text = "in favor of" if stance == "pro" else "against"
        
        system_prompt = f"""You are an expert argument architect. Your task is to create structured debate outlines.

Respond with JSON matching this exact schema:
{{
  "intro": "string - opening statement to introduce the topic",
  "conclusion": "string - final concluding statement",
  "premises": [
    {{
      "name": "string - snake_case identifier",
      "description": "string - the main claim",
      "statements": ["string - supporting statements"],
      "sub_premises": []  // nested premises if depth > 1
    }}
  ]
}}

Rules:
- Keep statements concise and factual
- Use logical progression
- Avoid emotional language
- Each premise should be independently verifiable"""

        prompt = f"""Create a structured argument outline.

Topic: {topic}
Stance: Argue {stance_text} this position
Complexity: {depth} levels of premises
Language: {language}

Generate a complete argument structure with:
1. An engaging introduction
2. {2 ** depth} main premises (each with 2-4 supporting statements)
3. A strong conclusion

Return ONLY valid JSON, no other text."""

        response = self.client.generate_json(
            prompt=prompt,
            system_prompt=system_prompt
        )
        
        return response
    
    def _generate_premise(
        self,
        premise_data: dict[str, Any],
        include_sources: bool,
        include_counterarguments: bool
    ) -> Premise:
        """Generate a single premise with support and sources."""
        name = premise_data.get("name", "premise")
        description = premise_data.get("description", "")
        statements = premise_data.get("statements", [])
        
        premise = Premise(name=name, description=description)
        
        # Add statements
        for stmt in statements:
            premise.add_statement(str(stmt))
        
        # Generate support arguments
        if include_counterarguments:
            support = self._generate_support(
                premise_data["description"],
                statements
            )
            for s in support:
                premise.add_support(s)
        
        # Generate sources
        if include_sources:
            sources = self._generate_sources(
                premise_data["description"],
                statements
            )
            for src in sources:
                premise.add_source(src)
        
        # Generate Five Ws explanations
        ws = self._generate_explanations(
            premise_data["description"],
            statements
        )
        
        for key, adder in (
            ("what", premise.add_what),
            ("why", premise.add_why),
            ("how", premise.add_how),
            ("when", premise.add_when),
            ("where", premise.add_where),
        ):
            if key in ws and ws[key]:
                adder(ws[key])

        return premise
    
    def _generate_support(
        self,
        claim: str,
        statements: list[str]
    ) -> list[str]:
        """Generate support arguments for when user disagrees."""
        system_prompt = """You are generating support arguments for a debate bot.
When a user disagrees with a claim, you need fallback arguments to persuade them.

Respond with JSON: {"support": ["argument1", "argument2", "argument3"]}

Rules:
- Provide 3-5 distinct supporting arguments
- Use different angles: logic, evidence, analogy, consequences
- Keep each under 2 sentences
- Be persuasive but factual"""

        prompt = f"""Generate support arguments for this claim:

Claim: {claim}
Supporting facts: {"; ".join(statements)}

Provide 3-5 fallback arguments to use when someone disagrees."""

        try:
            response = self.client.generate_json(
                prompt=prompt,
                system_prompt=system_prompt
            )
            return response.get("support", [])
        except Exception:
            return []
    
    def _generate_sources(
        self,
        claim: str,
        statements: list[str]
    ) -> list[str]:
        """Generate source citations for the claim."""
        system_prompt = """You are generating source citations for a debate bot.

Respond with JSON: {"sources": ["url1", "url2", "url3"]}

Rules:
- Provide 2-4 authoritative sources
- Prefer .gov, .edu, Wikipedia, major news outlets
- Sources must be real, verifiable URLs
- Do NOT invent fake URLs"""

        prompt = f"""Suggest authoritative sources for this claim:

Claim: {claim}
Supporting facts: {"; ".join(statements)}

List 2-4 real URLs where users can verify this information.
If you're unsure of exact URLs, suggest general reference pages."""

        try:
            response = self.client.generate_json(
                prompt=prompt,
                system_prompt=system_prompt
            )
            return response.get("sources", [])
        except Exception:
            return []
    
    def _generate_explanations(
        self,
        claim: str,
        statements: list[str]
    ) -> dict[str, str]:
        """Generate all Five-Ws explanations (what/why/how/when/where).

        Each field is kept to 1-2 sentences so the response stays small
        and within reach of smaller models.

        Args:
            claim: The premise claim being explained.
            statements: Supporting statements that provide context.

        Returns:
            Dict with keys what/why/how/when/where; missing keys on failure.
        """
        system_prompt = """You are generating Five-Ws explanations for a debate bot.

Respond with JSON:
{
  "what": "what this claim means in plain terms",
  "why": "why this claim is true or important",
  "how": "how this works or how we know it",
  "when": "when this applies or became relevant",
  "where": "where this is observed or documented"
}

Keep each value under 2 sentences. Be clear and concise. All five keys are required."""

        prompt = f"""Explain this claim using the Five Ws:

Claim: {claim}
Context: {"; ".join(statements)}

Provide a one- or two-sentence answer for each of: what, why, how, when, where."""

        try:
            return self.client.generate_json(
                prompt=prompt,
                system_prompt=system_prompt
            )
        except Exception:
            return {}
    
    @staticmethod
    def _slugify(text: str) -> str:
        """Convert text to a filesystem-safe slug."""
        # Lowercase
        text = text.lower()
        # Replace spaces with underscores
        text = text.replace(" ", "_")
        # Remove special characters
        text = re.sub(r"[^a-z0-9_]", "", text)
        # Remove multiple underscores
        text = re.sub(r"_+", "_", text)
        # Trim underscores
        return text.strip("_")
