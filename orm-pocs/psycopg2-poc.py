import argparse
import csv
import psycopg2
from psycopg2.extras import RealDictCursor


def create_database(host: str, user: str, password: str, database: str, port: int = 5432) -> None:
    """Create the database and tables."""
    # Connect to PostgreSQL
    conn = psycopg2.connect(
        host=host,
        user=user,
        password=password,
        port=port,
        # Connect to the 'postgres' database initially to create a new database
        database='postgres'
    )
    conn.autocommit = True
    
    try:
        with conn.cursor() as cursor:
            # Check if database exists
            cursor.execute("SELECT 1 FROM pg_catalog.pg_database WHERE datname = %s", (database,))
            exists = cursor.fetchone()
            
            if not exists:
                cursor.execute(f"CREATE DATABASE {database}")
                print(f"Created database {database}")
            else:
                print(f"Database {database} already exists")
    finally:
        conn.close()
    
    # Connect to the newly created database
    conn = psycopg2.connect(
        host=host,
        user=user,
        password=password,
        port=port,
        database=database
    )
    
    try:
        with conn.cursor() as cursor:
            # Create the people table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS people (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(100) NOT NULL,
                    address VARCHAR(200) NOT NULL,
                    state VARCHAR(2) NOT NULL,
                    zip VARCHAR(10) NOT NULL
                )
            """)
        
        conn.commit()
        print("Table 'people' created successfully")
    finally:
        conn.close()


def import_csv(csv_path: str, host: str, user: str, password: str, database: str, port: int = 5432) -> None:
    """Import data from CSV file to the database."""
    # Read CSV file
    people = []
    with open(csv_path, 'r') as file:
        reader = csv.DictReader(file)
        for row in reader:
            people.append(row)
    
    # Connect to database
    conn = psycopg2.connect(
        host=host,
        user=user,
        password=password,
        port=port,
        database=database
    )
    
    try:
        with conn.cursor() as cursor:
            # Insert data into database
            for person in people:
                cursor.execute(
                    "INSERT INTO people (name, address, state, zip) VALUES (%s, %s, %s, %s)",
                    (person['name'], person['address'], person['state'], person['zip'])
                )
        
        conn.commit()
        print(f"Imported {len(people)} records from {csv_path}")
    finally:
        conn.close()


def read_data(host: str, user: str, password: str, database: str, port: int = 5432) -> list:
    """Read all data from the database."""
    # Connect to database
    conn = psycopg2.connect(
        host=host,
        user=user,
        password=password,
        port=port,
        database=database,
        cursor_factory=RealDictCursor
    )
    
    try:
        with conn.cursor() as cursor:
            # Read all data
            cursor.execute("SELECT * FROM people")
            people = cursor.fetchall()
            
            if not people:
                print("No records found in the database.")
            else:
                print(f"Found {len(people)} records:")
                for person in people:
                    print(f"ID: {person['id']}, Name: {person['name']}, Address: {person['address']}, State: {person['state']}, ZIP: {person['zip']}")
            
            return people
    finally:
        conn.close()


def main():
    parser = argparse.ArgumentParser(description="Psycopg2 CLI for CSV Import")
    parser.add_argument("--host", default="localhost", help="PostgreSQL host")
    parser.add_argument("--port", type=int, default=5432, help="PostgreSQL port")
    parser.add_argument("--user", required=True, help="PostgreSQL user")
    parser.add_argument("--password", required=True, help="PostgreSQL password")
    parser.add_argument("--db", default="people_db", help="PostgreSQL database name")
    
    subparsers = parser.add_subparsers(dest="command", help="Commands")
    
    # Create database command
    create_parser = subparsers.add_parser("create", help="Create the database and table")
    
    # Import CSV command
    import_parser = subparsers.add_parser("import", help="Import data from CSV")
    import_parser.add_argument("csv_file", help="Path to CSV file")
    
    # Read data command
    read_parser = subparsers.add_parser("read", help="Read data from the database")
    
    args = parser.parse_args()
    
    if args.command == "create":
        create_database(args.host, args.user, args.password, args.db, args.port)
    elif args.command == "import":
        import_csv(args.csv_file, args.host, args.user, args.password, args.db, args.port)
    elif args.command == "read":
        read_data(args.host, args.user, args.password, args.db, args.port)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()