import argparse
import csv
import pymysql
from pymysql.cursors import DictCursor


def create_database(host: str, user: str, password: str, database: str) -> None:
    """Create the database and tables."""
    # Connect to MySQL
    connection = pymysql.connect(
        host=host,
        user=user,
        password=password
    )
    
    try:
        with connection.cursor() as cursor:
            # Create database if it doesn't exist
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS {database}")
            cursor.execute(f"USE {database}")
            
            # Create the people table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS people (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    name VARCHAR(100) NOT NULL,
                    address VARCHAR(200) NOT NULL,
                    state VARCHAR(2) NOT NULL,
                    zip VARCHAR(10) NOT NULL
                )
            """)
        
        connection.commit()
        print(f"Database and table created")
    finally:
        connection.close()


def import_csv(csv_path: str, host: str, user: str, password: str, database: str) -> None:
    """Import data from CSV file to the database."""
    # Read CSV file
    people = []
    with open(csv_path, 'r') as file:
        reader = csv.DictReader(file)
        for row in reader:
            people.append(row)
    
    # Connect to database
    connection = pymysql.connect(
        host=host,
        user=user,
        password=password,
        database=database
    )
    
    try:
        with connection.cursor() as cursor:
            # Insert data into database
            for person in people:
                cursor.execute(
                    "INSERT INTO people (name, address, state, zip) VALUES (%s, %s, %s, %s)",
                    (person['name'], person['address'], person['state'], person['zip'])
                )
        
        connection.commit()
        print(f"Imported {len(people)} records from {csv_path}")
    finally:
        connection.close()


def read_data(host: str, user: str, password: str, database: str) -> list:
    """Read all data from the database."""
    # Connect to database
    connection = pymysql.connect(
        host=host,
        user=user,
        password=password,
        database=database,
        cursorclass=DictCursor
    )
    
    try:
        with connection.cursor() as cursor:
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
        connection.close()


def main():
    parser = argparse.ArgumentParser(description="PyMySQL CLI for CSV Import")
    parser.add_argument("--host", default="localhost", help="MySQL host")
    parser.add_argument("--user", required=True, help="MySQL user")
    parser.add_argument("--password", required=True, help="MySQL password")
    parser.add_argument("--db", default="people_db", help="MySQL database name")
    
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
        create_database(args.host, args.user, args.password, args.db)
    elif args.command == "import":
        import_csv(args.csv_file, args.host, args.user, args.password, args.db)
    elif args.command == "read":
        read_data(args.host, args.user, args.password, args.db)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()