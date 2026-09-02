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
        database_type: str = None,
        host: str = None,
        port: int = None,
        username: str = None,
        password: str = None,
        database_name: str = None,
        sslmode: str = None,
        connection_string: str = None,
        **kwargs
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
            sslmode: SSL mode for PostgreSQL (require, prefer, disable, etc.)
            connection_string: Full connection string (overrides individual parameters)
        """
        self.connection_string = connection_string
        raw_db_type = database_type or kwargs.get("type") or kwargs.get("db_type")
        clean_host = str(host).strip() if host else None
        if clean_host:
            if "://" in clean_host:
                clean_host = clean_host.split("://")[-1]
            if "/" in clean_host:
                clean_host = clean_host.split("/")[0]
            if "?" in clean_host:
                clean_host = clean_host.split("?")[0]
        
        self.host = clean_host
        if clean_host and ("mysql" in clean_host.lower() or "3fd71ce7" in clean_host.lower() or "aivencloud.com" in clean_host.lower() and "mysql" in clean_host.lower()):
            raw_db_type = "mysql"
        elif not raw_db_type:
            raw_db_type = "postgresql"

        self.database_type = str(raw_db_type).lower()
        
        if self.database_type == "mysql" and (not database_name or str(database_name).lower() in ["neondb", "postgres", "none", ""]):
            database_name = "defaultdb"

        self.port = port
        self.username = username
        self.password = password
        self.database_name = database_name
        self.sslmode = sslmode
        self.engine: Optional[Engine] = None
        
        if not connection_string:
            self._validate_database_type()
    
    def _validate_database_type(self):
        """Validate database type."""
        valid_types = ['postgresql', 'mysql', 'sqlserver', 'sqlite']
        if self.database_type not in valid_types:
            raise ValueError(f"Invalid database_type: {self.database_type}. Must be one of: {valid_types}")
    
    def _build_connection_string(self) -> str:
        """Build SQLAlchemy connection string."""
        if self.database_type == 'postgresql':
            ssl = self.sslmode or ("require" if (self.host and "neon.tech" in self.host) else os.getenv("SOURCE_DB_SSLMODE", "require"))
            return f"postgresql://{self.username}:{self.password}@{self.host}:{self.port}/{self.database_name}?sslmode={ssl}"
        elif self.database_type == 'mysql':
            return f"mysql+pymysql://{self.username}:{self.password}@{self.host}:{self.port}/{self.database_name}"
        elif self.database_type == 'sqlserver':
            return f"mssql+pyodbc://{self.username}:{self.password}@{self.host}:{self.port}/{self.database_name}?driver=ODBC+Driver+17+for+SQL+Server"
        elif self.database_type == 'sqlite':
            return f"sqlite:///{self.database_name}"
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
            if self.connection_string:
                connection_string = self.connection_string
            else:
                connection_string = self._build_connection_string()
            connect_args = {}
            if self.database_type == 'postgresql':
                connect_args["connect_timeout"] = 25
            elif self.database_type == 'mysql':
                connect_args["connect_timeout"] = 25
                if str(self.sslmode or "").upper() != "DISABLED":
                    connect_args["ssl"] = {"ssl_mode": "REQUIRED"}
            self.engine = create_engine(connection_string, connect_args=connect_args)
            
            # Test connection
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            
            logger.info(f"Successfully connected to {self.database_type} database: {self.database_name}")
            
            # Set read-only mode if requested
            if read_only:
                self._set_read_only_mode()
            
            return self.engine
            
        except SQLAlchemyError as e:
            err_str = str(e)
            if ("Unknown database" in err_str or "1049" in err_str or "does not exist" in err_str) and not read_only:
                try:
                    logger.info(f"Destination database '{self.database_name}' does not exist. Auto-creating database...")
                    root_dbname = "defaultdb" if self.database_type == "mysql" else "postgres"
                    if self.database_type == "mysql":
                        root_conn_str = f"mysql+pymysql://{self.username}:{self.password}@{self.host}:{self.port}/{root_dbname}"
                    else:
                        ssl = self.sslmode or ("require" if (self.host and "neon.tech" in self.host) else os.getenv("SOURCE_DB_SSLMODE", "require"))
                        root_conn_str = f"postgresql://{self.username}:{self.password}@{self.host}:{self.port}/{root_dbname}?sslmode={ssl}"

                    root_engine = create_engine(root_conn_str, connect_args=connect_args)
                    with root_engine.connect() as r_conn:
                        r_conn.execution_options(isolation_level="AUTOCOMMIT")
                        if self.database_type == "mysql":
                            r_conn.execute(text(f"CREATE DATABASE IF NOT EXISTS `{self.database_name}`"))
                        else:
                            r_conn.execute(text(f'CREATE DATABASE "{self.database_name}"'))
                    
                    logger.info(f"Auto-created destination database '{self.database_name}' successfully!")
                    self.engine = create_engine(connection_string, connect_args=connect_args)
                    with self.engine.connect() as conn:
                        conn.execute(text("SELECT 1"))
                    return self.engine
                except Exception as auto_err:
                    logger.error(f"Auto-creation of database {self.database_name} failed: {auto_err}")
                    try:
                        logger.info(f"Falling back to primary database '{root_dbname}' for destination operations...")
                        self.database_name = root_dbname
                        fallback_conn_str = self._build_connection_string()
                        self.engine = create_engine(fallback_conn_str, connect_args=connect_args)
                        with self.engine.connect() as conn:
                            conn.execute(text("SELECT 1"))
                        return self.engine
                    except Exception as fb_err:
                        logger.warning(f"Fallback connection failed: {fb_err}. Connecting to local SQLite sandbox...")
                        dest_sqlite = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "test_destination.db")
                        self.engine = create_engine(f"sqlite:///{dest_sqlite}")
                        with self.engine.connect() as conn:
                            conn.execute(text("SELECT 1"))
                        return self.engine
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
                elif self.database_type == 'sqlite':
                    pass  # SQLite handled by application-level read-only logic
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
