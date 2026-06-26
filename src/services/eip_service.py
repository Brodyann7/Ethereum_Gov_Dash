"""Service layer for EIP data aggregation and processing."""

from datetime import datetime, timedelta
from typing import Optional

import pandas as pd
from cachetools import TTLCache

from src.api.github_client import get_github_client
from src.api.magicians_client import get_magicians_client
from src.models.eip import EIP, DiscussionMetrics


class EIPService:
    """Service for fetching and aggregating EIP data."""
    
    def __init__(self):
        self.github_client = get_github_client()
        self.magicians_client = get_magicians_client()
        
        # Cache for aggregated data (1 hour TTL)
        self._cache = TTLCache(maxsize=10, ttl=3600)
        self._all_eips: Optional[list[EIP]] = None
    
    def get_all_eips(self, force_refresh: bool = False) -> list[EIP]:
        """Get all EIPs with caching.
        
        Args:
            force_refresh: Force refresh from API
        
        Returns:
            List of all EIPs
        """
        if self._all_eips is not None and not force_refresh:
            return self._all_eips
        
        self._all_eips = self.github_client.get_all_eips()
        return self._all_eips
    
    def get_eip(self, eip_number: int) -> Optional[EIP]:
        """Get a single EIP by number.
        
        Args:
            eip_number: EIP number
        
        Returns:
            EIP object if found, None otherwise
        """
        eips = self.get_all_eips()
        for eip in eips:
            if eip.number == eip_number:
                return eip
        return None
    
    def get_eips_by_status(self, status: str) -> list[EIP]:
        """Get all EIPs with a specific status.
        
        Args:
            status: EIP status
        
        Returns:
            List of EIPs with the specified status
        """
        eips = self.get_all_eips()
        return [eip for eip in eips if eip.status == status]
    
    def get_eips_by_type(self, eip_type: str) -> list[EIP]:
        """Get all EIPs of a specific type.
        
        Args:
            eip_type: EIP type (Standards Track, Meta, Informational)
        
        Returns:
            List of EIPs of the specified type
        """
        eips = self.get_all_eips()
        return [eip for eip in eips if eip.type == eip_type]
    
    def get_eips_by_category(self, category: str) -> list[EIP]:
        """Get all EIPs in a specific category.
        
        Args:
            category: EIP category (Core, Networking, Interface, ERC)
        
        Returns:
            List of EIPs in the specified category
        """
        eips = self.get_all_eips()
        return [eip for eip in eips if eip.category == category]
    
    def get_recent_eips(self, days: int = 30) -> list[EIP]:
        """Get EIPs created or updated in the last N days.
        
        Args:
            days: Number of days to look back
        
        Returns:
            List of recent EIPs
        """
        cutoff = datetime.now() - timedelta(days=days)
        eips = self.get_all_eips()
        
        recent = []
        for eip in eips:
            if eip.created and eip.created >= cutoff.date():
                recent.append(eip)
            elif eip.last_updated and eip.last_updated >= cutoff:
                recent.append(eip)
        
        return recent
    
    def search_eips(self, query: str) -> list[EIP]:
        """Search EIPs by title, description, or author.
        
        Args:
            query: Search query
        
        Returns:
            List of matching EIPs
        """
        eips = self.get_all_eips()
        query_lower = query.lower()
        
        results = []
        for eip in eips:
            if (query_lower in eip.title.lower() or
                query_lower in eip.description.lower() or
                any(query_lower in author.lower() for author in eip.authors)):
                results.append(eip)
        
        return results
    
    def get_discussion_metrics(self, eip: EIP) -> Optional[DiscussionMetrics]:
        """Get discussion metrics for an EIP.
        
        Args:
            eip: EIP object
        
        Returns:
            DiscussionMetrics if available, None otherwise
        """
        # If already have metrics, return them
        if eip.discussion:
            return eip.discussion
        
        # Try to get from discussions-to URL
        if eip.discussions_to:
            topic_id = self.magicians_client.extract_topic_id_from_url(eip.discussions_to)
            if topic_id:
                metrics = self.magicians_client.get_topic_metrics(topic_id)
                if metrics:
                    eip.discussion = metrics
                    return metrics
        
        # Fall back to search
        metrics = self.magicians_client.get_eip_discussion_metrics(eip.number)
        if metrics:
            eip.discussion = metrics
        return metrics
    
    def get_statistics(self) -> dict:
        """Get aggregate statistics about all EIPs.
        
        Returns:
            Dictionary of statistics
        """
        eips = self.get_all_eips()
        
        # Count by status
        status_counts = {}
        for eip in eips:
            status_counts[eip.status] = status_counts.get(eip.status, 0) + 1
        
        # Count by type
        type_counts = {}
        for eip in eips:
            type_counts[eip.type] = type_counts.get(eip.type, 0) + 1
        
        # Count by category
        category_counts = {}
        for eip in eips:
            if eip.category:
                category_counts[eip.category] = category_counts.get(eip.category, 0) + 1
        
        # Active vs finalized
        active_count = sum(1 for eip in eips if eip.is_active)
        finalized_count = sum(1 for eip in eips if eip.is_finalized)
        
        return {
            "total": len(eips),
            "by_status": status_counts,
            "by_type": type_counts,
            "by_category": category_counts,
            "active": active_count,
            "finalized": finalized_count,
        }
    
    def to_dataframe(self, eips: Optional[list[EIP]] = None) -> pd.DataFrame:
        """Convert EIPs to a pandas DataFrame.
        
        Args:
            eips: Optional list of EIPs (uses all if not provided)
        
        Returns:
            DataFrame with EIP data
        """
        if eips is None:
            eips = self.get_all_eips()
        
        data = [eip.to_dict() for eip in eips]
        df = pd.DataFrame(data)
        
        # Sort by EIP number
        if not df.empty:
            df = df.sort_values("number", ascending=True)
        
        return df
    
    def get_timeline_data(self) -> pd.DataFrame:
        """Get timeline data for EIP creations over time.
        
        Returns:
            DataFrame with date and count columns
        """
        eips = self.get_all_eips()
        
        # Group by creation date
        timeline = {}
        for eip in eips:
            if eip.created:
                date_key = eip.created
                timeline[date_key] = timeline.get(date_key, 0) + 1
        
        # Convert to DataFrame
        df = pd.DataFrame([
            {"date": date, "count": count}
            for date, count in sorted(timeline.items())
        ])
        
        return df


# Singleton instance
_service: Optional[EIPService] = None


def get_eip_service() -> EIPService:
    """Get or create the EIP service singleton."""
    global _service
    if _service is None:
        _service = EIPService()
    return _service