import streamlit as st
from PIL import Image
from core.streamlit_drawing import get_click_coordinates_simple

def calibrate_axes_streamlit(image_pil):
    st.write("### X-Axis Calibration")
    st.write("Click 2 points along the X-axis (left to right)")
    
    # X-axis points (automatically proceed after 2 points)
    x_points = get_click_coordinates_simple(
        image_pil, 
        "Click 2 points along the X-axis", 
        key="x_axis_calib",
        max_points=2
    )
    
    if len(x_points) >= 2:
        x1_pixel, y1_pixel = x_points[0]
        x2_pixel, y2_pixel = x_points[1]
        
        st.write(f"X-axis points selected: ({x1_pixel:.1f}, {y1_pixel:.1f}) and ({x2_pixel:.1f}, {y2_pixel:.1f})")
        
        col1, col2 = st.columns(2)
        with col1:
            x1_data = st.number_input("Enter actual X-axis value for first point", key="x1_data")
        with col2:
            x2_data = st.number_input("Enter actual X-axis value for second point", key="x2_data")
        
        if x1_data != x2_data:  # Ensure we have different values
            st.write("### Y-Axis Calibration")
            st.write("Click 2 points along the Y-axis (bottom to top)")
            
            # Y-axis points (automatically proceed after 2 points)
            y_points = get_click_coordinates_simple(
                image_pil, 
                "Click 2 points along the Y-axis", 
                key="y_axis_calib",
                max_points=2
            )
            
            if len(y_points) >= 2:
                x3_pixel, y3_pixel = y_points[0]
                x4_pixel, y4_pixel = y_points[1]
                
                st.write(f"Y-axis points selected: ({x3_pixel:.1f}, {y3_pixel:.1f}) and ({x4_pixel:.1f}, {y4_pixel:.1f})")
                
                col3, col4 = st.columns(2)
                with col3:
                    y1_data = st.number_input("Enter actual Y-axis value for first point", key="y1_data")
                with col4:
                    y2_data = st.number_input("Enter actual Y-axis value for second point", key="y2_data")
                
                if y1_data != y2_data:  # Ensure we have different values
                    # Check if pixel coordinates are valid for calibration
                    x_pixel_diff = x2_pixel - x1_pixel
                    y_pixel_diff = y4_pixel - y3_pixel
                    
                    if abs(x_pixel_diff) < 5:  # X points too close together
                        st.error("❌ X-axis calibration points are too close together or identical. Please select two points that are further apart horizontally.")
                        st.write(f"Point 1: ({x1_pixel:.1f}, {y1_pixel:.1f})")
                        st.write(f"Point 2: ({x2_pixel:.1f}, {y2_pixel:.1f})")
                        st.write(f"Horizontal distance: {abs(x_pixel_diff):.1f} pixels (minimum: 5 pixels)")
                        
                        # Add button to reset X-axis calibration
                        if st.button("🔄 Reset X-axis Calibration", key="reset_x_calibration"):
                            if "x_axis_calib_points" in st.session_state:
                                del st.session_state["x_axis_calib_points"]
                            st.rerun()
                        return None
                        
                    elif abs(y_pixel_diff) < 5:  # Y points too close together
                        st.error("❌ Y-axis calibration points are too close together or identical. Please select two points that are further apart vertically.")
                        st.write(f"Point 1: ({x3_pixel:.1f}, {y3_pixel:.1f})")
                        st.write(f"Point 2: ({x4_pixel:.1f}, {y4_pixel:.1f})")
                        st.write(f"Vertical distance: {abs(y_pixel_diff):.1f} pixels (minimum: 5 pixels)")
                        
                        # Add button to reset Y-axis calibration
                        if st.button("🔄 Reset Y-axis Calibration", key="reset_y_calibration"):
                            if "y_axis_calib_points" in st.session_state:
                                del st.session_state["y_axis_calib_points"]
                            st.rerun()
                        return None
                    
                    else:
                        # Create transformation function with error handling
                        def pixel_to_data(x_pixel, y_pixel):
                            try:
                                # Check for division by zero before calculation
                                x_pixel_diff = x2_pixel - x1_pixel
                                y_pixel_diff = y4_pixel - y3_pixel
                                
                                if abs(x_pixel_diff) < 0.1:  # Essentially zero
                                    st.error("❌ X-axis calibration error: Points are identical")
                                    return 0, 0
                                
                                if abs(y_pixel_diff) < 0.1:  # Essentially zero  
                                    st.error("❌ Y-axis calibration error: Points are identical")
                                    return 0, 0
                                
                                # Linear interpolation for X
                                x_data = x1_data + (x_pixel - x1_pixel) * (x2_data - x1_data) / x_pixel_diff
                                # Linear interpolation for Y
                                y_data = y1_data + (y_pixel - y3_pixel) * (y2_data - y1_data) / y_pixel_diff
                                
                                return x_data, y_data
                                
                            except ZeroDivisionError:
                                st.error("❌ Calibration error: Division by zero. Please recalibrate your axes.")
                                return 0, 0
                            except Exception as e:
                                st.error(f"❌ Calibration error: {e}")
                                return 0, 0
                        st.success("✅ Axes calibration complete!")
                        st.write("**Calibration Summary:**")
                        st.write(f"- X-axis: {x1_data} to {x2_data} (pixel range: {x1_pixel:.1f} to {x2_pixel:.1f})")
                        st.write(f"- Y-axis: {y1_data} to {y2_data} (pixel range: {y3_pixel:.1f} to {y4_pixel:.1f})")
                        
                        # Show calibration quality
                        st.write("**Calibration Quality:**")
                        st.write(f"- X-axis pixel span: {abs(x_pixel_diff):.1f} pixels")
                        st.write(f"- Y-axis pixel span: {abs(y_pixel_diff):.1f} pixels")
                        
                        return pixel_to_data
                else:
                    st.warning("Please enter different Y-axis values")
            else:
                st.info("Please click 2 points on the Y-axis")
        else:
            st.warning("Please enter different X-axis values")
    else:
        st.info("Please click 2 points on the X-axis")
    
    return None