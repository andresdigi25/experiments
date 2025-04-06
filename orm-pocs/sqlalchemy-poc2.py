import argparse
import csv
import os
from typing import List, Optional

from sqlalchemy import create_engine, select, Table, Column, String, Integer, MetaData
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, Session


# Define the base class for SQLAlchemy models
class Base(DeclarativeBase):
    pass


# Define the Person model
class Person(Base):
    __tablename__ = "people"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    address: Mapped[str] = mapped_column(String(200))
    state: Mapped[str] = mapped_column(String(2))
    zip: Mapped[str] = mapped_column(String(10))
    
    def __repr__(self) -> str:
        return f"Person(id={self.id!r}, name={self.name!r}, state={self.state!r}, zip={self.zip!r})"


def create_database(db_path: str) -> None:
    """Create the database and tables."""
    engine = create_engine(f"sqlite:///{db_path}")
    Base.metadata.create_all(engine)
    print(f"Database created at {db_path}")


def import_csv(csv_path: str, db_path: str) -> None:
    """Import data from CSV file to the database."""
    engine = create_engine(f"sqlite:///{db_path}")
    
    # Read CSV file
    people = []
    with open(csv_path, 'r') as file:
        reader = csv.DictReader(file)
        for row in reader:
            people.append(row)
    
    # Insert data into database
    with Session(engine) as session:
        for person_data in people:
            person = Person(
                name=person_data['name'],
                address=person_data['address'],
                state=person_data['state'],
                zip=person_data['zip']
            )
            session.add(person)
        session.commit()
    
    print(f"Imported {len(people)} records from {csv_path}")


def read_data(db_path: str) -> List[Person]:
    """Read all data from the database."""
    engine = create_engine(f"sqlite:///{db_path}")
    
    with Session(engine) as session:
        stmt = select(Person)
        people = session.execute(stmt).scalars().all()
        
        if not people:
            print("No records found in the database.")
        else:
            print(f"Found {len(people)} records:")
            for person in people:
                print(f"ID: {person.id}, Name: {person.name}, Address: {person.address}, State: {person.state}, ZIP: {person.zip}")
        
        return people


def main():
    parser = argparse.ArgumentParser(description="SQLAlchemy CLI for CSV Import")
    parser.add_argument("--db", default="people.db", help="Path to SQLite database file")
    
    subparsers = parser.add_subparsers(dest="command", help="Commands")
    
    # Create database command
    create_parser = subparsers.add_parser("create", help="Create the database")
    
    # Import CSV command
    import_parser = subparsers.add_parser("import", help="Import data from CSV")
    import_parser.add_argument("csv_file", help="Path to CSV file")
    
    # Read data command
    read_parser = subparsers.add_parser("read", help="Read data from the database")
    
    args = parser.parse_args()
    
    if args.command == "create":
        create_database(args.db)
    elif args.command == "import":
        import_csv(args.csv_file, args.db)
    elif args.command == "read":
        read_data(args.db)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()