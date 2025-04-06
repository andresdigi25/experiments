from pydantic import BaseModel
from typing import Dict, List, Optional, Any

# Schema for upload response
class UploadSummary(BaseModel):
    totalRecords: int
    validRecords: int
    invalidRecords: int
    savedRecords: int

class UploadResponse(BaseModel):
    message: str
    summary: UploadSummary

# Schema for mapping creation
class MappingCreate(BaseModel):
    name: str
    mappings: Dict[str, List[str]]

class MappingResponse(BaseModel):
    message: str
    name: str

# Schema for record
class RecordBase(BaseModel):
    name: str
    address1: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip: Optional[str] = None
    auth_id: str

class RecordCreate(RecordBase):
    pass

class Record(RecordBase):
    id: int
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    class Config:
        orm_mode = True