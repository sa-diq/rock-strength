import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import base64
from io import BytesIO
import json

def extract_points_streamlit(image_pil, sandstone_name, pixel_to_data):
    st.write(f"### Extracting points for: {sandstone_name}")
    
    # Convert image to base64
    buffered = BytesIO()
    image_pil.save(buffered, format="PNG")
    img_base64 = base64.b64encode(buffered.getvalue()).decode()
    
    # Session state key for storing points
    points_key = f"points_{sandstone_name}_{st.session_state.sandstone_index}"
    
    # Initialize points in session state if not exists
    if points_key not in st.session_state:
        st.session_state[points_key] = []
    
    # Custom HTML with zoom, pan, and click functionality
    html_code = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            #image-container {{
                width: 100%;
                height: 600px;
                border: 2px solid #ddd;
                border-radius: 8px;
                overflow: hidden;
                position: relative;
                cursor: grab;
                background: #f8f9fa;
            }}
            #image-container:active {{
                cursor: grabbing;
            }}
            #zoomable-image {{
                position: absolute;
                transform-origin: 0 0;
                transition: transform 0.1s ease;
            }}
            .controls {{
                margin: 10px 0;
                text-align: center;
            }}
            .btn {{
                background: #0066cc;
                color: white;
                border: none;
                padding: 8px 16px;
                margin: 0 5px;
                border-radius: 4px;
                cursor: pointer;
                font-size: 14px;
            }}
            .btn:hover {{
                background: #0052a3;
            }}
            .btn:disabled {{
                background: #ccc;
                cursor: not-allowed;
            }}
            .point {{
                position: absolute;
                width: 8px;
                height: 8px;
                background: red;
                border: 2px solid white;
                border-radius: 50%;
                transform: translate(-50%, -50%);
                z-index: 100;
                box-shadow: 0 0 4px rgba(0,0,0,0.5);
            }}
            .zoom-info {{
                position: absolute;
                top: 10px;
                right: 10px;
                background: rgba(0,0,0,0.7);
                color: white;
                padding: 5px 10px;
                border-radius: 4px;
                font-size: 12px;
            }}
            .instructions {{
                text-align: center;
                margin: 10px 0;
                color: #666;
            }}
        </style>
    </head>
    <body>
        <div class="instructions">
            <strong>Click on data points | Drag to pan | Use buttons to zoom</strong>
        </div>
        
        <div class="controls">
            <button class="btn" onclick="zoomIn()">🔍+ Zoom In</button>
            <button class="btn" onclick="zoomOut()">🔍- Zoom Out</button>
            <button class="btn" onclick="resetView()">🎯 Reset View</button>
            <button class="btn" onclick="clearPoints()">🗑️ Clear Points</button>
        </div>
        
        <div id="image-container">
            <img id="zoomable-image" src="data:image/png;base64,{img_base64}" 
                 style="max-width: none; max-height: none;">
            <div class="zoom-info" id="zoom-info">Zoom: 1.0x</div>
        </div>
        
        <div style="margin-top: 10px; text-align: center;">
            <span id="point-count">Points: 0</span>
        </div>

        <script>
            let scale = 1;
            let translateX = 0;
            let translateY = 0;
            let isDragging = false;
            let dragStarted = false;
            let lastX = 0;
            let lastY = 0;
            let points = [];
            
            const container = document.getElementById('image-container');
            const image = document.getElementById('zoomable-image');
            const zoomInfo = document.getElementById('zoom-info');
            const pointCount = document.getElementById('point-count');
            
            // Load existing points from Streamlit
            const existingPoints = {json.dumps(st.session_state.get(points_key, []))};
            points = existingPoints;
            updateDisplay();
            
            function updateTransform() {{
                image.style.transform = `translate(${{translateX}}px, ${{translateY}}px) scale(${{scale}})`;
                zoomInfo.textContent = `Zoom: ${{scale.toFixed(1)}}x`;
            }}
            
            function updateDisplay() {{
                // Clear existing point markers
                document.querySelectorAll('.point').forEach(p => p.remove());
                
                // Add point markers
                points.forEach((point, index) => {{
                    const marker = document.createElement('div');
                    marker.className = 'point';
                    marker.style.left = (translateX + point.x * scale) + 'px';
                    marker.style.top = (translateY + point.y * scale) + 'px';
                    marker.title = `Point ${{index + 1}}: (${{point.x.toFixed(1)}}, ${{point.y.toFixed(1)}})`;
                    container.appendChild(marker);
                }});
                
                pointCount.textContent = `Points: ${{points.length}}`;
                
                // Send points back to Streamlit
                window.parent.postMessage({{
                    type: 'streamlit:setComponentValue',
                    value: points
                }}, '*');
            }}
            
            function zoomIn() {{
                scale = Math.min(scale * 1.5, 5);
                updateTransform();
                updateDisplay();
            }}
            
            function zoomOut() {{
                scale = Math.max(scale / 1.5, 0.5);
                updateTransform();
                updateDisplay();
            }}
            
            function resetView() {{
                scale = 1;
                translateX = 0;
                translateY = 0;
                updateTransform();
                updateDisplay();
            }}
            
            function clearPoints() {{
                points = [];
                updateDisplay();
            }}
            
            // Mouse events for panning and clicking
            container.addEventListener('mousedown', (e) => {{
                if (e.target === image || e.target === container) {{
                    isDragging = true;
                    dragStarted = false;
                    lastX = e.clientX;
                    lastY = e.clientY;
                    e.preventDefault();
                }}
            }});
            
            document.addEventListener('mousemove', (e) => {{
                if (isDragging) {{
                    const deltaX = e.clientX - lastX;
                    const deltaY = e.clientY - lastY;
                    
                    // If mouse moved more than 3 pixels, consider it a drag
                    if (Math.abs(deltaX) > 3 || Math.abs(deltaY) > 3) {{
                        dragStarted = true;
                        translateX += deltaX;
                        translateY += deltaY;
                        updateTransform();
                        updateDisplay();
                    }}
                    
                    lastX = e.clientX;
                    lastY = e.clientY;
                }}
            }});
            
            document.addEventListener('mouseup', (e) => {{
                if (isDragging && !dragStarted) {{
                    // This was a click, not a drag
                    const rect = container.getBoundingClientRect();
                    const x = (e.clientX - rect.left - translateX) / scale;
                    const y = (e.clientY - rect.top - translateY) / scale;
                    
                    points.push({{x: x, y: y}});
                    updateDisplay();
                }}
                
                isDragging = false;
                dragStarted = false;
            }});
            
            // Prevent context menu
            container.addEventListener('contextmenu', (e) => e.preventDefault());
            
            // Initial setup
            updateTransform();
            updateDisplay();
        </script>
    </body>
    </html>
    """
    
    # Render the component and get the returned value
    component_value = components.html(html_code, height=700)
    
    # Get points from session state (the component updates it via postMessage)
    points = st.session_state.get(points_key, [])
    
    if not points:
        st.info(f"Click on the plot above to select data points for {sandstone_name}.")
        return []

    st.write(f"**{len(points)} points selected**")
    
    # Convert pixel coordinates to data coordinates
    data_points = []
    for i, point in enumerate(points):
        x_pixel = point['x']
        y_pixel = point['y']
        x_data, y_data = pixel_to_data(x_pixel, y_pixel)
        data_points.append({
            "dataset": sandstone_name,
            "point_id": i + 1,
            "x_pixel": round(x_pixel, 4),
            "y_pixel": round(y_pixel, 4),
            "P (MPa)": round(x_data, 4),
            "Q (MPa)": round(y_data, 4)
        })
    
    # Show preview of extracted data
    if data_points:
        st.write("**Preview of extracted data:**")
        preview_df = pd.DataFrame(data_points)
        st.dataframe(preview_df, use_container_width=True)
    
    return data_points