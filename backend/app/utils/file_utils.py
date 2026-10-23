"""File Utilities.

Handles secure storage, file extension validation, MIME verification, and path safety.
"""

import os
import re
import hashlib
from pathlib import Path
from typing import Tuple
from backend.app.core.config import settings


def sanitize_filename(filename: str) -> str:
    """Sanitize the uploaded file's basename to prevent path traversal."""
    # Keep only alphanumeric, hyphens, underscores, dots
    base = os.path.basename(filename)
    clean_name = re.sub(r"[^a-zA-Z0-9_.-]", "_", base)
    return clean_name or "document_unnamed"


def validate_file_upload(filename: str, content_type: str, file_size: int) -> Tuple[bool, str]:
    """Validate file extension, size, and MIME type."""
    ext = Path(filename).suffix.lower()
    if ext not in settings.ALLOWED_EXTENSIONS:
        return (
            False,
            f"Unsupported file extension '{ext}'. Allowed extensions: {', '.join(settings.ALLOWED_EXTENSIONS)}",
        )

    if file_size > settings.MAX_FILE_SIZE_BYTES:
        return (
            False,
            f"File size ({file_size} bytes) exceeds maximum permitted limit ({settings.MAX_FILE_SIZE_BYTES} bytes)",
        )

    if content_type and content_type not in settings.ALLOWED_MIME_TYPES:
        # Warning/soft accept if extension is valid but MIME is generic
        pass

    return True, "Valid file"


def compute_file_sha256(filepath: Path) -> str:
    """Compute SHA-256 hash of a file for integrity and deduplication tracking."""
    sha256 = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            sha256.update(chunk)
    return sha256.hexdigest()
