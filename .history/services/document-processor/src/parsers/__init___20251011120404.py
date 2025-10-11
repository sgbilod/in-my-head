"""
Document Parsers Package
Provides parsers for multiple document formats
"""

from .base_parser import (
    BaseParser,
    ParsedDocument,
    ParsingError,
    UnsupportedFormatError,
    CorruptedFileError
)
from .parser_factory import ParserFactory
from .txt_parser import TxtParser
from .pdf_parser import PdfParser
from .docx_parser import DocxParser
from .pptx_parser import PptxParser
from .html_parser import HtmlParser
from .markdown_parser import MarkdownParser

__all__ = [
    # Base classes
    'BaseParser',
    'ParsedDocument',
    'ParsingError',
    'UnsupportedFormatError',
    'CorruptedFileError',
    
    # Factory
    'ParserFactory',
    
    # Individual parsers
    'TxtParser',
    'PdfParser',
    'DocxParser',
    'PptxParser',
    'HtmlParser',
    'MarkdownParser',
]
