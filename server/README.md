# Bruno AI Server

FastAPI backend server for Bruno AI - an AI-powered mobile application for household food management.

## Development

```bash
# Install dependencies
poetry install

# Run development server
poetry run uvicorn main:app --reload
```

## Dependencies

- FastAPI: Web framework
- SQLAlchemy: ORM
- PostgreSQL (asyncpg): Database
- Alembic: Database migrations
- Authentication: python-jose, passlib
- Testing: pytest, httpx
