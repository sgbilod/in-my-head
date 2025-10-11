"""
PDF Parser
Handles .pdf files using multiple libraries for best results
"""

from pathlib import Path
import time
from typing import List, Dict, Any

from .base_parser import BaseParser, ParsedDocument, ParsingError, CorruptedFileError

try:
    import PyPDF2
    PYPDF2_AVAILABLE = True
except ImportError:
    PYPDF2_AVAILABLE = False

try:
    import pdfplumber
    PDFPLUMBER_AVAILABLE = True
except ImportError:
    PDFPLUMBER_AVAILABLE = False

try:
    import fitz  # PyMuPDF
    PYMUPDF_AVAILABLE = True
except ImportError:
    PYMUPDF_AVAILABLE = False


class PdfParser(BaseParser):
    """
    PDF parser with multiple backend support
    Priority: PyMuPDF > pdfplumber > PyPDF2
    """

    @property
    def supported_formats(self) -> list[str]:
        return ['.pdf']

    async def parse(self, file_path: Path) -> ParsedDocument:
        """
        Parse PDF file

        Args:
            file_path: Path to the PDF file

        Returns:
            ParsedDocument with extracted content
        """
        start_time = time.time()
        errors = []

        # Try parsers in order of preference
        parsers = [
            (PYMUPDF_AVAILABLE, self._parse_with_pymupdf, "PyMuPDF"),
            (PDFPLUMBER_AVAILABLE, self._parse_with_pdfplumber, "pdfplumber"),
            (PYPDF2_AVAILABLE, self._parse_with_pypdf2, "PyPDF2"),
        ]

        for available, parser_func, parser_name in parsers:
            if available:
                try:
                    result = await parser_func(file_path)
                    result.parser_used = f"{self.name} ({parser_name})"
                    result.parsing_time = time.time() - start_time
                    return result
                except Exception as e:
                    errors.append(f"{parser_name} failed: {str(e)}")

        # All parsers failed
        raise ParsingError(
            f"All PDF parsers failed. Errors: {'; '.join(errors)}",
            parser=self.name,
            file_path=str(file_path)
        )

    async def _parse_with_pymupdf(self, file_path: Path) -> ParsedDocument:
        """Parse PDF using PyMuPDF (fitz)"""
        try:
            doc = fitz.open(file_path)

            # Extract text from all pages
            text_parts = []
            for page in doc:
                text_parts.append(page.get_text())

            text = "\n".join(text_parts)
            text = self._clean_text(text)

            # Extract metadata
            metadata = await self.extract_metadata(file_path)
            pdf_metadata = doc.metadata

            metadata.update({
                'title': pdf_metadata.get('title', ''),
                'author': pdf_metadata.get('author', ''),
                'subject': pdf_metadata.get('subject', ''),
                'creator': pdf_metadata.get('creator', ''),
                'producer': pdf_metadata.get('producer', ''),
                'page_count': len(doc),
                'word_count': len(text.split()),
            })

            # Extract links
            links = self._extract_links(text)

            # Extract images info
            images = []
            for page_num, page in enumerate(doc):
                image_list = page.get_images()
                for img_index, img in enumerate(image_list):
                    images.append({
                        'page': page_num + 1,
                        'index': img_index,
                        'xref': img[0]
                    })

            doc.close()

            return ParsedDocument(
                text=text,
                text_length=len(text),
                metadata=metadata,
                images=images if images else None,
                links=links if links else None,
                parser_used=self.name,
                parsing_time=0.0
            )

        except Exception as e:
            raise ParsingError(f"PyMuPDF parsing failed: {str(e)}")

    async def _parse_with_pdfplumber(self, file_path: Path) -> ParsedDocument:
        """Parse PDF using pdfplumber"""
        try:
            with pdfplumber.open(file_path) as pdf:
                # Extract text from all pages
                text_parts = []
                tables = []

                for page in pdf.pages:
                    text_parts.append(page.extract_text() or "")

                    # Extract tables
                    page_tables = page.extract_tables()
                    if page_tables:
                        tables.extend(page_tables)

                text = "\n".join(text_parts)
                text = self._clean_text(text)

                # Extract metadata
                metadata = await self.extract_metadata(file_path)
                metadata.update({
                    'page_count': len(pdf.pages),
                    'word_count': len(text.split()),
                })

                # Extract links
                links = self._extract_links(text)

                return ParsedDocument(
                    text=text,
                    text_length=len(text),
                    metadata=metadata,
                    tables=tables if tables else None,
                    links=links if links else None,
                    parser_used=self.name,
                    parsing_time=0.0
                )

        except Exception as e:
            raise ParsingError(f"pdfplumber parsing failed: {str(e)}")

    async def _parse_with_pypdf2(self, file_path: Path) -> ParsedDocument:
        """Parse PDF using PyPDF2"""
        try:
            with open(file_path, 'rb') as f:
                reader = PyPDF2.PdfReader(f)

                # Check if PDF is encrypted
                if reader.is_encrypted:
                    raise CorruptedFileError("PDF is encrypted")

                # Extract text from all pages
                text_parts = []
                for page in reader.pages:
                    text_parts.append(page.extract_text())

                text = "\n".join(text_parts)
                text = self._clean_text(text)

                # Extract metadata
                metadata = await self.extract_metadata(file_path)
                pdf_metadata = reader.metadata

                if pdf_metadata:
                    metadata.update({
                        'title': pdf_metadata.get('/Title', ''),
                        'author': pdf_metadata.get('/Author', ''),
                        'subject': pdf_metadata.get('/Subject', ''),
                        'creator': pdf_metadata.get('/Creator', ''),
                        'producer': pdf_metadata.get('/Producer', ''),
                    })

                metadata['page_count'] = len(reader.pages)
                metadata['word_count'] = len(text.split())

                # Extract links
                links = self._extract_links(text)

                return ParsedDocument(
                    text=text,
                    text_length=len(text),
                    metadata=metadata,
                    links=links if links else None,
                    parser_used=self.name,
                    parsing_time=0.0
                )

        except Exception as e:
            raise ParsingError(f"PyPDF2 parsing failed: {str(e)}")
