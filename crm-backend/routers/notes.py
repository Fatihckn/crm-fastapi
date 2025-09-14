from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.orm import Session
from typing import List
from database import get_db
from models import User, Note, UserRole
from schemas import NoteCreate, Note as NoteSchema, NoteResponse, NoteUpdate
from auth import get_current_user
from tasks import enqueue_note_summary, rule_based_summary
from models import NoteStatus
from sqlalchemy.exc import SQLAlchemyError

router = APIRouter(prefix="/notes", tags=["notes"])


@router.post("/", response_model=NoteSchema, status_code=status.HTTP_201_CREATED)
def create_note(note: NoteCreate, response: Response,
                db: Session = Depends(get_db),
                current_user: User = Depends(get_current_user)):
    db_note = Note(
        raw_text=note.raw_text,
        summary=None,
        status=NoteStatus.QUEUED,
        user_id=current_user.id
    )
    db.add(db_note)
    try:
        db.commit()
        db.refresh(db_note)
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database error")

    enqueue_note_summary(db_note.id)
    return db_note


@router.get("/{note_id}", response_model=NoteResponse)
def get_note(note_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    query = db.query(Note).filter(Note.id == note_id)

    if current_user.role == UserRole.AGENT:
        query = query.filter(Note.user_id == current_user.id)

    db_note = query.first()
    if not db_note:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Note not found"
        )

    return db_note


@router.get("/", response_model=List[NoteResponse])
def get_notes(
        skip: int = 0,
        limit: int = 100,
        status: NoteStatus = None,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    query = db.query(Note)

    if current_user.role == UserRole.AGENT:
        query = query.filter(Note.user_id == current_user.id)

    if status:
        query = query.filter(Note.status == status)

    notes = query.offset(skip).limit(limit).all()
    return notes


@router.put("/{note_id}", response_model=NoteSchema)
def update_note(note_id: int, note_update: NoteUpdate,
                db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    note = db.query(Note).filter(Note.id == note_id).first()
    if not note:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Note not found")

    if note_update.raw_text is not None:
        note.raw_text = note_update.raw_text
        note.summary = rule_based_summary(note_update.raw_text)
        note.status = NoteStatus.DONE

    db.commit()
    db.refresh(note)
    return note


@router.delete("/{note_id}")
def delete_note(note_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    query = db.query(Note).filter(Note.id == note_id)

    if current_user.role == UserRole.AGENT:
        query = query.filter(Note.user_id == current_user.id)

    db_note = query.first()
    if not db_note:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Note not found"
        )

    db.delete(db_note)
    db.commit()
    return {"message": "Note deleted successfully"}


@router.get("/{note_id}/status")
def get_note_status(note_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    note = db.query(Note).filter(Note.id == note_id).first()
    if not note:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Note not found")

    return {
        "note_id": note.id,
        "status": note.status,
        "summary": note.summary,
        "created_at": note.created_at,
        "updated_at": note.updated_at
    }
