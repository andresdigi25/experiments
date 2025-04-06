# SQLAlchemy 2.0 Async PostgreSQL Demo with Docker

This project demonstrates SQLAlchemy 2.0's async capabilities with PostgreSQL using asyncpg, with all components containerized using Docker.

## Prerequisites

- Docker and Docker Compose
- Basic knowledge of SQL and SQLAlchemy

## Project Structure

```
.
├── README.md
├── Dockerfile                  # Dockerfile for the Python application
├── async_sqlalchemy_demo.py    # Main Python demo script
├── cleanup.sh                  # Script to clean up Docker resources
├── docker-compose.yml          # Docker Compose configuration for all services
├── requirements.txt            # Python dependencies
└── run.sh                      # Script to run the demo
```

## Getting Started

1. Make the scripts executable:

   ```bash
   chmod +x run.sh cleanup.sh
   ```

2. Run the demo:

   ```bash
   ./run.sh
   ```

   This will:
   - Build the Docker images
   - Start the PostgreSQL container
   - Run the demo application container

3. When you're done, clean up resources:

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

## Docker Setup

- **PostgreSQL**: Running in its own container with volume persistence
- **Python Application**: Containerized Python 3.11 application with all dependencies
- **Networking**: Custom Docker network to connect the containers
- **Health Checks**: Proper health checks for PostgreSQL to ensure it's ready before the application starts

## Database Connection

The application connects to PostgreSQL using the hostname `postgres`, which is the service name in the Docker Compose configuration. The database connection string is:

```
postgresql+asyncpg://postgres:postgres@postgres/sqlalchemy_demo
```

## Container Logs

You can view the logs of the running containers with:

```bash
docker-compose logs
```

Or for a specific service:

```bash
docker-compose logs postgres
docker-compose logs demo_app
```

## Troubleshooting

- **Container Startup Issues**: Check the logs with `docker-compose logs`
- **Connection Failures**: Ensure the PostgreSQL container is healthy with `docker ps`
- **Database Errors**: Connect to the PostgreSQL container for direct interaction:
  ```bash
  docker exec -it sqlalchemy_demo_postgres psql -U postgres -d sqlalchemy_demo
  ```