import os
import sys
import streamlit as st

# Add the project root to the path
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from core.database import init_database

# Page configuration
st.set_page_config(
    page_title="Q-P Plot Digitiser",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded"
)

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

# Display database status in sidebar
if db_status["status"] == "success":
    st.sidebar.success("✅ Database Ready")
else:
    st.sidebar.error(f"❌ Database Issue")
    st.sidebar.write(db_status['message'])

# Main page content
st.title("🔬 Q-P Plot Digitizer")

st.markdown("""
### Welcome to the Q-P Plot Digitizer

This tool allows you to digitize Q-P plots from research papers and extract numerical data points using **DOI-based identification** for professional research workflows.

**Features:**
- **🔬 Digitize**: Upload and digitize Q-P plots using DOI + figure number
- **📚 Browse Data**: View and manage your digitized plots by DOI
- **📊 Statistics**: Monitor your digitization progress and database health

### Getting Started
1. Use the navigation sidebar to select a page
2. Start with **🔬 Digitize** to process your first plot
3. Enter the paper's **DOI** and **figure number** for proper identification
4. Use **📚 Browse Data** to manage your digitized plots
5. Check **📊 Statistics** to see your progress

### DOI-Based System
This tool uses **Digital Object Identifiers (DOIs)** for plot identification:
- **Globally unique** - No naming conflicts
- **Traceable** - Easy to find the original research paper  
- **Professional** - Matches academic citation standards
- **Searchable** - Find plots by paper DOI

**Example:** DOI `10.1016/j.jrmge.2023.02.015` + Figure `1a` → Identifier `10_1016_j_jrmge_2023_02_015_Fig1a`
""")

# Database information and statistics
if db_status["status"] == "success":
    st.markdown("### Database Overview")
    
    from core.database import db_manager
    try:
        stats = db_manager.get_database_stats()
        plots = db_manager.get_all_plots()
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("📊 Total Plots", stats.get('plots', 0))
        with col2:
            st.metric("🪨 Total Sandstones", stats.get('sandstones', 0))
        with col3:
            st.metric("📍 Total Data Points", stats.get('data_points', 0))
        with col4:
            st.metric("💾 Database Size", f"{stats.get('database_size_mb', 0)} MB")
        
        # Recent activity preview
        if plots:
            st.markdown("#### 🕒 Recent Activity")
            
            # Show last 3 plots
            recent_plots = sorted(plots, key=lambda x: x['created_at'] or '', reverse=True)[:3]
            
            for plot in recent_plots:
                col1, col2, col3 = st.columns([3, 1, 1])
                with col1:
                    st.write(f"📊 **{plot['doi']}** Figure {plot['figure_number']}")
                with col2:
                    if plot['created_at']:
                        st.write(plot['created_at'].strftime('%Y-%m-%d'))
                    else:
                        st.write("Unknown date")
                with col3:
                    st.write(f"{plot['total_points']} points")
            
            if len(plots) > 3:
                st.info(f"📚 View all {len(plots)} plots in **Browse Data**")
        else:
            st.info("📭 **No plots digitized yet** - Start with the **🔬 Digitize** page!")
        
        # Database file info
        st.markdown("#### 💾 Database Information")
        st.code(f"Database location: {db_manager.db_path}")
        
        if os.path.exists(db_manager.db_path):
            st.success("✅ Database file exists and is accessible")
        else:
            st.warning("⚠️ Database file not found")
            
    except Exception as e:
        st.warning(f"Could not load database information: {e}")
else:
    st.error("❌ **Database not available**")
    st.markdown("""
    ### Troubleshooting
    1. Check if the `data/` directory can be created
    2. Verify file system permissions
    3. Try restarting the application
    4. Check the error message in the sidebar for details
    """)

# Usage instructions
st.markdown("""
---
### 📋 How to Use

#### Step 1: Digitize a Plot
1. Go to **🔬 Digitize** page
2. Upload a clear Q-P plot image
3. Enter the paper's **DOI** (e.g., `10.1016/j.jrmge.2023.02.015`)
4. Enter the **figure number** (e.g., `1`, `2a`, `3b`)
5. Calibrate axes by clicking known points
6. Extract data points for each sandstone
7. Save to database

#### Step 2: Manage Your Data
1. Go to **📚 Browse Data** page
2. Search plots by DOI, figure, or identifier
3. View extracted data points
4. Download CSV files
5. Delete unwanted plots

#### Step 3: Track Progress
1. Go to **📊 Statistics** page
2. Monitor digitization progress
3. View database health
4. Check recent activity

### 💡 Best Practices
- **Use complete DOIs** - Include the full DOI from the paper
- **High-resolution images** - Better accuracy for digitization
- **Clear figure numbers** - Use exact figure labels from paper (1a, 2b, etc.)
- **Consistent naming** - Follow the paper's figure numbering
- **Regular backups** - Database is stored in `data/plots.db`

### 🔗 DOI Examples
- Journal article: `10.1016/j.jrmge.2023.02.015`
- Conference paper: `10.1109/ICSE.2023.00025`
- Preprint: `10.48550/arXiv.2301.12345`
- Book chapter: `10.1007/978-3-030-12345-6_7`

---
### About
This open-source tool helps researchers extract numerical data from Q-P plots in scientific publications using professional DOI-based identification.

**Built with:** Streamlit • SQLite • Python  
**License:** Open Source  
**Purpose:** Research Data Extraction
""")

# Footer
st.markdown("""
<div style='text-align: center; color: gray; font-size: 0.8em; margin-top: 2rem;'>
🔬 Q-P Plot Digitizer • Professional Research Tool • DOI-Based Data Management
</div>
""", unsafe_allow_html=True)