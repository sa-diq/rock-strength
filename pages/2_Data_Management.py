import os
import sys
import streamlit as st
import pandas as pd

# Add the project root to the path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core.database import db_manager

st.set_page_config(page_title="Browse Data", page_icon="📚", layout="wide")

def format_timestamp(timestamp):
    """Format timestamp for display"""
    if timestamp:
        return timestamp.strftime('%Y-%m-%d %H:%M')
    return 'Unknown date'

def display_plot_card(plot):
    """Display a single plot card with actions"""
    # Create a more descriptive title
    plot_title = f"📊 **{plot['doi']} Fig {plot['figure_number']}**"
    
    with st.expander(f"{plot_title} ({format_timestamp(plot['created_at'])})"):
        # Plot information
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.markdown(f"""
            **🔗 DOI:** {plot['doi']}  
            **📄 Figure:** {plot['figure_number']}  
            **🏷️ Identifier:** {plot['plot_identifier']}  
            **📏 X-axis range:** {plot['x_axis_range'] or 'Not specified'}  
            **📏 Y-axis range:** {plot['y_axis_range'] or 'Not specified'}  
            **🪨 Sandstones:** {plot['sandstone_count']}  
            **📍 Total data points:** {plot['total_points']}  
            """)
        
        with col2:
            # Action buttons
            show_data_key = f"show_data_{plot['id']}"
            
            # View/Hide data toggle
            if st.session_state.get(show_data_key, False):
                if st.button("🙈 Hide Data", key=f"hide_{plot['id']}"):
                    st.session_state[show_data_key] = False
                    st.rerun()
            else:
                if st.button("👁️ View Data", key=f"view_{plot['id']}"):
                    st.session_state[show_data_key] = True
                    st.rerun()
            
            # Delete button with confirmation
            delete_confirm_key = f"delete_confirm_{plot['id']}"
            
            if st.session_state.get(delete_confirm_key, False):
                st.warning("⚠️ Confirm deletion:")
                col_a, col_b = st.columns(2)
                with col_a:
                    if st.button("❌ Delete", key=f"confirm_delete_{plot['id']}", type="secondary"):
                        try:
                            db_manager.delete_plot(plot['id'])
                            st.success("✅ Deleted!")
                            st.session_state[delete_confirm_key] = False
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error: {e}")
                            st.session_state[delete_confirm_key] = False
                
                with col_b:
                    if st.button("↩️ Cancel", key=f"cancel_delete_{plot['id']}"):
                        st.session_state[delete_confirm_key] = False
                        st.rerun()
            else:
                if st.button("🗑️ Delete", key=f"delete_{plot['id']}", help="Delete this plot"):
                    st.session_state[delete_confirm_key] = True
                    st.rerun()
        
        # Show data if requested
        if st.session_state.get(show_data_key, False):
            try:
                plot_data = db_manager.get_plot_data(plot['id'])
                if plot_data and plot_data['data_points']:
                    st.markdown("#### 📋 Data Points")
                    
                    df = pd.DataFrame(plot_data['data_points'])
                    
                    # Data summary
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Total Points", len(df))
                    with col2:
                        st.metric("P Range (MPa)", f"{df['p_mpa'].min():.1f} - {df['p_mpa'].max():.1f}")
                    with col3:
                        st.metric("Q Range (MPa)", f"{df['q_mpa'].min():.1f} - {df['q_mpa'].max():.1f}")
                    
                    # Data table
                    st.dataframe(df, use_container_width=True)
                    
                    # Download button
                    csv = df.to_csv(index=False).encode('utf-8')
                    filename = f"{plot_data['plot_identifier']}_data.csv"
                    st.download_button(
                        "📥 Download CSV", 
                        csv, 
                        file_name=filename,
                        mime="text/csv",
                        key=f"download_{plot['id']}"
                    )
                else:
                    st.warning("⚠️ No data points found for this plot")
            except Exception as e:
                st.error(f"❌ Error loading plot data: {e}")

# Page header
st.title("📚 Browse Historical Data")
st.markdown("Manage and explore your digitized Q-P plots")
st.markdown("---")

# Check database connection
try:
    plots = db_manager.get_all_plots()
    
    if not plots:
        st.info("📭 **No plots found in the database**")
        st.markdown("""
        ### Getting Started
        1. Go to the **🔬 Digitize** page
        2. Upload and digitize your first Q-P plot
        3. Save it to the database
        4. Return here to view your data
        """)
    else:
        # Summary statistics
        total_points = sum(plot['total_points'] for plot in plots)
        total_sandstones = sum(plot['sandstone_count'] for plot in plots)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("📊 Total Plots", len(plots))
        with col2:
            st.metric("🪨 Total Sandstones", total_sandstones)
        with col3:
            st.metric("📍 Total Data Points", total_points)
        
        st.markdown("---")
        
        # Search and filter options
        col1, col2 = st.columns([2, 1])
        with col1:
            search_term = st.text_input(
                "🔍 Search plots", 
                placeholder="Search by DOI, figure number, or identifier...",
                help="Filter plots by DOI, figure number, or plot identifier"
            )
        with col2:
            sort_option = st.selectbox(
                "📅 Sort by",
                ["Newest first", "Oldest first", "DOI A-Z", "DOI Z-A"],
                help="Choose how to sort the plots"
            )
        
        # Apply search filter
        filtered_plots = plots
        if search_term:
            search_lower = search_term.lower()
            filtered_plots = [
                plot for plot in plots 
                if (search_lower in plot['doi'].lower() or 
                    search_lower in plot['figure_number'].lower() or
                    search_lower in plot['plot_identifier'].lower())
            ]
        
        # Apply sorting
        if sort_option == "Newest first":
            filtered_plots.sort(key=lambda x: x['created_at'] or '', reverse=True)
        elif sort_option == "Oldest first":
            filtered_plots.sort(key=lambda x: x['created_at'] or '')
        elif sort_option == "DOI A-Z":
            filtered_plots.sort(key=lambda x: x['doi'])
        elif sort_option == "DOI Z-A":
            filtered_plots.sort(key=lambda x: x['doi'], reverse=True)
        
        # Display filtered results
        if filtered_plots:
            st.markdown(f"**Found {len(filtered_plots)} plot(s)**")
            
            for plot in filtered_plots:
                display_plot_card(plot)
        else:
            st.warning(f"🔍 No plots found matching '{search_term}'")
        
        # Bulk actions
        if len(plots) > 1:
            st.markdown("---")
            st.markdown("### 🔧 Bulk Actions")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("📥 Export All Data"):
                    try:
                        all_data = []
                        for plot in plots:
                            plot_data = db_manager.get_plot_data(plot['id'])
                            if plot_data and plot_data['data_points']:
                                for point in plot_data['data_points']:
                                    point['doi'] = plot_data['doi']
                                    point['figure_number'] = plot_data['figure_number']
                                    point['plot_identifier'] = plot_data['plot_identifier']
                                    all_data.append(point)
                        
                        if all_data:
                            df_all = pd.DataFrame(all_data)
                            csv_all = df_all.to_csv(index=False).encode('utf-8')
                            st.download_button(
                                "📥 Download All Data as CSV",
                                csv_all,
                                file_name="all_plots_data.csv",
                                mime="text/csv"
                            )
                        else:
                            st.warning("No data to export")
                    except Exception as e:
                        st.error(f"Error exporting data: {e}")
            
            with col2:
                # Placeholder for future bulk operations
                st.info("More bulk actions coming soon...")

except Exception as e:
    st.error(f"❌ **Database Error:** {e}")
    st.markdown("""
    ### Troubleshooting
    1. Check if the database file exists
    2. Verify database permissions
    3. Try restarting the application
    """)