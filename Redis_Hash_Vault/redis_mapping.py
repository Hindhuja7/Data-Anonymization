"""
Redis Mapping System for Real-Time Anonymization

Handles:
- Real-to-fake mapping storage (Redis Hash Vault using HSET/HGET)
- Application-side encryption before storage (Fernet)
- Hashing original values (SHA-256) to prevent PII exposure in Redis keys/fields
- Redis AOF and maxmemory configuration automatically for resilience
- Consistent anonymization across tables (referential integrity)
- Local in-memory dictionary fallback cache & auto-sync when Redis recovers
"""

import redis
import hashlib
import json
from typing import Optional, Any, Dict
from cryptography.fernet import Fernet
import os
from aof_config import configure_redis_mitigations

# Try loading from .env if possible (reusing encryption key or generating one)
DEFAULT_KEY = os.getenv("ENCRYPTION_KEY") or os.getenv("HMAC_SECRET")


class RedisMappingSystem:
    """
    Redis-based memory-efficient mapping system for consistent anonymization.
    """
    
    def __init__(
        self,
        host: str = "localhost",
        port: int = 6379,
        db: int = 0,
        password: Optional[str] = None,
        encryption_key: Optional[str] = None,
        hmac_secret: Optional[str] = None
    ):
        """
        Initialize Redis mapping system.
        
        Args:
            host: Redis host
            port: Redis port
            db: Redis database number
            password: Redis password
            encryption_key: Key for encryption (loaded from env or auto-generated)
            hmac_secret: Backward compatibility secret key mapping
        """
        self.host = host
        self.port = port
        self.db = db
        self.password = password
        
        # Load environment variables dynamically
        from dotenv import load_dotenv
        load_dotenv()
        
        # 1. Initialize encryption
        key_source = encryption_key or hmac_secret or os.getenv("ENCRYPTION_KEY") or os.getenv("HMAC_SECRET")
        if key_source:
            # Ensure key is correctly padded to 32 bytes and base64 encoded for Fernet
            if isinstance(key_source, str):
                key_bytes = key_source.encode()
            else:
                key_bytes = key_source
            # Fernet keys must be 32 url-safe base64-encoded bytes
            # We derive a safe key using SHA-256 and base64 encoding it
            import base64
            derived_key = base64.urlsafe_b64encode(hashlib.sha256(key_bytes).digest())
            self.encryption_key = derived_key
        else:
            self.encryption_key = Fernet.generate_key()
        
        self.cipher = Fernet(self.encryption_key)
        
        # 2. Initialize Redis Client
        self.redis_client = redis.Redis(
            host=host,
            port=port,
            db=db,
            password=password,
            decode_responses=False,  # Store as bytes for encryption
            socket_timeout=0.05,
            socket_connect_timeout=0.05
        )
        
        self.online = True
        
        # 3. Local In-Memory Fallback Caches
        # Key format: "table:column:hashed_val"
        self.local_cache: Dict[str, str] = {}
        # Key format: "column:hashed_val"
        self.global_cache: Dict[str, str] = {}
        
        # 4. Configure Redis automatically for resilience
        self._configure_redis_mitigations()

    def _configure_redis_mitigations(self):
        """Configure Redis settings automatically for resilience and zero data loss."""
        try:
            # Check connection
            self.redis_client.ping()
            self.online = True
            
            # Delegate to Redis_AOF_Safety module
            configure_redis_mitigations(self.redis_client)
        except Exception as e:
            self.online = False
            print(f"Warning: Could not configure Redis mitigations: {e}. Falling back to local cache.")

    def _hash_key(self, value: str) -> str:
        """
        Hash the sensitive original value using SHA-256 with encryption_key as salt
        to prevent raw PII from being stored in Redis keys/fields.
        """
        hasher = hashlib.sha256()
        hasher.update(self.encryption_key)
        hasher.update(value.encode('utf-8'))
        return hasher.hexdigest()

    def _encrypt(self, value: str) -> bytes:
        """Encrypt value before storing in Redis."""
        return self.cipher.encrypt(value.encode())
    
    def _decrypt(self, encrypted_value: bytes) -> str:
        """Decrypt value retrieved from Redis."""
        return self.cipher.decrypt(encrypted_value).decode()
    
    def check_connection(self) -> bool:
        """Check if Redis is back online and perform automatic cache synchronization if recovered."""
        if not self.online:
            try:
                self.redis_client.ping()
                self.online = True
                print("[OK] Redis connection recovered! Syncing local cache to Redis...")
                self.sync_local_cache_to_redis()
            except Exception:
                self.online = False
        return self.online

    def sync_local_cache_to_redis(self):
        """Synchronize locally cached mappings back to Redis when it comes online."""
        if not self.online:
            return
            
        synced_local = 0
        synced_global = 0
        
        try:
            # 1. Sync Table Mappings
            for cache_key, anonymized_value in list(self.local_cache.items()):
                # cache_key format: "table_name:column_name:hashed_val"
                parts = cache_key.split(":")
                if len(parts) == 3:
                    table_name, column_name, hashed_val = parts
                    hash_key = f"mapping:{table_name}:{column_name}"
                    encrypted_value = self._encrypt(anonymized_value)
                    # Use hsetnx (Set field in hash only if it does not exist) to avoid overwriting
                    if self.redis_client.hsetnx(hash_key, hashed_val, encrypted_value):
                        synced_local += 1
                    # Remove from local cache after attempt
                    self.local_cache.pop(cache_key, None)
                    
            # 2. Sync Global Mappings
            for cache_key, anonymized_value in list(self.global_cache.items()):
                # cache_key format: "column_name:hashed_val"
                parts = cache_key.split(":")
                if len(parts) == 2:
                    column_name, hashed_val = parts
                    hash_key = f"global:{column_name}"
                    encrypted_value = self._encrypt(anonymized_value)
                    if self.redis_client.hsetnx(hash_key, hashed_val, encrypted_value):
                        synced_global += 1
                    # Remove from local cache after attempt
                    self.global_cache.pop(cache_key, None)
                    
            if synced_local > 0 or synced_global > 0:
                print(f"[OK] Synced local cache to Redis: {synced_local} table mappings, {synced_global} global mappings")
                
        except Exception as e:
            print(f"Warning: Failed to complete auto-sync: {e}")
            self.online = False

    def get_mapping(
        self,
        table_name: str,
        column_name: str,
        original_value: Any
    ) -> Optional[str]:
        """
        Get anonymized value from Redis mapping using HGET on hashed keys.
        """
        if original_value is None:
            return None
            
        hashed_val = self._hash_key(str(original_value))
        cache_key = f"{table_name}:{column_name}:{hashed_val}"
        
        # Periodic health check check to auto-recover online status
        self.check_connection()
        
        if not self.online:
            return self.local_cache.get(cache_key)
            
        # Read from Redis Hash Key: "mapping:{table_name}:{column_name}"
        hash_key = f"mapping:{table_name}:{column_name}"
        try:
            encrypted_value = self.redis_client.hget(hash_key, hashed_val)
            if encrypted_value:
                # Decrypt and cache locally
                decrypted = self._decrypt(encrypted_value)
                self.local_cache[cache_key] = decrypted
                return decrypted
        except Exception as e:
            self.online = False
            print(f"Error getting mapping from Redis: {e}. Falling back to local cache.")
            return self.local_cache.get(cache_key)
            
        return None
    
    def set_mapping(
        self,
        table_name: str,
        column_name: str,
        original_value: Any,
        anonymized_value: str
    ) -> bool:
        """
        Store anonymized value in Redis mapping using HSET on hashed keys.
        """
        if original_value is None:
            return False
            
        hashed_val = self._hash_key(str(original_value))
        cache_key = f"{table_name}:{column_name}:{hashed_val}"
        
        # Always update local cache as backup
        self.local_cache[cache_key] = anonymized_value
        
        self.check_connection()
        
        if not self.online:
            return True  # Fallback written successfully to RAM
            
        # Write to Redis Hash Key: "mapping:{table_name}:{column_name}"
        hash_key = f"mapping:{table_name}:{column_name}"
        try:
            encrypted_value = self._encrypt(anonymized_value)
            self.redis_client.hset(hash_key, hashed_val, encrypted_value)
            return True
        except Exception as e:
            self.online = False
            print(f"Error setting mapping in Redis: {e}. Falling back to local cache.")
            return True

    def get_global_mapping(
        self,
        column_name: str,
        original_value: Any
    ) -> Optional[str]:
        """
        Get anonymized value from global mapping (cross-table consistency) using HGET.
        """
        if original_value is None:
            return None
            
        hashed_val = self._hash_key(str(original_value))
        cache_key = f"{column_name}:{hashed_val}"
        
        self.check_connection()
        
        if not self.online:
            return self.global_cache.get(cache_key)
            
        # Read from Redis Hash Key: "global:{column_name}"
        hash_key = f"global:{column_name}"
        try:
            encrypted_value = self.redis_client.hget(hash_key, hashed_val)
            if encrypted_value:
                decrypted = self._decrypt(encrypted_value)
                self.global_cache[cache_key] = decrypted
                return decrypted
        except Exception as e:
            self.online = False
            print(f"Error getting global mapping from Redis: {e}. Falling back to local cache.")
            return self.global_cache.get(cache_key)
        
        return None
    
    def set_global_mapping(
        self,
        column_name: str,
        original_value: Any,
        anonymized_value: str
    ) -> bool:
        """
        Store anonymized value in global mapping (cross-table consistency) using HSET.
        """
        if original_value is None:
            return False
            
        hashed_val = self._hash_key(str(original_value))
        cache_key = f"{column_name}:{hashed_val}"
        
        # Always update local cache as backup
        self.global_cache[cache_key] = anonymized_value
        
        self.check_connection()
        
        if not self.online:
            return True  # Fallback written successfully to RAM
            
        # Write to Redis Hash Key: "global:{column_name}"
        hash_key = f"global:{column_name}"
        try:
            encrypted_value = self._encrypt(anonymized_value)
            self.redis_client.hset(hash_key, hashed_val, encrypted_value)
            return True
        except Exception as e:
            self.online = False
            print(f"Error setting global mapping in Redis: {e}. Falling back to local cache.")
            return True
    
    def clear_mappings(self, table_name: Optional[str] = None):
        """
        Clear mappings from both Redis and local caches.
        """
        # Clear local caches
        if table_name:
            # Clear table-specific caches
            prefix = f"{table_name}:"
            self.local_cache = {k: v for k, v in self.local_cache.items() if not k.startswith(prefix)}
        else:
            self.local_cache.clear()
            self.global_cache.clear()
            
        if not self.online:
            print("Local caches cleared (Redis is offline)")
            return
            
        try:
            if table_name:
                # Find all columns for this table in current Redis keys
                # Mappings are stored in keys like: mapping:{table_name}:{column_name}
                pattern = f"mapping:{table_name}:*"
                keys = self.redis_client.keys(pattern)
                if keys:
                    self.redis_client.delete(*keys)
            else:
                # Clear all mappings and global mappings
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
        Get statistics about stored mappings across Redis and local memory.
        """
        # If offline, return local cache counts
        if not self.online:
            return {
                "table_mappings": len(self.local_cache),
                "global_mappings": len(self.global_cache),
                "total_mappings": len(self.local_cache) + len(self.global_cache),
                "storage_mode": "local_memory_fallback"
            }
            
        try:
            # Count elements inside Redis hashes
            table_mappings = 0
            for key in self.redis_client.keys("mapping:*"):
                table_mappings += self.redis_client.hlen(key)
                
            global_mappings = 0
            for key in self.redis_client.keys("global:*"):
                global_mappings += self.redis_client.hlen(key)
            
            return {
                "table_mappings": table_mappings,
                "global_mappings": global_mappings,
                "total_mappings": table_mappings + global_mappings,
                "storage_mode": "redis_hash_vault"
            }
        except Exception as e:
            print(f"Error getting mapping stats: {e}")
            return {
                "table_mappings": len(self.local_cache),
                "global_mappings": len(self.global_cache),
                "total_mappings": len(self.local_cache) + len(self.global_cache),
                "storage_mode": "error_fallback_local"
            }
    
    def close(self):
        """Close Redis connection."""
        if self.redis_client:
            self.redis_client.close()
            print("Redis connection closed")


if __name__ == "__main__":
    # Test Redis mapping system
    print("=" * 60)
    print("TESTING REDIS MAPPING SYSTEM (STEP 9 - RESILIENT HASH VAULT)")
    print("=" * 60)
    
    mapping_system = RedisMappingSystem()
    
    # Test basic mapping
    mapping_system.set_mapping("employees", "customer_id", 123, "cust_abc123")
    result = mapping_system.get_mapping("employees", "customer_id", 123)
    print(f"Basic Hashed mapping test: {result}")
    
    # Test global mapping (cross-table consistency)
    mapping_system.set_global_mapping("customer_id", 123, "cust_xyz789")
    result = mapping_system.get_global_mapping("customer_id", 123)
    print(f"Global Hashed mapping test: {result}")
    
    # Test encryption
    mapping_system.set_mapping("employees", "aadhaar", "452188349021", "XXXXXX349021")
    result = mapping_system.get_mapping("employees", "aadhaar", "452188349021")
    print(f"Encrypted Hashed mapping test: {result}")
    
    # Get stats
    stats = mapping_system.get_mapping_stats()
    print(f"Mapping stats: {stats}")
    
    mapping_system.close()
    print("=" * 60)
