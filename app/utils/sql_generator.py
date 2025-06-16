from typing import Optional
import logging
from .schema_reader import get_schema_info
from .mistral_model import get_model

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SQLGenerator:
    def __init__(self):
        """Initialize the SQL generator with the Mistral model."""
        self.model = get_model()
        
    def generate_sql(self, prompt: str) -> str:
        """Generate SQL query from natural language prompt."""
        try:
            # Get schema information
            schema_info = get_schema_info()
            logger.info("Schema information retrieved successfully")
            
            # Generate SQL using the model
            sql_query = self.model.generate_sql(prompt, schema_info)
            logger.info(f"Generated SQL query: {sql_query}")
            
            return sql_query
            
        except Exception as e:
            logger.error(f"Error generating SQL: {str(e)}")
            raise

# Create a singleton instance
_sql_generator: Optional[SQLGenerator] = None

def get_sql_generator() -> SQLGenerator:
    """Get or create the SQL generator instance."""
    global _sql_generator
    if _sql_generator is None:
        _sql_generator = SQLGenerator()
    return _sql_generator

def generate_sql(prompt: str) -> str:
    """Generate SQL query from natural language prompt."""
    return get_sql_generator().generate_sql(prompt) 