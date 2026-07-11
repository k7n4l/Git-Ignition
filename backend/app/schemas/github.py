from pydantic import BaseModel

class RepoRequest(BaseModel):
    repo_url :str 

class TreeItem(BaseModel):
    path: str
    type: str #Type:- blob if file; tree if folder;
    size: int | None = None
    sha: str

class RepoTreeResponse(BaseModel):
    owner: str
    repo: str
    default_branch : str
    tree : list[TreeItem]