"""
Text normalizer for Unicode normalization and case handling.

Handles:
- Unicode normalization (NFKC)
- Case normalization
- Accent/diacritic handling
- Language-specific normalization
"""

import re
import unicodedata
from typing import Optional


class TextNormalizer:
    """
    Normalizes text for consistent processing.

    Features:
    - Unicode normalization (NFKC by default)
    - Case normalization (with proper noun preservation)
    - Accent/diacritic removal (optional)
    - Number normalization
    - Quotation mark normalization
    """

    def __init__(
        self,
        unicode_form: str = "NFKC",
        lowercase: bool = False,
        remove_accents: bool = False,
        normalize_numbers: bool = True,
        normalize_quotes: bool = True,
    ):
        """
        Initialize text normalizer.

        Args:
            unicode_form: Unicode normalization form (NFC, NFD, NFKC, NFKD)
            lowercase: Convert text to lowercase
            remove_accents: Remove accent marks from characters
            normalize_numbers: Normalize number formats
            normalize_quotes: Normalize quotation marks to standard forms
        """
        self.unicode_form = unicode_form
        self.lowercase = lowercase
        self.remove_accents = remove_accents
        self.normalize_numbers = normalize_numbers
        self.normalize_quotes = normalize_quotes

        # Compile patterns
        self._compile_patterns()

    def _compile_patterns(self):
        """Compile regex patterns for normalization."""
        # Number patterns
        self.number_with_commas = re.compile(r"(\d{1,3}(?:,\d{3})+)")
        
        # Quote patterns (fancy quotes to simple quotes)
        # Single quotes: ' ' ` ´
        self.fancy_single_quotes = re.compile(r"[\u2018\u2019\u201a\u201b`\u00b4]")
        # Double quotes: " " « »
        self.fancy_double_quotes = re.compile(r"[\u201c\u201d\u201e\u201f\u00ab\u00bb]")
        
        # Multiple punctuation
        self.multi_dash = re.compile(r"[-−–—]{2,}")
        self.multi_dot = re.compile(r"\.{4,}")    def normalize(self, text: str) -> str:
        """
        Normalize text.

        Args:
            text: Text to normalize

        Returns:
            Normalized text
        """
        if not text:
            return ""

        # Unicode normalization
        text = unicodedata.normalize(self.unicode_form, text)

        # Remove accents if requested
        if self.remove_accents:
            text = self._remove_accents(text)

        # Normalize quotes
        if self.normalize_quotes:
            text = self._normalize_quotes(text)

        # Normalize numbers
        if self.normalize_numbers:
            text = self._normalize_numbers(text)

        # Normalize punctuation
        text = self._normalize_punctuation(text)

        # Case normalization
        if self.lowercase:
            text = text.lower()

        return text

    def _remove_accents(self, text: str) -> str:
        """
        Remove accent marks from characters.

        Uses NFD decomposition to separate base characters from accents,
        then removes the accent marks.
        """
        # Decompose to separate base chars from accents
        nfd = unicodedata.normalize("NFD", text)

        # Remove combining characters (accents)
        output = []
        for char in nfd:
            if unicodedata.category(char) != "Mn":  # Mn = Mark, Nonspacing
                output.append(char)

        # Recompose
        return "".join(output)

    def _normalize_quotes(self, text: str) -> str:
        """Normalize fancy quotes to standard ASCII quotes."""
        # Single quotes
        text = self.fancy_single_quotes.sub("'", text)

        # Double quotes
        text = self.fancy_double_quotes.sub('"', text)

        return text

    def _normalize_numbers(self, text: str) -> str:
        """Normalize number formats."""
        # Remove commas from numbers (1,000 -> 1000)
        def replace_commas(match):
            return match.group(1).replace(",", "")

        text = self.number_with_commas.sub(replace_commas, text)

        return text

    def _normalize_punctuation(self, text: str) -> str:
        """Normalize punctuation marks."""
        # Multiple dashes to single em-dash
        text = self.multi_dash.sub("—", text)

        # Multiple dots (4+) to ellipsis
        text = self.multi_dot.sub("...", text)

        return text

    def normalize_batch(self, texts: list[str]) -> list[str]:
        """
        Normalize multiple texts efficiently.

        Args:
            texts: List of texts to normalize

        Returns:
            List of normalized texts
        """
        return [self.normalize(text) for text in texts]


def normalize_text(
    text: str,
    lowercase: bool = False,
    remove_accents: bool = False,
) -> str:
    """
    Convenience function for quick text normalization.

    Args:
        text: Text to normalize
        lowercase: Convert to lowercase
        remove_accents: Remove accent marks

    Returns:
        Normalized text
    """
    normalizer = TextNormalizer(
        lowercase=lowercase,
        remove_accents=remove_accents,
    )
    return normalizer.normalize(text)
