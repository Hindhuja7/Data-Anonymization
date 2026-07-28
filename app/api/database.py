from fastapi import APIRouter, HTTPException, Body, Header, Query
from typing import Dict, Any, Optional
from app.services.database_service import database_service
from app.services.pipeline_service import pipeline_service
from app.core.exceptions import handle_exception

router = APIRouter(prefix="/api/database", tags=["Database"])

@router.post("/test")
async def test_connection(config_data: Dict[str, Any] = Body(...)):
    """Test database connection with provided configuration"""
    try:
        result = database_service.test_connection(config_data)
        return result
    except Exception as e:
        raise handle_exception(e)

@router.post("/inspect")
async def inspect_database(config_data: Dict[str, Any] = Body(...)):
    """Inspect database schema, total tables, records, and columns dynamically"""
    try:
        result = database_service.inspect_database(config_data)
        return result
    except Exception as e:
        raise handle_exception(e)

@router.post("/config")
async def save_configuration(
    config_data: Dict[str, Any] = Body(...),
    x_user_id: Optional[str] = Header(None, alias="X-User-ID"),
    user_id: Optional[str] = Query(None)
):
    """Save user-scoped database configuration to file and start pipeline automatically"""
    try:
        uid = x_user_id or user_id or config_data.get("user_id")
        result = database_service.save_configuration(config_data, user_id=uid)
        
        if result.get("status") in ["success", "configured"]:
            selected_table = config_data.get("target_table")
            start_res = await pipeline_service.start_pipeline(
                user_id=uid,
                database_config=config_data,
                target_table=selected_table
            )
            
            from app.pipeline.state import pipeline_state
            actual_run_id = start_res.get("run_id") or pipeline_state.get("run_id")
            actual_target_table = start_res.get("target_table") or selected_table or pipeline_state.get("target_table")
            
            result["status"] = "configured"
            result["pipeline_started"] = True
            result["run_id"] = actual_run_id
            result["target_table"] = actual_target_table
            result["message"] = "Database configured successfully. Pipeline execution started automatically."
            
        return result
    except Exception as e:
        raise handle_exception(e)

@router.get("/config")
async def load_configuration(
    x_user_id: Optional[str] = Header(None, alias="X-User-ID"),
    user_id: Optional[str] = Query(None)
):
    """Load user-scoped database configuration"""
    try:
        uid = x_user_id or user_id
        result = database_service.load_configuration(user_id=uid)
        return result
    except Exception as e:
        raise handle_exception(e)

@router.delete("/config")
async def delete_configuration(
    x_user_id: Optional[str] = Header(None, alias="X-User-ID"),
    user_id: Optional[str] = Query(None)
):
    """Delete user-scoped database configuration file"""
    try:
        uid = x_user_id or user_id
        result = database_service.delete_configuration(user_id=uid)
        return result
    except Exception as e:
        raise handle_exception(e)
