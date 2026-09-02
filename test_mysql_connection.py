"""
Step 1: Test MySQL Connection with SSL
"""
import os
import pymysql
from dotenv import load_dotenv

load_dotenv()

def test_mysql_connection():
    """Test connection to Aiven MySQL database with SSL"""
    
    print("=" * 60)
    print("STEP 1: Testing MySQL Connection with SSL")
    print("=" * 60)
    
    try:
        # Load credentials from .env
        host = os.getenv('MYSQL_HOST')
        port = int(os.getenv('MYSQL_PORT'))
        username = os.getenv('MYSQL_USERNAME')
        password = os.getenv('MYSQL_PASSWORD')
        database = os.getenv('MYSQL_DATABASE')
        ssl_mode = os.getenv('MYSQL_SSL_MODE')
        
        print(f"\nConnection Details:")
        print(f"  Host: {host}")
        print(f"  Port: {port}")
        print(f"  Username: {username}")
        print(f"  Database: {database}")
        print(f"  SSL Mode: {ssl_mode}")
        
        # SSL configuration for Aiven MySQL
        ssl_config = {
            'ssl_ca': '/etc/ssl/certs/ca-certificates.crt',  # Linux CA bundle
            'ssl_verify_cert': True,
            'ssl_verify_identity': True
        }
        
        print(f"\nAttempting connection...")
        
        # Connect with SSL
        connection = pymysql.connect(
            host=host,
            port=port,
            user=username,
            password=password,
            database=database,
            ssl=ssl_config,
            connect_timeout=10
        )
        
        print("✓ Connection successful!")
        print(f"✓ SSL enabled: {connection.get_server_info()}")
        
        # Test query
        cursor = connection.cursor()
        cursor.execute("SELECT VERSION()")
        version = cursor.fetchone()
        print(f"✓ MySQL Version: {version[0]}")
        
        cursor.execute("SELECT DATABASE()")
        db_name = cursor.fetchone()
        print(f"✓ Connected to database: {db_name[0]}")
        
        cursor.close()
        connection.close()
        
        print("\n" + "=" * 60)
        print("CONNECTION TEST: PASSED")
        print("=" * 60)
        return True
        
    except Exception as e:
        print(f"\n✗ Connection failed: {e}")
        print("\n" + "=" * 60)
        print("CONNECTION TEST: FAILED")
        print("=" * 60)
        return False

if __name__ == "__main__":
    success = test_mysql_connection()
    exit(0 if success else 1)
