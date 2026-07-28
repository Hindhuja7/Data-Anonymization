from fastapi import APIRouter, HTTPException
from app.services.report_service import report_service
from app.core.exceptions import handle_exception

router = APIRouter(prefix="/api/reports", tags=["Reports"])

@router.get("/pdf")
async def generate_pdf_report():
    """Generate PDF compliance report"""
    try:
        result = report_service.generate_pdf_report()
        return result
    except Exception as e:
        raise handle_exception(e)

@router.get("/csv")
async def generate_csv_report():
    """Generate CSV compliance report"""
    try:
        result = report_service.generate_csv_report()
        return result
    except Exception as e:
        raise handle_exception(e)

@router.get("/sql")
async def generate_sql_report():
    """Generate SQL compliance report"""
    try:
        result = report_service.generate_sql_report()
        return result
    except Exception as e:
        raise handle_exception(e)

@router.get("/txt")
async def generate_txt_report():
    """Generate TXT compliance report"""
    try:
        result = report_service.generate_txt_report()
        return result
    except Exception as e:
        raise handle_exception(e)
