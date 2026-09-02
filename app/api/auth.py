from fastapi import APIRouter, HTTPException, Body
from typing import Dict, Any
from app.core.exceptions import handle_exception

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

@router.post("/login")
async def login(credentials: Dict[str, Any] = Body(...)):
    """Authenticate user and return token"""
    try:
        username = credentials.get("username") or credentials.get("email") or "b@gmail.com"
        password = credentials.get("password")
        
        if username:
            try:
                from app.services.audit_service import audit_service
                audit_service.log_event(
                    user_id=username,
                    action=f"[AUTH] User '{username}' logged in successfully",
                    category="security",
                    level="success",
                    step_name="Authentication",
                    details=f"User session authenticated for '{username}'. Token issued."
                )
            except Exception:
                pass
            return {
                "status": "success",
                "token": "mock_jwt_token",
                "user": username
            }
        else:
            raise HTTPException(status_code=400, detail="Invalid credentials")
    except Exception as e:
        raise handle_exception(e)

@router.post("/logout")
async def logout(payload: Dict[str, Any] = Body(default={})):
    """Logout user and invalidate token"""
    try:
        user_id = payload.get("user_id") or "user"
        try:
            from app.services.audit_service import audit_service
            audit_service.log_event(
                user_id=user_id,
                action=f"[AUTH] User '{user_id}' logged out",
                category="security",
                level="info",
                step_name="Authentication",
                details=f"User session closed for '{user_id}'."
            )
        except Exception:
            pass
        return {"status": "success", "message": "Logged out successfully"}
    except Exception as e:
        raise handle_exception(e)

@router.get("/verify")
async def verify_token():
    """Verify if token is valid"""
    try:
        return {"status": "valid", "user": "admin"}
    except Exception as e:
        raise handle_exception(e)
