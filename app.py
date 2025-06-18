import os
import sys
import streamlit as st

# Add the project root to the path
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from core.database import init_database
from navigation import create_navigation

# Page configuration
st.set_page_config(
    page_title="Q-P Plot Digitiser",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded"
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
st.title("🔬 Q-P Plot Digitizer")

st.markdown("""
### Welcome to the Q-P Plot Digitizer

This tool allows you to digitize Q-P plots from research papers and extract numerical data points.

**Features:**
- **🔬 Plot Digitisation**: Upload and digitise new Q-P plots
- **📚 Data Management**: View and manage your digitised plots
- **📊 Analytics**: Monitor your digitization progress

**Getting Started**
1. Use the navigation sidebar to select a page
2. Start with **Plot Digitisation** to process your first plot
3. Use **Data Management** to manage your digitised plots
4. Check **Analytics** to see your progress

### Database Status
""")

# Database information
if db_status["status"] == "success":
    from core.database import db_manager
    try:
        stats = db_manager.get_database_stats()
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("📊 Total Plots", stats.get('plots', 0))
        with col2:
            st.metric("🪨 Total Sandstones", stats.get('sandstones', 0))
        with col3:
            st.metric("📍 Total Data Points", stats.get('data_points', 0))
        
    except Exception as e:
        st.warning(f"Could not load database statistics: {e}")
else:
    st.error("Database not available. Please check your setup.")

st.markdown("""
---
### About
This tool helps researchers extract numerical data from Q-P plots in scientific publications.
""")