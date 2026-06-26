"""Parser for EIP markdown files with YAML frontmatter."""

import re
from datetime import date, datetime
from typing import Optional

import frontmatter

from src.models.eip import EIP


def parse_eip_markdown(content: str, eip_number: Optional[int] = None) -> EIP:
    """Parse an EIP markdown file and return an EIP object.
    
    Args:
        content: Raw markdown content of the EIP file
        eip_number: Optional EIP number (extracted from filename if not provided)
    
    Returns:
        EIP object with parsed metadata
    """
    post = frontmatter.loads(content)
    metadata = post.metadata
    
    # Extract EIP number
    number = eip_number or int(metadata.get("eip", 0))
    
    # Parse authors - can be comma-separated string
    authors_raw = metadata.get("author", "")
    if isinstance(authors_raw, str):
        authors = [a.strip() for a in authors_raw.split(",") if a.strip()]
    elif isinstance(authors_raw, list):
        authors = [str(a).strip() for a in authors_raw if str(a).strip()]
    else:
        authors = []
    
    # Parse created date
    created = None
    created_str = metadata.get("created", "")
    if created_str:
        try:
            created = datetime.strptime(str(created_str), "%Y-%m-%d").date()
        except ValueError:
            pass
    
    # Parse requires - can be comma-separated string or list
    requires = []
    requires_raw = metadata.get("requires", [])
    if isinstance(requires_raw, str):
        requires = [int(x.strip()) for x in requires_raw.split(",") if x.strip().isdigit()]
    elif isinstance(requires_raw, list):
        requires = [int(x) for x in requires_raw if str(x).strip().isdigit()]
    
    # Parse last-call-deadline
    last_call_deadline = None
    lcd_str = metadata.get("last-call-deadline", "")
    if lcd_str:
        try:
            last_call_deadline = datetime.strptime(str(lcd_str), "%Y-%m-%d").date()
        except ValueError:
            pass
    
    # Extract description from the abstract section if not in metadata
    description = metadata.get("description", "")
    if not description:
        description = _extract_abstract(post.content)
    
    # Build GitHub URL
    url = f"https://github.com/ethereum/EIPs/blob/master/EIPS/eip-{number}.md"
    
    return EIP(
        number=number,
        title=metadata.get("title", f"EIP-{number}"),
        description=description,
        authors=authors,
        status=metadata.get("status", "Draft"),
        type=metadata.get("type", ""),
        category=metadata.get("category"),
        created=created,
        requires=requires,
        discussions_to=metadata.get("discussions-to"),
        last_call_deadline=last_call_deadline,
        url=url,
    )


def _extract_abstract(content: str) -> str:
    """Extract the abstract section from EIP markdown content."""
    # Look for ## Abstract section
    match = re.search(r"##\n", content, re.IGNORECASE)
    if match:
        # Get text after the heading until next heading
        start = match.end()
        next_heading = re.search(r"\n##\n", content[start:])
        if next_heading:
            return content[start:start + next_heading.start()].strip()
        return content[start:start + 500].strip()
    return ""


def extract_eip_number_from_filename(filename: str) -> Optional[int]:
    """Extract EIP number from filename like 'eip-4844.md'."""
    match = re.match(r"eip-(\d+)\.md", filename, re.IGNORECASE)
    if match:
        return int(match.group(1))
    return None
