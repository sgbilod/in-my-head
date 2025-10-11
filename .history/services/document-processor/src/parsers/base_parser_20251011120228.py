"""
Base Parser Interface
All document parsers inherit from this abstract base class
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


@dataclass
class ParsedDocument:
    """Structured representation of a parsed document"""
    
    # Content
    text: str
    text_length: int
    
    # Metadata
    metadata: Dict[str, Any]
    
    # Optional extracted elements
    images: Optional[List[Dict[str, Any]]] = None
    tables: Optional[List[Dict[str, Any]]] = None
    links: Optional[List[str]] = None
    
    # Processing info
    parser_used: str = ""
    parsing_time: float = 0.0
    parsing_errors: Optional[List[str]] = None
    
    def __post_init__(self):
        """Calculate text length if not provided"""
        if self.text_length == 0:
            self.text_length = len(self.text)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "text": self.text,
            "text_length": self.text_length,
            "metadata": self.metadata,
            "images": self.images or [],
            "tables": self.tables or [],
            "links": self.links or [],
            "parser_used": self.parser_used,
            "parsing_time": self.parsing_time,
            "parsing_errors": self.parsing_errors or []
        }


class BaseParser(ABC):
    """
    Abstract base class for all document parsers
    
    All parsers must implement:
    - parse() method for actual parsing
    - supported_formats property listing supported file extensions
    """
    
    def __init__(self):
        self.name = self.__class__.__name__
    
    @property
    @abstractmethod
    def supported_formats(self) -> List[str]:
        """
        Return list of supported file extensions
        
        Returns:
            List of extensions like ['.pdf', '.txt']
        """
        pass
    
    @abstractmethod
    async def parse(self, file_path: Path) -> ParsedDocument:
        """
        Parse document and extract content
        
        Args:
            file_path: Path to the document file
            
        Returns:
            ParsedDocument with extracted content and metadata
            
        Raises:
            ParsingError: If parsing fails
        """
        pass
    
    def can_parse(self, file_path: Path) -> bool:
        """
        Check if this parser can handle the given file
        
        Args:
            file_path: Path to the document file
            
        Returns:
            True if parser supports this file format
        """
        suffix = file_path.suffix.lower()
        return suffix in self.supported_formats
    
    async def extract_metadata(self, file_path: Path) -> Dict[str, Any]:
        """
        Extract basic file metadata
        
        Args:
            file_path: Path to the document file
            
        Returns:
            Dictionary with file metadata
        """
        stat = file_path.stat()
        
        return {
            "filename": file_path.name,
            "file_size": stat.st_size,
            "file_type": file_path.suffix.lower().lstrip('.'),
            "created_at": datetime.fromtimestamp(stat.st_ctime).isoformat(),
            "modified_at": datetime.fromtimestamp(stat.st_mtime).isoformat(),
        }
    
    def _clean_text(self, text: str) -> str:
        """
        Basic text cleaning
        
        Args:
            text: Raw extracted text
            
        Returns:
            Cleaned text
        """
        # Remove null bytes
        text = text.replace('\x00', '')
        
        # Normalize whitespace
        import re
        text = re.sub(r'\s+', ' ', text)
        
        # Strip leading/trailing whitespace
        text = text.strip()
        
        return text
    
    def _extract_links(self, text: str) -> List[str]:
        """
        Extract URLs from text
        
        Args:
            text: Text to extract links from
            
        Returns:
            List of URLs found
        """
        import re
        url_pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
        return re.findall(url_pattern, text)


class ParsingError(Exception):
    """Exception raised when document parsing fails"""
    
    def __init__(self, message: str, parser: str = None, file_path: str = None):
        self.message = message
        self.parser = parser
        self.file_path = file_path
        super().__init__(self.message)
    
    def __str__(self):
        parts = [self.message]
        if self.parser:
            parts.append(f"Parser: {self.parser}")
        if self.file_path:
            parts.append(f"File: {self.file_path}")
        return " | ".join(parts)


class UnsupportedFormatError(ParsingError):
    """Exception raised when file format is not supported"""
    pass


class CorruptedFileError(ParsingError):
    """Exception raised when file is corrupted or invalid"""
    pass
