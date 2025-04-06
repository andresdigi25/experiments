from sqlalchemy import (
    create_engine, MetaData, Table, Column, Integer, String,
    insert, select, update, delete
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, Session

# ----------------------------
# Setup: Engine & Metadata
# ----------------------------
engine = create_engine("sqlite+pysqlite:///:memory:", echo=True)
metadata = MetaData()

# ----------------------------
# CORE-style Table definition
# ----------------------------
users_table = Table(
    "users",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("name", String),
    Column("email", String),
)

# ----------------------------
# ORM-style Base and Model
# ----------------------------
class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column()
    email: Mapped[str] = mapped_column()

# ----------------------------
# Create tables using ORM metadata (either works)
# ----------------------------
Base.metadata.create_all(engine)
# Or: metadata.create_all(engine)

# ----------------------------
# INSERT - Core Style
# ----------------------------
with Session(engine) as session:
    stmt = insert(users_table).values(name="Alice", email="alice@example.com")
    session.execute(stmt)
    session.commit()

# ----------------------------
# SELECT - Core Style
# ----------------------------
with Session(engine) as session:
    stmt = select(users_table).where(users_table.c.name == "Alice")
    result = session.execute(stmt)
    for row in result:
        print("CORE SELECT:", row)

# ----------------------------
# UPDATE - Core Style
# ----------------------------
with Session(engine) as session:
    stmt = update(users_table).where(users_table.c.name == "Alice").values(email="alice@updated.com")
    session.execute(stmt)
    session.commit()

# ----------------------------
# DELETE - Core Style
# ----------------------------
with Session(engine) as session:
    stmt = delete(users_table).where(users_table.c.name == "Alice")
    session.execute(stmt)
    session.commit()

# ----------------------------
# INSERT - ORM Style
# ----------------------------
with Session(engine) as session:
    user = User(name="Bob", email="bob@example.com")
    session.add(user)
    session.commit()

# ----------------------------
# SELECT - ORM Style
# ----------------------------
with Session(engine) as session:
    result = session.execute(select(User).where(User.name == "Bob"))
    user = result.scalar_one()
    print("ORM SELECT:", user.name, user.email)

# ----------------------------
# UPDATE - ORM Style
# ----------------------------
with Session(engine) as session:
    user = session.query(User).filter_by(name="Bob").first()
    user.email = "bob@updated.com"
    session.commit()

# ----------------------------
# DELETE - ORM Style
# ----------------------------
with Session(engine) as session:
    user = session.query(User).filter_by(name="Bob").first()
    session.delete(user)
    session.commit()
