import os
import sys
import streamlit as st
import pandas as pd
from datetime import datetime

from core.database import db_manager
from navigation import create_navigation

# Add the project root to the path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

st.set_page_config(page_title="Statistics", page_icon="📊", layout="wide")

# Initialize navigation
create_navigation()

def get_database_analytics():
    """Get comprehensive database analytics"""
    try:
        # Basic stats
        stats = db_manager.get_database_stats()
        
        # Get all plots for analysis
        plots = db_manager.get_all_plots()
        
        analytics = {
            'basic_stats': stats,
            'plots': plots,
            'average_points_per_plot': 0,
            'most_active_day': None
        }
        
        if plots:
            # Calculate average points per plot
            total_points = sum(plot['total_points'] for plot in plots)
            analytics['average_points_per_plot'] = total_points / len(plots)
            
            # Plot count by date
            date_counts = {}
            for plot in plots:
                if plot['created_at']:
                    date_str = plot['created_at'].strftime('%Y-%m-%d')
                    date_counts[date_str] = date_counts.get(date_str, 0) + 1
            
            # Find most active day
            if date_counts:
                analytics['most_active_day'] = max(date_counts, key=date_counts.get)
        
        return analytics
        
    except Exception as e:
        st.error(f"Error getting analytics: {e}")
        return None

# Page header
st.title("📊 Database Statistics")
st.markdown("Analytics and insights from your digitization work")
st.markdown("---")

# Get analytics data
analytics = get_database_analytics()

if analytics is None:
    st.error("❌ Unable to load statistics")
    st.stop()

basic_stats = analytics['basic_stats']
plots = analytics['plots']

# Overview metrics
st.markdown("### 📈 Overview")
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("📊 Total Plots", basic_stats.get('plots', 0))

with col2:
    st.metric("🪨 Total Sandstones", basic_stats.get('sandstones', 0))

with col3:
    st.metric("📍 Total Data Points", basic_stats.get('data_points', 0))

with col4:
    st.metric("💾 Database Size", f"{basic_stats.get('database_size_mb', 0)} MB")

# Additional metrics
if plots:
    col1, col2, col3 = st.columns(3)
    
    with col1:
        avg_points = analytics['average_points_per_plot']
        st.metric("📍 Avg Points/Plot", f"{avg_points:.1f}")
    
    with col2:
        most_active = analytics['most_active_day']
        st.metric("🔥 Most Active Day", most_active or "N/A")
    
    with col3:
        recent_plots = len([p for p in plots if p['created_at'] and 
                          (datetime.now() - p['created_at']).days <= 7])
        st.metric("📅 Plots This Week", recent_plots)

st.markdown("---")

# Recent activity section
if plots:
    st.markdown("### 🕒 Recent Activity")
    
    # Sort plots by date (newest first)
    recent_plots = sorted(plots, key=lambda x: x['created_at'] or datetime.min, reverse=True)[:5]
    
    for plot in recent_plots:
        col1, col2, col3 = st.columns([3, 1, 1])
        with col1:
            st.write(f"📊 **{plot['doi']} Fig {plot['figure_number']}**")
        with col2:
            if plot['created_at']:
                st.write(plot['created_at'].strftime('%Y-%m-%d %H:%M'))
            else:
                st.write("Unknown date")
        with col3:
            st.write(f"{plot['total_points']} points")
    
    st.markdown("---")

# Database details
st.markdown("### 🔧 Database Details")

col1, col2 = st.columns(2)
with col1:
    st.markdown(f"""
    **📊 Database Stats:**
    - Tables: 3 (plots, sandstones, data_points)
    - Indexes: 4 (for performance)
    - Format: SQLite 3
    """)

with col2:
    if basic_stats.get('database_size_mb', 0) > 0 and len(plots) > 0:
        avg_size_per_plot = basic_stats['database_size_mb'] / len(plots)
        st.markdown(f"""
        **💾 Storage Analysis:**
        - Database file: {basic_stats['database_size_mb']} MB
        - Avg per plot: {avg_size_per_plot:.2f} MB
        - Growth rate: Steady
        """)
    elif basic_stats.get('database_size_mb', 0) > 0:
        st.markdown(f"""
        **💾 Storage Analysis:**
        - Database file: {basic_stats['database_size_mb']} MB
        - Growth rate: Ready to grow
        """)
    else:
        st.markdown("""
        **💾 Storage Analysis:**
        - Database file: < 0.01 MB
        - Status: Newly created
        """)
    
    # Database health check
    try:
        # Simple connectivity test
        test_plots = db_manager.get_all_plots()
        st.success("✅ Database connection healthy")
    except Exception as e:
        st.error(f"❌ Database issue: {e}")

if not plots:
    # No data yet
    st.info("📭 **No data to analyze yet**")
    st.markdown("""
    ### Getting Started
    
    To see statistics:
    
    1. **🔬 Digitize** some Q-P plots
    2. **💾 Save** them to the database  
    3. **📊 Return here** to see your progress
    
    ### What You'll See
    
    Once you have data, this page will show:
    - **Overview metrics** - Total plots, sandstones, and data points
    - **Performance stats** - Average points per plot, activity tracking
    - **Recent activity** - Monitor your latest digitization work
    - **Database health** - Ensure everything is working properly
    """)

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: gray; font-size: 0.8em;'>
📊 Statistics updated in real-time • Built with Streamlit & SQLite
</div>
""", unsafe_allow_html=True)