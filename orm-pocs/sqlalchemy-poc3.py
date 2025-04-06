# file: main.py

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, Session
from sqlalchemy import String, Integer

# Step 1: Base class using DeclarativeBase (new in SQLAlchemy 2.0)
class Base(DeclarativeBase):
    pass

# Step 2: Define your model using `Mapped[]` and `mapped_column`
class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50))
    email: Mapped[str] = mapped_column(String(100))

    def __repr__(self) -> str:
        return f"<User(id={self.id}, name={self.name}, email={self.email})>"

# Step 3: Create engine
engine = create_engine("sqlite:///example.db", echo=True)

# Step 4: Create tables
Base.metadata.create_all(engine)

# Step 5: Insert data
with Session(engine) as session:
    user1 = User(name="Alice", email="alice@example.com")
    user2 = User(name="Bob", email="bob@example.com")

    session.add_all([user1, user2])
    session.commit()

# Step 6: Query data
with Session(engine) as session:
    all_users = session.query(User).all()
    for user in all_users:
        print(user)

    # Filter example
    bob = session.query(User).filter_by(name="Bob").first()
    print("Filtered:", bob)
