import os
import sys
from dotenv import load_dotenv
from database_connector import DatabaseConnector
from anonymizer import Anonymizer
import pandas as pd
from sqlalchemy import text

load_dotenv()

# Source database configuration
conn = DatabaseConnector(
    database_type=os.getenv("SOURCE_DB_TYPE", "postgresql"),
    host=os.getenv("SOURCE_DB_HOST"),
    port=int(os.getenv("SOURCE_DB_PORT", 5432)),
    username=os.getenv("SOURCE_DB_USERNAME"),
    password=os.getenv("SOURCE_DB_PASSWORD"),
    database_name=os.getenv("SOURCE_DB_NAME")
)
engine = conn.connect()

# Initialize anonymizer
anonymizer = Anonymizer(
    redis_host=os.getenv("REDIS_HOST", "localhost"),
    redis_port=int(os.getenv("REDIS_PORT", 6379))
)

try:
    # Fetch 5 customer rows from source
    with engine.connect() as connection:
        query = text("""
            SELECT customer_id, first_name, last_name, full_name, email, phone, 
                   aadhaar, pan, address, city, state, pincode, date_of_birth, kyc_status
            FROM customers
            LIMIT 5
        """)
        result = connection.execute(query)
        rows = result.fetchall()
        columns = result.keys()
        
        df = pd.DataFrame(rows, columns=columns)
    
    print("=" * 80)
    print("BEFORE ANONYMIZATION (5 Customer Rows)")
    print("=" * 80)
    print(df.to_string(index=False))
    print()
    
    # Apply anonymization
    anonymized_df = df.copy()
    
    # Define columns to anonymize and their techniques
    columns_to_anonymize = {
        "first_name": ("FULL_NAME", "TOKENIZATION"),
        "last_name": ("FULL_NAME", "TOKENIZATION"),
        "full_name": ("FULL_NAME", "TOKENIZATION"),
        "email": ("EMAIL", "TOKENIZATION"),
        "phone": ("PHONE", "TOKENIZATION"),
        "aadhaar": ("AADHAAR", "MASKING"),
        "pan": ("PAN", "MASKING"),
        "address": ("ADDRESS", "TOKENIZATION"),
        "city": ("LOCATION", "TOKENIZATION"),
        "state": ("LOCATION", "TOKENIZATION"),
        "pincode": ("LOCATION", "TOKENIZATION"),
    }
    
    # Generate row indices for consistency
    row_indices = list(range(len(df)))
    
    for column_name, (pii_type, technique) in columns_to_anonymize.items():
        if column_name in df.columns:
            anonymized_values = anonymizer.anonymize_column(
                values=df[column_name].tolist(),
                pii_type=pii_type,
                technique=technique,
                column_name=column_name,
                table_name="customers",
                is_foreign_key=False,
                is_primary_key=False,
                row_indices=row_indices
            )
            anonymized_df[column_name] = anonymized_values
    
    print("=" * 80)
    print("AFTER ANONYMIZATION (5 Customer Rows)")
    print("=" * 80)
    print(anonymized_df.to_string(index=False))
    print()
    
    print("=" * 80)
    print("DETAILED COMPARISON")
    print("=" * 80)
    
    for idx in range(len(df)):
        print(f"\n--- Row {idx + 1} ---")
        print(f"BEFORE:")
        print(f"  first_name: {df.iloc[idx]['first_name']}")
        print(f"  last_name: {df.iloc[idx]['last_name']}")
        print(f"  full_name: {df.iloc[idx]['full_name']}")
        print(f"  email: {df.iloc[idx]['email']}")
        print(f"  phone: {df.iloc[idx]['phone']}")
        print(f"  aadhaar: {df.iloc[idx]['aadhaar']}")
        print(f"  pan: {df.iloc[idx]['pan']}")
        print(f"  address: {df.iloc[idx]['address']}")
        print(f"  city: {df.iloc[idx]['city']}")
        print(f"  state: {df.iloc[idx]['state']}")
        print(f"  pincode: {df.iloc[idx]['pincode']}")
        print(f"  date_of_birth: {df.iloc[idx]['date_of_birth']}")
        print(f"  kyc_status: {df.iloc[idx]['kyc_status']}")
        
        print(f"\nAFTER:")
        print(f"  first_name: {anonymized_df.iloc[idx]['first_name']}")
        print(f"  last_name: {anonymized_df.iloc[idx]['last_name']}")
        print(f"  full_name: {anonymized_df.iloc[idx]['full_name']}")
        print(f"  email: {anonymized_df.iloc[idx]['email']}")
        print(f"  phone: {anonymized_df.iloc[idx]['phone']}")
        print(f"  aadhaar: {anonymized_df.iloc[idx]['aadhaar']}")
        print(f"  pan: {anonymized_df.iloc[idx]['pan']}")
        print(f"  address: {anonymized_df.iloc[idx]['address']}")
        print(f"  city: {anonymized_df.iloc[idx]['city']}")
        print(f"  state: {anonymized_df.iloc[idx]['state']}")
        print(f"  pincode: {anonymized_df.iloc[idx]['pincode']}")
        print(f"  date_of_birth: {df.iloc[idx]['date_of_birth']}")
        print(f"  kyc_status: {df.iloc[idx]['kyc_status']}")
        
        # Verify consistency
        expected_full_name = f"{anonymized_df.iloc[idx]['first_name']} {anonymized_df.iloc[idx]['last_name']}"
        full_name_match = anonymized_df.iloc[idx]['full_name'] == expected_full_name
        print(f"\n✓ Name consistency: {'PASS' if full_name_match else 'FAIL'}")
        if not full_name_match:
            print(f"  Expected: {expected_full_name}")
            print(f"  Got: {anonymized_df.iloc[idx]['full_name']}")
        
        # Verify pincode is 6 digits
        pincode_is_numeric = anonymized_df.iloc[idx]['pincode'].isdigit() and len(anonymized_df.iloc[idx]['pincode']) == 6
        print(f"✓ Pincode format: {'PASS' if pincode_is_numeric else 'FAIL'}")
        
        # Verify phone has +91 prefix
        phone_has_prefix = str(anonymized_df.iloc[idx]['phone']).startswith("+91")
        print(f"✓ Phone format: {'PASS' if phone_has_prefix else 'FAIL'}")
        
        # Verify email format
        email_has_at = "@" in str(anonymized_df.iloc[idx]['email'])
        print(f"✓ Email format: {'PASS' if email_has_at else 'FAIL'}")
        
        # Verify city is not a random word
        city_is_valid = anonymized_df.iloc[idx]['city'] not in ['harum', 'sequi', 'temporibus', 'dolor', 'sit']
        print(f"✓ City is valid: {'PASS' if city_is_valid else 'FAIL'}")
        
        # Verify state is not a random word
        state_is_valid = anonymized_df.iloc[idx]['state'] not in ['harum', 'sequi', 'temporibus', 'dolor', 'sit']
        print(f"✓ State is valid: {'PASS' if state_is_valid else 'FAIL'}")
        
        # Verify date_of_birth unchanged
        dob_unchanged = df.iloc[idx]['date_of_birth'] == anonymized_df.iloc[idx]['date_of_birth']
        print(f"✓ DOB unchanged: {'PASS' if dob_unchanged else 'FAIL'}")
        
        # Verify kyc_status unchanged
        kyc_unchanged = df.iloc[idx]['kyc_status'] == anonymized_df.iloc[idx]['kyc_status']
        print(f"✓ KYC status unchanged: {'PASS' if kyc_unchanged else 'FAIL'}")

finally:
    conn.disconnect()
