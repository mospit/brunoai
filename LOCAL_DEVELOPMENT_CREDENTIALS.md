# Local Development - Minimal Credential Set

This document specifies the **exact** environment variables that must be populated for local end-to-end testing of the Bruno AI application.

## Core Required Variables

These variables are **absolutely required** for basic functionality:

### Database Configuration
```bash
# PostgreSQL Database URL
DB_URL="postgresql://user:password@localhost:5432/bruno_ai_v2"
```
**Default for local testing**: Uses Docker Postgres container as defined in `infra/docker-compose.yml`

### Authentication & Security
```bash
# JWT Secret for token signing/verification
JWT_SECRET="your-jwt-secret-key-here-make-it-long-and-secure"

# Application secret key for general cryptographic operations
APP_SECRET_KEY="your-app-secret-key-here-also-make-it-long-and-secure"
```
**Local Development Defaults**: Generate these once and reuse. Example:
```bash
JWT_SECRET="dev-jwt-secret-key-local-testing-only-not-for-production-use"
APP_SECRET_KEY="dev-app-secret-key-local-testing-only-not-for-production-use"
```

### AI/LLM Provider (Required for Recipe Suggestions)
```bash
# OpenAI API Key for recipe suggestions and AI features
OPENAI_API_KEY="sk-proj-your-openai-key-here"
```
**Alternative**: Any one of these AI providers will work:
- `ANTHROPIC_API_KEY` (for Claude models)
- `GOOGLE_API_KEY` (for Gemini models)
- `MISTRAL_API_KEY` (for Mistral models)

### Caching/Session Storage
```bash
# Redis URL for caching and session management
REDIS_URL="redis://localhost:6379"
```
**Default for local testing**: Standard Redis localhost URL (requires Redis server running)

## Quick Start Setup

### 1. Start Infrastructure Services
```bash
# Start PostgreSQL database
cd infra
docker-compose up -d postgres

# Start Redis (if not using Docker)
# On macOS: brew services start redis
# On Ubuntu: sudo systemctl start redis-server
# On Windows: Download and run Redis from https://redis.io/download
```

### 2. Create Environment File
Create `.env` file in project root:
```bash
# Copy example and modify
cp .env.example .env

# Edit .env with the minimal required values:
DB_URL="postgresql://user:password@localhost:5432/bruno_ai_v2"
JWT_SECRET="dev-jwt-secret-key-local-testing-only-not-for-production-use"
APP_SECRET_KEY="dev-app-secret-key-local-testing-only-not-for-production-use"
OPENAI_API_KEY="your-actual-openai-api-key"
REDIS_URL="redis://localhost:6379"
```

### 3. Initialize Database
```bash
cd server
# Install dependencies
poetry install

# Run Alembic migrations
poetry run alembic upgrade head
```

### 4. Start Backend Server
```bash
cd server
poetry run uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 5. Start Flutter Client
```bash
cd client
flutter pub get
flutter run
```

## What Each Variable Enables

| Variable | Enables | Without It |
|----------|---------|------------|
| `DB_URL` | User accounts, pantry data, all CRUD operations | **Total failure** - no data persistence |
| `JWT_SECRET` | Login/signup, API authentication | **Authentication broken** - cannot login |
| `APP_SECRET_KEY` | General security operations, session management | **Security features broken** |
| `OPENAI_API_KEY` | Recipe suggestions, AI-powered features | Basic CRUD works, but **no AI features** |
| `REDIS_URL` | Session storage, caching, performance optimization | Slower performance, **sessions may not persist** |

## Sane Local Defaults

The following values are pre-configured for local development and require no changes:

```bash
# Already set in config.py with sensible defaults
REDIS_URL="redis://localhost:6379"  # Default Redis URL

# Already configured in docker-compose.yml
POSTGRES_USER="user"
POSTGRES_PASSWORD="password"
POSTGRES_DB="bruno_ai_v2"
# Results in: DB_URL="postgresql://user:password@localhost:5432/bruno_ai_v2"

# Server configuration (already in config.py)
HOST="0.0.0.0"
PORT=8000
ENVIRONMENT="development"
DEBUG=false
LOG_LEVEL="info"
```

## Optional Variables for Enhanced Testing

These are not required for basic functionality but enhance the experience:

```bash
# Firebase Authentication (optional - has fallback)
FIREBASE_WEB_API_KEY="your-firebase-web-api-key"
GCP_CREDENTIALS_JSON="{}"  # Firebase service account JSON
GCP_PROJECT_ID="your-gcp-project-id"

# Additional AI providers (alternatives to OpenAI)
ANTHROPIC_API_KEY="sk-ant-api03-your-key"
GOOGLE_API_KEY="your-google-gemini-key"
MISTRAL_API_KEY="your-mistral-key"

# Voice features (not required for core functionality)
VOXTRAL_API_KEY="your-voxtral-stt-key"
ELEVENLABS_API_KEY="your-elevenlabs-tts-key"

# External integrations
INSTACART_API_KEY="your-instacart-key"
MEM0_API_KEY="your-mem0-key"
```

## Testing Validation Checklist

With the minimal credentials set, you should be able to:

- [ ] **Launch Postgres container**: `docker-compose up -d postgres`
- [ ] **Run Alembic migrations**: `alembic upgrade head`
- [ ] **Start FastAPI backend**: Server starts on `http://localhost:8000`
- [ ] **Access API docs**: Visit `http://localhost:8000/docs`
- [ ] **User registration**: Create new account via API or Flutter app
- [ ] **User login**: Authenticate and receive JWT tokens
- [ ] **Pantry CRUD operations**: Add, view, update, delete pantry items
- [ ] **Basic recipe suggestions**: AI-powered recipe recommendations (requires LLM provider)
- [ ] **Flutter client connection**: Mobile app connects to localhost:8000
- [ ] **End-to-end flow**: Register → Login → Add pantry items → Get recipe suggestions

## Troubleshooting

### Database Connection Issues
```bash
# Verify Postgres is running
docker ps | grep postgres

# Check database exists
docker exec -it <postgres-container-id> psql -U user -d bruno_ai_v2 -c "\dt"
```

### Redis Connection Issues
```bash
# Test Redis connection
redis-cli ping
# Should return: PONG
```

### Authentication Issues
- Ensure `JWT_SECRET` and `APP_SECRET_KEY` are sufficiently long (minimum 32 characters)
- Check server logs for authentication errors
- Verify tokens are being stored in Flutter secure storage

### AI Features Not Working
- Verify your AI provider API key is valid and has credits
- Check server logs for API errors
- Ensure the provider API key environment variable matches the provider you want to use

## Security Notes for Local Development

⚠️ **The credentials listed in this document are for LOCAL DEVELOPMENT ONLY**

- Never use these values in production
- The example JWT/App secrets are intentionally marked as development-only
- Always use strong, unique secrets for production deployments
- Consider using `.env.local` for your personal development credentials to avoid committing them
