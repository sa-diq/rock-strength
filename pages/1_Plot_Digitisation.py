import os
import sys
import streamlit as st
from PIL import Image
import pandas as pd
from datetime import datetime

# Add the project root to the path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core.calibrate_axes_streamlit import calibrate_axes_streamlit
from core.extract_points_streamlit import extract_points_streamlit
from core.database import db_manager
from navigation import create_navigation

st.set_page_config(page_title="Digitise Plots", page_icon="🔬", layout="wide")

# Initialize custom navigation
create_navigation()

def init_session_state():
    """Initialize session state for digitization workflow"""
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
    keys_to_reset = ["step", "sandstone_index", "data_points", "pixel_to_data", 
                     "sandstone_names", "doi", "figure_number", "plot_identifier", "num_sandstones", "uploaded_file"]
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
    3: "Step 3: Extract Data Points",
    4: "Step 4: Save Results"
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
        st.image(img_pil, caption="Uploaded Plot", use_container_width=True)
    except Exception as e:
        st.error(f"Error loading image: {e}")
        st.stop()

    # Step 1: Enter metadata
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
        
        # DOI validation and duplicate checking
        validation_messages = []
        duplicate_warning = False
        plot_identifier = None
        
        if doi and figure_number:
            # Validate DOI format
            if not validate_doi(doi):
                validation_messages.append("⚠️ Invalid DOI format. Please check your DOI.")
            else:
                # Generate plot identifier
                clean_doi = format_doi_display(doi)
                plot_identifier = db_manager.generate_plot_identifier(clean_doi, figure_number)
                
                # Check for duplicates
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
                st.session_state.num_sandstones = num_sandstones
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

    # Step 3: Extract points for each sandstone
    elif st.session_state.step == 3:
        st.markdown("### 📍 Data Point Extraction")
        
        current_idx = st.session_state.sandstone_index
        total_sandstones = st.session_state.num_sandstones
        
        # Progress indicator
        progress = (current_idx + 1) / total_sandstones
        st.progress(progress, text=f"Sandstone {current_idx + 1} of {total_sandstones}")
        
        sandstone_name = st.text_input(
            f"Name for Sandstone {current_idx + 1}:", 
            placeholder="e.g., Berea_Sandstone",
            key=f"sandstone_name_{current_idx}"
        )
        
        points = None
        confirm_button_enabled = False
        
        if sandstone_name:
            if sandstone_name in st.session_state.sandstone_names:
                st.error("❌ Sandstone name already used. Please choose a different name.")
            else:
                points = extract_points_streamlit(
                    img_pil, 
                    sandstone_name, 
                    st.session_state.pixel_to_data
                )
                
                if points:
                    st.success(f"✅ {len(points)} points extracted for {sandstone_name}")
                    confirm_button_enabled = True
        
        # Navigation buttons
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("⬅️ Back to Calibration"):
                go_back()
                st.rerun()
        
        with col2:
            if current_idx > 0:
                if st.button("↩️ Previous Sandstone"):
                    go_back_one_sandstone()
                    st.rerun()
        
        with col3:
            if confirm_button_enabled:
                if st.button(f"✅ Confirm {sandstone_name}", type="primary"):
                    st.session_state.data_points.extend(points)
                    st.session_state.sandstone_names.append(sandstone_name)
                    st.session_state.sandstone_index += 1
                    
                    if st.session_state.sandstone_index >= total_sandstones:
                        st.session_state.step = 4
                    
                    st.rerun()
            else:
                st.button("✅ Confirm Points", disabled=True)

    # Step 4: Results and save
    elif st.session_state.step == 4:
        st.markdown("### 🎉 Digitization Complete!")
        
        if st.session_state.data_points:
            # Show summary
            df = pd.DataFrame(st.session_state.data_points)
            
            # Display plot information
            st.markdown("#### 📊 Plot Information")
            col1, col2 = st.columns(2)
            with col1:
                st.write(f"**DOI:** {st.session_state.doi}")
                st.write(f"**Figure:** {st.session_state.figure_number}")
            with col2:
                st.write(f"**Identifier:** {st.session_state.plot_identifier}")
                st.write(f"**Sandstones:** {len(st.session_state.sandstone_names)}")
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("📊 Total Points", len(df))
            with col2:
                st.metric("🪨 Sandstone Datasets", len(st.session_state.sandstone_names))
            with col3:
                st.metric("📏 P Range", f"{df['P(MPa)'].min():.1f} - {df['P(MPa)'].max():.1f}")
            
            # Data preview
            st.markdown("#### 📋 Data Preview")
            st.dataframe(df, use_container_width=True)
            
            # Action buttons
            col1, col2, col3 = st.columns(3)
            
            with col1:
                # Download CSV
                csv = df.to_csv(index=False).encode('utf-8')
                filename = f"{st.session_state.plot_identifier}_data.csv"
                st.download_button(
                    "📥 Download CSV", 
                    csv, 
                    file_name=filename,
                    mime="text/csv",
                    help="Download data as CSV file"
                )
            
            with col2:
                # Save to database
                if st.button("💾 Save to Database", type="primary"):
                    try:
                        # Save image file
                        image_path = save_uploaded_image(
                            st.session_state.uploaded_file, 
                            st.session_state.plot_identifier
                        )
                        
                        # Prepare plot data
                        plot_data = {
                            'doi': st.session_state.doi,
                            'figure_number': st.session_state.figure_number,
                            'plot_identifier': st.session_state.plot_identifier,
                            'image_path': image_path,
                            'x_axis_range': f"{st.session_state.get('x1_data', 0)} to {st.session_state.get('x2_data', 0)}",
                            'y_axis_range': f"{st.session_state.get('y1_data', 0)} to {st.session_state.get('y2_data', 0)}",
                            'data_points': st.session_state.data_points
                        }
                        
                        plot_id = db_manager.save_complete_plot(plot_data)
                        st.success(f"✅ Saved to database! Plot ID: {plot_id}")
                        
                    except Exception as e:
                        st.error(f"❌ Error saving: {e}")
            
            with col3:
                # Start new digitization
                if st.button("🔄 Start New Plot"):
                    reset_digitization()
                    st.rerun()
            
            # Back button
            st.markdown("---")
            if st.button("⬅️ Back to Point Extraction"):
                go_back()
                st.rerun()
        
        else:
            st.error("❌ No data points found!")
            if st.button("⬅️ Back to Point Extraction"):
                go_back()
                st.rerun()

else:
    st.info("👆 Please upload a Q-P plot image to begin digitization")
    
    # Show helpful instructions
    st.markdown("""
    ### 📋 Instructions
    1. **Upload** a clear image of your Q-P plot
    2. **Enter** DOI and figure number from the research paper  
    3. **Calibrate** by clicking on known axis points
    4. **Extract** data points for each sandstone
    5. **Save** your digitized data
    
    ### 💡 Tips
    - Use high-resolution images for better accuracy
    - Enter complete DOI (e.g., 10.1016/j.jrmge.2023.02.015)
    - Include figure letters/numbers (e.g., 1a, 2b, 3)
    - Ensure axes are clearly visible in the image
    
    ### 📄 DOI Format Examples
    - `10.1016/j.jrmge.2023.02.015`
    - `https://doi.org/10.1016/j.jrmge.2023.02.015`
    - `doi:10.1016/j.jrmge.2023.02.015`
    """)