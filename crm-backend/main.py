import threading
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import users, notes
from config import settings

app = FastAPI(
    title="CRM Backend API",
    description="A REST API with authentication and background AI summarize jobs",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(users.router)
app.include_router(notes.router)


@app.get("/")
async def root():
    return {
        "message": "CRM Backend API",
        "version": "1.0.0",
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy"}
