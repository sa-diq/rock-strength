import os
import sys
import streamlit as st
import pandas as pd
from datetime import datetime

# Add the project root to the path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Import all query functions from our combined module
from core.query_functions import (
    # Regular SQL functions
    execute_sql_query,
    add_to_query_history,
    get_example_queries,
    is_read_only_query,
    
    # Natural Language to SQL functions
    generate_sql_from_nl,
    execute_nl_generated_sql,
    validate_and_suggest_sql_fixes,
    get_example_nl_questions
)

from core.database import db_manager
from navigation import create_navigation

@st.cache_data(ttl=60)
def get_database_stats_for_query_page():
    """Cached stats for query page"""
    return db_manager.get_database_stats()

st.set_page_config(page_title="Database Queries", page_icon="🔍", layout="wide")

# Initialize navigation
create_navigation()

# Initialize session state
if 'query_history' not in st.session_state:
    st.session_state.query_history = []
if 'sql_query_value' not in st.session_state:
    st.session_state.sql_query_value = ""
if 'nl_generated_sql' not in st.session_state:
    st.session_state.nl_generated_sql = ""
if 'nl_question' not in st.session_state:
    st.session_state.nl_question = ""

# Page header
st.title("Database Queries")
st.markdown("Query your research data using SQL or natural language")
st.markdown("---")

# Add link to detailed schema page
st.markdown("### Database Schema")
st.info("Click below for entity relationship diagram and table structure:")
st.page_link("pages/4_Database_Schema.py", label="**View Full Schema**")

# Create tabs
tab_sql, tab_nl = st.tabs(["SQL Query", "Natural Language with Generative AI"])

# =============================================================================
# SQL TAB
# =============================================================================

with tab_sql:
    st.markdown("### SQL Query Interface")
    st.markdown("---")
    
    # Example queries
    st.markdown("### Example Queries")
    examples = get_example_queries()
    
    example_cols = st.columns(4)
    for i, example in enumerate(examples):
        with example_cols[i]:
            if st.button(f" {example['title']}", key=f"example_{i}"):
                st.session_state.sql_query_value = example['query']
                st.rerun()
    
    st.markdown("---")
    
    # Query input
    st.markdown("### Write Your Query")
    
    # Query history dropdown
    if st.session_state.query_history:
        selected_history = st.selectbox(
            "Recent Queries:",
            options=[""] + st.session_state.query_history,
            format_func=lambda x: "Select from history..." if x == "" else x[:100] + "..." if len(x) > 100 else x,
            key="history_select"
        )
        
        if selected_history:
            st.session_state.sql_query_value = selected_history
            st.rerun()
    
    # SQL text area - use value parameter for control
    query = st.text_area(
        "Enter your SQL query:",
        height=200,
        placeholder="SELECT COUNT(*) as total_plots FROM plots;",
        value=st.session_state.get('sql_query_value', ''),
        key="sql_query_input"
    )
    
    # Update session state when query changes
    if query != st.session_state.get('sql_query_value', ''):
        st.session_state.sql_query_value = query
    
    # Execute button
    col1, col2 = st.columns([1, 4])
    with col1:
        execute_button = st.button("Execute Query", type="primary")
    with col2:
        if st.button("Clear Query", key="clear_button"):
            st.session_state.sql_query_value = ""
            st.rerun()
    
    # Execute query
    if execute_button and query.strip():
        add_to_query_history(query)
        
        with st.spinner("Executing query..."):
            result = execute_sql_query(query)
        
        if result['success']:
            st.success(f"✅ Query executed successfully! ({result['row_count']} rows returned)")
            
            if result['data']:
                # Display results
                df = pd.DataFrame(result['data'], columns=result['columns'])
                st.dataframe(df, use_container_width=True)
                
                # Export options
                col1, col2 = st.columns([1, 4])
                with col1:
                    csv = df.to_csv(index=False).encode('utf-8')
                    st.download_button(
                        "📥 Export CSV",
                        csv,
                        file_name=f"query_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                        mime="text/csv"
                    )
                
                with col2:
                    st.info(f"Showing {len(df)} rows (max 50).")
            
            else:
                st.info("Query executed successfully but returned no results.")
        
        else:
            st.error(f"❌ **Query Error:**\n```\n{result['error']}\n```")
    
    elif execute_button:
        st.warning("⚠️ Please enter a query before executing.")

# =============================================================================
# NATURAL LANGUAGE TAB
# =============================================================================

with tab_nl:
    st.markdown("### Natural Language Query Interface")
    
    # Handle example question selection
    if 'example_question' in st.session_state:
        st.session_state.nl_question = st.session_state.example_question
        del st.session_state.example_question  # Clear after use
    
    question = st.text_input(
        "Enter your question below:",
        value=st.session_state.nl_question,
        placeholder="How many plots were digitized this year?",
        help="Examples: 'How many plots?', 'List all sandstone names'",
        key="nl_question_input"
    )
    
    # Update session state when question changes
    if question != st.session_state.nl_question:
        st.session_state.nl_question = question
        # Clear previous SQL when question changes
        st.session_state.nl_generated_sql = ""
    
    # Step 2: Generate SQL Button
    col1, col2 = st.columns([1, 3])
    
    with col1:
        generate_button = st.button("Generate SQL", type="primary", disabled=not question.strip())
    
    with col2:
        if st.button("Clear"):
            st.session_state.nl_question = ""
            st.session_state.nl_generated_sql = ""
            st.rerun()
    
    # Step 3: Generate SQL when button is pressed
    if generate_button and question.strip():
        with st.spinner("🔄 Generating SQL query..."):
            generated_sql = generate_sql_from_nl(question)
        
        if generated_sql:
            st.session_state.nl_generated_sql = generated_sql
            
            # Check if auto-fix was applied
            if "-- AUTO-FIXED VERSION:" in generated_sql:
                st.info(" **Auto-Fix Applied**: Detected and corrected SQL issues")
                
            st.success("✅ SQL generated successfully!")
        else:
            st.session_state.nl_generated_sql = ""
            st.error("❌ Failed to generate SQL. Please try rephrasing your question.")
    
    # Step 4: Show Generated SQL (if exists)
    if st.session_state.nl_generated_sql:
        st.markdown("#### Generated SQL Query")
        st.code(st.session_state.nl_generated_sql, language="sql")
        
        # Validate the generated SQL
        issues, suggestions = validate_and_suggest_sql_fixes(st.session_state.nl_generated_sql)
        
        if issues:
            st.warning(" **Potential SQL Issues Detected:**")
            for i, issue in enumerate(issues):
                st.write(f"• {issue}")
                if i < len(suggestions):
                    st.caption(f"  💡 Suggestion: {suggestions[i]}")
            
            st.info("**Tip:** Review the SQL above. You can copy it to the SQL tab for manual editing if needed.")
        
        # Step 5: Execute Button
        col1, col2 = st.columns([1, 3])
        
        with col1:
            execute_button = st.button("Execute Query", type="secondary")
        
        with col2:
            if issues:
                st.caption("⚠️ Review warnings above before executing")
            # else:
            #     st.caption("✅ SQL looks good - ready to execute")
        
        # Step 6: Execute and show results
        if execute_button:
            with st.spinner("🔄 Executing query..."):
                result = execute_nl_generated_sql(st.session_state.nl_generated_sql)
            
            if result['success']:
                st.success(f"✅ Query executed successfully! ({result['row_count']} rows returned)")
                
                if result['data']:
                    # Display results in a nice table
                    df = pd.DataFrame(result['data'], columns=result['columns'])
                    st.dataframe(df, use_container_width=True)
                    
                    # Export option
                    if len(df) > 0:
                        csv = df.to_csv(index=False).encode('utf-8')
                        st.download_button(
                            "📥 Export Results as CSV",
                            csv,
                            file_name=f"nl_query_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                            mime="text/csv"
                        )
                else:
                    st.info("Query executed successfully but returned no results.")
            
            else:
                # Handle errors
                if result.get('security_violation'):
                    st.error(f"**Security Alert**: {result['error']}")
                    st.markdown("""
                    **Why was this blocked?**
                    - Only SELECT queries are allowed
                    - No data modification permitted
                    - This protects your research data
                    """)
                else:
                    st.error(f"❌ **Query Error**: {result['error']}")
    
    # Step 7: Example Questions
    st.markdown("---")
    st.markdown("#### Example Questions")
    
    example_questions = get_example_nl_questions()
    
    # Display examples in 2 columns
    col1, col2 = st.columns(2)
    
    for i, example in enumerate(example_questions):
        with col1 if i % 2 == 0 else col2:
            if st.button(f"{example}", key=f"example_nl_{i}", help="Click to use this question"):
                st.session_state.example_question = example
                st.rerun()
    
    # Additional help
    with st.expander("ℹ️ How to Ask Good Questions"):
        st.markdown("""
        **Tips for better results:**
        
        ✅ **Good questions:**
        - "How many plots are there?"
        - "List all sandstone names"
        - "What's the average pressure for Berea sandstone?"
        - "Show plots from DOI 10.1016/..."
        
        ❌ **Questions that won't work well:**
        - Very complex multi-part questions
        - Questions about data not in the database
        - Requests to modify or delete data
        
        **Remember:** The AI generates SQL based on your database schema, then executes it against your real data.
        """)

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: gray; font-size: 0.8em;'>
🔍 Query interface • Read-only access • 50 row limit
</div>
""", unsafe_allow_html=True)