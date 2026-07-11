from urllib.parse import urlparse
from app.core.config import settings
import httpx
import base64

GITHUB_API = "https://api.github.com"

def _headers():
    headers = {"Accept": "application/vnd.github+json"}
    if settings.github_token:
        headers["Authorization"] = f"Bearer {settings.github_token}"
    return headers

def parse_repo_url(repo_url:str)-> tuple[str,str]:
    """Extract (owner, repo) from a GitHub URL."""
    path = urlparse(repo_url).path.strip("/")
    parts = path.split("/")
    if len(parts)<2:
        raise ValueError(f"Invalid Github URL: {repo_url}")
    return parts[0],parts[1].replace(".git","")

def get_default_branch(owner:str,repo:str) ->str:
    url = f"{GITHUB_API}/repos/{owner}/{repo}"
    resp = httpx.get(url,headers=_headers())
    resp.raise_for_status()
    return resp.json()["default_branch"]

def get_repo_tree(owner:str,repo:str) -> dict:
    branch = get_default_branch(owner,repo)
    url = f"{GITHUB_API}/repos/{owner}/{repo}/git/trees/{branch}"
    resp = httpx.get(url,headers=_headers(),params={"recursive":"1"})
    resp.raise_for_status()
    data = resp.json()

    return {
        "owner": owner,
        "repo" : repo,
        "default_branch": branch,
        "tree": [
            {
                "path": item["path"],
                "type": item["type"],
                "size": item.get("size"),
                "sha" : item["sha"],
            }
            for item in data["tree"]
        ],
    }

def get_file_content(owner:str,repo:str,path:str,branch:str) -> str:
    """Fetch raw content of a single file"""
    url = f"{GITHUB_API}/repos/{owner}/{repo}/contents/{path}"
    resp = httpx.get(url,headers=_headers(),params={"ref":branch})
    resp.raise_for_status()
    data = resp.json()

    if data.get("encoding") == "base64":
        return base64.b64decode(data["content"]).decode("utf-8",errors="ignore")
    return data.get("content","")
