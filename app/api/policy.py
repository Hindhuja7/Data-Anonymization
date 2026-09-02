from fastapi import APIRouter, HTTPException, Body
from typing import Dict, Any
from app.services.policy_service import policy_service
from app.core.exceptions import handle_exception

router = APIRouter(prefix="/api/policy", tags=["Policy"])

@router.get("/")
async def load_policy():
    """Load anonymization policy from file"""
    try:
        result = policy_service.load_policy()
        return result
    except Exception as e:
        raise handle_exception(e)

@router.put("/")
async def update_policy(policy_data: Dict[str, Any] = Body(...)):
    """Update and save anonymization policy"""
    try:
        result = policy_service.update_policy(policy_data)
        user_id = policy_data.get("user_id") or policy_data.get("policy_metadata", {}).get("user_id") or "lokinenihindhuja@gmail.com"
        tbl = policy_data.get("target_table") or policy_data.get("policy_metadata", {}).get("target_table", "customers")
        
        cols = policy_data.get("column_policies") or []
        tech_summary = []
        for c in cols:
            col_name = c.get("column_name") or c.get("name")
            tech = c.get("anonymization_technique") or "NO_CHANGE"
            if col_name and tech != "NO_CHANGE":
                tech_summary.append(f"{col_name} -> {tech}")
        
        tech_str = ", ".join(tech_summary) if tech_summary else "Standard Column Transformation Rules Applied"
        
        try:
            from app.services.audit_service import audit_service
            from app.pipeline.state import pipeline_state
            audit_service.log_event(
                user_id=user_id,
                action=f"[POLICY MODIFICATION SUCCESS] Modified PII techniques for table '{tbl}'",
                category="policy",
                level="info",
                step_name="Policy Engine",
                details=f"User '{user_id}' updated PII anonymization techniques for table '{tbl}': [{tech_str}]. Policy updated successfully.",
                run_id=pipeline_state.get("run_id") or "RUN_POLICY"
            )
        except Exception:
            pass
        return result
    except Exception as e:
        raise handle_exception(e)

@router.get("/pii")
async def load_pii_policy():
    """Load PII detection policy from file"""
    try:
        result = policy_service.load_pii_policy()
        return result
    except Exception as e:
        raise handle_exception(e)

@router.get("/samples")
async def load_samples():
    """Load sample data for policy preview"""
    try:
        result = policy_service.load_samples()
        return result
    except Exception as e:
        raise handle_exception(e)
