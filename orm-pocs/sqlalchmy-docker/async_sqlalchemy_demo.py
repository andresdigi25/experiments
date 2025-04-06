"""
SQLAlchemy 2.0 Async CRUD Operations with PostgreSQL
This script demonstrates both ORM-style and SQL Expression Language approaches
for Create, Read, Update, and Delete operations using async/await with PostgreSQL.
"""

import asyncio
from typing import List, Optional
from sqlalchemy import String, Integer, ForeignKey, select, insert, update, delete
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

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

def print_separator(message: str) -> None:
    """Print a separator with a message."""
    print("\n" + "="*80)
    print(f" {message} ".center(80, "="))
    print("="*80 + "\n")

async def print_all_users(session: AsyncSession) -> None:
    """Print all users in the database with their addresses."""
    result = await session.execute(select(User).order_by(User.id))
    users = result.scalars().all()
    
    print("\nCurrent users in database:")
    if not users:
        print("  No users found.")
        return
        
    for user in users:
        print(f"  - {user}")
        # Use a separate query to get addresses to avoid the greenlet issue
        address_result = await session.execute(
            select(Address).where(Address.user_id == user.id)
        )
        addresses = address_result.scalars().all()
        for addr in addresses:
            print(f"    * {addr}")
    print()

async def setup_database(engine):
    """Create all tables in the database."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    print("Database tables created")

async def demo_create_operations(async_session):
    """Demonstrate create operations."""
    print_separator("CREATE OPERATIONS")

    # ORM-style inserts
    print("CREATING RECORDS - ORM STYLE")
    async with async_session() as session:
        async with session.begin():
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
            for user in users:
                session.add(user)
            
        print("√ Added Alice, Bob and Charlie with addresses (ORM style)")

    # SQL Expression Language inserts
    print("\nCREATING RECORDS - SQL EXPRESSION STYLE")
    async with async_session() as session:
        async with session.begin():
            # Insert a single user
            stmt = insert(User).values(name="Dave", email="dave@example.com")
            result = await session.execute(stmt)
            
            # Get the user we just inserted to get its ID
            dave_result = await session.execute(
                select(User).where(User.name == "Dave")
            )
            dave = dave_result.scalar_one()
            
            # Insert address for Dave
            stmt = insert(Address).values(street="321 Elm St", city="Daveland", user_id=dave.id)
            await session.execute(stmt)
            
            # Insert multiple users at once
            stmt = insert(User).values([
                {"name": "Eve", "email": "eve@example.com"},
                {"name": "Frank", "email": "frank@example.com"}
            ])
            await session.execute(stmt)
            
            # Add an address for Eve
            eve_result = await session.execute(select(User).where(User.name == "Eve"))
            eve = eve_result.scalar_one()
            stmt = insert(Address).values(street="555 Apple Lane", city="Eveville", user_id=eve.id)
            await session.execute(stmt)
            
        print("√ Added Dave, Eve and Frank with addresses (SQL Expression style)")

    async with async_session() as session:
        await print_all_users(session)

async def demo_read_operations(async_session):
    """Demonstrate read operations."""
    print_separator("READ OPERATIONS")

    # ORM-style reads
    print("READING RECORDS - ORM STYLE")
    async with async_session() as session:
        # Get all users
        result = await session.execute(select(User))
        users = result.scalars().all()
        print(f"√ Found {len(users)} users")
        
        # Get user by primary key
        alice_result = await session.execute(select(User).where(User.name == "Alice"))
        alice = alice_result.scalar_one()
        alice_by_id = await session.get(User, alice.id)
        print(f"√ Found user by primary key: {alice_by_id}")
        
        # Filter by a condition
        result = await session.execute(select(User).where(User.name == "Bob"))
        bob = result.scalar_one()
        print(f"√ Found user by name: {bob}")
        
        # More complex filtering
        result = await session.execute(select(User).where(User.name.like("C%")))
        c_users = result.scalars().all()
        print(f"√ Found {len(c_users)} users starting with 'C'")
        
        # Join query
        stmt = select(User, Address).join(Address)
        result = await session.execute(stmt)
        users_with_addresses = result.all()
        print(f"√ Found {len(users_with_addresses)} user-address pairs")
        for user, address in users_with_addresses[:2]:  # Show just first two
            print(f"  - {user.name} lives at {address.street}, {address.city}")

    # SQL Expression Language reads
    print("\nREADING RECORDS - SQL EXPRESSION STYLE")
    async with async_session() as session:
        # Get all users
        stmt = select(User)
        result = await session.execute(stmt)
        users = result.scalars().all()
        print(f"√ Found {len(users)} users")
        
        # Get by primary key
        stmt = select(User).where(User.id == alice.id)
        result = await session.execute(stmt)
        alice = result.scalar_one()
        print(f"√ Found user by primary key: {alice}")
        
        # Filter by condition
        stmt = select(User).where(User.name == "Bob")
        result = await session.execute(stmt)
        bob = result.scalar_one()
        print(f"√ Found user by name: {bob}")
        
        # More complex filtering
        stmt = select(User).where(User.name.like("E%"))
        result = await session.execute(stmt)
        e_users = result.scalars().all()
        print(f"√ Found {len(e_users)} users starting with 'E'")
        
        # Join query
        stmt = select(User, Address).join(Address)
        result = await session.execute(stmt)
        user_addresses = result.all()
        print(f"√ Found {len(user_addresses)} user-address pairs")
        for user, address in user_addresses[:2]:  # Show just first two
            print(f"  - {user.name} lives at {address.street}, {address.city}")

async def demo_update_operations(async_session):
    """Demonstrate update operations."""
    print_separator("UPDATE OPERATIONS")

    # ORM-style updates
    print("UPDATING RECORDS - ORM STYLE")
    async with async_session() as session:
        async with session.begin():
            # Update a single user
            result = await session.execute(select(User).where(User.name == "Alice"))
            alice = result.scalar_one()
            if alice:
                alice.email = "alice.updated@example.com"
                print(f"√ Updated Alice's email to {alice.email}")
            
            # Update user's address
            result = await session.execute(select(User).where(User.name == "Bob"))
            bob = result.scalar_one()
            
            # Get Bob's addresses
            addr_result = await session.execute(
                select(Address).where(Address.user_id == bob.id)
            )
            addresses = addr_result.scalars().all()
            
            if addresses:
                addresses[0].street = "456 Updated Ave"
                print(f"√ Updated Bob's address to {addresses[0].street}")
            
            # Bulk update with filter
            stmt = (
                update(User)
                .where(User.name.in_(["Charlie", "Dave"]))
                .values(name=User.name + " (Updated)")
            )
            result = await session.execute(stmt)
            print(f"√ Bulk updated {result.rowcount} users")

    # SQL Expression Language updates
    print("\nUPDATING RECORDS - SQL EXPRESSION STYLE")
    async with async_session() as session:
        async with session.begin():
            # Update a single user
            stmt = (
                update(User)
                .where(User.name == "Eve")
                .values(email="eve.updated@example.com")
            )
            result = await session.execute(stmt)
            print(f"√ Updated {result.rowcount} user (Eve)")
            
            # Update address
            stmt = (
                update(Address)
                .where(Address.city == "Eveville")
                .values(street="555 Updated Lane")
            )
            result = await session.execute(stmt)
            print(f"√ Updated {result.rowcount} address")
            
            # Bulk update
            stmt = (
                update(User)
                .where(User.name.like("%Frank%"))
                .values(name="Frank (SQL Updated)")
            )
            result = await session.execute(stmt)
            print(f"√ Bulk updated {result.rowcount} users")

    async with async_session() as session:
        await print_all_users(session)

async def demo_delete_operations(async_session):
    """Demonstrate delete operations."""
    print_separator("DELETE OPERATIONS")

    # ORM-style deletes
    print("DELETING RECORDS - ORM STYLE")
    async with async_session() as session:
        async with session.begin():
            # Delete a user by object
            result = await session.execute(select(User).where(User.name == "Alice"))
            alice = result.scalar_one_or_none()
            if alice:
                await session.delete(alice)
                print(f"√ Deleted Alice (cascade deletes her addresses too)")
            
            # Bulk delete
            stmt = delete(Address).where(Address.city.like("%ville%"))
            result = await session.execute(stmt)
            print(f"√ Bulk deleted {result.rowcount} addresses containing 'ville'")

    # SQL Expression Language deletes
    print("\nDELETING RECORDS - SQL EXPRESSION STYLE")
    async with async_session() as session:
        async with session.begin():
            # Delete a user
            stmt = delete(User).where(User.email == "eve.updated@example.com")
            result = await session.execute(stmt)
            print(f"√ Deleted {result.rowcount} user (Eve)")
            
            # First, find all users to delete to access their addresses
            stmt = select(User).where(User.name.like("%(Updated)%"))
            result = await session.execute(stmt)
            users_to_delete = result.scalars().all()
            
            # Delete their addresses first (could also use a join delete)
            for user in users_to_delete:
                # Delete all addresses for this user
                stmt = delete(Address).where(Address.user_id == user.id)
                addr_result = await session.execute(stmt)
                print(f"  - Deleted {addr_result.rowcount} addresses for {user.name}")
            
            # Now delete the users
            stmt = delete(User).where(User.name.like("%(Updated)%"))
            result = await session.execute(stmt)
            print(f"√ Bulk deleted {result.rowcount} updated users")
    
    async with async_session() as session:
        await print_all_users(session)

async def main():
    """Main entry point for the demo."""
    print("SQLAlchemy 2.0 Async Demo with PostgreSQL")
    print("=======================================")
    
    # Create async engine for PostgreSQL
    engine = create_async_engine(
        "postgresql+asyncpg://postgres:postgres@localhost/sqlalchemy_demo",
        echo=False
    )
    
    # Create session factory
    async_session = async_sessionmaker(
        engine, 
        expire_on_commit=False,
        class_=AsyncSession
    )
    
    try:
        # Setup database (create tables)
        await setup_database(engine)
        
        # Run the demos
        await demo_create_operations(async_session)
        await demo_read_operations(async_session)
        await demo_update_operations(async_session)
        await demo_delete_operations(async_session)
        
        print_separator("DEMO COMPLETED SUCCESSFULLY")
    except Exception as e:
        print(f"\nERROR: {type(e).__name__}: {e}")
        print("Demo failed.")
    finally:
        # Dispose of the engine
        await engine.dispose()

if __name__ == "__main__":
    asyncio.run(main())