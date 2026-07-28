import asyncio
from typing import Dict, Any, Optional
from app.pipeline.controller import pipeline_controller
from app.pipeline.state import pipeline_state
from app.services.websocket_service import websocket_service
from app.core.logger import logger
from app.core.exceptions import PipelineException

class PipelineService:
    """Service for pipeline execution management"""
    
    async def start_pipeline(self, user_id: Optional[str] = None, database_config: Optional[dict] = None, target_table: Optional[str] = None) -> Dict[str, Any]:
        """Start pipeline execution with authoritative user-scoped configuration"""
        result = await pipeline_controller.start_pipeline(user_id=user_id, database_config=database_config, target_table=target_table)
        
        # Broadcast state update
        await websocket_service.broadcast_state()
        
        return result
    
    async def pause_pipeline(self) -> Dict[str, Any]:
        """Pause pipeline execution"""
        result = await pipeline_controller.pause_pipeline()
        
        # Broadcast state update
        await websocket_service.broadcast_state()
        
        return result
    
    async def resume_pipeline(self) -> Dict[str, Any]:
        """Resume pipeline execution"""
        result = await pipeline_controller.resume_pipeline()
        
        # Broadcast state update
        await websocket_service.broadcast_state()
        
        return result
    
    async def stop_pipeline(self, requested_run_id: Optional[str] = None) -> Dict[str, Any]:
        """Stop pipeline execution with run_id validation"""
        result = await pipeline_controller.stop_pipeline(requested_run_id=requested_run_id)
        
        # Broadcast state update
        await websocket_service.broadcast_state()
        
        return result

    async def pause_pipeline(self) -> Dict[str, Any]:
        """Pause active pipeline execution safely"""
        result = await pipeline_controller.pause_pipeline()
        await websocket_service.broadcast_state()
        return result

    async def resume_pipeline(self) -> Dict[str, Any]:
        """Resume user-paused pipeline on the SAME run_id"""
        result = await pipeline_controller.resume_pipeline()
        await websocket_service.broadcast_state()
        return result
    
    async def approve_pipeline(self) -> Dict[str, Any]:
        """Grant approval to resume pipeline"""
        result = await pipeline_controller.approve_pipeline()
        
        # Broadcast state update
        await websocket_service.broadcast_state()
        
        return result
    
    async def approve_validation(self) -> Dict[str, Any]:
        """Grant post-validation approval to write to destination DB"""
        result = await pipeline_controller.approve_validation()
        
        # Broadcast state update
        await websocket_service.broadcast_state()
        
        return result
    
    async def modify_and_reanonymize(self, modified_policy: Dict[str, Any]) -> Dict[str, Any]:
        """Modify policy and restart anonymization from step 8"""
        result = await pipeline_controller.modify_and_reanonymize(modified_policy)
        
        # Broadcast state update
        await websocket_service.broadcast_state()
        
        return result
    
    async def reset_pipeline(self) -> Dict[str, Any]:
        """Reset pipeline state"""
        result = await pipeline_controller.reset_pipeline()
        
        # Broadcast state update
        await websocket_service.broadcast_state()
        
        return result
    
    def get_pipeline_status(self) -> Dict[str, Any]:
        """Get current pipeline status"""
        return pipeline_controller.get_status()
    
    async def monitor_pipeline(self):
        """Monitor pipeline execution and broadcast updates"""
        last_status = pipeline_state.status
        last_step = pipeline_state.active_step
        
        while pipeline_state.is_running:
            # Check for status changes
            if pipeline_state.status != last_status:
                await websocket_service.broadcast_state()
                last_status = pipeline_state.status
            
            # Check for step changes
            if pipeline_state.active_step != last_step:
                await websocket_service.broadcast_step_update(
                    pipeline_state.active_step,
                    pipeline_state.status
                )
                last_step = pipeline_state.active_step
            
            # Broadcast state periodically
            await websocket_service.broadcast_state()
            
            # Wait before next check
            await asyncio.sleep(0.5)

# Global pipeline service instance
pipeline_service = PipelineService()
