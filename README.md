# Enterprise AI Knowledge OS

A production-grade AI knowledge management platform built with Next.js, FastAPI, PyTorch, and ChromaDB.

## Quick Start

### Prerequisites

- Node.js 20+
- Python 3.11+
- MySQL 8.0+
- Docker & Docker Compose (optional)

### Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/macOS

# Install dependencies
pip install -r requirements.txt

# Copy environment config
cp ../.env.example ../.env
# Edit .env with your MySQL credentials

# Run database migrations
alembic upgrade head

# Start the server
uvicorn app.main:app --reload --port 8000
```

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

### Docker Setup

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f
```

## Architecture

```
knowledge-os/
├── backend/          # FastAPI + Python (API, ML, services)
│   ├── app/
│   │   ├── api/      # API routers (v1)
│   │   ├── core/     # Security, middleware, exceptions
│   │   ├── db/       # SQLAlchemy models + session
│   │   ├── ml/       # PyTorch, sklearn, embeddings
│   │   ├── schemas/  # Pydantic request/response models
│   │   ├── services/ # Business logic layer
│   │   ├── vectorstore/  # ChromaDB abstraction
│   │   └── workers/  # Background processors
│   └── alembic/      # Database migrations
├── frontend/         # Next.js + React + TypeScript
│   └── src/
│       ├── app/      # Pages (App Router)
│       ├── components/  # Reusable UI components
│       ├── lib/      # API client, utilities
│       ├── stores/   # Zustand state management
│       └── types/    # TypeScript type definitions
└── docker-compose.yml
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/api/v1/auth/register` | POST | Register new user |
| `/api/v1/auth/login` | POST | Login |
| `/api/v1/auth/me` | GET | Current user profile |
| `/api/v1/workspaces/` | GET/POST | List/create workspaces |
| `/api/v1/documents/upload` | POST | Upload document |
| `/api/v1/search/` | POST | Semantic search |
| `/api/v1/chat/` | POST | RAG chat |
| `/api/v1/chat/stream` | POST | Streaming chat (SSE) |
| `/api/v1/models/` | GET | List available LLMs |

## Tech Stack

- **Frontend**: Next.js 15, React, TypeScript, TailwindCSS v4, shadcn/ui, Zustand, React Query
- **Backend**: FastAPI, SQLAlchemy (async), Alembic, JWT auth
- **AI/ML**: PyTorch, HuggingFace, sentence-transformers, scikit-learn
- **Database**: MySQL 8.0, ChromaDB
- **LLM**: Ollama (Llama 3, Mistral, Phi, DeepSeek)
