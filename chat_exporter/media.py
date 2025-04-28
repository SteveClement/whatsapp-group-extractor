"""Media file handling for WhatsApp chat exports."""

import os
from typing import Optional

def find_media_file(extract_dir: str, filename: str) -> Optional[str]:
    """Find a media file in the extracted directory.
    
    Args:
        extract_dir: Directory containing the extracted WhatsApp export
        filename: Name of the media file to find
        
    Returns:
        Path to the found media file, or None if not found
    """
    # Direct match first
    for root, _, files in os.walk(extract_dir):
        if filename in files:
            return os.path.join(root, filename)
    
    # Try different approaches based on file naming patterns
    if '-' in filename:
        # Handle desktop format: 00000179-PHOTO-2024-04-24-16-21-11.jpg
        parts = filename.split('-')
        if len(parts) >= 2:
            file_id = parts[0]
            file_type = parts[1].lower()
            
            # Try matching by ID and type
            for root, _, files in os.walk(extract_dir):
                for file in files:
                    if file.startswith(file_id) and file_type.lower() in file.lower():
                        return os.path.join(root, file)
    
    # Handle mobile format: IMG-20250425-WA0051.jpg
    # Extract the base pattern (IMG-20250425-WA0051)
    base_name = os.path.splitext(filename)[0]
    extension = os.path.splitext(filename)[1]
    
    for root, _, files in os.walk(extract_dir):
        for file in files:
            # Check if file matches the pattern (exact or with different extension)
            if file.startswith(base_name) or (base_name in file and file.endswith(extension)):
                return os.path.join(root, file)
    
    # Last resort: try a fuzzy match based on key parts of the filename
    # For WhatsApp mobile exports like IMG-20250425-WA0051.jpg
    if filename.startswith(('IMG-', 'VID-', 'AUD-', 'DOC-')) and 'WA' in filename:
        pattern_parts = filename.split('-')
        if len(pattern_parts) >= 3:
            wa_part = next((part for part in pattern_parts if part.startswith('WA')), None)
            date_part = next((part for part in pattern_parts if len(part) == 8 and part.isdigit()), None)
            
            if wa_part or date_part:
                for root, _, files in os.walk(extract_dir):
                    for file in files:
                        if (wa_part and wa_part in file) or (date_part and date_part in file):
                            return os.path.join(root, file)
    
    # If all fails, return None
    return None
