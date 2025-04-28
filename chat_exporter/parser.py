"""Parser for WhatsApp chat export files."""

import re
import os
import logging
from typing import List, Dict, Any, Optional, Tuple

from .models import Message, Media
from .media import extract_media_from_content, get_media_type

# Set up logging
logger = logging.getLogger(__name__)

def find_chat_file(extract_dir: str) -> str:
    """Find any WhatsApp chat text file in the extracted directory.
    
    Args:
        extract_dir: Directory containing the extracted WhatsApp export
        
    Returns:
        Path to the found chat file
        
    Raises:
        FileNotFoundError: If no chat file is found
    """
    txt_files = []
    
    # Look for all .txt files
    for root, _, files in os.walk(extract_dir):
        for file in files:
            if file.endswith('.txt') and not file.lower() == 'info.txt':
                txt_files.append(os.path.join(root, file))
    
    if not txt_files:
        raise FileNotFoundError("No text files found in the extracted directory")
    
    # If there's only one text file, use it
    if len(txt_files) == 1:
        logger.info(f"Found single chat file: {txt_files[0]}")
        return txt_files[0]
    
    # Score each file to determine which is most likely the chat file
    scored_files = []
    
    for file_path in txt_files:
        score = 0
        filename = os.path.basename(file_path)
        
        # Highest priority: Standard naming patterns
        if filename.endswith('_chat.txt'):
            score += 100
        elif 'chat' in filename.lower():
            score += 50
        
        # Check file size (larger files are more likely to be chat exports)
        score += min(os.path.getsize(file_path) / 1024, 50)  # Cap at 50 points
        
        # Peek at content to see if it looks like a chat
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            first_lines = [f.readline() for _ in range(min(10, os.path.getsize(file_path) // 50))]
            
            # Count lines that match typical WhatsApp timestamp patterns
            timestamp_pattern = r'^\[?(\d{1,2}/\d{1,2}/\d{2,4},\s\d{1,2}:\d{1,2})'
            matching_lines = sum(1 for line in first_lines if re.match(timestamp_pattern, line))
            
            # Score based on percentage of lines that match
            if first_lines:
                score += (matching_lines / len(first_lines)) * 40
        
        scored_files.append((file_path, score))
    
    # Sort by score descending
    scored_files.sort(key=lambda x: x[1], reverse=True)
    
    # Log all files and their scores
    for file_path, score in scored_files:
        logger.info(f"Chat file candidate: {file_path} (score: {score:.2f})")
    
    # Return the highest-scoring file
    logger.info(f"Selected chat file: {scored_files[0][0]}")
    return scored_files[0][0]

def find_info_file(extract_dir: str, custom_info_path: Optional[str] = None) -> Optional[str]:
    """Find the info.txt file using a hierarchy of locations.
    
    Args:
        extract_dir: Directory containing the extracted WhatsApp export
        custom_info_path: Optional path to a custom info.txt file
        
    Returns:
        Path to the found info file, or None if not found
    """
    # 1. Use custom path if provided
    if custom_info_path and os.path.exists(custom_info_path):
        logger.info(f"Using custom info file: {custom_info_path}")
        return custom_info_path
    
    # 2. Look in current working directory
    cwd_info = os.path.join(os.getcwd(), 'info.txt')
    if os.path.exists(cwd_info):
        logger.info(f"Using info file from current directory: {cwd_info}")
        return cwd_info
    
    # 3. Look in the extracted directory
    for root, _, files in os.walk(extract_dir):
        for file in files:
            if file.lower() == 'info.txt':
                info_path = os.path.join(root, file)
                logger.info(f"Found info file in extracted directory: {info_path}")
                return info_path
    
    # No info.txt found
    logger.info("No info.txt file found")
    return None

def detect_chat_format(lines: List[str]) -> Dict[str, Any]:
    """Detect the format of the chat export.
    
    Args:
        lines: First few lines of the chat file
        
    Returns:
        Dictionary with format information:
        {
            'type': 'desktop' or 'mobile',
            'timestamp_pattern': regex pattern for timestamps,
            'has_brackets': whether timestamps are in brackets,
            'separator': separator between timestamp and content (': ' or ' - '),
            'confidence': confidence score (0-1)
        }
    """
    # Initialize counters for different formats
    format_counts = {
        'desktop_bracketed': 0,  # [DD/MM/YYYY, HH:MM:SS] Sender: Message
        'desktop_unbracketed': 0,  # DD/MM/YYYY, HH:MM:SS Sender: Message
        'mobile': 0,  # DD/MM/YY, HH:MM - Sender: Message
    }
    
    # Look at the first few non-empty lines
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        # Check for desktop format with brackets
        if re.match(r'^\[\d{1,2}/\d{1,2}/\d{2,4},\s\d{1,2}:\d{1,2}(:\d{1,2})?\]\s', line):
            format_counts['desktop_bracketed'] += 1
        
        # Check for desktop format without brackets
        elif re.match(r'^\d{1,2}/\d{1,2}/\d{2,4},\s\d{1,2}:\d{1,2}(:\d{1,2})?\s', line) and ': ' in line:
            format_counts['desktop_unbracketed'] += 1
        
        # Check for mobile format
        elif re.match(r'^\d{1,2}/\d{1,2}/\d{2,4},\s\d{1,2}:\d{1,2}\s-\s', line):
            format_counts['mobile'] += 1
    
    # Determine the most likely format
    total_matches = sum(format_counts.values())
    if total_matches == 0:
        # Fallback to a generic pattern if no clear format is detected
        logger.warning("Could not detect chat format, using fallback pattern")
        return {
            'type': 'unknown',
            'timestamp_pattern': r'^\[?(\d{1,2}/\d{1,2}/\d{2,4},\s\d{1,2}:\d{1,2}(?::\d{1,2})?)\]?',
            'has_brackets': False,
            'separator': None,
            'confidence': 0.1
        }
    
    # Determine the dominant format
    dominant_format = max(format_counts, key=format_counts.get)
    confidence = format_counts[dominant_format] / total_matches
    
    logger.info(f"Detected chat format: {dominant_format} (confidence: {confidence:.2f})")
    
    if dominant_format == 'desktop_bracketed':
        return {
            'type': 'desktop',
            'timestamp_pattern': r'^\[(\d{1,2}/\d{1,2}/\d{2,4},\s\d{1,2}:\d{1,2}(?::\d{1,2})?)\]',
            'has_brackets': True,
            'separator': ': ',
            'confidence': confidence
        }
    elif dominant_format == 'desktop_unbracketed':
        return {
            'type': 'desktop',
            'timestamp_pattern': r'^(\d{1,2}/\d{1,2}/\d{2,4},\s\d{1,2}:\d{1,2}(?::\d{1,2})?)',
            'has_brackets': False,
            'separator': ': ',
            'confidence': confidence
        }
    else:  # mobile
        return {
            'type': 'mobile',
            'timestamp_pattern': r'^(\d{1,2}/\d{1,2}/\d{2,4},\s\d{1,2}:\d{1,2})',
            'has_brackets': False,
            'separator': ' - ',
            'confidence': confidence
        }

def parse_chat(chat_file_path: str) -> List[Message]:
    """Parse a WhatsApp chat file into Message objects.
    
    Args:
        chat_file_path: Path to the WhatsApp chat text file
        
    Returns:
        List of Message objects
    """
    with open(chat_file_path, 'r', encoding='utf-8', errors='ignore') as f:
        lines = f.readlines()
    
    logger.info(f"Parsing chat file with {len(lines)} lines")
    
    # Detect chat format from the first few non-empty lines
    non_empty_lines = [line for line in lines[:20] if line.strip()]
    format_info = detect_chat_format(non_empty_lines[:10])
    
    # Extract the regex pattern for timestamps based on detected format
    timestamp_pattern = format_info['timestamp_pattern']
    separator = format_info['separator']
    
    # Matches media attachments like <attached: 00000179-PHOTO-2025-04-24-16-21-11.jpg>
    # or VID-20230822-WA0001.mp4 (file attached)
    attachment_pattern_1 = r'<attached:\s+([^>]+)>'
    attachment_pattern_2 = r'([\w-]+\.(?:mp4|jpg|jpeg|png|gif|pdf|doc|docx|xls|xlsx|ppt|pptx))\s*\(file attached\)'
    
    # Matches "image omitted", "<Media omitted>", etc.
    omitted_pattern_1 = r'(?:image|video|audio|document|GIF)\s+omitted'
    omitted_pattern_2 = r'<Media omitted>'
    
    # Process the chat lines
    messages = []
    current_raw_message = None
    
    for line_num, line in enumerate(lines):
        line = line.strip()
        if not line:
            continue
        
        timestamp_match = re.match(timestamp_pattern, line)
        
        if timestamp_match:
            # If we found a timestamp, it's the start of a new message
            if current_raw_message:
                # Convert the raw message to a Message object
                messages.append(
                    Message.from_parsed_data(current_raw_message)
                )
            
            # Extract timestamp and message content
            timestamp_str = timestamp_match.group(1).strip()
            
            # Skip the separator and brackets based on detected format
            message_content = line[timestamp_match.end():].strip()
            
            # For desktop format, content typically starts with a colon after sender
            # For mobile format, content starts with a dash
            if format_info['type'] == 'mobile' and separator and message_content.startswith(separator):
                message_content = message_content[len(separator):].strip()
            elif format_info['type'] == 'desktop' and message_content.startswith(':'):
                message_content = message_content[1:].strip()
            
            # Extract media information from the content
            media_info = extract_media_from_content(message_content)
            
            # If media was found, clean up the content
            for media in media_info:
                if media['file']:
                    # Remove the media reference from the content
                    media_pattern = f"<attached:\\s+{re.escape(media['file'])}>"
                    message_content = re.sub(media_pattern, '', message_content).strip()
                    
                    # Also try to remove mobile format reference
                    media_pattern = f"{re.escape(media['file'])}\\s*\\(file attached\\)"
                    message_content = re.sub(media_pattern, '', message_content).strip()
            
            # Split the sender from the content
            parts = message_content.split(':', 1)
            sender = "System"
            content = message_content
            
            if len(parts) > 1:
                sender = parts[0].strip()
                content = parts[1].strip()
            else:
                # Special handling for system messages or edge cases
                if format_info['type'] == 'mobile':
                    # In mobile format, system messages often don't have a sender
                    if " added " in message_content or " left" in message_content:
                        sender = "System"
                        content = message_content
                    else:
                        # Try to detect if there's a hidden separator
                        potential_parts = message_content.split(' - ', 1)
                        if len(potential_parts) > 1:
                            sender = potential_parts[0].strip()
                            content = potential_parts[1].strip()
            
            # Create the new raw message dictionary
            current_raw_message = {
                'timestamp': timestamp_str,
                'sender': sender,
                'content': content,
                'media': media_info
            }
        elif current_raw_message:
            # This line is a continuation of the previous message or a media item
            attachment_match_1 = re.search(attachment_pattern_1, line)
            attachment_match_2 = re.search(attachment_pattern_2, line)
            omitted_match_1 = re.search(omitted_pattern_1, line)
            omitted_match_2 = re.search(omitted_pattern_2, line)
            
            if attachment_match_1:
                # Desktop format attachment
                media_file = attachment_match_1.group(1)
                media_type = get_media_type(media_file)
                
                current_raw_message['media'].append({
                    'type': media_type,
                    'file': media_file
                })
                logger.debug(f"Found desktop attachment in line {line_num+1}: {media_file}")
            elif attachment_match_2:
                # Mobile format attachment
                media_file = attachment_match_2.group(1)
                media_type = get_media_type(media_file)
                
                current_raw_message['media'].append({
                    'type': media_type,
                    'file': media_file
                })
                logger.debug(f"Found mobile attachment in line {line_num+1}: {media_file}")
            elif omitted_match_1 or omitted_match_2:
                # Media omitted indicator
                if omitted_match_1:
                    media_type = omitted_match_1.group(0).split()[0].lower()
                else:
                    media_type = 'media'  # Generic type for <Media omitted>
                
                current_raw_message['media'].append({
                    'type': media_type,
                    'file': None  # No file available
                })
            else:
                # Check if this line contains a file attached pattern before appending
                file_attached_match = re.search(attachment_pattern_2, line)
                if file_attached_match:
                    media_file = file_attached_match.group(1)
                    media_type = get_media_type(media_file)
                    
                    current_raw_message['media'].append({
                        'type': media_type,
                        'file': media_file
                    })
                    logger.debug(f"Found follow-up media in line {line_num+1}: {media_file}")
                else:
                    # Append to existing content
                    current_raw_message['content'] += "\n" + line
    
    # Don't forget to add the last message
    if current_raw_message:
        messages.append(
            Message.from_parsed_data(current_raw_message)
        )
    
    logger.info(f"Parsed {len(messages)} messages")
    
    return messages
