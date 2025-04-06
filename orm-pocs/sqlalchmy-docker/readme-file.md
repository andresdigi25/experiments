# SQLAlchemy 2.0 Async PostgreSQL Demo

This project demonstrates SQLAlchemy 2.0's async capabilities with PostgreSQL using asyncpg. It illustrates how to perform CRUD operations using both ORM-style and SQL Expression Language approaches in an asynchronous context.

## Prerequisites

- Python 3.7+
- Docker and Docker Compose
- Basic knowledge of SQL and SQLAlchemy

## Project Structure

```
.
├── README.md
├── async_sqlalchemy_demo.py    # Main Python demo script
├── cleanup.sh                  # Script to clean up resources
├── docker-compose.yml          # Docker Compose configuration for PostgreSQL
├── run.sh                      # Script to run the demo
└── setup.sh                    # Script to set up the environment
```

## Getting Started

1. Make the scripts executable:

   ```bash
   chmod +x setup.sh run.sh cleanup.sh
   ```

2. Run the setup script to create a virtual environment, install dependencies, and start PostgreSQL:

   ```bash
   ./setup.sh
   ```

3. Run the demo:

   ```bash
   ./run.sh
   ```

4. When you're done, clean up resources:

   ```bash
   ./cleanup.sh
   ```

## Features Demonstrated

The demo showcases the following SQLAlchemy 2.0 features:

- **Declarative Models**: Using modern type hints with `mapped_column`
- **Relationships**: One-to-many relationships with cascading deletes
- **CRUD Operations**:
  - Create: Both ORM and SQL Expression approaches
  - Read: Various querying techniques including filtering and joins
  - Update: Both individual and bulk updates
  - Delete: Both individual and bulk deletes
- **Async/Await**: Using SQLAlchemy's async API
- **Transaction Management**: Using async context managers

## Key Concepts

- **PostgreSQL with asyncpg**: Using a production-grade database with a high-performance async driver
- **Docker Integration**: Running PostgreSQL in a container for isolation and portability
- **Type Safety**: Using SQLAlchemy 2.0's improved type annotations
- **Modern Python Practices**: Leveraging async/await, type hints, and context managers

## Common Issues and Solutions

- **MissingGreenlet Error**: Make sure greenlet is installed and compatible with your Python version
- **Database Connectivity**: Ensure the PostgreSQL container is running with `docker ps`
- **PostgreSQL Authentication**: Check the credentials in the connection string match those in docker-compose.yml

## Additional Resources

- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/en/20/)
- [asyncpg Documentation](https://magicstack.github.io/asyncpg/current/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
