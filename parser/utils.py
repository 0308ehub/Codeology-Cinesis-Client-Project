"""
Shared utility functions for parsers.
Contains common parsing logic to avoid duplication.
"""
import re
from typing import Optional, Tuple
from datetime import datetime


def parse_date(date_str: str) -> Optional[datetime]:
    """
    Parse date string into datetime object.
    Supports multiple common date formats.
    
    Args:
        date_str: Date string in various formats
        
    Returns:
        datetime object or None if parsing fails
    """
    if not date_str:
        return None
    
    # Common date formats
    date_formats = [
        '%m/%d/%y',      # 10/28/24
        '%m/%d/%Y',      # 10/28/2024
        '%Y-%m-%d',      # 2024-10-28
        '%m-%d-%Y',      # 10-28-2024
        '%B %d, %Y',     # October 28, 2024
        '%b %d, %Y',     # Oct 28, 2024
        '%d %B %Y',      # 28 October 2024
        '%d %b %Y',      # 28 Oct 2024
        '%m/%d/%Y %I:%M %p',  # With time
    ]
    
    # Clean date string
    date_str = date_str.strip()
    # Remove time if present for some formats
    date_str = re.sub(r'\s+\d{1,2}:\d{2}\s*(AM|PM)?', '', date_str, flags=re.IGNORECASE)
    # Handle multiple dates (take first)
    date_str = date_str.split('\n')[0].strip()
    
    for fmt in date_formats:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    
    return None


def parse_trip(trip_str: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Parse trip string into origin and destination.
    
    Args:
        trip_str: Trip string like "Miami FL to Tampa FL"
        
    Returns:
        Tuple of (origin, destination) or (None, None) if parsing fails
    """
    if not trip_str:
        return None, None
    
    # Common patterns: "City ST to City ST", "City, ST to City, ST"
    patterns = [
        r'(.+?)\s+to\s+(.+)',   # "Miami FL to Tampa FL"
        r'(.+?)\s+→\s+(.+)',     # "Miami FL → Tampa FL"
        r'(.+?)\s+-\s+(.+)',     # "Miami FL - Tampa FL"
        r'(.+?)\s+→\s+(.+)',     # Unicode arrow
    ]
    
    for pattern in patterns:
        match = re.search(pattern, trip_str, re.IGNORECASE)
        if match:
            origin = match.group(1).strip()
            destination = match.group(2).strip()
            return origin, destination
    
    return None, None


def normalize_mc_id(mc_id: str) -> str:
    """
    Normalize MC number by removing all non-numeric characters.
    
    Args:
        mc_id: MC number string
        
    Returns:
        Normalized MC number (digits only)
    """
    if not mc_id:
        return ""
    return re.sub(r'[^\d]', '', str(mc_id))


def extract_rate_from_text(text: str) -> Optional[float]:
    """
    Extract rate amount from text using common patterns.
    
    Args:
        text: Text that may contain rate information
        
    Returns:
        Rate amount as float, or None if not found
    """
    if not text:
        return None
    
    # Rate patterns
    rate_patterns = [
        r'\$(\d+(?:,\d{3})*(?:\.\d{2})?)',           # $1,234.56
        r'(\d+(?:,\d{3})*(?:\.\d{2})?)\s*dollars?',  # 1234.56 dollars
        r'rate[:\s]+\$?([\d,]+\.?\d*)',              # rate: 1234.56
        r'amount[:\s]+\$?([\d,]+\.?\d*)',            # amount: 1234.56
        r'total[:\s]+\$?([\d,]+\.?\d*)',            # total: 1234.56
    ]
    
    for pattern in rate_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            rate_str = match.group(1).replace(',', '')
            try:
                return float(rate_str)
            except ValueError:
                continue
    
    return None

