from typing import Dict, List
from app.utils.db import get_schema_info

class SchemaReader:
    @staticmethod
    def get_formatted_schema() -> str:
        """
        Get the database schema formatted as a string for the LLM prompt.
        
        Returns:
            str: Formatted schema string
        """
        schema_info = get_schema_info()
        formatted_schema = []
        
        for table_name, columns in schema_info.items():
            # Format column information
            column_descriptions = []
            for col in columns:
                col_type = col["type"]
                nullable = "NULL" if col["nullable"] else "NOT NULL"
                pk = "PRIMARY KEY" if col["primary_key"] else ""
                default = f"DEFAULT {col['default']}" if col["default"] is not None else ""
                
                # Combine column attributes
                attrs = [attr for attr in [pk, nullable, default] if attr]
                col_desc = f"{col['name']} ({col_type})"
                if attrs:
                    col_desc += f" {' '.join(attrs)}"
                column_descriptions.append(col_desc)
            
            # Format table description
            table_desc = f"Table: {table_name}\nColumns:\n" + "\n".join(f"  - {col}" for col in column_descriptions)
            formatted_schema.append(table_desc)
        
        return "\n\n".join(formatted_schema)
    
    @staticmethod
    def get_schema_summary() -> Dict[str, List[str]]:
        """
        Get a simplified schema summary with just table names and column names.
        Useful for quick reference in the UI.
        
        Returns:
            Dict[str, List[str]]: Dictionary mapping table names to lists of column names
        """
        schema_info = get_schema_info()
        return {
            table_name: [col["name"] for col in columns]
            for table_name, columns in schema_info.items()
        } 