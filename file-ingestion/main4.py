import polars as pl
import pandas as pd
import dask.dataframe as dd
import pandera as pa
from pandera.typing import Series
from great_expectations.dataset import PandasDataset
import psycopg2
import logging
import requests
from fastapi import FastAPI

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
# API Endpoint to Reprocess & Fix Incorrect Records
# ================================
@app.post("/fix-invalid-records")
def fix_invalid_records():
    df = pd.read_csv(csv_file)
    df = df.rename(columns=mapping)
    
    corrected = 0
    for index, row in df.iterrows():
        correct_state = get_state_from_zip(row["zip"])
        if correct_state and correct_state != row["state"]:
            logging.warning(f"Correcting state for ZIP {row['zip']}: {row['state']} -> {correct_state}")
            df.at[index, "state"] = correct_state
            corrected += 1
    
    df.to_csv("corrected_data.csv", index=False)
    return {"message": f"{corrected} records corrected and saved to 'corrected_data.csv'"}

# ================================
# 1️⃣ Polars Processing
# ================================
df_polars = pl.read_csv(csv_file)
df_polars = df_polars.rename(mapping)
print("✅ Polars Processed:")
print(df_polars)

# ================================
# 2️⃣ Pandas Processing
# ================================
df_pandas = pd.read_csv(csv_file)
df_pandas = df_pandas.rename(columns=mapping)
df_validated = AddressSchema.validate(df_pandas)
print("✅ Pandas Processed and Validated")

# ================================
# 3️⃣ Dask Processing
# ================================
df_dask = dd.read_csv(csv_file)
df_dask = df_dask.rename(columns=mapping)
df_dask = df_dask.compute()
print("✅ Dask Processed:")
print(df_dask)

# ================================
# 4️⃣ Pandera Validation
# ================================
df_validated = AddressSchema.validate(df_pandas)
print("✅ Pandera Validation Passed")

# ================================
# 5️⃣ Great Expectations Validation
# ================================
ge_df = PandasDataset(df_pandas)
assert ge_df.expect_column_values_to_not_be_null("name").success
assert ge_df.expect_column_values_to_match_regex("auth_id", r"^AUTH\\d{3}$").success
print("✅ Great Expectations Validation Passed")

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
store_in_db(df_pandas)

print("✅ Storing Dask DataFrame in PostgreSQL")
store_in_db(df_dask)

print("✅ Storing Polars DataFrame in PostgreSQL")
store_in_db(df_polars.to_pandas())

print("✅ Data from all frameworks stored in PostgreSQL")
