from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String, insert, select

engine = create_engine("sqlite:///core.db", echo=True)
metadata = MetaData()

users = Table(
    "users", metadata,
    Column("id", Integer, primary_key=True),
    Column("name", String),
    Column("email", String)
)

metadata.create_all(engine)

# Insert data
with engine.connect() as conn:
    conn.execute(insert(users).values(name="Alice", email="alice@example.com"))
    conn.commit()

# Query data
with engine.connect() as conn:
    result = conn.execute(select(users))
    for row in result:
        print(row)
