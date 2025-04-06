"""
SQLAlchemy 2.0 CRUD Operations Demonstration
This script shows both ORM-style and SQL Expression Language approaches
for Create, Read, Update, and Delete operations.
Using mapped_column for better type safety.
"""

import os
from typing import List, Optional
from sqlalchemy import create_engine, String, Integer, ForeignKey, select, insert, update, delete
from sqlalchemy.orm import DeclarativeBase, Session, Mapped, mapped_column, relationship

# Remove the database file if it exists
if os.path.exists("sqlalchemy_demo.db"):
    os.remove("sqlalchemy_demo.db")

# Create base class for declarative models
class Base(DeclarativeBase):
    pass

# Define models with mapped_column
class User(Base):
    __tablename__ = 'users'
    
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50))
    email: Mapped[str] = mapped_column(String(100), unique=True)
    
    addresses: Mapped[List["Address"]] = relationship(
        back_populates="user", 
        cascade="all, delete-orphan"
    )
    
    def __repr__(self) -> str:
        return f"User(id={self.id}, name='{self.name}', email='{self.email}')"
    
class Address(Base):
    __tablename__ = 'addresses'
    
    id: Mapped[int] = mapped_column(primary_key=True)
    street: Mapped[str] = mapped_column(String(100))
    city: Mapped[str] = mapped_column(String(50))
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'))
    
    user: Mapped["User"] = relationship(back_populates="addresses")
    
    def __repr__(self) -> str:
        return f"Address(id={self.id}, street='{self.street}', city='{self.city}')"

# Create engine and tables
engine = create_engine("sqlite:///sqlalchemy_demo.db", echo=False)
Base.metadata.create_all(engine)

def print_separator(message: str) -> None:
    """Print a separator with a message."""
    print("\n" + "="*80)
    print(f" {message} ".center(80, "="))
    print("="*80 + "\n")

def print_all_users() -> None:
    """Print all users in the database."""
    with Session(engine) as session:
        users = session.execute(select(User)).scalars().all()
        print("\nCurrent users in database:")
        for user in users:
            print(f"  - {user}")
            for addr in user.addresses:
                print(f"    * {addr}")
        print()

# ==================== CREATE OPERATIONS ====================

print_separator("CREATE OPERATIONS")

# ORM-style inserts
print("CREATING RECORDS - ORM STYLE")
with Session(engine) as session:
    # Create individual user
    alice = User(name="Alice", email="alice@example.com")
    alice.addresses = [
        Address(street="123 Main St", city="Wonderland")
    ]
    session.add(alice)
    
    # Create multiple users at once
    users = [
        User(
            name="Bob", 
            email="bob@example.com",
            addresses=[
                Address(street="456 Oak Ave", city="Bobville")
            ]
        ),
        User(
            name="Charlie", 
            email="charlie@example.com",
            addresses=[
                Address(street="789 Pine Rd", city="Charlietown"),
                Address(street="101 Beach Blvd", city="Vacation City")
            ]
        )
    ]
    session.add_all(users)
    session.commit()
    print("√ Added Alice, Bob and Charlie with addresses (ORM style)")

# SQL Expression Language inserts
print("\nCREATING RECORDS - SQL EXPRESSION STYLE")
with Session(engine) as session:
    # Insert a single user
    stmt = insert(User).values(name="Dave", email="dave@example.com")
    result = session.execute(stmt)
    dave_id = result.inserted_primary_key[0]
    
    # Insert address for Dave
    stmt = insert(Address).values(street="321 Elm St", city="Daveland", user_id=dave_id)
    session.execute(stmt)
    
    # Insert multiple users at once
    stmt = insert(User).values([
        {"name": "Eve", "email": "eve@example.com"},
        {"name": "Frank", "email": "frank@example.com"}
    ])
    result = session.execute(stmt)
    
    # We'd need to get IDs separately for bulk inserts to add related addresses
    eve = session.execute(select(User).where(User.name == "Eve")).scalar_one()
    stmt = insert(Address).values(street="555 Apple Lane", city="Eveville", user_id=eve.id)
    session.execute(stmt)
    
    session.commit()
    print("√ Added Dave, Eve and Frank with addresses (SQL Expression style)")

print_all_users()

# ==================== READ OPERATIONS ====================

print_separator("READ OPERATIONS")

# ORM-style reads
print("READING RECORDS - ORM STYLE")
with Session(engine) as session:
    # Get all users
    users = session.query(User).all()
    print(f"√ Found {len(users)} users")
    
    # Get user by primary key
    alice = session.get(User, 1)  # In 2.0, session.get() is preferred over query.get()
    print(f"√ Found user by primary key: {alice}")
    
    # Filter by a condition
    bob = session.query(User).filter_by(name="Bob").first()
    print(f"√ Found user by name: {bob}")
    
    # More complex filtering
    c_users = session.query(User).filter(User.name.like("C%")).all()
    print(f"√ Found {len(c_users)} users starting with 'C'")
    
    # Join query
    users_with_addresses = session.query(User, Address).join(Address).all()
    print(f"√ Found {len(users_with_addresses)} user-address pairs")
    for user, address in users_with_addresses[:2]:  # Show just first two
        print(f"  - {user.name} lives at {address.street}, {address.city}")

# SQL Expression Language reads
print("\nREADING RECORDS - SQL EXPRESSION STYLE")
with Session(engine) as session:
    # Get all users
    stmt = select(User)
    users = session.execute(stmt).scalars().all()
    print(f"√ Found {len(users)} users")
    
    # Get by primary key
    stmt = select(User).where(User.id == 1)
    alice = session.execute(stmt).scalar_one()
    print(f"√ Found user by primary key: {alice}")
    
    # Filter by condition
    stmt = select(User).where(User.name == "Bob")
    bob = session.execute(stmt).scalar_one()
    print(f"√ Found user by name: {bob}")
    
    # More complex filtering
    stmt = select(User).where(User.name.like("E%"))
    e_users = session.execute(stmt).scalars().all()
    print(f"√ Found {len(e_users)} users starting with 'E'")
    
    # Join query
    stmt = select(User, Address).join(Address)
    result = session.execute(stmt).all()
    print(f"√ Found {len(result)} user-address pairs")
    for user, address in result[:2]:  # Show just first two
        print(f"  - {user.name} lives at {address.street}, {address.city}")

# ==================== UPDATE OPERATIONS ====================

print_separator("UPDATE OPERATIONS")

# ORM-style updates
print("UPDATING RECORDS - ORM STYLE")
with Session(engine) as session:
    # Update a single user
    alice = session.query(User).filter_by(name="Alice").first()
    if alice:
        alice.email = "alice.updated@example.com"
        print(f"√ Updated Alice's email to {alice.email}")
    
    # Update user's address
    bob = session.query(User).filter_by(name="Bob").first()
    if bob and bob.addresses:
        bob.addresses[0].street = "456 Updated Ave"
        print(f"√ Updated Bob's address to {bob.addresses[0].street}")
    
    # Bulk update with filter
    count = session.query(User).filter(
        User.name.in_(["Charlie", "Dave"])
    ).update(
        {User.name: User.name + " (Updated)"},
        synchronize_session="fetch"
    )
    print(f"√ Bulk updated {count} users")
    
    session.commit()

# SQL Expression Language updates
print("\nUPDATING RECORDS - SQL EXPRESSION STYLE")
with Session(engine) as session:
    # Update a single user
    stmt = (
        update(User)
        .where(User.name == "Eve")
        .values(email="eve.updated@example.com")
    )
    result = session.execute(stmt)
    print(f"√ Updated {result.rowcount} user (Eve)")
    
    # Update address
    stmt = (
        update(Address)
        .where(Address.city == "Eveville")
        .values(street="555 Updated Lane")
    )
    result = session.execute(stmt)
    print(f"√ Updated {result.rowcount} address")
    
    # Bulk update
    stmt = (
        update(User)
        .where(User.name.like("%Frank%"))
        .values(name="Frank (SQL Updated)")
    )
    result = session.execute(stmt)
    print(f"√ Bulk updated {result.rowcount} users")
    
    session.commit()

print_all_users()

# ==================== DELETE OPERATIONS ====================

print_separator("DELETE OPERATIONS")

# ORM-style deletes
print("DELETING RECORDS - ORM STYLE")
with Session(engine) as session:
    # Delete a user by object
    alice = session.query(User).filter_by(name="Alice").first()
    if alice:
        session.delete(alice)
        print(f"√ Deleted Alice (cascade deletes her addresses too)")
    
    # Bulk delete
    count = session.query(Address).filter(
        Address.city.like("%ville%")
    ).delete(synchronize_session="fetch")
    print(f"√ Bulk deleted {count} addresses containing 'ville'")
    
    session.commit()

# SQL Expression Language deletes
print("\nDELETING RECORDS - SQL EXPRESSION STYLE")
with Session(engine) as session:
    # Delete a user
    stmt = delete(User).where(User.name == "Eve.updated@example.com")
    result = session.execute(stmt)
    print(f"√ Deleted {result.rowcount} user (Eve)")
    
    # Bulk delete
    stmt = delete(User).where(User.name.like("%(Updated)%"))
    result = session.execute(stmt)
    print(f"√ Bulk deleted {result.rowcount} updated users")
    
    session.commit()

print_all_users()

print_separator("END OF DEMONSTRATION")