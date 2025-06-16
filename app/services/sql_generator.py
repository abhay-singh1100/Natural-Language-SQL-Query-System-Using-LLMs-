from typing import Dict, Optional, Tuple
from app.models.mistral_model import get_model
from app.services.schema_reader import SchemaReader
from app.utils.db import execute_query
import sqlparse

class SQLGenerator:
    def __init__(self):
        self.model = get_model()
        self.schema_reader = SchemaReader()

    def _load_prompt_template(self) -> str:
        """Load the prompt template for SQL generation."""
        try:
            with open("prompts/generate_sql.txt", "r") as f:
                return f.read().strip()
        except FileNotFoundError:
            # Fallback to a default template if file not found
            return """Given the following schema:
{schema}

And the user query:
{question}

Generate an appropriate SQL query.
SQL:"""

    def _format_prompt(self, question: str) -> str:
        """
        Format the prompt with schema and question.
        
        Args:
            question (str): Natural language question
            
        Returns:
            str: Formatted prompt
        """
        template = self._load_prompt_template()
        schema = self.schema_reader.get_formatted_schema()
        return template.format(schema=schema, question=question)

    def generate_and_execute(self, question: str) -> Tuple[str, Dict]:
        """
        Generate SQL from natural language and execute it.
        
        Args:
            question (str): Natural language question
            
        Returns:
            Tuple[str, Dict]: Generated SQL query and query results
        """
        try:
            # Get schema information
            schema_info = self.schema_reader.get_formatted_schema()
            
            # Generate SQL
            generated_sql = self.model.generate_sql(question, schema_info)
            
            # Format and validate SQL
            formatted_sql = sqlparse.format(
                generated_sql,
                keyword_case='upper',
                identifier_case='lower',
                reindent=True,
                strip_comments=True
            )
            
            # Execute query
            results = execute_query(formatted_sql)
            
            return formatted_sql, results
            
        except Exception as e:
            raise Exception(f"Error in SQL generation/execution: {str(e)}")

    def validate_sql(self, sql: str) -> bool:
        """
        Validate SQL query syntax.
        
        Args:
            sql (str): SQL query to validate
            
        Returns:
            bool: True if valid, False otherwise
        """
        try:
            # Use sqlparse to validate basic syntax
            parsed = sqlparse.parse(sql)
            if not parsed:
                return False
                
            # Additional validation could be added here
            # For example, checking for dangerous operations
            
            return True
        except Exception:
            return False

# Create a singleton instance
generator_instance: Optional[SQLGenerator] = None

def get_generator() -> SQLGenerator:
    """Get or create the SQL generator instance."""
    global generator_instance
    if generator_instance is None:
        generator_instance = SQLGenerator()
    return generator_instance 