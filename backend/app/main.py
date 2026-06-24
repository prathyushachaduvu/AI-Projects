from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from .config import get_settings
from .database import init_db
from .rag import add_document, generate_answer, list_documents, search_chunks
from .schemas import AskRequest, AskResponse, DocumentInfo, UploadResponse

settings = get_settings()
app = FastAPI(title=settings.app_name)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup() -> None:
    init_db()


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "app": settings.app_name}


@app.get("/documents", response_model=list[DocumentInfo])
def documents() -> list[dict]:
    return list_documents()


@app.post("/documents", response_model=UploadResponse)
async def upload_document(file: UploadFile = File(...)) -> dict:
    if not file.filename:
        raise HTTPException(status_code=400, detail="A filename is required.")

    allowed_extensions = (".txt", ".md", ".pdf")
    if not file.filename.lower().endswith(allowed_extensions):
        raise HTTPException(status_code=400, detail="Upload a .txt, .md, or .pdf file.")

    try:
        document = add_document(file.filename, file.content_type or "", await file.read())
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error

    return {"document": document}


@app.post("/ask", response_model=AskResponse)
def ask(request: AskRequest) -> dict:
    question = request.question.strip()
    if not question:
        raise HTTPException(status_code=400, detail="Question is required.")

    sources = search_chunks(question, request.top_k)
    answer, used_llm = generate_answer(question, sources)
    return {"answer": answer, "sources": sources, "used_llm": used_llm}
