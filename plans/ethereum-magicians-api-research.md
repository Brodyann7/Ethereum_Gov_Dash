# Ethereum Magicians Forum API Research

## Overview
The Ethereum Magicians forum (https://ethereum-magicians.org) runs on **Discourse**, an open-source discussion platform. Discourse provides a comprehensive JSON API that we can use to fetch EIP-related discussions.

## Key API Endpoints

### 1. Categories
```
GET https://ethereum-magicians.org/categories.json
```
Returns all forum categories. EIP discussions are typically in specific categories like:
- "EIPs" (Ethereum Improvement Proposals)
- "RFC" (Request for Comments)
- "Standards"

### 2. Topics (Discussions)
```
GET https://ethereum-magicians.org/c/{category_id}.json
GET https://ethereum-magicians.org/c/{category_id}/{page}.json
```
Returns topics in a specific category with pagination.

**Topic Data Structure:**
```json
{
  "id": 12345,
  "title": "EIP-4844: Shard Blob Transactions",
  "slug": "eip-4844-shard-blob-transactions",
  "posts_count": 150,
  "created_at": "2023-01-01T00:00:00.000Z",
  "last_posted_at": "2023-12-01T00:00:00.000Z",
  "views": 5000,
  "like_count": 45,
  "category_id": 12,
  "tags": ["EIP", "Core", "Networking"],
  "author": {
    "username": "developer_name",
    "avatar_template": "/user_avatar/..."
  }
}
```

### 3. Single Topic Details
```
GET https://ethereum-magicians.org/t/{topic_id}.json
OR
GET https://ethereum-magicians.org/t/{slug}/{topic_id}.json
```
Returns full topic with all posts.

**Post Data Structure:**
```json
{
  "id": 98765,
  "topic_id": 12345,
  "post_number": 1,
  "created_at": "2023-01-01T00:00:00.000Z",
  "updated_at": "2023-01-02T00:00:00.000Z",
  "cooked": "<div>HTML content of post</div>",
  "raw": "Markdown content of post",
  "username": "author_name",
  "like_count": 10,
  "reply_count": 5,
  "reads": 200
}
```

### 4. Latest Topics
```
GET https://ethereum-magicians.org/latest.json
GET https://ethereum-magicians.org/latest.json?page=1
```
Returns most recently active topics across all categories.

### 5. Search
```
GET https://ethereum-magicians.org/search.json?q=EIP-4844
```
Search for topics containing specific terms.

## Rate Limiting
- Discourse has built-in rate limiting
- Typically: 60 requests per minute for unauthenticated users
- Higher limits with API key authentication

## Authentication (Optional)
For higher rate limits, you can use:
```
Api-Key: YOUR_API_KEY
Api-Username: your_username
```

## Data Extraction Strategy

### EIP Identification
EIP topics typically follow naming conventions:
- Title starts with "EIP-{number}:"
- Tags include "EIP"
- Located in EIP-specific categories

### Status Tracking
EIP status can be inferred from:
1. Topic tags (e.g., "Draft", "Review", "Final", "Stagnant")
2. Category placement
3. Last activity date (stagnant if no activity > 6 months)

### Metrics to Extract
- **Engagement**: posts_count, views, like_count
- **Activity**: created_at, last_posted_at
- **Participants**: unique usernames in posts
- **Discussion depth**: reply_count, post_number distribution

## Next Steps for Implementation

1. **Verify API Access**: Test endpoints with curl/Python requests
2. **Identify EIP Categories**: Find category IDs for EIP discussions
3. **Build Data Fetcher**: Create Python module to fetch topics
4. **Parse EIP Numbers**: Extract EIP-{number} from titles
5. **Track Status Changes**: Monitor tag/category changes over time

## Python Libraries Needed
```
requests          # HTTP requests
pandas            # Data manipulation
streamlit         # Dashboard framework
plotly            # Visualizations
cachetools        # API response caching
```

## Sample Python Code Structure
```python
import requests
import pandas as pd
from datetime import datetime

class EthereumMagiciansAPI:
    BASE_URL = "https://ethereum-magicians.org"
    
    def __init__(self, api_key=None):
        self.headers = {}
        if api_key:
            self.headers['Api-Key'] = api_key
    
    def get_eip_topics(self, category_id, page=0):
        """Fetch EIP topics from a specific category"""
        url = f"{self.BASE_URL}/c/{category_id}/{page}.json"
        response = requests.get(url, headers=self.headers)
        return response.json()
    
    def get_topic_details(self, topic_id):
        """Fetch full topic with all posts"""
        url = f"{self.BASE_URL}/t/{topic_id}.json"
        response = requests.get(url, headers=self.headers)
        return response.json()
    
    def search_eips(self, query):
        """Search for EIP-related discussions"""
        url = f"{self.BASE_URL}/search.json?q={query}"
        response = requests.get(url, headers=self.headers)
        return response.json()
```

## Questions to Verify
- [ ] What are the exact category IDs for EIP discussions?
- [ ] Are there any authentication requirements?
- [ ] What is the actual rate limit?
- [ ] Do topics have consistent EIP numbering in titles?
- [ ] Are status tags consistently applied?
