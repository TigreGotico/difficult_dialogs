#!/usr/bin/env python3
"""Streamlit web demo for Difficult Dialogs.

Run with: streamlit run app.py
"""
import streamlit as st
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from difficult_dialogs import (
    Argument,
    SilentPolicy,
    KnowItAllPolicy,
    SocraticPolicy,
    DebatePolicy,
    ExploratoryPolicy,
    MaieuticPolicy,
    SkepticPolicy,
    TeacherPolicy,
    DebaterPolicy,
    MinimalistPolicy,
    AdaptivePolicy,
)

st.set_page_config(
    page_title="Difficult Dialogs",
    page_icon="💬",
    layout="wide",
    initial_sidebar_state="expanded",
)

# CSS that works in both light and dark mode — use currentColor / transparent
# backgrounds rather than hardcoded hex values.
st.markdown("""
<style>
    /* Remove hardcoded light backgrounds from chat bubbles */
    [data-testid="stChatMessage"] {
        border-radius: 0.5rem;
        margin-bottom: 0.5rem;
        border: 1px solid rgba(128,128,128,0.15);
    }
    /* Assistant bubble: subtle tint using CSS variable so it works in dark mode */
    [data-testid="stChatMessage"][data-testid*="assistant"],
    [data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-assistant"]) {
        background-color: color-mix(in srgb, currentColor 4%, transparent);
    }
    .finished-banner {
        padding: 0.75rem 1rem;
        border-radius: 0.5rem;
        border: 1px solid rgba(0,200,100,0.4);
        background-color: rgba(0,200,100,0.08);
        margin-top: 1rem;
    }
</style>
""", unsafe_allow_html=True)


# ------------------------------------------------------------------ #
# Policy registry
# ------------------------------------------------------------------ #

BASE_POLICIES = {
    "Know-It-All (Evidence)": KnowItAllPolicy,
    "Socratic (Questions)": SocraticPolicy,
    "Debate (Challenger)": DebatePolicy,
    "Exploratory (Neutral)": ExploratoryPolicy,
    "Maieutic (Discovery)": MaieuticPolicy,
    "Skeptic (Prove It)": SkepticPolicy,
    "Teacher (Lesson)": TeacherPolicy,
    "Debater (Formal)": DebaterPolicy,
    "Silent (Presentation)": SilentPolicy,
    "Minimalist (Terse)": MinimalistPolicy,
    "Adaptive (Auto-switch)": AdaptivePolicy,
}

POLICY_DESCRIPTIONS = {
    "Know-It-All (Evidence)":   "Corrects you with evidence when you disagree. Best for education and factual topics.",
    "Socratic (Questions)":     "Asks probing questions instead of giving answers. Best for critical thinking.",
    "Debate (Challenger)":      "Actively challenges your position. Best for debate practice.",
    "Exploratory (Neutral)":    "Presents multiple viewpoints neutrally. Best for controversial topics.",
    "Maieutic (Discovery)":     "Guides you to discover conclusions yourself.",
    "Skeptic (Prove It)":       "Doubts everything — you must prove each claim.",
    "Teacher (Lesson)":         "Structured lesson format with checks for understanding.",
    "Debater (Formal)":         "Formal debate rules: opening, rounds, closing.",
    "Silent (Presentation)":    "Presents all statements without waiting for feedback. Good for demos.",
    "Minimalist (Terse)":       "Brief acknowledgements only — no elaboration.",
    "Adaptive (Auto-switch)":   "Starts as Know-It-All; switches to Exploratory after 3 disagreements.",
    "LLM-Enhanced (Rephrase)":  "Wraps Know-It-All and rephrases every bot response via your LLM server.",
}


# ------------------------------------------------------------------ #
# Helpers
# ------------------------------------------------------------------ #

def load_arguments() -> dict[str, Path]:
    base = Path(__file__).parent.parent / "examples" / "sample_arguments"
    result: dict[str, Path] = {}
    if not base.exists():
        return result
    for cat in sorted(base.iterdir()):
        if not cat.is_dir():
            continue
        for arg_dir in sorted(cat.iterdir()):
            if arg_dir.is_dir():
                result[f"{cat.name}/{arg_dir.name}"] = arg_dir
    return result


def init_state() -> None:
    defaults = {
        "policy_instance": None,
        "current_argument": None,
        "current_policy": None,
        "chat_history": [],
        "started": False,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


def start_dialog(argument_path: Path, policy_name: str, llm_url: str, llm_model: str) -> bool:
    try:
        arg = Argument.from_directory(str(argument_path))

        if policy_name == "LLM-Enhanced (Rephrase)":
            from difficult_dialogs.policy import LLMEnhancedPolicy
            from difficult_dialogs.llm import LLMEnhancer
            enhancer = LLMEnhancer(llm_url.rstrip("/"), model=llm_model or None)
            inner = KnowItAllPolicy(arg)
            policy = LLMEnhancedPolicy(arg, inner, enhancer, style="conversational")
        elif policy_name == "Adaptive (Auto-switch)":
            policy = AdaptivePolicy(
                arg,
                initial_policy=KnowItAllPolicy(arg),
                fallback_policy=ExploratoryPolicy(arg),
                switch_threshold=3,
            )
        else:
            policy = BASE_POLICIES[policy_name](arg)

        st.session_state.current_argument = arg
        st.session_state.current_policy = policy_name
        st.session_state.policy_instance = policy
        st.session_state.chat_history = []
        st.session_state.started = True

        intro = policy.start()
        if intro:
            st.session_state.chat_history.append({"role": "assistant", "content": intro})

        return True
    except Exception as exc:
        st.error(f"Error loading argument: {exc}")
        return False


def handle_input(user_text: str) -> None:
    policy = st.session_state.policy_instance
    if not policy:
        return

    st.session_state.chat_history.append({"role": "user", "content": user_text})

    response = policy.handle_input(user_text)
    if response:
        st.session_state.chat_history.append({"role": "assistant", "content": response})

    if policy.state.finished:
        conclusion = policy.end()
        already = [m["content"] for m in st.session_state.chat_history]
        if conclusion and conclusion not in already:
            st.session_state.chat_history.append({
                "role": "assistant",
                "content": f"**Conclusion:** {conclusion}",
            })


# ------------------------------------------------------------------ #
# Main
# ------------------------------------------------------------------ #

def main() -> None:
    init_state()

    st.title("💬 Difficult Dialogs")
    st.caption("Structured argumentation — offline, deterministic, auditable.")

    arguments = load_arguments()

    # ---- Sidebar ----
    with st.sidebar:
        st.header("Setup")

        if not arguments:
            st.error("No sample arguments found in examples/sample_arguments/")
            return

        argument_key = st.selectbox(
            "Topic",
            options=list(arguments.keys()),
            format_func=lambda x: x.replace("_", " ").title(),
        )

        policy_name = st.selectbox(
            "Interaction style",
            options=list(POLICY_DESCRIPTIONS.keys()),
        )
        st.caption(POLICY_DESCRIPTIONS[policy_name])

        # LLM config — only shown when relevant
        llm_url = ""
        llm_model = ""
        if policy_name == "LLM-Enhanced (Rephrase)":
            with st.expander("LLM server settings", expanded=True):
                llm_url = st.text_input(
                    "Server URL",
                    value="http://localhost:11434",
                    help="OpenAI-compatible server (Ollama, llama.cpp, etc.)",
                )
                llm_model = st.text_input(
                    "Model name",
                    value="",
                    placeholder="leave blank for server default",
                )
                st.caption(
                    "Responses are rephrased via your LLM server. "
                    "Falls back to original text if unreachable."
                )

        col1, col2 = st.columns([3, 1])
        with col1:
            start_btn = st.button("▶ Start", use_container_width=True, type="primary")
        with col2:
            reset_btn = st.button("↺", use_container_width=True)

        if start_btn:
            start_dialog(arguments[argument_key], policy_name, llm_url, llm_model)
            st.rerun()

        if reset_btn:
            st.session_state.started = False
            st.session_state.chat_history = []
            st.session_state.policy_instance = None
            st.rerun()

        st.divider()
        st.metric("Arguments", len(arguments))
        st.metric("Categories", len({k.split("/")[0] for k in arguments}))
        st.metric("Policies", len(POLICY_DESCRIPTIONS))

        st.divider()
        st.markdown(
            "**difficult_dialogs** — zero-dependency structured debate.\n\n"
            "[GitHub](https://github.com/TigreGotico/difficult_dialogs) · "
            "[Docs](https://github.com/TigreGotico/difficult_dialogs/tree/dev/docs)"
        )

    # ---- Main area ----
    if not st.session_state.started:
        st.markdown("### 👈 Choose a topic and interaction style, then click **Start**")

        st.markdown("#### Available interaction styles")
        cols = st.columns(3)
        for i, (name, desc) in enumerate(POLICY_DESCRIPTIONS.items()):
            with cols[i % 3]:
                st.markdown(f"**{name}**  \n{desc}")

        st.divider()
        st.markdown("#### Browse topics")
        categories: dict[str, list[str]] = {}
        for key in arguments:
            cat, topic = key.split("/", 1)
            categories.setdefault(cat, []).append(topic)
        cat_cols = st.columns(min(len(categories), 3))
        for i, (cat, topics) in enumerate(sorted(categories.items())):
            with cat_cols[i % 3]:
                st.markdown(f"**{cat.replace('_', ' ').title()}**")
                for t in topics:
                    st.caption(t.replace("_", " ").title())
        return

    # Chat history
    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    policy = st.session_state.policy_instance
    if policy and not policy.state.finished:
        if user_input := st.chat_input("Your response…"):
            handle_input(user_input)
            st.rerun()
    elif policy and policy.state.finished:
        st.markdown(
            '<div class="finished-banner">✅ Dialog complete — reset or choose a new topic.</div>',
            unsafe_allow_html=True,
        )


if __name__ == "__main__":
    main()
