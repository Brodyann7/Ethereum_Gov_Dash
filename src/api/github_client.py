"""GitHub API client for fetching EIP data from ethereum/EIPs repository."""

import os
import re
import time
from datetime import datetime
from typing import Optional

import requests
from cachetools import TTLCache, cached

from src.parsers.eip_parser import parse_eip_markdown, extract_eip_number_from_filename
from src.models.eip import EIP


class EIPsGitHubClient:
    """Client for interacting with the ethereum/EIPs GitHub repository."""
    
    BASE_URL = "https://api.github.com/repos/ethereum/EIPs"
    RAW_URL = "https://raw.githubusercontent.com/ethereum/EIPs/master"
    
    def __init__(self, token: Optional[str] = None):
        """Initialize the GitHub client.
        
        Args:
            token: Optional GitHub personal access token for higher rate limits
        """
        self.token = token or os.getenv("GITHUB_TOKEN")
        self.session = requests.Session()
        self.session.headers.update({
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "EIP-Governance-Dashboard/1.0",
        })
        if self.token:
            self.session.headers["Authorization"] = f"token {self.token}"
        
        # Cache for API responses (1 hour TTL, max 100 items)
        self._cache = TTLCache(maxsize=100, ttl=3600)
    
    def _make_request(self, url: str, params: Optional[dict] = None) -> dict:
        """Make a rate-limited API request.
        
        Args:
            url: API endpoint URL
            params: Optional query parameters
        
        Returns:
            JSON response as dictionary
        """
        response = self.session.get(url, params=params, timeout=30)
        
        # Handle rate limiting
        if response.status_code == 403:
            reset_time = int(response.headers.get("X-RateLimit-Reset", 0))
            sleep_time = max(reset_time - int(time.time()), 1)
            print(f"Rate limited. Sleeping for {sleep_time} seconds...")
            time.sleep(sleep_time)
            response = self.session.get(url, params=params, timeout=30)
        
        response.raise_for_status()
        return response.json()
    
    def get_all_eip_files(self) -> list[dict]:
        """Fetch list of all EIP files from the repository.
        
        Returns:
            List of file metadata dictionaries
        """
        cache_key = "eip_files_list"
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        url = f"{self.BASE_URL}/contents/EIPS"
        files = self._make_request(url)
        
        # Filter to only .md files
        eip_files = [f for f in files if f["name"].endswith(".md") and f["name"].startswith("eip-")]
        
        self._cache[cache_key] = eip_files
        return eip_files
    
    def get_eip_content(self, eip_number: int) -> str:
        """Fetch raw markdown content of an EIP.
        
        Args:
            eip_number: EIP number
        
        Returns:
            Raw markdown content
        """
        cache_key = f"eip_content_{eip_number}"
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        url = f"{self.RAW_URL}/EIPS/eip-{eip_number}.md"
        response = self.session.get(url, timeout=30)
        response.raise_for_status()
        content = response.text
        
        self._cache[cache_key] = content
        return content
    
    def get_eip(self, eip_number: int, include_last_updated: bool = False) -> EIP:
        """Fetch and parse a single EIP.
        
        Args:
            eip_number: EIP number
            include_last_updated: Whether to fetch last commit date (slower)
        
        Returns:
            Parsed EIP object
        """
        content = self.get_eip_content(eip_number)
        eip = parse_eip_markdown(content, eip_number)
        
        # Get last updated time from GitHub API (optional, expensive)
        if include_last_updated:
            try:
                url = f"{self.BASE_URL}/commits?path=EIPS/eip-{eip_number}.md&per_page=1"
                commits = self._make_request(url)
                if commits:
                    eip.last_updated = datetime.fromisoformat(
                        commits[0]["commit"]["committer"]["date"].replace("Z", "+00:00")
                    )
            except Exception:
                pass
        
        return eip
    
    def get_all_eips(self, max_eips: Optional[int] = None) -> list[EIP]:
        """Fetch and parse all EIPs from the repository.
        
        Args:
            max_eips: Optional maximum number of EIPs to fetch (for testing)
        
        Returns:
            List of parsed EIP objects
        """
        files = self.get_all_eip_files()
        
        if max_eips:
            files = files[:max_eips]
        
        eips = []
        for file_info in files:
            eip_number = extract_eip_number_from_filename(file_info["name"])
            if eip_number is None:
                continue
            
            try:
                eip = self.get_eip(eip_number, include_last_updated=False)
                eips.append(eip)
            except Exception as e:
                print(f"Error fetching EIP-{eip_number}: {e}")
                continue
        
        return eips
    
    def get_eips_by_status(self, status: str) -> list[EIP]:
        """Fetch all EIPs with a specific status.
        
        Note: This fetches all EIPs and filters client-side since GitHub API
        doesn't support filtering by file content.
        
        Args:
            status: EIP status to filter by
        
        Returns:
            List of EIPs with the specified status
        """
        all_eips = self.get_all_eips()
        return [eip for eip in all_eips if eip.status == status]
    
    def search_eips(self, query: str) -> list[EIP]:
        """Search EIPs by title or description.
        
        Args:
            query: Search query
        
        Returns:
            List of matching EIPs
        """
        all_eips = self.get_all_eips()
        query_lower = query.lower()
        return [
            eip for eip in all_eips
            if query_lower in eip.title.lower() or query_lower in eip.description.lower()
        ]


# Singleton instance for reuse
_client: Optional[EIPsGitHubClient] = None


def get_github_client() -> EIPsGitHubClient:
    """Get or create the GitHub client singleton."""
    global _client
    if _client is None:
        _client = EIPsGitHubClient()
    return _client