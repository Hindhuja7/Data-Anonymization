
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
psql "postgresql://username:password@ep-xxx.us-east-2.aws.neon.tech/neondb?sslmode=require" -c "\COPY customers FROM 'test_data/customers.csv' DELIMITER ',' CSV HEADER"

# Import employees
psql "postgresql://username:password@ep-xxx.us-east-2.aws.neon.tech/neondb?sslmode=require" -c "\COPY employees FROM 'test_data/employees.csv' DELIMITER ',' CSV HEADER"

# Import accounts
psql "postgresql://username:password@ep-xxx.us-east-2.aws.neon.tech/neondb?sslmode=require" -c "\COPY accounts FROM 'test_data/accounts.csv' DELIMITER ',' CSV HEADER"

# Import transactions
psql "postgresql://username:password@ep-xxx.us-east-2.aws.neon.tech/neondb?sslmode=require" -c "\COPY transactions FROM 'test_data/transactions.csv' DELIMITER ',' CSV HEADER"
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
