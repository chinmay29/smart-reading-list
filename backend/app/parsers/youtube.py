"""YouTube video transcript parser."""
import re
from typing import Optional
from urllib.parse import urlparse, parse_qs
from .base import ContentParser, ParsedContent, registry

try:
    from youtube_transcript_api import YouTubeTranscriptApi
    from youtube_transcript_api._errors import (
        TranscriptsDisabled,
        NoTranscriptFound,
        VideoUnavailable,
    )
    YOUTUBE_TRANSCRIPT_AVAILABLE = True
except ImportError:
    YOUTUBE_TRANSCRIPT_AVAILABLE = False
    YouTubeTranscriptApi = None


class YouTubeParser(ContentParser):
    """Parser for YouTube video transcripts.
    
    Extracts video transcripts using the youtube-transcript-api library.
    Transcripts are then used for AI summarization.
    """
    
    # YouTube URL patterns
    YOUTUBE_PATTERNS = [
        r"(?:https?://)?(?:www\.)?youtube\.com/watch\?v=([a-zA-Z0-9_-]{11})",
        r"(?:https?://)?(?:www\.)?youtube\.com/embed/([a-zA-Z0-9_-]{11})",
        r"(?:https?://)?(?:www\.)?youtube\.com/v/([a-zA-Z0-9_-]{11})",
        r"(?:https?://)?youtu\.be/([a-zA-Z0-9_-]{11})",
        r"(?:https?://)?(?:www\.)?youtube\.com/shorts/([a-zA-Z0-9_-]{11})",
    ]
    
    def can_parse(self, source: str, mime_type: Optional[str] = None) -> bool:
        """Check if this is a YouTube URL."""
        return self._extract_video_id(source) is not None
    
    def _extract_video_id(self, url: str) -> Optional[str]:
        """Extract YouTube video ID from URL."""
        for pattern in self.YOUTUBE_PATTERNS:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        
        # Also try parsing query string for edge cases
        try:
            parsed = urlparse(url)
            if "youtube.com" in parsed.netloc or "youtu.be" in parsed.netloc:
                if parsed.path == "/watch":
                    query = parse_qs(parsed.query)
                    if "v" in query:
                        return query["v"][0]
        except Exception:
            pass
        
        return None
    
    def parse(self, content: str | bytes, source_url: Optional[str] = None) -> ParsedContent:
        """Extract transcript from YouTube video.
        
        Args:
            content: HTML content (used for title extraction as fallback)
            source_url: The YouTube video URL
            
        Returns:
            ParsedContent with transcript as content
        """
        if not source_url:
            return self._fallback_parse(content)
        
        video_id = self._extract_video_id(source_url)
        if not video_id:
            return self._fallback_parse(content)
        
        # Extract title from HTML content
        title = self._extract_title_from_html(content) or f"YouTube Video ({video_id})"
        channel = self._extract_channel_from_html(content)
        
        # Try to get transcript
        if not YOUTUBE_TRANSCRIPT_AVAILABLE:
            return ParsedContent(
                title=title,
                content=f"[YouTube Video: {video_id}]\n\nTranscript extraction is not available. "
                        f"Please install youtube-transcript-api: pip install youtube-transcript-api",
                author=channel,
                excerpt="Transcript not available - missing youtube-transcript-api package",
            )
        
        try:
            transcript = self._fetch_transcript(video_id)
            
            if not transcript:
                return ParsedContent(
                    title=title,
                    content=f"[YouTube Video: {video_id}]\n\nNo transcript available for this video. "
                            f"The video may not have captions enabled.",
                    author=channel,
                    excerpt="No transcript available",
                )
            
            # Format transcript nicely
            formatted_transcript = self._format_transcript(transcript)
            
            return ParsedContent(
                title=title,
                content=f"[YouTube Video Transcript]\n\n{formatted_transcript}",
                author=channel,
                excerpt=formatted_transcript[:500] if formatted_transcript else None,
            )
            
        except Exception as e:
            print(f"YouTube transcript extraction failed: {e}")
            return ParsedContent(
                title=title,
                content=f"[YouTube Video: {video_id}]\n\nFailed to extract transcript: {str(e)}",
                author=channel,
                excerpt=f"Transcript extraction failed: {str(e)[:100]}",
            )
    
    def _fetch_transcript(self, video_id: str) -> Optional[list]:
        """Fetch transcript from YouTube.
        
        Uses the youtube-transcript-api v1.x API.
        Tries English transcripts first, then falls back to any available.
        """
        try:
            api = YouTubeTranscriptApi()
            
            # Try to fetch English transcript directly
            try:
                transcript = api.fetch(video_id, languages=['en', 'en-US', 'en-GB'])
                return [{"text": s.text, "start": s.start, "duration": s.duration} for s in transcript]
            except Exception:
                pass
            
            # Get list of available transcripts and try any
            try:
                transcript_list = api.list(video_id)
                # The list method returns a TranscriptList with available transcripts
                # Try to fetch any available transcript
                transcript = api.fetch(video_id)  # Default will get first available
                return [{"text": s.text, "start": s.start, "duration": s.duration} for s in transcript]
            except Exception as e:
                print(f"Could not fetch any transcript: {e}")
                return None
            
        except TranscriptsDisabled:
            print(f"Transcripts are disabled for video: {video_id}")
            return None
        except VideoUnavailable:
            print(f"Video unavailable: {video_id}")
            return None
        except Exception as e:
            print(f"Error fetching transcript: {e}")
            return None
    
    def _format_transcript(self, transcript: list) -> str:
        """Format transcript entries into readable text.
        
        Groups transcript segments into paragraphs for better readability.
        """
        if not transcript:
            return ""
        
        # Combine all text segments
        segments = []
        current_paragraph = []
        
        for entry in transcript:
            text = entry.get("text", "").strip()
            if not text:
                continue
            
            # Clean up common transcript artifacts
            text = text.replace("\n", " ")
            text = re.sub(r"\[.*?\]", "", text)  # Remove [Music], [Applause], etc.
            text = text.strip()
            
            if not text:
                continue
            
            current_paragraph.append(text)
            
            # Break into paragraphs roughly every 5-7 sentences or ~500 chars
            paragraph_text = " ".join(current_paragraph)
            sentence_count = len(re.findall(r"[.!?]+", paragraph_text))
            
            if sentence_count >= 5 or len(paragraph_text) > 500:
                segments.append(paragraph_text)
                current_paragraph = []
        
        # Don't forget the last paragraph
        if current_paragraph:
            segments.append(" ".join(current_paragraph))
        
        return "\n\n".join(segments)
    
    def _extract_title_from_html(self, content: str | bytes) -> Optional[str]:
        """Extract video title from HTML."""
        if isinstance(content, bytes):
            content = content.decode("utf-8", errors="replace")
        
        # Try og:title meta tag (most reliable)
        match = re.search(r'<meta[^>]+property=["\']og:title["\'][^>]+content=["\']([^"\']+)["\']', content, re.IGNORECASE)
        if match:
            return match.group(1).strip()
        
        # Try <title> tag
        match = re.search(r"<title[^>]*>([^<]+)</title>", content, re.IGNORECASE)
        if match:
            title = match.group(1).strip()
            # Remove " - YouTube" suffix
            title = re.sub(r"\s*[-|]\s*YouTube\s*$", "", title, flags=re.IGNORECASE)
            return title
        
        return None
    
    def _extract_channel_from_html(self, content: str | bytes) -> Optional[str]:
        """Extract channel name from HTML."""
        if isinstance(content, bytes):
            content = content.decode("utf-8", errors="replace")
        
        # Try various patterns for channel name
        patterns = [
            r'"author":"([^"]+)"',
            r'"ownerChannelName":"([^"]+)"',
            r'<link[^>]+itemprop=["\']name["\'][^>]+content=["\']([^"\']+)["\']',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, content)
            if match:
                return match.group(1).strip()
        
        return None
    
    def _fallback_parse(self, content: str | bytes) -> ParsedContent:
        """Fallback when we can't extract transcript."""
        if isinstance(content, bytes):
            content = content.decode("utf-8", errors="replace")
        
        title = self._extract_title_from_html(content) or "YouTube Video"
        channel = self._extract_channel_from_html(content)
        
        return ParsedContent(
            title=title,
            content="[YouTube Video]\n\nUnable to extract transcript from this video.",
            author=channel,
            excerpt="Transcript not available",
        )


# Register YouTube parser BEFORE HTML parser (it needs priority)
# We insert at the beginning so it's checked first
registry._parsers.insert(0, YouTubeParser())
