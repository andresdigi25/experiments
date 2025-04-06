from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Dict, Optional, Any
import pandas as pd
import json
import os
import shutil
from sqlalchemy.orm import Session
from pathlib import Path
import uuid
import csv
import io

# Import local modules
from database import engine, SessionLocal, Base
import models
import schemas
from config import settings

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="File Parsing API", description="API for parsing and mapping different file formats")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Ensure upload directory exists
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)

# File type detection
def detect_file_type(filename: str) -> str:
    ext = os.path.splitext(filename)[1].lower()
    if ext == '.csv':
        return 'csv'
    elif ext in ['.xlsx', '.xls']:
        return 'excel'
    elif ext == '.json':
        return 'json'
    elif ext == '.txt':
        return 'text'
    else:
        return 'unknown'

# Normalize field names using the mapping configuration
def normalize_record(record: Dict[str, Any], mapping_key: str = 'default') -> Dict[str, Any]:
    # Get the appropriate mapping
    mapping = settings.FIELD_MAPPINGS.get(mapping_key, settings.FIELD_MAPPINGS['default'])
    
    # Initialize with None values for all target fields
    normalized_record = {target_field: None for target_field in mapping.keys()}
    
    # Process the record fields
    for source_field, value in record.items():
        source_field_lower = source_field.lower().strip()
        
        # Check each target field
        for target_field, possible_source_fields in mapping.items():
            if any(f.lower() == source_field_lower or source_field_lower.find(f.lower()) >= 0 
                  for f in possible_source_fields):
                normalized_record[target_field] = value
    
    return normalized_record

# Parse CSV files
async def parse_csv(file_path: str) -> List[Dict[str, Any]]:
    df = pd.read_csv(file_path)
    return df.fillna('').to_dict(orient='records')

# Parse Excel files
async def parse_excel(file_path: str) -> List[Dict[str, Any]]:
    df = pd.read_excel(file_path)
    return df.fillna('').to_dict(orient='records')

# Parse JSON files
async def parse_json(file_path: str) -> List[Dict[str, Any]]:
    with open(file_path, 'r') as f:
        data = json.load(f)
    
    # Ensure data is a list of records
    if isinstance(data, dict):
        data = [data]
    
    return data

# Parse text files (assuming tab or comma delimited)
async def parse_text(file_path: str) -> List[Dict[str, Any]]:
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Try to detect delimiter
    first_line = content.split('\n')[0]
    if '\t' in first_line:
        delimiter = '\t'
    else:
        delimiter = ','
    
    # Parse as CSV with detected delimiter
    f = io.StringIO(content)
    reader = csv.DictReader(f, delimiter=delimiter)
    return [row for row in reader]

# Process uploaded file
async def process_file(file_path: str, filename: str, source: str = 'default') -> Dict[str, Any]:
    file_type = detect_file_type(filename)
    
    # Parse file based on type
    if file_type == 'csv':
        records = await parse_csv(file_path)
    elif file_type == 'excel':
        records = await parse_excel(file_path)
    elif file_type == 'json':
        records = await parse_json(file_path)
    elif file_type == 'text':
        records = await parse_text(file_path)
    else:
        raise HTTPException(status_code=400, detail=f"Unsupported file type: {file_type}")
    
    # Normalize records using appropriate mapping
    normalized_records = [normalize_record(record, source) for record in records]
    
    # Validate records - ensure required fields are present
    valid_records = [
        record for record in normalized_records 
        if all(record[field] is not None for field in settings.VALIDATION['required_fields'])
    ]
    
    return {
        'total': len(records),
        'valid': len(valid_records),
        'invalid': len(records) - len(valid_records),
        'records': valid_records
    }

# Save records to database
def save_records(records: List[Dict[str, Any]], db: Session) -> Dict[str, Any]:
    saved_count = 0
    
    for record in records:
        # Check if record with this auth_id exists
        existing_record = db.query(models.Record).filter(
            models.Record.auth_id == record['auth_id']
        ).first()
        
        if existing_record:
            # Update existing record
            for key, value in record.items():
                if value is not None:
                    setattr(existing_record, key, value)
            db.commit()
            saved_count += 1
        else:
            # Create new record
            db_record = models.Record(
                name=record['name'],
                address1=record['address1'],
                city=record['city'],
                state=record['state'],
                zip=record['zip'],
                auth_id=record['auth_id']
            )
            db.add(db_record)
            db.commit()
            saved_count += 1
    
    return {'success': True, 'count': saved_count}

# API Endpoints
@app.post("/api/upload", response_model=schemas.UploadResponse)
async def upload_file(
    file: UploadFile = File(...),
    source: str = Form("default"),
    db: Session = Depends(get_db)
):
    try:
        # Create a temporary file path
        temp_file = Path(settings.UPLOAD_DIR) / f"{uuid.uuid4()}{os.path.splitext(file.filename)[1]}"
        
        # Save uploaded file
        with open(temp_file, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Process the file
        result = await process_file(str(temp_file), file.filename, source)
        
        # Save records to database
        save_result = save_records(result['records'], db)
        
        # Clean up the uploaded file
        os.remove(temp_file)
        
        return {
            "message": "File processed successfully",
            "summary": {
                "totalRecords": result['total'],
                "validRecords": result['valid'],
                "invalidRecords": result['invalid'],
                "savedRecords": save_result['count']
            }
        }
    except Exception as e:
        # Ensure temp file is cleaned up
        if 'temp_file' in locals() and os.path.exists(temp_file):
            os.remove(temp_file)
        
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/mappings", response_model=schemas.MappingResponse)
async def create_mapping(mapping: schemas.MappingCreate):
    try:
        # Add new mapping to settings
        settings.FIELD_MAPPINGS[mapping.name] = mapping.mappings
        return {"message": "Mapping configuration created", "name": mapping.name}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/mappings", response_model=Dict[str, Dict[str, List[str]]])
async def get_mappings():
    return settings.FIELD_MAPPINGS

# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=int(os.getenv("PORT", 8000)), reload=True)