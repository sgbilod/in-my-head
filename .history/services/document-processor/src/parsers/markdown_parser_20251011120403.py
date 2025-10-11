"""
Markdown Parser
Handles .md and .markdown files
"""

from pathlib import Path
import time

from .base_parser import BaseParser, ParsedDocument, ParsingError

try:
    import markdown
    from bs4 import BeautifulSoup
    MARKDOWN_AVAILABLE = True
except ImportError:
    MARKDOWN_AVAILABLE = False


class MarkdownParser(BaseParser):
    """Parser for Markdown documents"""
    
    @property
    def supported_formats(self) -> list[str]:
        return ['.md', '.markdown', '.mdown', '.mkd']
    
    async def parse(self, file_path: Path) -> ParsedDocument:
        """
        Parse Markdown file
        
        Args:
            file_path: Path to the Markdown file
            
        Returns:
            ParsedDocument with extracted content
        """
        if not MARKDOWN_AVAILABLE:
            raise ParsingError(
                "markdown library not installed",
                parser=self.name,
                file_path=str(file_path)
            )
        
        start_time = time.time()
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                md_content = f.read()
            
            # Convert markdown to HTML
            html = markdown.markdown(
                md_content,
                extensions=['extra', 'meta', 'tables']
            )
            
            # Parse HTML to extract clean text
            soup = BeautifulSoup(html, 'html.parser')
            text = soup.get_text()
            text = self._clean_text(text)
            
            # Extract metadata
            metadata = await self.extract_metadata(file_path)
            metadata['word_count'] = len(text.split())
            
            # Try to extract title from first H1
            h1 = soup.find('h1')
            if h1:
                metadata['title'] = h1.get_text().strip()
            
            # Extract links
            links = []
            for link in soup.find_all('a', href=True):
                links.append(link['href'])
            
            # Extract code blocks
            code_blocks = []
            for code in soup.find_all('code'):
                code_blocks.append(code.get_text())
            
            if code_blocks:
                metadata['code_blocks_count'] = len(code_blocks)
            
            # Extract tables
            tables = []
            for table in soup.find_all('table'):
                table_data = []
                for row in table.find_all('tr'):
                    row_data = [cell.get_text().strip()
                                for cell in row.find_all(['td', 'th'])]
                    if row_data:
                        table_data.append(row_data)
                if table_data:
                    tables.append(table_data)
            
            parsing_time = time.time() - start_time
            
            return ParsedDocument(
                text=text,
                text_length=len(text),
                metadata=metadata,
                tables=tables if tables else None,
                links=links if links else None,
                parser_used=self.name,
                parsing_time=parsing_time
            )
            
        except Exception as e:
            raise ParsingError(
                f"Failed to parse Markdown file: {str(e)}",
                parser=self.name,
                file_path=str(file_path)
            )
