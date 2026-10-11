# backend/models/session_store.py
from typing import Dict, Any, Optional
from scheduler.config import CombinedConfig

class SessionStore:
    def __init__(self):
        self.raw_config: Dict[str, Any] = {}
        self.config_filename: Optional[str] = None
        self.config_object: Optional[CombinedConfig] = None
        self.schedule: Any = None
        self.schedule_filename: Optional[str] = None
        self.is_loaded: bool = False

    def reset(self):
        self.raw_config = {}
        self.config_filename = None
        self.config_object = None
        self.schedule = None
        self.schedule_filename = None
        self.is_loaded = False

store = SessionStore()