from sqlalchemy import create_engine, MetaData, inspect, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from typing import Dict, List, Optional, Any
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///data/sample.db")

# Create SQLAlchemy engine and session with connection pooling
engine = create_engine(
    DATABASE_URL,
    pool_size=5,
    max_overflow=10,
    pool_timeout=30,
    pool_recycle=1800,  # Recycle connections after 30 minutes
    connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    """Get database session with proper error handling."""
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        db.rollback()
        raise RuntimeError(f"Database error: {str(e)}")
    finally:
        db.close()

def get_schema_info() -> Dict[str, List[Dict[str, Any]]]:
    """
    Get database schema information including tables and columns.
    Returns a dictionary with table names as keys and list of column info as values.
    """
    inspector = inspect(engine)
    schema_info = {}
    
    for table_name in inspector.get_table_names():
        columns = []
        for column in inspector.get_columns(table_name):
            column_info = {
                "name": column["name"],
                "type": str(column["type"]),
                "nullable": column["nullable"],
                "default": str(column["default"]) if column["default"] is not None else None,
                "primary_key": column.get("primary_key", False)
            }
            columns.append(column_info)
        schema_info[table_name] = columns
    
    return schema_info

def execute_query(query: str, params: Optional[Dict] = None) -> List[Dict]:
    """
    Execute a SQL query and return results as a list of dictionaries.
    
    Args:
        query (str): SQL query to execute
        params (Optional[Dict]): Query parameters
        
    Returns:
        List[Dict]: Query results
        
    Raises:
        ValueError: If the query is invalid or contains dangerous operations
        RuntimeError: If there's a database error
    """
    # Basic SQL injection prevention
    dangerous_operations = [
        "DROP DATABASE", "DROP TABLE", "TRUNCATE", "DELETE FROM",
        "UPDATE", "INSERT INTO", "CREATE TABLE", "ALTER TABLE"
    ]
    
    query_upper = query.upper()
    if any(op in query_upper for op in dangerous_operations):
        raise ValueError("Query contains dangerous operations that are not allowed")
    
    try:
        with engine.connect() as connection:
            # Use parameterized queries for safety
            result = connection.execute(text(query), params or {})
            # Convert rows to dictionaries using _mapping attribute
            return [dict(row._mapping) for row in result]
    except Exception as e:
        raise RuntimeError(f"Error executing query: {str(e)}")

def create_sample_database():
    """Create a sample database with sales data if it doesn't exist."""
    try:
        # Create data directory if it doesn't exist
        os.makedirs("data", exist_ok=True)
        
        if not os.path.exists("data/sample.db"):
            # Create sample tables
            with engine.connect() as connection:
                # Create tables
                connection.execute(text("""
                    CREATE TABLE IF NOT EXISTS sales (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        product TEXT NOT NULL,
                        city TEXT NOT NULL,
                        amount DECIMAL(10,2) NOT NULL,
                        date DATE NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """))
                
                # Check if data already exists
                result = connection.execute(text("SELECT COUNT(*) FROM sales"))
                count = result.scalar()
                
                if count == 0:
                    # Insert sample data only if table is empty
                    connection.execute(text("""
                        INSERT INTO sales (product, city, amount, date) VALUES
                        ('Laptop', 'New York', 1200.00, '2023-01-15'),
                        ('Smartphone', 'Los Angeles', 800.00, '2023-01-16'),
                        ('Tablet', 'Chicago', 500.00, '2023-01-17'),
                        ('Laptop', 'Boston', 1100.00, '2023-01-18'),
                        ('Smartphone', 'Miami', 850.00, '2023-01-19'),
                        ('Laptop', 'Seattle', 1150.00, '2023-01-20'),
                        ('Tablet', 'Denver', 550.00, '2023-01-21'),
                        ('Smartphone', 'Austin', 900.00, '2023-01-22')
                    """))
                connection.commit()
                
    except Exception as e:
        raise RuntimeError(f"Failed to create sample database: {str(e)}")

# Initialize sample database
try:
    create_sample_database()
except Exception as e:
    print(f"Warning: Failed to initialize sample database: {str(e)}") 