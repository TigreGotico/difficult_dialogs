"""Tests for TranscriptEntry.timestamp — population and serialization."""
from difficult_dialogs.builder import ArgumentBuilder
from difficult_dialogs.policy import KnowItAllPolicy, TranscriptEntry


def _sample_arg():
    return (
        ArgumentBuilder("ts_test")
        .intro("Intro.")
        .conclusion("Done.")
        .premise("p1").statement("Claim.").done()
        .build()
    )


class TestTimestampField:
    def test_default_is_none(self):
        e = TranscriptEntry(role="bot", text="hi")
        assert e.timestamp is None

    def test_to_dict_omits_none(self):
        e = TranscriptEntry(role="bot", text="hi")
        d = e.to_dict()
        assert "timestamp" not in d

    def test_to_dict_includes_when_set(self):
        e = TranscriptEntry(role="bot", text="hi", timestamp=1234567890.0)
        d = e.to_dict()
        assert d["timestamp"] == 1234567890.0

    def test_from_dict_missing_key(self):
        e = TranscriptEntry.from_dict({"role": "bot", "text": "hi"})
        assert e.timestamp is None

    def test_from_dict_with_timestamp(self):
        e = TranscriptEntry.from_dict({"role": "bot", "text": "hi", "timestamp": 99.9})
        assert e.timestamp == 99.9


class TestTimestampPopulation:
    def test_start_populates_timestamp(self):
        policy = KnowItAllPolicy(_sample_arg())
        policy.start()
        assert len(policy.state.transcript) == 1
        ts = policy.state.transcript[0].timestamp
        assert isinstance(ts, float)
        assert ts > 0

    def test_respond_populates_both(self):
        policy = KnowItAllPolicy(_sample_arg())
        policy.start()
        policy.respond("yes")
        # transcript: intro, user "yes", bot response
        assert len(policy.state.transcript) >= 3
        user_entry = policy.state.transcript[1]
        bot_entry = policy.state.transcript[2]
        assert user_entry.role == "user"
        assert isinstance(user_entry.timestamp, float)
        assert bot_entry.role == "bot"
        assert isinstance(bot_entry.timestamp, float)
        assert bot_entry.timestamp >= user_entry.timestamp


class TestTimestampExport:
    def test_markdown_includes_timestamp(self):
        from difficult_dialogs.export.transcript import export_transcript_to_markdown
        policy = KnowItAllPolicy(_sample_arg())
        policy.start()
        md = export_transcript_to_markdown(policy)
        # Should contain ISO timestamp
        assert "T" in md  # ISO format contains T

    def test_json_includes_timestamp(self):
        from difficult_dialogs.export.transcript import export_transcript_to_json
        policy = KnowItAllPolicy(_sample_arg())
        policy.start()
        entries = export_transcript_to_json(policy)
        assert "timestamp" in entries[0]
        assert isinstance(entries[0]["timestamp"], float)
