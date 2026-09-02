import re
from typing import Optional, Dict, Any
from app.core.logger import logger

class LogParser:
    """Parses 17-step pipeline execution logs to extract step information and metrics"""
    
    @staticmethod
    def get_step_from_log(line: str) -> Optional[int]:
        """Determine current pipeline step from log line (17-step format)"""
        step_mapping = {
            # 17-step DataVault AI pipeline
            "Connect Database": 1,
            "Extract Schema": 2,
            "Enterprise Detection": 3,
            "Privacy-Safe Sampling": 4,
            "PII Detection": 5,
            "Policy Generation": 6,
            "Admin Approval": 7,
            "WAITING": 7,  # Waiting for admin approval
            "Change Detection": 8,
            "Redis Hash Vault": 9,
            "Crash Recovery": 10,
            "Chunk Processing": 11,
            "Data Anonymization": 12,
            "Batch Loading": 13,
            "Validation Approval": 14,
            "Safe Database Generation": 15,
            "Audit Report": 16,
            "Output Delivery": 17,
            
            # Legacy patterns for backward compatibility
            "Loading and validating policy": 6,
            "Connecting to databases": 1,
            "Extracting source schema": 2,
            "Determining table processing order": 2,
            "Analyzing PK/FK relationships": 2,
            "Creating destination schema": 15,
            "Validating destination schema": 15,
            "Processing table": 11,
            "Initialize Redis mapping": 9,
            "Chunk:": 11,
            "Processed:": 13,
            "to_sql": 13,
            "append": 13,
            "batch": 13,
            "Validating results": 14,
            "Validation passed": 14,
            "Validation Engine": 14,
            "Generating Audit & Compliance Report": 16,
            "EXECUTION COMPLETED SUCCESSFULLY": 17,
            "EXECUTION COMPLETED": 17,
            "17-STEP PIPELINE COMPLETED": 17
        }
        
        for pattern, step in step_mapping.items():
            if pattern in line:
                return step
        
        return None
    
    @staticmethod
    def extract_records_processed(line: str) -> Optional[int]:
        """Extract number of records processed from log line"""
        # Pattern: "Processed: 12345 rows"
        match = re.search(r'Processed:\s*(\d+)\s*rows?', line)
        if match:
            return int(match.group(1))
        return None
    
    @staticmethod
    def extract_batch_info(line: str) -> Optional[Dict[str, Any]]:
        """Extract batch information from log line"""
        # Pattern: "Chunk: 123/456" or "batch 123"
        chunk_match = re.search(r'Chunk:\s*(\d+)/(\d+)', line)
        if chunk_match:
            return {
                "current_chunk": int(chunk_match.group(1)),
                "total_chunks": int(chunk_match.group(2))
            }
        
        batch_match = re.search(r'batch\s*(\d+)', line, re.IGNORECASE)
        if batch_match:
            return {"batch_number": int(batch_match.group(1))}
        
        return None
    
    @staticmethod
    def extract_table_name(line: str) -> Optional[str]:
        """Extract table name from log line"""
        # Pattern: "Processing table: users" or "table users"
        match = re.search(r'(?:Processing|table)\s*[:]\s*(\w+)', line, re.IGNORECASE)
        if match:
            return match.group(1)
        return None
    
    @staticmethod
    def extract_progress(line: str) -> Optional[float]:
        """Extract progress percentage from log line"""
        # Pattern: "Progress: 45%" or "45% complete"
        match = re.search(r'(\d+)%', line)
        if match:
            return float(match.group(1))
        return None
    
    @staticmethod
    def parse_log_line(line: str) -> Dict[str, Any]:
        """Parse a single log line and extract all available information"""
        result = {
            "step": LogParser.get_step_from_log(line),
            "records_processed": LogParser.extract_records_processed(line),
            "batch_info": LogParser.extract_batch_info(line),
            "table_name": LogParser.extract_table_name(line),
            "progress": LogParser.extract_progress(line),
            "raw_line": line
        }
        
        logger.debug(f"Parsed log line: {result}")
        return result

log_parser = LogParser()
