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

    

    def __init__(self, engine: Engine, sample_size: int = 20, database_type: str = "postgresql"):

        """

        Initialize sample extractor.

        

        Args:

            engine: SQLAlchemy Engine instance

            sample_size: Number of sample rows to fetch per table (default: 20)

            database_type: Database type ('postgresql', 'mysql', 'sqlserver') for random function

        """

        self.engine = engine

        self.sample_size = sample_size

        self.database_type = database_type.lower()
    
    def _get_random_function(self) -> str:
        """Get database-specific random function."""
        if self.database_type == 'postgresql':
            return 'RANDOM()'
        elif self.database_type == 'mysql':
            return 'RAND()'
        elif self.database_type == 'sqlserver':
            return 'NEWID()'
        else:
            return 'RANDOM()'

    

    def get_table_samples(self, table_name: str, column_names: List[str]) -> Dict[str, List[str]]:

        """

        Get sample values for each column in a table using column-wise random sampling.

        

        Args:

            table_name: Name of the table

            column_names: List of column names to extract samples for

        

        Returns:

            Dictionary mapping column names to lists of sample values

        """

        try:

            samples = {col: [] for col in column_names}

            

            with self.engine.connect() as conn:

                # Use single query to fetch all columns at once
                random_func = self._get_random_function()
                columns_str = ', '.join([f'"{col}"' for col in column_names])
                query = text(f'SELECT {columns_str} FROM "{table_name}" ORDER BY {random_func} LIMIT {self.sample_size}')

                result = conn.execute(query)
                rows = result.fetchall()

                # Extract values column-wise
                for row in rows:
                    for i, value in enumerate(row):
                        col_name = column_names[i]
                        if value is None:
                            samples[col_name].append("NULL")
                        else:
                            samples[col_name].append(str(value))

                

                logger.info(f"Extracted column-wise random samples from table: {table_name}")

                conn.rollback()
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

                conn.rollback()
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

