import json
import os
from typing import Dict, Any, Optional
from app.core.config import config
from app.core.logger import logger
from app.core.exceptions import PolicyException

class PolicyService:
    """Service for policy management and samples"""
    
    def __init__(self):
        self.policy_path = config.ANONYMIZATION_POLICY_PATH
        self.pii_policy_path = config.PII_POLICY_PATH
    
    def load_policy(self) -> Dict[str, Any]:
        """Load anonymization policy from file"""
        try:
            if not os.path.exists(self.policy_path):
                return {}
            
            with open(self.policy_path, 'r') as f:
                policy_data = json.load(f)
            
            logger.info("Anonymization policy loaded")
            return policy_data
            
        except Exception as e:
            logger.error(f"Failed to load policy: {e}")
            raise PolicyException(f"Failed to load policy: {e}")
    
    def update_policy(self, policy_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update and save anonymization policy"""
        try:
            # Calculate risk score based on policy
            risk_score = self._calculate_risk_score(policy_data)
            policy_data["overall_risk_score"] = risk_score
            
            with open(self.policy_path, 'w') as f:
                json.dump(policy_data, f, indent=2)

            from app.pipeline.state import pipeline_state
            pipeline_state.set("generated_policy", policy_data)
            pipeline_state.set("risk_score", risk_score)
            pipeline_state.set("privacy_score", max(0.0, round(100.0 - float(risk_score), 1)))
            
            logger.info(f"Policy updated with risk score: {risk_score}")
            return {
                "status": "success",
                "message": "Policy updated",
                "risk_score": risk_score
            }
            
        except Exception as e:
            logger.error(f"Failed to update policy: {e}")
            raise PolicyException(f"Failed to update policy: {e}")
    
    def load_pii_policy(self) -> Dict[str, Any]:
        """Load PII detection policy from file"""
        try:
            if not os.path.exists(self.pii_policy_path):
                return {}
            
            with open(self.pii_policy_path, 'r') as f:
                pii_policy = json.load(f)
            
            logger.info("PII policy loaded")
            return pii_policy
            
        except Exception as e:
            logger.error(f"Failed to load PII policy: {e}")
            raise PolicyException(f"Failed to load PII policy: {e}")
    
    def load_samples(self) -> Dict[str, Any]:
        """Load sample data for policy preview"""
        try:
            # Mock sample data - in production, this would come from database
            samples = {
                "tables": ["users", "orders", "products"],
                "sample_data": {
                    "users": [
                        {"id": 1, "name": "John Doe", "email": "john@example.com"},
                        {"id": 2, "name": "Jane Smith", "email": "jane@example.com"}
                    ]
                }
            }
            
            logger.info("Sample data loaded (mock)")
            return samples
            
        except Exception as e:
            logger.error(f"Failed to load samples: {e}")
            raise PolicyException(f"Failed to load samples: {e}")
    
    def _calculate_risk_score(self, policy: Dict[str, Any]) -> float:
        """Calculate risk score based on policy configuration"""
        # Simplified risk calculation
        risk_score = 0.0
        
        # Count sensitive columns
        sensitive_count = 0
        for table, columns in policy.get("tables", {}).items():
            for column, config in columns.items():
                if config.get("technique") != "none":
                    sensitive_count += 1
        
        # Base score on number of sensitive columns
        risk_score = min(100, sensitive_count * 2)
        
        return risk_score

# Global policy service instance
policy_service = PolicyService()
