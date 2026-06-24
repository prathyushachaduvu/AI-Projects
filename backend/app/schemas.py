from pydantic import BaseModel


class DocumentInfo(BaseModel):
    id: int
    filename: str
    content_type: str
    created_at: str
    chunks: int


class UploadResponse(BaseModel):
    document: DocumentInfo


class AskRequest(BaseModel):
    question: str
    top_k: int = 4


class Source(BaseModel):
    document_id: int
    chunk_id: int
    filename: str
    text: str


class AskResponse(BaseModel):
    answer: str
    sources: list[Source]
    used_llm: bool
