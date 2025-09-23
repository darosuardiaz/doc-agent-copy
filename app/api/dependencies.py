"""
FastAPI dependencies for the financial document processing system.
"""
import os
from typing import Generator
from fastapi import Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session

from app.database.connection import get_database
from app.config import get_settings

settings = get_settings()


def get_db() -> Generator[Session, None, None]:
    """Dependency to get database session."""
    return get_database()


def validate_file_upload(file: UploadFile = File(...)) -> UploadFile:
    """
    Validate uploaded file.
    
    Args:
        file: Uploaded file
        
    Returns:
        Validated file
        
    Raises:
        HTTPException: If file is invalid
    """
    # Check file extension
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No filename provided"
        )
    
    file_ext = os.path.splitext(file.filename)[1].lower()
    if file_ext not in settings.ALLOWED_FILE_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type {file_ext} not allowed. Allowed types: {settings.ALLOWED_FILE_TYPES}"
        )
    
    # Check file size (this is approximate since we're reading the file)
    if hasattr(file, 'size') and file.size and file.size > settings.MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File too large. Maximum size: {settings.MAX_FILE_SIZE} bytes"
        )
    
    return file


def ensure_upload_directory():
    """Ensure upload directory exists."""
    if not os.path.exists(settings.UPLOAD_DIRECTORY):
        os.makedirs(settings.UPLOAD_DIRECTORY, exist_ok=True)


def validate_session_id(session_id: str) -> str:
    """
    Validate chat session ID format.
    
    Args:
        session_id: Session ID to validate
        
    Returns:
        Validated session ID
        
    Raises:
        HTTPException: If session ID is invalid
    """
    if not session_id or len(session_id) < 10:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid session ID"
        )
    
    return session_id


def validate_document_id(document_id: str) -> str:
    """
    Validate document ID format.
    
    Args:
        document_id: Document ID to validate
        
    Returns:
        Validated document ID
        
    Raises:
        HTTPException: If document ID is invalid
    """
    if not document_id or len(document_id) < 10:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid document ID"
        )
    
    return document_id