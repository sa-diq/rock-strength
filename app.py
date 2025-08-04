import os
import sys
import streamlit as st

# Add the project root to the path
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from core.database import init_database, db_manager
from navigation import create_navigation

# Page configuration
st.set_page_config(
    page_title="Q-P Plot Digitiser",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Initialize navigation
create_navigation()


# Initialize database on app startup
@st.cache_resource
def initialize_database():
    """Initialize database connection - cached to avoid repeated calls"""
    try:
        if init_database():
            return {"status": "success", "message": "Database initialized successfully"}
        else:
            return {"status": "error", "message": "Failed to initialize database"}
    except Exception as e:
        return {"status": "error", "message": f"Database error: {e}"}

# Initialize database
db_status = initialize_database()

# Display database status
if db_status["status"] == "success":
    st.sidebar.success("✅ Database Ready")
else:
    st.sidebar.error(f"❌ Database Issue: {db_status['message']}")

# Main page content
st.title("Q-P Plot Digitizer")

st.markdown("""
### Welcome to the Q-P Plot Digitizer

This tool allows you to digitize Q-P plots from research papers and extract numerical data points.

**Features:**
- **Plot Digitisation**: Upload and digitise new Q-P plots
- **Data Management**: View and manage digitised plots
- **Database Query**: Query the database using SQL and natural language

""")

st.markdown("""
---
### About
This tool helps researchers extract numerical data from Q-P plots in scientific publications and download digitised data.
""")