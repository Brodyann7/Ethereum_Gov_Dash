# EIP Governance Dashboard - Architecture Design

## Overview
A Streamlit-based dashboard for tracking Ethereum L1 governance through EIPs (Ethereum Improvement Proposals). The dashboard will display EIP status, progression through stages, and community discussion activity.

## Data Sources

### 1. EIPs GitHub Repository
- **Repository**: `ethereum/EIPs`
- **Data**: Official EIP metadata from markdown frontmatter
- **Endpoint**: `https://api.github.com/repos/ethereum/EIPs/contents/EIPS`
- **Fields**:
  - `eip`: EIP number
  - `title`: EIP title
  - `description`: Brief description
  - `author`: List of authors with GitHub handles
  - `discussions-to`: Link to Ethereum Magicians discussion
  - `status`: Draft, Review, Last Call, Final, Stagnant, Withdrawn, Living
  - `type`: Standards Track, Meta, Informational
  - `category`: Core, Networking, Interface, ERC (for Standards Track)
  - `created`: Creation date (YYYY-MM-DD)
  - `requires`: List of dependent EIPs
  - `last-call-deadline`: Optional deadline for Last Call period

### 2. Ethereum Magicians Forum API
- **Base URL**: `https://ethereum-magicians.org`
- **Data**: Discussion metrics for each EIP
- **Key Endpoints**:
  - `GET /search.json?q=EIP-{number}` - Find discussion topic for an EIP
  - `GET /t/{topic_id}.json` - Get topic details with post count, views, likes
- **Metrics**:
  - Post count (discussion activity)
  - View count (community interest)
  - Like count (community support)
  - Last posted date (recent activity)
  - Participant count (unique contributors)

## EIP Status Workflow

```
Idea → Draft → Review → Last Call → Final
                    ↓
                Stagnant (6 months inactivity)
                    
Any stage → Withdrawn (by authors)
Living (continually updated, e.g., EIP-1)
```

## Dashboard Layout

### Page 1: Overview
- **Header**: Dashboard title, last updated timestamp
- **Key Metrics Cards**:
  - Total EIPs count
  - EIPs by status (Draft, Review, Last Call, Final, etc.)
  - EIPs by type (Core, Networking, Interface, ERC, Meta, Informational)
  - Recent activity (EIPs updated in last 30 days)
- **Visualizations**:
  - Status distribution pie chart
  - Type distribution bar chart
  - Timeline of EIP creations over time
  - Recent EIPs table (latest 10)

### Page 2: EIP Explorer
- **Filters**:
  - Status (multi-select)
  - Type (multi-select)
  - Category (multi-select)
  - Date range (created)
  - Search by title/author
- **Table**: Sortable, paginated list of EIPs
  - Columns: EIP #, Title, Status, Type, Category, Created, Authors
- **Quick Stats**: Filtered results count

### Page 3: EIP Detail
- **EIP Header**: Number, title, status badge, type/category
- **Metadata Section**: Authors, created date, dependencies, discussion link
- **Description**: EIP abstract/description
- **Discussion Metrics** (from Ethereum Magicians):
  - Post count, views, likes
  - Activity timeline
  - Top contributors
- **Status History**: Timeline of status changes (if available)

### Page 4: Activity Timeline
- **Timeline View**: Chronological list of EIP events
  - New EIPs created
  - Status changes
  - Major discussion milestones
- **Filters**: Date range, event type, EIP type/category

## Data Models

### EIP Model
```python
@dataclass
class EIP:
    number: int
    title: str
    description: str
    authors: List[str]
    status: str  # Draft, Review, Last Call, Final, Stagnant, Withdrawn, Living
    type: str  # Standards Track, Meta, Informational
    category: Optional[str]  # Core, Networking, Interface, ERC
    created: date
    requires: List[int]
    discussions_to: Optional[str]
    last_call_deadline: Optional[date]
    
    # Derived from GitHub API
    url: str
    last_updated: datetime
    
    # From Ethereum Magicians API
    discussion_topic_id: Optional[int]
    discussion_posts: Optional[int]
    discussion_views: Optional[int]
    discussion_likes: Optional[int]
    discussion_last_posted: Optional[datetime]
```

### Discussion Metrics Model
```python
@dataclass
class DiscussionMetrics:
    topic_id: int
    posts_count: int
    views: int
    likes: int
    last_posted_at: datetime
    participants: List[str]
    created_at: datetime
```

## API Integration Layer

### EIPsGitHubClient
```python
class EIPsGitHubClient:
    BASE_URL = "https://api.github.com/repos/ethereum/EIPs"
    
    def get_all_eips(self) -> List[dict]:
        """Fetch list of all EIP files"""
        
    def get_eip_content(self, eip_number: int) -> str:
        """Fetch raw markdown content of an EIP"""
        
    def parse_eip_frontmatter(self, content: str) -> dict:
        """Parse YAML frontmatter from EIP markdown"""
```

### EthereumMagiciansClient
```python
class EthereumMagiciansClient:
    BASE_URL = "https://ethereum-magicians.org"
    
    def search_eip_discussion(self, eip_number: int) -> Optional[dict]:
        """Search for discussion topic for an EIP"""
        
    def get_topic_metrics(self, topic_id: int) -> DiscussionMetrics:
        """Get discussion metrics for a topic"""
```

## Visualization Components

### Charts (using Plotly)
1. **Status Distribution**: Pie chart showing EIPs by status
2. **Type Distribution**: Bar chart showing EIPs by type
3. **Category Distribution**: Stacked bar chart for Standards Track categories
4. **Timeline**: Line chart showing EIP creations over time
5. **Activity Heatmap**: Calendar heatmap of discussion activity
6. **Status Flow**: Sankey diagram showing EIP progression through stages

### Tables
1. **EIP List**: Sortable, filterable table with status badges
2. **Recent Activity**: Timeline of recent EIP events
3. **Top Contributors**: Authors with most EIPs

## Caching Strategy

### In-Memory Cache
- Use `cachetools.TTLCache` for API responses
- TTL: 1 hour for EIP data, 15 minutes for discussion metrics
- Cache key: EIP number or topic ID

### Streamlit Cache
- Use `@st.cache_data` for expensive computations
- Cache parsed EIP data and aggregated metrics
- TTL: 1 hour

## Project Structure

```
ethereum_gov_dash/
├── app.py                    # Main Streamlit application
├── requirements.txt          # Python dependencies
├── .env.example              # Environment variables template
├── src/
│   ├── __init__.py
│   ├── api/
│   │   ├── __init__.py
│   │   ├── github_client.py  # EIPs GitHub API client
│   │   └── magicians_client.py  # Ethereum Magicians API client
│   ├── models/
│   │   ├── __init__.py
│   │   └── eip.py            # EIP and DiscussionMetrics dataclasses
│   ├── parsers/
│   │   ├── __init__.py
│   │   └── eip_parser.py     # EIP frontmatter parser
│   ├── services/
│   │   ├── __init__.py
│   │   └── eip_service.py    # Business logic for EIP data
│   └── ui/
│       ├── __init__.py
│       ├── overview.py       # Overview page
│       ├── explorer.py       # EIP Explorer page
│       ├── detail.py         # EIP Detail page
│       └── timeline.py       # Activity Timeline page
└── tests/
    ├── __init__.py
    ├── test_github_client.py
    ├── test_magicians_client.py
    └── test_eip_parser.py
```

## Implementation Plan

### Phase 1: Core Infrastructure
1. Set up project structure
2. Implement EIPs GitHub API client
3. Implement EIP frontmatter parser
4. Create EIP data model

### Phase 2: Data Integration
1. Implement Ethereum Magicians API client
2. Create EIP service layer with caching
3. Build data aggregation functions

### Phase 3: Dashboard UI
1. Create main Streamlit app with navigation
2. Implement Overview page
3. Implement EIP Explorer page
4. Implement EIP Detail page
5. Implement Activity Timeline page

### Phase 4: Polish & Optimization
1. Add loading states and error handling
2. Optimize API calls with caching
3. Add responsive design
4. Test with real data

## Dependencies

```
streamlit>=1.28.0
requests>=2.31.0
pandas>=2.0.0
plotly>=5.17.0
pyyaml>=6.0
python-frontmatter>=1.0.0
cachetools>=5.3.0
python-dateutil>=2.8.0
```

## Environment Variables

```
GITHUB_TOKEN=your_github_token  # Optional, for higher rate limits
MAGICIANS_API_KEY=your_api_key  # Optional, for higher rate limits
```

## Next Steps

1. Create project structure
2. Implement API clients
3. Build data models and parsers
4. Create Streamlit UI
5. Test and refine