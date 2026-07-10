"""
Schema extractor to retrieve database metadata.
Extracts table names, column names, data types, primary keys, and foreign keys.
"""

from typing import List, Dict, Any
from sqlalchemy import inspect, Engine
from sqlalchemy.engine.reflection import Inspector
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SchemaExtractor:
    """Extract database schema information."""
    
    def __init__(self, engine: Engine):
        """
        Initialize schema extractor.
        
        Args:
            engine: SQLAlchemy Engine instance
        """
        self.engine = engine
        self.inspector: Inspector = inspect(engine)
    
    def get_table_names(self) -> List[str]:
        """
        Get all table names in the database.
        
        Returns:
            List of table names
        """
        try:
            table_names = self.inspector.get_table_names()
            logger.info(f"Found {len(table_names)} tables")
            return table_names
        except Exception as e:
            logger.error(f"Failed to get table names: {e}")
            raise
    
    def get_table_schema(self, table_name: str) -> Dict[str, Any]:
        """
        Get complete schema information for a table.
        
        Args:
            table_name: Name of the table
        
        Returns:
            Dictionary with table schema information
        """
        try:
            columns = self.inspector.get_columns(table_name)
            primary_keys = self.inspector.get_pk_constraint(table_name)
            foreign_keys = self.inspector.get_foreign_keys(table_name)
            
            column_info = []
            for col in columns:
                column_info.append({
                    "column_name": col["name"],
                    "data_type": str(col["type"]),
                    "nullable": col.get("nullable", True),
                    "default": col.get("default"),
                    "autoincrement": col.get("autoincrement", False)
                })
            
            schema = {
                "table_name": table_name,
                "columns": column_info,
                "primary_keys": primary_keys.get("constrained_columns", []),
                "foreign_keys": foreign_keys
            }
            
            logger.info(f"Extracted schema for table: {table_name}")
            return schema
            
        except Exception as e:
            logger.error(f"Failed to get schema for table {table_name}: {e}")
            raise
    
    def get_all_schemas(self) -> List[Dict[str, Any]]:
        """
        Get schema information for all tables.
        
        Returns:
            List of schema dictionaries for all tables
        """
        table_names = self.get_table_names()
        schemas = []
        
        for table_name in table_names:
            try:
                schema = self.get_table_schema(table_name)
                schemas.append(schema)
            except Exception as e:
                logger.warning(f"Skipping table {table_name} due to error: {e}")
                continue
        
        logger.info(f"Extracted schemas for {len(schemas)} tables")
        return schemas
    
    def get_column_names(self, table_name: str) -> List[str]:
        """
        Get column names for a specific table.
        
        Args:
            table_name: Name of the table
        
        Returns:
            List of column names
        """
        try:
            columns = self.inspector.get_columns(table_name)
            return [col["name"] for col in columns]
        except Exception as e:
            logger.error(f"Failed to get column names for table {table_name}: {e}")
            raise
    
    def get_column_data_type(self, table_name: str, column_name: str) -> str:
        """
        Get data type for a specific column.
        
        Args:
            table_name: Name of the table
            column_name: Name of the column
        
        Returns:
            Data type as string
        """
        try:
            columns = self.inspector.get_columns(table_name)
            for col in columns:
                if col["name"] == column_name:
                    return str(col["type"])
            raise ValueError(f"Column {column_name} not found in table {table_name}")
        except Exception as e:
            logger.error(f"Failed to get data type for {table_name}.{column_name}: {e}")
            raise
