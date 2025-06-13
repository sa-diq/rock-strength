import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import streamlit as st
from PIL import Image
import pandas as pd
import shutil
from datetime import datetime

from core.calibrate_axes_streamlit import calibrate_axes_streamlit
from core.extract_points_streamlit import extract_points_streamlit
from core.database import db_manager, init_database

st.set_page_config(layout="wide", page_title="Q-P Plot Digitizer")

# Initialize database
if 'db_initialized' not in st.session_state:
    try:
        if init_database():
            st.session_state.db_initialized = True
            st.success("SQLite database initialized successfully")
        else:
            st.error("Failed to initialize database.")
    except Exception as e:
        st.error(f"Database initialization error: {e}")
        st.session_state.db_initialized = False

def init_session_state():
    defaults = {
        "current_page": "digitize",  # "digitize", "browse", or "stats"
        "step": 1,
        "sandstone_index": 0,
        "data_points": [],
        "pixel_to_data": None,
        "sandstone_names": []
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

def save_uploaded_image(uploaded_file, plot_name):
    """Save uploaded image to uploads directory"""
    os.makedirs("uploads", exist_ok=True)
    
    # Create filename with timestamp to avoid conflicts
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_extension = uploaded_file.name.split('.')[-1]
    filename = f"{plot_name}_{timestamp}.{file_extension}"
    filepath = os.path.join("uploads", filename)
    
    # Save the file
    with open(filepath, "wb") as f:
        f.write(uploaded_file.getbuffer())
    
    return filepath

def go_back():
    """Handle going back to previous step"""
    if st.session_state.step == 2:
        st.session_state.step = 1
    elif st.session_state.step == 3:
        st.session_state.step = 2
        st.session_state.sandstone_index = 0
        st.session_state.data_points = []
        st.session_state.sandstone_names = []
    elif st.session_state.step == 4:
        st.session_state.step = 3
        if st.session_state.sandstone_index > 0:
            st.session_state.sandstone_index -= 1
            if st.session_state.sandstone_names:
                last_name = st.session_state.sandstone_names[-1]
                st.session_state.data_points = [
                    point for point in st.session_state.data_points 
                    if point.get('dataset') != last_name
                ]
                st.session_state.sandstone_names.pop()

def go_back_one_sandstone():
    """Handle going back one sandstone in step 3"""
    if st.session_state.sandstone_index > 0:
        st.session_state.sandstone_index -= 1
        if st.session_state.sandstone_names:
            last_name = st.session_state.sandstone_names[-1]
            st.session_state.data_points = [
                point for point in st.session_state.data_points 
                if point.get('dataset') != last_name
            ]
            st.session_state.sandstone_names.pop()

def reset_digitization():
    """Reset all digitization session state"""
    keys_to_reset = ["step", "sandstone_index", "data_points", "pixel_to_data", 
                     "sandstone_names", "plot_name", "num_sandstones"]
    for key in keys_to_reset:
        if key in st.session_state:
            del st.session_state[key]
    st.session_state.step = 1

def digitize_page():
    st.title("Q-P Plot Digitizer")
    
    # File uploader
    uploaded_file = st.file_uploader("Upload Q-P Plot Image", type=["png", "jpg", "jpeg"])

    if uploaded_file:
        try:
            img_pil = Image.open(uploaded_file)
            st.image(img_pil, caption="Uploaded Plot", use_column_width=False)
        except Exception as e:
            st.error(f"Error loading image: {e}")
            return

        # Step 1: Enter metadata
        if st.session_state.step == 1:
            st.write("## Step 1: Enter Plot Information")
            plot_name = st.text_input("Enter plot name (e.g. Author_Year_FigNo)", key="plot_name_input")
            num_sandstones = st.number_input("How many sandstones?", min_value=1, step=1, key="num_sandstones_input")
            
            # Check for duplicate plot name
            duplicate_warning = False
            if plot_name and st.session_state.get('db_initialized', False):
                try:
                    if db_manager.check_plot_exists(plot_name):
                        st.warning(f"⚠️ A plot with the name '{plot_name}' already exists in the database!")
                        duplicate_warning = True
                except Exception as e:
                    st.error(f"Error checking for duplicates: {e}")
            
            col1, col2 = st.columns([1, 1])
            with col1:
                if st.button("Next: Calibrate Axes", key="next_to_calibration"):
                    if plot_name and num_sandstones:
                        if duplicate_warning:
                            st.error("Please choose a different plot name to avoid duplication")
                        else:
                            st.session_state.plot_name = plot_name
                            st.session_state.num_sandstones = num_sandstones
                            st.session_state.uploaded_file = uploaded_file
                            st.session_state.step = 2
                            st.rerun()
                    else:
                        st.error("Please fill in all fields")

        # Step 2: Calibrate Axes
        elif st.session_state.step == 2:
            st.write("## Step 2: Calibrate Axes")
            
            pixel_to_data = calibrate_axes_streamlit(img_pil)
            
            if pixel_to_data is not None:
                st.session_state.pixel_to_data = pixel_to_data
                
                col1, col2 = st.columns([1, 1])
                with col1:
                    if st.button("Next: Extract Points", key="next_to_extraction"):
                        st.session_state.step = 3
                        st.rerun()
                with col2:
                    if st.button("Back to Step 1", key="back_to_step1"):
                        go_back()
                        st.rerun()

        # Step 3: Extract points for each sandstone
        elif st.session_state.step == 3:
            st.write("## Step 3: Extract Data Points")
            
            current_idx = st.session_state.sandstone_index
            total_sandstones = st.session_state.num_sandstones
            
            st.write(f"Processing sandstone {current_idx + 1} of {total_sandstones}")
            
            sandstone_name = st.text_input(
                f"Enter name for sandstone {current_idx + 1}:", 
                key=f"sandstone_name_{current_idx}"
            )
            
            points = None
            confirm_button_enabled = False
            
            if sandstone_name:
                if sandstone_name in st.session_state.sandstone_names:
                    st.error("Sandstone name already used. Please choose a different name.")
                else:
                    points = extract_points_streamlit(
                        img_pil, 
                        sandstone_name, 
                        st.session_state.pixel_to_data
                    )
                    
                    if points:
                        st.write(f"Points extracted for {sandstone_name}: {len(points)}")
                        confirm_button_enabled = True
            
            col1, col2, col3 = st.columns([1, 1, 1])
            
            with col1:
                if confirm_button_enabled:
                    if st.button(f"Confirm points for {sandstone_name}", key=f"confirm_points_{current_idx}"):
                        st.session_state.data_points.extend(points)
                        st.session_state.sandstone_names.append(sandstone_name)
                        st.session_state.sandstone_index += 1
                        
                        if st.session_state.sandstone_index >= total_sandstones:
                            st.session_state.step = 4
                        
                        st.rerun()
                else:
                    st.button(f"Confirm points", key=f"confirm_points_{current_idx}", disabled=True)
            
            with col2:
                if current_idx > 0:
                    if st.button("Back to Previous Sandstone", key="back_prev_sandstone"):
                        go_back_one_sandstone()
                        st.rerun()
            
            with col3:
                if st.button("Back to Calibration", key="back_to_calibration"):
                    go_back()
                    st.rerun()

        # Step 4: Show results and save to database
        elif st.session_state.step == 4:
            st.write("## Step 4: Results")
            
            if st.session_state.data_points:
                df = pd.DataFrame(st.session_state.data_points)
                st.dataframe(df)
                
                col1, col2 = st.columns([1, 1])
                
                with col1:
                    # Download CSV button
                    csv = df.to_csv(index=False).encode('utf-8')
                    st.download_button(
                        "Download CSV", 
                        csv, 
                        file_name=f"{st.session_state.plot_name}_data.csv",
                        mime="text/csv"
                    )
                
                with col2:
                    # Save to database button
                    if st.session_state.get('db_initialized', False):
                        if st.button("Save to Database", key="save_to_db", type="primary"):
                            try:
                                # Save image file
                                image_path = save_uploaded_image(
                                    st.session_state.uploaded_file, 
                                    st.session_state.plot_name
                                )
                                
                                # Prepare plot data for database
                                plot_data = {
                                    'plot_name': st.session_state.plot_name,
                                    'image_path': image_path,
                                    'x_axis_range': f"{st.session_state.get('x1_data', 0)} to {st.session_state.get('x2_data', 0)}",
                                    'y_axis_range': f"{st.session_state.get('y1_data', 0)} to {st.session_state.get('y2_data', 0)}",
                                    'data_points': st.session_state.data_points
                                }
                                
                                plot_id = db_manager.save_complete_plot(plot_data)
                                st.success(f"✅ Plot saved to database with ID: {plot_id}")
                                
                            except Exception as e:
                                st.error(f"Error saving to database: {e}")
                    else:
                        st.warning("Database not available")
                
            else:
                st.warning("No data points extracted")
            
            # Navigation buttons
            col1, col2, col3 = st.columns([1, 1, 1])
            
            with col1:
                if st.button("Start Over", key="start_over"):
                    reset_digitization()
                    st.rerun()
            
            with col2:
                if st.button("Back to Point Extraction", key="back_to_extraction"):
                    go_back()
                    st.rerun()
            
            with col3:
                if st.button("Back to Calibration", key="back_to_calibration_from_results"):
                    st.session_state.step = 2
                    st.session_state.sandstone_index = 0
                    st.session_state.data_points = []
                    st.session_state.sandstone_names = []
                    st.rerun()

    else:
        st.info("Please upload an image to begin")

def browse_page():
    st.title("Browse Historical Data")
    
    if not st.session_state.get('db_initialized', False):
        st.error("Database not available")
        return
    
    try:
        plots = db_manager.get_all_plots()
        
        if not plots:
            st.info("No plots found in the database")
            return
        
        st.write(f"Found {len(plots)} plots in the database:")
        
        # Display plots in a nice format
        for plot in plots:
            with st.expander(f"📊 {plot['plot_name']} ({plot['created_at'].strftime('%Y-%m-%d %H:%M') if plot['created_at'] else 'Unknown date'})"):
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    st.write(f"**X-axis range:** {plot['x_axis_range'] or 'Not specified'}")
                    st.write(f"**Y-axis range:** {plot['y_axis_range'] or 'Not specified'}")
                    st.write(f"**Sandstones:** {plot['sandstone_count']}")
                    st.write(f"**Total data points:** {plot['total_points']}")
                
                with col2:
                    # View data button
                    view_key = f"view_{plot['id']}"
                    if st.button("View Data", key=view_key):
                        st.session_state[f"show_data_{plot['id']}"] = True
                    
                    # Delete button with confirmation
                    delete_key = f"delete_{plot['id']}"
                    confirm_key = f"confirm_delete_{plot['id']}"
                    
                    if st.session_state.get(confirm_key, False):
                        # Show confirmation state
                        st.warning("⚠️ Click again to confirm deletion")
                        if st.button("🗑️ Confirm Delete", key=f"confirm_{plot['id']}", type="secondary"):
                            try:
                                db_manager.delete_plot(plot['id'])
                                st.success("Plot deleted successfully!")
                                # Reset confirmation state
                                st.session_state[confirm_key] = False
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error deleting plot: {e}")
                                st.session_state[confirm_key] = False
                        
                        # Cancel button
                        if st.button("Cancel", key=f"cancel_{plot['id']}"):
                            st.session_state[confirm_key] = False
                            st.rerun()
                    else:
                        # Normal delete button
                        if st.button("Delete", key=delete_key, type="secondary"):
                            st.session_state[confirm_key] = True
                            st.rerun()
                
                # Show data if requested
                if st.session_state.get(f"show_data_{plot['id']}", False):
                    try:
                        plot_data = db_manager.get_plot_data(plot['id'])
                        if plot_data and plot_data['data_points']:
                            st.write("### Data Points")
                            df = pd.DataFrame(plot_data['data_points'])
                            st.dataframe(df, use_container_width=True)
                            
                            # Download option
                            csv = df.to_csv(index=False).encode('utf-8')
                            st.download_button(
                                "Download CSV", 
                                csv, 
                                file_name=f"{plot_data['plot_name']}_data.csv",
                                mime="text/csv",
                                key=f"download_{plot['id']}"
                            )
                            
                            # Hide data button
                            if st.button("Hide Data", key=f"hide_{plot['id']}"):
                                st.session_state[f"show_data_{plot['id']}"] = False
                                st.rerun()
                        else:
                            st.warning("No data points found for this plot")
                    except Exception as e:
                        st.error(f"Error loading plot data: {e}")
    
    except Exception as e:
        st.error(f"Error retrieving plots: {e}")

# Initialize session state
init_session_state()

def stats_page():
    st.title("Database Statistics")
    
    if not st.session_state.get('db_initialized', False):
        st.error("Database not available")
        return
    
    try:
        stats = db_manager.get_database_stats()
        
        if stats:
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Total Plots", stats.get('plots', 0))
            
            with col2:
                st.metric("Total Sandstones", stats.get('sandstones', 0))
            
            with col3:
                st.metric("Total Data Points", stats.get('data_points', 0))
            
            with col4:
                st.metric("Database Size", f"{stats.get('database_size_mb', 0)} MB")
            
            st.write("### Database Location")
            st.code(f"Database file: {db_manager.db_path}")
            
            if os.path.exists(db_manager.db_path):
                st.success("✅ Database file exists and is accessible")
            else:
                st.warning("⚠️ Database file not found")
                
        else:
            st.error("Could not retrieve database statistics")
            
    except Exception as e:
        st.error(f"Error retrieving statistics: {e}")

# Navigation
col1, col2, col3 = st.columns([1, 1, 1])
with col1:
    if st.button("🔬 Digitize", key="nav_digitize"):
        st.session_state.current_page = "digitize"
        st.rerun()
with col2:
    if st.button("📚 Browse Data", key="nav_browse"):
        st.session_state.current_page = "browse"
        st.rerun()
with col3:
    if st.button("📊 Stats", key="nav_stats"):
        st.session_state.current_page = "stats"
        st.rerun()

st.markdown("---")

# Show appropriate page
if st.session_state.current_page == "digitize":
    digitize_page()
elif st.session_state.current_page == "browse":
    browse_page()
else:
    stats_page()