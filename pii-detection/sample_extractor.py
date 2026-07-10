"""
Sample data extractor to fetch representative rows from database tables.
Fetches 20 sample rows per table for PII detection analysis.
"""

from typing import List, Dict, Any
from sqlalchemy import text, Engine
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SampleExtractor:
    """Extract sample data from database tables."""
    
    def __init__(self, engine: Engine, sample_size: int = 20):
        """
        Initialize sample extractor.
        
        Args:
            engine: SQLAlchemy Engine instance
            sample_size: Number of sample rows to fetch per table (default: 20)
        """
        self.engine = engine
        self.sample_size = sample_size
    
    def get_table_samples(self, table_name: str, column_names: List[str]) -> Dict[str, List[str]]:
        """
        Get sample values for each column in a table.
        
        Args:
            table_name: Name of the table
            column_names: List of column names to extract samples for
        
        Returns:
            Dictionary mapping column names to lists of sample values
        """
        try:
            with self.engine.connect() as conn:
                # Build SELECT query
                columns_str = ", ".join([f'"{col}"' for col in column_names])
                query = text(f'SELECT {columns_str} FROM "{table_name}" LIMIT {self.sample_size}')
                
                result = conn.execute(query)
                rows = result.fetchall()
                
                # Organize samples by column
                samples = {col: [] for col in column_names}
                
                for row in rows:
                    for i, col in enumerate(column_names):
                        value = row[i]
                        # Convert to string, handle None values
                        if value is None:
                            samples[col].append("NULL")
                        else:
                            samples[col].append(str(value))
                
                logger.info(f"Extracted {len(rows)} sample rows from table: {table_name}")
                return samples
                
        except Exception as e:
            logger.error(f"Failed to get samples for table {table_name}: {e}")
            raise
    
    def get_column_samples(self, table_name: str, column_name: str) -> List[str]:
        """
        Get sample values for a specific column.
        
        Args:
            table_name: Name of the table
            column_name: Name of the column
        
        Returns:
            List of sample values as strings
        """
        try:
            with self.engine.connect() as conn:
                query = text(f'SELECT "{column_name}" FROM "{table_name}" LIMIT {self.sample_size}')
                result = conn.execute(query)
                rows = result.fetchall()
                
                samples = []
                for row in rows:
                    value = row[0]
                    if value is None:
                        samples.append("NULL")
                    else:
                        samples.append(str(value))
                
                logger.info(f"Extracted {len(samples)} samples for column: {table_name}.{column_name}")
                return samples
                
        except Exception as e:
            logger.error(f"Failed to get samples for column {table_name}.{column_name}: {e}")
            raise
    
    def get_all_table_samples(self, table_schemas: List[Dict[str, Any]]) -> Dict[str, Dict[str, List[str]]]:
        """
        Get sample data for all tables.
        
        Args:
            table_schemas: List of table schema dictionaries
        
        Returns:
            Dictionary mapping table names to column sample dictionaries
        """
        all_samples = {}
        
        for schema in table_schemas:
            table_name = schema["table_name"]
            column_names = [col["column_name"] for col in schema["columns"]]
            
            try:
                samples = self.get_table_samples(table_name, column_names)
                all_samples[table_name] = samples
            except Exception as e:
                logger.warning(f"Skipping samples for table {table_name} due to error: {e}")
                all_samples[table_name] = {col: [] for col in column_names}
        
        logger.info(f"Extracted samples for {len(all_samples)} tables")
        return all_samples
