"""
Optimized Production-Ready Large CRM Dataset Generator with Cached Data Generation
"""
import os
import random
import time
import json
from datetime import datetime, timedelta
import pymysql
from faker import Faker
from dotenv import load_dotenv
from generation_monitor import GenerationMonitor

load_dotenv()

# Initialize Faker (single instance)
fake = Faker()
Faker.seed(42)

# Progress tracking file
PROGRESS_FILE = "crm_generation_progress_v3.json"

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

# Pre-generated data pools for performance
DATA_POOLS = {
    'cities': [],
    'states': [],
    'first_names': [],
    'last_names': [],
    'company_names': [],
    'industries': [],
    'job_titles': [],
    'street_names': [],
    'departments': [],
    'territories': [],
    'lead_sources': [],
    'lead_statuses': [],
    'opportunity_stages': [],
    'contract_types': [],
    'billing_frequencies': [],
    'contract_statuses': [],
    'priorities': [],
    'ticket_statuses': [],
    'ticket_categories': [],
    'activity_types': [],
    'activity_statuses': [],
    'invoice_statuses': [],
    'payment_methods': [],
    'account_types': [],
    'ifsc_banks': []
}

def initialize_data_pools():
    """Pre-generate data pools for faster random sampling"""
    print("Initializing data pools...")
    
    # Cities (Indian)
    indian_cities = ['Mumbai', 'Delhi', 'Bangalore', 'Chennai', 'Hyderabad', 'Pune', 
                    'Ahmedabad', 'Jaipur', 'Lucknow', 'Kolkata', 'Surat', 'Kanpur',
                    'Nagpur', 'Indore', 'Thane', 'Bhopal', 'Visakhapatnam', 'Pimpri',
                    'Patna', 'Vadodara', 'Ghaziabad', 'Ludhiana', 'Agra', 'Nashik']
    DATA_POOLS['cities'] = indian_cities * 2000  # Expand pool
    
    # States (Indian)
    indian_states = ['Maharashtra', 'Delhi', 'Karnataka', 'Tamil Nadu', 'Telangana', 
                    'Gujarat', 'Rajasthan', 'Uttar Pradesh', 'West Bengal', 'Madhya Pradesh',
                    'Punjab', 'Haryana', 'Kerala', 'Bihar', 'Odisha']
    DATA_POOLS['states'] = indian_states * 3000
    
    # First names (pre-generate 50,000)
    print("  Generating first names...")
    DATA_POOLS['first_names'] = [fake.first_name() for _ in range(50000)]
    
    # Last names (pre-generate 50,000)
    print("  Generating last names...")
    DATA_POOLS['last_names'] = [fake.last_name() for _ in range(50000)]
    
    # Company names (pre-generate 50,000)
    print("  Generating company names...")
    DATA_POOLS['company_names'] = [fake.company() for _ in range(50000)]
    
    # Industries
    industries = ['Technology', 'Healthcare', 'Finance', 'Manufacturing', 'Retail', 
                  'Education', 'Consulting', 'Energy', 'Telecommunications', 'Transportation',
                  'Real Estate', 'Construction', 'Agriculture', 'Pharmaceuticals', 'Media']
    DATA_POOLS['industries'] = industries * 3000
    
    # Job titles (pre-generate 50,000)
    print("  Generating job titles...")
    DATA_POOLS['job_titles'] = [fake.job() for _ in range(50000)]
    
    # Street names (pre-generate 50,000)
    print("  Generating street names...")
    DATA_POOLS['street_names'] = [fake.street_name() for _ in range(50000)]
    
    # Departments
    departments = ['Sales', 'Marketing', 'Finance', 'IT', 'Operations', 'HR', 'Executive', 'Legal', 'R&D']
    DATA_POOLS['departments'] = departments * 5000
    
    # Territories
    territories = ['North India', 'South India', 'East India', 'West India', 'Central India']
    DATA_POOLS['territories'] = territories * 10000
    
    # Lead sources
    lead_sources = ['website', 'referral', 'cold_call', 'trade_show', 'social_media', 'email_campaign', 'other']
    DATA_POOLS['lead_sources'] = lead_sources * 7000
    
    # Lead statuses
    lead_statuses = ['new', 'contacted', 'qualified', 'lost', 'converted']
    DATA_POOLS['lead_statuses'] = lead_statuses * 10000
    
    # Opportunity stages
    opportunity_stages = ['prospecting', 'qualification', 'needs_analysis', 'value_proposition', 
                        'negotiation', 'closed_won', 'closed_lost']
    DATA_POOLS['opportunity_stages'] = opportunity_stages * 7000
    
    # Contract types
    contract_types = ['service', 'product', 'subscription', 'maintenance', 'consulting']
    DATA_POOLS['contract_types'] = contract_types * 10000
    
    # Billing frequencies
    billing_frequencies = ['monthly', 'quarterly', 'annually', 'one_time']
    DATA_POOLS['billing_frequencies'] = billing_frequencies * 12500
    
    # Contract statuses
    contract_statuses = ['draft', 'active', 'expired', 'terminated', 'renewed']
    DATA_POOLS['contract_statuses'] = contract_statuses * 10000
    
    # Priorities
    priorities = ['low', 'medium', 'high', 'critical']
    DATA_POOLS['priorities'] = priorities * 12500
    
    # Ticket statuses
    ticket_statuses = ['open', 'in_progress', 'pending_customer', 'resolved', 'closed']
    DATA_POOLS['ticket_statuses'] = ticket_statuses * 10000
    
    # Ticket categories
    ticket_categories = ['technical', 'billing', 'feature_request', 'bug', 'other']
    DATA_POOLS['ticket_categories'] = ticket_categories * 10000
    
    # Activity types
    activity_types = ['call', 'email', 'meeting', 'note', 'task', 'demo', 'follow_up']
    DATA_POOLS['activity_types'] = activity_types * 7000
    
    # Activity statuses
    activity_statuses = ['scheduled', 'completed', 'cancelled', 'in_progress']
    DATA_POOLS['activity_statuses'] = activity_statuses * 12500
    
    # Invoice statuses
    invoice_statuses = ['draft', 'sent', 'paid', 'overdue', 'cancelled']
    DATA_POOLS['invoice_statuses'] = invoice_statuses * 10000
    
    # Payment methods
    payment_methods = ['credit_card', 'bank_transfer', 'check', 'paypal', 'wire', 'upi', 'net_banking']
    DATA_POOLS['payment_methods'] = payment_methods * 7000
    
    # Account types
    account_types = ['prospect', 'active', 'inactive', 'churned']
    DATA_POOLS['account_types'] = account_types * 12500
    
    # IFSC banks
    ifsc_banks = ['SBIN', 'HDFC', 'ICIC', 'AXIS', 'KKBK', 'UBIN', 'PUNB', 'CORP', 
                 'IDFB', 'DLBL', 'YESB', 'INDB', 'RATN', 'BAND', 'CNRB', 'KVBL']
    DATA_POOLS['ifsc_banks'] = ifsc_banks * 3000
    
    print("Data pools initialized.")

class ConnectionWrapper:
    """Wrapper for MySQL connection that allows in-place updates"""
    def __init__(self, connection):
        self.connection = connection
    
    def cursor(self):
        return self.connection.cursor()
    
    def commit(self):
        return self.connection.commit()
    
    def rollback(self):
        return self.connection.rollback()
    
    def close(self):
        return self.connection.close()
    
    def update_connection(self, new_connection):
        self.connection = new_connection

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

def ping_connection(connection):
    """Ping MySQL server to verify connection is alive"""
    try:
        cursor = connection.cursor()
        cursor.execute('SELECT 1')
        cursor.fetchone()
        cursor.close()
        return True
    except:
        return False

def reconnect_with_backoff(reconnect_intervals=[2, 5, 10, 20, 40, 60], monitor=None):
    """Reconnect to MySQL with exponential backoff, retry indefinitely"""
    attempt = 0
    while True:
        attempt += 1
        interval = reconnect_intervals[(attempt - 1) % len(reconnect_intervals)]
        
        try:
            print(f"  Attempting reconnection #{attempt} (waiting {interval}s)...")
            time.sleep(interval)
            
            new_connection = get_connection()
            
            # Verify connection with ping
            if ping_connection(new_connection):
                print(f"  ✓ Reconnection successful (attempt #{attempt})")
                if monitor:
                    monitor.record_resume()
                return new_connection
            else:
                print(f"  ✗ Reconnection failed - ping unsuccessful")
                new_connection.close()
                
        except Exception as e:
            print(f"  ✗ Reconnection failed: {e}")

def check_server_writable(connection):
    """Check if the server is writable (not in read-only mode)"""
    try:
        cursor = connection.cursor()
        cursor.execute('SELECT @@read_only')
        read_only = cursor.fetchone()[0]
        cursor.close()
        return read_only == 0
    except:
        return False

def wait_for_writable_log(connection, monitor=None):
    """Poll @@global.read_only every 5 seconds until writable, return immediately when writable"""
    attempt = 0
    while True:
        attempt += 1
        try:
            cursor = connection.cursor()
            cursor.execute('SELECT @@global.read_only')
            read_only = cursor.fetchone()[0]
            cursor.close()
            
            if read_only == 0:
                print(f"  ✓ Server is now writable (after {attempt * 5}s)")
                return True
            else:
                elapsed = attempt * 5
                print(f"  Server is read-only (polling... {elapsed}s elapsed)")
                time.sleep(5)
        except:
            # Connection lost during check
            print(f"  Connection lost during writable check")
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

# Optimized data generation functions using pre-generated pools
def generate_indian_pan():
    """Generate realistic Indian PAN number (lightweight)"""
    letters = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
    first_three = ''.join(random.choice(letters) for _ in range(3))
    fourth = random.choice(['A', 'B', 'C', 'F', 'G', 'H', 'L', 'J', 'P', 'T', 'K'])
    digits = ''.join(random.choice('0123456789') for _ in range(4))
    last = random.choice(letters)
    return f"{first_three}{fourth}{digits}{last}"

def generate_indian_gstin():
    """Generate realistic Indian GSTIN number (lightweight)"""
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
    """Generate realistic Indian bank account number (lightweight)"""
    length = random.randint(11, 16)
    return ''.join(random.choice('0123456789') for _ in range(length))

def generate_indian_ifsc():
    """Generate realistic Indian IFSC code (lightweight)"""
    bank = random.choice(DATA_POOLS['ifsc_banks'])
    branch = ''.join(random.choice('0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ') for _ in range(6))
    return f"{bank}0{branch}"

def generate_indian_phone():
    """Generate realistic Indian phone number (lightweight)"""
    first = random.choice(['6', '7', '8', '9'])
    rest = ''.join(random.choice('0123456789') for _ in range(9))
    return f"+91 {first}{rest[:4]} {rest[4:]}"

def generate_indian_address():
    """Generate realistic Indian address (using pools)"""
    street_num = random.randint(1, 999)
    street_name = random.choice(DATA_POOLS['street_names'])
    city = random.choice(DATA_POOLS['cities'])
    state = random.choice(DATA_POOLS['states'])
    postal = str(random.randint(100000, 999999))
    
    return f"{street_num}, {street_name}, {city}, {state} - {postal}"

def generate_companies(count, start_id=1):
    """Generate companies with optimized data generation"""
    print(f"\nGenerating {count} companies...")
    
    companies = []
    for i in range(count):
        company = {
            'name': random.choice(DATA_POOLS['company_names']),
            'industry': random.choice(DATA_POOLS['industries']),
            'website': f"https://www{''.join(random.choice('abcdefghijklmnopqrstuvwxyz') for _ in range(8))}.com",
            'phone': generate_indian_phone(),
            'address': generate_indian_address(),
            'city': random.choice(DATA_POOLS['cities']),
            'state': random.choice(DATA_POOLS['states']),
            'postal_code': str(random.randint(100000, 999999)),
            'country': 'India',
            'employee_count': random.randint(10, 5000),
            'annual_revenue': round(random.uniform(100000, 100000000), 2)
        }
        companies.append(company)
        
        if (i + 1) % 10000 == 0:
            print(f"  Generated {i + 1}/{count} companies")
    
    return companies

def generate_sales_reps(count, start_id=1):
    """Generate sales representatives with optimized data generation"""
    print(f"\nGenerating {count} sales representatives...")
    
    sales_reps = []
    for i in range(count):
        rep = {
            'first_name': random.choice(DATA_POOLS['first_names']),
            'last_name': random.choice(DATA_POOLS['last_names']),
            'email': f"{random.choice(DATA_POOLS['first_names']).lower()}.{random.choice(DATA_POOLS['last_names']).lower()}@{random.choice(['gmail.com', 'yahoo.com', 'outlook.com', 'company.com'])}",
            'phone': generate_indian_phone(),
            'hire_date': fake.date_between(start_date='-5y', end_date='today'),
            'territory': random.choice(DATA_POOLS['territories']),
            'commission_rate': round(random.uniform(0.05, 0.15), 4),
            'target_quota': round(random.uniform(50000, 500000), 2)
        }
        sales_reps.append(rep)
        
        if (i + 1) % 10000 == 0:
            print(f"  Generated {i + 1}/{count} sales representatives")
    
    return sales_reps

def generate_customers(count, company_ids, start_id=1):
    """Generate customers with optimized data generation"""
    print(f"\nGenerating {count} customers...")
    
    customers = []
    for i in range(count):
        customer = {
            'company_id': random.choice(company_ids) if company_ids else None,
            'account_name': random.choice(DATA_POOLS['company_names']),
            'account_number': ''.join(random.choice('0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ') for _ in range(8)),
            'industry': random.choice(DATA_POOLS['job_titles']),
            'customer_since': fake.date_between(start_date='-3y', end_date='today'),
            'account_type': random.choice(DATA_POOLS['account_types']),
            'annual_revenue': round(random.uniform(10000, 5000000), 2),
            'employee_count': random.randint(5, 1000),
            'billing_address': generate_indian_address(),
            'billing_city': random.choice(DATA_POOLS['cities']),
            'billing_state': random.choice(DATA_POOLS['states']),
            'billing_postal_code': str(random.randint(100000, 999999)),
            'billing_country': 'India',
            'shipping_address': generate_indian_address(),
            'shipping_city': random.choice(DATA_POOLS['cities']),
            'shipping_state': random.choice(DATA_POOLS['states']),
            'shipping_postal_code': str(random.randint(100000, 999999)),
            'shipping_country': 'India'
        }
        customers.append(customer)
        
        if (i + 1) % 10000 == 0:
            print(f"  Generated {i + 1}/{count} customers")
    
    return customers

def generate_contacts(count, customer_ids, start_id=1):
    """Generate contacts with optimized data generation"""
    print(f"\nGenerating {count} contacts...")
    
    contacts = []
    for i in range(count):
        contact = {
            'customer_id': random.choice(customer_ids),
            'first_name': random.choice(DATA_POOLS['first_names']),
            'last_name': random.choice(DATA_POOLS['last_names']),
            'title': random.choice(DATA_POOLS['job_titles']),
            'email': f"{random.choice(DATA_POOLS['first_names']).lower()}.{random.choice(DATA_POOLS['last_names']).lower()}@{random.choice(['gmail.com', 'yahoo.com', 'outlook.com'])}",
            'phone': generate_indian_phone(),
            'mobile': generate_indian_phone(),
            'department': random.choice(DATA_POOLS['departments']),
            'is_primary': (i % 5 == 0)
        }
        contacts.append(contact)
        
        if (i + 1) % 10000 == 0:
            print(f"  Generated {i + 1}/{count} contacts")
    
    return contacts

def generate_leads(count, company_ids, sales_rep_ids, start_id=1):
    """Generate leads with optimized data generation"""
    print(f"\nGenerating {count} leads...")
    
    leads = []
    for i in range(count):
        lead = {
            'company_id': random.choice(company_ids) if company_ids else None,
            'sales_rep_id': random.choice(sales_rep_ids) if sales_rep_ids else None,
            'first_name': random.choice(DATA_POOLS['first_names']),
            'last_name': random.choice(DATA_POOLS['last_names']),
            'email': f"{random.choice(DATA_POOLS['first_names']).lower()}.{random.choice(DATA_POOLS['last_names']).lower()}@{random.choice(['gmail.com', 'yahoo.com'])}",
            'phone': generate_indian_phone(),
            'company_name': random.choice(DATA_POOLS['company_names']),
            'title': random.choice(DATA_POOLS['job_titles']),
            'industry': random.choice(DATA_POOLS['job_titles']),
            'lead_source': random.choice(DATA_POOLS['lead_sources']),
            'lead_status': random.choice(DATA_POOLS['lead_statuses']),
            'lead_score': random.randint(0, 100),
            'estimated_value': round(random.uniform(1000, 100000), 2),
            'notes': fake.paragraph()
        }
        leads.append(lead)
        
        if (i + 1) % 10000 == 0:
            print(f"  Generated {i + 1}/{count} leads")
    
    return leads

def generate_opportunities(count, customer_ids, sales_rep_ids, lead_ids, start_id=1):
    """Generate opportunities with optimized data generation"""
    print(f"\nGenerating {count} opportunities...")
    
    stage_probability = {
        'prospecting': 10, 'qualification': 25, 'needs_analysis': 40,
        'value_proposition': 60, 'negotiation': 80, 'closed_won': 100, 'closed_lost': 0
    }
    
    opportunities = []
    for i in range(count):
        stage = random.choice(DATA_POOLS['opportunity_stages'])
        probability = stage_probability[stage]
        
        opportunity = {
            'customer_id': random.choice(customer_ids),
            'sales_rep_id': random.choice(sales_rep_ids) if sales_rep_ids else None,
            'lead_id': random.choice(lead_ids) if lead_ids else None,
            'opportunity_name': f"Opportunity - {random.choice(DATA_POOLS['company_names'])} - {random.choice(DATA_POOLS['job_titles'])}",
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
    """Generate contracts with optimized data generation"""
    print(f"\nGenerating {count} contracts...")
    
    contracts = []
    for i in range(count):
        start_date = fake.date_between(start_date='-2y', end_date='today')
        contract = {
            'customer_id': random.choice(customer_ids),
            'opportunity_id': random.choice(opportunity_ids) if opportunity_ids else None,
            'contract_number': f"CTR-{''.join(random.choice('0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ') for _ in range(8))}",
            'contract_type': random.choice(DATA_POOLS['contract_types']),
            'start_date': start_date,
            'end_date': start_date + timedelta(days=random.randint(365, 1825)),
            'contract_value': round(random.uniform(10000, 500000), 2),
            'billing_frequency': random.choice(DATA_POOLS['billing_frequencies']),
            'status': random.choice(DATA_POOLS['contract_statuses']),
            'terms': fake.paragraph()
        }
        contracts.append(contract)
        
        if (i + 1) % 10000 == 0:
            print(f"  Generated {i + 1}/{count} contracts")
    
    return contracts

def generate_support_tickets(count, customer_ids, contact_ids, contract_ids, sales_rep_ids, start_id=1):
    """Generate support tickets with optimized data generation"""
    print(f"\nGenerating {count} support tickets...")
    
    tickets = []
    for i in range(count):
        status = random.choice(DATA_POOLS['ticket_statuses'])
        created_at = fake.date_time_between(start_date='-6m', end_date='now')
        
        ticket = {
            'customer_id': random.choice(customer_ids),
            'contact_id': random.choice(contact_ids) if contact_ids else None,
            'contract_id': random.choice(contract_ids) if contract_ids else None,
            'ticket_number': f"TKT-{''.join(random.choice('0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ') for _ in range(8))}",
            'subject': f"Support Request - {random.choice(DATA_POOLS['job_titles'])}",
            'description': fake.paragraph(),
            'priority': random.choice(DATA_POOLS['priorities']),
            'status': status,
            'category': random.choice(DATA_POOLS['ticket_categories']),
            'assigned_to': random.choice(sales_rep_ids) if sales_rep_ids else None,
            'resolved_at': created_at + timedelta(days=random.randint(1, 30)) if status in ['resolved', 'closed'] else None
        }
        tickets.append(ticket)
        
        if (i + 1) % 10000 == 0:
            print(f"  Generated {i + 1}/{count} support tickets")
    
    return tickets

def generate_activities(count, customer_ids, contact_ids, opportunity_ids, lead_ids, sales_rep_ids, start_id=1):
    """Generate activities with optimized data generation"""
    print(f"\nGenerating {count} activities...")
    
    activities = []
    for i in range(count):
        status = random.choice(DATA_POOLS['activity_statuses'])
        due_date = fake.date_time_between(start_date='-1m', end_date='+1m')
        
        activity = {
            'customer_id': random.choice(customer_ids) if customer_ids else None,
            'contact_id': random.choice(contact_ids) if contact_ids else None,
            'opportunity_id': random.choice(opportunity_ids) if opportunity_ids else None,
            'lead_id': random.choice(lead_ids) if lead_ids else None,
            'sales_rep_id': random.choice(sales_rep_ids),
            'activity_type': random.choice(DATA_POOLS['activity_types']),
            'subject': f"{random.choice(DATA_POOLS['activity_types']).title()} - {random.choice(DATA_POOLS['job_titles'])}",
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
    """Generate invoices with optimized data generation"""
    print(f"\nGenerating {count} invoices...")
    
    invoices = []
    for i in range(count):
        invoice_date = fake.date_between(start_date='-6m', end_date='today')
        amount = round(random.uniform(1000, 50000), 2)
        tax_amount = round(amount * 0.18, 2)  # 18% GST
        
        status = random.choice(DATA_POOLS['invoice_statuses'])
        payment_date = invoice_date + timedelta(days=random.randint(1, 60)) if status == 'paid' else None
        
        invoice = {
            'customer_id': random.choice(customer_ids),
            'contract_id': random.choice(contract_ids) if contract_ids else None,
            'invoice_number': f"INV-{''.join(random.choice('0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ') for _ in range(8))}",
            'invoice_date': invoice_date,
            'due_date': invoice_date + timedelta(days=30),
            'amount': amount,
            'tax_amount': tax_amount,
            'total_amount': amount + tax_amount,
            'status': status,
            'payment_method': random.choice(DATA_POOLS['payment_methods']) if status == 'paid' else None,
            'payment_date': payment_date,
            'notes': fake.sentence()
        }
        invoices.append(invoice)
        
        if (i + 1) % 10000 == 0:
            print(f"  Generated {i + 1}/{count} invoices")
    
    return invoices

def insert_batch_with_retry(cursor, table_name, columns, data, batch_size=BATCH_SIZE, 
                           connection=None, progress=None, table_name_for_progress=None,
                           start_time=None, total_target=0, monitor=None):
    """Insert data in batches with exponential backoff retry logic and checkpointing"""
    if not data:
        return 0
    
    placeholders = ', '.join(['%s'] * len(columns))
    columns_str = ', '.join(columns)
    sql = f"INSERT IGNORE INTO {table_name} ({columns_str}) VALUES ({placeholders})"
    
    total_inserted = 0
    reconnect_count = 0
    readonly_event_count = 0
    deadlock_count = 0
    total_wait_time = 0
    batch_number = 0
    
    for i in range(0, len(data), batch_size):
        batch = data[i:i + batch_size]
        batch_values = [tuple(row[col] for col in columns) for row in batch]
        
        batch_number += 1
        batch_start_time = time.time()
        
        # Ping connection before each batch
        if connection and not ping_connection(connection):
            print(f"  Connection lost before batch, reconnecting...")
            try:
                connection.rollback()
                connection.close()
            except:
                pass
            new_connection = reconnect_with_backoff(monitor=monitor)
            connection.update_connection(new_connection)
            cursor = connection.cursor()
            reconnect_count += 1
        
        # Check server status before each batch
        readonly_status = "WRITABLE"
        if connection and not check_server_writable(connection):
            print(f"  Server is read-only, polling for writable state...")
            readonly_status = "READ-ONLY"
            readonly_start = time.time()
            if not wait_for_writable_log(connection, monitor=monitor):
                print(f"  Connection lost during polling, reconnecting...")
                try:
                    connection.rollback()
                    connection.close()
                except:
                    pass
                new_connection = reconnect_with_backoff(monitor=monitor)
                connection.update_connection(new_connection)
                cursor = connection.cursor()
                reconnect_count += 1
            readonly_wait = time.time() - readonly_start
            total_wait_time += readonly_wait
            if monitor:
                monitor.record_readonly(readonly_wait)
            readonly_event_count += 1
            readonly_status = "WRITABLE"
        
        # Retry with exponential backoff
        max_retries = 5
        base_delay = 1  # seconds
        
        for attempt in range(max_retries):
            try:
                cursor.executemany(sql, batch_values)
                total_inserted += len(batch)
                
                batch_time = time.time() - batch_start_time
                
                # Record batch metrics
                if monitor:
                    monitor.record_batch(table_name, len(batch), batch_time)
                
                # Comprehensive dashboard after every batch
                remaining = len(data) - total_inserted
                overall_pct = (total_inserted / len(data)) * 100
                throughput = len(batch) / batch_time if batch_time > 0 else 0
                
                print(f"\n{'='*80}")
                print(f"DASHBOARD - {table_name.upper()}")
                print(f"{'='*80}")
                print(f"Current Table: {table_name}")
                print(f"Current Batch: {batch_number}")
                print(f"Rows Generated: {total_inserted:,}")
                print(f"Rows Remaining: {remaining:,}")
                print(f"Overall Progress: {overall_pct:.1f}%")
                print(f"Current Throughput: {throughput:.2f} rows/sec")
                
                if start_time and total_target > 0:
                    eta = calculate_eta(start_time, total_target, total_inserted)
                    if eta:
                        eta_str = format_eta(eta)
                        print(f"Current ETA: {eta_str}")
                
                print(f"Read-Only Status: {readonly_status}")
                print(f"Reconnect Count: {reconnect_count}")
                print(f"Deadlock Count: {deadlock_count}")
                print(f"Total Waiting Time: {total_wait_time:.1f}s")
                print(f"{'='*80}\n")
                
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
                error_code = e.args[0]
                
                # Handle connection errors
                if error_code in [2013, 2006]:  # Lost connection or MySQL server has gone away
                    print(f"  Connection error {error_code} detected, reconnecting...")
                    try:
                        connection.rollback()
                        connection.close()
                    except:
                        pass
                    new_connection = reconnect_with_backoff(monitor=monitor)
                    connection.update_connection(new_connection)
                    cursor = connection.cursor()
                    reconnect_count += 1
                    continue  # Retry with new connection
                
                elif error_code == 1290:  # read-only error
                    print(f"  Read-only error detected (attempt {attempt + 1}/{max_retries})")
                    readonly_start = time.time()
                    if connection and wait_for_writable_log(connection, monitor=monitor):
                        readonly_wait = time.time() - readonly_start
                        total_wait_time += readonly_wait
                        if monitor:
                            monitor.record_readonly(readonly_wait)
                        readonly_event_count += 1
                        continue  # Retry
                    else:
                        print(f"  Connection lost during polling, reconnecting...")
                        try:
                            connection.rollback()
                            connection.close()
                        except:
                            pass
                        new_connection = reconnect_with_backoff(monitor=monitor)
                        connection.update_connection(new_connection)
                        cursor = connection.cursor()
                        reconnect_count += 1
                        continue
                        
                elif error_code == 1213:  # deadlock error
                    if attempt < max_retries - 1:
                        # Rollback the failed batch
                        connection.rollback()
                        
                        # Record deadlock
                        deadlock_count += 1
                        if monitor:
                            monitor.record_deadlock(table_name)
                        
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
    """Main generation process with optimized data generation"""
    print("=" * 80)
    print("OPTIMIZED PRODUCTION-READY CRM DATASET GENERATOR")
    print("=" * 80)
    
    # Initialize monitor
    monitor = GenerationMonitor()
    monitor.start()
    
    # Check if this is a resume
    progress = load_progress()
    if progress.get('start_time'):
        monitor.record_resume()
    
    # Initialize data pools
    initialize_data_pools()
    
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
    
    raw_connection = get_connection()
    connection = ConnectionWrapper(raw_connection)
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
            total_target=total_target, monitor=monitor
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
            total_target=total_target, monitor=monitor
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
                total_target=total_target, monitor=monitor
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
                total_target=total_target, monitor=monitor
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
                total_target=total_target, monitor=monitor
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
                total_target=total_target, monitor=monitor
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
                total_target=total_target, monitor=monitor
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
                total_target=total_target, monitor=monitor
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
                total_target=total_target, monitor=monitor
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
                total_target=total_target, monitor=monitor
            )
            total_inserted += inserted
            print(f"  Progress: {total_inserted}/{remaining} invoices inserted")
        
        print(f"✓ Inserted {total_inserted} invoices")
        update_table_progress(progress, 'invoices', target)
    
    cursor.close()
    connection.close()
    
    # Stop monitoring and generate report
    monitor.stop()
    
    # Final report
    elapsed_time = time.time() - start_time
    
    print("\n" + "=" * 80)
    print("GENERATION COMPLETED")
    print("=" * 80)
    print(f"Total elapsed time: {elapsed_time:.2f} seconds ({elapsed_time/60:.2f} minutes)")
    
    # Export monitoring reports
    print("\n" + "=" * 80)
    print("GENERATING MONITORING REPORTS")
    print("=" * 80)
    
    json_file = monitor.export_json("crm_generation_report.json")
    print(f"✓ JSON report exported: {json_file}")
    
    pdf_file = monitor.export_pdf("crm_generation_report.pdf")
    print(f"✓ PDF report exported: {pdf_file}")
    
    # Print summary
    summary = monitor.get_summary()
    print("\n" + "=" * 80)
    print("MONITORING SUMMARY")
    print("=" * 80)
    print(f"Total batches: {summary['batch_metrics']['total_batches']}")
    print(f"Total rows inserted: {summary['batch_metrics']['total_rows_inserted']:,}")
    print(f"Average batch time: {summary['batch_metrics']['average_batch_time_seconds']:.4f}s")
    print(f"Average throughput: {summary['batch_metrics']['average_rows_per_second']:.2f} rows/sec")
    print(f"Peak throughput: {summary['batch_metrics']['peak_throughput_rows_per_second']:.2f} rows/sec")
    print(f"Deadlocks encountered: {summary['error_handling']['deadlock_count']}")
    print(f"Read-only events: {summary['error_handling']['readonly_event_count']}")
    print(f"Total read-only wait time: {summary['error_handling']['total_readonly_wait_time_formatted']}")
    print(f"Resume count: {summary['resilience']['resume_count']}")
    
    # Clean up progress file
    if os.path.exists(PROGRESS_FILE):
        os.remove(PROGRESS_FILE)
        print(f"\n✓ Removed progress file: {PROGRESS_FILE}")
    
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
