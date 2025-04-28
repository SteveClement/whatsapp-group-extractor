"""Utility functions for the WhatsApp chat exporter."""

import re
from datetime import datetime
from typing import Optional

def parse_timestamp(timestamp_str: str) -> Optional[datetime]:
    """Parse timestamp string into a datetime object, handling multiple formats.
    
    Args:
        timestamp_str: String representation of timestamp from WhatsApp
        
    Returns:
        datetime object if parsing succeeds, None if all formats fail
    """
    # Remove any brackets if present
    timestamp_str = timestamp_str.strip()
    if timestamp_str.startswith('['):
        timestamp_str = timestamp_str[1:]
    if timestamp_str.endswith(']'):
        timestamp_str = timestamp_str[:-1]
    
    # Try different formats
    formats = [
        '%d/%m/%Y, %H:%M:%S',  # Desktop format: 16/04/2024, 11:59:24
        '%d/%m/%Y, %H:%M',     # Desktop format without seconds
        '%m/%d/%y, %H:%M',     # US mobile format: 8/22/23, 10:33
        '%d/%m/%y, %H:%M',     # European mobile format: 22/8/23, 10:33
        '%d/%m/%y, %H:%M:%S',  # European mobile format with seconds
        '%m/%d/%Y, %H:%M',     # US format with 4-digit year
        '%m/%d/%Y, %H:%M:%S'   # US format with 4-digit year and seconds
    ]
    
    for fmt in formats:
        try:
            return datetime.strptime(timestamp_str, fmt)
        except ValueError:
            continue
    
    # If all formats fail, return None
    return None

def extract_title_from_info(info_text: str) -> str:
    """Extract chat title from info.txt content.
    
    Args:
        info_text: Content of the info.txt file
        
    Returns:
        Title string if found, otherwise "WhatsApp Chat"
    """
    if not info_text:
        return "WhatsApp Chat"
        
    lines = info_text.splitlines()
    if lines and lines[0].startswith("Title:"):
        return lines[0][6:].strip()
        
    return "WhatsApp Chat"
