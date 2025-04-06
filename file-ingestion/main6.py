import polars as pl
import pandas as pd
import dask.dataframe as dd
import pandera as pa
from pandera.typing import Series
from great_expectations.dataset import PandasDataset
import psycopg2
import logging
import requests
from fastapi import FastAPI, BackgroundTasks, UploadFile, File

# Configure Logging
logging.basicConfig(filename="validation_errors.log", level=logging.WARNING, format='%(asctime)s - %(levelname)s - %(message)s')

# Initialize FastAPI
app = FastAPI()

# ================================
# Load CSV File
# ================================
csv_file = "data.csv"

# ================================
# Define Schema and Mapping
# ================================
mapping = {
    "full_name": "name",
    "street_address": "street",
    "city": "city",
    "state": "state",
    "zipcode": "zip",
    "auth_id": "auth_id"
}

# ZIP Code to State Mapping for Validation
zip_to_state = {
    10001: "NY",
    90001: "CA",
    60601: "IL",
    77001: "TX",
    85001: "AZ"
}

# External Geolocation API for ZIP-State Validation
GEOLOCATION_API_URL = "https://api.zippopotam.us/us/"

def get_state_from_zip(zip_code):
    response = requests.get(f"{GEOLOCATION_API_URL}{zip_code}")
    if response.status_code == 200:
        return response.json()["places"][0]["state abbreviation"]
    return None

# ================================
# Pandera Schema Definitions
# ================================
class AddressSchema(pa.DataFrameModel):
    name: Series[str]
    street: Series[str]
    city: Series[str]
    state: Series[str] = pa.Column(str, checks=pa.Check.str_matches(r"^[A-Z]{2}$"))
    zip: Series[int]
    auth_id: Series[str] = pa.Column(str, checks=pa.Check.str_matches(r"^AUTH\\d{3}$"))

class HINSchema(pa.DataFrameModel):
    hin: Series[str] = pa.Column(str, checks=pa.Check.str_matches(r"^\d{9}$"))
    name: Series[str]
    address: Series[str]
    city: Series[str]
    state: Series[str] = pa.Column(str, checks=pa.Check.str_matches(r"^[A-Z]{2}$"))
    zip: Series[int]
    entity_type: Series[str]

class DEASchema(pa.DataFrameModel):
    dea_number: Series[str] = pa.Column(str, checks=pa.Check.str_matches(r"^[A-Z]{2}\d{7}$"))
    provider_name: Series[str]
    license_type: Series[str]
    expiration_date: Series[str]  # Future validation to check date format

class NPISchema(pa.DataFrameModel):
    npi: Series[str] = pa.Column(str, checks=pa.Check.str_matches(r"^\d{10}$"))
    provider_name: Series[str]
    taxonomy_code: Series[str]
    specialty: Series[str]
    state: Series[str] = pa.Column(str, checks=pa.Check.str_matches(r"^[A-Z]{2}$"))

# ================================
# API Endpoint for HIN, DEA, NPI Validation
# ================================
@app.post("/validate-hin-dea-npi")
def validate_identifiers(file: UploadFile = File(...)):
    df = pd.read_csv(file.file)
    file_type = file.filename.split(".")[0].lower()
    
    if "hin" in file_type:
        df_validated = HINSchema.validate(df)
        table_name = "validated_hin"
    elif "dea" in file_type:
        df_validated = DEASchema.validate(df)
        table_name = "validated_dea"
    elif "npi" in file_type:
        df_validated = NPISchema.validate(df)
        table_name = "validated_npi"
    else:
        return {"error": "Unknown file type. Use HIN, DEA, or NPI in the filename."}
    
    store_validated_data(df_validated, table_name)
    return {"message": f"{file.filename} validated and stored in {table_name}."}

# ================================
# Store Validated Data in PostgreSQL
# ================================
def store_validated_data(df, table_name):
    DB_CONNECTION = psycopg2.connect(
        dbname="ingestion_db",
        user="postgres",
        password="password",
        host="localhost",
        port="5432"
    )
    cursor = DB_CONNECTION.cursor()
    cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS {table_name} (
            id SERIAL PRIMARY KEY,
            {', '.join(df.columns)} TEXT
        )
    """)
    
    for _, row in df.iterrows():
        cursor.execute(f"INSERT INTO {table_name} ({', '.join(df.columns)}) VALUES ({', '.join(['%s'] * len(row))})", row.tolist())
    DB_CONNECTION.commit()
    print(f"✅ Data stored in {table_name}")

print("✅ API Endpoint for HIN, DEA, NPI Validation Added")
