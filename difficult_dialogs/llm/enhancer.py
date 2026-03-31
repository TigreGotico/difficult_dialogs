"""LLM-powered response enhancer for natural language generation."""
from __future__ import annotations

from difficult_dialogs.llm.client import LLMClient


class LLMEnhancer:
    """Enhances pre-written arguments with natural LLM phrasing.
    
    Unlike the generator (which creates arguments), the enhancer
    rephrases existing approved content at runtime for variety.
    
    Args:
        base_url: URL of OpenAI-compatible LLM server
        model: Model name to use
    
    Example:
        >>> enhancer = LLMEnhancer("http://192.168.1.200:8000", "qwen-72b")
        >>> enhanced = enhancer.rephrase("Computers process information")
        >>> print(enhanced)
        "At their core, computers are designed to handle and manipulate data"
    """
    
    def __init__(
        self,
        base_url: str,
        model: str | None = None
    ) -> None:
        self.client = LLMClient(base_url, model, timeout=30.0)
        self._cache: dict[str, str] = {}
    
    def rephrase(
        self,
        text: str,
        context: str | None = None,
        style: str = "conversational"
    ) -> str:
        """Rephrase text while preserving meaning.
        
        Args:
            text: Original text to rephrase
            context: Optional context about the conversation
            style: One of "conversational", "formal", "friendly", "academic"
        
        Returns:
            Rephrased text, or original if enhancement fails
        """
        # Check cache first
        cache_key = f"{text}:{context}:{style}"
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        styles = {
            "conversational": "casual, like talking to a friend",
            "formal": "professional and precise",
            "friendly": "warm and approachable",
            "academic": "scholarly and well-reasoned"
        }
        
        style_desc = styles.get(style, styles["conversational"])
        
        system_prompt = """You are rephrasing pre-approved debate statements.
CRITICAL RULES:
- Preserve the exact meaning - do not change the claim
- Do not add new information or arguments
- Do not contradict the original statement
- Just say it differently using different words
- Keep similar length
- Sound natural and human"""

        context_str = f"\nContext: {context}" if context else ""
        
        prompt = f"""Rephrase this statement in a {style_desc} way{context_str}:

Original: "{text}"

Provide ONLY the rephrased version, no quotes, no explanations."""

        try:
            response = self.client.generate(
                prompt=prompt,
                system_prompt=system_prompt,
                temperature=0.8,  # Higher for variety
                max_tokens=256
            )
            
            enhanced = response.text.strip()
            
            # Sanity check: don't return if it's wildly different
            if self._is_too_different(text, enhanced):
                return text
            
            # Cache result
            self._cache[cache_key] = enhanced
            return enhanced
            
        except Exception:
            # Fall back to original on any error
            return text
    
    def explain(
        self,
        concept: str,
        question_type: str = "why"
    ) -> str | None:
        """Generate an explanation for a concept.
        
        Args:
            concept: The concept to explain
            question_type: One of "what", "why", "how", "when", "where"
        
        Returns:
            Explanation text, or None if generation fails
        """
        system_prompt = f"""You are providing brief explanations in a debate.
Keep your answer under 2 sentences.
Be clear and factual.
Do not introduce new claims, just explain what's already established."""

        prompt = f"In a debate, someone asks '{question_type}?' about: {concept}\n\nProvide a brief, clear explanation."

        try:
            response = self.client.generate(
                prompt=prompt,
                system_prompt=system_prompt,
                temperature=0.5,
                max_tokens=128
            )
            return response.text.strip()
        except Exception:
            return None
    
    def summarize_exchange(
        self,
        user_statements: list[str],
        bot_statements: list[str]
    ) -> str:
        """Summarize the debate exchange so far.
        
        Args:
            user_statements: What the user has said/asked
            bot_statements: What the bot has presented
        
        Returns:
            Brief summary paragraph
        """
        system_prompt = """Summarize this debate exchange neutrally.
Focus on what was discussed, not who was right.
Keep it under 3 sentences."""

        prompt = f"""Summarize this debate:

User said: {"; ".join(user_statements[-3:])}
Bot presented: {"; ".join(bot_statements[-3:])}

Provide a neutral 1-2 sentence summary."""

        try:
            response = self.client.generate(
                prompt=prompt,
                system_prompt=system_prompt,
                temperature=0.3,
                max_tokens=128
            )
            return response.text.strip()
        except Exception:
            return ""
    
    def _is_too_different(self, original: str, enhanced: str) -> bool:
        """Check if enhanced text deviates too much from original."""
        # Simple heuristic: word overlap
        orig_words = set(original.lower().split())
        enh_words = set(enhanced.lower().split())
        
        if not orig_words or not enh_words:
            return True
        
        overlap = len(orig_words & enh_words) / min(len(orig_words), len(enh_words))
        
        # Less than 30% word overlap = too different
        return overlap < 0.3
    
    def clear_cache(self) -> None:
        """Clear the rephrasing cache."""
        self._cache.clear()
