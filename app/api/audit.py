from typing import Optional
from fastapi import APIRouter, Query, HTTPException, Response
from app.services.audit_service import audit_service
from app.core.exceptions import handle_exception

router = APIRouter(tags=["Audit & Dashboard"])

@router.get("/api/audit/logs")
async def get_audit_logs(
    user_id: Optional[str] = Query(None),
    category: Optional[str] = Query("all"),
    level: Optional[str] = Query("all"),
    run_id: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    mode: str = Query("personal")
):
    """Fetch real-time user-scoped audit logs with optional filtering"""
    try:
        logs = audit_service.get_user_logs(
            user_id=user_id,
            category=category,
            level=level,
            run_id=run_id,
            search=search,
            mode=mode
        )
        return {
            "status": "success",
            "count": len(logs),
            "logs": logs
        }
    except Exception as e:
        raise handle_exception(e)

@router.get("/api/dashboard/stats")
async def get_dashboard_stats(
    user_id: Optional[str] = Query(None),
    mode: str = Query("personal")
):
    """Fetch dynamic dashboard KPIs, compliance health, and technique breakdown"""
    try:
        stats = audit_service.get_dashboard_stats(user_id=user_id, mode=mode)
        return {
            "status": "success",
            "stats": stats
        }
    except Exception as e:
        raise handle_exception(e)

@router.get("/api/audit/export")
async def export_audit_report(
    format: str = Query("json", regex="^(json|csv)$"),
    user_id: Optional[str] = Query(None)
):
    """Export complete audit trail as JSON or CSV compliance report"""
    try:
        logs = audit_service.get_user_logs(user_id=user_id)
        
        if format == "csv":
            import csv, io
            output = io.StringIO()
            writer = csv.writer(output)
            writer.writerow(["ID", "Timestamp", "User ID", "Run ID", "Step Index", "Step Name", "Category", "Level", "Action", "Details", "HMAC Hash"])
            for l in logs:
                writer.writerow([
                    l.get("id"), l.get("timestamp"), l.get("user_id"), l.get("run_id"),
                    l.get("step_index"), l.get("step_name"), l.get("category"), l.get("level"),
                    l.get("action"), l.get("details"), l.get("audit_hash")
                ])
            return Response(
                content=output.getvalue(),
                media_type="text/csv",
                headers={"Content-Disposition": "attachment; filename=datavault_audit_report.csv"}
            )
        else:
            import json
            return Response(
                content=json.dumps(logs, indent=2),
                media_type="application/json",
                headers={"Content-Disposition": "attachment; filename=datavault_audit_report.json"}
            )
    except Exception as e:
        raise handle_exception(e)
