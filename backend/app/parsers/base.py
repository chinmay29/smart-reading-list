"""Parser registry for extensible document format support."""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional


@dataclass
class ParsedContent:
    """Result of parsing a document."""
    title: str
    content: str  # Clean text content
    author: Optional[str] = None
    published_date: Optional[str] = None
    excerpt: Optional[str] = None  # First paragraph or meta description


class ContentParser(ABC):
    """Abstract base class for content parsers.
    
    To add support for a new format (e.g., PDF):
    1. Create a new parser class extending ContentParser
    2. Implement can_parse() and parse() methods
    3. Register in PARSERS list below
    """
    
    @abstractmethod
    def can_parse(self, source: str, mime_type: Optional[str] = None) -> bool:
        """Check if this parser can handle the given source."""
        pass
    
    @abstractmethod
    def parse(self, content: str | bytes, source_url: Optional[str] = None) -> ParsedContent:
        """Parse the content and return structured data."""
        pass


class ParserRegistry:
    """Registry of all available parsers."""
    
    def __init__(self):
        self._parsers: list[ContentParser] = []
    
    def register(self, parser: ContentParser) -> None:
        """Register a new parser."""
        self._parsers.append(parser)
    
    def get_parser(self, source: str, mime_type: Optional[str] = None) -> Optional[ContentParser]:
        """Get the appropriate parser for a source."""
        for parser in self._parsers:
            if parser.can_parse(source, mime_type):
                return parser
        return None
    
    def parse(self, content: str | bytes, source: str, mime_type: Optional[str] = None) -> ParsedContent:
        """Parse content using the appropriate parser."""
        parser = self.get_parser(source, mime_type)
        if parser is None:
            raise ValueError(f"No parser available for source: {source}, mime_type: {mime_type}")
        return parser.parse(content, source)


# Global registry instance
registry = ParserRegistry()


def get_parser_registry() -> ParserRegistry:
    """Get the global parser registry."""
    return registry
