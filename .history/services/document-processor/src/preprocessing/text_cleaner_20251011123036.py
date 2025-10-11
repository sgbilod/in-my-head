"""
Text cleaner for removing noise and normalizing whitespace.

Handles:
- Header/footer patterns
- HTML remnants
- Special characters
- Excessive whitespace
- Control characters
"""

import re
from typing import Optional


class TextCleaner:
    """
    Cleans text by removing noise and normalizing whitespace.
    
    Features:
    - Removes common header/footer patterns
    - Strips HTML tags and entities
    - Removes control characters
    - Normalizes whitespace
    - Removes excessive punctuation
    """
    
    def __init__(
        self,
        remove_urls: bool = False,
        remove_emails: bool = False,
        remove_phone_numbers: bool = False,
        min_line_length: int = 3,
    ):
        """
        Initialize text cleaner.
        
        Args:
            remove_urls: Remove URLs from text
            remove_emails: Remove email addresses
            remove_phone_numbers: Remove phone numbers
            min_line_length: Minimum line length to keep (shorter lines removed)
        """
        self.remove_urls = remove_urls
        self.remove_emails = remove_emails
        self.remove_phone_numbers = remove_phone_numbers
        self.min_line_length = min_line_length
        
        # Compile regex patterns
        self._compile_patterns()
    
    def _compile_patterns(self):
        """Compile regex patterns for efficient matching."""
        # HTML patterns
        self.html_tag_pattern = re.compile(r"<[^>]+>")
        self.html_entity_pattern = re.compile(r"&[a-zA-Z]+;|&#\d+;")
        
        # URL pattern
        self.url_pattern = re.compile(
            r"http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+"
        )
        
        # Email pattern
        self.email_pattern = re.compile(
            r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"
        )
        
        # Phone number pattern (US format)
        self.phone_pattern = re.compile(
            r"\b(?:\+?1[-.]?)?\(?\d{3}\)?[-.]?\d{3}[-.]?\d{4}\b"
        )
        
        # Control characters (except newline, tab, carriage return)
        self.control_char_pattern = re.compile(r"[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]")
        
        # Multiple spaces/tabs
        self.multi_space_pattern = re.compile(r"[ \t]+")
        
        # Multiple newlines
        self.multi_newline_pattern = re.compile(r"\n{3,}")
        
        # Common header/footer patterns
        self.header_footer_patterns = [
            re.compile(r"^Page \d+ of \d+$", re.IGNORECASE),
            re.compile(r"^\d+/\d+/\d+$"),  # Dates
            re.compile(r"^-{3,}$"),  # Horizontal lines
            re.compile(r"^={3,}$"),
            re.compile(r"^\*{3,}$"),
            re.compile(r"^_{3,}$"),
            re.compile(r"^\.{3,}$"),
        ]
        
        # Excessive punctuation
        self.excessive_punct_pattern = re.compile(r"([!?.]){4,}")
    
    def clean(self, text: str) -> str:
        """
        Clean text by removing noise and normalizing.
        
        Args:
            text: Raw text to clean
            
        Returns:
            Cleaned text
        """
        if not text:
            return ""
        
        # Remove HTML tags and entities
        text = self._remove_html(text)
        
        # Remove control characters
        text = self.control_char_pattern.sub("", text)
        
        # Remove URLs, emails, phone numbers if requested
        if self.remove_urls:
            text = self.url_pattern.sub("[URL]", text)
        if self.remove_emails:
            text = self.email_pattern.sub("[EMAIL]", text)
        if self.remove_phone_numbers:
            text = self.phone_pattern.sub("[PHONE]", text)
        
        # Normalize whitespace within lines
        text = self.multi_space_pattern.sub(" ", text)
        
        # Process line by line
        lines = text.split("\n")
        cleaned_lines = []
        
        for line in lines:
            line = line.strip()
            
            # Skip empty lines
            if not line:
                continue
            
            # Skip short lines (likely noise)
            if len(line) < self.min_line_length:
                continue
            
            # Skip header/footer patterns
            if self._is_header_footer(line):
                continue
            
            cleaned_lines.append(line)
        
        # Join lines
        text = "\n".join(cleaned_lines)
        
        # Remove excessive punctuation
        text = self.excessive_punct_pattern.sub(r"\1\1\1", text)
        
        # Normalize multiple newlines to max 2
        text = self.multi_newline_pattern.sub("\n\n", text)
        
        # Final trim
        text = text.strip()
        
        return text
    
    def _remove_html(self, text: str) -> str:
        """Remove HTML tags and entities."""
        # Remove HTML tags
        text = self.html_tag_pattern.sub("", text)
        
        # Remove HTML entities
        text = self.html_entity_pattern.sub(" ", text)
        
        return text
    
    def _is_header_footer(self, line: str) -> bool:
        """Check if line matches header/footer patterns."""
        for pattern in self.header_footer_patterns:
            if pattern.match(line):
                return True
        return False
    
    def clean_batch(self, texts: list[str]) -> list[str]:
        """
        Clean multiple texts efficiently.
        
        Args:
            texts: List of texts to clean
            
        Returns:
            List of cleaned texts
        """
        return [self.clean(text) for text in texts]


def clean_text(
    text: str,
    remove_urls: bool = False,
    remove_emails: bool = False,
    remove_phone_numbers: bool = False,
) -> str:
    """
    Convenience function for quick text cleaning.
    
    Args:
        text: Text to clean
        remove_urls: Remove URLs
        remove_emails: Remove email addresses
        remove_phone_numbers: Remove phone numbers
        
    Returns:
        Cleaned text
    """
    cleaner = TextCleaner(
        remove_urls=remove_urls,
        remove_emails=remove_emails,
        remove_phone_numbers=remove_phone_numbers,
    )
    return cleaner.clean(text)
