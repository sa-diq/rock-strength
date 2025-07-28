# navigation.py - Custom navigation for Q-P Digitization Tool
import streamlit as st

@st.cache_data
def get_navigation_header_html():
    """Cache the navigation header HTML"""
    return """
    <div style="background-color: #f0f2f6; padding: 1rem; border-radius: 0.5rem; margin-bottom: 1rem;">
        <h2 style="margin: 0; color: #262730;">🔬 Q-P Plot Digitizer</h2>
        <p style="margin: 0; color: #666;">Rock Density Research Tool</p>
    </div>
    """

def create_navigation():
    """Create clean horizontal navigation for Q-P digitizer"""
    
    st.markdown(get_navigation_header_html(), unsafe_allow_html=True)
    
    # Navigation buttons
    col1, col2, col3, col4 = st.columns([1, 1, 1, 1])
    
    with col1:
        st.page_link("app.py", label="Home", icon="🏠")
    
    with col2:
        st.page_link("pages/1_Plot_Digitisation.py", label="Digitise Plots", icon="📊")
    
    with col3:
        st.page_link("pages/2_Data_Management.py", label="Data Management", icon="📋")
    
    with col4:
        st.page_link("pages/3_DB_Query.py", label="Database Query", icon="🔍")
    
    st.markdown("---")

def create_simple_navigation():
    """Simpler version with just essential pages"""
    
    # App title
    st.markdown("# 🔬 Q-P Plot Digitizer")
    
    # Simple navigation tabs
    col1, col2, col3 = st.columns([1, 1, 1])
    
    with col1:
        st.page_link("app.py", label="Home", icon="🏠")
    
    with col2:
        st.page_link("pages/1_Plot_Digitisation.py", label="Digitize", icon="📊")
    
    with col3:
        st.page_link("pages/2_Data_Management.py", label="Review", icon="📋")
    
    st.markdown("---")

# You can choose which navigation style to use
def get_navigation():
    """Choose which navigation to use"""
    return create_simple_navigation()  # or create_navigation() for full version