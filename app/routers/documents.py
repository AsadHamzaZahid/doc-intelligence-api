import os
import uuid
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from pypdf import PdfReader
from app.database import get_db, Async_Sessionmaker
from app.models.documents import Document, Chunk
from app.services.auth_dependency import get_current_user
from app.models.user import User
from app.services.chunking import chunk_text
from fastapi.responses import StreamingResponse
from app.services.embeddings import get_embedding, stream_answer
from sqlalchemy import select

router = APIRouter(prefix="/documents", tags=["documents"])

UPLOAD_DIR = "uploaded_files"
os.makedirs(UPLOAD_DIR, exist_ok=True)


async def process_document(document_id: uuid.UUID, file_path: str):
    """
    Runs AFTER the upload response has already been sent to the client.
    Does the slow work: extract text, chunk it, embed each chunk, save,
    then flip the document's status to 'ready'.
    Needs its OWN db session, since the request's session is already closed
    by the time this runs.
    """
    async with Async_Sessionmaker() as db:
        reader = PdfReader(file_path)
        full_text = ""
        for page in reader.pages:
            full_text += page.extract_text() or " "

        chunks = chunk_text(full_text)

        for i, chunk_content in enumerate(chunks):
            embedding = get_embedding(chunk_content)
            chunk = Chunk(
                document_id=document_id,
                content=chunk_content,
                chunk_index=i,
                embedding=embedding,
            )
            db.add(chunk)

        result = await db.execute(select(Document).where(Document.id == document_id))
        document = result.scalar_one()
        document.status = "ready"

        await db.commit()


@router.post("/upload")
async def upload(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if not file.filename.endswith(".pdf"):
        raise HTTPException(
            status_code=400, detail="only pdf format files are allowed")

    file_path = os.path.join(UPLOAD_DIR, f"{uuid.uuid4()}_{file.filename}")
    contents = await file.read()

    with open(file_path, "wb") as f:
        f.write(contents)

    new_document = Document(
        user_id=current_user.id,
        file_name=file.filename,
        status="processing",
    )
    db.add(new_document)
    await db.commit()
    await db.refresh(new_document)

    # Kick off the slow work in the background — response returns immediately,
    # doesn't wait for chunking/embedding to finish.
    background_tasks.add_task(process_document, new_document.id, file_path)

    return {
        "document_id": new_document.id,
        "file_name": new_document.file_name,
        # will say "processing" here, flips to "ready" shortly after
        "status": new_document.status,
    }


@router.get("/{document_id}")
async def get_document_status(
    document_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Quick way to check if a document has finished processing yet."""
    result = await db.execute(
        select(Document).where(Document.id == document_id,
                               Document.user_id == current_user.id)
    )
    document = result.scalar_one_or_none()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    return {"document_id": document.id, "file_name": document.file_name, "status": document.status}


@router.get("/ask")
async def ask_questions(
    query: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query_embeddings = get_embedding(query)

    result = await db.execute(
        select(Chunk, Document.file_name)
        .join(Document, Chunk.document_id == Document.id)
        .where(Document.user_id == current_user.id)
        .order_by(Chunk.embedding.cosine_distance(query_embeddings))
        .limit(5)
    )

    rows = result.all()

    if not rows:
        return StreamingResponse(iter(["No documents found"]), media_type="text/plain")

    context_chunks = [chunk.content for chunk, _ in rows]

    return StreamingResponse(stream_answer(query, context_chunks), media_type="text/plain")
