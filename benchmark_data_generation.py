"""
Benchmark Data Generation Performance
"""
import time
import random
from faker import Faker

# Initialize Faker (single instance)
fake = Faker()
Faker.seed(42)

# Pre-generated data pools
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
    
    indian_cities = ['Mumbai', 'Delhi', 'Bangalore', 'Chennai', 'Hyderabad', 'Pune', 
                    'Ahmedabad', 'Jaipur', 'Lucknow', 'Kolkata', 'Surat', 'Kanpur',
                    'Nagpur', 'Indore', 'Thane', 'Bhopal', 'Visakhapatnam', 'Pimpri',
                    'Patna', 'Vadodara', 'Ghaziabad', 'Ludhiana', 'Agra', 'Nashik']
    DATA_POOLS['cities'] = indian_cities * 2000
    
    indian_states = ['Maharashtra', 'Delhi', 'Karnataka', 'Tamil Nadu', 'Telangana', 
                    'Gujarat', 'Rajasthan', 'Uttar Pradesh', 'West Bengal', 'Madhya Pradesh',
                    'Punjab', 'Haryana', 'Kerala', 'Bihar', 'Odisha']
    DATA_POOLS['states'] = indian_states * 3000
    
    print("  Generating first names...")
    DATA_POOLS['first_names'] = [fake.first_name() for _ in range(50000)]
    
    print("  Generating last names...")
    DATA_POOLS['last_names'] = [fake.last_name() for _ in range(50000)]
    
    print("  Generating company names...")
    DATA_POOLS['company_names'] = [fake.company() for _ in range(50000)]
    
    industries = ['Technology', 'Healthcare', 'Finance', 'Manufacturing', 'Retail', 
                  'Education', 'Consulting', 'Energy', 'Telecommunications', 'Transportation',
                  'Real Estate', 'Construction', 'Agriculture', 'Pharmaceuticals', 'Media']
    DATA_POOLS['industries'] = industries * 3000
    
    print("  Generating job titles...")
    DATA_POOLS['job_titles'] = [fake.job() for _ in range(50000)]
    
    print("  Generating street names...")
    DATA_POOLS['street_names'] = [fake.street_name() for _ in range(50000)]
    
    departments = ['Sales', 'Marketing', 'Finance', 'IT', 'Operations', 'HR', 'Executive', 'Legal', 'R&D']
    DATA_POOLS['departments'] = departments * 5000
    
    territories = ['North India', 'South India', 'East India', 'West India', 'Central India']
    DATA_POOLS['territories'] = territories * 10000
    
    lead_sources = ['website', 'referral', 'cold_call', 'trade_show', 'social_media', 'email_campaign', 'other']
    DATA_POOLS['lead_sources'] = lead_sources * 7000
    
    lead_statuses = ['new', 'contacted', 'qualified', 'lost', 'converted']
    DATA_POOLS['lead_statuses'] = lead_statuses * 10000
    
    opportunity_stages = ['prospecting', 'qualification', 'needs_analysis', 'value_proposition', 
                        'negotiation', 'closed_won', 'closed_lost']
    DATA_POOLS['opportunity_stages'] = opportunity_stages * 7000
    
    contract_types = ['service', 'product', 'subscription', 'maintenance', 'consulting']
    DATA_POOLS['contract_types'] = contract_types * 10000
    
    billing_frequencies = ['monthly', 'quarterly', 'annually', 'one_time']
    DATA_POOLS['billing_frequencies'] = billing_frequencies * 12500
    
    contract_statuses = ['draft', 'active', 'expired', 'terminated', 'renewed']
    DATA_POOLS['contract_statuses'] = contract_statuses * 10000
    
    priorities = ['low', 'medium', 'high', 'critical']
    DATA_POOLS['priorities'] = priorities * 12500
    
    ticket_statuses = ['open', 'in_progress', 'pending_customer', 'resolved', 'closed']
    DATA_POOLS['ticket_statuses'] = ticket_statuses * 10000
    
    ticket_categories = ['technical', 'billing', 'feature_request', 'bug', 'other']
    DATA_POOLS['ticket_categories'] = ticket_categories * 10000
    
    activity_types = ['call', 'email', 'meeting', 'note', 'task', 'demo', 'follow_up']
    DATA_POOLS['activity_types'] = activity_types * 7000
    
    activity_statuses = ['scheduled', 'completed', 'cancelled', 'in_progress']
    DATA_POOLS['activity_statuses'] = activity_statuses * 12500
    
    invoice_statuses = ['draft', 'sent', 'paid', 'overdue', 'cancelled']
    DATA_POOLS['invoice_statuses'] = invoice_statuses * 10000
    
    payment_methods = ['credit_card', 'bank_transfer', 'check', 'paypal', 'wire', 'upi', 'net_banking']
    DATA_POOLS['payment_methods'] = payment_methods * 7000
    
    account_types = ['prospect', 'active', 'inactive', 'churned']
    DATA_POOLS['account_types'] = account_types * 12500
    
    ifsc_banks = ['SBIN', 'HDFC', 'ICIC', 'AXIS', 'KKBK', 'UBIN', 'PUNB', 'CORP', 
                 'IDFB', 'DLBL', 'YESB', 'INDB', 'RATN', 'BAND', 'CNRB', 'KVBL']
    DATA_POOLS['ifsc_banks'] = ifsc_banks * 3000
    
    print("Data pools initialized.")

def generate_indian_phone():
    """Generate realistic Indian phone number (lightweight)"""
    import random
    first = random.choice(['6', '7', '8', '9'])
    rest = ''.join(random.choice('0123456789') for _ in range(9))
    return f"+91 {first}{rest[:4]} {rest[4:]}"

def generate_indian_address():
    """Generate realistic Indian address (using pools)"""
    import random
    street_num = random.randint(1, 999)
    street_name = random.choice(DATA_POOLS['street_names'])
    city = random.choice(DATA_POOLS['cities'])
    state = random.choice(DATA_POOLS['states'])
    postal = str(random.randint(100000, 999999))
    
    return f"{street_num}, {street_name}, {city}, {state} - {postal}"

# OLD METHOD (using Faker for everything)
def generate_contacts_old(count):
    """Generate contacts using old Faker-heavy method"""
    contacts = []
    for i in range(count):
        contact = {
            'first_name': fake.first_name(),
            'last_name': fake.last_name(),
            'title': fake.job(),
            'email': fake.email(),
            'phone': f"+91 {random.choice(['6', '7', '8', '9'])}{''.join(random.choice('0123456789') for _ in range(9))}",
            'mobile': f"+91 {random.choice(['6', '7', '8', '9'])}{''.join(random.choice('0123456789') for _ in range(9))}",
            'department': random.choice(['Sales', 'Marketing', 'Finance', 'IT', 'Operations', 'HR', 'Executive']),
            'is_primary': (i % 5 == 0)
        }
        contacts.append(contact)
    return contacts

# NEW METHOD (using pre-generated pools)
def generate_contacts_new(count):
    """Generate contacts using optimized method with pools"""
    contacts = []
    for i in range(count):
        contact = {
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
    return contacts

print("=" * 80)
print("DATA GENERATION PERFORMANCE BENCHMARK")
print("=" * 80)

# Test sizes
test_sizes = [1000, 5000, 10000]

print("\n1. OLD METHOD (Faker-heavy)")
print("-" * 80)
old_results = {}
for size in test_sizes:
    start = time.time()
    contacts = generate_contacts_old(size)
    end = time.time()
    elapsed = end - start
    rate = size / elapsed
    old_results[size] = {'elapsed': elapsed, 'rate': rate}
    print(f"  {size:6d} contacts: {elapsed:6.4f}s ({rate:8.2f} rows/sec)")

print("\n2. NEW METHOD (Pre-generated pools)")
print("-" * 80)
print("Initializing data pools...")
initialize_data_pools()

new_results = {}
for size in test_sizes:
    start = time.time()
    contacts = generate_contacts_new(size)
    end = time.time()
    elapsed = end - start
    rate = size / elapsed
    new_results[size] = {'elapsed': elapsed, 'rate': rate}
    print(f"  {size:6d} contacts: {elapsed:6.4f}s ({rate:8.2f} rows/sec)")

print("\n3. PERFORMANCE COMPARISON")
print("-" * 80)
print(f"{'Size':>6s} | {'Old (s)':>10s} | {'New (s)':>10s} | {'Speedup':>10s} | {'Improvement':>12s}")
print("-" * 70)
for size in test_sizes:
    old_time = old_results[size]['elapsed']
    new_time = new_results[size]['elapsed']
    speedup = old_time / new_time
    improvement = ((old_time - new_time) / old_time) * 100
    print(f"{size:6d} | {old_time:10.4f} | {new_time:10.4f} | {speedup:10.2f}x | {improvement:11.1f}%")

print("\n4. ESTIMATED COMPLETION TIME COMPARISON")
print("-" * 80)
total_rows = 5464250
old_rate = old_results[10000]['rate']
new_rate = new_results[10000]['rate']

old_time = total_rows / old_rate
new_time = total_rows / new_rate

print(f"Total rows to generate: {total_rows:,}")
print(f"Old method rate: {old_rate:.2f} rows/sec")
print(f"New method rate: {new_rate:.2f} rows/sec")
print(f"\nOld method estimated time: {old_time/3600:.2f} hours ({old_time/60:.2f} minutes)")
print(f"New method estimated time: {new_time/3600:.2f} hours ({new_time/60:.2f} minutes)")
print(f"Time saved: {(old_time - new_time)/3600:.2f} hours ({(old_time - new_time)/60:.2f} minutes)")

print("\n" + "=" * 80)
print("BENCHMARK COMPLETE")
print("=" * 80)
