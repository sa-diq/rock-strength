import os
import sys
import streamlit as st
from PIL import Image
import pandas as pd
from datetime import datetime
import matplotlib.pyplot as plt

# Add the project root to the path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core.calibrate_axes_streamlit import calibrate_axes_streamlit
from core.extract_points_streamlit import extract_points_streamlit
from core.database import db_manager
from core.recreate_plot import (
    create_single_sandstone_validation_overlay, 
    aggregate_validated_sandstones_for_save,
    create_progress_indicator
)
from navigation import create_navigation

st.set_page_config(page_title="Digitise Plots", page_icon="🔬", layout="wide")

# Initialize custom navigation
create_navigation()

def init_session_state():
    """Initialize session state for per-sandstone digitization workflow"""
    defaults = {
        "step": 1,
        # Per-sandstone workflow state
        "current_sandstone_index": 0,
        "sandstone_validation_status": "extract",  # "extract" | "validate" | "confirmed"
        "extract_sub_phase": "name_entry",  # "name_entry" | "point_extraction"
        "validated_sandstones": [],  # List of completed sandstone data
        "current_sandstone_name": "",
        "current_sandstone_points": [],
        # Existing state (keep for compatibility)
        "pixel_to_data": None,
        "total_sandstones": 0
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

def save_uploaded_image(uploaded_file, plot_identifier):
    """Save uploaded image to uploads directory"""
    os.makedirs("uploads", exist_ok=True)
    
    # Create filename with timestamp to avoid conflicts
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_extension = uploaded_file.name.split('.')[-1]
    filename = f"{plot_identifier}_{timestamp}.{file_extension}"
    filepath = os.path.join("uploads", filename)
    
    # Save the file
    with open(filepath, "wb") as f:
        f.write(uploaded_file.getbuffer())
    
    return filepath

def reset_digitization():
    """Reset all digitization session state"""
    keys_to_reset = [
        "step", "current_sandstone_index", "sandstone_validation_status", 
        "extract_sub_phase", "validated_sandstones", "current_sandstone_name", 
        "current_sandstone_points", "pixel_to_data", "doi", "figure_number", 
        "plot_identifier", "total_sandstones", "uploaded_file"
    ]
    for key in keys_to_reset:
        if key in st.session_state:
            del st.session_state[key]
    st.session_state.step = 1

def validate_doi(doi: str) -> bool:
    """Basic DOI validation"""
    if not doi:
        return False
    
    # Remove common prefixes
    clean_doi = doi.replace('https://doi.org/', '').replace('http://doi.org/', '').replace('doi:', '').strip()
    
    # Basic DOI pattern: starts with 10. followed by registrant code
    if not clean_doi.startswith('10.'):
        return False
    
    # Should contain at least one slash after the registrant code
    if '/' not in clean_doi[3:]:
        return False
    
    return True

def format_doi_display(doi: str) -> str:
    """Format DOI for display (remove protocols)"""
    return doi.replace('https://doi.org/', '').replace('http://doi.org/', '').replace('doi:', '').strip()

def go_back():
    """Handle going back to previous step"""
    if st.session_state.step == 2:
        st.session_state.step = 1
    elif st.session_state.step == 3:
        # Handle per-sandstone back navigation
        if st.session_state.sandstone_validation_status == "validate":
            # Back to point extraction
            st.session_state.sandstone_validation_status = "extract"
            st.session_state.extract_sub_phase = "point_extraction"
        elif st.session_state.sandstone_validation_status == "extract":
            if st.session_state.extract_sub_phase == "point_extraction":
                # Back to name entry
                st.session_state.extract_sub_phase = "name_entry"
            elif st.session_state.extract_sub_phase == "name_entry":
                if st.session_state.current_sandstone_index > 0:
                    # Back to previous sandstone - go to validate state so user can see the validation overlay
                    st.session_state.current_sandstone_index -= 1
                    st.session_state.sandstone_validation_status = "validate"
                    
                    # Load previous sandstone data from the validated list
                    prev_sandstone = st.session_state.validated_sandstones[-1]
                    st.session_state.current_sandstone_name = prev_sandstone['name']
                    st.session_state.current_sandstone_points = prev_sandstone['points']
                    
                    # IMPORTANT: Remove from validated list to avoid duplicates when user validates again
                    st.session_state.validated_sandstones.pop()
                else:
                    # Back to calibration
                    st.session_state.step = 2
    elif st.session_state.step == 4:
        st.session_state.step = 3

def proceed_to_next_sandstone():
    """Move to next sandstone or complete workflow"""
    # Save current sandstone to validated list
    current_sandstone_data = {
        'name': st.session_state.current_sandstone_name,
        'points': st.session_state.current_sandstone_points.copy()
    }
    
    # Check if we're updating existing or adding new
    existing_index = None
    for i, sandstone in enumerate(st.session_state.validated_sandstones):
        if sandstone['name'] == current_sandstone_data['name']:
            existing_index = i
            break
    
    if existing_index is not None:
        # Update existing
        st.session_state.validated_sandstones[existing_index] = current_sandstone_data
    else:
        # Add new
        st.session_state.validated_sandstones.append(current_sandstone_data)
    
    # Check if this was the last sandstone
    if st.session_state.current_sandstone_index + 1 >= st.session_state.total_sandstones:
        # LAST SANDSTONE: Auto-save and complete
        try:
            # Aggregate all validated data
            all_data_points = aggregate_validated_sandstones_for_save(st.session_state.validated_sandstones)
            
            # Save image file
            image_path = save_uploaded_image(
                st.session_state.uploaded_file, 
                st.session_state.plot_identifier
            )
            
            # Prepare plot data for database
            plot_data = {
                'doi': st.session_state.doi,
                'figure_number': st.session_state.figure_number,
                'plot_identifier': st.session_state.plot_identifier,
                'image_path': image_path,
                'x_axis_range': f"{st.session_state.get('x1_data', 0)} to {st.session_state.get('x2_data', 0)}",
                'y_axis_range': f"{st.session_state.get('y1_data', 0)} to {st.session_state.get('y2_data', 0)}",
                'data_points': all_data_points
            }
            
            # Save to database
            plot_id = db_manager.save_complete_plot(plot_data)
            st.session_state.final_plot_id = plot_id
            st.session_state.step = 4  # Go to completion page
            
        except Exception as e:
            st.error(f"❌ Error saving plot: {e}")
            # Don't advance step, keep data safe
            return False
    else:
        # NEXT SANDSTONE: Advance to next
        st.session_state.current_sandstone_index += 1
        st.session_state.sandstone_validation_status = "extract"
        st.session_state.extract_sub_phase = "name_entry"  # Reset to name entry
        st.session_state.current_sandstone_name = ""
        st.session_state.current_sandstone_points = []
    
    return True

# Initialize session state
init_session_state()

# Page header
st.title("🔬 Digitize Q-P Plots")
st.markdown("---")

# Progress indicator
step = st.session_state.get('step', 1)
progress_text = {
    1: "Step 1: Upload & Configure",
    2: "Step 2: Calibrate Axes", 
    3: "Step 3: Extract & Validate Data Points",
    4: "Step 4: Completion"
}

st.info(f"**{progress_text.get(step, 'Unknown Step')}**")

# File uploader (always visible)
uploaded_file = st.file_uploader(
    "Upload Q-P Plot Image", 
    type=["png", "jpg", "jpeg"],
    help="Upload a clear image of your Q-P plot"
)

if uploaded_file:
    try:
        img_pil = Image.open(uploaded_file)
        st.image(img_pil, caption="Uploaded Plot")
    except Exception as e:
        st.error(f"Error loading image: {e}")
        st.stop()

    # Step 1: Enter metadata (unchanged from original)
    if st.session_state.step == 1:
        st.markdown("### 📝 Publication Information")
        
        col1, col2 = st.columns([2, 1])
        with col1:
            doi = st.text_input(
                "DOI", 
                placeholder="e.g., 10.1016/j.jrmge.2023.02.015 or https://doi.org/10.1016/j.jrmge.2023.02.015",
                help="Enter the DOI of the research paper",
                key="doi_input"
            )
        with col2:
            figure_number = st.text_input(
                "Figure Number", 
                placeholder="e.g., 1, 2a, 3b",
                help="Figure number or identifier from the paper",
                key="figure_number_input"
            )
        
        col3, col4 = st.columns([1, 1])
        with col3:
            num_sandstones = st.number_input(
                "Number of Sandstone Datasets", 
                min_value=1, 
                step=1, 
                help="How many different sandstone datasets are in this plot?",
                key="num_sandstones_input"
            )
        
        # DOI validation and duplicate checking (unchanged)
        validation_messages = []
        duplicate_warning = False
        plot_identifier = None
        
        if doi and figure_number:
            if not validate_doi(doi):
                validation_messages.append("⚠️ Invalid DOI format. Please check your DOI.")
            else:
                clean_doi = format_doi_display(doi)
                plot_identifier = db_manager.generate_plot_identifier(clean_doi, figure_number)
                
                try:
                    if db_manager.check_plot_exists(clean_doi, figure_number):
                        validation_messages.append(f"⚠️ Plot already exists: {clean_doi} Figure {figure_number}")
                        duplicate_warning = True
                    else:
                        validation_messages.append(f"✅ Plot identifier: {plot_identifier}")
                except Exception as e:
                    validation_messages.append(f"❌ Error checking for duplicates: {e}")
        
        # Display validation messages
        for message in validation_messages:
            if "⚠️" in message or "❌" in message:
                st.warning(message)
            else:
                st.success(message)
        
        # Navigation buttons
        col1, col2 = st.columns([1, 3])
        with col1:
            if st.button("🔄 Reset", help="Start over"):
                reset_digitization()
                st.rerun()
        
        with col2:
            button_disabled = not (doi and figure_number and num_sandstones and validate_doi(doi) and not duplicate_warning)
            if st.button("➡️ Next: Calibrate Axes", type="primary", disabled=button_disabled):
                clean_doi = format_doi_display(doi)
                st.session_state.doi = clean_doi
                st.session_state.figure_number = figure_number
                st.session_state.plot_identifier = plot_identifier
                st.session_state.total_sandstones = num_sandstones
                st.session_state.uploaded_file = uploaded_file
                st.session_state.step = 2
                st.rerun()

    # Step 2: Calibrate Axes
    elif st.session_state.step == 2:
        st.markdown("### 📏 Axis Calibration")
        
        pixel_to_data = calibrate_axes_streamlit(img_pil)
        
        if pixel_to_data is not None:
            st.session_state.pixel_to_data = pixel_to_data
            
            # Navigation buttons
            col1, col2 = st.columns(2)
            with col1:
                if st.button("⬅️ Back to Setup"):
                    go_back()
                    st.rerun()
            with col2:
                if st.button("➡️ Next: Extract Points", type="primary"):
                    st.session_state.step = 3
                    st.rerun()

    # Step 3: Per-Sandstone Extraction and Validation
    elif st.session_state.step == 3:
        st.markdown("### 📍 Per-Sandstone Data Extraction")
        
        # Progress indicator
        create_progress_indicator(
            st.session_state.current_sandstone_index,
            st.session_state.total_sandstones,
            [s['name'] for s in st.session_state.validated_sandstones] + [st.session_state.current_sandstone_name],
            st.session_state.validated_sandstones
        )
        
        current_sandstone_num = st.session_state.current_sandstone_index + 1
        status = st.session_state.sandstone_validation_status
        
        if status == "extract":
            if st.session_state.extract_sub_phase == "name_entry":
                # SUB-PHASE 1: NAME ENTRY ONLY
                st.markdown(f"#### 🪨 Sandstone {current_sandstone_num} - Enter Name")
                
                # Get sandstone name
                sandstone_name = st.text_input(
                    f"Name for Sandstone {current_sandstone_num}:", 
                    value=st.session_state.current_sandstone_name,
                    placeholder="e.g., Berea_Sandstone",
                    key=f"sandstone_name_{current_sandstone_num}"
                )
                
                # Show instruction text
                st.markdown("**Press Enter When Done**")
                
                # Check for name change and validation
                if sandstone_name and sandstone_name != st.session_state.current_sandstone_name:
                    # Check for duplicate names
                    existing_names = [s['name'] for s in st.session_state.validated_sandstones]
                    if sandstone_name in existing_names:
                        st.error("❌ Sandstone name already used. Please choose a different name.")
                    else:
                        # Valid name - update state and proceed to point extraction
                        st.session_state.current_sandstone_name = sandstone_name
                        st.session_state.current_sandstone_points = []  # Reset points
                        st.session_state.extract_sub_phase = "point_extraction"
                        st.rerun()
                
                # Navigation buttons - only back
                col1, col2 = st.columns([1, 3])
                with col1:
                    if st.button("⬅️ Back"):
                        go_back()
                        st.rerun()
                
                with col2:
                    if st.session_state.current_sandstone_index > 0:
                        if st.button("↩️ Previous Sandstone"):
                            go_back()
                            st.rerun()
            
            elif st.session_state.extract_sub_phase == "point_extraction":
                # SUB-PHASE 2: POINT EXTRACTION
                st.markdown(f"#### 📍 Sandstone {current_sandstone_num} - Extract Points")
                st.markdown(f"**Current sandstone:** {st.session_state.current_sandstone_name}")
                
                # Extract points
                points = extract_points_streamlit(
                    img_pil, 
                    st.session_state.current_sandstone_name, 
                    st.session_state.pixel_to_data
                )
                
                # Update the workflow state
                st.session_state.current_sandstone_points = points
                
                # Navigation buttons
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    if st.button("⬅️ Back to Name"):
                        go_back()
                        st.rerun()
                
                with col2:
                    if st.session_state.current_sandstone_index > 0:
                        if st.button("↩️ Previous Sandstone"):
                            go_back()
                            st.rerun()
                
                with col3:
                    if st.button("➡️ Validate Points", type="primary"):
                        st.session_state.sandstone_validation_status = "validate"
                        st.rerun()
        
        elif status == "validate":
            # VALIDATE PHASE: Show validation overlay and get user confirmation
            st.markdown(f"#### 🔍 Sandstone {current_sandstone_num} - Validation")
            
            if st.session_state.current_sandstone_points:
                # Create and display validation overlay
                try:
                    validation_fig = create_single_sandstone_validation_overlay(
                        img_pil, 
                        st.session_state.current_sandstone_name,
                        st.session_state.current_sandstone_points
                    )
                    st.pyplot(validation_fig)
                    plt.close(validation_fig)  # Prevent memory leaks
                    
                except Exception as e:
                    st.error(f"❌ Error creating validation overlay: {e}")
                
                # Validation question
                st.markdown("---")
                st.markdown("#### 🔍 Visual Validation")
                st.write(f"**Do the extracted points (+ markers) accurately represent the {st.session_state.current_sandstone_name} data points?**")
                
                # Validation controls
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    if st.button("⬅️ Back to Extract"):
                        st.session_state.sandstone_validation_status = "extract"
                        st.session_state.extract_sub_phase = "point_extraction"
                        st.rerun()
                
                with col2:
                    if st.button("❌ Re-extract Points", help="Points don't look accurate"):
                        st.session_state.sandstone_validation_status = "extract"
                        st.session_state.extract_sub_phase = "point_extraction"
                        st.session_state.current_sandstone_points = []
                        st.rerun()
                
                with col3:
                    next_action = "Save All & Complete" if current_sandstone_num >= st.session_state.total_sandstones else f"Next: Sandstone {current_sandstone_num + 1}"
                    if st.button(f"✅ {next_action}", type="primary", help="Points look good"):
                        if proceed_to_next_sandstone():
                            st.rerun()
            
            else:
                st.error("❌ No points to validate!")
                if st.button("⬅️ Back to Extract"):
                    st.session_state.sandstone_validation_status = "extract"
                    st.session_state.extract_sub_phase = "point_extraction"
                    st.rerun()
        
    # Step 4: Completion Page (NEW)
    elif st.session_state.step == 4:
        st.markdown("### 🎉 Digitization Complete!")
        
        # Success message
        st.success("✅ All sandstones have been successfully digitized and saved!")
        
        # Summary information
        total_points = sum(len(s['points']) for s in st.session_state.validated_sandstones)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Plot Saved", f"ID: {st.session_state.get('final_plot_id', 'Unknown')}")
        with col2:
            st.metric("Sandstone Datasets", len(st.session_state.validated_sandstones))
        with col3:
            st.metric("Total Data Points", total_points)
        
        # Show completed sandstones
        st.markdown("#### 📊 Completed Sandstones")
        for i, sandstone in enumerate(st.session_state.validated_sandstones):
            st.write(f"**{i+1}. {sandstone['name']}**: {len(sandstone['points'])} points")
        
        # Action buttons
        col1, col2 = st.columns(2)
        
        with col1:
            # Download all data as CSV - Made more prominent
            if st.session_state.validated_sandstones:
                all_points = aggregate_validated_sandstones_for_save(st.session_state.validated_sandstones)
                df = pd.DataFrame(all_points)
                csv = df.to_csv(index=False).encode('utf-8')
                filename = f"{st.session_state.plot_identifier}_complete_data.csv"
                st.download_button(
                    "📥 Download Digitised Plot", 
                    csv, 
                    file_name=filename,
                    mime="text/csv",
                    help="Download data as CSV file",
                    type="secondary"
                )
        
        with col2:
            # Start new digitization
            if st.button("🔄 Digitize Another Plot", type="primary"):
                reset_digitization()
                st.rerun()
        
        # Additional info
        st.markdown("---")
        st.info("💡 **Tip**: Use the 'Data Management' tab above to view, search, and manage all your digitized plots.")

else:
    st.info("👆 Please upload a Q-P plot image to begin digitization")
    
    # Show helpful instructions (unchanged from original)
    st.markdown("""
    ### 📋 Instructions
    1. **Upload** a clear image of your Q-P plot
    2. **Enter** DOI and figure number from the research paper  
    3. **Calibrate** by clicking on known axis points
    4. **Extract & Validate** data points for each sandstone individually
    5. **Auto-save** occurs after validating the last sandstone
    
    ### 💡 Tips
    - Use high-resolution images for better accuracy
    - Enter complete DOI (e.g., 10.1016/j.jrmge.2023.02.015)
    - Include figure letters/numbers (e.g., 1a, 2b, 3)
    - Ensure axes are clearly visible in the image
    - **New**: Each sandstone is validated individually for better quality control
    
    ### 📄 DOI Format Examples
    - `10.1016/j.jrmge.2023.02.015`
    - `https://doi.org/10.1016/j.jrmge.2023.02.015`
    - `doi:10.1016/j.jrmge.2023.02.015`
    """)