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
    
    def get_table_names(self, target_table: str = None) -> List[str]:
        """
        Get table names in the database, filtered by targeted table if specified.
        """
        try:
            import os
            target = target_table or os.getenv("TARGET_TABLE") or os.getenv("TABLES_TO_PROCESS")
            db_tables = self.inspector.get_table_names()
            if target:
                requested_tables = [t.strip() for t in target.split(",") if t.strip()]
                filtered = [t for t in requested_tables if t in db_tables]
                if filtered:
                    logger.info(f"Target table validation passed for: {filtered}")
                    return filtered
                else:
                    raise ValueError(f"Target table '{target}' strictly does not exist in connected database! Available database tables: {db_tables}")

            logger.info(f"Found {len(db_tables)} tables in database")
            return db_tables
        except Exception as e:
            logger.error(f"Failed to get table names: {e}")
            raise
    
    def get_table_schema(self, table_name: str) -> Dict[str, Any]:
        """
        Get complete schema information for a table including all constraints, keys, and metadata.
        
        Args:
            table_name: Name of the table
        
        Returns:
            Dictionary with complete table schema information
        """
        try:
            # Extract all available schema information automatically
            columns = self.inspector.get_columns(table_name)
            
            # Wrap optional dialect capabilities in try-except to prevent crashes on SQLite/unsupported engines
            primary_keys = {}
            try:
                primary_keys = self.inspector.get_pk_constraint(table_name)
            except Exception:
                pass
                
            foreign_keys = []
            try:
                foreign_keys = self.inspector.get_foreign_keys(table_name)
            except Exception:
                pass
                
            unique_constraints = []
            try:
                unique_constraints = self.inspector.get_unique_constraints(table_name)
            except Exception:
                pass
                
            check_constraints = []
            try:
                check_constraints = self.inspector.get_check_constraints(table_name)
            except Exception:
                pass
                
            indexes = []
            try:
                indexes = self.inspector.get_indexes(table_name)
            except Exception:
                pass
                
            table_comment = None
            try:
                table_comment = self.inspector.get_table_comment(table_name)
            except Exception:
                pass
            
            # Enhanced column information with all metadata
            column_info = []
            for col in columns:
                column_info.append({
                    "column_name": col["name"],
                    "data_type": str(col["type"]),
                    "nullable": col.get("nullable", True),
                    "default": col.get("default"),
                    "autoincrement": col.get("autoincrement", False),
                    "comment": col.get("comment"),
                    "computed": col.get("computed"),
                    "identity": col.get("identity")
                })
            
            schema = {
                "table_name": table_name,
                "columns": column_info,
                "primary_keys": primary_keys.get("constrained_columns", []) if primary_keys else [],
                "primary_key_constraint": primary_keys,
                "foreign_keys": foreign_keys,
                "unique_constraints": unique_constraints,
                "check_constraints": check_constraints,
                "indexes": indexes,
                "table_comment": table_comment
            }
            
            logger.info(f"Extracted complete schema for table: {table_name}")
            return schema
            
        except Exception as e:
            logger.error(f"Failed to get schema for table {table_name}: {e}")
            raise
    
    def get_all_schemas(self, target_table: str = None) -> List[Dict[str, Any]]:
        """
        Extract complete schema information for target table or all database tables.
        
        Returns:
            List of schema dictionaries for all tables
        """
        table_names = self.get_table_names(target_table=target_table)
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
