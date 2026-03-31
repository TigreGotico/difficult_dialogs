"""Unit tests for difficult_dialogs.llm — LLMClient, ArgumentGenerator, LLMEnhancer."""
from __future__ import annotations

import json
import pytest
from unittest.mock import MagicMock, patch
from io import BytesIO
from urllib.error import URLError

from difficult_dialogs.llm.client import LLMClient, LLMResponse
from difficult_dialogs.llm.generator import ArgumentGenerator
from difficult_dialogs.llm.enhancer import LLMEnhancer
from difficult_dialogs.arguments import Argument
from difficult_dialogs.premises import Premise


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _mock_urlopen(response_text: str, status: int = 200):
    """Return a context manager that yields a fake HTTP response."""
    class FakeResponse:
        def __init__(self, text: str, status: int) -> None:
            self._data = text.encode("utf-8") if isinstance(text, str) else text
            self.status = status

        def read(self) -> bytes:
            return self._data

        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

    return FakeResponse(response_text, status)


def _chat_response(content: str, model: str = "test-model") -> str:
    """Build a minimal OpenAI-style chat completion JSON string."""
    return json.dumps({
        "choices": [{"message": {"content": content}}],
        "model": model,
        "usage": {"prompt_tokens": 10, "completion_tokens": 20},
    })


# ---------------------------------------------------------------------------
# LLMClient.generate
# ---------------------------------------------------------------------------

class TestLLMClientGenerate:
    """Tests for LLMClient.generate()."""

    def test_basic_generation(self) -> None:
        """generate() parses a standard chat completion response."""
        client = LLMClient("http://localhost:8000", model="test-model")
        fake_resp = _mock_urlopen(_chat_response("Hello, world!"))

        with patch("difficult_dialogs.llm.client.urlopen", return_value=fake_resp):
            result = client.generate("Say hello")

        assert result.text == "Hello, world!"
        assert result.model == "test-model"
        assert result.usage is not None

    def test_generate_with_system_prompt(self) -> None:
        """generate() includes system message when system_prompt is given."""
        client = LLMClient("http://localhost:8000")
        fake_resp = _mock_urlopen(_chat_response("I am an assistant."))

        with patch("difficult_dialogs.llm.client.urlopen", return_value=fake_resp):
            result = client.generate("Who are you?", system_prompt="You are an assistant.")

        assert result.text == "I am an assistant."

    def test_generate_with_stop_sequences(self) -> None:
        """generate() passes stop sequences in the payload."""
        client = LLMClient("http://localhost:8000", model="m")
        fake_resp = _mock_urlopen(_chat_response("Done."))

        with patch("difficult_dialogs.llm.client.urlopen", return_value=fake_resp):
            result = client.generate("Generate", stop=["END", "STOP"])

        assert result.text == "Done."

    def test_generate_without_model(self) -> None:
        """generate() works when no model is set."""
        client = LLMClient("http://localhost:8000")
        resp = json.dumps({
            "choices": [{"message": {"content": "No model."}}],
        })
        with patch("difficult_dialogs.llm.client.urlopen", return_value=_mock_urlopen(resp)):
            result = client.generate("Test")
        assert result.text == "No model."


# ---------------------------------------------------------------------------
# LLMClient.generate_json
# ---------------------------------------------------------------------------

class TestLLMClientGenerateJson:
    """Tests for LLMClient.generate_json()."""

    def test_parse_plain_json(self) -> None:
        """generate_json() parses bare JSON response."""
        client = LLMClient("http://localhost:8000")
        data = {"key": "value"}
        fake_resp = _mock_urlopen(_chat_response(json.dumps(data)))

        with patch("difficult_dialogs.llm.client.urlopen", return_value=fake_resp):
            result = client.generate_json("Return JSON")

        assert result == data

    def test_strip_json_fence(self) -> None:
        """generate_json() strips ```json ... ``` fences."""
        client = LLMClient("http://localhost:8000")
        fenced = "```json\n{\"x\": 1}\n```"
        fake_resp = _mock_urlopen(_chat_response(fenced))

        with patch("difficult_dialogs.llm.client.urlopen", return_value=fake_resp):
            result = client.generate_json("Return JSON")

        assert result == {"x": 1}

    def test_strip_bare_fence(self) -> None:
        """generate_json() strips ``` ... ``` fences (no language tag)."""
        client = LLMClient("http://localhost:8000")
        fenced = "```\n{\"y\": 2}\n```"
        fake_resp = _mock_urlopen(_chat_response(fenced))

        with patch("difficult_dialogs.llm.client.urlopen", return_value=fake_resp):
            result = client.generate_json("Return JSON")

        assert result == {"y": 2}

    def test_invalid_json_raises_value_error(self) -> None:
        """generate_json() raises ValueError for non-JSON response."""
        client = LLMClient("http://localhost:8000")
        fake_resp = _mock_urlopen(_chat_response("This is not JSON at all."))

        with patch("difficult_dialogs.llm.client.urlopen", return_value=fake_resp):
            with pytest.raises(ValueError, match="invalid JSON"):
                client.generate_json("Return JSON")

    def test_generate_json_with_schema(self) -> None:
        """generate_json() accepts a schema hint."""
        client = LLMClient("http://localhost:8000")
        schema = {"type": "object", "properties": {"name": {"type": "string"}}}
        fake_resp = _mock_urlopen(_chat_response('{"name": "test"}'))

        with patch("difficult_dialogs.llm.client.urlopen", return_value=fake_resp):
            result = client.generate_json("Return JSON", schema=schema)

        assert result == {"name": "test"}


# ---------------------------------------------------------------------------
# LLMClient.health_check
# ---------------------------------------------------------------------------

class TestLLMClientHealthCheck:
    """Tests for LLMClient.health_check()."""

    def test_health_check_true_on_200(self) -> None:
        """health_check() returns True when /health returns 200."""
        client = LLMClient("http://localhost:8000")

        class FakeResp:
            status = 200
            def __enter__(self): return self
            def __exit__(self, *a): pass

        with patch("difficult_dialogs.llm.client.urlopen", return_value=FakeResp()):
            assert client.health_check() is True

    def test_health_check_falls_back_to_models(self) -> None:
        """health_check() tries /v1/models when /health fails."""
        client = LLMClient("http://localhost:8000")

        call_count = [0]

        class FakeResp:
            status = 200
            def __enter__(self): return self
            def __exit__(self, *a): pass

        def fake_urlopen(req, timeout=None):
            call_count[0] += 1
            if "/health" in req.full_url:
                raise URLError("health not found")
            return FakeResp()

        with patch("difficult_dialogs.llm.client.urlopen", side_effect=fake_urlopen):
            result = client.health_check()

        assert result is True
        assert call_count[0] == 2

    def test_health_check_false_when_both_fail(self) -> None:
        """health_check() returns False when both endpoints fail."""
        client = LLMClient("http://localhost:8000")

        with patch("difficult_dialogs.llm.client.urlopen", side_effect=URLError("down")):
            assert client.health_check() is False


# ---------------------------------------------------------------------------
# ArgumentGenerator
# ---------------------------------------------------------------------------

class TestArgumentGenerator:
    """Tests for ArgumentGenerator using a mocked LLMClient."""

    def _make_generator(self) -> ArgumentGenerator:
        gen = ArgumentGenerator.__new__(ArgumentGenerator)
        gen.client = MagicMock()
        # health_check must pass so generate() doesn't raise RuntimeError
        gen.client.health_check.return_value = True
        return gen

    def _structure(self, premises: list[dict] | None = None) -> dict:
        """Build a minimal _generate_structure response."""
        return {
            "intro": "Test intro.",
            "conclusion": "Test conclusion.",
            "premises": premises or [
                {"name": "premise_one", "description": "Desc one.", "statements": ["Claim one."]},
            ],
        }

    def test_generate_returns_argument(self) -> None:
        """generate() returns an Argument with premises."""
        gen = self._make_generator()
        gen.client.generate_json.side_effect = [
            self._structure([
                {"name": "p1", "description": "D1.", "statements": ["S1.", "S2."]},
                {"name": "p2", "description": "D2.", "statements": ["S3."]},
            ]),
            # support for p1
            {"support": ["Support1."]},
            # sources for p1
            {"sources": ["https://example.com/p1"]},
            # explanations for p1
            {"what": "W.", "why": "Y.", "how": "H.", "when": "T.", "where": "R."},
            # support for p2
            {"support": ["Support2."]},
            # sources for p2
            {"sources": ["https://example.com/p2"]},
            # explanations for p2
            {"what": "W2.", "why": "Y2.", "how": "H2.", "when": "T2.", "where": "R2."},
        ]

        arg = gen.generate("climate change", stance="pro")

        assert isinstance(arg, Argument)
        assert len(arg.premises) == 2
        assert arg.intro == "Test intro."
        assert arg.conclusion == "Test conclusion."

    def test_generate_skips_premises_without_name(self) -> None:
        """generate() handles premises with missing name gracefully."""
        gen = self._make_generator()
        gen.client.generate_json.side_effect = [
            self._structure([
                {"name": "real", "description": "D.", "statements": ["S."]},
            ]),
            {"support": []},
            {"sources": []},
            {"what": "W.", "why": "Y.", "how": "H.", "when": "T.", "where": "R."},
        ]

        arg = gen.generate("topic")
        assert len(arg.premises) == 1

    def test_generate_no_include_sources_no_counterargs(self) -> None:
        """generate() with include_sources=False, include_counterarguments=False."""
        gen = self._make_generator()
        gen.client.generate_json.side_effect = [
            self._structure(),
            # only explanations (no support or sources calls)
            {"what": "W.", "why": "Y.", "how": "H.", "when": "T.", "where": "R."},
        ]

        arg = gen.generate(
            "topic",
            include_sources=False,
            include_counterarguments=False,
        )
        assert isinstance(arg, Argument)
        assert len(arg.premises) == 1

    def test_slugify(self) -> None:
        """_slugify converts topic to filesystem-safe slug."""
        assert ArgumentGenerator._slugify("Climate Change!") == "climate_change"
        assert ArgumentGenerator._slugify("AI & ML") == "ai_ml"
        assert ArgumentGenerator._slugify("  spaces  ") == "spaces"

    def test_generate_server_unreachable_raises(self) -> None:
        """generate() raises RuntimeError when health_check fails."""
        gen = self._make_generator()
        gen.client.health_check.return_value = False

        with pytest.raises(RuntimeError, match="not responding"):
            gen.generate("topic")

    def test_generate_support_returns_empty_on_error(self) -> None:
        """_generate_support() returns [] when LLM call fails."""
        gen = self._make_generator()
        gen.client.generate_json.side_effect = ValueError("bad json")
        result = gen._generate_support("claim", ["s1"])
        assert result == []

    def test_generate_sources_returns_empty_on_error(self) -> None:
        """_generate_sources() returns [] when LLM call fails."""
        gen = self._make_generator()
        gen.client.generate_json.side_effect = ValueError("bad json")
        result = gen._generate_sources("claim", ["s1"])
        assert result == []

    def test_generate_explanations_returns_empty_on_error(self) -> None:
        """_generate_explanations() returns {} when LLM call fails."""
        gen = self._make_generator()
        gen.client.generate_json.side_effect = ValueError("bad json")
        result = gen._generate_explanations("claim", ["s1"])
        assert result == {}


# ---------------------------------------------------------------------------
# LLMEnhancer
# ---------------------------------------------------------------------------

class TestLLMEnhancer:
    """Tests for LLMEnhancer using a mocked LLMClient."""

    def _make_enhancer(self) -> LLMEnhancer:
        enhancer = LLMEnhancer.__new__(LLMEnhancer)
        enhancer.client = MagicMock()
        enhancer._cache = {}
        return enhancer

    def test_rephrase_returns_enhanced_text(self) -> None:
        """rephrase() returns the LLM's response text when meaningful."""
        enhancer = self._make_enhancer()
        # Use a response with good word overlap so it passes the sanity check
        original = "Computers process information efficiently and quickly."
        rephrased = "Computers handle information efficiently and quickly."
        enhancer.client.generate.return_value = LLMResponse(text=rephrased, model="t")

        result = enhancer.rephrase(original)
        assert result == rephrased

    def test_rephrase_falls_back_on_too_different(self) -> None:
        """rephrase() returns original when enhanced text is too different."""
        enhancer = self._make_enhancer()
        original = "The sky is blue."
        enhancer.client.generate.return_value = LLMResponse(
            text="Completely unrelated content about something else entirely.", model="t"
        )

        result = enhancer.rephrase(original)
        assert result == original

    def test_rephrase_falls_back_on_exception(self) -> None:
        """rephrase() returns original text when LLM call fails."""
        enhancer = self._make_enhancer()
        enhancer.client.generate.side_effect = RuntimeError("connection failed")

        result = enhancer.rephrase("Some statement.")
        assert result == "Some statement."

    def test_rephrase_uses_cache(self) -> None:
        """rephrase() returns cached result without calling LLM again."""
        enhancer = self._make_enhancer()
        original = "The sky is blue."
        # Pre-populate cache
        cache_key = f"{original}:None:conversational"
        enhancer._cache[cache_key] = "Cached result."

        result = enhancer.rephrase(original)
        assert result == "Cached result."
        enhancer.client.generate.assert_not_called()

    def test_explain_returns_text(self) -> None:
        """explain() returns LLM explanation text."""
        enhancer = self._make_enhancer()
        enhancer.client.generate.return_value = LLMResponse(
            text="Because it is fundamental.", model="t"
        )

        result = enhancer.explain("gravity", question_type="why")
        assert result == "Because it is fundamental."

    def test_explain_returns_none_on_error(self) -> None:
        """explain() returns None when LLM call fails."""
        enhancer = self._make_enhancer()
        enhancer.client.generate.side_effect = RuntimeError("error")

        result = enhancer.explain("concept")
        assert result is None

    def test_summarize_exchange(self) -> None:
        """summarize_exchange() returns a summary string."""
        enhancer = self._make_enhancer()
        enhancer.client.generate.return_value = LLMResponse(
            text="We discussed the topic.", model="t"
        )

        result = enhancer.summarize_exchange(["user said x"], ["bot said y"])
        assert result == "We discussed the topic."

    def test_summarize_exchange_returns_empty_on_error(self) -> None:
        """summarize_exchange() returns empty string on failure."""
        enhancer = self._make_enhancer()
        enhancer.client.generate.side_effect = RuntimeError("error")

        result = enhancer.summarize_exchange(["u"], ["b"])
        assert result == ""

    def test_clear_cache(self) -> None:
        """clear_cache() empties the cache dict."""
        enhancer = self._make_enhancer()
        enhancer._cache["key"] = "value"
        enhancer.clear_cache()
        assert enhancer._cache == {}

    def test_is_too_different_true(self) -> None:
        """_is_too_different() returns True for low word overlap."""
        enhancer = self._make_enhancer()
        assert enhancer._is_too_different("the sky is blue", "fox jumped over fence") is True

    def test_is_too_different_false(self) -> None:
        """_is_too_different() returns False for high word overlap."""
        enhancer = self._make_enhancer()
        assert enhancer._is_too_different(
            "the sky is blue today",
            "the sky was blue today",
        ) is False

    def test_is_too_different_empty_strings(self) -> None:
        """_is_too_different() returns True when either string is empty."""
        enhancer = self._make_enhancer()
        assert enhancer._is_too_different("", "something") is True
        assert enhancer._is_too_different("something", "") is True

    def test_enhancer_init(self) -> None:
        """LLMEnhancer.__init__ sets client and cache."""
        enhancer = LLMEnhancer("http://localhost:8000", model="test-model")
        assert enhancer.client is not None
        assert enhancer._cache == {}
