from fastapi import APIRouter,HTTPException
from app.schemas.github import RepoTreeResponse,RepoRequest
from app.services import github_service

router = APIRouter(prefix="/repo",tags=["github"])

@router.post("/tree", response_model=RepoTreeResponse)
def fetch_repo_tree(payload:RepoRequest):
    try:
        owner,repo = github_service.parse_repo_url(payload.repo_url)
        result =github_service.get_repo_tree(owner,repo)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Github API Error: {e}")