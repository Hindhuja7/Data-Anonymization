from typing import Optional, Dict, Any

class TrafficSimulationPayload(dict):
    def __init__(
        self,
        operation: str = "INSERT",
        target_table: Optional[str] = None,
        record_id: Optional[Any] = None,
        custom_data: Optional[Dict[str, Any]] = None,
        user_id: Optional[str] = None,
        **kwargs
    ):
        super().__init__(
            operation=operation,
            target_table=target_table,
            record_id=record_id,
            custom_data=custom_data,
            user_id=user_id,
            **kwargs
        )
        self.operation = operation
        self.target_table = target_table
        self.record_id = record_id
        self.custom_data = custom_data
        self.user_id = user_id
