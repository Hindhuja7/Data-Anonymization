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
