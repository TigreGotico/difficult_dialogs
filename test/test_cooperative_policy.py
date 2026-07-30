"""Tests for CooperativePolicy."""
from difficult_dialogs.builder import ArgumentBuilder
from difficult_dialogs.policy import CooperativePolicy, POLICY_REGISTRY, get_policy


def _sample_arg():
    return (
        ArgumentBuilder("coop_test")
        .intro("Let's discuss.")
        .conclusion("Thanks for the conversation.")
        .premise("p1").statement("First claim.").support("Evidence.").done()
        .premise("p2").statement("Second claim.").done()
        .premise("p3").statement("Third claim.").done()
        .build()
    )


class TestCooperativePolicyRegistration:
    def test_in_registry(self):
        assert "cooperative" in POLICY_REGISTRY
        assert POLICY_REGISTRY["cooperative"] is CooperativePolicy

    def test_get_policy(self):
        policy = get_policy("cooperative", _sample_arg())
        assert isinstance(policy, CooperativePolicy)


class TestCooperativeAgreement:
    def test_agreement_advances(self):
        policy = CooperativePolicy(_sample_arg())
        policy.start()
        response = policy.handle_input("yes")
        assert response is not None
        assert "First claim." in response

    def test_agreement_resets_disagree_count(self):
        policy = CooperativePolicy(_sample_arg())
        policy.start()
        policy.handle_input("no")
        policy.handle_input("yes")
        assert policy._consecutive_disagree == 0


class TestCooperativeDisagreement:
    def test_disagreement_acknowledges(self):
        policy = CooperativePolicy(_sample_arg())
        policy.start()
        response = policy.handle_input("no")
        assert response is not None
        # Should contain acknowledgment language
        assert any(phrase in response for phrase in [
            "understand", "fair", "respect", "hear you",
        ])

    def test_disagreement_advances_to_next(self):
        policy = CooperativePolicy(_sample_arg())
        policy.start()
        # First response after start should present p1
        r1 = policy.handle_input("yes")
        # Now disagree — should advance past p1 to p2
        r2 = policy.handle_input("no")
        assert r2 is not None
        # Should present the next claim, not loop on support
        assert "What do you think?" in r2

    def test_disagreement_does_not_loop_on_support(self):
        policy = CooperativePolicy(_sample_arg())
        policy.start()
        policy.handle_input("yes")  # advance to p1
        r1 = policy.handle_input("no")  # disagree with p1
        # KnowItAllPolicy would return support here; Cooperative should advance
        assert "Evidence." not in r1


class TestCooperativeRepeatedDisagreement:
    def test_repeated_disagree_uses_summary(self):
        policy = CooperativePolicy(_sample_arg())
        policy.start()
        policy.handle_input("no")  # 1
        policy.handle_input("no")  # 2
        r3 = policy.handle_input("no")  # 3 — should use summary phrases
        assert r3 is not None
        assert any(phrase in r3 for phrase in [
            "agree to disagree", "differently", "Fair enough",
        ])


class TestCooperativeCompletion:
    def test_completes_after_all_premises(self):
        policy = CooperativePolicy(_sample_arg())
        policy.start()
        for _ in range(10):
            if policy.state.finished:
                break
            policy.handle_input("yes")
        assert policy.state.finished


class TestCooperativeFiveWs:
    def test_five_w_question(self):
        arg = (
            ArgumentBuilder("5w")
            .intro("I.").conclusion("C.")
            .premise("p1").statement("s").why("Because reasons.").done()
            .build()
        )
        policy = CooperativePolicy(arg)
        policy.start()
        policy.handle_input("yes")  # present p1
        response = policy.handle_input("why?")
        assert response is not None
        assert "Because reasons." in response
