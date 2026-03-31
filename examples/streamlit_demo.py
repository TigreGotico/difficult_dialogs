#!/usr/bin/env python3
"""Streamlit web demo for Difficult Dialogs."""
import sys
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
from difficult_dialogs.arguments import Argument
from difficult_dialogs.policy import KnowItAllPolicy

# Page config
st.set_page_config(
    page_title="Difficult Dialogs Demo",
    page_icon="💬",
    layout="wide"
)

# Title and description
st.title("💬 Difficult Dialogs")
st.markdown("""
**Interactive debate simulator** - Choose an argument and debate with the AI!

The AI will present structured arguments with premises, evidence, and sources.
Your job is to engage in critical thinking by agreeing or disagreeing with each statement.
""")

# Sidebar for argument selection
st.sidebar.header("Select Argument")

# Find all available arguments
sample_dir = Path(__file__).parent / "sample_arguments"
available_args = []

if sample_dir.exists():
    for category in sorted(sample_dir.iterdir()):
        if category.is_dir() and not category.name.startswith("."):
            for topic in sorted(category.iterdir()):
                if topic.is_dir() and (topic / "intro.dialog").exists():
                    available_args.append((category.name, topic))

if not available_args:
    st.error("No sample arguments found! Run `python examples/batch_generate.py` first.")
    st.stop()

# Category filter
categories = sorted(set(cat for cat, _ in available_args))
selected_category = st.sidebar.selectbox("Category", categories)

# Filter arguments by category
category_args = [(cat, topic) for cat, topic in available_args if cat == selected_category]
arg_names = [topic.name.replace("_", " ").title() for _, topic in category_args]

selected_name = st.sidebar.selectbox("Topic", arg_names)
selected_idx = arg_names.index(selected_name)
_, selected_topic = category_args[selected_idx]

# Load argument
@st.cache_resource
def load_argument(path: Path) -> tuple[Argument, KnowItAllPolicy]:
    """Load argument and create policy."""
    arg = Argument().load(path)
    policy = KnowItAllPolicy(arg)
    return arg, policy

try:
    argument, policy = load_argument(selected_topic)
except Exception as e:
    st.error(f"Failed to load argument: {e}")
    st.stop()

# Display argument info
st.sidebar.markdown("---")
st.sidebar.markdown(f"**Premises:** {len(argument.premises)}")
st.sidebar.markdown(f"**Status:** {'Active' if policy.has_more_premises() else 'Completed'}")

# Initialize session state
if "current_statement" not in st.session_state:
    st.session_state.current_statement = None
if "premise_index" not in st.session_state:
    st.session_state.premise_index = 0
if "statement_index" not in st.session_state:
    st.session_state.statement_index = 0
if "dialog_history" not in st.session_state:
    st.session_state.dialog_history = []
if "user_responses" not in st.session_state:
    st.session_state.user_responses = []

# Reset when argument changes
if "loaded_arg_path" not in st.session_state or st.session_state.loaded_arg_path != str(selected_topic):
    st.session_state.loaded_arg_path = str(selected_topic)
    st.session_state.premise_index = 0
    st.session_state.statement_index = 0
    st.session_state.dialog_history = [argument.intro]
    st.session_state.user_responses = []
    # Get first statement
    if argument.premises:
        premise = argument.premises[0]
        stmt = premise.get_next_statement(set())
        if stmt:
            st.session_state.current_statement = stmt

# Main content area
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("Dialog")
    
    # Show dialog history
    for i, entry in enumerate(st.session_state.dialog_history):
        if i < len(st.session_state.user_responses):
            # User response
            response = st.session_state.user_responses[i]
            icon = "✅" if response == "yes" else "❌"
            st.markdown(f"{icon} **You:** {response.title()}")
        
        if isinstance(entry, str):
            st.markdown(f"**AI:** {entry}")
    
    # Current statement to respond to
    if st.session_state.current_statement and policy.has_more_premises():
        st.markdown("---")
        premise = argument.premises[st.session_state.premise_index]
        st.info(f"**Premise {st.session_state.premise_index + 1}/{len(argument.premises)}: {premise.name}**")
        st.markdown(f"**Statement:** {st.session_state.current_statement.text}")
        
        # Response buttons
        col_yes, col_no = st.columns(2)
        with col_yes:
            if st.button("✅ Agree", use_container_width=True, key="agree_btn"):
                # Process agreement
                st.session_state.current_statement.agree()
                st.session_state.user_responses.append("yes")
                st.session_state.dialog_history.append(str(st.session_state.current_statement))
                
                # Get next statement or move to next premise
                cache = set()
                next_stmt = premise.get_next_statement(cache)
                if next_stmt:
                    st.session_state.current_statement = next_stmt
                    st.session_state.statement_index += 1
                else:
                    st.session_state.premise_index += 1
                    st.session_state.statement_index = 0
                    if st.session_state.premise_index < len(argument.premises):
                        next_premise = argument.premises[st.session_state.premise_index]
                        next_stmt = next_premise.get_next_statement(cache)
                        st.session_state.current_statement = next_stmt
                    else:
                        st.session_state.current_statement = None
                        st.session_state.dialog_history.append(argument.conclusion)
                
                st.rerun()
        
        with col_no:
            if st.button("❌ Disagree", use_container_width=True, key="disagree_btn"):
                # Process disagreement
                st.session_state.current_statement.disagree()
                st.session_state.user_responses.append("no")
                response_text = policy.handle_input("no")
                if response_text:
                    st.session_state.dialog_history.append(response_text)
                
                # Stay on same statement or move on based on policy
                cache = set()
                next_stmt = premise.get_next_statement(cache)
                if next_stmt:
                    st.session_state.current_statement = next_stmt
                    st.session_state.statement_index += 1
                else:
                    st.session_state.premise_index += 1
                    st.session_state.statement_index = 0
                    if st.session_state.premise_index < len(argument.premises):
                        next_premise = argument.premises[st.session_state.premise_index]
                        next_stmt = next_premise.get_next_statement(cache)
                        st.session_state.current_statement = next_stmt
                    else:
                        st.session_state.current_statement = None
                        st.session_state.dialog_history.append(argument.conclusion)
                
                st.rerun()
    
    # Conclusion
    if not st.session_state.current_statement or not policy.has_more_premises():
        st.markdown("---")
        st.success(f"**Conclusion:** {argument.conclusion}")
        st.markdown("**Dialog complete!** Thank you for engaging with this argument.")
        
        if st.button("🔄 Restart This Argument"):
            st.session_state.premise_index = 0
            st.session_state.statement_index = 0
            st.session_state.dialog_history = [argument.intro]
            st.session_state.user_responses = []
            if argument.premises:
                premise = argument.premises[0]
                stmt = premise.get_next_statement(set())
                st.session_state.current_statement = stmt
            st.rerun()

with col2:
    st.subheader("Argument Structure")
    
    # Show premises navigation
    st.markdown("**Premises:**")
    for i, premise in enumerate(argument.premises):
        icon = "✅" if i < st.session_state.premise_index else ("📍" if i == st.session_state.premise_index else "⚪")
        st.markdown(f"{icon} **{i+1}. {premise.name}**")
        
        # Show statements in this premise
        if i <= st.session_state.premise_index:
            for j, stmt in enumerate(premise.statements):
                stmt_icon = "✓" if stmt.agreed else ("?" if i == st.session_state.premise_index and j >= st.session_state.statement_index else "✗")
                indent = "  " * (j + 1)
                st.markdown(f"{indent}{stmt_icon} {stmt.text[:60]}...")
    
    # Sources
    all_sources = []
    for premise in argument.premises:
        all_sources.extend(premise.sources)
    
    if all_sources:
        st.markdown("---")
        st.markdown("**Sources:**")
        for source in all_sources[:5]:  # Limit display
            st.markdown(f"• {source[:80]}...")
        if len(all_sources) > 5:
            st.markdown(f"...and {len(all_sources) - 5} more")

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: gray;'>
<em>Difficult Dialogs v0.4.0 - Structured arguments for meaningful debates</em>
</div>
""", unsafe_allow_html=True)

# Debug info (optional, can be removed)
with st.expander("🔧 Debug Info"):
    st.json({
        "premise_index": st.session_state.premise_index,
        "statement_index": st.session_state.statement_index,
        "total_premises": len(argument.premises),
        "has_more": policy.has_more_premises(),
        "current_statement": str(st.session_state.current_statement) if st.session_state.current_statement else None
    })
