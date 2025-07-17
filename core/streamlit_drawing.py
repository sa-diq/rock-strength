import streamlit as st
import numpy as np
from streamlit_image_coordinates import streamlit_image_coordinates

def get_point_color_selector(key_prefix):
    """
    Create a color selector for extraction points
    
    Args:
        key_prefix: Unique prefix for the selectbox key
        
    Returns:
        tuple: (color_hex, color_name) for the selected color
    """
    
    # Define color options
    color_options = {
        "🔵 Blue": "#0066FF",
        "🟢 Green": "#00AA00", 
        "🟡 Yellow": "#FFD700",
        "🟣 Purple": "#8A2BE2",
        "🟠 Orange": "#FF8C00",
        "🔴 Red": "#FF0000"
    }
    
    # Default to blue (most visible on most plots)
    selected_color_name = st.selectbox(
        "🎨 Point Color:",
        options=list(color_options.keys()),
        index=0,  # Default to first option
        key=f"{key_prefix}_color_selector",
        help="Choose a color that contrasts well with your plot's data points"
    )
    
    selected_color_hex = color_options[selected_color_name]
    
    return selected_color_hex, selected_color_name

def get_click_coordinates(image, instructions, key):
    """
    Get click coordinates using streamlit-image-coordinates
    
    Args:
        image: PIL Image object
        instructions: Instructions to show user
        key: Unique key for the component
        
    Returns:
        list: List of (x, y) coordinate tuples
    """
    st.write(instructions)
    
    # Color selector
    point_color, color_name = get_point_color_selector(key)
    
    # Show color tip
    st.info(f"💡 **Tip**: Using {color_name.split()[1]} points. Change color if they're hard to see on your plot.")
    
    # Initialize session state for storing points
    points_key = f"{key}_points"
    if points_key not in st.session_state:
        st.session_state[points_key] = []
    
    # Display image with coordinate capture
    value = streamlit_image_coordinates(
        image,
        key=f"{key}_image_coords",
        height=image.height,
        width=image.width
    )
    
    # Handle new clicks
    if value is not None and value["x"] is not None and value["y"] is not None:
        new_point = (value["x"], value["y"])
        
        # Check if this point is significantly different from existing points
        # (avoid duplicate clicks)
        is_new_point = True
        for existing_point in st.session_state[points_key]:
            if abs(existing_point[0] - new_point[0]) < 5 and abs(existing_point[1] - new_point[1]) < 5:
                is_new_point = False
                break
        
        if is_new_point:
            st.session_state[points_key].append(new_point)
            st.rerun()
    
    # Show current points with visual overlay
    if st.session_state[points_key]:
        st.success(f"✅ {len(st.session_state[points_key])} points selected with {color_name.split()[1]} markers!")
        
        # Display current points
        for i, (x, y) in enumerate(st.session_state[points_key]):
            st.write(f"Point {i+1}: ({x:.1f}, {y:.1f})")
    
    # Control buttons
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🗑️ Clear Points", key=f"{key}_clear"):
            st.session_state[points_key] = []
            st.rerun()
    
    with col2:
        if st.session_state[points_key]:
            if st.button("✅ Confirm Points", key=f"{key}_confirm"):
                st.success("Points confirmed!")
    
    return st.session_state[points_key]

def get_click_coordinates_simple(image, instructions, key, max_points=None):
    """
    Simplified version for calibration with streamlit-image-coordinates
    
    Args:
        image: PIL Image object
        instructions: Instructions to show user
        key: Unique key for the component
        max_points: Maximum number of points to collect
        
    Returns:
        list: List of (x, y) coordinate tuples
    """
    st.write(instructions)
    
    # Color selector
    point_color, color_name = get_point_color_selector(key)
    
    # Initialize session state for storing points
    points_key = f"{key}_points"
    if points_key not in st.session_state:
        st.session_state[points_key] = []
    
    # Display image with coordinate capture
    value = streamlit_image_coordinates(
        image,
        key=f"{key}_image_coords",
        height=image.height,
        width=image.width
    )
    
    # Handle new clicks
    if value is not None and value["x"] is not None and value["y"] is not None:
        new_point = (value["x"], value["y"])
        
        # Check if we haven't reached max points
        if max_points is None or len(st.session_state[points_key]) < max_points:
            # Check if this point is significantly different from existing points
            is_new_point = True
            for existing_point in st.session_state[points_key]:
                if abs(existing_point[0] - new_point[0]) < 5 and abs(existing_point[1] - new_point[1]) < 5:
                    is_new_point = False
                    break
            
            if is_new_point:
                st.session_state[points_key].append(new_point)
                st.rerun()
    
    # Show current status
    points = st.session_state[points_key]
    
    if max_points:
        current_count = len(points)
        remaining = max_points - current_count
        
        if current_count >= max_points:
            st.success(f"✅ {max_points} points selected with {color_name.split()[1]} markers!")
        else:
            st.write(f"📍 {color_name.split()[1]} points selected: {current_count}/{max_points} ({remaining} more needed)")
    else:
        st.write(f"📍 {color_name.split()[1]} points selected: {len(points)}")
    
    # Display current points
    for i, (x, y) in enumerate(points):
        st.write(f"Point {i+1}: ({x:.1f}, {y:.1f})")
    
    # Control buttons
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🗑️ Clear Points", key=f"{key}_clear"):
            st.session_state[points_key] = []
            st.rerun()
    
    with col2:
        if points and st.button("✅ Confirm Points", key=f"{key}_confirm"):
            if not max_points or len(points) >= max_points:
                st.success("Points confirmed!")
    
    return points