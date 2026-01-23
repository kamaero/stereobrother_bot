"""
Minimal storage utilities for testing purposes.
"""

import os
import shutil
from pathlib import Path
from typing import BinaryIO, Optional
from urllib.parse import urljoin


class StorageManager:
    """Minimal storage manager for testing."""

    def __init__(self, storage_type: str = "local", local_path: str = "./storage"):
        self.storage_type = storage_type
        self.local_path = Path(local_path)
        self.local_path.mkdir(parents=True, exist_ok=True)

    def upload_file(self, file_path: str, filename: str) -> str:
        """Upload a file to storage."""
        source_path = Path(file_path)
        dest_path = self.local_path / filename

        if self.storage_type == "local":
            shutil.copy2(source_path, dest_path)
            return f"/storage/{filename}"
        else:
            # For testing, just return a dummy URL
            return f"https://example.com/storage/{filename}"

    def download_file(self, filename: str, dest_path: str) -> bool:
        """Download a file from storage."""
        source_path = self.local_path / filename
        dest = Path(dest_path)

        if source_path.exists():
            shutil.copy2(source_path, dest)
            return True
        return False

    def delete_file(self, filename: str) -> bool:
        """Delete a file from storage."""
        file_path = self.local_path / filename
        if file_path.exists():
            file_path.unlink()
            return True
        return False

    def file_exists(self, filename: str) -> bool:
        """Check if a file exists in storage."""
        return (self.local_path / filename).exists()

    def get_file_url(self, filename: str) -> str:
        """Get URL for a file."""
        if self.storage_type == "local":
            return f"/storage/{filename}"
        else:
            return f"https://example.com/storage/{filename}"

    def list_files(self, prefix: str = "") -> list[str]:
        """List files in storage."""
        files = []
        for file_path in self.local_path.glob(f"{prefix}*"):
            if file_path.is_file():
                files.append(file_path.name)
        return files

    def get_file_size(self, filename: str) -> Optional[int]:
        """Get file size in bytes."""
        file_path = self.local_path / filename
        if file_path.exists():
            return file_path.stat().st_size
        return None


# Create a default instance for convenience
default_storage = StorageManager()
