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

# Example usage functions
def example_usage():
    """
    Example of how to use these functions
    """
    
    # Assuming plot ID 1 exists in your database
    plot_id = 1
    
    print("1. Getting plot data...")
    data = get_plot_data_for_recreation(plot_id)
    if data:
        print(f"Found plot: {data['plot_info']['doi']} Fig {data['plot_info']['figure_number']}")
    
    print("\n2. Recreating the plot...")
    recreate_qp_plot(plot_id, save_path="recreated_plot.png")
    
    print("\n3. Exporting data to CSV...")
    export_plot_data_to_csv(plot_id)
    
    print("\n4. Getting summary statistics...")
    get_summary_statistics(plot_id)
    
    print("\n5. Comparing with original...")
    compare_digitized_vs_original(plot_id)

if __name__ == "__main__":
    # You would need to initialize the database first
    # from core.database import init_database
    # init_database()
    
    # Then run the example
    # example_usage()
    pass