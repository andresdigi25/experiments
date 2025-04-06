from fastapi import FastAPI, UploadFile, File, BackgroundTasks
import shutil
import os
import mimetypes
import polars as pl
import boto3
import json
import uuid
import psycopg2
from pathlib import Path
from celery import Celery
from pydantic import BaseModel, conint, confloat, constr
from datetime import datetime

# Initialize FastAPI
app = FastAPI()

# Initialize Celery (Custom Orchestration)
celery_app = Celery(
    "ingestion",
    broker="redis://localhost:6379/0",
    backend="redis://localhost:6379/0"
)

# AWS Configuration
DYNAMODB_TABLE = "FileMetadata"
dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(DYNAMODB_TABLE)
s3_client = boto3.client("s3")
STEP_FUNCTION_ARN = "arn:aws:states:us-east-1:123456789012:stateMachine:IngestionStateMachine"
step_functions_client = boto3.client("stepfunctions")
S3_BUCKET = "processed-data-bucket"

# PostgreSQL Configuration
DB_CONNECTION = psycopg2.connect(
    dbname="ingestion_db",
    user="postgres",
    password="password",
    host="localhost",
    port="5432"
)
cursor = DB_CONNECTION.cursor()
cursor.execute("""
    CREATE TABLE IF NOT EXISTS processed_data (
        id SERIAL PRIMARY KEY,
        order_id INT,
        date DATE,
        amount FLOAT
    )
""")
DB_CONNECTION.commit()

# Directory to store uploaded files
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Supported file formats
SUPPORTED_FORMATS = {"csv", "json", "parquet", "xlsx"}

# Schema Validation with Pydantic
class OrderSchema(BaseModel):
    order_id: conint(gt=0)
    date: constr(regex="\\d{4}-\\d{2}-\\d{2}")
    amount: confloat(gt=0)

# Mapper & Transformation Logic
def transform_data(df: pl.DataFrame) -> pl.DataFrame:
    return df.rename({"id": "order_id", "order_date": "date", "total": "amount"})

# Function to detect file type
def detect_file_type(file_path: str) -> str:
    mime_type, _ = mimetypes.guess_type(file_path)
    if mime_type:
        if "csv" in mime_type:
            return "csv"
        elif "json" in mime_type:
            return "json"
        elif "parquet" in mime_type:
            return "parquet"
        elif "spreadsheet" in mime_type:
            return "xlsx"
    return Path(file_path).suffix.lower().strip(".")

# Function to store metadata in DynamoDB
def store_metadata(filename: str, file_type: str, status: str):
    table.put_item(
        Item={
            "id": str(uuid.uuid4()),
            "filename": filename,
            "file_type": file_type,
            "status": status,
            "timestamp": datetime.utcnow().isoformat()
        }
    )

# Function to invoke AWS Step Functions
def invoke_step_function(payload):
    response = step_functions_client.start_execution(
        stateMachineArn=STEP_FUNCTION_ARN,
        input=json.dumps(payload)
    )
    return response

# Background task for ingestion pipeline
@celery_app.task
def process_file(file_path: str, filename: str):
    file_type = detect_file_type(file_path)
    if file_type not in SUPPORTED_FORMATS:
        store_metadata(filename, file_type, "Error: Unsupported file format")
        return {"error": "Unsupported file format"}
    
    # Load file using Polars
    if file_type == "csv":
        df = pl.read_csv(file_path)
    elif file_type == "json":
        df = pl.read_json(file_path)
    elif file_type == "parquet":
        df = pl.read_parquet(file_path)
    elif file_type == "xlsx":
        df = pl.read_excel(file_path)
    
    # Apply transformations
    df = transform_data(df)
    
    # Validate data using Pydantic
    for row in df.rows():
        try:
            OrderSchema(order_id=row[0], date=row[1], amount=row[2])
        except Exception as e:
            store_metadata(filename, file_type, f"Validation Error: {str(e)}")
            return {"error": f"Validation failed: {str(e)}"}
    
    # Store processed data in PostgreSQL
    for row in df.rows():
        cursor.execute("INSERT INTO processed_data (order_id, date, amount) VALUES (%s, %s, %s)", row)
    DB_CONNECTION.commit()
    
    # Store processed file in S3
    s3_client.upload_file(file_path, S3_BUCKET, filename)
    
    # Invoke AWS Step Functions
    invoke_step_function({"filename": filename, "status": "processed"})
    
    store_metadata(filename, file_type, "Processed Successfully")
    return {"status": "File processed successfully"}

# API Endpoint to Upload Files
@app.post("/upload/")
def upload_file(file: UploadFile = File(...), background_tasks: BackgroundTasks = BackgroundTasks()):
    file_path = os.path.join(UPLOAD_DIR, file.filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # Store metadata
    store_metadata(file.filename, "pending", "uploaded")
    
    # Trigger background processing task
    background_tasks.add_task(process_file, file_path, file.filename)
    
    return {"message": "File uploaded and processing started", "filename": file.filename}
