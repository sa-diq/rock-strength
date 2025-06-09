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

# Step 1: Upload Image
if "step" not in st.session_state:
    st.session_state.step = 1
if "sandstone_index" not in st.session_state:
    st.session_state.sandstone_index = 0
if "data_points" not in st.session_state:
    st.session_state.data_points = []

uploaded_file = st.file_uploader("Upload Q-P Plot Image", type=["png", "jpg", "jpeg"])

if uploaded_file:
    img_pil = Image.open(uploaded_file)
    st.image(img_pil, caption="Uploaded Plot", use_container_width=True)

    # Step 2: Enter metadata
    if st.session_state.step == 1:
        plot_name = st.text_input("Enter plot name (e.g. Author_Year_FigNo)")
        num_sandstones = st.number_input("How many sandstones?", min_value=1, step=1)
        if st.button("Next"):
            st.session_state.plot_name = plot_name
            st.session_state.num_sandstones = num_sandstones
            st.session_state.sandstone_names = []
            st.session_state.step = 2

    # Step 3: Calibrate Axes
    elif st.session_state.step == 2:
        st.write("## Step 3: Calibrate Axes")
        st.session_state.pixel_to_data = calibrate_axes_streamlit(img_pil)
        if st.button("Next"):
            st.session_state.step = 3

    # Step 4: Enter sandstone name & extract points
    elif st.session_state.step == 3:
        idx = st.session_state.sandstone_index
        name = st.text_input(f"Enter name for sandstone {idx + 1}")
        if name:
            st.session_state.sandstone_names.append(name)
            points = extract_points_streamlit(img_pil, name, st.session_state.pixel_to_data)
            if points:
                st.session_state.data_points.extend(points)
            if st.button("Next Sandstone"):
                st.session_state.sandstone_index += 1
                if st.session_state.sandstone_index >= st.session_state.num_sandstones:
                    st.session_state.step = 4

    # Step 5: Save and show results
    elif st.session_state.step == 4:
        st.success("Extraction Complete!")
        df = pd.DataFrame(st.session_state.data_points)
        st.dataframe(df)
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button("Download CSV", csv, file_name=f"{st.session_state.plot_name}_data.csv")

