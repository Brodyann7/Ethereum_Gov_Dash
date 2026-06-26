"""Data models for EIP governance dashboard."""

from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Optional


@dataclass
class DiscussionMetrics:
    """Metrics from Ethereum Magicians forum discussion."""
    topic_id: int
    posts_count: int = 0
    views: int = 0
    like_count: int = 0
    last_posted_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    participants: list[str] = field(default_factory=list)


@dataclass
class EIP:
    """Represents an Ethereum Improvement Proposal."""
    number: int
    title: str
    description: str = ""
    authors: list[str] = field(default_factory=list)
    status: str = "Draft"  # Draft, Review, Last Call, Final, Stagnant, Withdrawn, Living
    type: str = ""  # Standards Track, Meta, Informational
    category: Optional[str] = None  # Core, Networking, Interface, ERC
    created: Optional[date] = None
    requires: list[int] = field(default_factory=list)
    discussions_to: Optional[str] = None
    last_call_deadline: Optional[date] = None
    
    # GitHub metadata
    url: str = ""
    last_updated: Optional[datetime] = None
    
    # Discussion metrics (from Ethereum Magicians)
    discussion: Optional[DiscussionMetrics] = None
    
    @property
    def status_order(self) -> int:
        """Return numeric order for status (for sorting)."""
        status_map = {
            "Idea": 0,
            "Draft": 1,
            "Review": 2,
            "Last Call": 3,
            "Final": 4,
            "Living": 5,
            "Stagnant": 6,
            "Withdrawn": 7,
        }
        return status_map.get(self.status, 99)
    
    @property
    def is_active(self) -> bool:
        """Check if EIP is in an active state."""
        return self.status in ("Draft", "Review", "Last Call")
    
    @property
    def is_finalized(self) -> bool:
        """Check if EIP has reached finality."""
        return self.status in ("Final", "Living")
    
    @property
    def short_authors(self) -> str:
        """Return comma-separated author names (truncated if too many)."""
        if len(self.authors) <= 3:
            return ", ".join(self.authors)
        return ", ".join(self.authors[:3]) + f" +{len(self.authors) - 3}"
    
    def to_dict(self) -> dict:
        """Convert to dictionary for DataFrame creation."""
        return {
            "number": self.number,
            "title": self.title,
            "description": self.description,
            "authors": self.authors,
            "status": self.status,
            "type": self.type,
            "category": self.category,
            "created": self.created,
            "requires": self.requires,
            "discussions_to": self.discussions_to,
            "last_call_deadline": self.last_call_deadline,
            "url": self.url,
            "last_updated": self.last_updated,
            "discussion_posts": self.discussion.posts_count if self.discussion else None,
            "discussion_views": self.discussion.views if self.discussion else None,
            "discussion_likes": self.discussion.like_count if self.discussion else None,
            "discussion_last_posted": self.discussion.last_posted_at if self.discussion else None,
        }


# Valid EIP statuses
EIP_STATUSES = ["Draft", "Review", "Last Call", "Final", "Stagnant", "Withdrawn", "Living"]

# Valid EIP types
EIP_TYPES = ["Standards Track", "Meta", "Informational"]

# Valid EIP categories (for Standards Track)
EIP_CATEGORIES = ["Core", "Networking", "Interface", "ERC"]

# Status colors for UI
STATUS_COLORS = {
    "Draft": "#6366f1",       # Indigo
    "Review": "#f59e0b",      # Amber
    "Last Call": "#ef4444",   # Red
    "Final": "#10b981",       # Green
    "Stagnant": "#6b7280",    # Gray
    "Withdrawn": "#dc2626",   # Dark red
    "Living": "#8b5cf6",      # Purple
}