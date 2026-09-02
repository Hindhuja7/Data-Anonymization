from fastapi import HTTPException, status

class DataVaultException(Exception):
    """Base exception for DataVault AI"""
    pass

class PipelineException(DataVaultException):
    """Pipeline execution exceptions"""
    pass

class DatabaseException(DataVaultException):
    """Database operation exceptions"""
    pass

class PolicyException(DataVaultException):
    """Policy management exceptions"""
    pass

class ReportException(DataVaultException):
    """Report generation exceptions"""
    pass

class WebSocketException(DataVaultException):
    """WebSocket connection exceptions"""
    pass

class ApprovalException(DataVaultException):
    """Approval workflow exceptions"""
    pass

def handle_exception(exc: Exception) -> HTTPException:
    """Convert custom exceptions to HTTP exceptions"""
    if isinstance(exc, HTTPException):
        return exc
    if isinstance(exc, PipelineException):
        return HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc)
        )
    elif isinstance(exc, DatabaseException):
        return HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(exc)}"
        )
    elif isinstance(exc, PolicyException):
        return HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Policy error: {str(exc)}"
        )
    elif isinstance(exc, ReportException):
        return HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Report generation error: {str(exc)}"
        )
    elif isinstance(exc, ApprovalException):
        return HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Approval error: {str(exc)}"
        )
    else:
        return HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(exc)}"
        )
