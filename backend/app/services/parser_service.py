import logging
import httpx
from pathlib import Path
from llama_index


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

# File extension -> language label. Used both for chunk metadata and to
# decide which splitter to use.
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

DOCKERFILE_NAMES = {"Dockerfile", "dockerfile"}
