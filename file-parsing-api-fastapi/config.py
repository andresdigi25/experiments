import os
from typing import Dict, List, Any
from pydantic import BaseSettings

class Settings(BaseSettings):
    # Database settings
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", 
        "postgresql://user:password@db:5432/datastore"
    )
    
    # Upload directory
    UPLOAD_DIR: str = os.getenv("UPLOAD_DIR", "uploads")
    
    # Field mapping configurations
    FIELD_MAPPINGS: Dict[str, Dict[str, List[str]]] = {
        # Default mapping that works as a fallback
        "default": {
            "name": ["name", "full_name", "customer_name", "client_name"],
            "address1": ["address", "address1", "street_address", "street"],
            "city": ["city", "town"],
            "state": ["state", "province", "region"],
            "zip": ["zip", "zipcode", "postal_code", "postalcode", "zip_code"],
            "auth_id": ["auth_id", "authid", "authorization_id", "auth", "id"]
        },
        
        # Example of a vendor-specific mapping
        "vendor1": {
            "name": ["customer"],
            "address1": ["primary_address"],
            "city": ["customer_city"],
            "state": ["customer_state"],
            "zip": ["customer_zip"],
            "auth_id": ["customer_id"]
        }
    }
    
    # Validation rules
    VALIDATION: Dict[str, Any] = {
        # Required fields for a record to be considered valid
        "required_fields": ["name", "auth_id"],
        
        # Optional validation rules (examples)
        "rules": {
            "zip": {
                "pattern": r"^\d{5}(-\d{4})?$",
                "message": "ZIP code must be 5 digits or 5+4 format"
            },
            "state": {
                "max_length": 2,
                "message": "State should be a 2-letter code"
            }
        }
    }

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

# Create a global settings object
settings = Settings()