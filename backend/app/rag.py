import re
import sys
from io import BytesIO

from openai import OpenAI
from pypdf import PdfReader

try:
    from .config import get_settings
    from .database import get_connection
except ImportError:
    from config import get_settings
    from database import get_connection


def extract_text(filename: str, content: bytes) -> str:
    if filename.lower().endswith(".pdf"):
        reader = PdfReader(BytesIO(content))
        pages = [page.extract_text() or "" for page in reader.pages]
        return "\n".join(pages).strip()

    return content.decode("utf-8", errors="ignore").strip()


def chunk_text(text: str, chunk_size: int = 900, overlap: int = 150) -> list[str]:
    clean_text = re.sub(r"\s+", " ", text).strip()
    if not clean_text:
        return []

    chunks: list[str] = []
    start = 0
    while start < len(clean_text):
        end = min(start + chunk_size, len(clean_text))
        chunks.append(clean_text[start:end])
        if end == len(clean_text):
            break
        start = max(0, end - overlap)
    return chunks


def add_document(filename: str, content_type: str, content: bytes) -> dict:
    text = extract_text(filename, content)
    chunks = chunk_text(text)
    if not chunks:
        raise ValueError("No readable text found in this file.")

    with get_connection() as connection:
        cursor = connection.execute(
            "INSERT INTO documents (filename, content_type) VALUES (?, ?)",
            (filename, content_type or "application/octet-stream"),
        )
        document_id = cursor.lastrowid

        for index, chunk in enumerate(chunks):
            chunk_cursor = connection.execute(
                "INSERT INTO chunks (document_id, chunk_index, text) VALUES (?, ?, ?)",
                (document_id, index, chunk),
            )
            chunk_id = chunk_cursor.lastrowid
            connection.execute(
                "INSERT INTO chunk_search (text, filename, chunk_id, document_id) VALUES (?, ?, ?, ?)",
                (chunk, filename, chunk_id, document_id),
            )

        row = connection.execute(
            """
            SELECT d.id, d.filename, d.content_type, d.created_at, COUNT(c.id) AS chunks
            FROM documents d
            JOIN chunks c ON c.document_id = d.id
            WHERE d.id = ?
            GROUP BY d.id
            """,
            (document_id,),
        ).fetchone()

    return dict(row)


def list_documents() -> list[dict]:
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT d.id, d.filename, d.content_type, d.created_at, COUNT(c.id) AS chunks
            FROM documents d
            LEFT JOIN chunks c ON c.document_id = d.id
            GROUP BY d.id
            ORDER BY d.created_at DESC
            """
        ).fetchall()
    return [dict(row) for row in rows]


def search_chunks(question: str, top_k: int) -> list[dict]:
    query = " OR ".join(token for token in re.findall(r"[A-Za-z0-9]+", question) if len(token) > 2)
    if not query:
        query = question

    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT
                chunk_search.document_id,
                chunk_search.chunk_id,
                chunk_search.filename,
                chunk_search.text
            FROM chunk_search
            WHERE chunk_search MATCH ?
            ORDER BY bm25(chunk_search)
            LIMIT ?
            """,
            (query, max(1, min(top_k, 10))),
        ).fetchall()
    return [dict(row) for row in rows]


def build_extractive_answer(question: str, sources: list[dict]) -> str:
    if not sources:
        return "I could not find relevant information in the uploaded documents."

    context = sources[0]["text"]
    return (
        "Based on the most relevant uploaded document section, here is the closest answer:\n\n"
        f"{context}\n\n"
        "Add an OpenAI API key in backend/.env if you want a synthesized answer instead of this extracted context."
    )


def generate_answer(question: str, sources: list[dict]) -> tuple[str, bool]:
    settings = get_settings()
    if not settings.openai_api_key or not sources:
        return build_extractive_answer(question, sources), False

    context = "\n\n".join(
        f"Source {index + 1} ({source['filename']}): {source['text']}"
        for index, source in enumerate(sources)
    )
    client = OpenAI(api_key=settings.openai_api_key)
    response = client.chat.completions.create(
        model=settings.openai_model,
        messages=[
            {
                "role": "system",
                "content": (
                    "Answer only from the provided context. If the context does not contain the answer, "
                    "say that the uploaded documents do not include enough information."
                ),
            },
            {"role": "user", "content": f"Question: {question}\n\nContext:\n{context}"},
        ],
        temperature=0.2,
    )
    return response.choices[0].message.content or "", True


if __name__ == "__main__":
    print("This file contains RAG helper functions.")
    print("Start the backend with: python run_backend.py")
    sys.exit(0)
