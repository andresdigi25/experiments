import polars as pl
import pandas as pd
import dask.dataframe as dd
import pandera as pa
from pandera.typing import Series
from great_expectations.dataset import PandasDataset
import psycopg2
import logging
import requests
from fastapi import FastAPI, BackgroundTasks

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

class AddressSchema(pa.SchemaModel):
    name: Series[str]
    street: Series[str]
    city: Series[str]
    state: Series[str] = pa.Field(str_matches=r"^[A-Z]{2}$")
    zip: Series[int]
    auth_id: Series[str] = pa.Field(str_matches=r"^AUTH\\d{3}$")
    
    @pa.check("zip")
    def zip_matches_state(cls, zip_series: Series[int], state_series: Series[str]) -> Series[bool]:
        mismatches = zip_series[zip_series.map(lambda z: zip_to_state.get(z, get_state_from_zip(z)) != state_series.loc[z.index])]
        if not mismatches.empty:
            logging.warning(f"ZIP-State mismatches detected: {mismatches.to_dict()}")
        return zip_series.map(lambda z: zip_to_state.get(z, get_state_from_zip(z)) == state_series.loc[z.index])

# ================================
# API Endpoint for Validation Errors
# ================================
@app.get("/validation-errors")
def get_validation_errors():
    with open("validation_errors.log", "r") as log_file:
        return {"errors": log_file.readlines()}

# ================================
# API Endpoint for Bulk Reprocessing
# ================================
@app.post("/bulk-reprocess")
def bulk_reprocess(background_tasks: BackgroundTasks):
    background_tasks.add_task(reprocess_large_datasets)
    return {"message": "Bulk reprocessing started in the background."}

def reprocess_large_datasets():
    df_dask = dd.read_csv(csv_file)
    df_dask = df_dask.rename(columns=mapping)
    
    def correct_state(row):
        correct_state = get_state_from_zip(row["zip"])
        if correct_state and correct_state != row["state"]:
            logging.warning(f"Correcting state for ZIP {row['zip']}: {row['state']} -> {correct_state}")
            row["state"] = correct_state
        return row
    
    df_dask = df_dask.map_partitions(lambda df: df.apply(correct_state, axis=1))
    df_dask.compute().to_csv("corrected_bulk_data.csv", index=False)
    logging.info("Bulk reprocessing completed and saved to 'corrected_bulk_data.csv'")

# ================================
# Store Data in PostgreSQL
# ================================
DB_CONNECTION = psycopg2.connect(
    dbname="ingestion_db",
    user="postgres",
    password="password",
    host="localhost",
    port="5432"
)
cursor = DB_CONNECTION.cursor()
cursor.execute("""
    CREATE TABLE IF NOT EXISTS validated_data (
        id SERIAL PRIMARY KEY,
        name TEXT,
        street TEXT,
        city TEXT,
        state TEXT,
        zip INT,
        auth_id TEXT
    )
""")

# Insert Pandas DataFrame

def store_in_db(df):
    for _, row in df.iterrows():
        cursor.execute("INSERT INTO validated_data (name, street, city, state, zip, auth_id) VALUES (%s, %s, %s, %s, %s, %s)", row.tolist())
    DB_CONNECTION.commit()

print("✅ Storing Pandas DataFrame in PostgreSQL")
store_in_db(pd.read_csv(csv_file).rename(columns=mapping))

print("✅ Bulk Reprocessing API added for large datasets")
