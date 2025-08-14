import psycopg2
import psycopg2.extras
import os
from datetime import datetime
from typing import List, Dict, Optional, Tuple
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatabaseManager:
    def __init__(self):
        self.database_url = os.getenv('DATABASE_URL')
        if not self.database_url:
            raise Exception("DATABASE_URL not found in environment variables")
    
    def get_connection(self):
        """Get a new database connection for thread safety"""
        try:
            connection = psycopg2.connect(
                self.database_url,
                cursor_factory=psycopg2.extras.RealDictCursor
            )
            return connection
        except psycopg2.Error as e:
            logger.error(f"Error connecting to PostgreSQL: {e}")
            return None
    
    def connect(self):
        """Test database connection"""
        connection = self.get_connection()
        if connection:
            connection.close()
            logger.info("Successfully connected to PostgreSQL database")
            return True
        return False
    
    def disconnect(self):
        """No-op for compatibility"""
        pass
    
    def create_tables(self):
        """Create all required tables """
        connection = self.get_connection()
        if not connection:
            logger.error("Cannot create connection to database")
            return False
        
        tables = {
            'plots': """
                CREATE TABLE IF NOT EXISTS plots (
                    id SERIAL PRIMARY KEY,
                    doi TEXT NOT NULL,
                    figure_number TEXT NOT NULL,
                    plot_identifier TEXT UNIQUE NOT NULL,
                    x_axis_range TEXT,
                    y_axis_range TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(doi, figure_number)
                )
            """,
            'sandstones': """
                CREATE TABLE IF NOT EXISTS sandstones (
                    id SERIAL PRIMARY KEY,
                    plot_id INTEGER NOT NULL,
                    sandstone_name TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (plot_id) REFERENCES plots(id) ON DELETE CASCADE,
                    UNIQUE(plot_id, sandstone_name)
                )
            """,
            'data_points': """
                CREATE TABLE IF NOT EXISTS data_points (
                    id SERIAL PRIMARY KEY,
                    sandstone_id INTEGER NOT NULL,
                    x_pixel REAL NOT NULL,
                    y_pixel REAL NOT NULL,
                    p_mpa REAL NOT NULL,
                    q_mpa REAL NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (sandstone_id) REFERENCES sandstones(id) ON DELETE CASCADE
                )
            """
        }
        
        try:
            cursor = connection.cursor()
            for table_name, query in tables.items():
                cursor.execute(query)
                logger.info(f"Table {table_name} created or verified")
            
            # Create indexes for better performance
            indexes = [
                "CREATE INDEX IF NOT EXISTS idx_sandstones_plot_id ON sandstones(plot_id)",
                "CREATE INDEX IF NOT EXISTS idx_data_points_sandstone_id ON data_points(sandstone_id)",
                "CREATE INDEX IF NOT EXISTS idx_plots_doi ON plots(doi)",
                "CREATE INDEX IF NOT EXISTS idx_plots_identifier ON plots(plot_identifier)"
            ]
            
            for index_query in indexes:
                cursor.execute(index_query)
            
            connection.commit()
            cursor.close()
            connection.close()
            logger.info("PostgreSQL database successfully initialized")
            return True
        except psycopg2.Error as e:
            logger.error(f"Error creating tables: {e}")
            if connection:
                connection.close()
            return False
    
    def check_plot_exists(self, doi: str, figure_number: str) -> bool:
        """Check if a plot with the given DOI and figure number already exists"""
        connection = self.get_connection()
        if not connection:
            raise Exception("Cannot connect to database")
            
        try:
            cursor = connection.cursor()
            cursor.execute("SELECT COUNT(*) FROM plots WHERE doi = %s AND figure_number = %s", (doi, figure_number))
            count = cursor.fetchone()[0]
            cursor.close()
            connection.close()
            return count > 0
        except psycopg2.Error as e:
            if connection:
                connection.close()
            logger.error(f"Error checking plot existence: {e}")
            raise Exception(f"Database error: {e}")
    
    def generate_plot_identifier(self, doi: str, figure_number: str) -> str:
        """Generate a standardized plot identifier from DOI and figure number"""
        # Clean DOI by removing protocol and common prefixes
        clean_doi = doi.replace('https://doi.org/', '').replace('http://doi.org/', '').replace('doi:', '')
        # Replace special characters with underscores
        clean_doi = clean_doi.replace('/', '_').replace('.', '_')
        # Clean figure number
        clean_fig = figure_number.replace(' ', '_').replace('.', '_')
        return f"{clean_doi}_Fig{clean_fig}"
    
    def save_complete_plot(self, plot_data: Dict) -> int:
        """Save complete plot data in a single transaction - NO IMAGE STORAGE"""
        connection = self.get_connection()
        if not connection:
            raise Exception("Cannot connect to database")
            
        cursor = None
        try:
            cursor = connection.cursor()
            
            # Begin transaction
            cursor.execute("BEGIN")
            
            # Insert plot (without image_path)
            cursor.execute("""
                INSERT INTO plots (doi, figure_number, plot_identifier, x_axis_range, y_axis_range)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING id
            """, (
                plot_data['doi'],
                plot_data['figure_number'],
                plot_data['plot_identifier'],
                plot_data['x_axis_range'],
                plot_data['y_axis_range']
            ))
            plot_id = cursor.fetchone()[0]
            
            # Group data points by sandstone
            sandstone_data = {}
            for point in plot_data['data_points']:
                sandstone_name = point['dataset']
                if sandstone_name not in sandstone_data:
                    sandstone_data[sandstone_name] = []
                sandstone_data[sandstone_name].append(point)
            
            # Insert sandstones and their data points
            for sandstone_name, points in sandstone_data.items():
                # Insert sandstone
                cursor.execute("""
                    INSERT INTO sandstones (plot_id, sandstone_name)
                    VALUES (%s, %s)
                    RETURNING id
                """, (plot_id, sandstone_name))
                sandstone_id = cursor.fetchone()[0]
                
                # Insert data points for this sandstone
                point_values = [
                    (sandstone_id, point['x_pixel'], point['y_pixel'], 
                     point['P(MPa)'], point['Q(MPa)'])
                    for point in points
                ]
                cursor.executemany("""
                    INSERT INTO data_points (sandstone_id, x_pixel, y_pixel, p_mpa, q_mpa)
                    VALUES (%s, %s, %s, %s, %s)
                """, point_values)
            
            # Commit transaction
            cursor.execute("COMMIT")
            cursor.close()
            connection.close()
            logger.info(f"Plot '{plot_data['plot_identifier']}' saved successfully with ID {plot_id}")
            return plot_id
            
        except psycopg2.Error as e:
            if cursor:
                cursor.execute("ROLLBACK")
                cursor.close()
            if connection:
                connection.close()
            logger.error(f"Error saving plot data: {e}")
            raise Exception(f"Database error: {e}")
    
    def get_all_plots(self) -> List[Dict]:
        """Retrieve all plots with basic information"""
        connection = self.get_connection()
        if not connection:
            raise Exception("Cannot connect to database")
            
        try:
            cursor = connection.cursor()
            cursor.execute("""
                SELECT p.id, p.doi, p.figure_number, p.plot_identifier, p.x_axis_range, p.y_axis_range, 
                       p.created_at, COUNT(DISTINCT s.id) as sandstone_count,
                       COUNT(dp.id) as total_points
                FROM plots p
                LEFT JOIN sandstones s ON p.id = s.plot_id
                LEFT JOIN data_points dp ON s.id = dp.sandstone_id
                GROUP BY p.id, p.doi, p.figure_number, p.plot_identifier, p.x_axis_range, p.y_axis_range, p.created_at
                ORDER BY p.created_at DESC
            """)
            
            plots = []
            for row in cursor.fetchall():
                plots.append({
                    'id': row['id'],
                    'doi': row['doi'],
                    'figure_number': row['figure_number'],
                    'plot_identifier': row['plot_identifier'],
                    'x_axis_range': row['x_axis_range'],
                    'y_axis_range': row['y_axis_range'],
                    'created_at': datetime.fromisoformat(row['created_at'].isoformat()) if row['created_at'] else None,
                    'sandstone_count': row['sandstone_count'],
                    'total_points': row['total_points']
                })
            
            cursor.close()
            connection.close()
            return plots
        except psycopg2.Error as e:
            if connection:
                connection.close()
            logger.error(f"Error retrieving plots: {e}")
            raise Exception(f"Database error: {e}")
    
    def get_plot_data(self, plot_id: int) -> Optional[Dict]:
        """Retrieve complete data for a specific plot"""
        connection = self.get_connection()
        if not connection:
            raise Exception("Cannot connect to database")
            
        try:
            cursor = connection.cursor()
            
            # Get plot info
            cursor.execute("SELECT * FROM plots WHERE id = %s", (plot_id,))
            plot_row = cursor.fetchone()
            
            if not plot_row:
                cursor.close()
                connection.close()
                return None
            
            # Convert row to dict
            plot = dict(plot_row)
            
            # Get sandstones and data points
            cursor.execute("""
                SELECT s.sandstone_name, dp.x_pixel, dp.y_pixel, dp.p_mpa, dp.q_mpa
                FROM sandstones s
                JOIN data_points dp ON s.id = dp.sandstone_id
                WHERE s.plot_id = %s
                ORDER BY s.sandstone_name, dp.id
            """, (plot_id,))
            
            data_points = []
            for row in cursor.fetchall():
                data_points.append(dict(row))
            
            cursor.close()
            connection.close()
            
            # Format the response
            plot['data_points'] = data_points
            return plot
            
        except psycopg2.Error as e:
            if connection:
                connection.close()
            logger.error(f"Error retrieving plot data: {e}")
            raise Exception(f"Database error: {e}")
    
    def delete_plot(self, plot_id: int) -> bool:
        """Delete a plot and all associated data"""
        connection = self.get_connection()
        if not connection:
            raise Exception("Cannot connect to database")
            
        try:
            cursor = connection.cursor()
            
            # Delete plot (cascades to sandstones and data_points)
            cursor.execute("DELETE FROM plots WHERE id = %s", (plot_id,))
            affected_rows = cursor.rowcount
            
            connection.commit()
            cursor.close()
            connection.close()
            
            logger.info(f"Plot {plot_id} deleted successfully")
            return affected_rows > 0
            
        except psycopg2.Error as e:
            if connection:
                connection.close()
            logger.error(f"Error deleting plot: {e}")
            raise Exception(f"Database error: {e}")
    
    def get_database_stats(self) -> Dict:
        """Get basic database statistics"""
        connection = self.get_connection()
        if not connection:
            return {}
            
        try:
            cursor = connection.cursor()
            
            # Get table counts
            cursor.execute("SELECT COUNT(*) FROM plots")
            plot_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM sandstones")
            sandstone_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM data_points")
            point_count = cursor.fetchone()[0]
            
            # Get database size
            cursor.execute("SELECT pg_size_pretty(pg_database_size(current_database()))")
            db_size = cursor.fetchone()[0]
            
            cursor.close()
            connection.close()
            
            return {
                'plots': plot_count,
                'sandstones': sandstone_count,
                'data_points': point_count,
                'database_size': db_size
            }
            
        except psycopg2.Error as e:
            if connection:
                connection.close()
            logger.error(f"Error getting database stats: {e}")
            return {}

# Global database manager instance
db_manager = DatabaseManager()

def init_database():
    """Initialise database connection and create tables"""
    if db_manager.connect():
        return db_manager.create_tables()
    return False