# file: complex_example.py

from typing import List
from sqlalchemy import create_engine, String, Integer, ForeignKey, Table
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    mapped_column,
    relationship,
    Session,
    selectinload,
)
from sqlalchemy import select

# 1. Define Base
class Base(DeclarativeBase):
    pass

# 2. Association Table (Many-to-Many)
user_role_table = Table(
    "user_role_association",
    Base.metadata,
    mapped_column("user_id", ForeignKey("users.id"), primary_key=True),
    mapped_column("role_id", ForeignKey("roles.id"), primary_key=True),
)

# 3. Role Model
class Role(Base):
    __tablename__ = "roles"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50), unique=True)

    users: Mapped[List["User"]] = relationship(
        back_populates="roles",
        secondary=user_role_table,
    )

    def __repr__(self):
        return f"<Role(id={self.id}, name={self.name})>"

# 4. User Model
class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50))
    email: Mapped[str] = mapped_column(String(100), unique=True)

    roles: Mapped[List[Role]] = relationship(
        back_populates="users",
        secondary=user_role_table,
    )

    def __repr__(self):
        return f"<User(id={self.id}, name={self.name}, email={self.email})>"

# 5. Setup Engine
engine = create_engine("sqlite:///complex.db", echo=False)
Base.metadata.create_all(engine)

def insert_data():
    with Session(engine) as session:
        # Create roles
        admin = Role(name="admin")
        editor = Role(name="editor")
        viewer = Role(name="viewer")

        # Add roles first
        session.add_all([admin, editor, viewer])
        session.flush()  # Ensure IDs are available

        # Method 1: Add user and roles via constructor
        user1 = User(name="Alice", email="alice@example.com", roles=[admin, viewer])

        # Method 2: Add user then assign roles
        user2 = User(name="Bob", email="bob@example.com")
        user2.roles.append(editor)
        user2.roles.append(viewer)

        # Method 3: Bulk insert and manual linking
        user3 = User(name="Charlie", email="charlie@example.com")
        session.add(user3)
        session.flush()
        user3.roles.extend([admin])

        session.add_all([user1, user2])
        session.commit()


# Get all users
def get_all_users():
    with Session(engine) as session:
        users = session.scalars(select(User)).all()
        for user in users:
            print(user)

# Get all users with their roles (eager loading)
def get_users_with_roles():
    with Session(engine) as session:
        users = session.scalars(
            select(User).options(selectinload(User.roles))
        ).all()
        for user in users:
            print(f"{user.name} -> {[role.name for role in user.roles]}")

# Get user by ID
def get_user_by_id(user_id: int):
    with Session(engine) as session:
        user = session.get(User, user_id)
        print(user)

# Get users by role name
def get_users_by_role(role_name: str):
    with Session(engine) as session:
        users = session.scalars(
            select(User)
            .join(User.roles)
            .where(Role.name == role_name)
            .options(selectinload(User.roles))
        ).all()
        for user in users:
            print(f"{user.name} ({user.email}) has role: {role_name}")


if __name__ == "__main__":
    insert_data()
    print("\nAll users:")
    get_all_users()

    print("\nAll users with roles:")
    get_users_with_roles()

    print("\nUser with ID 2:")
    get_user_by_id(2)

    print("\nUsers with role 'admin':")
    get_users_by_role("admin")
