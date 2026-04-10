import os
import uuid
import aiofiles
from pathlib import Path
from typing import Optional
from fastapi import UploadFile, HTTPException, status


# Allowed file extensions and MIME types
ALLOWED_EXTENSIONS = {
    # Images
    ".jpg": ["image/jpeg"],
    ".jpeg": ["image/jpeg"],
    ".png": ["image/png"],
    ".webp": ["image/webp"],
    # Documents
    ".pdf": ["application/pdf"],
    ".docx": ["application/vnd.openxmlformats-officedocument.wordprocessingml.document"],
    ".xlsx": ["application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"],
}

# Flatten allowed MIME types
ALLOWED_MIME_TYPES = set()
for mimes in ALLOWED_EXTENSIONS.values():
    ALLOWED_MIME_TYPES.update(mimes)


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename by removing special characters and limiting length.
    
    Args:
        filename: Original filename
        
    Returns:
        Sanitized filename
    """
    # Get extension
    name = Path(filename).stem
    ext = Path(filename).suffix.lower()
    
    # Remove special characters, keep alphanumeric, dash, underscore
    safe_name = "".join(c if c.isalnum() or c in ("-", "_") else "_" for c in name)
    
    # Limit length
    safe_name = safe_name[:100]
    
    return f"{safe_name}{ext}"


def validate_file(file: UploadFile, max_size_mb: int = 10) -> None:
    """
    Validate file type and size.
    
    Args:
        file: Uploaded file
        max_size_mb: Maximum file size in MB
        
    Raises:
        HTTPException: If file is invalid
    """
    # Check MIME type
    if file.content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type '{file.content_type}' not allowed. Allowed types: {', '.join(ALLOWED_MIME_TYPES)}"
        )
    
    # Check file extension
    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File extension '{ext}' not allowed. Allowed extensions: {', '.join(ALLOWED_EXTENSIONS.keys())}"
        )
    
    # Validate extension matches MIME type
    if file.content_type not in ALLOWED_EXTENSIONS.get(ext, []):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File extension '{ext}' does not match content type '{file.content_type}'"
        )


async def save_uploaded_file(
    file: UploadFile, 
    subfolder: str,
    upload_dir: str = "/app/uploads",
    max_size_mb: int = 10
) -> str:
    """
    Save an uploaded file to disk with validation.
    
    Args:
        file: Uploaded file from FastAPI
        subfolder: Subdirectory within upload_dir (e.g., 'supplier_documents')
        upload_dir: Base upload directory
        max_size_mb: Maximum file size in MB
        
    Returns:
        Relative URL path to the saved file (e.g., '/uploads/supplier_documents/uuid_filename.pdf')
        
    Raises:
        HTTPException: If file validation fails or save fails
    """
    # Validate file type
    validate_file(file, max_size_mb)
    
    # Generate unique filename
    unique_id = uuid.uuid4().hex[:12]
    safe_filename = sanitize_filename(file.filename)
    final_filename = f"{unique_id}_{safe_filename}"
    
    # Create directory structure
    target_dir = Path(upload_dir) / subfolder
    target_dir.mkdir(parents=True, exist_ok=True)
    
    # Full file path
    file_path = target_dir / final_filename
    
    try:
        # Read and validate file size
        contents = await file.read()
        file_size_mb = len(contents) / (1024 * 1024)
        
        if file_size_mb > max_size_mb:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File size ({file_size_mb:.2f} MB) exceeds maximum allowed size ({max_size_mb} MB)"
            )
        
        # Write file asynchronously
        async with aiofiles.open(file_path, 'wb') as f:
            await f.write(contents)
        
        # Return relative URL
        relative_url = f"/uploads/{subfolder}/{final_filename}"
        return relative_url
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save file: {str(e)}"
        )
    finally:
        # Reset file pointer for potential reuse
        await file.seek(0)


async def delete_file(file_url: str, upload_dir: str = "/app/uploads") -> bool:
    """
    Delete a file from disk given its URL.
    
    Args:
        file_url: Relative URL of the file (e.g., '/uploads/supplier_documents/uuid_filename.pdf')
        upload_dir: Base upload directory
        
    Returns:
        True if file was deleted, False if file didn't exist
        
    Raises:
        HTTPException: If deletion fails
    """
    try:
        # Extract path from URL (remove leading /uploads/)
        if not file_url.startswith("/uploads/"):
            return False
        
        relative_path = file_url.replace("/uploads/", "")
        file_path = Path(upload_dir) / relative_path
        
        if file_path.exists():
            file_path.unlink()
            return True
        
        return False
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete file: {str(e)}"
        )
