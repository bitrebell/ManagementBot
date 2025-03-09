"""
Database initialization
"""

import os
import json
from typing import Dict, List, Any, Optional, Union

# Simple JSON database implementation
class JSONDatabase:
    def __init__(self, db_name: str):
        self.db_name = db_name
        self.db_path = f"bot/database/data/{db_name}.json"
        self.data = self._load_db()
    
    def _load_db(self) -> Dict:
        """Load database from file"""
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        # Create file if it doesn't exist
        if not os.path.exists(self.db_path):
            with open(self.db_path, "w") as f:
                json.dump({}, f)
            return {}
        
        # Load data from file
        try:
            with open(self.db_path, "r") as f:
                return json.load(f)
        except json.JSONDecodeError:
            # If file is corrupted, create a new one
            with open(self.db_path, "w") as f:
                json.dump({}, f)
            return {}
    
    def _save_db(self) -> None:
        """Save database to file"""
        with open(self.db_path, "w") as f:
            json.dump(self.data, f, indent=4)
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get value from database"""
        return self.data.get(key, default)
    
    def set(self, key: str, value: Any) -> None:
        """Set value in database"""
        self.data[key] = value
        self._save_db()
    
    def delete(self, key: str) -> None:
        """Delete key from database"""
        if key in self.data:
            del self.data[key]
            self._save_db()
    
    def list_keys(self) -> List[str]:
        """List all keys in database"""
        return list(self.data.keys())
    
    def contains(self, key: str) -> bool:
        """Check if key exists in database"""
        return key in self.data

# Database instances
notes_db = JSONDatabase("notes")
welcome_db = JSONDatabase("welcome")
filters_db = JSONDatabase("filters")
warnings_db = JSONDatabase("warnings")
settings_db = JSONDatabase("settings") 