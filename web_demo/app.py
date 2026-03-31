#!/usr/bin/env python3
"""Streamlit web demo for Difficult Dialogs.

Run with: streamlit run app.py
Deploy to Hugging Face Spaces: https://huggingface.co/spaces
"""
import streamlit as st
from pathlib import Path
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from difficult_dialogs import (
    Argument,
    SilentPolicy,
    KnowItAllPolicy,
    SocraticPolicy,
    DebatePolicy,
    ExploratoryPolicy,
)


# Page configuration
st.set_page_config(
    page_title="Difficult Dialogs - Interactive Demo",
    page_icon="💬",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS for better chat appearance
st.markdown("""
<style>
    .stChatMessage {
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
    }
    .stChatMessage[data-testid="stChatMessage"]:nth-child(odd) {
        background-color: #f0f2f6;
    }
    .policy-selector {
        background-color: #e8f4f8;
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
    }
</style>
""", unsafe_allow_html=True)


# Policy mapping
POLICIES = {
    "Silent (Presentation)": SilentPolicy,
    "Know-It-All (Evidence)": KnowItAllPolicy,
    "Socratic (Questions)": SocraticPolicy,
    "Debate (Challenger)": DebatePolicy,
    "Exploratory (Neutral)": ExploratoryPolicy,
}

POLICY_DESCRIPTIONS = {
    "Silent (Presentation)": "Presents all statements without waiting for feedback. Best for lectures and presentations.",
    "Know-It-All (Evidence)": "Provides supporting evidence when you disagree. Best for education and factual topics.",
    "Socratic (Questions)": "Asks probing questions instead of giving answers. Best for critical thinking and philosophy.",
    "Debate (Challenger)": "Actively challenges your disagreements. Best for debate practice and testing convictions.",
    "Exploratory (Neutral)": "Acknowledges multiple viewpoints neutrally. Best for controversial topics.",
}


def load_sample_arguments():
    """Load available sample arguments."""
    base_path = Path(__file__).parent.parent / "examples" / "sample_arguments"
    arguments = {}
    
    if not base_path.exists():
        return arguments
    
    for category_dir in sorted(base_path.iterdir()):
        if not category_dir.is_dir():
            continue
        
        category = category_dir.name
        for arg_dir in sorted(category_dir.iterdir()):
            if arg_dir.is_dir():
                key = f"{category}/{arg_dir.name}"
                arguments[key] = arg_dir
    
    return arguments


def init_session_state():
    """Initialize Streamlit session state."""
    if "current_policy" not in st.session_state:
        st.session_state.current_policy = None
    if "current_argument" not in st.session_state:
        st.session_state.current_argument = None
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    if "policy_instance" not in st.session_state:
        st.session_state.policy_instance = None
    if "started" not in st.session_state:
        st.session_state.started = False


def start_dialog(argument_path: str, policy_name: str):
    """Start a new dialog with selected argument and policy."""
    try:
        # Load argument
        arg = Argument()
        arg.load(argument_path)
        
        # Create policy
        policy_class = POLICIES[policy_name]
        policy = policy_class(arg)
        
        # Initialize state
        st.session_state.current_argument = arg
        st.session_state.current_policy = policy_name
        st.session_state.policy_instance = policy
        st.session_state.chat_history = []
        st.session_state.started = True
        
        # Add intro message
        intro = policy.start()
        st.session_state.chat_history.append({
            "role": "assistant",
            "content": intro,
        })
        
        return True
        
    except Exception as e:
        st.error(f"Error loading argument: {e}")
        return False


def handle_user_input(user_input: str):
    """Process user input and generate response."""
    if not st.session_state.policy_instance:
        return
    
    policy = st.session_state.policy_instance
    
    # Get response from policy
    response = policy.handle_input(user_input)
    
    # Add user message to history
    st.session_state.chat_history.append({
        "role": "user",
        "content": user_input,
    })
    
    # Add bot response if any
    if response:
        st.session_state.chat_history.append({
            "role": "assistant",
            "content": response,
        })
    
    # Check if dialog finished
    if policy.state.finished:
        conclusion = policy.end()
        if conclusion and conclusion not in [msg["content"] for msg in st.session_state.chat_history]:
            st.session_state.chat_history.append({
                "role": "assistant",
                "content": f"\n**Conclusion:** {conclusion}",
            })


def main():
    """Main application."""
    init_session_state()
    
    # Header
    st.title("💬 Difficult Dialogs")
    st.markdown("**Interactive argument exploration tool**")
    
    # Sidebar for configuration
    with st.sidebar:
        st.header("Configuration")
        
        # Load available arguments
        arguments = load_sample_arguments()
        
        if not arguments:
            st.error("No sample arguments found!")
            st.info("Please ensure the examples/sample_arguments directory exists.")
            return
        
        # Argument selector
        st.subheader("Select Argument")
        argument_choice = st.selectbox(
            "Choose a topic to explore:",
            options=list(arguments.keys()),
            format_func=lambda x: x.replace("_", " ").title(),
        )
        
        # Policy selector
        st.subheader("Choose Interaction Style")
        policy_choice = st.selectbox(
            "How should the AI respond?",
            options=list(POLICIES.keys()),
            help="Different policies provide different interaction experiences",
        )
        
        # Show policy description
        st.info(POLICY_DESCRIPTIONS[policy_choice])
        
        # Start/restart button
        col1, col2 = st.columns([2, 1])
        with col1:
            if st.button("🚀 Start New Dialog", use_container_width=True):
                arg_path = arguments[argument_choice]
                start_dialog(str(arg_path), policy_choice)
        
        with col2:
            if st.session_state.started:
                if st.button("🔄 Reset", use_container_width=True):
                    st.session_state.started = False
                    st.session_state.chat_history = []
                    st.session_state.policy_instance = None
        
        # Statistics
        st.divider()
        st.subheader("Library Stats")
        st.metric("Available Arguments", len(arguments))
        st.metric("Categories", len(set(a.split("/")[0] for a in arguments.keys())))
        st.metric("Policies Available", len(POLICIES))
        
        # Info
        st.divider()
        st.markdown("""
### About Difficult Dialogs

A framework for structured argumentation that runs **offline** with **zero dependencies**.

**Key Features:**
- ✅ File-based argument format
- ✅ Multiple dialog policies
- ✅ LLM-powered generation
- ✅ Works without API calls

[View on GitHub](https://github.com/difficult-dialogs/difficult_dialogs)
        """)
    
    # Main chat area
    if not st.session_state.started:
        st.markdown("""
### 👈 Select an argument and policy to begin!

Use the sidebar to:
1. **Choose a topic** from our library of 30+ arguments
2. **Select an interaction style** (policy)
3. **Click "Start New Dialog"**

Each policy offers a unique experience:
- **Silent**: One-way presentation
- **Know-It-All**: Evidence-based persuasion  
- **Socratic**: Questioning approach
- **Debate**: Active challenging
- **Exploratory**: Neutral exploration
        """)
        
        # Show featured arguments
        st.markdown("### Featured Arguments")
        
        featured = [
            ("technology/artificial_intelligence_will_benefit_humanity", "🤖 AI Benefits"),
            ("philosophy/i_think_therefore_i_am", "🧠 Cogito Ergo Sum"),
            ("health/exercise_improves_mental_health", "💪 Exercise & Mental Health"),
            ("society/universal_basic_income_reduces_poverty", "💰 Universal Basic Income"),
        ]
        
        cols = st.columns(4)
        for idx, (path, emoji) in enumerate(featured):
            if path in arguments:
                with cols[idx % 4]:
                    st.markdown(f"**{emoji}** {path.split('/')[-1].replace('_', ' ').title()}")
        
        return
    
    # Display chat history
    for message in st.session_state.chat_history:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # Chat input
    if st.session_state.policy_instance and not st.session_state.policy_instance.state.finished:
        if prompt := st.chat_input("Type your response..."):
            handle_user_input(prompt)
            st.rerun()
    elif st.session_state.policy_instance and st.session_state.policy_instance.state.finished:
        st.success("✅ Dialog completed! Choose a new argument or reset to start over.")


if __name__ == "__main__":
    main()
