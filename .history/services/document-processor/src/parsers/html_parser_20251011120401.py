"""
HTML Parser
Handles .html and .htm files
"""

from pathlib import Path
import time

from .base_parser import BaseParser, ParsedDocument, ParsingError

try:
    from bs4 import BeautifulSoup
    BS4_AVAILABLE = True
except ImportError:
    BS4_AVAILABLE = False


class HtmlParser(BaseParser):
    """Parser for HTML documents"""
    
    @property
    def supported_formats(self) -> list[str]:
        return ['.html', '.htm']
    
    async def parse(self, file_path: Path) -> ParsedDocument:
        """
        Parse HTML file
        
        Args:
            file_path: Path to the HTML file
            
        Returns:
            ParsedDocument with extracted content
        """
        if not BS4_AVAILABLE:
            raise ParsingError(
                "beautifulsoup4 library not installed",
                parser=self.name,
                file_path=str(file_path)
            )
        
        start_time = time.time()
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                html_content = f.read()
            
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()
            
            # Extract text
            text = soup.get_text()
            text = self._clean_text(text)
            
            # Extract metadata
            metadata = await self.extract_metadata(file_path)
            
            # Try to extract HTML metadata
            title_tag = soup.find('title')
            if title_tag:
                metadata['title'] = title_tag.get_text().strip()
            
            # Meta tags
            meta_tags = {}
            for meta in soup.find_all('meta'):
                name = meta.get('name') or meta.get('property')
                content = meta.get('content')
                if name and content:
                    meta_tags[name] = content
            
            metadata['meta_tags'] = meta_tags
            metadata['word_count'] = len(text.split())
            
            # Extract links
            links = []
            for link in soup.find_all('a', href=True):
                links.append(link['href'])
            
            # Extract images
            images = []
            for img in soup.find_all('img', src=True):
                images.append({
                    'src': img['src'],
                    'alt': img.get('alt', '')
                })
            
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
                images=images if images else None,
                tables=tables if tables else None,
                links=links if links else None,
                parser_used=self.name,
                parsing_time=parsing_time
            )
            
        except Exception as e:
            raise ParsingError(
                f"Failed to parse HTML file: {str(e)}",
                parser=self.name,
                file_path=str(file_path)
            )
