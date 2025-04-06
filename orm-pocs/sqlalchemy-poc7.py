"""
SQLAlchemy 2.0 Async CRUD Operations Demonstration
This script shows both ORM-style and SQL Expression Language approaches
for Create, Read, Update, and Delete operations using async/await.

IMPORTANT: Before running this script, install:
    pip install sqlalchemy aiosqlite greenlet
"""

import os
import asyncio
import sqlite3  # For manual DB cleanup
from typing import List, Optional

# SQLAlchemy imports
from sqlalchemy import String, Integer, ForeignKey, select, insert, update, delete
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

# ==================== MODEL DEFINITIONS ====================

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

# ==================== HELPER FUNCTIONS ====================

def print_separator(message: str) -> None:
    """Print a separator with a message."""
    print("\n" + "="*80)
    print(f" {message} ".center(80, "="))
    print("="*80 + "\n")

# ==================== MAIN ASYNC FUNCTION ====================

async def run_demo():
    """Main async function to run the entire demo."""
    
    # Database setup - manually remove old DB file if it exists
    db_path = "sqlalchemy_async_demo.db"
    if os.path.exists(db_path):
        try:
            os.remove(db_path)
        except OSError as e:
            print(f"Warning: Could not remove existing DB: {e}")
    
    # Create engine with explicit connection arguments
    engine = create_async_engine(
        f"sqlite+aiosqlite:///{db_path}", 
        echo=False,
        connect_args={"check_same_thread": False}
    )
    
    # Create session factory
    AsyncSessionLocal = async_sessionmaker(
        bind=engine,
        expire_on_commit=False,
        class_=AsyncSession
    )
    
    # Create tables
    print("Creating database tables...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("Tables created.")

    # ==================== CREATE OPERATIONS ====================
    print_separator("CREATE OPERATIONS")
    
    # ORM-style inserts
    print("CREATING RECORDS - ORM STYLE")
    async with AsyncSessionLocal() as session:
        try:
            # Create a user with address
            alice = User(name="Alice", email="alice@example.com")
            alice.addresses = [Address(street="123 Main St", city="Wonderland")]
            session.add(alice)
            
            # Create more users
            bob = User(name="Bob", email="bob@example.com")
            bob.addresses = [Address(street="456 Oak Ave", city="Bobville")]
            session.add(bob)
            
            charlie = User(name="Charlie", email="charlie@example.com")
            charlie.addresses = [
                Address(street="789 Pine Rd", city="Charlietown"),
                Address(street="101 Beach Blvd", city="Vacation City")
            ]
            session.add(charlie)
            
            # Commit the transaction
            await session.commit()
            print("√ Added Alice, Bob and Charlie with addresses (ORM style)")
        except Exception as e:
            await session.rollback()
            print(f"Error in ORM-style inserts: {e}")
            raise

    # SQL Expression Language inserts
    print("\nCREATING RECORDS - SQL EXPRESSION STYLE")
    async with AsyncSessionLocal() as session:
        try:
            # Insert a single user
            stmt = insert(User).values(name="Dave", email="dave@example.com")
            result = await session.execute(stmt)
            
            # Get the ID (for SQLite this works)
            dave_id = result.inserted_primary_key[0]
            
            # Insert address for Dave
            addr_stmt = insert(Address).values(
                street="321 Elm St", 
                city="Daveland", 
                user_id=dave_id
            )
            await session.execute(addr_stmt)
            
            # Insert multiple users
            users_stmt = insert(User).values([
                {"name": "Eve", "email": "eve@example.com"},
                {"name": "Frank", "email": "frank@example.com"}
            ])
            await session.execute(users_stmt)
            
            # Commit transaction
            await session.commit()
            print("√ Added Dave, Eve and Frank (SQL Expression style)")
            
            # In a new transaction, add address for Eve
            result = await session.execute(select(User).where(User.name == "Eve"))
            eve = result.scalar_one()
            
            addr_stmt = insert(Address).values(
                street="555 Apple Lane",
                city="Eveville",
                user_id=eve.id
            )
            await session.execute(addr_stmt)
            await session.commit()
            print("√ Added address for Eve")
            
        except Exception as e:
            await session.rollback()
            print(f"Error in SQL Expression-style inserts: {e}")
            raise

    # Print all users
    print("\nCurrent users in database:")
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(User).order_by(User.id))
        users = result.scalars().all()
        
        for user in users:
            print(f"  - {user}")
            for addr in user.addresses:
                print(f"    * {addr}")

    # ==================== READ OPERATIONS ====================
    print_separator("READ OPERATIONS")
    
    # ORM-style reads
    print("READING RECORDS - ORM STYLE")
    async with AsyncSessionLocal() as session:
        try:
            # Get all users
            stmt = select(User)
            result = await session.execute(stmt)
            users = result.scalars().all()
            print(f"√ Found {len(users)} users")
            
            # Get user by ID
            alice = await session.get(User, 1)
            print(f"√ Found by ID: {alice}")
            
            # Filter by condition
            stmt = select(User).where(User.name == "Bob")
            result = await session.execute(stmt)
            bob = result.scalar_one()
            print(f"√ Found by name: {bob}")
            
            # Complex filter
            stmt = select(User).where(User.name.like("C%"))
            result = await session.execute(stmt)
            c_users = result.scalars().all()
            print(f"√ Found {len(c_users)} users starting with 'C'")
            
        except Exception as e:
            print(f"Error in ORM-style reads: {e}")
            raise
    
    # SQL Expression-style reads
    print("\nREADING RECORDS - SQL EXPRESSION STYLE")
    async with AsyncSessionLocal() as session:
        try:
            # Join query
            stmt = select(User, Address).join(Address)
            result = await session.execute(stmt)
            rows = result.all()
            print(f"√ Found {len(rows)} user-address pairs")
            
            for i, (user, address) in enumerate(rows[:3]):  # Show up to 3
                print(f"  {i+1}. {user.name} at {address.street}, {address.city}")
                
        except Exception as e:
            print(f"Error in SQL Expression-style reads: {e}")
            raise

    # ==================== UPDATE OPERATIONS ====================
    print_separator("UPDATE OPERATIONS")
    
    # ORM-style updates
    print("UPDATING RECORDS - ORM STYLE")
    async with AsyncSessionLocal() as session:
        try:
            # Update one user by loading and modifying
            result = await session.execute(select(User).where(User.name == "Alice"))
            alice = result.scalar_one()
            alice.email = "alice.updated@example.com"
            
            # Update address
            if alice.addresses:
                alice.addresses[0].street = "123 Updated St"
            
            await session.commit()
            print(f"√ Updated Alice's email to {alice.email}")
            print(f"√ Updated Alice's address to {alice.addresses[0].street}")
            
        except Exception as e:
            await session.rollback()
            print(f"Error in ORM-style updates: {e}")
            raise
    
    # SQL Expression-style updates
    print("\nUPDATING RECORDS - SQL EXPRESSION STYLE") 
    async with AsyncSessionLocal() as session:
        try:
            # Update with SQL Expression
            stmt = (
                update(User)
                .where(User.name == "Bob")
                .values(email="bob.updated@example.com")
            )
            result = await session.execute(stmt)
            
            # Bulk update
            stmt = (
                update(User)
                .where(User.name.in_(["Charlie", "Dave"]))
                .values(name=User.name + " (Updated)")
            )
            result = await session.execute(stmt)
            
            await session.commit()
            print(f"√ Updated users with SQL Expression style")
            
        except Exception as e:
            await session.rollback() 
            print(f"Error in SQL Expression-style updates: {e}")
            raise

    # Print users after updates
    print("\nUsers after updates:")
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(User).order_by(User.id))
        users = result.scalars().all()
        
        for user in users:
            print(f"  - {user}")
            for addr in user.addresses:
                print(f"    * {addr}")

    # ==================== DELETE OPERATIONS ====================
    print_separator("DELETE OPERATIONS")
    
    # ORM-style deletes
    print("DELETING RECORDS - ORM STYLE")
    async with AsyncSessionLocal() as session:
        try:
            # Delete a user object (cascades to addresses)
            result = await session.execute(select(User).where(User.name == "Frank"))
            frank = result.scalar_one()
            await session.delete(frank)
            
            await session.commit()
            print(f"√ Deleted Frank and his addresses")
            
        except Exception as e:
            await session.rollback()
            print(f"Error in ORM-style deletes: {e}")
            raise
    
    # SQL Expression-style deletes
    print("\nDELETING RECORDS - SQL EXPRESSION STYLE")
    async with AsyncSessionLocal() as session:
        try:
            # Delete with SQL Expression
            stmt = delete(Address).where(Address.city.like("%ville%"))
            result = await session.execute(stmt)
            count = result.rowcount
            
            await session.commit()
            print(f"√ Deleted {count} addresses with 'ville' in city name")
            
        except Exception as e:
            await session.rollback()
            print(f"Error in SQL Expression-style deletes: {e}")
            raise

    # Final database state
    print("\nFinal database state:")
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(User).order_by(User.id))
        users = result.scalars().all()
        
        for user in users:
            print(f"  - {user}")
            for addr in user.addresses:
                print(f"    * {addr}")

    print_separator("DEMO COMPLETED")
    
    # Properly close engine
    await engine.dispose()

# ==================== ENTRY POINT ====================

def main():
    """Entry point that runs the async demo."""
    try:
        # Clear event loop policy if needed for some environments
        # asyncio.set_event_loop_policy(None)
        
        # Run with asyncio
        asyncio.run(run_demo())
    except Exception as e:
        print(f"Error running async demo: {type(e).__name__}: {e}")
        # If you're getting greenlet errors, try this alternative:
        # loop = asyncio.new_event_loop()
        # asyncio.set_event_loop(loop)
        # loop.run_until_complete(run_demo())
        # loop.close()

if __name__ == "__main__":
    main()