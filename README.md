# Doc Intelligence API

Upload a PDF, ask it questions, get answers pulled straight from the document. That's the whole idea.

This is a RAG (Retrieval-Augmented Generation) system built from scratch to actually understand what happens under the hood, not just import a library and call it a day.

## What it does

1. You sign up and log in (JWT auth, passwords hashed with bcrypt, nothing stored in plain text)
2. You upload a PDF
3. It gets split into chunks and each chunk gets turned into a vector embedding
4. You ask a question in plain English
5. The API finds the most relevant chunks using vector similarity search in Postgres
6. Those chunks get handed to an LLM, which streams back an answer grounded in your actual document

No hallucinated answers from thin air. If the document doesn't say it, the model says it doesn't know.

## Stack

- **FastAPI** for the API layer, fully async
- **PostgreSQL + pgvector** for storage, including the embeddings themselves
- **SQLAlchemy 2.0 + Alembic** for the ORM and migrations
- **Mistral AI** for embeddings and chat completions
- **JWT** for auth
- **Background tasks** so uploads don't sit there waiting on embedding generation
- **Docker** for deployment

## Why it's built this way

**Schemas are separate from models.** The database knows about hashed passwords. The API response never does. That separation isn't an accident, it's what keeps sensitive fields from accidentally leaking in a JSON response.

**Chunking has overlap.** If you split text into clean, non-overlapping blocks, you risk cutting a sentence in half right where the important part was. A little overlap between chunks means context doesn't get lost at the seams.

**Uploads don't block on embeddings.** Turning text into vectors takes a few seconds per chunk. Nobody wants to sit there watching a spinner. The file gets saved, the response comes back immediately, and the actual processing happens in the background. Check the status endpoint if you want to know when it's done.

**Every document search is scoped to the logged-in user.** Multi-tenant isolation isn't bolted on after the fact, it's baked into the query itself.

## Running it locally

```bash
git clone <your-repo-url>
cd doc-intelligence-api
python -m venv venv
venv\Scripts\activate   # Windows
pip install -r requirements.txt
```

Create a `.env` file:

```
DATABASE_URL=postgresql+asyncpg://user:password@host/dbname
SECRET_KEY=some-random-string
ACCESS_TOKEN_EXPIRE_MINUTES=60
MISTRAL_API_KEY=your-mistral-key
```

Run the migrations, then start the server:

```bash
alembic upgrade head
uvicorn app.main:app --reload
```

Open `http://127.0.0.1:8000/docs` and you're in.

## API endpoints

| Method | Endpoint | What it does |
|---|---|---|
| POST | `/auth/signup` | Create an account |
| POST | `/auth/login` | Get a JWT token |
| GET | `/auth/me` | Confirm who you're logged in as |
| POST | `/documents/upload` | Upload a PDF |
| GET | `/documents/{id}` | Check if it's done processing |
| GET | `/documents/ask` | Ask a question, get a streamed answer |

## What's still missing

This isn't pretending to be finished. A few things that would matter more at real scale:

- Celery instead of FastAPI's built-in background tasks, for when a single server isn't enough
- A proper test database instead of running tests against the real one
- Support for file types other than PDF
- Some kind of usage tracking per user, since Mistral API calls aren't free

## Why I built this

Mostly to stop reading about production backend patterns and actually hit the bugs myself. Auth was harder than it looks. Async SQLAlchemy sessions will humble you. pgvector is genuinely satisfying once it works. Every error in this project got fixed the slow way, one traceback at a time, which is honestly the only way any of it actually sticks.
