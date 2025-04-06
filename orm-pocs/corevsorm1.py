# file: core_example.py

import pandas as pd
from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String, Float, insert, select, update, delete

# Load CSV
df = pd.read_csv("employees.csv")

# Setup engine and metadata
engine = create_engine("sqlite:///core_employees.db", echo=False)
metadata = MetaData()

# Define table
employees = Table(
    "employees", metadata,
    Column("id", Integer, primary_key=True),
    Column("name", String),
    Column("department", String),
    Column("salary", Float),
)

# Create the table
metadata.drop_all(engine)
metadata.create_all(engine)

# Insert data from CSV
with engine.begin() as conn:
    conn.execute(insert(employees), df.to_dict(orient="records"))

# Read all records
with engine.connect() as conn:
    all_df = pd.read_sql(select(employees), conn)

# Update
with engine.begin() as conn:
    conn.execute(update(employees).where(employees.c.name == "Bob").values(salary=55000))

# Delete
with engine.begin() as conn:
    conn.execute(delete(employees).where(employees.c.id == 3))

# Read updated table
with engine.connect() as conn:
    updated_df = pd.read_sql(select(employees), conn)

# Analysis
print("\n📊 SQLAlchemy Core - Analysis")
print(updated_df.groupby("department")["salary"].mean())
print("\n💸 Highest paid employee (Core):")
print(updated_df.loc[updated_df["salary"].idxmax()])
