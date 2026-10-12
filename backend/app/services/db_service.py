import sqlite3
import numpy as np
from pathlib import Path
from typing import Optional
from app.core.config import settings

def get_db_path() -> Path:
    """Resolve database path relative to backend directory and ensure directory exists."""
    raw_path = Path(settings.db_path)
    if not raw_path.is_absolute():
        # app/services/db_service.py -> app/services -> app -> backend
        backend_dir = Path(__file__).resolve().parent.parent.parent
        raw_path = backend_dir / raw_path
    raw_path.parent.mkdir(parents=True, exist_ok=True)
    return raw_path

def get_connection() -> sqlite3.Connection:
    """Create and return a configured SQLite connection."""
    db_file = get_db_path()
    conn = sqlite3.connect(str(db_file), timeout=10.0)
    conn.row_factory = sqlite3.Row
    return conn

def init_db() -> None:
    """Initialize database tables and indexes if they do not exist."""
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS chunks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                owner TEXT NOT NULL,
                repo TEXT NOT NULL,
                branch TEXT NOT NULL,
                file_path TEXT NOT NULL,
                chunk_index INTEGER NOT NULL,
                language TEXT,
                file_extension TEXT,
                content TEXT NOT NULL,
                embedding BLOB NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(owner, repo, branch, file_path, chunk_index)
            )
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_chunks_repo_branch 
            ON chunks (owner, repo, branch)
        """)

def serialize_embedding(embedding: np.ndarray) -> bytes:
    """
    Serialize 384-d float array to compact binary bytes.
    384 float32 values = 1,536 bytes (vs ~4 KB as JSON text).
    """
    return embedding.astype(np.float32).tobytes()

def deserialize_embedding(blob: bytes) -> np.ndarray:
    """Deserialize compact binary bytes back to a float32 NumPy array."""
    return np.frombuffer(blob, dtype=np.float32)

def has_indexed_repo(owner: str, repo: str, branch: str) -> bool:
    """Check if any chunks exist for the specified repository and branch."""
    init_db()
    with get_connection() as conn:
        cursor = conn.execute(
            "SELECT COUNT(1) FROM chunks WHERE owner = ? AND repo = ? AND branch = ?",
            (owner, repo, branch),
        )
        count = cursor.fetchone()[0]
        return count > 0

def get_indexed_branch(owner: str, repo: str) -> Optional[str]:
    """Retrieve the first indexed branch for this owner/repo if one exists."""
    init_db()
    with get_connection() as conn:
        cursor = conn.execute(
            "SELECT branch FROM chunks WHERE owner = ? AND repo = ? LIMIT 1",
            (owner, repo),
        )
        row = cursor.fetchone()
        return row["branch"] if row else None

def save_repo_chunks(
    owner: str,
    repo: str,
    branch: str,
    chunks: list[dict],
    embeddings: np.ndarray,
) -> int:
    """
    Atomically replace all chunks and embeddings for a repo and branch.
    Runs inside a transaction: if insertion fails, previous index is retained.
    """
    init_db()
    if len(chunks) != len(embeddings):
        raise ValueError("Number of chunks and embeddings must match.")

    records = []
    for chunk, emb in zip(chunks, embeddings):
        records.append((
            owner,
            repo,
            branch,
            chunk["file_path"],
            chunk["chunk_index"],
            chunk.get("language"),
            chunk.get("file_extension"),
            chunk["content"],
            serialize_embedding(emb),
        ))

    with get_connection() as conn:
        # Atomic transaction: delete previous active chunks for this repo/branch
        conn.execute(
            "DELETE FROM chunks WHERE owner = ? AND repo = ? AND branch = ?",
            (owner, repo, branch),
        )
        conn.executemany(
            """
            INSERT INTO chunks (
                owner, repo, branch, file_path, chunk_index,
                language, file_extension, content, embedding
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            records,
        )

    return len(records)

def get_repo_chunks(owner: str, repo: str, branch: str) -> list[dict]:
    """
    Retrieve all chunks and their deserialized embeddings for a given repository and branch.
    """
    init_db()
    with get_connection() as conn:
        cursor = conn.execute(
            """
            SELECT id, owner, repo, branch, file_path, chunk_index,
                   language, file_extension, content, embedding
            FROM chunks
            WHERE owner = ? AND repo = ? AND branch = ?
            ORDER BY file_path, chunk_index
            """,
            (owner, repo, branch),
        )
        rows = cursor.fetchall()

    results: list[dict] = []
    for row in rows:
        results.append({
            "id": row["id"],
            "owner": row["owner"],
            "repo": row["repo"],
            "branch": row["branch"],
            "file_path": row["file_path"],
            "chunk_index": row["chunk_index"],
            "language": row["language"],
            "file_extension": row["file_extension"],
            "content": row["content"],
            "embedding": deserialize_embedding(row["embedding"]),
        })

    return results
