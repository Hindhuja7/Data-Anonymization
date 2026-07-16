"""
Redis Mapping System for Real-Time Anonymization

Handles:
- Real-to-fake mapping storage (Redis Hash Vault)
- Application-side encryption before storage
- Redis AOF configuration for crash safety
- Consistent anonymization across tables (referential integrity)
"""

import redis
import hashlib
import json
from typing import Optional, Any
from cryptography.fernet import Fernet
import os


class RedisMappingSystem:
    """
    Redis-based mapping system for consistent anonymization.
    """
    
    def __init__(
        self,
        host: str = "localhost",
        port: int = 6379,
        db: int = 0,
        password: Optional[str] = None,
        encryption_key: Optional[str] = None
    ):
        """
        Initialize Redis mapping system.
        
        Args:
            host: Redis host
            port: Redis port
            db: Redis database number
            password: Redis password
            encryption_key: Key for application-side encryption (auto-generated if None)
        """
        self.host = host
        self.port = port
        self.db = db
        self.password = password
        
        # Initialize encryption
        if encryption_key:
            self.encryption_key = encryption_key.encode()
        else:
            self.encryption_key = Fernet.generate_key()
        
        self.cipher = Fernet(self.encryption_key)
        
        # Initialize Redis client
        self.redis_client = redis.Redis(
            host=host,
            port=port,
            db=db,
            password=password,
            decode_responses=False  # Store as bytes for encryption
        )
        
        # Enable AOF for crash safety
        self._enable_aof()
    
    def _enable_aof(self):
        """Enable Redis Append-Only File for crash safety."""
        try:
            self.redis_client.config_set('appendonly', 'yes')
            self.redis_client.config_set('appendfsync', 'everysec')
            print("Redis AOF enabled for crash safety")
        except Exception as e:
            print(f"Warning: Could not enable Redis AOF: {e}")
    
    def _encrypt(self, value: str) -> bytes:
        """
        Encrypt value before storing in Redis.
        
        Args:
            value: Value to encrypt
        
        Returns:
            Encrypted bytes
        """
        return self.cipher.encrypt(value.encode())
    
    def _decrypt(self, encrypted_value: bytes) -> str:
        """
        Decrypt value from Redis.
        
        Args:
            encrypted_value: Encrypted bytes
        
        Returns:
            Decrypted string
        """
        return self.cipher.decrypt(encrypted_value).decode()
    
    def get_mapping(
        self,
        table_name: str,
        column_name: str,
        original_value: Any
    ) -> Optional[str]:
        """
        Get anonymized value from Redis mapping.
        
        Args:
            table_name: Table name
            column_name: Column name
            original_value: Original value to look up
        
        Returns:
            Anonymized value if exists, None otherwise
        """
        if original_value is None:
            return None
        
        # Create Redis key
        redis_key = f"mapping:{table_name}:{column_name}:{str(original_value)}"
        
        try:
            encrypted_value = self.redis_client.get(redis_key)
            if encrypted_value:
                return self._decrypt(encrypted_value)
        except Exception as e:
            print(f"Error getting mapping from Redis: {e}")
        
        return None
    
    def set_mapping(
        self,
        table_name: str,
        column_name: str,
        original_value: Any,
        anonymized_value: str
    ) -> bool:
        """
        Store anonymized value in Redis mapping.
        
        Args:
            table_name: Table name
            column_name: Column name
            original_value: Original value
            anonymized_value: Anonymized value
        
        Returns:
            True if successful, False otherwise
        """
        if original_value is None:
            return False
        
        # Create Redis key
        redis_key = f"mapping:{table_name}:{column_name}:{str(original_value)}"
        
        try:
            encrypted_value = self._encrypt(anonymized_value)
            self.redis_client.set(redis_key, encrypted_value)
            return True
        except Exception as e:
            print(f"Error setting mapping in Redis: {e}")
            return False
    
    def get_global_mapping(
        self,
        column_name: str,
        original_value: Any
    ) -> Optional[str]:
        """
        Get anonymized value from global mapping (cross-table consistency).
        
        Args:
            column_name: Column name (e.g., customer_id)
            original_value: Original value to look up
        
        Returns:
            Anonymized value if exists, None otherwise
        """
        if original_value is None:
            return None
        
        # Create global Redis key (no table prefix)
        redis_key = f"global:{column_name}:{str(original_value)}"
        
        try:
            encrypted_value = self.redis_client.get(redis_key)
            if encrypted_value:
                return self._decrypt(encrypted_value)
        except Exception as e:
            print(f"Error getting global mapping from Redis: {e}")
        
        return None
    
    def set_global_mapping(
        self,
        column_name: str,
        original_value: Any,
        anonymized_value: str
    ) -> bool:
        """
        Store anonymized value in global mapping (cross-table consistency).
        
        Args:
            column_name: Column name (e.g., customer_id)
            original_value: Original value
            anonymized_value: Anonymized value
        
        Returns:
            True if successful, False otherwise
        """
        if original_value is None:
            return False
        
        # Create global Redis key (no table prefix)
        redis_key = f"global:{column_name}:{str(original_value)}"
        
        try:
            encrypted_value = self._encrypt(anonymized_value)
            self.redis_client.set(redis_key, encrypted_value)
            return True
        except Exception as e:
            print(f"Error setting global mapping in Redis: {e}")
            return False
    
    def clear_mappings(self, table_name: Optional[str] = None):
        """
        Clear mappings from Redis.
        
        Args:
            table_name: If provided, clear only mappings for this table.
                       If None, clear all mappings.
        """
        try:
            if table_name:
                # Clear mappings for specific table
                pattern = f"mapping:{table_name}:*"
                keys = self.redis_client.keys(pattern)
                if keys:
                    self.redis_client.delete(*keys)
            else:
                # Clear all mappings
                patterns = ["mapping:*", "global:*"]
                for pattern in patterns:
                    keys = self.redis_client.keys(pattern)
                    if keys:
                        self.redis_client.delete(*keys)
            print("Mappings cleared from Redis")
        except Exception as e:
            print(f"Error clearing mappings from Redis: {e}")
    
    def get_mapping_stats(self) -> dict:
        """
        Get statistics about stored mappings.
        
        Returns:
            Dictionary with mapping statistics
        """
        try:
            table_mappings = len(self.redis_client.keys("mapping:*"))
            global_mappings = len(self.redis_client.keys("global:*"))
            
            return {
                "table_mappings": table_mappings,
                "global_mappings": global_mappings,
                "total_mappings": table_mappings + global_mappings
            }
        except Exception as e:
            print(f"Error getting mapping stats: {e}")
            return {
                "table_mappings": 0,
                "global_mappings": 0,
                "total_mappings": 0
            }
    
    def close(self):
        """Close Redis connection."""
        if self.redis_client:
            self.redis_client.close()
            print("Redis connection closed")


if __name__ == "__main__":
    # Test Redis mapping system
    mapping_system = RedisMappingSystem()
    
    # Test basic mapping
    mapping_system.set_mapping("employees", "customer_id", 123, "cust_abc123")
    result = mapping_system.get_mapping("employees", "customer_id", 123)
    print(f"Basic mapping test: {result}")
    
    # Test global mapping (cross-table consistency)
    mapping_system.set_global_mapping("customer_id", 123, "cust_xyz789")
    result = mapping_system.get_global_mapping("customer_id", 123)
    print(f"Global mapping test: {result}")
    
    # Test encryption
    mapping_system.set_mapping("employees", "aadhaar", "452188349021", "XXXXXX349021")
    result = mapping_system.get_mapping("employees", "aadhaar", "452188349021")
    print(f"Encrypted mapping test: {result}")
    
    # Get stats
    stats = mapping_system.get_mapping_stats()
    print(f"Mapping stats: {stats}")
    
    mapping_system.close()
