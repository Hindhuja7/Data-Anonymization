"""
Stage 1: Generate Large CRM Dataset in Stages with Indian-Specific PII
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
PROGRESS_FILE = "crm_generation_progress.json"

# Target sizes
TARGET_SIZES = {
    'companies': 25000,
    'customers': 500000,
    'contacts': 750000,
    'sales_representatives': 5000,
    'leads': 300000,
    'opportunities': 250000,
    'contracts': 150000,
    'support_tickets': 1000000,
    'activities': 2000000,
    'invoices': 500000
}

# Stage 1 target (100K total records)
STAGE1_TARGETS = {
    'companies': 500,
    'customers': 5000,
    'contacts': 10000,
    'sales_representatives': 250,
    'leads': 5000,
    'opportunities': 4000,
    'contracts': 3000,
    'support_tickets': 20000,
    'activities': 40000,
    'invoices': 10000
}

BATCH_SIZE = 25000

def get_connection():
    """Get MySQL connection with SSL"""
    # Use default SSL configuration - PyMySQL will handle SSL automatically
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

def wait_for_writable(connection, max_wait_seconds=300, check_interval=5):
    """Wait for server to become writable, with timeout"""
    import time as time_module
    start_wait = time_module.time()
    
    while time_module.time() - start_wait < max_wait_seconds:
        if check_server_writable(connection):
            return True
        print(f"  Server is read-only, waiting {check_interval}s...")
        time_module.sleep(check_interval)
    
    return False

def load_progress():
    """Load progress from file"""
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_progress(progress):
    """Save progress to file"""
    with open(PROGRESS_FILE, 'w') as f:
        json.dump(progress, f, indent=2)

def generate_indian_pan():
    """Generate realistic Indian PAN number"""
    # Format: 5 letters + 4 digits + 1 letter
    letters = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
    first_three = ''.join(random.choice(letters) for _ in range(3))
    fourth = random.choice(['A', 'B', 'C', 'F', 'G', 'H', 'L', 'J', 'P', 'T', 'K'])
    digits = ''.join(random.choice('0123456789') for _ in range(4))
    last = random.choice(letters)
    return f"{first_three}{fourth}{digits}{last}"

def generate_indian_gstin():
    """Generate realistic Indian GSTIN number"""
    # Format: 2-digit state code + 10-digit PAN + 3-digit entity number + 1 check digit
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
    # Typically 11-16 digits
    length = random.randint(11, 16)
    return ''.join(random.choice('0123456789') for _ in range(length))

def generate_indian_ifsc():
    """Generate realistic Indian IFSC code"""
    # Format: 4 letters (bank code) + 0 + 6 alphanumeric (branch code)
    banks = ['SBIN', 'HDFC', 'ICIC', 'AXIS', 'KKBK', 'UBIN', 'PUNB', 'CORP', 
             'IDFB', 'DLBL', 'YESB', 'INDB', 'RATN', 'BAND', 'CNRB', 'KVBL']
    bank = random.choice(banks)
    branch = ''.join(random.choice('0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ') for _ in range(6))
    return f"{bank}0{branch}"

def generate_indian_phone():
    """Generate realistic Indian phone number"""
    # Format: +91 XXXXX XXXXX
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

def clear_test_data():
    """Clear existing test data"""
    print("=" * 80)
    print("CLEARING EXISTING TEST DATA")
    print("=" * 80)
    
    connection = get_connection()
    cursor = connection.cursor()
    
    # Disable foreign key checks temporarily
    cursor.execute("SET FOREIGN_KEY_CHECKS = 0")
    
    # Drop tables in reverse order of dependencies
    drop_order = [
        'invoices', 'activities', 'support_tickets', 'contracts',
        'opportunities', 'leads', 'contacts', 'customers',
        'sales_representatives', 'companies'
    ]
    
    for table in drop_order:
        cursor.execute(f"TRUNCATE TABLE {table}")
        print(f"✓ Cleared {table}")
    
    # Re-enable foreign key checks
    cursor.execute("SET FOREIGN_KEY_CHECKS = 1")
    
    connection.commit()
    cursor.close()
    connection.close()
    
    print("\n✓ All test data cleared")

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
    
    # Use unique email generation
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
    
    # Reset unique generator
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

def insert_batch(cursor, table_name, columns, data, batch_size=BATCH_SIZE, connection=None, commit_after_batch=False):
    """Insert data in batches with progress tracking using INSERT IGNORE to handle duplicates"""
    if not data:
        return 0
    
    placeholders = ', '.join(['%s'] * len(columns))
    columns_str = ', '.join(columns)
    sql = f"INSERT IGNORE INTO {table_name} ({columns_str}) VALUES ({placeholders})"
    
    total_inserted = 0
    for i in range(0, len(data), batch_size):
        # Check server status before each batch
        if connection and not check_server_writable(connection):
            print(f"  Server is read-only, waiting...")
            if not wait_for_writable(connection, max_wait_seconds=60):
                print(f"  ERROR: Server remained read-only after 60 seconds")
                raise Exception("Server is read-only and cannot proceed")
        
        batch = data[i:i + batch_size]
        batch_values = [tuple(row[col] for col in columns) for row in batch]
        
        try:
            cursor.executemany(sql, batch_values)
            total_inserted += len(batch)
            
            if total_inserted % 10000 == 0:
                print(f"    Inserted {total_inserted}/{len(data)} rows into {table_name}")
            
            # Commit after each batch if requested (for better recovery)
            if commit_after_batch and connection:
                connection.commit()
            
            # Add small delay between batches to reduce server load
            time.sleep(0.1)
            
        except pymysql.err.OperationalError as e:
            if e.args[0] == 1290:  # read-only error
                print(f"  Read-only error detected, waiting for server to become writable...")
                if connection and wait_for_writable(connection, max_wait_seconds=60):
                    # Retry the batch
                    cursor.executemany(sql, batch_values)
                    total_inserted += len(batch)
                    if total_inserted % 10000 == 0:
                        print(f"    Inserted {total_inserted}/{len(data)} rows into {table_name}")
                    if commit_after_batch and connection:
                        connection.commit()
                else:
                    print(f"  ERROR: Server remained read-only after 60 seconds")
                    raise
            elif e.args[0] == 1213:  # deadlock error
                print(f"  Deadlock detected, retrying batch after short delay...")
                time.sleep(1)  # Wait before retry
                # Retry the batch
                cursor.executemany(sql, batch_values)
                total_inserted += len(batch)
                if total_inserted % 10000 == 0:
                    print(f"    Inserted {total_inserted}/{len(data)} rows into {table_name}")
                if commit_after_batch and connection:
                    connection.commit()
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

def verify_integrity(connection):
    """Verify referential integrity"""
    cursor = connection.cursor()
    
    checks = [
        ("customers.company_id", "SELECT COUNT(*) FROM customers WHERE company_id IS NOT NULL AND company_id NOT IN (SELECT id FROM companies)"),
        ("contacts.customer_id", "SELECT COUNT(*) FROM contacts WHERE customer_id NOT IN (SELECT id FROM customers)"),
        ("leads.company_id", "SELECT COUNT(*) FROM leads WHERE company_id IS NOT NULL AND company_id NOT IN (SELECT id FROM companies)"),
        ("leads.sales_rep_id", "SELECT COUNT(*) FROM leads WHERE sales_rep_id IS NOT NULL AND sales_rep_id NOT IN (SELECT id FROM sales_representatives)"),
        ("opportunities.customer_id", "SELECT COUNT(*) FROM opportunities WHERE customer_id NOT IN (SELECT id FROM customers)"),
        ("opportunities.sales_rep_id", "SELECT COUNT(*) FROM opportunities WHERE sales_rep_id IS NOT NULL AND sales_rep_id NOT IN (SELECT id FROM sales_representatives)"),
        ("opportunities.lead_id", "SELECT COUNT(*) FROM opportunities WHERE lead_id IS NOT NULL AND lead_id NOT IN (SELECT id FROM leads)"),
        ("contracts.customer_id", "SELECT COUNT(*) FROM contracts WHERE customer_id NOT IN (SELECT id FROM customers)"),
        ("contracts.opportunity_id", "SELECT COUNT(*) FROM contracts WHERE opportunity_id IS NOT NULL AND opportunity_id NOT IN (SELECT id FROM opportunities)"),
        ("support_tickets.customer_id", "SELECT COUNT(*) FROM support_tickets WHERE customer_id NOT IN (SELECT id FROM customers)"),
        ("support_tickets.contact_id", "SELECT COUNT(*) FROM support_tickets WHERE contact_id IS NOT NULL AND contact_id NOT IN (SELECT id FROM contacts)"),
        ("support_tickets.contract_id", "SELECT COUNT(*) FROM support_tickets WHERE contract_id IS NOT NULL AND contract_id NOT IN (SELECT id FROM contracts)"),
        ("support_tickets.assigned_to", "SELECT COUNT(*) FROM support_tickets WHERE assigned_to IS NOT NULL AND assigned_to NOT IN (SELECT id FROM sales_representatives)"),
        ("activities.customer_id", "SELECT COUNT(*) FROM activities WHERE customer_id IS NOT NULL AND customer_id NOT IN (SELECT id FROM customers)"),
        ("activities.contact_id", "SELECT COUNT(*) FROM activities WHERE contact_id IS NOT NULL AND contact_id NOT IN (SELECT id FROM contacts)"),
        ("activities.opportunity_id", "SELECT COUNT(*) FROM activities WHERE opportunity_id IS NOT NULL AND opportunity_id NOT IN (SELECT id FROM opportunities)"),
        ("activities.lead_id", "SELECT COUNT(*) FROM activities WHERE lead_id IS NOT NULL AND lead_id NOT IN (SELECT id FROM leads)"),
        ("activities.sales_rep_id", "SELECT COUNT(*) FROM activities WHERE sales_rep_id NOT IN (SELECT id FROM sales_representatives)"),
        ("invoices.customer_id", "SELECT COUNT(*) FROM invoices WHERE customer_id NOT IN (SELECT id FROM customers)"),
        ("invoices.contract_id", "SELECT COUNT(*) FROM invoices WHERE contract_id IS NOT NULL AND contract_id NOT IN (SELECT id FROM contracts)"),
    ]
    
    total_violations = 0
    for check_name, query in checks:
        cursor.execute(query)
        violations = cursor.fetchone()[0]
        total_violations += violations
    
    cursor.close()
    return total_violations

def get_storage_stats(connection):
    """Get storage statistics"""
    cursor = connection.cursor()
    
    cursor.execute("""
        SELECT table_name, table_rows, ROUND(((data_length + index_length) / 1024 / 1024), 2) AS size_mb
        FROM information_schema.TABLES
        WHERE table_schema = %s
        ORDER BY table_name
    """, (os.getenv('MYSQL_DATABASE'),))
    
    stats = cursor.fetchall()
    cursor.close()
    
    total_mb = sum(row[2] for row in stats)
    total_rows = sum(row[1] for row in stats)
    
    return stats, total_rows, total_mb

def generate_stage(targets, stage_name):
    """Generate a specific stage of data"""
    print("=" * 80)
    print(f"GENERATING {stage_name}")
    print("=" * 80)
    
    start_time = time.time()
    
    connection = get_connection()
    cursor = connection.cursor()
    
    # Get current counts to resume if interrupted
    current_counts = get_current_counts(connection)
    progress = load_progress()
    
    print(f"\nCurrent counts:")
    for table, count in current_counts.items():
        print(f"  {table}: {count:,}")
    
    # Generate in dependency order
    print("\n" + "=" * 80)
    print("GENERATING DATA")
    print("=" * 80)
    
    # 1. Companies
    target = targets['companies']
    current = current_counts.get('companies', 0)
    remaining = target - current
    
    if remaining > 0:
        companies = generate_companies(remaining, start_id=current + 1)
        inserted = insert_batch(cursor, 'companies',
                               ['name', 'industry', 'website', 'phone', 'address', 'city', 'state',
                                'postal_code', 'country', 'employee_count', 'annual_revenue'],
                               companies, connection=connection, commit_after_batch=True)
        connection.commit()
        print(f"✓ Inserted {inserted} companies")
        company_ids = list(range(1, target + 1))
    else:
        print(f"✓ Companies already at target ({current:,})")
        company_ids = list(range(1, current + 1))
    
    # 2. Sales Representatives
    target = targets['sales_representatives']
    current = current_counts.get('sales_representatives', 0)
    remaining = target - current
    
    if remaining > 0:
        sales_reps = generate_sales_reps(remaining, start_id=current + 1)
        inserted = insert_batch(cursor, 'sales_representatives',
                               ['first_name', 'last_name', 'email', 'phone', 'hire_date', 'territory',
                                'commission_rate', 'target_quota'],
                               sales_reps, connection=connection, commit_after_batch=True)
        connection.commit()
        print(f"✓ Inserted {inserted} sales representatives")
        sales_rep_ids = list(range(1, target + 1))
    else:
        print(f"✓ Sales representatives already at target ({current:,})")
        sales_rep_ids = list(range(1, current + 1))
    
    # 3. Customers (chunked generation for large tables)
    target = targets['customers']
    current = current_counts.get('customers', 0)
    remaining = target - current
    
    if remaining > 0:
        chunk_size = 10000  # Generate and insert in chunks
        total_inserted = 0
        for chunk_start in range(0, remaining, chunk_size):
            chunk_end = min(chunk_start + chunk_size, remaining)
            chunk_count = chunk_end - chunk_start
            chunk_start_id = current + chunk_start + 1
            
            customers = generate_customers(chunk_count, company_ids, start_id=chunk_start_id)
            inserted = insert_batch(cursor, 'customers',
                                   ['company_id', 'account_name', 'account_number', 'industry', 'customer_since',
                                    'account_type', 'annual_revenue', 'employee_count', 'billing_address',
                                    'billing_city', 'billing_state', 'billing_postal_code', 'billing_country',
                                    'shipping_address', 'shipping_city', 'shipping_state', 'shipping_postal_code',
                                    'shipping_country'],
                                   customers, connection=connection, commit_after_batch=True)
            connection.commit()
            total_inserted += inserted
            print(f"  Progress: {total_inserted}/{remaining} customers inserted")
        
        print(f"✓ Inserted {total_inserted} customers")
        customer_ids = list(range(1, target + 1))
    else:
        print(f"✓ Customers already at target ({current:,})")
        customer_ids = list(range(1, current + 1))
    
    # 4. Contacts (chunked generation for large tables)
    target = targets['contacts']
    current = current_counts.get('contacts', 0)
    remaining = target - current
    
    if remaining > 0:
        chunk_size = 10000  # Generate and insert in chunks
        total_inserted = 0
        for chunk_start in range(0, remaining, chunk_size):
            chunk_end = min(chunk_start + chunk_size, remaining)
            chunk_count = chunk_end - chunk_start
            chunk_start_id = current + chunk_start + 1
            
            contacts = generate_contacts(chunk_count, customer_ids, start_id=chunk_start_id)
            inserted = insert_batch(cursor, 'contacts',
                                   ['customer_id', 'first_name', 'last_name', 'title', 'email', 'phone',
                                    'mobile', 'department', 'is_primary'],
                                   contacts, connection=connection, commit_after_batch=True)
            connection.commit()
            total_inserted += inserted
            print(f"  Progress: {total_inserted}/{remaining} contacts inserted")
        
        print(f"✓ Inserted {total_inserted} contacts")
        contact_ids = list(range(1, target + 1))
    else:
        print(f"✓ Contacts already at target ({current:,})")
        contact_ids = list(range(1, current + 1))
    
    # 5. Leads (chunked generation for large tables)
    target = targets['leads']
    current = current_counts.get('leads', 0)
    remaining = target - current
    
    if remaining > 0:
        chunk_size = 10000  # Generate and insert in chunks
        total_inserted = 0
        for chunk_start in range(0, remaining, chunk_size):
            chunk_end = min(chunk_start + chunk_size, remaining)
            chunk_count = chunk_end - chunk_start
            chunk_start_id = current + chunk_start + 1
            
            leads = generate_leads(chunk_count, company_ids, sales_rep_ids, start_id=chunk_start_id)
            inserted = insert_batch(cursor, 'leads',
                                   ['company_id', 'sales_rep_id', 'first_name', 'last_name', 'email', 'phone',
                                    'company_name', 'title', 'industry', 'lead_source', 'lead_status',
                                    'lead_score', 'estimated_value', 'notes'],
                                   leads, connection=connection, commit_after_batch=True)
            connection.commit()
            total_inserted += inserted
            print(f"  Progress: {total_inserted}/{remaining} leads inserted")
        
        print(f"✓ Inserted {total_inserted} leads")
        lead_ids = list(range(1, target + 1))
    else:
        print(f"✓ Leads already at target ({current:,})")
        lead_ids = list(range(1, current + 1))
    
    # 6. Opportunities (chunked generation for large tables)
    target = targets['opportunities']
    current = current_counts.get('opportunities', 0)
    remaining = target - current
    
    if remaining > 0:
        chunk_size = 10000  # Generate and insert in chunks
        total_inserted = 0
        for chunk_start in range(0, remaining, chunk_size):
            chunk_end = min(chunk_start + chunk_size, remaining)
            chunk_count = chunk_end - chunk_start
            chunk_start_id = current + chunk_start + 1
            
            opportunities = generate_opportunities(chunk_count, customer_ids, sales_rep_ids, lead_ids, start_id=chunk_start_id)
            inserted = insert_batch(cursor, 'opportunities',
                                   ['customer_id', 'sales_rep_id', 'lead_id', 'opportunity_name', 'opportunity_stage',
                                    'amount', 'probability', 'expected_close_date', 'actual_close_date', 'description'],
                                   opportunities, connection=connection, commit_after_batch=True)
            connection.commit()
            total_inserted += inserted
            print(f"  Progress: {total_inserted}/{remaining} opportunities inserted")
        
        print(f"✓ Inserted {total_inserted} opportunities")
        opportunity_ids = list(range(1, target + 1))
    else:
        print(f"✓ Opportunities already at target ({current:,})")
        opportunity_ids = list(range(1, current + 1))
    
    # 7. Contracts (chunked generation for large tables)
    target = targets['contracts']
    current = current_counts.get('contracts', 0)
    remaining = target - current
    
    if remaining > 0:
        chunk_size = 10000  # Generate and insert in chunks
        total_inserted = 0
        for chunk_start in range(0, remaining, chunk_size):
            chunk_end = min(chunk_start + chunk_size, remaining)
            chunk_count = chunk_end - chunk_start
            chunk_start_id = current + chunk_start + 1
            
            contracts = generate_contracts(chunk_count, customer_ids, opportunity_ids, start_id=chunk_start_id)
            inserted = insert_batch(cursor, 'contracts',
                                   ['customer_id', 'opportunity_id', 'contract_number', 'contract_type', 'start_date',
                                    'end_date', 'contract_value', 'billing_frequency', 'status', 'terms'],
                                   contracts, connection=connection, commit_after_batch=True)
            connection.commit()
            total_inserted += inserted
            print(f"  Progress: {total_inserted}/{remaining} contracts inserted")
        
        print(f"✓ Inserted {total_inserted} contracts")
        contract_ids = list(range(1, target + 1))
    else:
        print(f"✓ Contracts already at target ({current:,})")
        contract_ids = list(range(1, current + 1))
    
    # 8. Support Tickets (chunked generation for large tables)
    target = targets['support_tickets']
    current = current_counts.get('support_tickets', 0)
    remaining = target - current
    
    if remaining > 0:
        chunk_size = 10000  # Generate and insert in chunks
        total_inserted = 0
        for chunk_start in range(0, remaining, chunk_size):
            chunk_end = min(chunk_start + chunk_size, remaining)
            chunk_count = chunk_end - chunk_start
            chunk_start_id = current + chunk_start + 1
            
            support_tickets = generate_support_tickets(chunk_count, customer_ids, contact_ids, contract_ids, sales_rep_ids, start_id=chunk_start_id)
            inserted = insert_batch(cursor, 'support_tickets',
                                   ['customer_id', 'contact_id', 'contract_id', 'ticket_number', 'subject',
                                    'description', 'priority', 'status', 'category', 'assigned_to', 'resolved_at'],
                                   support_tickets, connection=connection, commit_after_batch=True)
            connection.commit()
            total_inserted += inserted
            print(f"  Progress: {total_inserted}/{remaining} support tickets inserted")
        
        print(f"✓ Inserted {total_inserted} support tickets")
    else:
        print(f"✓ Support tickets already at target ({current:,})")
    
    # 9. Activities (chunked generation for large tables)
    target = targets['activities']
    current = current_counts.get('activities', 0)
    remaining = target - current
    
    if remaining > 0:
        chunk_size = 10000  # Generate and insert in chunks
        total_inserted = 0
        for chunk_start in range(0, remaining, chunk_size):
            chunk_end = min(chunk_start + chunk_size, remaining)
            chunk_count = chunk_end - chunk_start
            chunk_start_id = current + chunk_start + 1
            
            activities = generate_activities(chunk_count, customer_ids, contact_ids, opportunity_ids, lead_ids, sales_rep_ids, start_id=chunk_start_id)
            inserted = insert_batch(cursor, 'activities',
                                   ['customer_id', 'contact_id', 'opportunity_id', 'lead_id', 'sales_rep_id',
                                    'activity_type', 'subject', 'description', 'status', 'due_date',
                                    'completed_at', 'duration_minutes'],
                                   activities, connection=connection, commit_after_batch=True)
            connection.commit()
            total_inserted += inserted
            print(f"  Progress: {total_inserted}/{remaining} activities inserted")
        
        print(f"✓ Inserted {total_inserted} activities")
    else:
        print(f"✓ Activities already at target ({current:,})")
    
    # 10. Invoices (chunked generation for large tables)
    target = targets['invoices']
    current = current_counts.get('invoices', 0)
    remaining = target - current
    
    if remaining > 0:
        chunk_size = 10000  # Generate and insert in chunks
        total_inserted = 0
        for chunk_start in range(0, remaining, chunk_size):
            chunk_end = min(chunk_start + chunk_size, remaining)
            chunk_count = chunk_end - chunk_start
            chunk_start_id = current + chunk_start + 1
            
            invoices = generate_invoices(chunk_count, customer_ids, contract_ids, start_id=chunk_start_id)
            inserted = insert_batch(cursor, 'invoices',
                                   ['customer_id', 'contract_id', 'invoice_number', 'invoice_date', 'due_date',
                                    'amount', 'tax_amount', 'total_amount', 'status', 'payment_method',
                                    'payment_date', 'notes'],
                                   invoices, connection=connection, commit_after_batch=True)
            connection.commit()
            total_inserted += inserted
            print(f"  Progress: {total_inserted}/{remaining} invoices inserted")
        
        print(f"✓ Inserted {total_inserted} invoices")
    else:
        print(f"✓ Invoices already at target ({current:,})")
    
    cursor.close()
    connection.close()
    
    elapsed_time = time.time() - start_time
    
    print("\n" + "=" * 80)
    print(f"{stage_name} COMPLETED")
    print("=" * 80)
    print(f"Elapsed time: {elapsed_time:.2f} seconds ({elapsed_time/60:.2f} minutes)")
    
    return elapsed_time

def verify_stage(stage_name):
    """Verify a stage of data"""
    print("\n" + "=" * 80)
    print(f"VERIFYING {stage_name}")
    print("=" * 80)
    
    connection = get_connection()
    
    # Row counts
    print("\nRow Counts:")
    counts = get_current_counts(connection)
    total_rows = sum(counts.values())
    for table, count in counts.items():
        print(f"  {table:25} {count:10,}")
    print(f"\nTotal: {total_rows:,} rows")
    
    # Referential integrity
    print("\nReferential Integrity:")
    violations = verify_integrity(connection)
    print(f"  Total violations: {violations}")
    if violations == 0:
        print("  ✓ All foreign key constraints satisfied")
    else:
        print("  ✗ Foreign key violations found")
    
    # Storage
    print("\nStorage Usage:")
    stats, total_rows, total_mb = get_storage_stats(connection)
    for table, rows, size_mb in stats:
        print(f"  {table:25} {rows:10,} rows  {size_mb:8.2f} MB")
    print(f"\nTotal: {total_rows:,} rows, {total_mb:.2f} MB ({total_mb/1024:.2f} GB)")
    
    connection.close()
    
    return violations == 0

def main():
    """Main generation process - resume from existing data"""
    print("=" * 80)
    print("LARGE CRM DATASET GENERATION - RESUME MODE")
    print("=" * 80)
    
    # Skip data clearing and Stage 1 - resume directly to full dataset
    print("\nSkipping Stage 1 and data clearing - resuming from existing data...")
    
    # Full dataset
    print("\n" + "=" * 80)
    print("FULL DATASET: 5,480,000 RECORDS")
    print("=" * 80)
    
    full_time = generate_stage(TARGET_SIZES, "FULL DATASET")
    full_success = verify_stage("FULL DATASET")
    
    if not full_success:
        print("\n✗ Full dataset failed verification.")
        return False
    
    # Final report
    print("\n" + "=" * 80)
    print("FINAL REPORT")
    print("=" * 80)
    
    connection = get_connection()
    
    print("\n1. Final Row Counts:")
    counts = get_current_counts(connection)
    total_rows = sum(counts.values())
    for table, count in counts.items():
        target = TARGET_SIZES.get(table, 0)
        status = "✓" if count == target else "✗"
        print(f"  {status} {table:25} {count:10,} (target: {target:,})")
    print(f"\nTotal: {total_rows:,} rows (target: {sum(TARGET_SIZES.values()):,})")
    
    print("\n2. Storage Used:")
    stats, total_rows, total_mb = get_storage_stats(connection)
    for table, rows, size_mb in stats:
        print(f"  {table:25} {rows:10,} rows  {size_mb:8.2f} MB")
    print(f"\nTotal: {total_rows:,} rows, {total_mb:.2f} MB ({total_mb/1024:.2f} GB)")
    
    print(f"\n3. Total Execution Time:")
    print(f"  Stage 1: {stage1_time:.2f} seconds ({stage1_time/60:.2f} minutes)")
    print(f"  Full dataset: {full_time:.2f} seconds ({full_time/60:.2f} minutes)")
    print(f"  Total: {stage1_time + full_time:.2f} seconds ({(stage1_time + full_time)/60:.2f} minutes)")
    
    print("\n4. Referential Integrity Report:")
    violations = verify_integrity(connection)
    if violations == 0:
        print("  ✓ All 20 foreign key constraints satisfied")
        print("  ✓ 0 orphan records")
    else:
        print(f"  ✗ {violations} foreign key violations found")
    
    connection.close()
    
    print("\n5. Pipeline Readiness:")
    print("  ✓ Dataset contains realistic enterprise CRM data")
    print("  ✓ Indian-specific PII included (phone numbers, addresses)")
    print("  ✓ Multiple related tables for referential integrity testing")
    print("  ✓ Large-scale dataset suitable for performance testing")
    print("  ✓ Ready for Enterprise Data Privacy Anonymization Pipeline testing")
    
    # Clean up progress file
    if os.path.exists(PROGRESS_FILE):
        os.remove(PROGRESS_FILE)
    
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
