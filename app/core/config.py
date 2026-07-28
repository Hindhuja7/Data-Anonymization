import os
from typing import Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    """Application configuration"""
    
    # Directory paths
    BASE_DIR: str = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    DIRECTORY: str = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    # File paths
    ANONYMIZATION_POLICY_PATH: str = os.path.join(DIRECTORY, "anonymization_policy.json")
    PII_POLICY_PATH: str = os.path.join(DIRECTORY, "pii_policy.json")
    COMPLIANCE_REPORT_PATH: str = os.path.join(DIRECTORY, "compliance_report.json")
    APPROVAL_PATH: str = os.path.join(DIRECTORY, "approval_granted.txt")
    SANDBOX_DB_PATH: str = os.path.join(DIRECTORY, "sandbox.db")
    
    # Pipeline configuration
    TOTAL_STEPS: int = 17
    BATCH_SIZE: int = 1000
    
    # API configuration
    API_TITLE: str = "DataVault AI - Enterprise Backend Server"
    API_VERSION: str = "1.0.0"
    
    # CORS configuration
    CORS_ORIGINS: list = ["*"]
    
    @classmethod
    def get_path(cls, *path_parts: str) -> str:
        """Get a path relative to the base directory"""
        return os.path.join(cls.DIRECTORY, *path_parts)

config = Config()
