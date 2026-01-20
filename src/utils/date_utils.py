"""Date parsing and formatting utilities"""
from datetime import datetime
from typing import Optional
from dateutil import parser as dateutil_parser


def parse_xer_date(date_str: Optional[str]) -> Optional[datetime]:
    """
    Parse date from XER format to Python datetime

    XER date formats:
    - YYYY-MM-DD HH:MM
    - YYYY-MM-DD-HH.MM
    - YYYY-MM-DD

    Args:
        date_str: Date string from XER file

    Returns:
        datetime object or None if date_str is empty/None
    """
    if not date_str or date_str.strip() == '':
        return None

    try:
        # Replace - with space for time separator
        # Handle both "YYYY-MM-DD HH:MM" and "YYYY-MM-DD-HH.MM" formats
        cleaned = date_str.strip()

        # Try parsing with dateutil (handles multiple formats)
        dt = dateutil_parser.parse(cleaned)
        return dt

    except (ValueError, TypeError):
        return None


def format_iso8601(dt: Optional[datetime]) -> Optional[str]:
    """
    Format datetime to ISO 8601 with Z timezone

    Args:
        dt: datetime object

    Returns:
        ISO 8601 formatted string with Z suffix, or None
    """
    if dt is None:
        return None

    # Format as ISO 8601 and append Z (UTC)
    return dt.isoformat() + 'Z'
