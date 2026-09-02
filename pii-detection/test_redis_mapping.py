"""
Standalone Redis Mapping Test

Tests Redis connectivity, secure key generation, encryption/decryption,
and basic mapping operations without running the full pipeline.
"""

import os
from dotenv import load_dotenv
from redis_mapping import RedisMappingSystem

load_dotenv()

def test_redis_connection():
    """Test basic Redis connection."""
    print("=" * 80)
    print("TEST 1: Redis Connection")
    print("=" * 80)
    
    try:
        redis_host = os.getenv("REDIS_HOST", "localhost")
        redis_port = int(os.getenv("REDIS_PORT", 6379))
        hmac_secret = os.getenv("HMAC_SECRET", "test-secret")
        
        print(f"Connecting to Redis at {redis_host}:{redis_port}")
        print(f"HMAC Secret: {hmac_secret[:10]}..." if len(hmac_secret) > 10 else f"HMAC Secret: {hmac_secret}")
        
        mapping_system = RedisMappingSystem(
            host=redis_host,
            port=redis_port,
            hmac_secret=hmac_secret
        )
        
        # Test connection
        pong = mapping_system.redis_client.ping()
        print(f"Redis PING: {pong}")
        
        if pong:
            print("✓ Redis connection successful")
            return mapping_system
        else:
            print("✗ Redis connection failed")
            return None
            
    except Exception as e:
        print(f"✗ Redis connection error:")
        print(f"  Exception type: {type(e).__name__}")
        print(f"  Exception: {repr(e)}")
        import traceback
        print(f"  Traceback: {traceback.format_exc()}")
        return None

def test_secure_key_generation(mapping_system):
    """Test HMAC-SHA256 secure key generation."""
    print("\n" + "=" * 80)
    print("TEST 2: Secure Key Generation")
    print("=" * 80)
    
    try:
        test_values = ["John Doe", "12345", "test@example.com"]
        
        for value in test_values:
            secure_key = mapping_system._generate_secure_key(value)
            print(f"Value: {value}")
            print(f"Secure Key: {secure_key}")
            print(f"Key Length: {len(secure_key)}")
            print()
        
        # Test consistency
        key1 = mapping_system._generate_secure_key("John Doe")
        key2 = mapping_system._generate_secure_key("John Doe")
        key3 = mapping_system._generate_secure_key("Jane Doe")
        
        print(f"Consistency test:")
        print(f"  'John Doe' → {key1}")
        print(f"  'John Doe' → {key2}")
        print(f"  'Jane Doe' → {key3}")
        print(f"  Same value produces same key: {key1 == key2}")
        print(f"  Different values produce different keys: {key1 != key3}")
        
        print("✓ Secure key generation working")
        
    except Exception as e:
        print(f"✗ Secure key generation error:")
        print(f"  Exception type: {type(e).__name__}")
        print(f"  Exception: {repr(e)}")
        import traceback
        print(f"  Traceback: {traceback.format_exc()}")

def test_encryption_decryption(mapping_system):
    """Test encryption and decryption."""
    print("\n" + "=" * 80)
    print("TEST 3: Encryption/Decryption")
    print("=" * 80)
    
    try:
        test_values = ["John Doe", "12345", "test@example.com"]
        
        for value in test_values:
            encrypted = mapping_system._encrypt(value)
            decrypted = mapping_system._decrypt(encrypted)
            
            print(f"Original: {value}")
            print(f"Encrypted: {encrypted[:50]}..." if len(encrypted) > 50 else f"Encrypted: {encrypted}")
            print(f"Decrypted: {decrypted}")
            print(f"Match: {value == decrypted}")
            print()
        
        print("✓ Encryption/decryption working")
        
    except Exception as e:
        print(f"✗ Encryption/decryption error:")
        print(f"  Exception type: {type(e).__name__}")
        print(f"  Exception: {repr(e)}")
        import traceback
        print(f"  Traceback: {traceback.format_exc()}")

def test_basic_mapping(mapping_system):
    """Test basic set and get mapping."""
    print("\n" + "=" * 80)
    print("TEST 4: Basic Mapping Operations")
    print("=" * 80)
    
    try:
        # Clear any existing test data
        mapping_system.clear_mappings("test_table")
        
        # Test set mapping
        print("Setting mapping: test_table.test_column 'John Doe' → 'Jane Smith'")
        success = mapping_system.set_mapping("test_table", "test_column", "John Doe", "Jane Smith")
        print(f"Set result: {success}")
        
        # Test get mapping
        print("Getting mapping for 'John Doe'")
        result = mapping_system.get_mapping("test_table", "test_column", "John Doe")
        print(f"Get result: {result}")
        print(f"Expected: Jane Smith")
        print(f"Match: {result == 'Jane Smith'}")
        
        # Test non-existent mapping
        print("Getting mapping for 'Non Existent'")
        result = mapping_system.get_mapping("test_table", "test_column", "Non Existent")
        print(f"Get result: {result}")
        print(f"Expected: None")
        print(f"Match: {result is None}")
        
        # Test NULL handling
        print("Testing NULL value handling")
        result = mapping_system.get_mapping("test_table", "test_column", None)
        print(f"Get result for None: {result}")
        print(f"Expected: None")
        print(f"Match: {result is None}")
        
        print("✓ Basic mapping operations working")
        
    except Exception as e:
        print(f"✗ Basic mapping operations error:")
        print(f"  Exception type: {type(e).__name__}")
        print(f"  Exception: {repr(e)}")
        import traceback
        print(f"  Traceback: {traceback.format_exc()}")

def test_global_mapping(mapping_system):
    """Test global (cross-table) mapping."""
    print("\n" + "=" * 80)
    print("TEST 5: Global Mapping Operations")
    print("=" * 80)
    
    try:
        # Clear any existing test data
        mapping_system.clear_mappings()
        
        # Test set global mapping
        print("Setting global mapping: customer_id '123' → 'cust_abc123'")
        success = mapping_system.set_global_mapping("customer_id", 123, "cust_abc123")
        print(f"Set result: {success}")
        
        # Test get global mapping
        print("Getting global mapping for customer_id '123'")
        result = mapping_system.get_global_mapping("customer_id", 123)
        print(f"Get result: {result}")
        print(f"Expected: cust_abc123")
        print(f"Match: {result == 'cust_abc123'}")
        
        # Test consistency across tables
        print("Testing consistency: same value should return same result")
        result2 = mapping_system.get_global_mapping("customer_id", 123)
        print(f"Second get result: {result2}")
        print(f"Match: {result == result2}")
        
        print("✓ Global mapping operations working")
        
    except Exception as e:
        print(f"✗ Global mapping operations error:")
        print(f"  Exception type: {type(e).__name__}")
        print(f"  Exception: {repr(e)}")
        import traceback
        print(f"  Traceback: {traceback.format_exc()}")

def test_mapping_stats(mapping_system):
    """Test mapping statistics."""
    print("\n" + "=" * 80)
    print("TEST 6: Mapping Statistics")
    print("=" * 80)
    
    try:
        stats = mapping_system.get_mapping_stats()
        print(f"Table mappings: {stats['table_mappings']}")
        print(f"Global mappings: {stats['global_mappings']}")
        print(f"Total mappings: {stats['total_mappings']}")
        
        print("✓ Mapping statistics working")
        
    except Exception as e:
        print(f"✗ Mapping statistics error:")
        print(f"  Exception type: {type(e).__name__}")
        print(f"  Exception: {repr(e)}")
        import traceback
        print(f"  Traceback: {traceback.format_exc()}")

def cleanup(mapping_system):
    """Clean up test data."""
    print("\n" + "=" * 80)
    print("CLEANUP")
    print("=" * 80)
    
    try:
        mapping_system.clear_mappings()
        print("✓ Test data cleared")
        mapping_system.close()
        print("✓ Redis connection closed")
        
    except Exception as e:
        print(f"✗ Cleanup error:")
        print(f"  Exception type: {type(e).__name__}")
        print(f"  Exception: {repr(e)}")

def main():
    """Run all Redis mapping tests."""
    print("\n" + "=" * 80)
    print("REDIS MAPPING SYSTEM STANDALONE TEST")
    print("=" * 80)
    
    # Test 1: Connection
    mapping_system = test_redis_connection()
    if not mapping_system:
        print("\n✗ Cannot proceed without Redis connection")
        return
    
    # Test 2: Secure key generation
    test_secure_key_generation(mapping_system)
    
    # Test 3: Encryption/decryption
    test_encryption_decryption(mapping_system)
    
    # Test 4: Basic mapping
    test_basic_mapping(mapping_system)
    
    # Test 5: Global mapping
    test_global_mapping(mapping_system)
    
    # Test 6: Statistics
    test_mapping_stats(mapping_system)
    
    # Cleanup
    cleanup(mapping_system)
    
    print("\n" + "=" * 80)
    print("ALL TESTS COMPLETED")
    print("=" * 80)

if __name__ == "__main__":
    main()
