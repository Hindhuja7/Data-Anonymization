"""
Production-Ready Large CRM Dataset Generator with Checkpointing and Robust Error Handling
"""
import os
import random
import time
import json
from datetime import datetime, timedelta
import pymysql
from faker import Faker
from dotenv import load_dotenv

load_dotenv()

# Initialize Faker
fake = Faker()
Faker.seed(42)

# Progress tracking file
PROGRESS_FILE = "crm_generation_progress_v2.json"

# Target sizes
TARGET_SIZES = {
    'companies': 24500,
    'customers': 495000,
    'contacts': 740000,
    'sales_representatives': 4750,
    'leads': 300000,
    'opportunities': 250000,
    'contracts': 150000,
    'support_tickets': 1000000,
    'activities': 2000000,
    'invoices': 500000
}

BATCH_SIZE = 25000
CHUNK_SIZE = 10000

def get_connection():
    """Get MySQL connection with SSL"""
    return pymysql.connect(
        host=os.getenv('MYSQL_HOST'),
        port=int(os.getenv('MYSQL_PORT')),
        user=os.getenv('MYSQL_USERNAME'),
        password=os.getenv('MYSQL_PASSWORD'),
        database=os.getenv('MYSQL_DATABASE'),
        ssl={'ssl_mode': 'PREFERRED'}
    )

def check_server_writable(connection):
    """Check if the server is writable (not in read-only mode)"""
    cursor = connection.cursor()
    cursor.execute('SELECT @@read_only')
    read_only = cursor.fetchone()[0]
    cursor.close()
    return read_only == 0

def wait_for_writable_log(connection, max_wait_seconds=600, check_interval=5):
    """Wait for server to become writable with logging, extended timeout"""
    start_wait = time.time()
    
    while time.time() - start_wait < max_wait_seconds:
        if check_server_writable(connection):
            return True
        elapsed = int(time.time() - start_wait)
        print(f"  Server is read-only, waiting... ({elapsed}s elapsed, max {max_wait_seconds}s)")
        time.sleep(check_interval)
    
    return False

def load_progress():
    """Load progress from file"""
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE, 'r') as f:
            return json.load(f)
    return {
        'tables': {},
        'start_time': None,
        'last_update': None
    }

def save_progress(progress):
    """Save progress to file"""
    progress['last_update'] = datetime.now().isoformat()
    with open(PROGRESS_FILE, 'w') as f:
        json.dump(progress, f, indent=2)

def update_table_progress(progress, table_name, rows_completed, last_id=None):
    """Update progress for a specific table"""
    if 'tables' not in progress:
        progress['tables'] = {}
    
    progress['tables'][table_name] = {
        'rows_completed': rows_completed,
        'last_id': last_id,
        'timestamp': datetime.now().isoformat()
    }
    
    save_progress(progress)

def calculate_eta(start_time, total_target, completed):
    """Calculate estimated time remaining"""
    if completed == 0:
        return None
    
    elapsed = time.time() - start_time
    rate = completed / elapsed  # rows per second
    
    if rate == 0:
        return None
    
    remaining = total_target - completed
    eta_seconds = remaining / rate
    
    return eta_seconds

def format_eta(seconds):
    """Format ETA in human-readable format"""
    if seconds is None:
        return "Unknown"
    
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    
    if hours > 0:
        return f"{hours}h {minutes}m {secs}s"
    elif minutes > 0:
        return f"{minutes}m {secs}s"
    else:
        return f"{secs}s"

def generate_indian_pan():
    """Generate realistic Indian PAN number"""
    letters = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
    first_three = ''.join(random.choice(letters) for _ in range(3))
    fourth = random.choice(['A', 'B', 'C', 'F', 'G', 'H', 'L', 'J', 'P', 'T', 'K'])
    digits = ''.join(random.choice('0123456789') for _ in range(4))
    last = random.choice(letters)
    return f"{first_three}{fourth}{digits}{last}"

def generate_indian_gstin():
    """Generate realistic Indian GSTIN number"""
    state_codes = ['01', '02', '03', '04', '05', '06', '07', '08', '09', '10',
                   '11', '12', '13', '14', '15', '16', '17', '18', '19', '20',
                   '21', '22', '23', '24', '25', '26', '27', '28', '29', '30',
                   '31', '32', '33', '34', '35', '36', '37']
    state = random.choice(state_codes)
    pan_part = ''.join(random.choice('0123456789') for _ in range(10))
    entity = ''.join(random.choice('0123456789') for _ in range(3))
    check = random.choice('0123456789')
    return f"{state}{pan_part}{entity}{check}"

def generate_indian_bank_account():
    """Generate realistic Indian bank account number"""
    length = random.randint(11, 16)
    return ''.join(random.choice('0123456789') for _ in range(length))

def generate_indian_ifsc():
    """Generate realistic Indian IFSC code"""
    banks = ['SBIN', 'HDFC', 'ICIC', 'AXIS', 'KKBK', 'UBIN', 'PUNB', 'CORP', 
             'IDFB', 'DLBL', 'YESB', 'INDB', 'RATN', 'BAND', 'CNRB', 'KVBL']
    bank = random.choice(banks)
    branch = ''.join(random.choice('0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ') for _ in range(6))
    return f"{bank}0{branch}"

def generate_indian_phone():
    """Generate realistic Indian phone number"""
    first = random.choice(['6', '7', '8', '9'])
    rest = ''.join(random.choice('0123456789') for _ in range(9))
    return f"+91 {first}{rest[:4]} {rest[4:]}"

def generate_indian_address():
    """Generate realistic Indian address"""
    cities = ['Mumbai', 'Delhi', 'Bangalore', 'Chennai', 'Hyderabad', 'Pune', 
              'Ahmedabad', 'Jaipur', 'Lucknow', 'Kolkata', 'Surat', 'Kanpur',
              'Nagpur', 'Indore', 'Thane', 'Bhopal', 'Visakhapatnam', 'Pimpri']
    states = ['Maharashtra', 'Delhi', 'Karnataka', 'Tamil Nadu', 'Telangana', 
              'Gujarat', 'Rajasthan', 'Uttar Pradesh', 'West Bengal', 'Madhya Pradesh']
    
    street_num = random.randint(1, 999)
    street_name = fake.street_name()
    city = random.choice(cities)
    state = random.choice(states)
    postal = str(random.randint(100000, 999999))
    
    return f"{street_num}, {street_name}, {city}, {state} - {postal}"

def generate_companies(count, start_id=1):
    """Generate companies with Indian PII"""
    print(f"\nGenerating {count} companies...")
    
    industries = ['Technology', 'Healthcare', 'Finance', 'Manufacturing', 'Retail', 
                  'Education', 'Consulting', 'Energy', 'Telecommunications', 'Transportation']
    
    companies = []
    for i in range(count):
        company = {
            'name': fake.company(),
            'industry': random.choice(industries),
            'website': fake.url(),
            'phone': generate_indian_phone(),
            'address': generate_indian_address(),
            'city': fake.city(),
            'state': fake.state(),
            'postal_code': fake.zipcode(),
            'country': 'India',
            'employee_count': random.randint(10, 5000),
            'annual_revenue': round(random.uniform(100000, 100000000), 2)
        }
        companies.append(company)
        
        if (i + 1) % 10000 == 0:
            print(f"  Generated {i + 1}/{count} companies")
    
    return companies

def generate_sales_reps(count, start_id=1):
    """Generate sales representatives with Indian PII"""
    print(f"\nGenerating {count} sales representatives...")
    
    territories = ['North India', 'South India', 'East India', 'West India', 'Central India']
    
    email_generator = fake.unique
    
    sales_reps = []
    for i in range(count):
        rep = {
            'first_name': fake.first_name(),
            'last_name': fake.last_name(),
            'email': email_generator.email(),
            'phone': generate_indian_phone(),
            'hire_date': fake.date_between(start_date='-5y', end_date='today'),
            'territory': random.choice(territories),
            'commission_rate': round(random.uniform(0.05, 0.15), 4),
            'target_quota': round(random.uniform(50000, 500000), 2)
        }
        sales_reps.append(rep)
        
        if (i + 1) % 10000 == 0:
            print(f"  Generated {i + 1}/{count} sales representatives")
    
    fake.unique.clear()
    
    return sales_reps

def generate_customers(count, company_ids, start_id=1):
    """Generate customers with Indian PII"""
    print(f"\nGenerating {count} customers...")
    
    account_types = ['prospect', 'active', 'inactive', 'churned']
    
    customers = []
    for i in range(count):
        customer = {
            'company_id': random.choice(company_ids) if company_ids else None,
            'account_name': fake.company(),
            'account_number': fake.uuid4()[:8].upper(),
            'industry': fake.job(),
            'customer_since': fake.date_between(start_date='-3y', end_date='today'),
            'account_type': random.choice(account_types),
            'annual_revenue': round(random.uniform(10000, 5000000), 2),
            'employee_count': random.randint(5, 1000),
            'billing_address': generate_indian_address(),
            'billing_city': fake.city(),
            'billing_state': fake.state(),
            'billing_postal_code': fake.zipcode(),
            'billing_country': 'India',
            'shipping_address': generate_indian_address(),
            'shipping_city': fake.city(),
            'shipping_state': fake.state(),
            'shipping_postal_code': fake.zipcode(),
            'shipping_country': 'India'
        }
        customers.append(customer)
        
        if (i + 1) % 10000 == 0:
            print(f"  Generated {i + 1}/{count} customers")
    
    return customers

def generate_contacts(count, customer_ids, start_id=1):
    """Generate contacts with Indian PII"""
    print(f"\nGenerating {count} contacts...")
    
    departments = ['Sales', 'Marketing', 'Finance', 'IT', 'Operations', 'HR', 'Executive']
    
    contacts = []
    for i in range(count):
        contact = {
            'customer_id': random.choice(customer_ids),
            'first_name': fake.first_name(),
            'last_name': fake.last_name(),
            'title': fake.job(),
            'email': fake.email(),
            'phone': generate_indian_phone(),
            'mobile': generate_indian_phone(),
            'department': random.choice(departments),
            'is_primary': (i % 5 == 0)
        }
        contacts.append(contact)
        
        if (i + 1) % 10000 == 0:
            print(f"  Generated {i + 1}/{count} contacts")
    
    return contacts

def generate_leads(count, company_ids, sales_rep_ids, start_id=1):
    """Generate leads with Indian PII"""
    print(f"\nGenerating {count} leads...")
    
    lead_sources = ['website', 'referral', 'cold_call', 'trade_show', 'social_media', 'email_campaign', 'other']
    lead_statuses = ['new', 'contacted', 'qualified', 'lost', 'converted']
    
    leads = []
    for i in range(count):
        lead = {
            'company_id': random.choice(company_ids) if company_ids else None,
            'sales_rep_id': random.choice(sales_rep_ids) if sales_rep_ids else None,
            'first_name': fake.first_name(),
            'last_name': fake.last_name(),
            'email': fake.email(),
            'phone': generate_indian_phone(),
            'company_name': fake.company(),
            'title': fake.job(),
            'industry': fake.job(),
            'lead_source': random.choice(lead_sources),
            'lead_status': random.choice(lead_statuses),
            'lead_score': random.randint(0, 100),
            'estimated_value': round(random.uniform(1000, 100000), 2),
            'notes': fake.paragraph()
        }
        leads.append(lead)
        
        if (i + 1) % 10000 == 0:
            print(f"  Generated {i + 1}/{count} leads")
    
    return leads

def generate_opportunities(count, customer_ids, sales_rep_ids, lead_ids, start_id=1):
    """Generate opportunities"""
    print(f"\nGenerating {count} opportunities...")
    
    stages = ['prospecting', 'qualification', 'needs_analysis', 'value_proposition', 
              'negotiation', 'closed_won', 'closed_lost']
    
    opportunities = []
    for i in range(count):
        stage = random.choice(stages)
        probability = {
            'prospecting': 10, 'qualification': 25, 'needs_analysis': 40,
            'value_proposition': 60, 'negotiation': 80, 'closed_won': 100, 'closed_lost': 0
        }[stage]
        
        opportunity = {
            'customer_id': random.choice(customer_ids),
            'sales_rep_id': random.choice(sales_rep_ids) if sales_rep_ids else None,
            'lead_id': random.choice(lead_ids) if lead_ids else None,
            'opportunity_name': f"Opportunity - {fake.company()} - {fake.job()}",
            'opportunity_stage': stage,
            'amount': round(random.uniform(5000, 500000), 2),
            'probability': probability,
            'expected_close_date': fake.date_between(start_date='+1m', end_date='+1y'),
            'actual_close_date': fake.date_between(start_date='-1y', end_date='today') if stage in ['closed_won', 'closed_lost'] else None,
            'description': fake.paragraph()
        }
        opportunities.append(opportunity)
        
        if (i + 1) % 10000 == 0:
            print(f"  Generated {i + 1}/{count} opportunities")
    
    return opportunities

def generate_contracts(count, customer_ids, opportunity_ids, start_id=1):
    """Generate contracts"""
    print(f"\nGenerating {count} contracts...")
    
    contract_types = ['service', 'product', 'subscription', 'maintenance', 'consulting']
    billing_frequencies = ['monthly', 'quarterly', 'annually', 'one_time']
    statuses = ['draft', 'active', 'expired', 'terminated', 'renewed']
    
    contracts = []
    for i in range(count):
        start_date = fake.date_between(start_date='-2y', end_date='today')
        contract = {
            'customer_id': random.choice(customer_ids),
            'opportunity_id': random.choice(opportunity_ids) if opportunity_ids else None,
            'contract_number': f"CTR-{fake.uuid4()[:8].upper()}",
            'contract_type': random.choice(contract_types),
            'start_date': start_date,
            'end_date': start_date + timedelta(days=random.randint(365, 1825)),
            'contract_value': round(random.uniform(10000, 500000), 2),
            'billing_frequency': random.choice(billing_frequencies),
            'status': random.choice(statuses),
            'terms': fake.paragraph()
        }
        contracts.append(contract)
        
        if (i + 1) % 10000 == 0:
            print(f"  Generated {i + 1}/{count} contracts")
    
    return contracts

def generate_support_tickets(count, customer_ids, contact_ids, contract_ids, sales_rep_ids, start_id=1):
    """Generate support tickets"""
    print(f"\nGenerating {count} support tickets...")
    
    priorities = ['low', 'medium', 'high', 'critical']
    statuses = ['open', 'in_progress', 'pending_customer', 'resolved', 'closed']
    categories = ['technical', 'billing', 'feature_request', 'bug', 'other']
    
    tickets = []
    for i in range(count):
        status = random.choice(statuses)
        created_at = fake.date_time_between(start_date='-6m', end_date='now')
        
        ticket = {
            'customer_id': random.choice(customer_ids),
            'contact_id': random.choice(contact_ids) if contact_ids else None,
            'contract_id': random.choice(contract_ids) if contract_ids else None,
            'ticket_number': f"TKT-{fake.uuid4()[:8].upper()}",
            'subject': f"Support Request - {fake.job()}",
            'description': fake.paragraph(),
            'priority': random.choice(priorities),
            'status': status,
            'category': random.choice(categories),
            'assigned_to': random.choice(sales_rep_ids) if sales_rep_ids else None,
            'resolved_at': created_at + timedelta(days=random.randint(1, 30)) if status in ['resolved', 'closed'] else None
        }
        tickets.append(ticket)
        
        if (i + 1) % 10000 == 0:
            print(f"  Generated {i + 1}/{count} support tickets")
    
    return tickets

def generate_activities(count, customer_ids, contact_ids, opportunity_ids, lead_ids, sales_rep_ids, start_id=1):
    """Generate activities"""
    print(f"\nGenerating {count} activities...")
    
    activity_types = ['call', 'email', 'meeting', 'note', 'task', 'demo', 'follow_up']
    statuses = ['scheduled', 'completed', 'cancelled', 'in_progress']
    
    activities = []
    for i in range(count):
        status = random.choice(statuses)
        due_date = fake.date_time_between(start_date='-1m', end_date='+1m')
        
        activity = {
            'customer_id': random.choice(customer_ids) if customer_ids else None,
            'contact_id': random.choice(contact_ids) if contact_ids else None,
            'opportunity_id': random.choice(opportunity_ids) if opportunity_ids else None,
            'lead_id': random.choice(lead_ids) if lead_ids else None,
            'sales_rep_id': random.choice(sales_rep_ids),
            'activity_type': random.choice(activity_types),
            'subject': f"{random.choice(activity_types).title()} - {fake.job()}",
            'description': fake.paragraph(),
            'status': status,
            'due_date': due_date,
            'completed_at': due_date if status == 'completed' else None,
            'duration_minutes': random.randint(15, 120) if status == 'completed' else None
        }
        activities.append(activity)
        
        if (i + 1) % 10000 == 0:
            print(f"  Generated {i + 1}/{count} activities")
    
    return activities

def generate_invoices(count, customer_ids, contract_ids, start_id=1):
    """Generate invoices"""
    print(f"\nGenerating {count} invoices...")
    
    statuses = ['draft', 'sent', 'paid', 'overdue', 'cancelled']
    payment_methods = ['credit_card', 'bank_transfer', 'check', 'paypal', 'wire', 'upi', 'net_banking']
    
    invoices = []
    for i in range(count):
        invoice_date = fake.date_between(start_date='-6m', end_date='today')
        amount = round(random.uniform(1000, 50000), 2)
        tax_amount = round(amount * 0.18, 2)  # 18% GST
        
        status = random.choice(statuses)
        payment_date = invoice_date + timedelta(days=random.randint(1, 60)) if status == 'paid' else None
        
        invoice = {
            'customer_id': random.choice(customer_ids),
            'contract_id': random.choice(contract_ids) if contract_ids else None,
            'invoice_number': f"INV-{fake.uuid4()[:8].upper()}",
            'invoice_date': invoice_date,
            'due_date': invoice_date + timedelta(days=30),
            'amount': amount,
            'tax_amount': tax_amount,
            'total_amount': amount + tax_amount,
            'status': status,
            'payment_method': random.choice(payment_methods) if status == 'paid' else None,
            'payment_date': payment_date,
            'notes': fake.sentence()
        }
        invoices.append(invoice)
        
        if (i + 1) % 10000 == 0:
            print(f"  Generated {i + 1}/{count} invoices")
    
    return invoices

def insert_batch_with_retry(cursor, table_name, columns, data, batch_size=BATCH_SIZE, 
                           connection=None, progress=None, table_name_for_progress=None,
                           start_time=None, total_target=0):
    """Insert data in batches with exponential backoff retry logic and checkpointing"""
    if not data:
        return 0
    
    placeholders = ', '.join(['%s'] * len(columns))
    columns_str = ', '.join(columns)
    sql = f"INSERT IGNORE INTO {table_name} ({columns_str}) VALUES ({placeholders})"
    
    total_inserted = 0
    for i in range(0, len(data), batch_size):
        batch = data[i:i + batch_size]
        batch_values = [tuple(row[col] for col in columns) for row in batch]
        
        # Check server status before each batch
        if connection and not check_server_writable(connection):
            print(f"  Server is read-only, waiting for writable state...")
            if not wait_for_writable_log(connection, max_wait_seconds=600):
                print(f"  ERROR: Server remained read-only after 600 seconds")
                raise Exception("Server is read-only and cannot proceed")
        
        # Retry with exponential backoff
        max_retries = 5
        base_delay = 1  # seconds
        
        for attempt in range(max_retries):
            try:
                cursor.executemany(sql, batch_values)
                total_inserted += len(batch)
                
                # Progress logging with ETA
                if total_inserted % 10000 == 0 or total_inserted == len(data):
                    pct = (total_inserted / len(data)) * 100
                    print(f"    Inserted {total_inserted}/{len(data)} rows into {table_name} ({pct:.1f}%)")
                    
                    if start_time and total_target > 0:
                        eta = calculate_eta(start_time, total_target, total_inserted)
                        if eta:
                            eta_str = format_eta(eta)
                            print(f"    ETA: {eta_str}")
                
                # Commit after each batch
                if connection:
                    connection.commit()
                
                # Save checkpoint after each batch
                if progress and table_name_for_progress:
                    update_table_progress(progress, table_name_for_progress, total_inserted)
                
                # Small delay between batches to reduce server load
                time.sleep(0.1)
                
                # Success - break out of retry loop
                break
                
            except pymysql.err.OperationalError as e:
                if e.args[0] == 1290:  # read-only error
                    print(f"  Read-only error detected (attempt {attempt + 1}/{max_retries})")
                    if connection and wait_for_writable_log(connection, max_wait_seconds=600):
                        continue  # Retry
                    else:
                        print(f"  ERROR: Server remained read-only after 600 seconds")
                        raise
                        
                elif e.args[0] == 1213:  # deadlock error
                    if attempt < max_retries - 1:
                        # Rollback the failed batch
                        connection.rollback()
                        
                        # Exponential backoff
                        delay = base_delay * (2 ** attempt)
                        print(f"  Deadlock detected (attempt {attempt + 1}/{max_retries}), retrying after {delay}s...")
                        time.sleep(delay)
                        continue  # Retry
                    else:
                        print(f"  ERROR: Max retries ({max_retries}) exceeded for deadlock")
                        raise
                else:
                    raise
    
    return total_inserted

def get_current_counts(connection):
    """Get current row counts for all tables"""
    cursor = connection.cursor()
    
    cursor.execute("SHOW TABLES")
    tables = [table[0] for table in cursor.fetchall()]
    
    counts = {}
    for table in tables:
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        counts[table] = cursor.fetchone()[0]
    
    cursor.close()
    return counts

def main():
    """Main generation process with checkpointing and robust error handling"""
    print("=" * 80)
    print("PRODUCTION-READY CRM DATASET GENERATOR")
    print("=" * 80)
    
    # Load existing progress
    progress = load_progress()
    
    # Initialize start time if not set
    if progress.get('start_time') is None:
        progress['start_time'] = datetime.now().isoformat()
        save_progress(progress)
    
    start_time = datetime.fromisoformat(progress['start_time']).timestamp()
    
    print(f"\nStart time: {progress['start_time']}")
    if progress.get('last_update'):
        print(f"Last update: {progress['last_update']}")
    
    print(f"\nProgress file: {PROGRESS_FILE}")
    print("Mode: Resume from checkpoint (never clears existing data)")
    
    connection = get_connection()
    cursor = connection.cursor()
    
    # Get current counts
    current_counts = get_current_counts(connection)
    
    print(f"\nCurrent database state:")
    total_current = 0
    total_target = sum(TARGET_SIZES.values())
    
    for table in sorted(TARGET_SIZES.keys()):
        current = current_counts.get(table, 0)
        target = TARGET_SIZES[table]
        status = "✓" if current >= target else "◐"
        pct = (current / target) * 100 if target > 0 else 0
        print(f"  {status} {table:25s} {current:>10,} / {target:<10,} ({pct:>5.1f}%)")
        total_current += current
    
    print(f"\nTotal: {total_current:,} / {total_target:,} rows ({(total_current/total_target)*100:.1f}%)")
    
    # Calculate overall ETA
    eta = calculate_eta(start_time, total_target, total_current)
    if eta:
        print(f"Overall ETA: {format_eta(eta)}")
    
    # Generate in dependency order
    print("\n" + "=" * 80)
    print("GENERATING DATA (skipping completed tables)")
    print("=" * 80)
    
    # 1. Companies
    target = TARGET_SIZES['companies']
    current = current_counts.get('companies', 0)
    
    if current >= target:
        print(f"✓ Companies already complete ({current:,}/{target:,})")
        company_ids = list(range(1, current + 1))
    else:
        remaining = target - current
        print(f"\nGenerating {remaining:,} companies (current: {current:,})")
        companies = generate_companies(remaining, start_id=current + 1)
        inserted = insert_batch_with_retry(
            cursor, 'companies',
            ['name', 'industry', 'website', 'phone', 'address', 'city', 'state',
             'postal_code', 'country', 'employee_count', 'annual_revenue'],
            companies, connection=connection, progress=progress, 
            table_name_for_progress='companies', start_time=start_time, 
            total_target=total_target
        )
        print(f"✓ Inserted {inserted} companies")
        update_table_progress(progress, 'companies', target)
        company_ids = list(range(1, target + 1))
    
    # 2. Sales Representatives
    target = TARGET_SIZES['sales_representatives']
    current = current_counts.get('sales_representatives', 0)
    
    if current >= target:
        print(f"✓ Sales representatives already complete ({current:,}/{target:,})")
        sales_rep_ids = list(range(1, current + 1))
    else:
        remaining = target - current
        print(f"\nGenerating {remaining:,} sales representatives (current: {current:,})")
        sales_reps = generate_sales_reps(remaining, start_id=current + 1)
        inserted = insert_batch_with_retry(
            cursor, 'sales_representatives',
            ['first_name', 'last_name', 'email', 'phone', 'hire_date', 'territory',
             'commission_rate', 'target_quota'],
            sales_reps, connection=connection, progress=progress,
            table_name_for_progress='sales_representatives', start_time=start_time,
            total_target=total_target
        )
        print(f"✓ Inserted {inserted} sales representatives")
        update_table_progress(progress, 'sales_representatives', target)
        sales_rep_ids = list(range(1, target + 1))
    
    # 3. Customers (chunked)
    target = TARGET_SIZES['customers']
    current = current_counts.get('customers', 0)
    
    if current >= target:
        print(f"✓ Customers already complete ({current:,}/{target:,})")
        customer_ids = list(range(1, current + 1))
    else:
        remaining = target - current
        print(f"\nGenerating {remaining:,} customers (current: {current:,})")
        total_inserted = 0
        
        for chunk_start in range(0, remaining, CHUNK_SIZE):
            chunk_end = min(chunk_start + CHUNK_SIZE, remaining)
            chunk_count = chunk_end - chunk_start
            chunk_start_id = current + chunk_start + 1
            
            customers = generate_customers(chunk_count, company_ids, start_id=chunk_start_id)
            inserted = insert_batch_with_retry(
                cursor, 'customers',
                ['company_id', 'account_name', 'account_number', 'industry', 'customer_since',
                 'account_type', 'annual_revenue', 'employee_count', 'billing_address',
                 'billing_city', 'billing_state', 'billing_postal_code', 'billing_country',
                 'shipping_address', 'shipping_city', 'shipping_state', 'shipping_postal_code',
                 'shipping_country'],
                customers, connection=connection, progress=progress,
                table_name_for_progress='customers', start_time=start_time,
                total_target=total_target
            )
            total_inserted += inserted
            print(f"  Progress: {total_inserted}/{remaining} customers inserted")
        
        print(f"✓ Inserted {total_inserted} customers")
        update_table_progress(progress, 'customers', target)
        customer_ids = list(range(1, target + 1))
    
    # 4. Contacts (chunked)
    target = TARGET_SIZES['contacts']
    current = current_counts.get('contacts', 0)
    
    if current >= target:
        print(f"✓ Contacts already complete ({current:,}/{target:,})")
        contact_ids = list(range(1, current + 1))
    else:
        remaining = target - current
        print(f"\nGenerating {remaining:,} contacts (current: {current:,})")
        total_inserted = 0
        
        for chunk_start in range(0, remaining, CHUNK_SIZE):
            chunk_end = min(chunk_start + CHUNK_SIZE, remaining)
            chunk_count = chunk_end - chunk_start
            chunk_start_id = current + chunk_start + 1
            
            contacts = generate_contacts(chunk_count, customer_ids, start_id=chunk_start_id)
            inserted = insert_batch_with_retry(
                cursor, 'contacts',
                ['customer_id', 'first_name', 'last_name', 'title', 'email', 'phone',
                 'mobile', 'department', 'is_primary'],
                contacts, connection=connection, progress=progress,
                table_name_for_progress='contacts', start_time=start_time,
                total_target=total_target
            )
            total_inserted += inserted
            print(f"  Progress: {total_inserted}/{remaining} contacts inserted")
        
        print(f"✓ Inserted {total_inserted} contacts")
        update_table_progress(progress, 'contacts', target)
        contact_ids = list(range(1, target + 1))
    
    # 5. Leads (chunked)
    target = TARGET_SIZES['leads']
    current = current_counts.get('leads', 0)
    
    if current >= target:
        print(f"✓ Leads already complete ({current:,}/{target:,})")
        lead_ids = list(range(1, current + 1))
    else:
        remaining = target - current
        print(f"\nGenerating {remaining:,} leads (current: {current:,})")
        total_inserted = 0
        
        for chunk_start in range(0, remaining, CHUNK_SIZE):
            chunk_end = min(chunk_start + CHUNK_SIZE, remaining)
            chunk_count = chunk_end - chunk_start
            chunk_start_id = current + chunk_start + 1
            
            leads = generate_leads(chunk_count, company_ids, sales_rep_ids, start_id=chunk_start_id)
            inserted = insert_batch_with_retry(
                cursor, 'leads',
                ['company_id', 'sales_rep_id', 'first_name', 'last_name', 'email', 'phone',
                 'company_name', 'title', 'industry', 'lead_source', 'lead_status',
                 'lead_score', 'estimated_value', 'notes'],
                leads, connection=connection, progress=progress,
                table_name_for_progress='leads', start_time=start_time,
                total_target=total_target
            )
            total_inserted += inserted
            print(f"  Progress: {total_inserted}/{remaining} leads inserted")
        
        print(f"✓ Inserted {total_inserted} leads")
        update_table_progress(progress, 'leads', target)
        lead_ids = list(range(1, target + 1))
    
    # 6. Opportunities (chunked)
    target = TARGET_SIZES['opportunities']
    current = current_counts.get('opportunities', 0)
    
    if current >= target:
        print(f"✓ Opportunities already complete ({current:,}/{target:,})")
        opportunity_ids = list(range(1, current + 1))
    else:
        remaining = target - current
        print(f"\nGenerating {remaining:,} opportunities (current: {current:,})")
        total_inserted = 0
        
        for chunk_start in range(0, remaining, CHUNK_SIZE):
            chunk_end = min(chunk_start + CHUNK_SIZE, remaining)
            chunk_count = chunk_end - chunk_start
            chunk_start_id = current + chunk_start + 1
            
            opportunities = generate_opportunities(chunk_count, customer_ids, sales_rep_ids, lead_ids, start_id=chunk_start_id)
            inserted = insert_batch_with_retry(
                cursor, 'opportunities',
                ['customer_id', 'sales_rep_id', 'lead_id', 'opportunity_name', 'opportunity_stage',
                 'amount', 'probability', 'expected_close_date', 'actual_close_date', 'description'],
                opportunities, connection=connection, progress=progress,
                table_name_for_progress='opportunities', start_time=start_time,
                total_target=total_target
            )
            total_inserted += inserted
            print(f"  Progress: {total_inserted}/{remaining} opportunities inserted")
        
        print(f"✓ Inserted {total_inserted} opportunities")
        update_table_progress(progress, 'opportunities', target)
        opportunity_ids = list(range(1, target + 1))
    
    # 7. Contracts (chunked)
    target = TARGET_SIZES['contracts']
    current = current_counts.get('contracts', 0)
    
    if current >= target:
        print(f"✓ Contracts already complete ({current:,}/{target:,})")
        contract_ids = list(range(1, current + 1))
    else:
        remaining = target - current
        print(f"\nGenerating {remaining:,} contracts (current: {current:,})")
        total_inserted = 0
        
        for chunk_start in range(0, remaining, CHUNK_SIZE):
            chunk_end = min(chunk_start + CHUNK_SIZE, remaining)
            chunk_count = chunk_end - chunk_start
            chunk_start_id = current + chunk_start + 1
            
            contracts = generate_contracts(chunk_count, customer_ids, opportunity_ids, start_id=chunk_start_id)
            inserted = insert_batch_with_retry(
                cursor, 'contracts',
                ['customer_id', 'opportunity_id', 'contract_number', 'contract_type', 'start_date',
                 'end_date', 'contract_value', 'billing_frequency', 'status', 'terms'],
                contracts, connection=connection, progress=progress,
                table_name_for_progress='contracts', start_time=start_time,
                total_target=total_target
            )
            total_inserted += inserted
            print(f"  Progress: {total_inserted}/{remaining} contracts inserted")
        
        print(f"✓ Inserted {total_inserted} contracts")
        update_table_progress(progress, 'contracts', target)
        contract_ids = list(range(1, target + 1))
    
    # 8. Support Tickets (chunked)
    target = TARGET_SIZES['support_tickets']
    current = current_counts.get('support_tickets', 0)
    
    if current >= target:
        print(f"✓ Support tickets already complete ({current:,}/{target:,})")
    else:
        remaining = target - current
        print(f"\nGenerating {remaining:,} support tickets (current: {current:,})")
        total_inserted = 0
        
        for chunk_start in range(0, remaining, CHUNK_SIZE):
            chunk_end = min(chunk_start + CHUNK_SIZE, remaining)
            chunk_count = chunk_end - chunk_start
            chunk_start_id = current + chunk_start + 1
            
            support_tickets = generate_support_tickets(chunk_count, customer_ids, contact_ids, contract_ids, sales_rep_ids, start_id=chunk_start_id)
            inserted = insert_batch_with_retry(
                cursor, 'support_tickets',
                ['customer_id', 'contact_id', 'contract_id', 'ticket_number', 'subject',
                 'description', 'priority', 'status', 'category', 'assigned_to', 'resolved_at'],
                support_tickets, connection=connection, progress=progress,
                table_name_for_progress='support_tickets', start_time=start_time,
                total_target=total_target
            )
            total_inserted += inserted
            print(f"  Progress: {total_inserted}/{remaining} support tickets inserted")
        
        print(f"✓ Inserted {total_inserted} support tickets")
        update_table_progress(progress, 'support_tickets', target)
    
    # 9. Activities (chunked)
    target = TARGET_SIZES['activities']
    current = current_counts.get('activities', 0)
    
    if current >= target:
        print(f"✓ Activities already complete ({current:,}/{target:,})")
    else:
        remaining = target - current
        print(f"\nGenerating {remaining:,} activities (current: {current:,})")
        total_inserted = 0
        
        for chunk_start in range(0, remaining, CHUNK_SIZE):
            chunk_end = min(chunk_start + CHUNK_SIZE, remaining)
            chunk_count = chunk_end - chunk_start
            chunk_start_id = current + chunk_start + 1
            
            activities = generate_activities(chunk_count, customer_ids, contact_ids, opportunity_ids, lead_ids, sales_rep_ids, start_id=chunk_start_id)
            inserted = insert_batch_with_retry(
                cursor, 'activities',
                ['customer_id', 'contact_id', 'opportunity_id', 'lead_id', 'sales_rep_id',
                 'activity_type', 'subject', 'description', 'status', 'due_date',
                 'completed_at', 'duration_minutes'],
                activities, connection=connection, progress=progress,
                table_name_for_progress='activities', start_time=start_time,
                total_target=total_target
            )
            total_inserted += inserted
            print(f"  Progress: {total_inserted}/{remaining} activities inserted")
        
        print(f"✓ Inserted {total_inserted} activities")
        update_table_progress(progress, 'activities', target)
    
    # 10. Invoices (chunked)
    target = TARGET_SIZES['invoices']
    current = current_counts.get('invoices', 0)
    
    if current >= target:
        print(f"✓ Invoices already complete ({current:,}/{target:,})")
    else:
        remaining = target - current
        print(f"\nGenerating {remaining:,} invoices (current: {current:,})")
        total_inserted = 0
        
        for chunk_start in range(0, remaining, CHUNK_SIZE):
            chunk_end = min(chunk_start + CHUNK_SIZE, remaining)
            chunk_count = chunk_end - chunk_start
            chunk_start_id = current + chunk_start + 1
            
            invoices = generate_invoices(chunk_count, customer_ids, contract_ids, start_id=chunk_start_id)
            inserted = insert_batch_with_retry(
                cursor, 'invoices',
                ['customer_id', 'contract_id', 'invoice_number', 'invoice_date', 'due_date',
                 'amount', 'tax_amount', 'total_amount', 'status', 'payment_method',
                 'payment_date', 'notes'],
                invoices, connection=connection, progress=progress,
                table_name_for_progress='invoices', start_time=start_time,
                total_target=total_target
            )
            total_inserted += inserted
            print(f"  Progress: {total_inserted}/{remaining} invoices inserted")
        
        print(f"✓ Inserted {total_inserted} invoices")
        update_table_progress(progress, 'invoices', target)
    
    cursor.close()
    connection.close()
    
    # Final report
    elapsed_time = time.time() - start_time
    
    print("\n" + "=" * 80)
    print("GENERATION COMPLETED")
    print("=" * 80)
    print(f"Total elapsed time: {elapsed_time:.2f} seconds ({elapsed_time/60:.2f} minutes)")
    
    # Clean up progress file
    if os.path.exists(PROGRESS_FILE):
        os.remove(PROGRESS_FILE)
        print(f"Removed progress file: {PROGRESS_FILE}")
    
    print("\n" + "=" * 80)
    print("DATASET GENERATION: COMPLETED SUCCESSFULLY")
    print("=" * 80)
    
    return True

if __name__ == "__main__":
    try:
        success = main()
        exit(0 if success else 1)
    except Exception as e:
        print(f"\n✗ Error during generation: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
