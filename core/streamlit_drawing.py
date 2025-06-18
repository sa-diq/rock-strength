# streamlit_drawing.py - Complete fixed version with automatic compatibility patch

# Apply compatibility patch before importing streamlit_drawable_canvas
def patch_drawable_canvas():
    """Patch streamlit-drawable-canvas to work with modern Streamlit versions"""
    try:
        # Try to import image_to_url from new location
        from streamlit.elements.lib.image_utils import image_to_url
        
        # Patch the old location that streamlit-drawable-canvas expects
        import streamlit.elements.image as st_image
        if not hasattr(st_image, 'image_to_url'):
            st_image.image_to_url = image_to_url
            print("✅ Applied compatibility patch for streamlit-drawable-canvas")
        
        return True
        
    except ImportError:
        try:
            # Fallback to old location (for older Streamlit versions)
            from streamlit.elements.image import image_to_url
            return True
        except ImportError:
            print("❌ Could not find image_to_url function")
            return False

# Apply the patch
patch_drawable_canvas()

# Now import the canvas component and other dependencies
from streamlit_drawable_canvas import st_canvas
import streamlit as st
import numpy as np

def get_click_coordinates(image, instructions, key, stroke_width=3):
    """
    Get click coordinates using the original drawable canvas - now with crosses!
    """
    st.write(instructions)
    canvas_result = st_canvas(
        fill_color="rgba(255, 0, 0, 0.1)",  # Very transparent fill
        stroke_width=3,  # Thicker stroke for cross effect
        stroke_color="#FF0000",
        background_color="#eee",
        background_image=image,
        update_streamlit=True,
        height=image.height,
        width=image.width,
        drawing_mode="point",
        point_display_radius=4,  # Smaller radius for cross-like appearance
        key=key
    )

    if canvas_result.json_data and canvas_result.json_data["objects"]:
        return [
            (obj["left"], obj["top"])
            for obj in canvas_result.json_data["objects"]
            if obj["type"] == "circle"
        ]
    return []

def get_click_coordinates_simple(image, instructions, key, max_points=None):
    """
    Simplified version for calibration that auto-proceeds after reaching max_points
    """
    st.write(instructions)
    
    # Show progress if max_points is specified
    if max_points:
        # Use session state to track completion
        completion_key = f"{key}_completed"
        if completion_key not in st.session_state:
            st.session_state[completion_key] = False
    
    canvas_result = st_canvas(
        fill_color="rgba(255, 0, 0, 0.1)",  # Very transparent fill
        stroke_width=3,  # Thicker stroke for cross effect
        stroke_color="#FF0000",
        background_color="#eee",
        background_image=image,
        update_streamlit=True,
        height=image.height,
        width=image.width,
        drawing_mode="point",
        point_display_radius=4,  # Smaller radius for cross-like appearance
        key=key
    )

    # Extract points
    points = []
    if canvas_result.json_data and canvas_result.json_data["objects"]:
        points = [
            (obj["left"], obj["top"])
            for obj in canvas_result.json_data["objects"]
            if obj["type"] == "circle"
        ]
    
    # Show current status
    if max_points:
        current_count = len(points)
        remaining = max_points - current_count
        
        if current_count >= max_points:
            st.success(f"✅ {max_points} points selected!")
            if completion_key in st.session_state:
                st.session_state[completion_key] = True
        else:
            st.write(f"📍 Points selected: {current_count}/{max_points} ({remaining} more needed)")
    else:
        st.write(f"📍 Points selected: {len(points)}")
    
    # Add control buttons
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🗑️ Clear Points", key=f"{key}_clear"):
            # Force canvas to clear by changing its key
            st.rerun()
    
    with col2:
        if points and st.button("✅ Confirm Points", key=f"{key}_confirm"):
            if not max_points or len(points) >= max_points:
                st.success("Points confirmed!")
    
    return points