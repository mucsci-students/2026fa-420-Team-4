# backend/models/session_store.py
from typing import Dict, Any, Optional
from scheduler.config import CombinedConfig

class SessionStore:
    """Hold the process-wide configuration and generated schedules in memory."""

    def __init__(self):
        """Initialize an empty configuration and schedule store."""
        self.raw_config: Dict[str, Any] = {}
        self.config_object: Optional[CombinedConfig] = None
        self.schedule: Any = None
        self.is_loaded: bool = False

    def reset(self):
        """Clear the loaded configuration, generated schedules, and loaded flag."""
        self.raw_config = {}
        self.config_object = None
        self.schedule = None
        self.is_loaded = False

store = SessionStore()