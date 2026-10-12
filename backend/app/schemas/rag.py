from typing import Optional
from pydantic import BaseModel

class IndexRepoRequest(BaseModel):
    repo_url: str
    branch: Optional[str] = None

class IndexRepoResponse(BaseModel):
    owner: str
    repo: str
    branch: str
    files_processed: int
    chunks_stored: int
    status: str

class AskRepoRequest(BaseModel):
    repo_url: str
    branch: Optional[str] = None
    question: str

class RetrievedChunkInfo(BaseModel):
    file_path: str
    chunk_index: int
    similarity_score: float
    content: str

class AskRepoResponse(BaseModel):
    answer: str
    sources: list[str]
    retrieved_chunks: list[RetrievedChunkInfo]
