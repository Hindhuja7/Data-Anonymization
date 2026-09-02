"""
Step 3: Generate Small Test Dataset for CRM
"""
import os
import random
import pymysql
from faker import Faker
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

# Initialize Faker
fake = Faker()
Faker.seed(42)  # For reproducible data

def get_connection():
    """Get MySQL connection with SSL"""
    ssl_config = {
        'ssl_ca': '/etc/ssl/certs/ca-certificates.crt',
        'ssl_verify_cert': True,
        'ssl_verify_identity': True
    }
    
    return pymysql.connect(
        host=os.getenv('MYSQL_HOST'),
        port=int(os.getenv('MYSQL_PORT')),
        user=os.getenv('MYSQL_USERNAME'),
        password=os.getenv('MYSQL_PASSWORD'),
        database=os.getenv('MYSQL_DATABASE'),
        ssl=ssl_config
    )

def generate_companies(count):
    """Generate companies data"""
    print(f"\nGenerating {count} companies...")
    
    industries = ['Technology', 'Healthcare', 'Finance', 'Manufacturing', 'Retail', 
                  'Education', 'Consulting', 'Energy', 'Telecommunications', 'Transportation']
    
    companies = []
    for _ in range(count):
        company = {
            'name': fake.company(),
            'industry': random.choice(industries),
            'website': fake.url(),
            'phone': fake.phone_number(),
            'address': fake.street_address(),
            'city': fake.city(),
            'state': fake.state(),
            'postal_code': fake.zipcode(),
            'country': fake.country(),
            'employee_count': random.randint(10, 5000),
            'annual_revenue': round(random.uniform(100000, 100000000), 2)
        }
        companies.append(company)
    
    return companies

def generate_sales_reps(count):
    """Generate sales representatives data"""
    print(f"\nGenerating {count} sales representatives...")
    
    territories = ['North America', 'Europe', 'Asia Pacific', 'Latin America', 'Middle East']
    
    sales_reps = []
    for _ in range(count):
        rep = {
            'first_name': fake.first_name(),
            'last_name': fake.last_name(),
            'email': fake.email(),
            'phone': fake.phone_number(),
            'hire_date': fake.date_between(start_date='-5y', end_date='today'),
            'territory': random.choice(territories),
            'commission_rate': round(random.uniform(0.05, 0.15), 4),
            'target_quota': round(random.uniform(50000, 500000), 2)
        }
        sales_reps.append(rep)
    
    return sales_reps

def generate_customers(count, company_ids):
    """Generate customers data"""
    print(f"\nGenerating {count} customers...")
    
    account_types = ['prospect', 'active', 'inactive', 'churned']
    
    customers = []
    for _ in range(count):
        customer = {
            'company_id': random.choice(company_ids) if company_ids else None,
            'account_name': fake.company(),
            'account_number': fake.uuid4()[:8].upper(),
            'industry': fake.job(),
            'customer_since': fake.date_between(start_date='-3y', end_date='today'),
            'account_type': random.choice(account_types),
            'annual_revenue': round(random.uniform(10000, 5000000), 2),
            'employee_count': random.randint(5, 1000),
            'billing_address': fake.street_address(),
            'billing_city': fake.city(),
            'billing_state': fake.state(),
            'billing_postal_code': fake.zipcode(),
            'billing_country': fake.country(),
            'shipping_address': fake.street_address(),
            'shipping_city': fake.city(),
            'shipping_state': fake.state(),
            'shipping_postal_code': fake.zipcode(),
            'shipping_country': fake.country()
        }
        customers.append(customer)
    
    return customers

def generate_contacts(count, customer_ids):
    """Generate contacts data"""
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
            'phone': fake.phone_number(),
            'mobile': fake.phone_number(),
            'department': random.choice(departments),
            'is_primary': (i % 5 == 0)  # Every 5th contact is primary
        }
        contacts.append(contact)
    
    return contacts

def generate_leads(count, company_ids, sales_rep_ids):
    """Generate leads data"""
    print(f"\nGenerating {count} leads...")
    
    lead_sources = ['website', 'referral', 'cold_call', 'trade_show', 'social_media', 'email_campaign', 'other']
    lead_statuses = ['new', 'contacted', 'qualified', 'lost', 'converted']
    
    leads = []
    for _ in range(count):
        lead = {
            'company_id': random.choice(company_ids) if company_ids else None,
            'sales_rep_id': random.choice(sales_rep_ids) if sales_rep_ids else None,
            'first_name': fake.first_name(),
            'last_name': fake.last_name(),
            'email': fake.email(),
            'phone': fake.phone_number(),
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
    
    return leads

def generate_opportunities(count, customer_ids, sales_rep_ids, lead_ids):
    """Generate opportunities data"""
    print(f"\nGenerating {count} opportunities...")
    
    stages = ['prospecting', 'qualification', 'needs_analysis', 'value_proposition', 
              'negotiation', 'closed_won', 'closed_lost']
    
    opportunities = []
    for _ in range(count):
        stage = random.choice(stages)
        probability = {
            'prospecting': 10,
            'qualification': 25,
            'needs_analysis': 40,
            'value_proposition': 60,
            'negotiation': 80,
            'closed_won': 100,
            'closed_lost': 0
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
    
    return opportunities

def generate_contracts(count, customer_ids, opportunity_ids):
    """Generate contracts data"""
    print(f"\nGenerating {count} contracts...")
    
    contract_types = ['service', 'product', 'subscription', 'maintenance', 'consulting']
    billing_frequencies = ['monthly', 'quarterly', 'annually', 'one_time']
    statuses = ['draft', 'active', 'expired', 'terminated', 'renewed']
    
    contracts = []
    for _ in range(count):
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
    
    return contracts

def generate_support_tickets(count, customer_ids, contact_ids, contract_ids, sales_rep_ids):
    """Generate support tickets data"""
    print(f"\nGenerating {count} support tickets...")
    
    priorities = ['low', 'medium', 'high', 'critical']
    statuses = ['open', 'in_progress', 'pending_customer', 'resolved', 'closed']
    categories = ['technical', 'billing', 'feature_request', 'bug', 'other']
    
    tickets = []
    for _ in range(count):
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
    
    return tickets

def generate_activities(count, customer_ids, contact_ids, opportunity_ids, lead_ids, sales_rep_ids):
    """Generate activities data"""
    print(f"\nGenerating {count} activities...")
    
    activity_types = ['call', 'email', 'meeting', 'note', 'task', 'demo', 'follow_up']
    statuses = ['scheduled', 'completed', 'cancelled', 'in_progress']
    
    activities = []
    for _ in range(count):
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
    
    return activities

def generate_invoices(count, customer_ids, contract_ids):
    """Generate invoices data"""
    print(f"\nGenerating {count} invoices...")
    
    statuses = ['draft', 'sent', 'paid', 'overdue', 'cancelled']
    payment_methods = ['credit_card', 'bank_transfer', 'check', 'paypal', 'wire']
    
    invoices = []
    for _ in range(count):
        invoice_date = fake.date_between(start_date='-6m', end_date='today')
        amount = round(random.uniform(1000, 50000), 2)
        tax_amount = round(amount * 0.1, 2)
        
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
    
    return invoices

def insert_batch(cursor, table_name, columns, data, batch_size=100):
    """Insert data in batches"""
    if not data:
        return
    
    placeholders = ', '.join(['%s'] * len(columns))
    columns_str = ', '.join(columns)
    sql = f"INSERT INTO {table_name} ({columns_str}) VALUES ({placeholders})"
    
    for i in range(0, len(data), batch_size):
        batch = data[i:i + batch_size]
        batch_values = [tuple(row[col] for col in columns) for row in batch]
        cursor.executemany(sql, batch_values)
        print(f"  Inserted {min(i + batch_size, len(data))}/{len(data)} rows into {table_name}")

def generate_test_dataset():
    """Generate small test dataset"""
    
    print("=" * 60)
    print("STEP 3: Generating Small Test Dataset")
    print("=" * 60)
    
    connection = get_connection()
    cursor = connection.cursor()
    
    # Test dataset sizes
    sizes = {
        'companies': 100,
        'customers': 1000,
        'contacts': 2000,
        'sales_representatives': 50,
        'leads': 500,
        'opportunities': 300,
        'contracts': 200,
        'support_tickets': 2000,
        'activities': 5000,
        'invoices': 1000
    }
    
    print(f"\nTarget sizes:")
    for table, count in sizes.items():
        print(f"  {table}: {count:,}")
    
    # Generate data in dependency order
    print("\n" + "=" * 60)
    print("Generating Data")
    print("=" * 60)
    
    # 1. Companies
    companies = generate_companies(sizes['companies'])
    insert_batch(cursor, 'companies', 
                 ['name', 'industry', 'website', 'phone', 'address', 'city', 'state', 
                  'postal_code', 'country', 'employee_count', 'annual_revenue'],
                 companies)
    company_ids = list(range(1, len(companies) + 1))
    
    # 2. Sales Representatives
    sales_reps = generate_sales_reps(sizes['sales_representatives'])
    insert_batch(cursor, 'sales_representatives',
                 ['first_name', 'last_name', 'email', 'phone', 'hire_date', 'territory', 
                  'commission_rate', 'target_quota'],
                 sales_reps)
    sales_rep_ids = list(range(1, len(sales_reps) + 1))
    
    # 3. Customers
    customers = generate_customers(sizes['customers'], company_ids)
    insert_batch(cursor, 'customers',
                 ['company_id', 'account_name', 'account_number', 'industry', 'customer_since',
                  'account_type', 'annual_revenue', 'employee_count', 'billing_address',
                  'billing_city', 'billing_state', 'billing_postal_code', 'billing_country',
                  'shipping_address', 'shipping_city', 'shipping_state', 'shipping_postal_code',
                  'shipping_country'],
                 customers)
    customer_ids = list(range(1, len(customers) + 1))
    
    # 4. Contacts
    contacts = generate_contacts(sizes['contacts'], customer_ids)
    insert_batch(cursor, 'contacts',
                 ['customer_id', 'first_name', 'last_name', 'title', 'email', 'phone',
                  'mobile', 'department', 'is_primary'],
                 contacts)
    contact_ids = list(range(1, len(contacts) + 1))
    
    # 5. Leads
    leads = generate_leads(sizes['leads'], company_ids, sales_rep_ids)
    insert_batch(cursor, 'leads',
                 ['company_id', 'sales_rep_id', 'first_name', 'last_name', 'email', 'phone',
                  'company_name', 'title', 'industry', 'lead_source', 'lead_status',
                  'lead_score', 'estimated_value', 'notes'],
                 leads)
    lead_ids = list(range(1, len(leads) + 1))
    
    # 6. Opportunities
    opportunities = generate_opportunities(sizes['opportunities'], customer_ids, sales_rep_ids, lead_ids)
    insert_batch(cursor, 'opportunities',
                 ['customer_id', 'sales_rep_id', 'lead_id', 'opportunity_name', 'opportunity_stage',
                  'amount', 'probability', 'expected_close_date', 'actual_close_date', 'description'],
                 opportunities)
    opportunity_ids = list(range(1, len(opportunities) + 1))
    
    # 7. Contracts
    contracts = generate_contracts(sizes['contracts'], customer_ids, opportunity_ids)
    insert_batch(cursor, 'contracts',
                 ['customer_id', 'opportunity_id', 'contract_number', 'contract_type', 'start_date',
                  'end_date', 'contract_value', 'billing_frequency', 'status', 'terms'],
                 contracts)
    contract_ids = list(range(1, len(contracts) + 1))
    
    # 8. Support Tickets
    support_tickets = generate_support_tickets(sizes['support_tickets'], customer_ids, contact_ids, 
                                               contract_ids, sales_rep_ids)
    insert_batch(cursor, 'support_tickets',
                 ['customer_id', 'contact_id', 'contract_id', 'ticket_number', 'subject',
                  'description', 'priority', 'status', 'category', 'assigned_to', 'resolved_at'],
                 support_tickets)
    
    # 9. Activities
    activities = generate_activities(sizes['activities'], customer_ids, contact_ids, 
                                      opportunity_ids, lead_ids, sales_rep_ids)
    insert_batch(cursor, 'activities',
                 ['customer_id', 'contact_id', 'opportunity_id', 'lead_id', 'sales_rep_id',
                  'activity_type', 'subject', 'description', 'status', 'due_date', 
                  'completed_at', 'duration_minutes'],
                 activities)
    
    # 10. Invoices
    invoices = generate_invoices(sizes['invoices'], customer_ids, contract_ids)
    insert_batch(cursor, 'invoices',
                 ['customer_id', 'contract_id', 'invoice_number', 'invoice_date', 'due_date',
                  'amount', 'tax_amount', 'total_amount', 'status', 'payment_method', 
                  'payment_date', 'notes'],
                 invoices)
    
    connection.commit()
    
    # Verify row counts
    print("\n" + "=" * 60)
    print("Verifying Row Counts")
    print("=" * 60)
    
    cursor.execute("SHOW TABLES")
    tables = [table[0] for table in cursor.fetchall()]
    
    all_correct = True
    for table in tables:
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        actual_count = cursor.fetchone()[0]
        expected_count = sizes.get(table, 0)
        status = "✓" if actual_count == expected_count else "✗"
        print(f"{status} {table}: {actual_count:,} (expected: {expected_count:,})")
        if actual_count != expected_count:
            all_correct = False
    
    # Verify referential integrity
    print("\n" + "=" * 60)
    print("Verifying Referential Integrity")
    print("=" * 60)
    
    integrity_checks = [
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
    
    integrity_ok = True
    for check_name, query in integrity_checks:
        cursor.execute(query)
        violations = cursor.fetchone()[0]
        status = "✓" if violations == 0 else "✗"
        print(f"{status} {check_name}: {violations} violations")
        if violations > 0:
            integrity_ok = False
    
    # Show sample records
    print("\n" + "=" * 60)
    print("Sample Records")
    print("=" * 60)
    
    for table in ['companies', 'customers', 'contacts', 'sales_representatives', 'leads', 
                  'opportunities', 'contracts', 'support_tickets', 'activities', 'invoices']:
        cursor.execute(f"SELECT * FROM {table} LIMIT 2")
        rows = cursor.fetchall()
        cursor.execute(f"DESCRIBE {table}")
        columns = [col[0] for col in cursor.fetchall()]
        
        print(f"\n{table}:")
        for row in rows:
            print(f"  {dict(zip(columns, row))}")
    
    cursor.close()
    connection.close()
    
    print("\n" + "=" * 60)
    if all_correct and integrity_ok:
        print("TEST DATASET GENERATION: COMPLETED SUCCESSFULLY")
    else:
        print("TEST DATASET GENERATION: COMPLETED WITH ERRORS")
    print("=" * 60)
    
    return all_correct and integrity_ok

if __name__ == "__main__":
    try:
        success = generate_test_dataset()
        if success:
            print("\n✓ Test dataset generated and validated successfully")
            print("⏸️  Waiting for your approval before generating the large enterprise dataset")
        else:
            print("\n✗ Test dataset generation completed with errors")
            exit(1)
    except Exception as e:
        print(f"\n✗ Error generating test dataset: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
