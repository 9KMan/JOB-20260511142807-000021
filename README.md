# Product Matcher MVP

AI-powered product matching and search system for deduplicating supplier product records.

## Quick Start

### Backend

```bash
cd backend
pip install -r requirements.txt
# Set DATABASE_URL and OPENAI_API_KEY in .env
python app.py
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

## Architecture

- Flask API + React (Vite) frontend
- PostgreSQL + pgvector for vector similarity search
- TF-IDF for deduplication, OpenAI embeddings for semantic matching