import pymysql
import os
from dotenv import load_dotenv

load_dotenv()

conn = pymysql.connect(
    host=os.getenv('MYSQL_HOST'),
    port=int(os.getenv('MYSQL_PORT')),
    user=os.getenv('MYSQL_USERNAME'),
    password=os.getenv('MYSQL_PASSWORD'),
    database=os.getenv('MYSQL_DATABASE'),
    ssl={'ssl_mode': 'PREFERRED'}
)

cursor = conn.cursor()

# Check global read_only status
cursor.execute('SELECT @@global.read_only')
global_read_only = cursor.fetchone()[0]

# Check session read_only status
cursor.execute('SELECT @@read_only')
session_read_only = cursor.fetchone()[0]

print(f'@@global.read_only: {global_read_only}')
print(f'@@read_only: {session_read_only}')

cursor.close()
conn.close()
