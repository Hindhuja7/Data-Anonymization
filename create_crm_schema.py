"""
Step 2: Create CRM Schema with Normalized Tables
"""
import os
import pymysql
from dotenv import load_dotenv

load_dotenv()

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

def create_crm_schema():
    """Create normalized CRM schema with all tables"""
    
    print("=" * 60)
    print("STEP 2: Creating CRM Schema")
    print("=" * 60)
    
    connection = get_connection()
    cursor = connection.cursor()
    
    # Drop existing tables if they exist (in reverse order of dependencies)
    drop_statements = [
        "DROP TABLE IF EXISTS invoices",
        "DROP TABLE IF EXISTS activities",
        "DROP TABLE IF EXISTS support_tickets",
        "DROP TABLE IF EXISTS contracts",
        "DROP TABLE IF EXISTS opportunities",
        "DROP TABLE IF EXISTS leads",
        "DROP TABLE IF EXISTS contacts",
        "DROP TABLE IF EXISTS customers",
        "DROP TABLE IF EXISTS sales_representatives",
        "DROP TABLE IF EXISTS companies"
    ]
    
    print("\nDropping existing tables (if any)...")
    for stmt in drop_statements:
        cursor.execute(stmt)
    print("✓ Existing tables dropped")
    
    # Create tables in order of dependencies
    
    # 1. companies
    print("\nCreating table: companies")
    cursor.execute("""
        CREATE TABLE companies (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            industry VARCHAR(100),
            website VARCHAR(255),
            phone VARCHAR(50),
            address TEXT,
            city VARCHAR(100),
            state VARCHAR(100),
            postal_code VARCHAR(20),
            country VARCHAR(100),
            employee_count INT,
            annual_revenue DECIMAL(20,2),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            INDEX idx_industry (industry),
            INDEX idx_city (city),
            INDEX idx_state (state)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """)
    print("✓ companies table created")
    
    # 2. sales_representatives
    print("\nCreating table: sales_representatives")
    cursor.execute("""
        CREATE TABLE sales_representatives (
            id INT AUTO_INCREMENT PRIMARY KEY,
            first_name VARCHAR(100) NOT NULL,
            last_name VARCHAR(100) NOT NULL,
            email VARCHAR(255) UNIQUE NOT NULL,
            phone VARCHAR(50),
            hire_date DATE,
            territory VARCHAR(100),
            commission_rate DECIMAL(5,4),
            target_quota DECIMAL(20,2),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            INDEX idx_email (email),
            INDEX idx_territory (territory)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """)
    print("✓ sales_representatives table created")
    
    # 3. customers
    print("\nCreating table: customers")
    cursor.execute("""
        CREATE TABLE customers (
            id INT AUTO_INCREMENT PRIMARY KEY,
            company_id INT,
            account_name VARCHAR(255) NOT NULL,
            account_number VARCHAR(50) UNIQUE,
            industry VARCHAR(100),
            customer_since DATE,
            account_type ENUM('prospect', 'active', 'inactive', 'churned') DEFAULT 'prospect',
            annual_revenue DECIMAL(20,2),
            employee_count INT,
            billing_address TEXT,
            billing_city VARCHAR(100),
            billing_state VARCHAR(100),
            billing_postal_code VARCHAR(20),
            billing_country VARCHAR(100),
            shipping_address TEXT,
            shipping_city VARCHAR(100),
            shipping_state VARCHAR(100),
            shipping_postal_code VARCHAR(20),
            shipping_country VARCHAR(100),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE SET NULL,
            INDEX idx_company_id (company_id),
            INDEX idx_account_type (account_type),
            INDEX idx_account_number (account_number)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """)
    print("✓ customers table created")
    
    # 4. contacts
    print("\nCreating table: contacts")
    cursor.execute("""
        CREATE TABLE contacts (
            id INT AUTO_INCREMENT PRIMARY KEY,
            customer_id INT NOT NULL,
            first_name VARCHAR(100) NOT NULL,
            last_name VARCHAR(100) NOT NULL,
            title VARCHAR(100),
            email VARCHAR(255),
            phone VARCHAR(50),
            mobile VARCHAR(50),
            department VARCHAR(100),
            is_primary BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            FOREIGN KEY (customer_id) REFERENCES customers(id) ON DELETE CASCADE,
            INDEX idx_customer_id (customer_id),
            INDEX idx_email (email),
            INDEX idx_is_primary (is_primary)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """)
    print("✓ contacts table created")
    
    # 5. leads
    print("\nCreating table: leads")
    cursor.execute("""
        CREATE TABLE leads (
            id INT AUTO_INCREMENT PRIMARY KEY,
            company_id INT,
            sales_rep_id INT,
            first_name VARCHAR(100) NOT NULL,
            last_name VARCHAR(100) NOT NULL,
            email VARCHAR(255),
            phone VARCHAR(50),
            company_name VARCHAR(255),
            title VARCHAR(100),
            industry VARCHAR(100),
            lead_source ENUM('website', 'referral', 'cold_call', 'trade_show', 'social_media', 'email_campaign', 'other') DEFAULT 'website',
            lead_status ENUM('new', 'contacted', 'qualified', 'lost', 'converted') DEFAULT 'new',
            lead_score INT DEFAULT 0,
            estimated_value DECIMAL(20,2),
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE SET NULL,
            FOREIGN KEY (sales_rep_id) REFERENCES sales_representatives(id) ON DELETE SET NULL,
            INDEX idx_company_id (company_id),
            INDEX idx_sales_rep_id (sales_rep_id),
            INDEX idx_lead_status (lead_status),
            INDEX idx_lead_source (lead_source)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """)
    print("✓ leads table created")
    
    # 6. opportunities
    print("\nCreating table: opportunities")
    cursor.execute("""
        CREATE TABLE opportunities (
            id INT AUTO_INCREMENT PRIMARY KEY,
            customer_id INT NOT NULL,
            sales_rep_id INT,
            lead_id INT,
            opportunity_name VARCHAR(255) NOT NULL,
            opportunity_stage ENUM('prospecting', 'qualification', 'needs_analysis', 'value_proposition', 'negotiation', 'closed_won', 'closed_lost') DEFAULT 'prospecting',
            amount DECIMAL(20,2),
            probability INT DEFAULT 0,
            expected_close_date DATE,
            actual_close_date DATE,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            FOREIGN KEY (customer_id) REFERENCES customers(id) ON DELETE CASCADE,
            FOREIGN KEY (sales_rep_id) REFERENCES sales_representatives(id) ON DELETE SET NULL,
            FOREIGN KEY (lead_id) REFERENCES leads(id) ON DELETE SET NULL,
            INDEX idx_customer_id (customer_id),
            INDEX idx_sales_rep_id (sales_rep_id),
            INDEX idx_lead_id (lead_id),
            INDEX idx_opportunity_stage (opportunity_stage),
            INDEX idx_expected_close_date (expected_close_date)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """)
    print("✓ opportunities table created")
    
    # 7. contracts
    print("\nCreating table: contracts")
    cursor.execute("""
        CREATE TABLE contracts (
            id INT AUTO_INCREMENT PRIMARY KEY,
            customer_id INT NOT NULL,
            opportunity_id INT,
            contract_number VARCHAR(50) UNIQUE NOT NULL,
            contract_type ENUM('service', 'product', 'subscription', 'maintenance', 'consulting') DEFAULT 'service',
            start_date DATE NOT NULL,
            end_date DATE,
            contract_value DECIMAL(20,2),
            billing_frequency ENUM('monthly', 'quarterly', 'annually', 'one_time') DEFAULT 'annually',
            status ENUM('draft', 'active', 'expired', 'terminated', 'renewed') DEFAULT 'draft',
            terms TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            FOREIGN KEY (customer_id) REFERENCES customers(id) ON DELETE CASCADE,
            FOREIGN KEY (opportunity_id) REFERENCES opportunities(id) ON DELETE SET NULL,
            INDEX idx_customer_id (customer_id),
            INDEX idx_opportunity_id (opportunity_id),
            INDEX idx_contract_number (contract_number),
            INDEX idx_status (status)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """)
    print("✓ contracts table created")
    
    # 8. support_tickets
    print("\nCreating table: support_tickets")
    cursor.execute("""
        CREATE TABLE support_tickets (
            id INT AUTO_INCREMENT PRIMARY KEY,
            customer_id INT NOT NULL,
            contact_id INT,
            contract_id INT,
            ticket_number VARCHAR(50) UNIQUE NOT NULL,
            subject VARCHAR(255) NOT NULL,
            description TEXT,
            priority ENUM('low', 'medium', 'high', 'critical') DEFAULT 'medium',
            status ENUM('open', 'in_progress', 'pending_customer', 'resolved', 'closed') DEFAULT 'open',
            category ENUM('technical', 'billing', 'feature_request', 'bug', 'other') DEFAULT 'technical',
            assigned_to INT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            resolved_at TIMESTAMP NULL,
            FOREIGN KEY (customer_id) REFERENCES customers(id) ON DELETE CASCADE,
            FOREIGN KEY (contact_id) REFERENCES contacts(id) ON DELETE SET NULL,
            FOREIGN KEY (contract_id) REFERENCES contracts(id) ON DELETE SET NULL,
            FOREIGN KEY (assigned_to) REFERENCES sales_representatives(id) ON DELETE SET NULL,
            INDEX idx_customer_id (customer_id),
            INDEX idx_contact_id (contact_id),
            INDEX idx_contract_id (contract_id),
            INDEX idx_assigned_to (assigned_to),
            INDEX idx_ticket_number (ticket_number),
            INDEX idx_status (status),
            INDEX idx_priority (priority)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """)
    print("✓ support_tickets table created")
    
    # 9. activities
    print("\nCreating table: activities")
    cursor.execute("""
        CREATE TABLE activities (
            id INT AUTO_INCREMENT PRIMARY KEY,
            customer_id INT,
            contact_id INT,
            opportunity_id INT,
            lead_id INT,
            sales_rep_id INT NOT NULL,
            activity_type ENUM('call', 'email', 'meeting', 'note', 'task', 'demo', 'follow_up') DEFAULT 'call',
            subject VARCHAR(255) NOT NULL,
            description TEXT,
            status ENUM('scheduled', 'completed', 'cancelled', 'in_progress') DEFAULT 'scheduled',
            due_date TIMESTAMP NULL,
            completed_at TIMESTAMP NULL,
            duration_minutes INT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            FOREIGN KEY (customer_id) REFERENCES customers(id) ON DELETE SET NULL,
            FOREIGN KEY (contact_id) REFERENCES contacts(id) ON DELETE SET NULL,
            FOREIGN KEY (opportunity_id) REFERENCES opportunities(id) ON DELETE SET NULL,
            FOREIGN KEY (lead_id) REFERENCES leads(id) ON DELETE SET NULL,
            FOREIGN KEY (sales_rep_id) REFERENCES sales_representatives(id) ON DELETE CASCADE,
            INDEX idx_customer_id (customer_id),
            INDEX idx_contact_id (contact_id),
            INDEX idx_opportunity_id (opportunity_id),
            INDEX idx_lead_id (lead_id),
            INDEX idx_sales_rep_id (sales_rep_id),
            INDEX idx_activity_type (activity_type),
            INDEX idx_due_date (due_date)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """)
    print("✓ activities table created")
    
    # 10. invoices
    print("\nCreating table: invoices")
    cursor.execute("""
        CREATE TABLE invoices (
            id INT AUTO_INCREMENT PRIMARY KEY,
            customer_id INT NOT NULL,
            contract_id INT,
            invoice_number VARCHAR(50) UNIQUE NOT NULL,
            invoice_date DATE NOT NULL,
            due_date DATE,
            amount DECIMAL(20,2) NOT NULL,
            tax_amount DECIMAL(20,2) DEFAULT 0,
            total_amount DECIMAL(20,2) NOT NULL,
            status ENUM('draft', 'sent', 'paid', 'overdue', 'cancelled') DEFAULT 'draft',
            payment_method VARCHAR(100),
            payment_date DATE,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            FOREIGN KEY (customer_id) REFERENCES customers(id) ON DELETE CASCADE,
            FOREIGN KEY (contract_id) REFERENCES contracts(id) ON DELETE SET NULL,
            INDEX idx_customer_id (customer_id),
            INDEX idx_contract_id (contract_id),
            INDEX idx_invoice_number (invoice_number),
            INDEX idx_status (status),
            INDEX idx_invoice_date (invoice_date),
            INDEX idx_due_date (due_date)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """)
    print("✓ invoices table created")
    
    connection.commit()
    
    # Verify tables
    print("\n" + "=" * 60)
    print("Verifying Tables")
    print("=" * 60)
    
    cursor.execute("SHOW TABLES")
    tables = cursor.fetchall()
    print(f"\nTotal tables created: {len(tables)}")
    for table in tables:
        print(f"  ✓ {table[0]}")
    
    # Verify constraints
    print("\n" + "=" * 60)
    print("Verifying Foreign Key Constraints")
    print("=" * 60)
    
    cursor.execute("""
        SELECT TABLE_NAME, CONSTRAINT_NAME, REFERENCED_TABLE_NAME
        FROM information_schema.KEY_COLUMN_USAGE
        WHERE TABLE_SCHEMA = %s
        AND REFERENCED_TABLE_NAME IS NOT NULL
        ORDER BY TABLE_NAME, CONSTRAINT_NAME
    """, (os.getenv('MYSQL_DATABASE'),))
    
    constraints = cursor.fetchall()
    print(f"\nTotal foreign key constraints: {len(constraints)}")
    for constraint in constraints:
        print(f"  ✓ {constraint[0]}.{constraint[1]} -> {constraint[2]}")
    
    # Verify indexes
    print("\n" + "=" * 60)
    print("Verifying Indexes")
    print("=" * 60)
    
    cursor.execute("""
        SELECT TABLE_NAME, INDEX_NAME, COLUMN_NAME
        FROM information_schema.STATISTICS
        WHERE TABLE_SCHEMA = %s
        AND INDEX_NAME != 'PRIMARY'
        ORDER BY TABLE_NAME, INDEX_NAME
    """, (os.getenv('MYSQL_DATABASE'),))
    
    indexes = cursor.fetchall()
    print(f"\nTotal indexes (excluding primary keys): {len(indexes)}")
    for index in indexes:
        print(f"  ✓ {index[0]}.{index[1]} on {index[2]}")
    
    cursor.close()
    connection.close()
    
    print("\n" + "=" * 60)
    print("SCHEMA CREATION: COMPLETED")
    print("=" * 60)
    
    return True

if __name__ == "__main__":
    try:
        create_crm_schema()
        print("\n✓ All tables created successfully with constraints and indexes")
    except Exception as e:
        print(f"\n✗ Error creating schema: {e}")
        exit(1)
