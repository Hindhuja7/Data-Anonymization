"""
Lightweight, read-only ValidationContext holding database connectors, schema metadata, and execution settings.
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional

@dataclass(frozen=True)
class ValidationContext:
    source_connector: Any
    destination_connector: Any
    policy: Dict[str, Any]
    source_schema: Dict[str, Any]
    processed_tables: List[Dict[str, Any]]
    execution_id: str
    config: Dict[str, Any] = field(default_factory=dict)
