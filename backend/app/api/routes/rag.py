import logging
from fastapi import APIRouter, HTTPException
from app.core.config import settings
from app.schemas.rag import (
    IndexRepoRequest,
    IndexRepoResponse,
    AskRepoRequest,
    AskRepoResponse,
    RetrievedChunkInfo,
)
from app.services import (
    github_service,
    parser_service,
    embedding_service,
    db_service,
    retrieval_service,
    groq_service,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/repo", tags=["rag"])

@router.post("/index", response_model=IndexRepoResponse)
def index_repo(payload: IndexRepoRequest):
    """
    Fetch repository files, parse code into chunks, generate embeddings locally,
    and persist them into SQLite for semantic search.
    """
    try:
        owner, repo = github_service.parse_repo_url(payload.repo_url)
        branch = payload.branch or github_service.get_default_branch(owner, repo)

        logger.info("Fetching repository tree for %s/%s (%s)...", owner, repo, branch)
        tree_data = github_service.get_repo_tree(owner, repo, branch=branch)
        
        # 1. Check file limit before downloading file contents
        relevant_files = parser_service.filter_relevant_files(tree_data["tree"])
        if len(relevant_files) > settings.index_max_files:
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Repository contains {len(relevant_files)} indexable files, "
                    f"exceeding the configured limit of {settings.index_max_files}. "
                    "Adjust INDEX_MAX_FILES in your .env if you wish to index larger repositories."
                ),
            )

        logger.info(
            "Parsing and chunking %d relevant files for %s/%s...",
            len(relevant_files),
            owner,
            repo,
        )
        chunks = parser_service.parse_repo(owner, repo, branch, tree_data["tree"])
        if not chunks:
            raise HTTPException(
                status_code=400,
                detail="No readable text or code chunks found in this repository.",
            )

        # 2. Extract content text and generate 384-dimensional embeddings
        logger.info("Generating embeddings for %d chunks...", len(chunks))
        chunk_texts = [c["content"] for c in chunks]
        embeddings = embedding_service.embed_texts(chunk_texts, batch_size=32)

        # 3. Save into SQLite atomically (replaces previous index without leaving duplicates)
        logger.info("Saving chunks and embeddings to SQLite...")
        stored_count = db_service.save_repo_chunks(owner, repo, branch, chunks, embeddings)

        return IndexRepoResponse(
            owner=owner,
            repo=repo,
            branch=branch,
            files_processed=len(relevant_files),
            chunks_stored=stored_count,
            status="indexed",
        )

    except HTTPException:
        raise
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        logger.exception("Failed to index repository")
        raise HTTPException(status_code=502, detail=f"Indexing failed: {exc}")


@router.post("/ask", response_model=AskRepoResponse)
def ask_repo(payload: AskRepoRequest):
    """
    Search indexed repository chunks using cosine similarity and generate an answer via Groq.
    """
    try:
        owner, repo = github_service.parse_repo_url(payload.repo_url)

        # Resolve branch: use requested, or fall back to an indexed branch, or default branch
        branch = payload.branch
        if not branch:
            branch = db_service.get_indexed_branch(owner, repo)
            if not branch:
                branch = github_service.get_default_branch(owner, repo)

        # 1. Ensure repository has been indexed
        if not db_service.has_indexed_repo(owner, repo, branch):
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Repository '{owner}/{repo}' (branch: '{branch}') has not been indexed yet. "
                    "Please call POST /repo/index first."
                ),
            )

        # 2. Load stored chunk embeddings from SQLite (no re-fetching or re-embedding of the repo!)
        stored_chunks = db_service.get_repo_chunks(owner, repo, branch)
        if not stored_chunks:
            raise HTTPException(
                status_code=400,
                detail="No stored chunks found for this repository and branch.",
            )

        # 3. Embed the question with the same MiniLM model
        query_vector = embedding_service.embed_query(payload.question)

        # 4. Calculate cosine similarity and select top 4 relevant chunks
        top_results = retrieval_service.retrieve_top_chunks(query_vector, stored_chunks, top_k=4)
        if not top_results:
            raise HTTPException(
                status_code=400,
                detail="Could not retrieve relevant chunks for the question.",
            )

        # 5. Build citations strictly from actual chunk metadata
        top_chunks = [item[0] for item in top_results]
        sources = list(dict.fromkeys(c["file_path"] for c in top_chunks))

        # 6. Generate answer using Groq API
        answer = groq_service.generate_answer(payload.question, top_chunks)

        retrieved_chunk_infos = [
            RetrievedChunkInfo(
                file_path=chunk["file_path"],
                chunk_index=chunk["chunk_index"],
                similarity_score=round(score, 4),
                content=chunk["content"],
            )
            for chunk, score in top_results
        ]

        return AskRepoResponse(
            answer=answer,
            sources=sources,
            retrieved_chunks=retrieved_chunk_infos,
        )

    except HTTPException:
        raise
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        logger.exception("Failed to answer question")
        raise HTTPException(status_code=502, detail=f"Question answering failed: {exc}")
