import logging
import httpx
from pathlib import Path
from llama_index.core.node_parser import CodeSplitter,SentenceSplitter
from llama_index.core.schema import Document
from app.services import github_service

logger = logging.getLogger(__name__)

##  CONSTANTS ##

IGNORED_DIRS: set[str] = {
    "node_modules", ".git", "dist", "build", "target", "vendor",
    ".venv", "venv", "__pycache__", ".next",
}

IGNORED_LOCK_FILES: set[str] = {
    "package-lock.json", "yarn.lock", "pnpm-lock.yaml",
    "poetry.lock", "Cargo.lock", "composer.lock", "Pipfile.lock",
}

IGNORED_EXTENSIONS: set[str] = {
    # images
    ".png", ".jpg", ".jpeg", ".gif", ".ico", ".svg", ".bmp", ".webp",
    # fonts
    ".woff", ".woff2", ".ttf", ".eot", ".otf",
    # media
    ".mp4", ".mov", ".avi", ".mp3", ".wav",
    # archives
    ".zip", ".tar", ".gz", ".rar", ".7z",
    # documents / binaries
    ".pdf", ".exe", ".dll", ".so", ".dylib", ".bin", ".dat",
    # ML model weights / serialized models
    ".pkl", ".pt", ".onnx", ".h5", ".ckpt", ".safetensors",
}

MAX_FILE_SIZE_BYTES = 200_000

# File extension -> language label.
LANGUAGE_MAP: dict[str, str] = {
    ".py": "python",
    ".js": "javascript",
    ".mjs": "javascript",
    ".ts": "typescript",
    ".tsx": "tsx",
    ".jsx": "jsx",
    ".java": "java",
    ".go": "go",
    ".rb": "ruby",
    ".rs": "rust",
    ".c": "c",
    ".h": "c",
    ".cpp": "cpp",
    ".cc": "cpp",
    ".hpp": "cpp",
    ".cs": "c_sharp",
    ".php": "php",
    ".kt": "kotlin",
    ".swift": "swift",
    ".html": "html",
    ".htm": "html",
    ".css": "css",
    ".scss": "scss",
    ".sql": "sql",
    ".json": "json",
    ".yaml": "yaml",
    ".yml": "yaml",
    ".xml": "xml",
    ".sh": "bash",
    ".bash": "bash",
    ".md": "markdown",
}
## DUE TO DOCKER FILE NOT HAVING ANY EXTENSION
DOCKERFILE_NAMES = {"Dockerfile", "dockerfile"}


### HELPER FOR FILE FILTERING BEFORE CHUNKING ###

def detect_language(path:str) -> str | None:
    filename = Path(path).name
    if filename in DOCKERFILE_NAMES:
        return "dockerfile"
    suffix = Path(path).suffix.lower()
    return LANGUAGE_MAP.get(suffix)

def is_ignored_path(path:str) -> bool:
    parts = Path(path).parts
    if any(part in IGNORED_DIRS for part in parts):
        return True
    return Path(path).name in IGNORED_LOCK_FILES

def is_ignored_extension(path:str) -> bool:
    return Path(path).suffix.lower() in IGNORED_EXTENSIONS

def is_relevant_file(path:str, size: int | None) -> bool:
    if size is not None and size > MAX_FILE_SIZE_BYTES:
        return False
    if is_ignored_path(path):
        return False
    if is_ignored_extension(path):
        return False
    return True

def filter_relevant_file(tree: list[dict]) -> list[dict]:
    ### BLOB means file ###
    return [
        item for item in tree
        if item.get("type") == "blob" and is_relevant_file(item["path"],item.get("size"))
    ]

def is_binary_content(content:str) ->bool:
    ###   Catches files that slip past extension filtering (e.g. mislabeled or extensionless binaries)
    if "\x00" in content:
        return True
    sample = content[:2000]
    if not sample:
        return True
    non_printable = sum(1 for ch in sample if ord(ch)< 9 or 13 <  ord(ch) <32)
    return (non_printable/len(sample)) > 0.05

### SPLITTER CACHE: ###