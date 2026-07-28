from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.services.websocket_service import websocket_service
from app.services.pipeline_service import pipeline_service
from app.core.exceptions import handle_exception
import asyncio

router = APIRouter(prefix="/api/pipeline", tags=["WebSocket"])

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time pipeline updates"""
    try:
        await websocket_service.connect(websocket)
        
        # Start monitoring task
        monitor_task = asyncio.create_task(pipeline_service.monitor_pipeline())
        
        try:
            while True:
                # Keep connection alive and handle incoming messages
                data = await websocket.receive_text()
                # Handle client messages if needed
                await websocket.send_json({"received": data})
                
        except WebSocketDisconnect:
            websocket_service.disconnect(websocket)
            monitor_task.cancel()
            
    except Exception as e:
        websocket_service.disconnect(websocket)
        raise handle_exception(e)
