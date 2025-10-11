"""
Plain Text Parser
Handles .txt files
"""

from pathlib import Path
import time
import chardet

from .base_parser import BaseParser, ParsedDocument, ParsingError


class TxtParser(BaseParser):
    """Parser for plain text files"""
    
    @property
    def supported_formats(self) -> list[str]:
        return ['.txt', '.text', '.log']
    
    async def parse(self, file_path: Path) -> ParsedDocument:
        """
        Parse plain text file
        
        Args:
            file_path: Path to the text file
            
        Returns:
            ParsedDocument with extracted content
        """
        start_time = time.time()
        errors = []
        
        try:
            # Detect encoding
            with open(file_path, 'rb') as f:
                raw_data = f.read()
                detected = chardet.detect(raw_data)
                encoding = detected['encoding'] or 'utf-8'
            
            # Read text with detected encoding
            try:
                text = raw_data.decode(encoding)
            except UnicodeDecodeError:
                # Fallback to utf-8 with error handling
                text = raw_data.decode('utf-8', errors='ignore')
                errors.append(f"Encoding issues detected. Used fallback decoding.")
            
            # Extract metadata
            metadata = await self.extract_metadata(file_path)
            metadata['encoding'] = encoding
            metadata['word_count'] = len(text.split())
            metadata['line_count'] = len(text.splitlines())
            metadata['char_count'] = len(text)
            
            # Extract links
            links = self._extract_links(text)
            
            parsing_time = time.time() - start_time
            
            return ParsedDocument(
                text=text,
                text_length=len(text),
                metadata=metadata,
                links=links if links else None,
                parser_used=self.name,
                parsing_time=parsing_time,
                parsing_errors=errors if errors else None
            )
            
        except Exception as e:
            raise ParsingError(
                f"Failed to parse text file: {str(e)}",
                parser=self.name,
                file_path=str(file_path)
            )
