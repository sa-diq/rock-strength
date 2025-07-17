import os
import sys
import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime

from core.database import db_manager
from navigation import create_navigation

# Add the project root to the path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

st.set_page_config(page_title="Database Queries", layout="wide")

# Initialize navigation
create_navigation()

# Initialize session state for query history
if 'query_history' not in st.session_state:
    st.session_state.query_history = []
if 'sql_query_value' not in st.session_state:
    st.session_state.sql_query_value = ""

def is_read_only_query(query):
    """Check if query is read-only (SELECT only)"""
    query_clean = query.strip().upper()
    
    # Allow SELECT, WITH (for CTEs), and EXPLAIN
    allowed_starts = ['SELECT', 'WITH', 'EXPLAIN']
    
    # Check if query starts with allowed keywords
    for start in allowed_starts:
        if query_clean.startswith(start):
            return True
    
    return False

def execute_sql_query(query):
    """Execute SQL query with safety checks"""
    
    # Clean up query - remove trailing semicolons and whitespace
    query = query.strip().rstrip(';')
    
    # Check if query is read-only
    if not is_read_only_query(query):
        raise ValueError("Only SELECT queries are allowed for security reasons")
    
    # Check for multiple statements (basic protection)
    if ';' in query:
        raise ValueError("Multiple statements not allowed. Please execute one query at a time.")
    
    try:
        connection = db_manager.get_connection()
        if not connection:
            raise Exception("Cannot connect to database")
        
        cursor = connection.cursor()
        
        # Add LIMIT 50 if not already present (check case insensitively)
        query_upper = query.upper()
        if 'LIMIT' not in query_upper:
            query += " LIMIT 50"
        else:
            # If LIMIT exists, check if it's higher than 50
            import re
            limit_match = re.search(r'LIMIT\s+(\d+)', query_upper)
            if limit_match:
                existing_limit = int(limit_match.group(1))
                if existing_limit > 50:
                    # Replace with LIMIT 50
                    query = re.sub(r'LIMIT\s+\d+', 'LIMIT 50', query, flags=re.IGNORECASE)
        
        cursor.execute(query)
        
        # Get column names
        columns = [description[0] for description in cursor.description]
        
        # Get results
        results = cursor.fetchall()
        
        cursor.close()
        connection.close()
        
        return {
            'success': True,
            'columns': columns,
            'data': results,
            'row_count': len(results)
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }

def add_to_query_history(query):
    """Add query to session state history"""
    if query.strip() and query not in st.session_state.query_history:
        st.session_state.query_history.insert(0, query)
        # Keep only last 10 queries
        st.session_state.query_history = st.session_state.query_history[:10]

def display_schema_info(schema_info):
    """Display database schema information"""
    st.markdown("### 📋 Database Schema")
    
    for table_name, info in schema_info.items():
        with st.expander(f"📊 **{table_name}** ({info['row_count']} rows)"):
            
            # Column information
            st.markdown("**Columns:**")
            col_df = pd.DataFrame(info['columns'], columns=['ID', 'Name', 'Type', 'Not Null', 'Default', 'Primary Key'])
            st.dataframe(col_df[['Name', 'Type', 'Not Null', 'Primary Key']], use_container_width=True)
            
            # Sample data
            if info['sample_data']:
                st.markdown("**Sample Data:**")
                column_names = [col[1] for col in info['columns']]
                sample_df = pd.DataFrame(info['sample_data'], columns=column_names)
                st.dataframe(sample_df, use_container_width=True)
            else:
                st.info("No sample data available")

def get_example_queries():
    """Get basic example queries"""
    return [
        {
            'title': 'Count All Plots',
            'query': 'SELECT COUNT(*) as total_plots FROM plots;'
        },
        {
            'title': 'List All Sandstones',
            'query': 'SELECT DISTINCT sandstone_name FROM sandstones;'
        },
        {
            'title': 'Show All Plots',
            'query': 'SELECT doi, figure_number, created_at FROM plots ORDER BY created_at DESC;'
        },
        {
            'title': 'Get Data to Replot Figure',
            'query': '''SELECT p.doi, p.figure_number, s.sandstone_name, 
       dp.p_mpa, dp.q_mpa
FROM plots p
JOIN sandstones s ON p.id = s.plot_id  
JOIN data_points dp ON s.id = dp.sandstone_id
WHERE p.doi = '10.1016/j.jsg.2012.08.014' 
  AND p.figure_number = '8';'''
        }
    ]

# Page header
st.title("Database Queries")
st.markdown("Query the available digitised research data using SQL or natural language")
st.markdown("---")

# Create tabs
tab_sql, tab_nl = st.tabs(["SQL Query", "Generative AI"])

with tab_sql:
    st.markdown("### 🛠️ SQL Query Interface")
    
    # Add link to detailed schema page
    st.markdown("#### Database Schema")
    st.info("Click below for entity relationship diagram and table structure:")
    st.page_link("pages/4_Database_Schema.py", label="View Full Schema")
    
    st.markdown("---")
        
        # Example queries
    st.markdown("### Example Queries")
    examples = get_example_queries()
    
    example_cols = st.columns(4)
    for i, example in enumerate(examples):
        with example_cols[i]:
            if st.button(f"📋 {example['title']}", key=f"example_{i}"):
                st.session_state.sql_query_value = example['query']
                st.rerun()
    
    st.markdown("---")
    
    # Query input
    st.markdown("### Write Your SQL Query")
    
    # Query history dropdown
    if st.session_state.query_history:
        selected_history = st.selectbox(
            "📚 Recent Queries:",
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
        height=150,
        placeholder="SELECT * FROM plots WHERE created_at >= date('now', '-7 days');",
        value=st.session_state.get('sql_query_value', ''),
        key="sql_query_input"
    )
    
    # Update session state when query changes
    if query != st.session_state.get('sql_query_value', ''):
        st.session_state.sql_query_value = query
    
    # Execute button
    col1, col2 = st.columns([1, 4])
    with col1:
        execute_button = st.button("▶️ Execute Query", type="primary")
    with col2:
        if st.button("🗑️ Clear Query", key="clear_button"):
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
                    st.info(f"💡 Showing {len(df)} rows (max 50). Use LIMIT in your query for pagination.")
            
            else:
                st.info("📭 Query executed successfully but returned no results.")
        
        else:
            st.error(f"❌ **Query Error:**\n```\n{result['error']}\n```")
    
    elif execute_button:
        st.warning("⚠️ Please enter a query before executing.")

with tab_nl:
    st.markdown("### 🤖 Natural Language Query Interface")
    st.info("🚧 **Coming Soon!** This feature will allow you to ask questions in plain English and automatically generate SQL queries.")
    
    # Placeholder for natural language interface
    st.markdown("""
    **Planned Features:**
    - Ask questions like "How many plots were digitized this year?"
    - Automatic SQL generation from natural language
    - Context-aware suggestions based on your data
    - Integration with AI models for query optimization
    
    **Example Questions:**
    - "Show me all sandstone types"
    - "What's the average pressure value across all data points?"
    - "List plots digitized in the last month"
    - "Which DOI has the most sandstone datasets?"
    """)
    
    # Placeholder input (non-functional)
    nl_query = st.text_input(
        "Ask a question about your data:",
        placeholder="How many plots were digitized this year?",
        disabled=True
    )
    
    st.button("🤖 Generate Query", disabled=True)

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: gray; font-size: 0.8em;'>
🔍 Query interface • Read-only access • 50 row limit
</div>
""", unsafe_allow_html=True)