import sqlite3
import os
from datetime import datetime
from typing import List, Dict, Optional, Tuple
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatabaseManager:
    def __init__(self, db_path=None):
        if db_path is None:
            # Get the directory where this script is located
            script_dir = os.path.dirname(os.path.abspath(__file__))
            # Go up one level to the project root
            project_root = os.path.dirname(script_dir)
            # Create data directory path
            db_path = os.path.join(project_root, 'data', 'plots.db')
        
        self.db_path = db_path
        # Ensure data directory exists
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
    
    def get_connection(self):
        """Get a new database connection for thread safety"""
        try:
            connection = sqlite3.connect(self.db_path, check_same_thread=False)
            connection.row_factory = sqlite3.Row  # Enable column access by name
            return connection
        except sqlite3.Error as e:
            logger.error(f"Error connecting to SQLite: {e}")
            return None
    
    def connect(self):
        """Test database connection"""
        connection = self.get_connection()
        if connection:
            connection.close()
            logger.info(f"Successfully connected to SQLite database: {self.db_path}")
            return True
        return False
    
    def disconnect(self):
        """No-op for compatibility"""
        pass
    
    def check_schema_version(self):
        """Check if database has new DOI-based schema"""
        connection = self.get_connection()
        if not connection:
            return False
            
        try:
            cursor = connection.cursor()
            # Check if DOI column exists in plots table
            cursor.execute("PRAGMA table_info(plots)")
            columns = [row[1] for row in cursor.fetchall()]
            has_doi = 'doi' in columns
            cursor.close()
            connection.close()
            return has_doi
        except sqlite3.Error:
            if connection:
                connection.close()
            return False
    
    def migrate_database(self):
        """Migrate old database to new DOI-based schema"""
        connection = self.get_connection()
        if not connection:
            return False
            
        try:
            cursor = connection.cursor()
            logger.info("Starting database migration to DOI-based schema...")
            
            # Backup old data
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = cursor.fetchall()
            
            if any('plots' in str(table) for table in tables):
                # Check if we have old data
                cursor.execute("SELECT COUNT(*) FROM plots")
                old_count = cursor.fetchone()[0]
                
                if old_count > 0:
                    logger.warning(f"Found {old_count} plots in old format. Creating backup...")
                    
                    # Create backup table
                    cursor.execute("""
                        CREATE TABLE IF NOT EXISTS plots_backup AS 
                        SELECT * FROM plots
                    """)
                    
                    # Drop old tables to recreate with new schema
                    cursor.execute("DROP TABLE IF EXISTS data_points")
                    cursor.execute("DROP TABLE IF EXISTS sandstones") 
                    cursor.execute("DROP TABLE IF EXISTS plots")
                    
                    logger.info("Old tables backed up and removed")
                else:
                    # No data, just drop tables
                    cursor.execute("DROP TABLE IF EXISTS data_points")
                    cursor.execute("DROP TABLE IF EXISTS sandstones")
                    cursor.execute("DROP TABLE IF EXISTS plots")
            
            connection.commit()
            cursor.close()
            connection.close()
            logger.info("Database migration completed")
            return True
            
        except sqlite3.Error as e:
            logger.error(f"Error during migration: {e}")
            if connection:
                connection.close()
            return False
    
    def create_tables(self):
        """Create all required tables"""
        connection = self.get_connection()
        if not connection:
            logger.error(f"Cannot create connection to database at: {self.db_path}")
            return False
        
        # Check if we need to migrate
        if not self.check_schema_version():
            logger.info("Old database schema detected, migrating...")
            if not self.migrate_database():
                logger.error("Database migration failed")
                connection.close()
                return False
            # Get new connection after migration
            connection.close()
            connection = self.get_connection()
            if not connection:
                return False
            
        try:
            # Test if we can write to the database location
            test_file = os.path.join(os.path.dirname(self.db_path), 'test_write.tmp')
            with open(test_file, 'w') as f:
                f.write('test')
            os.remove(test_file)
            logger.info(f"Write permissions confirmed for: {os.path.dirname(self.db_path)}")
        except Exception as e:
            logger.error(f"No write permissions for database directory: {e}")
            return False
            
        tables = {
            'plots': """
                CREATE TABLE IF NOT EXISTS plots (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    doi TEXT NOT NULL,
                    figure_number TEXT NOT NULL,
                    plot_identifier TEXT UNIQUE NOT NULL,
                    image_path TEXT NOT NULL,
                    x_axis_range TEXT,
                    y_axis_range TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(doi, figure_number)
                )
            """,
            'sandstones': """
                CREATE TABLE IF NOT EXISTS sandstones (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    plot_id INTEGER NOT NULL,
                    sandstone_name TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (plot_id) REFERENCES plots(id) ON DELETE CASCADE,
                    UNIQUE(plot_id, sandstone_name)
                )
            """,
            'data_points': """
                CREATE TABLE IF NOT EXISTS data_points (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
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
            logger.info(f"Database successfully initialized at: {self.db_path}")
            return True
        except sqlite3.Error as e:
            logger.error(f"Error creating tables: {e}")
            connection.close()
            return False
    
    def check_plot_exists(self, doi: str, figure_number: str) -> bool:
        """Check if a plot with the given DOI and figure number already exists"""
        connection = self.get_connection()
        if not connection:
            raise Exception("Cannot connect to database")
            
        try:
            cursor = connection.cursor()
            cursor.execute("SELECT COUNT(*) FROM plots WHERE doi = ? AND figure_number = ?", (doi, figure_number))
            count = cursor.fetchone()[0]
            cursor.close()
            connection.close()
            return count > 0
        except sqlite3.Error as e:
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
        """Save complete plot data in a single transaction"""
        connection = self.get_connection()
        if not connection:
            raise Exception("Cannot connect to database")
            
        cursor = None
        try:
            cursor = connection.cursor()
            
            # Begin transaction
            cursor.execute("BEGIN TRANSACTION")
            
            # Insert plot
            cursor.execute("""
                INSERT INTO plots (doi, figure_number, plot_identifier, image_path, x_axis_range, y_axis_range)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                plot_data['doi'],
                plot_data['figure_number'],
                plot_data['plot_identifier'],
                plot_data['image_path'],
                plot_data['x_axis_range'],
                plot_data['y_axis_range']
            ))
            plot_id = cursor.lastrowid
            
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
                    VALUES (?, ?)
                """, (plot_id, sandstone_name))
                sandstone_id = cursor.lastrowid
                
                # Insert data points for this sandstone
                point_values = [
                    (sandstone_id, point['x_pixel'], point['y_pixel'], 
                     point['P(MPa)'], point['Q(MPa)'])
                    for point in points
                ]
                cursor.executemany("""
                    INSERT INTO data_points (sandstone_id, x_pixel, y_pixel, p_mpa, q_mpa)
                    VALUES (?, ?, ?, ?, ?)
                """, point_values)
            
            # Commit transaction
            cursor.execute("COMMIT")
            cursor.close()
            connection.close()
            logger.info(f"Plot '{plot_data['plot_identifier']}' saved successfully with ID {plot_id}")
            return plot_id
            
        except sqlite3.Error as e:
            if cursor:
                cursor.execute("ROLLBACK")
                cursor.close()
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
                    'created_at': datetime.fromisoformat(row['created_at']) if row['created_at'] else None,
                    'sandstone_count': row['sandstone_count'],
                    'total_points': row['total_points']
                })
            
            cursor.close()
            connection.close()
            return plots
        except sqlite3.Error as e:
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
            cursor.execute("SELECT * FROM plots WHERE id = ?", (plot_id,))
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
                WHERE s.plot_id = ?
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
            
        except sqlite3.Error as e:
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
            
            # Get image path before deletion
            cursor.execute("SELECT image_path FROM plots WHERE id = ?", (plot_id,))
            result = cursor.fetchone()
            image_path = result['image_path'] if result else None
            
            # Delete plot (cascades to sandstones and data_points)
            cursor.execute("DELETE FROM plots WHERE id = ?", (plot_id,))
            affected_rows = cursor.rowcount
            
            connection.commit()
            cursor.close()
            connection.close()
            
            # Remove image file if it exists
            if image_path and os.path.exists(image_path):
                try:
                    os.remove(image_path)
                    logger.info(f"Deleted image file: {image_path}")
                except OSError as e:
                    logger.warning(f"Could not delete image file {image_path}: {e}")
            
            logger.info(f"Plot {plot_id} deleted successfully")
            return affected_rows > 0
            
        except sqlite3.Error as e:
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
            
            # Get database file size
            db_size = os.path.getsize(self.db_path) if os.path.exists(self.db_path) else 0
            
            cursor.close()
            connection.close()
            
            return {
                'plots': plot_count,
                'sandstones': sandstone_count,
                'data_points': point_count,
                'database_size_mb': round(db_size / (1024 * 1024), 2)
            }
            
        except sqlite3.Error as e:
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