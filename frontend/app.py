import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import streamlit as st
from PIL import Image
import pandas as pd

from core.calibrate_axes_streamlit import calibrate_axes_streamlit
from core.extract_points_streamlit import extract_points_streamlit

st.set_page_config(layout="wide")
st.title("Q-P Plot Digitizer")

def init_session_state():
    defaults = {
        "step": 1,
        "sandstone_index": 0,
        "data_points": [],
        "pixel_to_data": None,
        "sandstone_names": []
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

def go_back():
    """Handle going back to previous step"""
    if st.session_state.step == 2:
        # From calibration back to metadata
        st.session_state.step = 1
    elif st.session_state.step == 3:
        # From point extraction back to calibration
        st.session_state.step = 2
        # Reset sandstone progress
        st.session_state.sandstone_index = 0
        st.session_state.data_points = []
        st.session_state.sandstone_names = []
    elif st.session_state.step == 4:
        # From results back to point extraction
        st.session_state.step = 3
        # Go back to last sandstone
        if st.session_state.sandstone_index > 0:
            st.session_state.sandstone_index -= 1
            # Remove last sandstone's data
            if st.session_state.sandstone_names:
                last_name = st.session_state.sandstone_names[-1]
                st.session_state.data_points = [
                    point for point in st.session_state.data_points 
                    if point.get('sandstone_name') != last_name
                ]
                st.session_state.sandstone_names.pop()

def go_back_one_sandstone():
    """Handle going back one sandstone in step 3"""
    if st.session_state.sandstone_index > 0:
        st.session_state.sandstone_index -= 1
        # Remove the last sandstone's data
        if st.session_state.sandstone_names:
            last_name = st.session_state.sandstone_names[-1]
            st.session_state.data_points = [
                point for point in st.session_state.data_points 
                if point.get('sandstone_name') != last_name
            ]
            st.session_state.sandstone_names.pop()

# Initialize session state
init_session_state()

# Step 1: Upload Image
uploaded_file = st.file_uploader("Upload Q-P Plot Image", type=["png", "jpg", "jpeg"])

if uploaded_file:
    try:
        img_pil = Image.open(uploaded_file)
        st.image(img_pil, caption="Uploaded Plot", use_column_width=False)
    except Exception as e:
        st.error(f"Error loading image: {e}")
        st.stop()
        

    # Step 1: Enter metadata
    if st.session_state.step == 1:
        st.write("## Step 1: Enter Plot Information")
        plot_name = st.text_input("Enter plot name (e.g. Author_Year_FigNo)", key="plot_name_input")
        num_sandstones = st.number_input("How many sandstones?", min_value=1, step=1, key="num_sandstones_input")
        
        col1, col2 = st.columns([1, 1])
        with col1:
            if st.button("Next: Calibrate Axes", key="next_to_calibration"):
                if plot_name and num_sandstones:
                    st.session_state.plot_name = plot_name
                    st.session_state.num_sandstones = num_sandstones
                    st.session_state.step = 2
                    st.rerun()
                else:
                    st.error("Please fill in all fields")
        
        # No back button needed for step 1 since it's the first step

    # Step 2: Calibrate Axes
    elif st.session_state.step == 2:
        st.write("## Step 2: Calibrate Axes")
        
        # Call calibration function
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
        
        # Get sandstone name
        sandstone_name = st.text_input(
            f"Enter name for sandstone {current_idx + 1}:", 
            key=f"sandstone_name_{current_idx}"
        )
        
        # Initialize variables
        points = None
        confirm_button_enabled = False
        
        if sandstone_name:
            # Check for duplicate names
            if sandstone_name in st.session_state.sandstone_names:
                st.error("Sandstone name already used. Please choose a different name.")
            else:
                # Extract points for this sandstone
                points = extract_points_streamlit(
                    img_pil, 
                    sandstone_name, 
                    st.session_state.pixel_to_data
                )
                
                if points:
                    # Show current points
                    st.write(f"Points extracted for {sandstone_name}: {len(points)}")
                    confirm_button_enabled = True
        
        # Buttons always shown below the plot
        col1, col2, col3 = st.columns([1, 1, 1])
        
        with col1:
            if confirm_button_enabled:
                if st.button(f"Confirm points for {sandstone_name}", key=f"confirm_points_{current_idx}"):
                    # Add points to session state
                    st.session_state.data_points.extend(points)
                    st.session_state.sandstone_names.append(sandstone_name)
                    st.session_state.sandstone_index += 1
                    
                    # Check if we're done
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

    # Step 4: Show results and download
    elif st.session_state.step == 4:
        st.write("## Step 4: Results")
        st.success("Extraction Complete!")
        
        if st.session_state.data_points:
            df = pd.DataFrame(st.session_state.data_points)
            st.dataframe(df)
            
            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button(
                "Download CSV", 
                csv, 
                file_name=f"{st.session_state.plot_name}_data.csv",
                mime="text/csv"
            )
        else:
            st.warning("No data points extracted")
        
        col1, col2, col3 = st.columns([1, 1, 1])
        
        with col1:
            if st.button("Start Over", key="start_over"):
                # Reset all session state
                for key in list(st.session_state.keys()):
                    del st.session_state[key]
                st.rerun()
        
        with col2:
            if st.button("Back to Point Extraction", key="back_to_extraction"):
                go_back()
                st.rerun()
        
        with col3:
            if st.button("Back to Calibration", key="back_to_calibration_from_results"):
                st.session_state.step = 2
                # Reset extraction data
                st.session_state.sandstone_index = 0
                st.session_state.data_points = []
                st.session_state.sandstone_names = []
                st.rerun()

else:
    st.info("Please upload an image to begin")