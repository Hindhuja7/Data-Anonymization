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

# Get all tables
cursor.execute('SHOW TABLES')
tables = [row[0] for row in cursor.fetchall()]

print('='*80)
print('QUICK DATABASE STATUS')
print('='*80)

# Target sizes for comparison
TARGET_SIZES = {
    'companies': 24500,
    'sales_representatives': 4750,
    'customers': 495000,
    'contacts': 740000,
    'leads': 300000,
    'opportunities': 250000,
    'contracts': 150000,
    'support_tickets': 1000000,
    'activities': 2000000,
    'invoices': 500000
}

print('\n1. ROW COUNTS')
print('-'*80)
total_rows = 0
for table in sorted(tables):
    cursor.execute(f'SELECT COUNT(*) FROM {table}')
    count = cursor.fetchone()[0]
    target = TARGET_SIZES.get(table, 0)
    status = '✓' if count >= target else '✗' if target > 0 else '?'
    progress = f'{count}/{target}' if target > 0 else str(count)
    print(f'  {status} {table:25s} {count:>10,} rows (target: {target:,})')
    total_rows += count

print(f'\n  Total: {total_rows:,} rows')

print('\n2. TABLE COMPLETION STATUS')
print('-'*80)
complete = []
incomplete = []

for table in sorted(tables):
    cursor.execute(f'SELECT COUNT(*) FROM {table}')
    count = cursor.fetchone()[0]
    target = TARGET_SIZES.get(table, 0)
    
    if target > 0:
        if count >= target:
            complete.append((table, count, target))
        else:
            incomplete.append((table, count, target))

print('COMPLETE TABLES:')
for table, count, target in complete:
    print(f'  ✓ {table:25s} {count:,}/{target:,} rows')

print('\nINCOMPLETE TABLES:')
for table, count, target in incomplete:
    pct = (count / target) * 100
    remaining = target - count
    print(f'  ◐ {table:25s} {count:,}/{target:,} ({pct:.1f}%) - {remaining:,} remaining')

cursor.close()
conn.close()
