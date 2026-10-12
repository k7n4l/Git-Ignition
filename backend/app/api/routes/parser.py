from fastapi import HTTPException, APIRouter
import logging
from app.schemas.parser import ParseRepoRequest,ParseRepoResponse
from app.services import github_service,parser_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/repo",tags=["parser"])

@router.post("/parse", response_model=ParseRepoResponse)
def parse_repo(payload: ParseRepoRequest):
    try:
        owner,repo = github_service.parse_repo_url(payload.repo_url)
        tree_data = github_service.get_repo_tree(owner, repo)
        branch = tree_data["default_branch"]
        logger.info("Calling parser_service.parse_repo()")
        chunks = parser_service.parse_repo(owner, repo, branch, tree_data["tree"])

        return {
            "owner": owner,
            "repo": repo,
            "branch": branch,
            "total_files_parsed": len({c["file_path"] for c in chunks}),
            "total_chunks": len(chunks),
            "chunks": chunks,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception("Parsing error")
        raise HTTPException(status_code=502, detail=f"Parsing Error: {e}")
