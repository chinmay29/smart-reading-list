"""HTML/Article parser using trafilatura."""
import re
from typing import Optional
from .base import ContentParser, ParsedContent, registry

try:
    import trafilatura
    from trafilatura.settings import use_config
    TRAFILATURA_AVAILABLE = True
except ImportError:
    TRAFILATURA_AVAILABLE = False

try:
    from readability import Document as ReadabilityDocument
    READABILITY_AVAILABLE = True
except ImportError:
    READABILITY_AVAILABLE = False


class HTMLParser(ContentParser):
    """Parser for HTML web articles.
    
    Uses trafilatura for main content extraction with
    readability-lxml as fallback.
    """
    
    def __init__(self):
        if TRAFILATURA_AVAILABLE:
            # Configure trafilatura for better extraction
            self.config = use_config()
            self.config.set("DEFAULT", "EXTRACTION_TIMEOUT", "30")
    
    def can_parse(self, source: str, mime_type: Optional[str] = None) -> bool:
        """Handle HTML and common web article URLs."""
        if mime_type and mime_type.startswith("text/html"):
            return True
        # Common article URL patterns
        web_patterns = [
            r"https?://",
            r"\.html?$",
            r"\.htm$",
        ]
        return any(re.search(pattern, source, re.IGNORECASE) for pattern in web_patterns)
    
    def parse(self, content: str | bytes, source_url: Optional[str] = None) -> ParsedContent:
        """Extract article content from HTML."""
        if isinstance(content, bytes):
            content = content.decode("utf-8", errors="replace")
        
        # Try trafilatura first (best quality)
        if TRAFILATURA_AVAILABLE:
            result = self._parse_with_trafilatura(content, source_url)
            if result and result.content:
                return result
        
        # Fallback to readability
        if READABILITY_AVAILABLE:
            result = self._parse_with_readability(content)
            if result and result.content:
                return result
        
        # Last resort: basic extraction
        return self._basic_extraction(content)
    
    def _parse_with_trafilatura(self, html: str, url: Optional[str]) -> Optional[ParsedContent]:
        """Use trafilatura for extraction."""
        try:
            # Extract with metadata
            result = trafilatura.extract(
                html,
                url=url,
                include_comments=False,
                include_tables=True,
                no_fallback=False,
                favor_precision=True,
                config=self.config,
            )
            
            if not result:
                return None
            
            # Get metadata separately
            metadata = trafilatura.extract_metadata(html)
            
            return ParsedContent(
                title=metadata.title if metadata else self._extract_title(html),
                content=result,
                author=metadata.author if metadata else None,
                published_date=metadata.date if metadata else None,
                excerpt=result[:500] if result else None,
            )
        except Exception:
            return None
    
    def _parse_with_readability(self, html: str) -> Optional[ParsedContent]:
        """Use readability-lxml as fallback."""
        try:
            doc = ReadabilityDocument(html)
            content = doc.summary()
            
            # Strip remaining HTML tags
            clean_content = re.sub(r"<[^>]+>", " ", content)
            clean_content = re.sub(r"\s+", " ", clean_content).strip()
            
            return ParsedContent(
                title=doc.title(),
                content=clean_content,
                excerpt=clean_content[:500] if clean_content else None,
            )
        except Exception:
            return None
    
    def _basic_extraction(self, html: str) -> ParsedContent:
        """Basic HTML tag stripping as last resort."""
        # Remove script and style
        html = re.sub(r"<script[^>]*>.*?</script>", "", html, flags=re.DOTALL | re.IGNORECASE)
        html = re.sub(r"<style[^>]*>.*?</style>", "", html, flags=re.DOTALL | re.IGNORECASE)
        
        # Strip all tags
        text = re.sub(r"<[^>]+>", " ", html)
        text = re.sub(r"\s+", " ", text).strip()
        
        return ParsedContent(
            title=self._extract_title(html) or "Untitled",
            content=text[:10000],  # Limit content
            excerpt=text[:500] if text else None,
        )
    
    def _extract_title(self, html: str) -> str:
        """Extract title from HTML."""
        # Try <title> tag
        match = re.search(r"<title[^>]*>([^<]+)</title>", html, re.IGNORECASE)
        if match:
            return match.group(1).strip()
        
        # Try <h1>
        match = re.search(r"<h1[^>]*>([^<]+)</h1>", html, re.IGNORECASE)
        if match:
            return match.group(1).strip()
        
        return "Untitled"


# Register the HTML parser
registry.register(HTMLParser())
