import sqlite3
import os
from typing import Dict, List
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SchemaReader:
    def __init__(self, db_path: str = None):
        """Initialize the schema reader with database path."""
        self.db_path = db_path or os.getenv('DATABASE_URL', 'sqlite:///nlp_sales.db').replace('sqlite:///', '')
        
    def get_schema_info(self) -> str:
        """Get formatted schema information from the database."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get all tables
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' 
                AND name NOT LIKE 'sqlite_%'
            """)
            tables = cursor.fetchall()
            
            if not tables:
                logger.error("No tables found in database")
                raise ValueError("No tables found in database")
            
            logger.info(f"Found tables: {[table[0] for table in tables]}")
            
            schema_info = []
            for (table_name,) in tables:
                # Get table schema
                cursor.execute(f"PRAGMA table_info({table_name})")
                columns = cursor.fetchall()
                
                # Format table information
                table_info = [f"table {table_name}"]  # Changed to lowercase 'table' for better parsing
                for col in columns:
                    col_id, name, type_, notnull, default_val, pk = col
                    constraints = []
                    if pk:
                        constraints.append("PRIMARY KEY")
                    if notnull:
                        constraints.append("NOT NULL")
                    if default_val is not None:
                        constraints.append(f"DEFAULT {default_val}")
                    
                    col_def = f"  {name} {type_}"  # Simplified column definition
                    if constraints:
                        col_def += " " + " ".join(constraints)
                    table_info.append(col_def)
                
                # Get foreign key information
                cursor.execute(f"PRAGMA foreign_key_list({table_name})")
                foreign_keys = cursor.fetchall()
                if foreign_keys:
                    table_info.append("  foreign keys:")  # Changed to lowercase
                    for fk in foreign_keys:
                        id_, seq, ref_table, from_col, to_col, on_update, on_delete, match = fk
                        table_info.append(f"    {from_col} references {ref_table}({to_col})")
                
                schema_info.append("\n".join(table_info))
            
            # Add example queries with more explicit formatting
            schema_info.append("\nExample valid queries:")
            schema_info.append("1. SELECT p.product_name, SUM(s.total_amount) as total_sales FROM sales s JOIN products p ON s.product_id = p.product_id GROUP BY p.product_name;")
            schema_info.append("2. SELECT c.customer_name, COUNT(s.sale_id) as purchase_count FROM customers c JOIN sales s ON c.customer_id = s.customer_id GROUP BY c.customer_name;")
            schema_info.append("3. SELECT p.category, SUM(s.total_amount) as category_sales FROM products p JOIN sales s ON p.product_id = s.product_id GROUP BY p.category;")
            
            final_schema = "\n\n".join(schema_info)
            logger.info("Generated schema information:")
            logger.info(final_schema)
            return final_schema
            
        except sqlite3.Error as e:
            logger.error(f"Database error while reading schema: {e}")
            raise
        except Exception as e:
            logger.error(f"Error reading schema: {e}")
            raise
        finally:
            if 'conn' in locals():
                conn.close()

# Create a singleton instance
_schema_reader: SchemaReader = None

def get_schema_reader() -> SchemaReader:
    """Get or create the schema reader instance."""
    global _schema_reader
    if _schema_reader is None:
        _schema_reader = SchemaReader()
    return _schema_reader

def get_schema_info() -> str:
    """Get formatted schema information."""
    return get_schema_reader().get_schema_info() 