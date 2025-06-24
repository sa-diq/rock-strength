import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from core.database import db_manager
import numpy as np

def get_plot_data_for_recreation(plot_id: int):
    """
    Get all data needed to recreate a plot from the database
    
    Args:
        plot_id: ID of the plot to recreate
        
    Returns:
        dict: Contains plot metadata and formatted data for plotting
    """
    try:
        # Get complete plot data from database
        plot_data = db_manager.get_plot_data(plot_id)
        
        if not plot_data:
            print(f"No plot found with ID {plot_id}")
            return None
        
        # Extract plot metadata
        plot_info = {
            'doi': plot_data['doi'],
            'figure_number': plot_data['figure_number'],
            'plot_identifier': plot_data['plot_identifier'],
            'x_axis_range': plot_data['x_axis_range'],
            'y_axis_range': plot_data['y_axis_range'],
            'image_path': plot_data['image_path'],
            'created_at': plot_data['created_at']
        }
        
        # Convert data points to DataFrame for easy manipulation
        if plot_data['data_points']:
            df = pd.DataFrame(plot_data['data_points'])
            
            # Group data by sandstone for plotting
            sandstone_data = {}
            for sandstone in df['sandstone_name'].unique():
                sandstone_df = df[df['sandstone_name'] == sandstone]
                sandstone_data[sandstone] = {
                    'P_MPa': sandstone_df['p_mpa'].values,
                    'Q_MPa': sandstone_df['q_mpa'].values,
                    'x_pixel': sandstone_df['x_pixel'].values,
                    'y_pixel': sandstone_df['y_pixel'].values
                }
        else:
            sandstone_data = {}
        
        return {
            'plot_info': plot_info,
            'sandstone_data': sandstone_data,
            'raw_dataframe': df if plot_data['data_points'] else pd.DataFrame()
        }
        
    except Exception as e:
        print(f"Error retrieving plot data: {e}")
        return None

def recreate_qp_plot(plot_id: int, save_path: str = None, show_plot: bool = True):
    """
    Recreate a Q-P plot from database data
    
    Args:
        plot_id: ID of the plot to recreate
        save_path: Optional path to save the plot
        show_plot: Whether to display the plot
    """
    
    # Get data from database
    data = get_plot_data_for_recreation(plot_id)
    
    if not data:
        return None
    
    plot_info = data['plot_info']
    sandstone_data = data['sandstone_data']
    
    if not sandstone_data:
        print("No data points found for this plot")
        return None
    
    # Create the plot
    plt.figure(figsize=(10, 8))
    
    # Define colors for different sandstones
    colors = plt.cm.Set1(np.linspace(0, 1, len(sandstone_data)))
    
    # Plot each sandstone dataset
    for i, (sandstone_name, data_points) in enumerate(sandstone_data.items()):
        plt.scatter(
            data_points['P_MPa'], 
            data_points['Q_MPa'],
            label=sandstone_name,
            color=colors[i],
            alpha=0.7,
            s=50
        )
    
    # Customize the plot
    plt.xlabel('P (MPa)', fontsize=12)
    plt.ylabel('Q (MPa)', fontsize=12)
    plt.title(f'Recreated Q-P Plot: {plot_info["doi"]} Fig {plot_info["figure_number"]}', fontsize=14, fontweight='bold')
    plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.grid(True, alpha=0.3)
    
    # Add metadata as text
    plt.figtext(0.02, 0.02, 
                f"DOI: {plot_info['doi']} | Figure: {plot_info['figure_number']}\n"
                f"Ranges - X: {plot_info['x_axis_range']}, Y: {plot_info['y_axis_range']}\n"
                f"Digitized: {plot_info['created_at']}", 
                fontsize=8, style='italic')
    
    plt.tight_layout()
    
    # Save if requested
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"Plot saved to: {save_path}")
    
    # Show if requested
    if show_plot:
        plt.show()
    
    return plt.gcf()

def export_plot_data_to_csv(plot_id: int, output_path: str = None):
    """
    Export plot data to CSV format
    
    Args:
        plot_id: ID of the plot to export
        output_path: Optional custom output path
    """
    
    data = get_plot_data_for_recreation(plot_id)
    
    if not data or data['raw_dataframe'].empty:
        print("No data to export")
        return None
    
    df = data['raw_dataframe']
    plot_identifier = data['plot_info']['plot_identifier']
    
    # If no output path specified, create one
    if not output_path:
        output_path = f"{plot_identifier}_recreated_data.csv"
    
    # Export to CSV
    df.to_csv(output_path, index=False)
    print(f"Data exported to: {output_path}")
    
    return df

def compare_digitized_vs_original(plot_id: int):
    """
    Create a comparison showing digitized points on the original image
    
    Args:
        plot_id: ID of the plot to analyze
    """
    from PIL import Image
    
    data = get_plot_data_for_recreation(plot_id)
    
    if not data:
        return None
    
    plot_info = data['plot_info']
    sandstone_data = data['sandstone_data']
    
    # Load original image
    try:
        img = Image.open(plot_info['image_path'])
        
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))
        
        # Left plot: Original image with digitized points overlaid
        ax1.imshow(img)
        colors = plt.cm.Set1(np.linspace(0, 1, len(sandstone_data)))
        
        for i, (sandstone_name, data_points) in enumerate(sandstone_data.items()):
            ax1.scatter(
                data_points['x_pixel'], 
                data_points['y_pixel'],
                label=sandstone_name,
                color=colors[i],
                s=30,
                alpha=0.8
            )
        
        ax1.set_title(f'Original Image: {plot_info["doi"]} Fig {plot_info["figure_number"]}')
        ax1.legend()
        ax1.set_xlabel('Pixel X')
        ax1.set_ylabel('Pixel Y')
        
        # Right plot: Recreated Q-P plot
        for i, (sandstone_name, data_points) in enumerate(sandstone_data.items()):
            ax2.scatter(
                data_points['P_MPa'], 
                data_points['Q_MPa'],
                label=sandstone_name,
                color=colors[i],
                alpha=0.7,
                s=50
            )
        
        ax2.set_xlabel('P (MPa)')
        ax2.set_ylabel('Q (MPa)')
        ax2.set_title('Recreated Q-P Plot')
        ax2.legend()
        ax2.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.show()
        
        return fig
        
    except Exception as e:
        print(f"Error loading image: {e}")
        return None

def get_summary_statistics(plot_id: int):
    """
    Get summary statistics for a digitized plot
    
    Args:
        plot_id: ID of the plot to analyze
    """
    
    data = get_plot_data_for_recreation(plot_id)
    
    if not data or data['raw_dataframe'].empty:
        print("No data available")
        return None
    
    df = data['raw_dataframe']
    plot_info = data['plot_info']
    
    print(f"\n=== SUMMARY FOR PLOT: {plot_info['doi']} Fig {plot_info['figure_number']} ===")
    print(f"Plot Identifier: {plot_info['plot_identifier']}")
    print(f"Digitized on: {plot_info['created_at']}")
    print(f"X-axis range: {plot_info['x_axis_range']}")
    print(f"Y-axis range: {plot_info['y_axis_range']}")
    print(f"Total data points: {len(df)}")
    print(f"Number of sandstone datasets: {df['sandstone_name'].nunique()}")
    
    print("\n--- By Sandstone ---")
    for sandstone in df['sandstone_name'].unique():
        subset = df[df['sandstone_name'] == sandstone]
        print(f"\n{sandstone}:")
        print(f"  Points: {len(subset)}")
        print(f"  P range: {subset['p_mpa'].min():.2f} - {subset['p_mpa'].max():.2f} MPa")
        print(f"  Q range: {subset['q_mpa'].min():.2f} - {subset['q_mpa'].max():.2f} MPa")
        print(f"  P mean: {subset['p_mpa'].mean():.2f} ± {subset['p_mpa'].std():.2f} MPa")
        print(f"  Q mean: {subset['q_mpa'].mean():.2f} ± {subset['q_mpa'].std():.2f} MPa")
    
    return df.groupby('sandstone_name').agg({
        'p_mpa': ['count', 'mean', 'std', 'min', 'max'],
        'q_mpa': ['count', 'mean', 'std', 'min', 'max']
    })

# ============================================================================
# NEW VALIDATION FUNCTIONS (For workflow validation step)
# ============================================================================

def create_validation_overlay(image_pil, data_points, sandstone_names):
    """
    Create validation overlay showing extracted points on original image
    Specifically designed for Streamlit workflow validation step
    
    Args:
        image_pil: PIL Image object of the original plot
        data_points: List of extracted data point dictionaries
        sandstone_names: List of sandstone dataset names
        
    Returns:
        matplotlib.figure.Figure: Figure object for Streamlit display
    """
    
    # Create figure with good size for Streamlit
    fig, ax = plt.subplots(1, 1, figsize=(12, 8))
    
    # Display original image
    ax.imshow(image_pil)
    
    # Define colors for different sandstones
    colors = plt.cm.Set1(np.linspace(0, 1, len(sandstone_names)))
    color_map = {name: colors[i] for i, name in enumerate(sandstone_names)}
    
    # Track which sandstones we've seen for legend
    seen_sandstones = set()
    
    # Plot extracted points by sandstone
    for point in data_points:
        sandstone = point['dataset']
        color = color_map.get(sandstone, 'red')
        
        # Only add label for first occurrence of each sandstone
        label = sandstone if sandstone not in seen_sandstones else None
        if label:
            seen_sandstones.add(sandstone)
        
        # Plot point with subtle cross-hair style
        ax.scatter(
            point['x_pixel'], 
            point['y_pixel'],
            color=color,
            s=60,  # Reduced size
            alpha=0.7,  # More transparent
            marker='+',  # Cross marker
            linewidths=1.5,  # Thinner lines
            label=label
        )
    
    # Add legend if we have multiple sandstones
    if len(seen_sandstones) > 1:
        ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
    
    # Styling
    ax.set_title('Validation: Extracted Points Overlay', fontsize=14, fontweight='bold')
    ax.set_xlabel('Pixel X')
    ax.set_ylabel('Pixel Y')
    
    # Add grid for reference
    ax.grid(True, alpha=0.3)
    
    # Tight layout to prevent legend cutoff
    plt.tight_layout()
    
    return fig

def calculate_validation_metrics(data_points, sandstone_names):
    """
    Calculate validation metrics for the extracted points
    
    Args:
        data_points: List of extracted data point dictionaries
        sandstone_names: List of sandstone dataset names
        
    Returns:
        dict: Validation metrics and statistics
    """
    
    if not data_points:
        return {}
    
    # Convert to easier format for analysis
    df = pd.DataFrame(data_points)
    
    metrics = {}
    
    # Overall statistics
    metrics['total_points'] = len(data_points)
    metrics['total_sandstones'] = len(sandstone_names)
    metrics['points_per_sandstone'] = len(data_points) / len(sandstone_names) if len(sandstone_names) > 0 else 0
    
    # P and Q value ranges
    metrics['p_range'] = {
        'min': df['P(MPa)'].min(),
        'max': df['P(MPa)'].max(),
        'span': df['P(MPa)'].max() - df['P(MPa)'].min()
    }
    
    metrics['q_range'] = {
        'min': df['Q(MPa)'].min(),
        'max': df['Q(MPa)'].max(), 
        'span': df['Q(MPa)'].max() - df['Q(MPa)'].min()
    }
    
    # Physical reasonableness checks
    metrics['negative_p_count'] = (df['P(MPa)'] < 0).sum()
    metrics['negative_q_count'] = (df['Q(MPa)'] < 0).sum()
    
    # Avoid division by zero for Q/P ratio
    valid_ratios = df['P(MPa)'] > 0.1  # Avoid very small P values
    if valid_ratios.any():
        q_p_ratios = df.loc[valid_ratios, 'Q(MPa)'] / df.loc[valid_ratios, 'P(MPa)']
        metrics['extreme_q_p_ratio'] = (q_p_ratios > 10).sum()
    else:
        metrics['extreme_q_p_ratio'] = 0
    
    # Per-sandstone breakdown
    metrics['by_sandstone'] = {}
    for sandstone in sandstone_names:
        subset = df[df['dataset'] == sandstone]
        if len(subset) > 0:
            subset_valid_ratios = subset['P(MPa)'] > 0.1
            avg_ratio = (subset.loc[subset_valid_ratios, 'Q(MPa)'] / subset.loc[subset_valid_ratios, 'P(MPa)']).mean() if subset_valid_ratios.any() else 0
            
            metrics['by_sandstone'][sandstone] = {
                'point_count': len(subset),
                'p_range': f"{subset['P(MPa)'].min():.1f} - {subset['P(MPa)'].max():.1f}",
                'q_range': f"{subset['Q(MPa)'].min():.1f} - {subset['Q(MPa)'].max():.1f}",
                'avg_q_p_ratio': avg_ratio
            }
    
    return metrics

def display_validation_summary(metrics):
    """
    Display validation metrics in Streamlit format
    
    Args:
        metrics: Dictionary from calculate_validation_metrics()
    """
    import streamlit as st
    
    if not metrics:
        st.warning("⚠️ No validation metrics available")
        return
    
    # Overall summary
    st.markdown("#### 📊 Extraction Summary")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total Points", metrics['total_points'])
    with col2:
        st.metric("Sandstone Datasets", metrics['total_sandstones'])
    with col3:
        st.metric("Avg Points/Dataset", f"{metrics['points_per_sandstone']:.1f}")
    
    # Data ranges
    st.markdown("#### 📏 Data Ranges")
    col1, col2 = st.columns(2)
    
    with col1:
        st.write(f"**P (MPa):** {metrics['p_range']['min']:.1f} → {metrics['p_range']['max']:.1f}")
        st.write(f"**Range span:** {metrics['p_range']['span']:.1f} MPa")
    
    with col2:
        st.write(f"**Q (MPa):** {metrics['q_range']['min']:.1f} → {metrics['q_range']['max']:.1f}")
        st.write(f"**Range span:** {metrics['q_range']['span']:.1f} MPa")
    
    # Quality checks
    st.markdown("#### 🔍 Quality Checks")
    
    warnings = []
    if metrics['negative_p_count'] > 0:
        warnings.append(f"⚠️ {metrics['negative_p_count']} points have negative P values")
    if metrics['negative_q_count'] > 0:
        warnings.append(f"⚠️ {metrics['negative_q_count']} points have negative Q values")
    if metrics['extreme_q_p_ratio'] > 0:
        warnings.append(f"⚠️ {metrics['extreme_q_p_ratio']} points have Q/P ratio > 10 (unusually high)")
    
    if warnings:
        for warning in warnings:
            st.warning(warning)
    else:
        st.success("✅ All quality checks passed")
    
    # Per-sandstone details
    if metrics['by_sandstone']:
        st.markdown("#### 🪨 By Sandstone Dataset")
        for sandstone, data in metrics['by_sandstone'].items():
            with st.expander(f"{sandstone} ({data['point_count']} points)"):
                st.write(f"**P range:** {data['p_range']} MPa")
                st.write(f"**Q range:** {data['q_range']} MPa")
                st.write(f"**Avg Q/P ratio:** {data['avg_q_p_ratio']:.2f}")

if __name__ == "__main__":
    pass