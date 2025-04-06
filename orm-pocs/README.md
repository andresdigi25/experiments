name,address,state,zip
John Doe,123 Main St,CA,90210
Jane Smith,456 Oak St,NY,10001

pip install sqlalchemy marshmallow click  
python cli.py sample_addresses.csv 1


# Create the database and table
python pymysql_script.py --user your_user --password your_pass create

# Import data from CSV
python pymysql_script.py --user your_user --password your_pass import people.csv

# Read the data
python pymysql_script.py --user your_user --password your_pass read


# Database CSV Import Examples

This project demonstrates how to import CSV data into different databases using various Python libraries.

## Setup Instructions

1. **Ensure you have the following installed**:
   - Docker and Docker Compose
   - Python 3.6 or higher
   - Required Python packages: `pymysql`, `psycopg2-binary`

2. **File organization**:
   Make sure you have all these files in the same directory:
   - `docker-compose.yml` - Docker Compose configuration for MySQL and PostgreSQL
   - `run-examples.sh` - Bash script to run all examples
   - `pymysql-cli.py` - PyMySQL CLI example
   - `psycopg2-cli.py` - Psycopg2 CLI example
   - `people.csv` - Sample CSV data (will be created by the script if not present)

## Running the Examples

### 1. Make the script executable:

```bash
chmod +x run-examples.sh
```

### 2. Run the script:

```bash
./run-examples.sh
```

This script will:
- Create a sample CSV file if it doesn't exist
- Start Docker containers for MySQL and PostgreSQL
- Run the PyMySQL example against MySQL
- Run the Psycopg2 example against PostgreSQL

### 3. Stop the containers when done:

```bash
docker-compose down
```

## Database Connection Information

### MySQL:
- Host: localhost
- Port: 3306
- Database: people_db
- Username: dbuser
- Password: dbpassword

### PostgreSQL:
- Host: localhost
- Port: 5432
- Database: people_db
- Username: dbuser
- Password: dbpassword

## Manual Execution

If you prefer to run the examples individually, you can use these commands:

### PyMySQL Example:
```bash
python pymysql-cli.py --host localhost --user dbuser --password dbpassword --db people_db create
python pymysql-cli.py --host localhost --user dbuser --password dbpassword --db people_db import people.csv
python pymysql-cli.py --host localhost --user dbuser --password dbpassword --db people_db read
```

### Psycopg2 Example:
```bash
python psycopg2-cli.py --host localhost --port 5432 --user dbuser --password dbpassword --db people_db create
python psycopg2-cli.py --host localhost --port 5432 --user dbuser --password dbpassword --db people_db import people.csv
python psycopg2-cli.py --host localhost --port 5432 --user dbuser --password dbpassword --db people_db read
```

## Troubleshooting

- If you encounter connection errors, ensure that the Docker containers are running properly
- Check container logs using `docker logs mysql-container` or `docker logs postgres-container`
- Verify that the port mappings match what is specified in the Docker Compose file