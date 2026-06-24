# Local RAG Application

This is a starter Retrieval-Augmented Generation project with:

- FastAPI backend
- React/Vite frontend
- SQLite database
- Full-text document retrieval
- Optional OpenAI answer generation

The app accepts `.txt`, `.md`, and `.pdf` uploads, stores document chunks in SQLite, retrieves relevant chunks for a question, and returns an answer with source text.

## Project Structure

```text
backend/
  app/
    main.py          FastAPI routes
    rag.py           document parsing, chunking, retrieval, answer generation
    database.py      SQLite setup
    config.py        environment settings
  sample_policy.txt  sample document for testing
  requirements.txt
  .env.example

frontend/
  src/
    main.jsx         React app
    styles.css       UI styles
  package.json
```

## Tools To Install

Backend:

- Python 3.10 or newer
- pip
- A terminal such as PowerShell
- Optional: Postman or Insomnia for API testing

Frontend:

- Node.js LTS
- npm, which comes with Node.js

Database:

- Nothing extra is required for the default setup.
- SQLite is built into Python and the app creates `backend/storage/rag.db` automatically.

Optional:

- OpenAI API key if you want generated answers instead of extractive answers.

## Backend Setup

From the project root:

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
python run_backend.py
```

The backend will run at:

```text
http://127.0.0.1:8000
```

Check health:

```text
http://127.0.0.1:8000/health
```

API docs:

```text
http://127.0.0.1:8000/docs
```

Do not run `backend/app/rag.py` directly. That file is used by the backend API. Use `python run_backend.py` from the `backend` folder.

## Frontend Setup

Open a second terminal from the project root:

```powershell
cd frontend
npm install
npm run dev
```

The frontend will run at:

```text
http://127.0.0.1:5173
```

## Optional OpenAI Setup

Edit `backend/.env` and add:

```text
OPENAI_API_KEY="your_api_key_here"
OPENAI_MODEL="gpt-4o-mini"
```

Restart the backend after changing `.env`.

## Test Example

1. Start the backend.
2. Start the frontend.
3. Upload `backend/sample_policy.txt`.
4. Ask:

```text
What is the refund policy for cancelled orders?
```

Expected answer without an OpenAI key:

```text
Based on the most relevant uploaded document section, here is the closest answer:

Refund Policy Customers can cancel an order before it has shipped and receive a full refund...
```

Expected answer with an OpenAI key:

```text
Customers can cancel an order before it ships and receive a full refund. If the order has already shipped, they need to request a return after delivery.
```

Expected source:

```text
sample_policy.txt
```

## API Test Examples

Upload a document:

```powershell
curl.exe -X POST "http://127.0.0.1:8000/documents" -F "file=@backend/sample_policy.txt"
```

Ask a question:

```powershell
curl.exe -X POST "http://127.0.0.1:8000/ask" -H "Content-Type: application/json" -d "{\"question\":\"What is the refund policy for cancelled orders?\",\"top_k\":4}"
```

## Is This Project Ready?

This is ready as a local starter RAG project. It is suitable for testing upload, retrieval, source display, and optional LLM answer generation.

Before production use, add authentication, stronger file validation, background ingestion jobs, better observability, and a production vector database if your document volume grows.
