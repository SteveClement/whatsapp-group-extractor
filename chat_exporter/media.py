"""Media file handling for WhatsApp chat exports."""

import os
import re
import mimetypes
from datetime import datetime
from typing import Optional, List, Dict, Tuple

# Initialize mimetypes
mimetypes.init()

# Media type mapping by extension
MEDIA_TYPE_MAP = {
    # Images
    'jpg': 'photo', 'jpeg': 'photo', 'png': 'photo', 'gif': 'photo', 
    'webp': 'photo', 'heic': 'photo', 'heif': 'photo',
    
    # Videos
    'mp4': 'video', 'mov': 'video', 'avi': 'video', 'mkv': 'video', 
    'webm': 'video', '3gp': 'video', 'flv': 'video',
    
    # Audio
    'mp3': 'audio', 'wav': 'audio', 'ogg': 'audio', 'aac': 'audio',
    'm4a': 'audio', 'flac': 'audio', 'opus': 'audio',
    
    # Documents
    'pdf': 'document', 'doc': 'document', 'docx': 'document',
    'xls': 'document', 'xlsx': 'document', 'ppt': 'document',
    'pptx': 'document', 'txt': 'document', 'csv': 'document',
    'zip': 'document', 'rar': 'document', '7z': 'document',
    'vcf': 'document',  # Contact cards
    
    # WhatsApp specific
    'opus': 'voice_message',
    'ptt': 'voice_message'
}

def get_media_type(filename: str) -> str:
    """Determine the media type from a filename.
    
    Args:
        filename: Name of the media file
        
    Returns:
        Media type (photo, video, audio, document, etc.)
    """
    if not filename:
        return 'unknown'
    
    # Get the extension without the dot
    ext = os.path.splitext(filename)[1].lower().lstrip('.')
    
    # Check our mapping first
    if ext in MEDIA_TYPE_MAP:
        return MEDIA_TYPE_MAP[ext]
    
    # Fall back to mime type detection
    mime_type, _ = mimetypes.guess_type(filename)
    
    if mime_type:
        if mime_type.startswith('image/'):
            return 'photo'
        elif mime_type.startswith('video/'):
            return 'video'
        elif mime_type.startswith('audio/'):
            return 'audio'
        elif mime_type.startswith('text/'):
            return 'document'
        elif mime_type.startswith('application/'):
            return 'document'
    
    # Check filename patterns
    if re.match(r'^(IMG|image)-', filename, re.IGNORECASE):
        return 'photo'
    elif re.match(r'^(VID|video)-', filename, re.IGNORECASE):
        return 'video'
    elif re.match(r'^(AUD|audio)-', filename, re.IGNORECASE):
        return 'audio'
    elif re.match(r'^(DOC|document)-', filename, re.IGNORECASE):
        return 'document'
    elif 'PHOTO' in filename.upper():
        return 'photo'
    elif 'VIDEO' in filename.upper():
        return 'video'
    elif 'AUDIO' in filename.upper():
        return 'audio'
    elif 'VOICE' in filename.upper():
        return 'voice_message'
    
    # Default to unknown
    return 'unknown'

def find_media_file(directory: str, filename: str) -> Optional[str]:
    """Find a media file in the provided directory.
    
    Args:
        directory: Directory to search for the media file
        filename: Name of the media file to find
        
    Returns:
        Path to the found media file, or None if not found
    """
    # Guard against empty filename
    if not filename:
        return None
    
    # First check if the media file exists directly in the media folder
    media_path = os.path.join(directory, os.path.basename(filename))
    if os.path.exists(media_path):
        return media_path
    
    # If we don't find the direct match, try walking the directory
    for root, _, files in os.walk(directory):
        if os.path.basename(filename) in files:
            return os.path.join(root, os.path.basename(filename))
    
    # Extract key information from the filename
    base_name, extension = os.path.splitext(filename)
    extension = extension.lower()
    
    # Initialize pattern matchers
    pattern_matches: Dict[str, List[Tuple[str, float]]] = {
        'exact': [],
        'partial': [],
        'fuzzy': []
    }
    
    # Create different pattern match criteria
    
    # 1. Desktop format: 00000179-PHOTO-2024-04-24-16-21-11.jpg
    desktop_pattern = None
    if '-' in base_name:
        parts = base_name.split('-')
        if len(parts) >= 2:
            # Extract file ID and type
            file_id = parts[0]
            if file_id.isdigit():
                file_type = parts[1].lower() if len(parts) > 1 else ''
                
                # Create a pattern to match similar files
                desktop_pattern = f"{file_id}-{file_type}"
    
    # 2. Mobile format: IMG-20250425-WA0051.jpg
    mobile_pattern = None
    wa_part = None
    date_part = None
    
    if base_name.startswith(('IMG-', 'VID-', 'AUD-', 'DOC-')) and 'WA' in base_name:
        pattern_parts = base_name.split('-')
        
        # Extract key components
        prefix = pattern_parts[0] if pattern_parts else ''
        wa_part = next((part for part in pattern_parts if part.startswith('WA')), None)
        date_part = next((part for part in pattern_parts if len(part) == 8 and part.isdigit()), None)
        
        if wa_part or date_part:
            mobile_parts = []
            if prefix:
                mobile_parts.append(prefix)
            if date_part:
                mobile_parts.append(date_part)
            if wa_part:
                mobile_parts.append(wa_part)
            
            mobile_pattern = '-'.join(mobile_parts)
    
    # Scan for matching files
    for root, _, files in os.walk(directory):
        for file in files:
            file_path = os.path.join(root, file)
            file_base, file_ext = os.path.splitext(file)
            
            # Skip if the extension is completely different and not a media file
            if extension and file_ext.lower() != extension and not file_ext.lower() in MEDIA_TYPE_MAP:
                continue
            
            # Score the matches from most to least specific
            
            # 1. Exact filename match (without considering path)
            if file == filename:
                pattern_matches['exact'].append((file_path, 1.0))
                continue
            
            # 2. Exact basename match with different extension
            if file_base == base_name:
                pattern_matches['exact'].append((file_path, 0.9))
                continue
            
            # 3. Desktop pattern match
            if desktop_pattern and desktop_pattern in file:
                score = 0.8
                # Bonus for matching file extension
                if file_ext.lower() == extension:
                    score += 0.1
                pattern_matches['partial'].append((file_path, score))
                continue
            
            # 4. Mobile pattern match
            if mobile_pattern and all(part in file for part in mobile_pattern.split('-')):
                score = 0.7
                # Bonus for matching file extension
                if file_ext.lower() == extension:
                    score += 0.1
                pattern_matches['partial'].append((file_path, score))
                continue
            
            # 5. Individual component matches for mobile format
            if wa_part and wa_part in file:
                score = 0.5
                # Bonus for matching date part
                if date_part and date_part in file:
                    score += 0.2
                # Bonus for matching file extension
                if file_ext.lower() == extension:
                    score += 0.1
                pattern_matches['fuzzy'].append((file_path, score))
                continue
            
            # 6. Basename is contained in the filename
            if base_name in file:
                score = 0.4
                # Bonus for matching file extension
                if file_ext.lower() == extension:
                    score += 0.1
                pattern_matches['fuzzy'].append((file_path, score))
                continue
    
    # Return the best match, checking each category in order of specificity
    for category in ['exact', 'partial', 'fuzzy']:
        if pattern_matches[category]:
            # Sort by score descending
            best_matches = sorted(pattern_matches[category], key=lambda x: x[1], reverse=True)
            return best_matches[0][0]
    
    # If all fails, return None
    return None

def scan_media_directory(directory: str) -> Dict[str, List[str]]:
    """Scan the directory for media files and categorize them.
    
    Args:
        directory: Directory containing media files
        
    Returns:
        Dictionary mapping media types to lists of file paths
    """
    media_files: Dict[str, List[str]] = {
        'photo': [],
        'video': [],
        'audio': [],
        'voice_message': [],
        'document': [],
        'unknown': []
    }
    
    for root, _, files in os.walk(directory):
        for file in files:
            # Skip text files (likely chat or info files)
            if file.endswith('.txt'):
                continue
                
            file_path = os.path.join(root, file)
            media_type = get_media_type(file)
            
            if media_type in media_files:
                media_files[media_type].append(file_path)
            else:
                media_files['unknown'].append(file_path)
    
    return media_files

def extract_media_from_content(content: str) -> List[Dict[str, str]]:
    """Extract media references from message content.
    
    Args:
        content: Message content text
        
    Returns:
        List of media dictionaries with type and filename
    """
    media = []
    
    # Pattern for desktop format attachments
    desktop_pattern = r'<attached:\s+([^>]+)>'
    desktop_matches = re.findall(desktop_pattern, content)
    
    for filename in desktop_matches:
        media_type = get_media_type(filename)
        media.append({
            'type': media_type,
            'file': filename.strip()
        })
    
    # Pattern for mobile format attachments
    mobile_pattern = r'([\w\-\.]+\.(jpg|jpeg|png|gif|mp4|avi|mp3|pdf|doc))\s+\(file attached\)'
    mobile_matches = re.findall(mobile_pattern, content, re.IGNORECASE)
    
    for match in mobile_matches:
        filename = match[0]
        media_type = get_media_type(filename)
        media.append({
            'type': media_type,
            'file': filename
        })
    
    # Pattern for omitted media
    omitted_patterns = [
        r'(image|video|audio|document|media|GIF)\s+omitted',
        r'<Media omitted>'
    ]
    
    for pattern in omitted_patterns:
        omitted_matches = re.findall(pattern, content, re.IGNORECASE)
        for match in omitted_matches:
            # For <Media omitted>, match will be the whole string
            if match == '<Media omitted>':
                media_type = 'media'
            else:
                # Otherwise, it's the captured group
                media_type = match.lower()
            
            media.append({
                'type': media_type,
                'file': None
            })
    
    return media
