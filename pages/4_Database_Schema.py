import os
import sys
import streamlit as st
import streamlit.components.v1

from navigation import create_navigation

# Add the project root to the path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

st.set_page_config(page_title="Database Schema", page_icon="📊", layout="wide")

# Initialize navigation
create_navigation()

def display_mermaid_schema():
    """Display the database schema using mermaid diagram"""
    
    # Mermaid diagram content
    mermaid_content = """
erDiagram
    PLOTS {
        INTEGER id PK "AUTO_INCREMENT"
        TEXT doi "NOT NULL"
        TEXT figure_number "NOT NULL"
        TEXT plot_identifier "UNIQUE NOT NULL"
        TEXT image_path "NOT NULL"
        TEXT x_axis_range "Calibrated range"
        TEXT y_axis_range "Calibrated range"
        TIMESTAMP created_at "DEFAULT CURRENT_TIMESTAMP"
        TIMESTAMP updated_at "DEFAULT CURRENT_TIMESTAMP"
    }
    
    SANDSTONES {
        INTEGER id PK "AUTO_INCREMENT"
        INTEGER plot_id FK "NOT NULL"
        TEXT sandstone_name "NOT NULL"
        TIMESTAMP created_at "DEFAULT CURRENT_TIMESTAMP"
    }
    
    DATA_POINTS {
        INTEGER id PK "AUTO_INCREMENT"
        INTEGER sandstone_id FK "NOT NULL"
        REAL x_pixel "NOT NULL - Original click position"
        REAL y_pixel "NOT NULL - Original click position"
        REAL p_mpa "NOT NULL - Converted pressure value"
        REAL q_mpa "NOT NULL - Converted deviatoric stress"
        TIMESTAMP created_at "DEFAULT CURRENT_TIMESTAMP"
    }
    
    %% Relationships
    PLOTS ||--o{ SANDSTONES : "contains"
    SANDSTONES ||--o{ DATA_POINTS : "has"
    
    %% Additional Notes
    PLOTS {
        string UNIQUE_CONSTRAINT "UNIQUE(doi, figure_number)"
        string INDEX_doi "idx_plots_doi"
        string INDEX_identifier "idx_plots_identifier"
    }
    
    SANDSTONES {
        string UNIQUE_CONSTRAINT "UNIQUE(plot_id, sandstone_name)"
        string FOREIGN_KEY "FK(plot_id) REFERENCES plots(id) ON DELETE CASCADE"
        string INDEX_plot_id "idx_sandstones_plot_id"
    }
    
    DATA_POINTS {
        string FOREIGN_KEY "FK(sandstone_id) REFERENCES sandstones(id) ON DELETE CASCADE"
        string INDEX_sandstone_id "idx_data_points_sandstone_id"
    }
    """
    
    # Display using HTML with mermaid
    st.components.v1.html(f"""
    <!DOCTYPE html>
    <html>
    <head>
        <script src="https://cdnjs.cloudflare.com/ajax/libs/mermaid/10.6.1/mermaid.min.js"></script>
        <style>
            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', sans-serif;
                margin: 0;
                padding: 20px;
                background: #fafafa;
            }}
            .mermaid {{
                display: flex;
                justify-content: center;
                background: white;
                border-radius: 8px;
                padding: 20px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }}
        </style>
    </head>
    <body>
        <div class="mermaid">
            {mermaid_content}
        </div>
        
        <script>
            mermaid.initialize({{
                startOnLoad: true,
                theme: 'default',
                themeVariables: {{
                    primaryColor: '#f0f2f6',
                    primaryTextColor: '#262730',
                    primaryBorderColor: '#667eea',
                    lineColor: '#667eea',
                    secondaryColor: '#ffffff',
                    tertiaryColor: '#f8f9fa',
                    background: '#ffffff',
                    mainBkg: '#f8f9fa',
                    secondBkg: '#ffffff',
                    tertiaryBkg: '#f0f2f6'
                }},
                er: {{
                    entityPadding: 15,
                    stroke: '#667eea',
                    fill: '#f8f9fa',
                    fontSize: 12
                }}
            }});
        </script>
    </body>
    </html>
    """, height=1000)

# Page header
st.title("📊 Database Schema")
st.markdown("---")

# Display the mermaid diagram
display_mermaid_schema()