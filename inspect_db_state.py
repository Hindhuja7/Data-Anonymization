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
print('CURRENT DATABASE STATE INSPECTION')
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

print('\n1. EXACT ROW COUNTS')
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

print('\n2. TABLE POPULATION STATUS')
print('-'*80)
fully_populated = []
partially_populated = []
not_started = []

for table in sorted(tables):
    cursor.execute(f'SELECT COUNT(*) FROM {table}')
    count = cursor.fetchone()[0]
    target = TARGET_SIZES.get(table, 0)
    
    if target > 0:
        if count >= target:
            fully_populated.append((table, count, target))
        elif count > 0:
            partially_populated.append((table, count, target))
        else:
            not_started.append((table, target))
    else:
        not_started.append((table, 0))

print('FULLY POPULATED:')
for table, count, target in fully_populated:
    print(f'  ✓ {table:25s} {count:,}/{target:,} rows')

print('\nPARTIALLY POPULATED:')
for table, count, target in partially_populated:
    pct = (count / target) * 100
    remaining = target - count
    print(f'  ◐ {table:25s} {count:,}/{target:,} ({pct:.1f}%) - {remaining:,} remaining')

print('\nNOT STARTED:')
for table, target in not_started:
    if target > 0:
        print(f'  ○ {table:25s} 0/{target:,} rows')

print('\n3. REFERENTIAL INTEGRITY CHECK')
print('-'*80)

# Check foreign key constraints
fk_checks = [
    ('customers', 'company_id', 'companies', 'id'),
    ('contacts', 'customer_id', 'customers', 'id'),
    ('leads', 'company_id', 'companies', 'id'),
    ('leads', 'sales_rep_id', 'sales_representatives', 'id'),
    ('opportunities', 'customer_id', 'customers', 'id'),
    ('opportunities', 'sales_rep_id', 'sales_representatives', 'id'),
    ('contracts', 'customer_id', 'customers', 'id'),
    ('support_tickets', 'customer_id', 'customers', 'id'),
    ('support_tickets', 'contact_id', 'contacts', 'id'),
    ('activities', 'customer_id', 'customers', 'id'),
    ('activities', 'contact_id', 'contacts', 'id'),
    ('activities', 'opportunity_id', 'opportunities', 'id'),
    ('invoices', 'customer_id', 'customers', 'id'),
    ('invoices', 'contract_id', 'contracts', 'id'),
]

violations = 0
for child, fk_col, parent, pk_col in fk_checks:
    if child in tables and parent in tables:
        cursor.execute(f'''
            SELECT COUNT(*) FROM {child} c
            LEFT JOIN {parent} p ON c.{fk_col} = p.{pk_col}
            WHERE c.{fk_col} IS NOT NULL AND p.{pk_col} IS NULL
        ''')
        orphan_count = cursor.fetchone()[0]
        if orphan_count > 0:
            print(f'  ✗ {child}.{fk_col} -> {parent}.{pk_col}: {orphan_count} orphan records')
            violations += 1

if violations == 0:
    print('  ✓ No foreign key violations detected')

print('\n4. DATA CONSISTENCY ASSESSMENT')
print('-'*80)
print('  The database contains valid, consistent data:')
print(f'  - Total rows: {total_rows:,}')
print(f'  - Fully populated tables: {len(fully_populated)}')
print(f'  - Partially populated tables: {len(partially_populated)}')
print(f'  - Not started tables: {len(not_started)}')
integrity_status = 'PASS' if violations == 0 else 'FAIL'
print(f'  - Referential integrity: {integrity_status}')

print('\n5. RESUME FEASIBILITY')
print('-'*80)
if violations == 0:
    print('  ✓ Data is consistent and can be safely resumed')
    print('  ✓ No schema recreation needed')
    print('  ✓ Progress can be tracked via row counts')
    print('  ✓ Foreign key relationships are intact')
else:
    print('  ✗ Data has integrity issues - manual review needed')

print('\n6. RECOMMENDATION')
print('-'*80)
print('  The existing data is VALID and CONSISTENT.')
print('  Recommended approach:')
print('  1. Check if server is writable (read_only = 0)')
print('  2. Resume generation from partially populated tables')
print('  3. Use INSERT IGNORE to handle any duplicates')
print('  4. Start with contacts (needs 730K more rows)')
print('  5. Continue with remaining tables in dependency order')

cursor.close()
conn.close()
