from fastapi import APIRouter, HTTPException, UploadFile
from sqlalchemy.orm import Session

from database import engine
from models import Document
from schemas import DocumentCreate, DocumentResponse, DocumentUpdate

router = APIRouter(prefix="/documents", tags=["documents"])


@router.get(
    "",
    response_model=list[DocumentResponse],
    summary="List all documents",
)
def list_documents():
    with Session(engine) as db:
        return db.query(Document).all()


@router.get(
    "/{document_id}",
    response_model=DocumentResponse,
    summary="Get one document",
    responses={404: {"description": "Document not found"}},
)
def get_document(document_id: int):
    with Session(engine) as db:
        document = db.get(Document, document_id)
        if document is None:
            raise HTTPException(status_code=404, detail="Document not found")
        return document


@router.post(
    "",
    response_model=DocumentResponse,
    summary="Create a document",
    status_code=201,
)
def create_document(payload: DocumentCreate):
    with Session(engine) as db:
        document = Document(**payload.model_dump())
        db.add(document)
        db.commit()
        db.refresh(document)
        return document


@router.put(
    "/{document_id}",
    response_model=DocumentResponse,
    summary="Update a document",
    responses={404: {"description": "Document not found"}},
)
def update_document(document_id: int, payload: DocumentUpdate):
    with Session(engine) as db:
        document = db.get(Document, document_id)
        if document is None:
            raise HTTPException(status_code=404, detail="Document not found")

        for field, value in payload.model_dump().items():
            setattr(document, field, value)

        db.commit()
        db.refresh(document)
        return document


@router.delete(
    "/{document_id}",
    summary="Delete a document",
    responses={404: {"description": "Document not found"}},
)
def delete_document(document_id: int):
    with Session(engine) as db:
        document = db.get(Document, document_id)
        if document is None:
            raise HTTPException(status_code=404, detail="Document not found")

        db.delete(document)
        db.commit()
        return {"detail": "Document deleted"}


@router.post(
    "/upload",
    response_model=DocumentResponse,
    summary="Upload a text/plain file and create a document from it",
    status_code=201,
    responses={400: {"description": "Unsupported file type"}},
)
async def upload_document(file: UploadFile):
    # Required: accept text/plain only. Do NOT treat binary (e.g. PDF) bytes
    # as if they were readable text — that produces garbage content.
    if file.content_type != "text/plain":
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {file.content_type}. Only text/plain is accepted.",
        )

    raw_bytes = await file.read()
    try:
        text_content = raw_bytes.decode("utf-8")
    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="File is not valid UTF-8 text.")

    with Session(engine) as db:
        document = Document(
            title=file.filename or "Uploaded document",
            content=text_content,
            description="Created from file upload",
        )
        db.add(document)
        db.commit()
        db.refresh(document)
        return document
