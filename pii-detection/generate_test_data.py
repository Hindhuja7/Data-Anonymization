"""
Generate synthetic Indian enterprise dataset for PII detection testing.
Creates CSV files for import into Neon PostgreSQL.
"""

import pandas as pd
import random
import string
from faker import Faker
import os

# Initialize Faker with Indian locale
fake = Faker('en_IN')

# Configuration
NUM_CUSTOMERS = 100000
NUM_EMPLOYEES = 5000
NUM_ACCOUNTS = 150000
NUM_TRANSACTIONS = 500000

# Output directory
OUTPUT_DIR = "test_data"
os.makedirs(OUTPUT_DIR, exist_ok=True)


def generate_aadhaar():
    """Generate realistic Aadhaar number (12 digits)."""
    return f"{random.randint(1000, 9999)} {random.randint(1000, 9999)} {random.randint(1000, 9999)}"


def generate_pan():
    """Generate realistic PAN number (5 letters + 4 digits + 1 letter)."""
    letters = ''.join(random.choices(string.ascii_uppercase, k=5))
    digits = ''.join(random.choices(string.digits, k=4))
    last_letter = random.choice(string.ascii_uppercase)
    return f"{letters}{digits}{last_letter}"


def generate_indian_phone():
    """Generate Indian phone number (+91 followed by 10 digits starting with 6-9)."""
    return f"+91 {random.choice([6, 7, 8, 9])}{random.randint(100000000, 999999999)}"


def generate_gstin():
    """Generate GSTIN (15 characters)."""
    state_code = f"{random.randint(1, 37):02d}"
    pan = generate_pan()
    entity_code = random.choice(string.digits)
    alphabet = random.choice(string.ascii_uppercase)
    check_digit = random.choice(string.digits + string.ascii_uppercase)
    return f"{state_code}{pan}{entity_code}{alphabet}Z{check_digit}"


def generate_customers(n):
    """Generate customers table with Indian PII data."""
    print(f"Generating {n} customers...")
    
    data = []
    for i in range(n):
        customer_id = i + 1
        first_name = fake.first_name()
        last_name = fake.last_name()
        full_name = f"{first_name} {last_name}"
        email = fake.email()
        phone = generate_indian_phone()
        aadhaar = generate_aadhaar()
        pan = generate_pan()
        address = fake.address().replace('\n', ', ')
        city = fake.city()
        state = fake.state()
        pincode = fake.postcode()
        date_of_birth = fake.date_of_birth(minimum_age=18, maximum_age=80)
        kyc_status = random.choice(['verified', 'pending', 'rejected'])
        registration_date = fake.date_between(start_date='-5y', end_date='today')
        
        data.append({
            'customer_id': customer_id,
            'first_name': first_name,
            'last_name': last_name,
            'full_name': full_name,
            'email': email,
            'phone': phone,
            'aadhaar': aadhaar,
            'pan': pan,
            'address': address,
            'city': city,
            'state': state,
            'pincode': pincode,
            'date_of_birth': date_of_birth,
            'kyc_status': kyc_status,
            'registration_date': registration_date
        })
    
    df = pd.DataFrame(data)
    df.to_csv(f"{OUTPUT_DIR}/customers.csv", index=False)
    print(f"Customers saved to {OUTPUT_DIR}/customers.csv")
    return df


def generate_employees(n):
    """Generate employees table with salary and contact info."""
    print(f"Generating {n} employees...")
    
    data = []
    departments = ['Engineering', 'Sales', 'Marketing', 'HR', 'Finance', 'Operations', 'Customer Support']
    designations = ['Manager', 'Senior Developer', 'Developer', 'Analyst', 'Executive', 'Lead', 'Associate']
    
    for i in range(n):
        employee_id = i + 1
        first_name = fake.first_name()
        last_name = fake.last_name()
        full_name = f"{first_name} {last_name}"
        email = fake.email()
        phone = generate_indian_phone()
        personal_email = fake.email()
        personal_phone = generate_indian_phone()
        aadhaar = generate_aadhaar()
        pan = generate_pan()
        uan = f"{random.randint(100000000000, 999999999999)}"  # 12-digit UAN
        department = random.choice(departments)
        designation = random.choice(designations)
        salary = random.randint(300000, 2500000)  # Indian salary range
        joining_date = fake.date_between(start_date='-10y', end_date='today')
        address = fake.address().replace('\n', ', ')
        emergency_contact = generate_indian_phone()
        emergency_contact_name = fake.name()
        
        data.append({
            'employee_id': employee_id,
            'first_name': first_name,
            'last_name': last_name,
            'full_name': full_name,
            'email': email,
            'phone': phone,
            'personal_email': personal_email,
            'personal_phone': personal_phone,
            'aadhaar': aadhaar,
            'pan': pan,
            'uan': uan,
            'department': department,
            'designation': designation,
            'salary': salary,
            'joining_date': joining_date,
            'address': address,
            'emergency_contact': emergency_contact,
            'emergency_contact_name': emergency_contact_name
        })
    
    df = pd.DataFrame(data)
    df.to_csv(f"{OUTPUT_DIR}/employees.csv", index=False)
    print(f"Employees saved to {OUTPUT_DIR}/employees.csv")
    return df


def generate_accounts(n, customer_df):
    """Generate accounts table linked to customers."""
    print(f"Generating {n} accounts...")
    
    data = []
    account_types = ['Savings', 'Current', 'Fixed Deposit', 'Recurring Deposit']
    statuses = ['Active', 'Inactive', 'Dormant', 'Closed']
    
    customer_ids = customer_df['customer_id'].tolist()
    
    for i in range(n):
        account_id = i + 1
        customer_id = random.choice(customer_ids)
        account_number = f"{random.randint(1000000000, 9999999999)}"
        account_type = random.choice(account_types)
        balance = round(random.uniform(1000, 10000000), 2)
        status = random.choice(statuses)
        opening_date = fake.date_between(start_date='-5y', end_date='today')
        ifsc_code = f"{random.choice(string.ascii_uppercase)}{random.choice(string.ascii_uppercase)}{random.choice(string.ascii_uppercase)}{random.choice(string.ascii_uppercase)}0{random.randint(100000, 999999)}"
        branch_name = fake.company()
        gstin = generate_gstin() if account_type in ['Current', 'Fixed Deposit'] else None
        
        data.append({
            'account_id': account_id,
            'customer_id': customer_id,
            'account_number': account_number,
            'account_type': account_type,
            'balance': balance,
            'status': status,
            'opening_date': opening_date,
            'ifsc_code': ifsc_code,
            'branch_name': branch_name,
            'gstin': gstin
        })
    
    df = pd.DataFrame(data)
    # Convert balance to string with proper decimal formatting to avoid JSON inference
    df['balance'] = df['balance'].apply(lambda x: f"{x:.2f}")
    # Convert account_number to string to preserve leading zeros if any
    df['account_number'] = df['account_number'].astype(str)
    df.to_csv(f"{OUTPUT_DIR}/accounts.csv", index=False, quoting=1)  # Quote all non-numeric fields
    print(f"Accounts saved to {OUTPUT_DIR}/accounts.csv")
    return df


def generate_transactions(n, account_df):
    """Generate transactions table linked to accounts."""
    print(f"Generating {n} transactions...")
    
    data = []
    transaction_types = ['Credit', 'Debit', 'Transfer', 'Withdrawal', 'Deposit']
    categories = ['Salary', 'Shopping', 'Food', 'Transport', 'Utilities', 'Entertainment', 'Medical', 'Education', 'Transfer', 'Other']
    
    account_ids = account_df['account_id'].tolist()
    
    for i in range(n):
        transaction_id = i + 1
        account_id = random.choice(account_ids)
        transaction_type = random.choice(transaction_types)
        amount = round(random.uniform(100, 500000), 2)
        transaction_date = fake.date_time_between(start_date='-2y', end_date='now')
        category = random.choice(categories)
        description = fake.sentence()[:100]
        reference_number = f"{random.randint(100000000000, 999999999999)}"
        beneficiary_account = f"{random.randint(1000000000, 9999999999)}" if transaction_type in ['Transfer', 'Withdrawal'] else None
        beneficiary_name = fake.name() if transaction_type in ['Transfer', 'Withdrawal'] else None
        
        data.append({
            'transaction_id': transaction_id,
            'account_id': account_id,
            'transaction_type': transaction_type,
            'amount': amount,
            'transaction_date': transaction_date,
            'category': category,
            'description': description,
            'reference_number': reference_number,
            'beneficiary_account': beneficiary_account,
            'beneficiary_name': beneficiary_name
        })
    
    df = pd.DataFrame(data)
    # Convert amount to string with proper decimal formatting to avoid JSON inference
    df['amount'] = df['amount'].apply(lambda x: f"{x:.2f}")
    # Convert beneficiary_account to string
    df['beneficiary_account'] = df['beneficiary_account'].astype(str)
    df.to_csv(f"{OUTPUT_DIR}/transactions.csv", index=False, quoting=1)  # Quote all non-numeric fields
    print(f"Transactions saved to {OUTPUT_DIR}/transactions.csv")
    return df


def generate_schema_sql():
    """Generate SQL schema file for Neon import."""
    print("Generating SQL schema...")
    
    schema = """
-- Drop existing tables
DROP TABLE IF EXISTS transactions;
DROP TABLE IF EXISTS accounts;
DROP TABLE IF EXISTS employees;
DROP TABLE IF EXISTS customers;

-- Create customers table
CREATE TABLE customers (
    customer_id INTEGER PRIMARY KEY,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    full_name VARCHAR(200),
    email VARCHAR(255),
    phone VARCHAR(20),
    aadhaar VARCHAR(14),
    pan VARCHAR(10),
    address TEXT,
    city VARCHAR(100),
    state VARCHAR(100),
    pincode VARCHAR(10),
    date_of_birth DATE,
    kyc_status VARCHAR(20),
    registration_date DATE
);

-- Create employees table
CREATE TABLE employees (
    employee_id INTEGER PRIMARY KEY,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    full_name VARCHAR(200),
    email VARCHAR(255),
    phone VARCHAR(20),
    personal_email VARCHAR(255),
    personal_phone VARCHAR(20),
    aadhaar VARCHAR(14),
    pan VARCHAR(10),
    uan VARCHAR(12),
    department VARCHAR(100),
    designation VARCHAR(100),
    salary INTEGER,
    joining_date DATE,
    address TEXT,
    emergency_contact VARCHAR(20),
    emergency_contact_name VARCHAR(200)
);

-- Create accounts table
CREATE TABLE accounts (
    account_id INTEGER PRIMARY KEY,
    customer_id INTEGER,
    account_number BIGINT,
    account_type VARCHAR(50),
    balance NUMERIC(15, 2),
    status VARCHAR(20),
    opening_date DATE,
    ifsc_code VARCHAR(15),
    branch_name VARCHAR(200),
    gstin VARCHAR(20),
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
);

-- Create transactions table
CREATE TABLE transactions (
    transaction_id INTEGER PRIMARY KEY,
    account_id INTEGER,
    transaction_type VARCHAR(20),
    amount DECIMAL(15, 2),
    transaction_date TIMESTAMP,
    category VARCHAR(50),
    description TEXT,
    reference_number VARCHAR(15),
    beneficiary_account VARCHAR(20),
    beneficiary_name VARCHAR(200),
    FOREIGN KEY (account_id) REFERENCES accounts(account_id)
);

-- Create indexes for better performance
CREATE INDEX idx_accounts_customer_id ON accounts(customer_id);
CREATE INDEX idx_transactions_account_id ON transactions(account_id);
CREATE INDEX idx_transactions_date ON transactions(transaction_date);
CREATE INDEX idx_customers_email ON customers(email);
CREATE INDEX idx_customers_phone ON customers(phone);
CREATE INDEX idx_employees_email ON employees(email);
"""
    
    with open(f"{OUTPUT_DIR}/schema.sql", "w") as f:
        f.write(schema)
    
    print(f"Schema saved to {OUTPUT_DIR}/schema.sql")


def generate_import_instructions():
    """Generate instructions for importing data into Neon."""
    instructions = """
# Import Instructions for Neon PostgreSQL

## Prerequisites
1. Install PostgreSQL client tools
2. Have your Neon connection string ready

## Steps

### 1. Create the schema
```bash
psql "postgresql://username:password@ep-xxx.us-east-2.aws.neon.tech/neondb?sslmode=require" -f test_data/schema.sql
```

### 2. Import CSV files
```bash
# Import customers
psql "postgresql://username:password@ep-xxx.us-east-2.aws.neon.tech/neondb?sslmode=require" -c "\\COPY customers FROM 'test_data/customers.csv' DELIMITER ',' CSV HEADER"

# Import employees
psql "postgresql://username:password@ep-xxx.us-east-2.aws.neon.tech/neondb?sslmode=require" -c "\\COPY employees FROM 'test_data/employees.csv' DELIMITER ',' CSV HEADER"

# Import accounts
psql "postgresql://username:password@ep-xxx.us-east-2.aws.neon.tech/neondb?sslmode=require" -c "\\COPY accounts FROM 'test_data/accounts.csv' DELIMITER ',' CSV HEADER"

# Import transactions
psql "postgresql://username:password@ep-xxx.us-east-2.aws.neon.tech/neondb?sslmode=require" -c "\\COPY transactions FROM 'test_data/transactions.csv' DELIMITER ',' CSV HEADER"
```

### 3. Verify data
```bash
psql "postgresql://username:password@ep-xxx.us-east-2.aws.neon.tech/neondb?sslmode=require" -c "SELECT COUNT(*) FROM customers;"
psql "postgresql://username:password@ep-xxx.us-east-2.aws.neon.tech/neondb?sslmode=require" -c "SELECT COUNT(*) FROM employees;"
psql "postgresql://username:password@ep-xxx.us-east-2.aws.neon.tech/neondb?sslmode=require" -c "SELECT COUNT(*) FROM accounts;"
psql "postgresql://username:password@ep-xxx.us-east-2.aws.neon.tech/neondb?sslmode=require" -c "SELECT COUNT(*) FROM transactions;"
```

## Alternative: Use Neon Console
You can also import CSV files directly through the Neon Console:
1. Go to your Neon project
2. Navigate to SQL Editor
3. Use the IMPORT command or copy-paste CSV data
"""
    
    with open(f"{OUTPUT_DIR}/IMPORT_INSTRUCTIONS.md", "w") as f:
        f.write(instructions)
    
    print(f"Import instructions saved to {OUTPUT_DIR}/IMPORT_INSTRUCTIONS.md")


def main():
    """Main function to generate all test data."""
    print("=" * 70)
    print("Generating Synthetic Indian Enterprise Dataset")
    print("=" * 70)
    
    # Generate schema
    generate_schema_sql()
    
    # Generate tables
    customers_df = generate_customers(NUM_CUSTOMERS)
    employees_df = generate_employees(NUM_EMPLOYEES)
    accounts_df = generate_accounts(NUM_ACCOUNTS, customers_df)
    transactions_df = generate_transactions(NUM_TRANSACTIONS, accounts_df)
    
    # Generate import instructions
    generate_import_instructions()
    
    print("=" * 70)
    print("Data Generation Complete!")
    print("=" * 70)
    print(f"Customers: {NUM_CUSTOMERS:,} rows")
    print(f"Employees: {NUM_EMPLOYEES:,} rows")
    print(f"Accounts: {NUM_ACCOUNTS:,} rows")
    print(f"Transactions: {NUM_TRANSACTIONS:,} rows")
    print(f"\nAll files saved to: {OUTPUT_DIR}/")
    print(f"Schema: {OUTPUT_DIR}/schema.sql")
    print(f"Instructions: {OUTPUT_DIR}/IMPORT_INSTRUCTIONS.md")


if __name__ == "__main__":
    main()
