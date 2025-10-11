"""
Parser Factory
Selects the appropriate parser based on file type
"""

from pathlib import Path
from typing import Optional
import magic

from .base_parser import BaseParser, UnsupportedFormatError
from .txt_parser import TxtParser
from .pdf_parser import PdfParser
from .docx_parser import DocxParser
from .pptx_parser import PptxParser
from .html_parser import HtmlParser
from .markdown_parser import MarkdownParser


class ParserFactory:
    """
    Factory class for creating appropriate document parsers

    Usage:
        parser = ParserFactory.get_parser("document.pdf")
        result = await parser.parse("document.pdf")
    """

    # Registry of available parsers
    _parsers = [
        TxtParser,
        PdfParser,
        DocxParser,
        PptxParser,
        HtmlParser,
        MarkdownParser,
    ]

    @classmethod
    def get_parser(cls, file_path: Path) -> BaseParser:
        """
        Get the appropriate parser for a file

        Args:
            file_path: Path to the document file

        Returns:
            Parser instance that can handle the file

        Raises:
            UnsupportedFormatError: If no parser supports the file format
        """
        if isinstance(file_path, str):
            file_path = Path(file_path)

        # Try to find a parser that can handle this file
        for parser_class in cls._parsers:
            parser = parser_class()
            if parser.can_parse(file_path):
                return parser

        # No parser found
        raise UnsupportedFormatError(
            f"No parser available for file format: {file_path.suffix}",
            file_path=str(file_path)
        )

    @classmethod
    def detect_file_type(cls, file_path: Path) -> str:
        """
        Detect file type using magic numbers (file signatures)

        Args:
            file_path: Path to the file

        Returns:
            MIME type string
        """
        try:
            mime = magic.Magic(mime=True)
            return mime.from_file(str(file_path))
        except Exception:
            # Fallback to extension-based detection
            suffix = file_path.suffix.lower()
            mime_types = {
                '.pdf': 'application/pdf',
                '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                '.doc': 'application/msword',
                '.pptx': 'application/vnd.openxmlformats-officedocument.presentationml.presentation',
                '.ppt': 'application/vnd.ms-powerpoint',
                '.txt': 'text/plain',
                '.html': 'text/html',
                '.htm': 'text/html',
                '.md': 'text/markdown',
                '.markdown': 'text/markdown',
            }
            return mime_types.get(suffix, 'application/octet-stream')

    @classmethod
    def get_supported_formats(cls) -> list[str]:
        """
        Get list of all supported file formats

        Returns:
            List of supported extensions
        """
        formats = set()
        for parser_class in cls._parsers:
            parser = parser_class()
            formats.update(parser.supported_formats)
        return sorted(formats)

    @classmethod
    def register_parser(cls, parser_class: type[BaseParser]):
        """
        Register a new parser

        Args:
            parser_class: Parser class to register
        """
        if parser_class not in cls._parsers:
            cls._parsers.append(parser_class)

    @classmethod
    def is_supported(cls, file_path: Path) -> bool:
        """
        Check if file format is supported

        Args:
            file_path: Path to the file

        Returns:
            True if format is supported
        """
        try:
            cls.get_parser(file_path)
            return True
        except UnsupportedFormatError:
            return False
