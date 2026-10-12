from pydantic import BaseModel

class Chunk(BaseModel):
    content: str
    file_path: str
    language: str | None=None
    chunk_index: int
    file_extension: str

class ParseRepoRequest(BaseModel):
    repo_url: str

class ParseRepoResponse(BaseModel):
    owner: str
    repo: str
    branch: str
    total_files_parsed: int
    total_chunks: int
    chunks: list[Chunk]