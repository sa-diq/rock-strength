import streamlit as st
from PIL import Image
from core.streamlit_drawing import get_click_coordinates

def calibrate_axes_streamlit(image_pil):
    st.write("### X-Axis Calibration")
    st.write("Click 2 points along the X-axis (left to right)")
    
    # X-axis points
    x_points = get_click_coordinates(image_pil, "Click 2 points along the X-axis", key="x_axis_calib")
    
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
            
            # Y-axis points
            y_points = get_click_coordinates(image_pil, "Click 2 points along the Y-axis", key="y_axis_calib")
            
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
                    # Create transformation function
                    def pixel_to_data(x_pixel, y_pixel):
                        # Linear interpolation for X
                        x_data = x1_data + (x_pixel - x1_pixel) * (x2_data - x1_data) / (x2_pixel - x1_pixel)
                        # Linear interpolation for Y
                        y_data = y1_data + (y_pixel - y3_pixel) * (y2_data - y1_data) / (y4_pixel - y3_pixel)
                        return x_data, y_data
                    
                    st.success("✅ Axes calibration complete!")
                    st.write("**Calibration Summary:**")
                    st.write(f"- X-axis: {x1_data} to {x2_data}")
                    st.write(f"- Y-axis: {y1_data} to {y2_data}")
                    
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