import argparse
import csv
import os
from typing import List, Optional

from sqlmodel import Field, Session, SQLModel, create_engine, select


# Define the Person model
class Person(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    address: str
    state: str
    zip: str


def create_database(db_path: str) -> None:
    """Create the database and tables."""
    engine = create_engine(f"sqlite:///{db_path}")
    SQLModel.metadata.create_all(engine)
    print(f"Database created at {db_path}")


def import_csv(csv_path: str, db_path: str) -> None:
    """Import data from CSV file to the database."""
    engine = create_engine(f"sqlite:///{db_path}")
    
    # Read CSV file
    people = []
    with open(csv_path, 'r') as file:
        reader = csv.DictReader(file)
        for row in reader:
            people.append(Person(**row))
    
    # Insert data into database
    with Session(engine) as session:
        for person in people:
            session.add(person)
        session.commit()
    
    print(f"Imported {len(people)} records from {csv_path}")


def read_data(db_path: str) -> List[Person]:
    """Read all data from the database."""
    engine = create_engine(f"sqlite:///{db_path}")
    
    with Session(engine) as session:
        statement = select(Person)
        people = session.exec(statement).all()
        
        if not people:
            print("No records found in the database.")
        else:
            print(f"Found {len(people)} records:")
            for person in people:
                print(f"ID: {person.id}, Name: {person.name}, Address: {person.address}, State: {person.state}, ZIP: {person.zip}")
        
        return people


def main():
    parser = argparse.ArgumentParser(description="SQLModel CLI for CSV Import")
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