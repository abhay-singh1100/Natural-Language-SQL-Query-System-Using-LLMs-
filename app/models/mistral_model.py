from ctransformers import AutoModelForCausalLM
import os
from dotenv import load_dotenv
from typing import Optional
import re
import logging

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

class MistralModel:
    def __init__(self):
        # Using TheBloke's GGUF Mistral model
        self.model_name = os.getenv("MODEL_NAME", "TheBloke/Mistral-7B-Instruct-v0.1-GGUF")
        self.model_file = os.getenv("MODEL_FILE", "mistral-7b-instruct-v0.1.Q4_K_M.gguf")
        self.device = "cuda" if os.getenv("USE_CUDA", "false").lower() == "true" else "cpu"
        self.model = None
        
        # Validate model configuration
        if not self.model_name or not self.model_file:
            raise ValueError("MODEL_NAME and MODEL_FILE must be set in .env file")
            
        # Check if model file exists
        model_path = os.path.join(os.path.expanduser("~"), ".cache", "huggingface", "hub", self.model_file)
        if not os.path.exists(model_path):
            raise FileNotFoundError(
                f"Model file not found at {model_path}. "
                "Please ensure you have downloaded the model file and it's in the correct location."
            )
        
        self._load_model()

    def _load_model(self):
        """Load the GGUF Mistral model with appropriate settings."""
        try:
            # Configure model parameters for optimal performance
            model_kwargs = {
                "model_type": "mistral",
                "gpu_layers": 0 if self.device == "cpu" else -1,
                "context_length": 2048,
                "threads": os.cpu_count() or 4,
            }
            
            # Load the model
            self.model = AutoModelForCausalLM.from_pretrained(
                self.model_name,
                model_file=self.model_file,
                **model_kwargs
            )
                
        except Exception as e:
            raise RuntimeError(f"Failed to load model: {str(e)}. Please check your model configuration and system requirements.")

    def generate_sql(self, prompt: str, schema_info: str) -> str:
        """Generate SQL query from natural language prompt using the Mistral model."""
        logger.info(f"Generating SQL for prompt: {prompt}")
        
        # Preprocess the prompt to be more specific
        prompt = prompt.strip()
        if not any(word in prompt.lower() for word in ['show', 'list', 'get', 'find', 'what', 'how']):
            prompt = f"show {prompt}"
        
        full_prompt = f"""<s>[INST] You are a SQL expert assistant. Your task is to convert natural language questions into valid SQL queries.

SYSTEM RULES:
1. ALWAYS generate complete, valid SQL queries
2. NEVER output partial or incomplete queries
3. ALWAYS include a FROM clause in SELECT queries
4. ALWAYS specify columns to select (use * only when appropriate)
5. NEVER include markdown formatting or code blocks
6. ALWAYS end queries with a semicolon
7. ALWAYS use table aliases for better readability
8. ALWAYS include proper JOINs when querying multiple tables

DATABASE SCHEMA:
{schema_info}

USER QUESTION: {prompt}

Generate a valid SQL query that answers this question. The query must be complete and executable.
Output ONLY the SQL query without any explanations or formatting.
[/INST]</s>"""

        try:
            logger.info("Sending prompt to model...")
            generated_text = self.model(
                full_prompt,
                max_new_tokens=512,
                temperature=0.1,  # Lower temperature for more consistent output
                top_p=0.95,
                repetition_penalty=1.1,
                stop=["</s>", "[INST]", "Question:", "SQL:", "```", "Here's", "The query"],
            )
            
            logger.info(f"Model generated text: {generated_text}")
            sql_query = self._extract_sql_query(generated_text)
            logger.info(f"Extracted SQL query: {sql_query}")
            
            # Additional validation for SELECT queries
            if sql_query.lower().startswith("select"):
                # Check for basic SELECT query structure
                if "from" not in sql_query.lower():
                    # Try to fix common issues
                    if "select" in sql_query.lower():
                        # If it's just a SELECT without FROM, add FROM sales
                        if "*" in sql_query.lower():
                            sql_query = "SELECT s.* FROM sales s;"
                        else:
                            # Try to extract the columns and add FROM sales
                            select_part = sql_query.lower().split(";")[0].replace("select", "").strip()
                            if select_part:
                                # Add table alias to columns if not present
                                columns = [col.strip() for col in select_part.split(",")]
                                columns_with_alias = []
                                for col in columns:
                                    if "." not in col:
                                        if "as" in col.lower():
                                            col_name, alias = col.lower().split("as")
                                            columns_with_alias.append(f"s.{col_name.strip()} as {alias.strip()}")
                                        else:
                                            columns_with_alias.append(f"s.{col.strip()}")
                                    else:
                                        columns_with_alias.append(col)
                                sql_query = f"SELECT {', '.join(columns_with_alias)} FROM sales s;"
                            else:
                                raise ValueError("SELECT query must include a FROM clause and specify columns")
                
                if sql_query.lower().count("select") > 1:
                    raise ValueError("Query contains multiple SELECT statements")
                
                if "*" not in sql_query.lower() and "from" in sql_query.lower():
                    # If not selecting all columns, ensure at least one column is specified
                    select_part = sql_query.lower().split("from")[0]
                    if not any(col.strip() for col in select_part.replace("select", "").split(",")):
                        raise ValueError("SELECT query must specify at least one column")
            
            logger.info(f"Final SQL query: {sql_query}")
            return sql_query
            
        except Exception as e:
            logger.error(f"Error generating SQL: {str(e)}")
            raise ValueError(f"Error generating SQL: {str(e)}")

    def _extract_sql_query(self, generated_text: str) -> str:
        """Extract SQL query from generated text."""
        try:
            # Clean up the generated text
            text = generated_text.strip()
            
            # Remove any markdown formatting
            text = text.replace("```sql", "").replace("```", "")
            
            # Find the first SQL statement
            sql_match = re.search(r'(SELECT|INSERT|UPDATE|DELETE|CREATE|ALTER|DROP).*?;', text, re.IGNORECASE | re.DOTALL)
            if not sql_match:
                raise ValueError("No SQL query found in generated text")
            
            sql_query = sql_match.group(0).strip()
            
            # Additional validation for empty or incomplete queries
            if len(sql_query.strip()) <= 2:
                raise ValueError("Generated query is incomplete")
            
            # Basic SQL validation
            if sql_query.lower().startswith("select"):
                if "from" not in sql_query.lower():
                    raise ValueError("SELECT query must include a FROM clause")
                if sql_query.lower().count("select") > 1:
                    raise ValueError("Query contains multiple SELECT statements")
            
            return sql_query
            
        except Exception as e:
            logger.error(f"Failed to extract SQL query: {str(e)}")
            raise ValueError(f"Failed to extract SQL query: {str(e)}")

# Create a singleton instance
model_instance: Optional[MistralModel] = None

def get_model() -> MistralModel:
    """Get or create the model instance."""
    global model_instance
    if model_instance is None:
        model_instance = MistralModel()
    return model_instance 