"""
Database connector using SQLAlchemy with read-only connection support.
Supports PostgreSQL, MySQL, and SQL Server.
"""

from typing import Optional
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DatabaseConnector:
    """Database connector with read-only connection support."""
    
    def __init__(
        self,
        database_type: str,
        host: str,
        port: int,
        username: str,
        password: str,
        database_name: str
    ):
        """
        Initialize database connector.
        
        Args:
            database_type: 'postgresql', 'mysql', or 'sqlserver'
            host: Database host
            port: Database port
            username: Database username
            password: Database password
            database_name: Database name
        """
        self.database_type = database_type.lower()
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.database_name = database_name
        self.engine: Optional[Engine] = None
        
        self._validate_database_type()
    
    def _validate_database_type(self):
        """Validate database type."""
        valid_types = ['postgresql', 'mysql', 'sqlserver']
        if self.database_type not in valid_types:
            raise ValueError(f"Invalid database_type: {self.database_type}. Must be one of: {valid_types}")
    
    def _build_connection_string(self) -> str:
        """Build SQLAlchemy connection string."""
        if self.database_type == 'postgresql':
            return f"postgresql://{self.username}:{self.password}@{self.host}:{self.port}/{self.database_name}"
        elif self.database_type == 'mysql':
            return f"mysql+pymysql://{self.username}:{self.password}@{self.host}:{self.port}/{self.database_name}"
        elif self.database_type == 'sqlserver':
            return f"mssql+pyodbc://{self.username}:{self.password}@{self.host}:{self.port}/{self.database_name}?driver=ODBC+Driver+17+for+SQL+Server"
        else:
            raise ValueError(f"Unsupported database type: {self.database_type}")
    
    def connect(self, read_only: bool = True) -> Engine:
        """
        Establish database connection.
        
        Args:
            read_only: If True, sets transaction to read-only mode
        
        Returns:
            SQLAlchemy Engine instance
        """
        try:
            connection_string = self._build_connection_string()
            self.engine = create_engine(connection_string)
            
            # Test connection
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            
            logger.info(f"Successfully connected to {self.database_type} database: {self.database_name}")
            
            # Set read-only mode if requested
            if read_only:
                self._set_read_only_mode()
            
            return self.engine
            
        except SQLAlchemyError as e:
            logger.error(f"Failed to connect to database: {e}")
            raise
    
    def _set_read_only_mode(self):
        """Set connection to read-only mode based on database type."""
        try:
            with self.engine.connect() as conn:
                if self.database_type == 'postgresql':
                    conn.execute(text("SET TRANSACTION READ ONLY"))
                elif self.database_type == 'mysql':
                    conn.execute(text("SET SESSION TRANSACTION READ ONLY"))
                elif self.database_type == 'sqlserver':
                    conn.execute(text("SET TRANSACTION ISOLATION LEVEL SNAPSHOT"))
            logger.info("Set connection to read-only mode")
        except SQLAlchemyError as e:
            logger.warning(f"Could not set read-only mode: {e}. Connection will be read-only by application logic.")
    
    def disconnect(self):
        """Close database connection."""
        if self.engine:
            self.engine.dispose()
            logger.info("Database connection closed")
    
    def test_connection(self) -> bool:
        """
        Test database connection.
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            return True
        except SQLAlchemyError as e:
            logger.error(f"Connection test failed: {e}")
            return False
    
    def __enter__(self):
        """Context manager entry."""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.disconnect()
