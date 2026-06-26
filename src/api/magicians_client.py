"""Ethereum Magicians Forum API client for fetching discussion metrics."""

import os
import re
import time
from datetime import datetime
from typing import Optional

import requests
from cachetools import TTLCache

from src.models.eip import DiscussionMetrics


class EthereumMagiciansClient:
    """Client for interacting with the Ethereum Magicians Discourse forum."""
    
    BASE_URL = "https://ethereum-magicians.org"
    
    def __init__(self, api_key: Optional[str] = None, api_username: Optional[str] = None):
        """Initialize the Ethereum Magicians client.
        
        Args:
            api_key: Optional API key for higher rate limits
            api_username: Optional API username (required with api_key)
        """
        self.api_key = api_key or os.getenv("MAGICIANS_API_KEY")
        self.api_username = api_username or os.getenv("MAGICIANS_API_USERNAME")
        
        self.session = requests.Session()
        self.session.headers.update({
            "Accept": "application/json",
            "User-Agent": "EIP-Governance-Dashboard/1.0",
        })
        if self.api_key and self.api_username:
            self.session.headers["Api-Key"] = self.api_key
            self.session.headers["Api-Username"] = self.api_username
        
        # Cache for API responses (15 minutes TTL, max 200 items)
        self._cache = TTLCache(maxsize=200, ttl=900)
        
        # Rate limiting: track last request time
        self._last_request_time = 0
        self._min_request_interval = 1.0  # 1 second between requests
    
    def _rate_limit(self):
        """Enforce rate limiting between requests."""
        elapsed = time.time() - self._last_request_time
        if elapsed < self._min_request_interval:
            time.sleep(self._min_request_interval - elapsed)
        self._last_request_time = time.time()
    
    def _make_request(self, url: str, params: Optional[dict] = None) -> dict:
        """Make a rate-limited API request.
        
        Args:
            url: API endpoint URL
            params: Optional query parameters
        
        Returns:
            JSON response as dictionary
        """
        self._rate_limit()
        
        response = self.session.get(url, params=params, timeout=30)
        
        # Handle rate limiting (Discourse returns 429)
        if response.status_code == 429:
            retry_after = int(response.headers.get("Retry-After", 60))
            print(f"Rate limited by Discourse. Sleeping for {retry_after} seconds...")
            time.sleep(retry_after)
            response = self.session.get(url, params=params, timeout=30)
        
        response.raise_for_status()
        return response.json()
    
    def search_eip_discussion(self, eip_number: int) -> Optional[dict]:
        """Search for the discussion topic for an EIP.
        
        Args:
            eip_number: EIP number to search for
        
        Returns:
            Topic data dictionary if found, None otherwise
        """
        cache_key = f"search_eip_{eip_number}"
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        # Search for EIP discussion
        query = f"EIP-{eip_number}"
        url = f"{self.BASE_URL}/search.json"
        params = {"q": query}
        
        try:
            data = self._make_request(url, params=params)
            topics = data.get("topics", [])
            
            # Find the most relevant topic (usually the first one)
            for topic in topics:
                title = topic.get("title", "")
                # Check if title matches EIP number
                if re.search(rf"EIP-{eip_number}\b", title, re.IGNORECASE):
                    self._cache[cache_key] = topic
                    return topic
            
            # If no exact match, return first result if it's related
            if topics:
                self._cache[cache_key] = topics[0]
                return topics[0]
            
        except Exception as e:
            print(f"Error searching for EIP-{eip_number} discussion: {e}")
        
        return None
    
    def get_topic_details(self, topic_id: int) -> Optional[dict]:
        """Fetch full topic details including all posts.
        
        Args:
            topic_id: Discourse topic ID
        
        Returns:
            Topic details dictionary if found, None otherwise
        """
        cache_key = f"topic_{topic_id}"
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        url = f"{self.BASE_URL}/t/{topic_id}.json"
        
        try:
            data = self._make_request(url)
            self._cache[cache_key] = data
            return data
        except Exception as e:
            print(f"Error fetching topic {topic_id}: {e}")
            return None
    
    def get_topic_metrics(self, topic_id: int) -> Optional[DiscussionMetrics]:
        """Fetch discussion metrics for a topic.
        
        Args:
            topic_id: Discourse topic ID
        
        Returns:
            DiscussionMetrics object if found, None otherwise
        """
        cache_key = f"metrics_{topic_id}"
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        topic_data = self.get_topic_details(topic_id)
        if not topic_data:
            return None
        
        # Extract metrics from topic data
        posts = topic_data.get("post_stream", {}).get("posts", [])
        
        # Get unique participants
        participants = list(set(
            post.get("username", "") for post in posts if post.get("username")
        ))
        
        # Parse dates
        created_at = None
        if topic_data.get("created_at"):
            try:
                created_at = datetime.fromisoformat(
                    topic_data["created_at"].replace("Z", "+00:00")
                )
            except ValueError:
                pass
        
        last_posted_at = None
        if topic_data.get("last_posted_at"):
            try:
                last_posted_at = datetime.fromisoformat(
                    topic_data["last_posted_at"].replace("Z", "+00:00")
                )
            except ValueError:
                pass
        
        metrics = DiscussionMetrics(
            topic_id=topic_id,
            posts_count=topic_data.get("posts_count", len(posts)),
            views=topic_data.get("views", 0),
            like_count=topic_data.get("like_count", 0),
            last_posted_at=last_posted_at,
            created_at=created_at,
            participants=participants,
        )
        
        self._cache[cache_key] = metrics
        return metrics
    
    def get_eip_discussion_metrics(self, eip_number: int) -> Optional[DiscussionMetrics]:
        """Fetch discussion metrics for an EIP.
        
        Args:
            eip_number: EIP number
        
        Returns:
            DiscussionMetrics object if found, None otherwise
        """
        # First search for the discussion topic
        topic = self.search_eip_discussion(eip_number)
        if not topic:
            return None
        
        topic_id = topic.get("id")
        if not topic_id:
            return None
        
        return self.get_topic_metrics(topic_id)
    
    def extract_topic_id_from_url(self, url: str) -> Optional[int]:
        """Extract topic ID from an Ethereum Magicians URL.
        
        Args:
            url: URL like https://ethereum-magicians.org/t/slug/12345
        
        Returns:
            Topic ID if found, None otherwise
        """
        match = re.search(r"/t/[^/]+/(\n", url)
        if match:
            return int(match.group(1))
        return None


# Singleton instance for reuse
_client: Optional[EthereumMagiciansClient] = None


def get_magicians_client() -> EthereumMagiciansClient:
    """Get or create the Ethereum Magicians client singleton."""
    global _client
    if _client is None:
        _client = EthereumMagiciansClient()
    return _client