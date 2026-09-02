import json
import os
from typing import Dict, Any, Optional
from app.core.config import config
from app.core.logger import logger
from app.core.exceptions import DatabaseException

class DatabaseService:
    """Service for database connection and configuration management"""
    
    def __init__(self):
        self.config_path = os.path.join(config.DIRECTORY, "database_config.json")
    
    def test_connection(self, config_data: Dict[str, Any]) -> Dict[str, Any]:
        """Test database connection with provided configuration"""
        try:
            logger.info(f"Testing database connection for {config_data.get('host', 'unknown')}")
            
            # If password is blank, try using stored password if available
            incoming_password = str(config_data.get("password", "")).strip()
            if not incoming_password and os.path.exists(self.config_path):
                try:
                    with open(self.config_path, 'r') as f:
                        existing = json.load(f)
                        config_data["password"] = existing.get("password", "").strip()
                except Exception:
                    pass
            else:
                config_data["password"] = incoming_password

            host = config_data.get("host")
            database = config_data.get("database")
            username = config_data.get("username")
            password = config_data.get("password")
            db_type = config_data.get("type", "postgresql")
            use_saved_credentials = config_data.get("use_saved_credentials", False)

            if not host or not database:
                return {
                    "status": "failed",
                    "message": "Host and Database name are required fields."
                }

            # If testing a manual/new config without a password and without explicit saved credential flag
            if not password and use_saved_credentials:
                if os.path.exists(self.config_path):
                    with open(self.config_path, 'r') as f:
                        saved = json.load(f)
                        password = saved.get("password", "")

            if not password and not use_saved_credentials:
                return {
                    "status": "failed",
                    "message": "Password is required for testing a manual/new database connection."
                }

            # Perform actual connection test
            try:
                from database_connector import DatabaseConnector
                port_val = int(config_data.get("port", 5432)) if config_data.get("port") else 5432
                connector = DatabaseConnector(
                    database_type=db_type,
                    host=host,
                    port=port_val,
                    username=username,
                    password=password,
                    database_name=database
                )
                connector.connect(read_only=True)
                connector.disconnect()
                return {
                    "status": "success",
                    "message": "Database connection test successful!",
                    "database": database,
                    "host": host
                }
            except Exception as conn_err:
                logger.warning(f"Database connection attempt failed: {conn_err}")
                clean_msg = self._sanitize_connection_error(str(conn_err), host, port_val, username, database)
                return {
                    "status": "failed",
                    "message": clean_msg
                }
                
        except Exception as e:
            logger.error(f"Database connection test failed: {e}")
            return {
                "status": "failed",
                "message": f"Connection test failed: {str(e)}"
            }

    def _sanitize_connection_error(self, err_str: str, host: str, port: int, username: str, database: str) -> str:
        """Sanitize raw database error messages to prevent exposing secrets or verbose traces."""
        err_lower = err_str.lower()
        if "name or service not known" in err_lower or "could not translate host name" in err_lower:
            return f"DNS lookup failed for host '{host}'. Please verify the host address (e.g. Neon host format: 'ep-something-pooler.us-east-1.aws.neon.tech' without extra subdomains like '.c-9' or URL prefixes)."
        elif "timeout" in err_lower or "timed out" in err_lower:
            return f"Connection attempt timed out for {host}:{port}. If using Neon PostgreSQL, the compute endpoint may be waking from an auto-paused state — please try clicking Test Connection again."
        elif "could not connect" in err_lower or "connection refused" in err_lower:
            return f"Unable to reach database server at {host}:{port}. Please verify host address, port, and network/firewall rules."
        elif "password authentication failed" in err_lower or "access denied" in err_lower:
            return f"Authentication failed for user '{username}'. Please check your password."
        elif "database" in err_lower and ("does not exist" in err_lower or "unknown database" in err_lower):
            return f"Database '{database}' does not exist on target server."
        else:
            return f"Connection failed to {host}:{port}. Please check your credentials and database configuration."

    def inspect_database(self, config_data: Dict[str, Any]) -> Dict[str, Any]:
        """Inspect connected database metadata dynamically without returning secrets."""
        import time
        start_time = time.time()

        try:
            host = config_data.get("host")
            database = config_data.get("database")
            username = config_data.get("username")
            password = config_data.get("password")
            db_type = config_data.get("type", "postgresql")
            use_saved = config_data.get("use_saved_credentials", False)
            port_val = int(config_data.get("port", 5432)) if config_data.get("port") else 5432

            if not password and use_saved and os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    saved = json.load(f)
                    password = saved.get("password", "")

            if not host or not database or (db_type != "sqlite" and not password):
                return {
                    "status": "failed",
                    "message": "Host, database name, and password are required for inspection."
                }

            from database_connector import DatabaseConnector
            from schema_extractor import SchemaExtractor
            from sqlalchemy import inspect, text

            t_conn_start = time.time()
            connector = DatabaseConnector(
                database_type=db_type,
                host=host,
                port=port_val,
                username=username,
                password=password,
                database_name=database
            )
            connector.connect(read_only=True)
            t_conn = time.time() - t_conn_start
            
            t_disc_start = time.time()
            inspector = inspect(connector.engine)
            extractor = SchemaExtractor(connector.engine)
            table_names = inspector.get_table_names()
            t_disc = time.time() - t_disc_start

            tables_list = []
            total_records = 0
            total_columns = 0

            with connector.engine.connect() as conn:
                for table_name in table_names:
                    t_col_start = time.time()
                    cols = inspector.get_columns(table_name)
                    cols_count = len(cols)
                    t_col = time.time() - t_col_start

                    t_cnt_start = time.time()
                    row_count = 0
                    try:
                        res = conn.execute(text(f'SELECT count(*) FROM "{table_name}"'))
                        row_count = res.scalar() or 0
                    except Exception:
                        pass
                    t_cnt = time.time() - t_cnt_start

                    logger.info(f"DIAGNOSTIC - Table {table_name}: col_schema={t_col:.3f}s, count={t_cnt:.3f}s ({row_count} rows)")

                    total_columns += cols_count
                    total_records += row_count
                    tables_list.append({
                        "name": table_name,
                        "columns": cols_count,
                        "records": row_count
                    })

            connector.disconnect()
            total_inspection_time = time.time() - start_time
            logger.info(f"TOTAL INSPECTION DIAGNOSTICS - Conn: {t_conn:.3f}s, Disc: {t_disc:.3f}s, Total: {total_inspection_time:.3f}s")

            return {
                "status": "success",
                "database": database,
                "total_tables": len(tables_list),
                "total_records": total_records,
                "total_columns": total_columns,
                "tables": tables_list,
                "timing": {
                    "connection_time_sec": round(t_conn, 3),
                    "discovery_time_sec": round(t_disc, 3),
                    "total_inspection_time_sec": round(total_inspection_time, 3)
                }
            }
        except Exception as e:
            logger.error(f"Database inspection failed: {e}")
            clean_msg = self._sanitize_connection_error(str(e), config_data.get("host", ""), int(config_data.get("port", 5432) or 5432), config_data.get("username", ""), config_data.get("database", ""))
            return {
                "status": "failed",
                "message": f"Database inspection failed: {clean_msg}"
            }
    
    def _get_user_config_path(self, user_id: Optional[str] = None) -> Optional[str]:
        if not user_id or user_id in ["null", "undefined", "anonymous"]:
            return None
        safe_user = "".join(c for c in str(user_id) if c.isalnum() or c in ['-', '_'])
        return os.path.join(config.DIRECTORY, f"database_config_{safe_user}.json")

    def save_configuration(self, config_data: Dict[str, Any], user_id: Optional[str] = None) -> Dict[str, Any]:
        """Save database configuration to user-scoped file"""
        try:
            target_path = self._get_user_config_path(user_id) or self.config_path
            existing_config = {}
            if os.path.exists(target_path):
                try:
                    with open(target_path, 'r') as f:
                        existing_config = json.load(f)
                except Exception:
                    pass
            elif os.path.exists(self.config_path):
                try:
                    with open(self.config_path, 'r') as f:
                        existing_config = json.load(f)
                except Exception:
                    pass

            # Merge config fields safely
            merged_config = dict(existing_config)
            for k, v in config_data.items():
                if v is not None and str(v).strip() != "":
                    merged_config[k] = v

            final_password = str(merged_config.get("password", "")).strip()
            db_type = merged_config.get("type", "postgresql")
            if db_type != "sqlite" and not final_password:
                return {
                    "status": "failed",
                    "message": "Password is required for database configuration."
                }

            config_data = merged_config
            config_data["type"] = db_type
            config_data["database_type"] = db_type
            db_name_val = config_data.get("database") or config_data.get("database_name") or "defaultdb"
            config_data["database"] = db_name_val
            config_data["database_name"] = db_name_val
            config_data["destination_database_name"] = f"{db_name_val}_anonymized"
            config_data["password"] = final_password
            config_data["user_id"] = user_id or "default"

            if "auto_start" not in config_data:
                config_data["auto_start"] = False
            
            with open(self.config_path, 'w') as f:
                json.dump(config_data, f, indent=2)

            if target_path != self.config_path:
                try:
                    with open(target_path, 'w') as f:
                        json.dump(config_data, f, indent=2)
                except Exception:
                    pass
            
            logger.info(f"Database configuration saved for user '{user_id or 'default'}'")
            return {"status": "success", "message": "Configuration saved successfully"}
            
        except Exception as e:
            logger.error(f"Failed to save database configuration: {e}")
            return {"status": "failed", "message": f"Failed to save configuration: {str(e)}"}
    
    def load_configuration(self, user_id: Optional[str] = None) -> Dict[str, Any]:
        """Load database configuration from user-scoped file or default config file"""
        try:
            user_path = self._get_user_config_path(user_id)
            target_path = user_path if (user_path and os.path.exists(user_path)) else self.config_path
            
            if not target_path or not os.path.exists(target_path):
                logger.info(f"No database configuration found for user '{user_id or 'default'}' (unconfigured)")
                return {
                    "status": "not_configured",
                    "configured": False,
                    "config": None
                }
            
            with open(target_path, 'r') as f:
                config_data = json.load(f)
            
            has_password = bool(config_data.get("password"))
            sanitized = {k: v for k, v in config_data.items() if k != "password"}
            sanitized["password"] = ""
            sanitized["has_password"] = has_password
            sanitized["status"] = "success"
            sanitized["configured"] = True

            logger.info(f"Database configuration loaded for user '{user_id}'")
            return sanitized
            
        except Exception as e:
            logger.error(f"Failed to load database configuration: {e}")
            return {"status": "not_configured", "configured": False, "config": None}
    
    def delete_configuration(self, user_id: Optional[str] = None) -> Dict[str, Any]:
        """Delete user-scoped database configuration file"""
        try:
            target_path = self._get_user_config_path(user_id) or self.config_path
            if os.path.exists(target_path):
                os.remove(target_path)
                logger.info(f"Database configuration deleted for user '{user_id}'")
                return {"status": "success", "message": "Configuration deleted"}
            else:
                return {"status": "not_found", "message": "Configuration not found"}
                
        except Exception as e:
            logger.error(f"Failed to delete database configuration: {e}")
            return {"status": "failed", "message": str(e)}

# Global database service instance
database_service = DatabaseService()
