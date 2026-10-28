#!/usr/bin/env python3
"""Latency benchmark for difficult_dialogs policies.

Runs 100 simulated turns against a sample argument with each of the 14
built-in policies and prints a table of p50 and p95 latencies.

No network connection or LLM server required.

Usage:
    python scripts/benchmark.py
"""
from __future__ import annotations

import statistics
import time

from difficult_dialogs.builder import ArgumentBuilder
from difficult_dialogs.policy import POLICY_REGISTRY, BasePolicy, get_policy
from difficult_dialogs.yesno import set_solver


# ---------------------------------------------------------------------------
# Minimal solver so we don't need OPM installed
# ---------------------------------------------------------------------------

class _BenchmarkSolver:
    def match_yes_or_no(self, text: str, lang: str = "en-US") -> bool | None:
        t = text.lower().strip()
        if t in ("yes", "agree"):
            return True
        if t in ("no", "disagree"):
            return False
        return None


# ---------------------------------------------------------------------------
# Sample argument
# ---------------------------------------------------------------------------

def _make_benchmark_argument():
    b = (
        ArgumentBuilder("benchmark_argument")
        .intro("Welcome to the benchmark argument.")
        .conclusion("Thank you for participating in this benchmark.")
    )
    for i in range(5):
        pb = b.premise(f"premise_{i}")
        for j in range(3):
            pb.statement(f"Premise {i}, statement {j}: this is evidence supporting the argument.")
        pb.support(f"Support for premise {i}.")
        pb.why(f"Because premise {i} is well-supported by research.")
        pb.done()
    return b.build()


# ---------------------------------------------------------------------------
# Benchmark
# ---------------------------------------------------------------------------

_TURNS = 100
# Alternate yes/no to exercise both agree and disagree paths
_USER_INPUTS = ["yes" if i % 2 == 0 else "no" for i in range(_TURNS)]

# Policies that need special constructor args — skip them
_SKIP = {"webhook", "llmenhanced", "multiargument", "multichoice"}


def benchmark_policy(name: str, argument) -> list[float]:
    """Run _TURNS turns and return per-turn latencies in seconds."""
    try:
        policy = get_policy(name, argument)
    except Exception:
        return []

    latencies: list[float] = []
    policy.start()

    for user_input in _USER_INPUTS:
        if policy.state.finished:
            break
        t0 = time.perf_counter()
        policy.respond(user_input)
        t1 = time.perf_counter()
        latencies.append(t1 - t0)

    return latencies


def main() -> int:
    set_solver(_BenchmarkSolver())
    argument = _make_benchmark_argument()

    print(f"Benchmark: {_TURNS} turns per policy, {len(argument.premises)} premises")
    print()
    print(f"{'Policy':<20} {'Turns':>6} {'p50 (µs)':>10} {'p95 (µs)':>10}")
    print("-" * 50)

    for name in sorted(POLICY_REGISTRY):
        if name in _SKIP:
            continue

        latencies = benchmark_policy(name, argument)
        if not latencies:
            print(f"{name:<20} {'SKIP':>6}")
            continue

        p50 = statistics.median(latencies)
        p95 = sorted(latencies)[int(len(latencies) * 0.95)]

        print(f"{name:<20} {len(latencies):>6} {p50 * 1e6:>10.1f} {p95 * 1e6:>10.1f}")

    print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
