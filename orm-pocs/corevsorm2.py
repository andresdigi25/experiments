# file: orm_example.py

import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, Session
from sqlalchemy import String, Integer, Float, select

# Load CSV
df = pd.read_csv("employees.csv")

# Define engine
engine = create_engine("sqlite:///orm_employees.db", echo=False)

# Define Base and Model
class Base(DeclarativeBase):
    pass

class Employee(Base):
    __tablename__ = "employees"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String)
    department: Mapped[str] = mapped_column(String)
    salary: Mapped[float] = mapped_column(Float)

# Create table
Base.metadata.drop_all(engine)
Base.metadata.create_all(engine)

# Insert CSV rows
with Session(engine) as session:
    employees = [Employee(**row) for row in df.to_dict(orient="records")]
    session.add_all(employees)
    session.commit()

# Query all
with Session(engine) as session:
    result = session.scalars(select(Employee)).all()
    all_df = pd.DataFrame([vars(e) for e in result]).drop("_sa_instance_state", axis=1)

# Update
with Session(engine) as session:
    bob = session.scalars(select(Employee).where(Employee.name == "Bob")).first()
    bob.salary = 55000
    session.commit()

# Delete
with Session(engine) as session:
    charlie = session.get(Employee, 3)
    session.delete(charlie)
    session.commit()

# Requery
with Session(engine) as session:
    result = session.scalars(select(Employee)).all()
    updated_df = pd.DataFrame([vars(e) for e in result]).drop("_sa_instance_state", axis=1)

# Analysis
print("\n📊 SQLAlchemy ORM - Analysis")
print(updated_df.groupby("department")["salary"].mean())
print("\n💸 Highest paid employee (ORM):")
print(updated_df.loc[updated_df["salary"].idxmax()])
