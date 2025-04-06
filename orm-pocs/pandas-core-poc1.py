# file: csv_sqlalchemy_pandas.py

import pandas as pd
from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String, Float, select, insert, update, delete

# 1. Load CSV into DataFrame
df = pd.read_csv("employees.csv")
print("\n📄 Original CSV:")
print(df)

# 2. Create Engine and Metadata
engine = create_engine("sqlite:///employees.db", echo=True)
metadata = MetaData()

# 3. Define Table
employees = Table(
    "employees", metadata,
    Column("id", Integer, primary_key=True),
    Column("name", String),
    Column("department", String),
    Column("salary", Float)
)

# 4. Create Table in DB
metadata.drop_all(engine)  # Reset (for demo purposes)
metadata.create_all(engine)

# 5. Insert Data from DataFrame to DB
with engine.begin() as conn:
    conn.execute(insert(employees), df.to_dict(orient="records"))

# 6. Read Data Back into DataFrame
with engine.connect() as conn:
    result_df = pd.read_sql(select(employees), conn)

print("\n📊 Data from DB:")
print(result_df)

# 7. UPDATE Salary for one employee
with engine.begin() as conn:
    stmt = update(employees).where(employees.c.name == "Bob").values(salary=55000)
    conn.execute(stmt)

# 8. DELETE Employee by ID
with engine.begin() as conn:
    stmt = delete(employees).where(employees.c.id == 3)
    conn.execute(stmt)

# 9. Re-read updated table
with engine.connect() as conn:
    df_updated = pd.read_sql(select(employees), conn)

print("\n🔁 After UPDATE and DELETE:")
print(df_updated)

# 10. ANALYSIS with Pandas
print("\n📈 Average salary by department:")
print(df_updated.groupby("department")["salary"].mean())

print("\n💸 Highest paid employee:")
print(df_updated.loc[df_updated["salary"].idxmax()])
