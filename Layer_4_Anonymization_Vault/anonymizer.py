"""
Data Anonymization Module

Implements various anonymization techniques for PII data:
- TOKENIZATION: Replace with realistic fake values
- MASKING: Replace sensitive characters with X
- HASHING: One-way hash for IDs
- DIFFERENTIAL_PRIVACY: Add statistical noise to numerical values

Integrated with Redis mapping system for:
- Consistent anonymization across tables (referential integrity)
- Application-side encryption before storage
- Crash safety via Redis AOF
"""

import hashlib
import random
import re
from typing import Any, Dict, List, Optional
from faker import Faker
import numpy as np
import sys
import os
_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _layer in ["Layer_1_Connection_Extraction", "Layer_2_Enterprise_Classification", "Layer_3_PII_Detection", "Layer_4_Anonymization_Vault"]:
    _path = os.path.join(_root, _layer)
    if _path not in sys.path:
        sys.path.insert(0, _path)

from redis_mapping import RedisMappingSystem


class Anonymizer:
    """
    Main anonymization class that applies various techniques to PII data.
    """
    
    def __init__(
        self,
        locale: str = "en_IN",
        redis_host: str = "localhost",
        redis_port: int = 6379,
        redis_db: int = 0,
        redis_password: Optional[str] = None
    ):
        """
        Initialize the anonymizer.
        
        Args:
            locale: Locale for Faker library (default: en_IN for India)
            redis_host: Redis host for mapping system
            redis_port: Redis port
            redis_db: Redis database number
            redis_password: Redis password
        """
        self.faker = Faker(locale)
        Faker.seed(12345)  # For reproducible results
        
        # Initialize Redis mapping system
        self.redis_mapping = RedisMappingSystem(
            host=redis_host,
            port=redis_port,
            db=redis_db,
            password=redis_password
        )
    
    def anonymize_column(
        self,
        values: List[Any],
        pii_type: Optional[str],
        technique: str,
        column_name: Optional[str] = None,
        table_name: Optional[str] = None,
        is_foreign_key: bool = False,
        is_primary_key: bool = False
    ) -> List[Any]:
        """
        Anonymize a column of values based on PII type and technique.
        
        Args:
            values: List of values to anonymize
            pii_type: Type of PII (FULL_NAME, EMAIL, AADHAAR, etc.)
            technique: Anonymization technique (TOKENIZATION, MASKING, HASHING, etc.)
            column_name: Name of the column (for context)
            table_name: Name of the table (for Redis mapping)
            is_foreign_key: Whether column is a foreign key (for global mapping)
            is_primary_key: Whether column is a primary key (for global mapping)
        
        Returns:
            List of anonymized values
        """
        if technique.upper() == "NO_CHANGE":
            return values
        
        if technique.upper() == "TOKENIZATION":
            return self._tokenize(values, pii_type, column_name, table_name, is_foreign_key, is_primary_key)
        
        elif technique.upper() == "MASKING":
            return self._mask(values, pii_type, column_name, table_name, is_foreign_key, is_primary_key)
        
        elif technique.upper() == "HASHING":
            return self._hash(values, column_name, table_name, is_foreign_key, is_primary_key)
        
        elif technique.upper() == "DIFFERENTIAL_PRIVACY":
            return self._add_differential_privacy(values, pii_type, column_name)
        
        elif technique.upper() == "PSEUDONYMIZATION":
            return self._pseudonymize(values, pii_type, column_name, table_name, is_foreign_key, is_primary_key)
        
        elif technique.upper() == "GENERALIZATION":
            return self._generalize(values, pii_type, column_name)
        
        elif technique.upper() == "REDACTION":
            return self._redact(values, pii_type, column_name)
        
        else:
            # Unknown technique, return original
            return values
    
    def _tokenize(
        self,
        values: List[Any],
        pii_type: Optional[str],
        column_name: Optional[str],
        table_name: Optional[str] = None,
        is_foreign_key: bool = False,
        is_primary_key: bool = False
    ) -> List[Any]:
        """
        Replace values with realistic fake values using Faker with Redis mapping.
        
        Args:
            values: List of values to tokenize
            pii_type: Type of PII
            column_name: Name of the column
            table_name: Name of the table
            is_foreign_key: Whether column is a foreign key (for global mapping)
            is_primary_key: Whether column is a primary key (for global mapping)
        
        Returns:
            List of tokenized values
        """
        tokenized = []
        
        # Use schema-based detection for global mapping (not keyword-based)
        needs_global_mapping = is_foreign_key or is_primary_key
        
        for value in values:
            if value is None or value == "":
                tokenized.append(value)
                continue
            
            # Check Redis for existing mapping
            if needs_global_mapping and table_name:
                existing_mapping = self.redis_mapping.get_global_mapping(column_name, value)
                if existing_mapping:
                    tokenized.append(existing_mapping)
                    continue
            elif table_name:
                existing_mapping = self.redis_mapping.get_mapping(table_name, column_name, value)
                if existing_mapping:
                    tokenized.append(existing_mapping)
                    continue
            
            # Generate new fake value
            if pii_type == "FULL_NAME" or column_name in ["first_name", "last_name", "full_name", "emergency_contact_name", "beneficiary_name"]:
                if column_name == "first_name":
                    fake_value = self.faker.first_name()
                elif column_name == "last_name":
                    fake_value = self.faker.last_name()
                else:
                    fake_value = self.faker.name()
            
            elif pii_type == "EMAIL" or "email" in column_name.lower():
                fake_value = self.faker.email()
            
            elif pii_type == "INDIAN_PHONE" or "phone" in column_name.lower() or "contact" in column_name.lower():
                fake_value = self.faker.phone_number()
            
            elif pii_type == "ADDRESS" or "address" in column_name.lower():
                fake_value = self.faker.address()
            
            else:
                # Default: generate a fake value of the same type
                if isinstance(value, str):
                    fake_value = self.faker.word()
                else:
                    fake_value = value
            
            # Store in Redis for consistency
            if needs_global_mapping and table_name:
                self.redis_mapping.set_global_mapping(column_name, value, fake_value)
            elif table_name:
                self.redis_mapping.set_mapping(table_name, column_name, value, fake_value)
            
            tokenized.append(fake_value)
        
        return tokenized
    
    def _mask(
        self,
        values: List[Any],
        pii_type: Optional[str],
        column_name: Optional[str],
        table_name: Optional[str] = None,
        is_foreign_key: bool = False,
        is_primary_key: bool = False
    ) -> List[Any]:
        """
        Mask sensitive characters with X with Redis mapping.
        
        Args:
            values: List of values to mask
            pii_type: Type of PII
            column_name: Name of the column
            table_name: Name of the table
            is_foreign_key: Whether column is a foreign key (for global mapping)
            is_primary_key: Whether column is a primary key (for global mapping)
        
        Returns:
            List of masked values
        """
        masked = []
        
        # Use schema-based detection for global mapping (not keyword-based)
        needs_global_mapping = is_foreign_key or is_primary_key
        
        for value in values:
            if value is None or value == "":
                masked.append(value)
                continue
            
            value_str = str(value)
            
            # Check Redis for existing mapping
            if needs_global_mapping and table_name:
                existing_mapping = self.redis_mapping.get_global_mapping(column_name, value)
                if existing_mapping:
                    masked.append(existing_mapping)
                    continue
            elif table_name:
                existing_mapping = self.redis_mapping.get_mapping(table_name, column_name, value)
                if existing_mapping:
                    masked.append(existing_mapping)
                    continue
            
            # Remove spaces and dashes for processing
            clean_value = re.sub(r'[\s-]', '', value_str)
            
            if pii_type == "AADHAAR" or "aadhaar" in column_name.lower():
                # Aadhaar: 12 digits, mask last 4
                if len(clean_value) >= 4:
                    masked_value = clean_value[:-4] + "XXXX"
                    # Preserve original formatting
                    if " " in value_str:
                        masked_value = " ".join([masked_value[i:i+4] for i in range(0, len(masked_value), 4)])
                else:
                    masked_value = "X" * len(clean_value)
            
            elif pii_type == "PAN" or "pan" in column_name.lower():
                # PAN: 10 characters (5 letters + 4 digits + 1 letter), mask last 4
                if len(clean_value) >= 4:
                    masked_value = clean_value[:-4] + "XXXX"
                else:
                    masked_value = "X" * len(clean_value)
            
            elif pii_type == "GSTIN" or "gstin" in column_name.lower():
                # GSTIN: 15 characters, mask last 5
                if len(clean_value) >= 5:
                    masked_value = clean_value[:-5] + "XXXXX"
                else:
                    masked_value = "X" * len(clean_value)
            
            elif pii_type == "CREDIT_CARD" or "credit" in column_name.lower():
                # Credit card: mask all but last 4
                if len(clean_value) >= 4:
                    masked_value = "X" * (len(clean_value) - 4) + clean_value[-4:]
                else:
                    masked_value = "X" * len(clean_value)
            
            elif pii_type == "BANK_ACCOUNT" or "account" in column_name.lower():
                # Bank account: mask all but last 4
                if len(clean_value) >= 4:
                    masked_value = "X" * (len(clean_value) - 4) + clean_value[-4:]
                else:
                    masked_value = "X" * len(clean_value)
            
            elif pii_type == "DRIVING_LICENSE" or "license" in column_name.lower():
                # Driving license: mask last 4
                if len(clean_value) >= 4:
                    masked_value = clean_value[:-4] + "XXXX"
                else:
                    masked_value = "X" * len(clean_value)
            
            elif pii_type == "UAN" or "uan" in column_name.lower():
                # UAN: 12 digits, mask last 4
                if len(clean_value) >= 4:
                    masked_value = clean_value[:-4] + "XXXX"
                else:
                    masked_value = "X" * len(clean_value)
            
            else:
                # Default: mask all characters
                masked_value = "X" * len(value_str)
            
            # Store in Redis for consistency
            if needs_global_mapping and table_name:
                self.redis_mapping.set_global_mapping(column_name, value, masked_value)
            elif table_name:
                self.redis_mapping.set_mapping(table_name, column_name, value, masked_value)
            
            masked.append(masked_value)
        
        return masked
    
    def _hash(
        self,
        values: List[Any],
        column_name: Optional[str],
        table_name: Optional[str] = None,
        is_foreign_key: bool = False,
        is_primary_key: bool = False
    ) -> List[Any]:
        """
        Apply one-way hash to values with Redis mapping for consistency.
        
        Args:
            values: List of values to hash
            column_name: Name of the column
            table_name: Name of the table
            is_foreign_key: Whether column is a foreign key (for global mapping)
            is_primary_key: Whether column is a primary key (for global mapping)
        
        Returns:
            List of hashed values
        """
        hashed = []
        
        # Use schema-based detection for global mapping (not keyword-based)
        needs_global_mapping = is_foreign_key or is_primary_key
        
        for value in values:
            if value is None or value == "":
                hashed.append(value)
                continue
            
            # Check Redis for existing mapping
            if needs_global_mapping and table_name:
                # Use global mapping for foreign keys and primary keys (cross-table consistency)
                existing_mapping = self.redis_mapping.get_global_mapping(column_name, value)
                if existing_mapping:
                    hashed.append(existing_mapping)
                    continue
            
            # Generate new hash
            hash_value = hashlib.sha256(str(value).encode()).hexdigest()
            
            # Store in Redis for consistency
            if needs_global_mapping and table_name:
                self.redis_mapping.set_global_mapping(column_name, value, hash_value)
            elif table_name:
                self.redis_mapping.set_mapping(table_name, column_name, value, hash_value)
            
            hashed.append(hash_value)
        
        return hashed
    
    def _add_differential_privacy(
        self,
        values: List[Any],
        pii_type: Optional[str],
        column_name: Optional[str]
    ) -> List[Any]:
        """
        Add statistical noise to numerical values for differential privacy.
        
        Args:
            values: List of values to add noise to
            pii_type: Type of PII
            column_name: Name of the column
        
        Returns:
            List of values with added noise
        """
        noisy_values = []
        
        # Convert to float for processing
        numeric_values = []
        for value in values:
            if value is None or value == "":
                numeric_values.append(None)
            else:
                try:
                    numeric_values.append(float(value))
                except (ValueError, TypeError):
                    numeric_values.append(None)
        
        # Calculate standard deviation for noise scaling
        valid_values = [v for v in numeric_values if v is not None]
        if valid_values:
            std_dev = np.std(valid_values)
            noise_scale = std_dev * 0.1  # 10% of standard deviation
        else:
            noise_scale = 1.0  # Default noise scale
        
        for value in numeric_values:
            if value is None:
                noisy_values.append(None)
                continue
            
            # Add Laplacian noise
            noise = np.random.laplace(0, noise_scale)
            noisy_value = value + noise
            
            # Round to appropriate precision
            if pii_type == "FINANCIAL" or "salary" in column_name.lower() or "balance" in column_name.lower() or "amount" in column_name.lower():
                noisy_value = round(noisy_value, 2)
            elif "age" in column_name.lower():
                noisy_value = max(0, round(noisy_value))  # Age can't be negative
            else:
                noisy_value = round(noisy_value)
            
            noisy_values.append(noisy_value)
        
        return noisy_values
    
    def _pseudonymize(
        self,
        values: List[Any],
        pii_type: Optional[str],
        column_name: Optional[str],
        table_name: Optional[str] = None,
        is_foreign_key: bool = False,
        is_primary_key: bool = False
    ) -> List[Any]:
        """
        Replace with consistent pseudonyms using Redis mapping (same input → same output).
        
        Args:
            values: List of values to pseudonymize
            pii_type: Type of PII
            column_name: Name of the column
            table_name: Name of the table
            is_foreign_key: Whether column is a foreign key (for global mapping)
            is_primary_key: Whether column is a primary key (for global mapping)
        
        Returns:
            List of pseudonymized values
        """
        pseudonymized = []
        
        # Use schema-based detection for global mapping (not keyword-based)
        needs_global_mapping = is_foreign_key or is_primary_key
        
        for value in values:
            if value is None or value == "":
                pseudonymized.append(value)
                continue
            
            # Check Redis for existing mapping
            if needs_global_mapping and table_name:
                existing_mapping = self.redis_mapping.get_global_mapping(column_name, value)
                if existing_mapping:
                    pseudonymized.append(existing_mapping)
                    continue
            elif table_name:
                existing_mapping = self.redis_mapping.get_mapping(table_name, column_name, value)
                if existing_mapping:
                    pseudonymized.append(existing_mapping)
                    continue
            
            # Generate a new pseudonym
            if pii_type == "FULL_NAME" or "name" in column_name.lower():
                fake_value = self.faker.name()
            elif pii_type == "EMAIL" or "email" in column_name.lower():
                fake_value = self.faker.email()
            else:
                fake_value = self.faker.word()
            
            # Store in Redis for consistency
            if needs_global_mapping and table_name:
                self.redis_mapping.set_global_mapping(column_name, value, fake_value)
            elif table_name:
                self.redis_mapping.set_mapping(table_name, column_name, value, fake_value)
            
            pseudonymized.append(fake_value)
        
        return pseudonymized
    
    def _generalize(
        self,
        values: List[Any],
        pii_type: Optional[str],
        column_name: Optional[str]
    ) -> List[Any]:
        """
        Generalize values to broader categories.
        
        Args:
            values: List of values to generalize
            pii_type: Type of PII
            column_name: Name of the column
        
        Returns:
            List of generalized values
        """
        generalized = []
        
        for value in values:
            if value is None or value == "":
                generalized.append(value)
                continue
            
            value_str = str(value)
            
            if column_name in ["city", "state"] or pii_type == "ADDRESS":
                # For city/state, replace with "CITY" or "STATE"
                if column_name == "city":
                    generalized.append("CITY")
                elif column_name == "state":
                    generalized.append("STATE")
                else:
                    generalized.append("LOCATION")
            
            elif column_name == "pincode" or "pincode" in column_name.lower():
                # For pincode, generalize to first 3 digits (region)
                if len(value_str) >= 3:
                    generalized.append(value_str[:3] + "XXX")
                else:
                    generalized.append("XXXXXX")
            
            elif pii_type == "DATE_OF_BIRTH" or "date_of_birth" in column_name.lower() or "dob" in column_name.lower():
                # For date of birth, generalize to year only
                if len(value_str) >= 4:
                    generalized.append(value_str[:4] + "-XX-XX")
                else:
                    generalized.append("XXXX-XX-XX")
            
            else:
                # Default: replace with category name
                generalized.append("GENERALIZED")
        
        return generalized
    
    def _redact(
        self,
        values: List[Any],
        pii_type: Optional[str],
        column_name: Optional[str]
    ) -> List[Any]:
        """
        Completely redact values (replace with REDACTED).
        
        Args:
            values: List of values to redact
            pii_type: Type of PII
            column_name: Name of the column
        
        Returns:
            List of redacted values
        """
        redacted = []
        
        for value in values:
            if value is None or value == "":
                redacted.append(value)
            else:
                redacted.append("REDACTED")
        
        return redacted


def anonymize_dataframe(
    data: Dict[str, List[Any]],
    pii_report: Dict[str, Any]
) -> Dict[str, List[Any]]:
    """
    Anonymize a complete dataframe based on PII detection report.
    
    Args:
        data: Dictionary with column names as keys and lists of values
        pii_report: PII detection report from database_pii_detection
    
    Returns:
        Dictionary with anonymized data
    """
    anonymizer = Anonymizer()
    anonymized_data = {}
    
    # Copy all columns initially
    for column_name, values in data.items():
        anonymized_data[column_name] = values.copy()
    
    # Apply anonymization based on PII report
    for table in pii_report.get("tables", []):
        for column_info in table.get("columns", []):
            column_name = column_info["column_name"]
            technique = column_info.get("recommended_technique", "NO_CHANGE")
            pii_type = column_info.get("pii_type")
            
            if column_name in anonymized_data and technique != "NO_CHANGE":
                anonymized_data[column_name] = anonymizer.anonymize_column(
                    values=anonymized_data[column_name],
                    pii_type=pii_type,
                    technique=technique,
                    column_name=column_name
                )
    
    return anonymized_data


if __name__ == "__main__":
    # Test the anonymizer
    anonymizer = Anonymizer()
    
    # Test TOKENIZATION
    names = ["John Doe", "Jane Smith", "Bob Johnson"]
    tokenized_names = anonymizer._tokenize(names, "FULL_NAME", "full_name")
    print(f"TOKENIZATION (names): {tokenized_names}")
    
    # Test MASKING
    aadhaars = ["4521 8834 9021", "5192 8374 6102", "6283 9475 3102"]
    masked_aadhaars = anonymizer._mask(aadhaars, "AADHAAR", "aadhaar")
    print(f"MASKING (aadhaar): {masked_aadhaars}")
    
    # Test HASHING
    ids = ["user_123", "user_456", "user_789"]
    hashed_ids = anonymizer._hash(ids, "customer_id")
    print(f"HASHING (ids): {hashed_ids}")
    
    # Test DIFFERENTIAL_PRIVACY
    salaries = [45000, 78000, 92000]
    noisy_salaries = anonymizer._add_differential_privacy(salaries, "FINANCIAL", "salary")
    print(f"DIFFERENTIAL_PRIVACY (salary): {noisy_salaries}")
    
    # Test GENERALIZATION
    pincodes = ["600001", "600002", "600003"]
    generalized_pincodes = anonymizer._generalize(pincodes, "ADDRESS", "pincode")
    print(f"GENERALIZATION (pincode): {generalized_pincodes}")
