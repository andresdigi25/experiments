#!/bin/bash

# Set default values
CSV_FILE="people.csv"
WAIT_TIME=15

# Database connection settings (match docker-compose.yml)
MYSQL_HOST="localhost"
MYSQL_PORT="3306"
MYSQL_USER="dbuser"
MYSQL_PASSWORD="dbpassword"
MYSQL_DB="people_db"

PG_HOST="localhost"
PG_PORT="5432"
PG_USER="dbuser"
PG_PASSWORD="dbpassword"
PG_DB="people_db"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Create the CSV file if it doesn't exist
if [ ! -f "$CSV_FILE" ]; then
    echo -e "${YELLOW}Creating sample CSV file '$CSV_FILE'...${NC}"
    cat > "$CSV_FILE" << EOF
name,address,state,zip
John Doe,123 Main St,CA,90210
Jane Smith,456 Oak St,NY,10001
EOF
    echo -e "${GREEN}CSV file created.${NC}"
fi

# Check if docker and docker-compose are installed
if ! command -v docker &> /dev/null || ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}Error: Docker and/or docker-compose are not installed.${NC}"
    exit 1
fi

# Check if required python packages are installed
echo -e "${BLUE}Checking required Python packages...${NC}"
pip install pymysql psycopg2-binary &> /dev/null
if [ $? -ne 0 ]; then
    echo -e "${RED}Error installing required packages.${NC}"
    exit 1
fi
echo -e "${GREEN}Required packages are installed.${NC}"

# Start Docker containers
echo -e "${YELLOW}Starting Docker containers for MySQL and PostgreSQL...${NC}"
docker-compose up -d

# Wait for containers to be ready
echo -e "${BLUE}Waiting $WAIT_TIME seconds for databases to be ready...${NC}"
sleep $WAIT_TIME

# Check if containers are healthy
MYSQL_HEALTHY=$(docker inspect --format='{{.State.Health.Status}}' mysql-container)
PG_HEALTHY=$(docker inspect --format='{{.State.Health.Status}}' postgres-container)

if [ "$MYSQL_HEALTHY" != "healthy" ] || [ "$PG_HEALTHY" != "healthy" ]; then
    echo -e "${YELLOW}Databases may not be fully initialized yet. This is OK, we'll proceed anyway.${NC}"
fi

echo -e "\n${GREEN}=== Running PyMySQL Example ===${NC}"
# Run PyMySQL example
echo -e "${BLUE}Creating database schema with PyMySQL...${NC}"
python pymysql-cli.py --host "$MYSQL_HOST" --user "$MYSQL_USER" --password "$MYSQL_PASSWORD" --db "$MYSQL_DB" create

echo -e "${BLUE}Importing data with PyMySQL...${NC}"
python pymysql-cli.py --host "$MYSQL_HOST" --user "$MYSQL_USER" --password "$MYSQL_PASSWORD" --db "$MYSQL_DB" import "$CSV_FILE"

echo -e "${BLUE}Reading data with PyMySQL...${NC}"
python pymysql-cli.py --host "$MYSQL_HOST" --user "$MYSQL_USER" --password "$MYSQL_PASSWORD" --db "$MYSQL_DB" read

echo -e "\n${GREEN}=== Running Psycopg2 Example ===${NC}"
# Run Psycopg2 example
echo -e "${BLUE}Creating database schema with Psycopg2...${NC}"
python psycopg2-cli.py --host "$PG_HOST" --port "$PG_PORT" --user "$PG_USER" --password "$PG_PASSWORD" --db "$PG_DB" create

echo -e "${BLUE}Importing data with Psycopg2...${NC}"
python psycopg2-cli.py --host "$PG_HOST" --port "$PG_PORT" --user "$PG_USER" --password "$PG_PASSWORD" --db "$PG_DB" import "$CSV_FILE"

echo -e "${BLUE}Reading data with Psycopg2...${NC}"
python psycopg2-cli.py --host "$PG_HOST" --port "$PG_PORT" --user "$PG_USER" --password "$PG_PASSWORD" --db "$PG_DB" read

echo -e "\n${GREEN}All examples completed successfully!${NC}"
echo -e "${YELLOW}To stop the Docker containers, run:${NC} docker-compose down"