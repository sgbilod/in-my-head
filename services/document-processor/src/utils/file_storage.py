"""
File Storage Utility
Handles file storage operations
"""

import os
import hashlib
from pathlib import Path
from typing import Optional
from datetime import datetime
import aiofiles


class FileStorage:
    """Manages file storage operations"""
    
    def __init__(self, base_path: Optional[str] = None):
        """
        Initialize file storage
        
        Args:
            base_path: Base directory for file storage
        """
        if base_path is None:
            # Default to data/uploads in project root
            project_root = Path(__file__).parent.parent.parent.parent
            base_path = project_root / "data" / "uploads"
        
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
    
    async def save_file(
        self,
        content: bytes,
        filename: str,
        content_type: Optional[str] = None
    ) -> str:
        """
        Save file to storage
        
        Args:
            content: File content as bytes
            filename: Original filename
            content_type: MIME type
        
        Returns:
            Relative path to saved file
        """
        # Create subdirectory based on current date
        date_dir = datetime.now().strftime("%Y/%m/%d")
        save_dir = self.base_path / date_dir
        save_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate unique filename using hash
        file_hash = hashlib.md5(content).hexdigest()[:12]
        file_ext = Path(filename).suffix
        unique_filename = f"{file_hash}_{Path(filename).stem}{file_ext}"
        
        # Full path
        file_path = save_dir / unique_filename
        
        # Save file
        async with aiofiles.open(file_path, 'wb') as f:
            await f.write(content)
        
        # Return relative path from base_path
        return str(file_path.relative_to(self.base_path))
    
    def get_full_path(self, relative_path: str) -> Path:
        """
        Get full filesystem path from relative path
        
        Args:
            relative_path: Relative path from base
        
        Returns:
            Full Path object
        """
        return self.base_path / relative_path
    
    def delete_file(self, relative_path: str) -> bool:
        """
        Delete a file from storage
        
        Args:
            relative_path: Relative path from base
        
        Returns:
            True if deleted, False if not found
        """
        file_path = self.get_full_path(relative_path)
        
        if file_path.exists():
            file_path.unlink()
            
            # Try to clean up empty parent directories
            try:
                parent = file_path.parent
                if not any(parent.iterdir()):  # If directory is empty
                    parent.rmdir()
            except:
                pass
            
            return True
        
        return False
    
    def file_exists(self, relative_path: str) -> bool:
        """Check if file exists"""
        return self.get_full_path(relative_path).exists()
    
    def get_file_size(self, relative_path: str) -> Optional[int]:
        """Get file size in bytes"""
        file_path = self.get_full_path(relative_path)
        return file_path.stat().st_size if file_path.exists() else None
