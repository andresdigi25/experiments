
# Scrum Master Bot

A simple NLP-powered assistant for daily standups.

## Features

- Run daily standups for your team
- Track tasks, blockers, and progress
- Natural language processing for sentiment analysis and task extraction
- Two interfaces:
  - CLI: Rich terminal interface using Textual
  - API: RESTful API using FastAPI

## Installation

```bash
pip install scrummaster
```

## Usage
pip install -e .
python run.py --interface cli
python run.py --interface api --port 8000

# CLI
scrummaster-cli
# or
python -m scrummaster.cli

# API
scrummaster-api
# or
python -m scrummaster.api

### CLI Interface

```bash
# Start the CLI interface
scrummaster-cli
```

### API Interface

```bash
# Start the API server
scrummaster-api

# Access the API at http://localhost:8000
```

## API Documentation

When running the API server, you can access the auto-generated API documentation at:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Project Structure

- `scrummaster/core.py`: Core functionality and business logic
- `scrummaster/cli.py`: Terminal user interface using Textual
- `scrummaster/api.py`: RESTful API using FastAPI

## License

MIT
