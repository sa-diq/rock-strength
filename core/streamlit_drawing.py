import streamlit as st
import numpy as np
from streamlit_image_coordinates import streamlit_image_coordinates
from PIL import Image, ImageDraw
import io

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

def create_image_with_points(original_image, points, color_hex, marker_size=8):
    """
    Create a copy of the image with points drawn on it
    
    Args:
        original_image: PIL Image object
        points: List of (x, y) tuples
        color_hex: Color for the points
        marker_size: Size of the point markers
        
    Returns:
        PIL Image with points drawn on it
    """
    # Create a copy of the original image and convert to RGBA for transparency
    img_copy = original_image.copy()
    if img_copy.mode != 'RGBA':
        img_copy = img_copy.convert('RGBA')
    
    # Create a transparent overlay for the markers
    overlay = Image.new('RGBA', img_copy.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    
    # Convert hex color to RGBA with transparency
    color_rgb = tuple(int(color_hex[i:i+2], 16) for i in (1, 3, 5))
    color_rgba = color_rgb + (180,)  # Alpha value of 180 (out of 255) for transparency
    
    # Draw each point as a thin cross
    for x, y in points:
        # Draw cross with thinner lines
        draw.line([x-marker_size, y, x+marker_size, y], fill=color_rgba, width=2)
        draw.line([x, y-marker_size, x, y+marker_size], fill=color_rgba, width=2)
    
    # Composite the overlay onto the original image
    result = Image.alpha_composite(img_copy, overlay)
    
    # Convert back to RGB if needed
    if original_image.mode == 'RGB':
        result = result.convert('RGB')
    
    return result

def get_click_coordinates(image, instructions, key):
    """
    Get click coordinates using streamlit-image-coordinates with visual feedback
    """
    st.write(instructions)
    
    # Color selector
    point_color, color_name = get_point_color_selector(key)
    st.info(f"💡 **Tip**: Using {color_name.split()[1]} points. Change colour if they're hard to see on your plot.")
    
    # Initialize session state
    points_key = f"{key}_points"
    reset_key = f"{key}_reset_counter"
    
    if points_key not in st.session_state:
        st.session_state[points_key] = []
    if reset_key not in st.session_state:
        st.session_state[reset_key] = 0
    
    # Create image with points drawn on it
    display_image = create_image_with_points(image, st.session_state[points_key], point_color)
    
    # Display image with coordinate capture
    value = streamlit_image_coordinates(
        display_image,
        key=f"{key}_image_coords_{st.session_state[reset_key]}",
        height=image.height,
        width=image.width
    )
    
    # Handle new clicks
    if value is not None and value["x"] is not None and value["y"] is not None:
        new_point = (value["x"], value["y"])
        
        # Check if this point is significantly different from existing points
        is_new_point = True
        for existing_point in st.session_state[points_key]:
            if abs(existing_point[0] - new_point[0]) < 10 and abs(existing_point[1] - new_point[1]) < 10:
                is_new_point = False
                break
        
        if is_new_point:
            st.session_state[points_key].append(new_point)
            st.rerun()
    
    # Show current points
    current_points = st.session_state[points_key]
    if current_points:
        st.success(f"✅ {len(current_points)} points selected with {color_name.split()[1]} markers!")
    else:
        st.write(f"📍 No {color_name.split()[1]} points selected yet")
    
    # Control buttons
    col1, col2= st.columns(2)
    
    with col1:
        if st.button("🗑️ Clear All", key=f"{key}_clear"):
            st.session_state[points_key] = []
            st.session_state[reset_key] += 1
            st.rerun()
    
    with col2:
        if current_points:
            if st.button("↩️ Undo Last", key=f"{key}_undo"):
                if len(st.session_state[points_key]) > 0:
                    st.session_state[points_key].pop()
                st.session_state[reset_key] += 1
                st.rerun()
        else:
            st.button("↩️ Undo Last", key=f"{key}_undo_disabled", disabled=True)
    
    return current_points

def get_click_coordinates_simple(image, instructions, key, max_points=None):
    """
    Simplified version for calibration with streamlit-image-coordinates and visual feedback
    
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
    reset_key = f"{key}_reset_counter"
    
    if points_key not in st.session_state:
        st.session_state[points_key] = []
    if reset_key not in st.session_state:
        st.session_state[reset_key] = 0
    
    # Create image with existing points drawn on it
    display_image = create_image_with_points(image, st.session_state[points_key], point_color)
    
    # Display image with coordinate capture - use reset counter to force component refresh
    value = streamlit_image_coordinates(
        display_image,
        key=f"{key}_image_coords_{st.session_state[reset_key]}",
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
                if abs(existing_point[0] - new_point[0]) < 10 and abs(existing_point[1] - new_point[1]) < 10:
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
    # for i, (x, y) in enumerate(points):
    #     st.write(f"Point {i+1}: ({x:.1f}, {y:.1f})")
    
    # Control buttons
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🗑️ Clear All", key=f"{key}_clear"):
            st.session_state[points_key] = []
            st.session_state[reset_key] += 1  # Force component reset
            st.rerun()
    
    with col2:
        if points:
            if st.button("↩️ Undo Last", key=f"{key}_undo"):
                st.session_state[points_key].pop()  # Remove last point
                st.session_state[reset_key] += 1  # Force component reset
                st.rerun()
        else:
            st.button("↩️ Undo Last", key=f"{key}_undo_disabled", disabled=True)
    
    # with col3:
    #     if points:
    #         if st.button("✅ Confirm Points", key=f"{key}_confirm"):
    #             if not max_points or len(points) >= max_points:
    #                 st.success("Points confirmed!")
    #     else:
    #         st.button("✅ Confirm Points", key=f"{key}_confirm_disabled", disabled=True)
    
    return points