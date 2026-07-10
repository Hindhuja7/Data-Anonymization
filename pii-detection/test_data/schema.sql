
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
