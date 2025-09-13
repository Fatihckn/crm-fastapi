from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime
from models import UserRole, NoteStatus


class UserBase(BaseModel):
    email: EmailStr
    role: UserRole = UserRole.AGENT


class UserCreate(UserBase):
    password: str


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class User(UserBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    email: Optional[str] = None


class NoteBase(BaseModel):
    raw_text: str


class NoteCreate(NoteBase):
    pass


class NoteUpdate(BaseModel):
    raw_text: Optional[str] = None


class Note(NoteBase):
    id: int
    summary: Optional[str] = None
    status: NoteStatus
    user_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class NoteResponse(Note):
    owner: User
