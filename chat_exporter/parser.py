"""Parser for WhatsApp chat export files."""

import re
import os
from typing import List, Dict, Any, Optional

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
    
    # First priority: _chat.txt (standard desktop export)
    for file_path in txt_files:
        if os.path.basename(file_path).endswith('_chat.txt'):
            return file_path
    
    # Second priority: Use the first text file that's not info.txt
    for file_path in txt_files:
        if os.path.basename(file_path).lower() != 'info.txt':
            return file_path
    
    # This should not happen given the earlier check, but just in case
    raise FileNotFoundError("Could not find any suitable chat file in the extracted directory")

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
        return custom_info_path
    
    # 2. Look in current working directory
    cwd_info = os.path.join(os.getcwd(), 'info.txt')
    if os.path.exists(cwd_info):
        return cwd_info
    
    # 3. Look in the extracted directory
    for root, _, files in os.walk(extract_dir):
        for file in files:
            if file.lower() == 'info.txt':
                return os.path.join(root, file)
    
    # No info.txt found
    return None

def parse_chat(chat_file_path: str) -> List[Dict[str, Any]]:
    """Parse a WhatsApp chat file into a structured format.
    
    Args:
        chat_file_path: Path to the WhatsApp chat text file
        
    Returns:
        List of message dictionaries
    """
    with open(chat_file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    print(f"Parsing chat file with {len(lines)} lines")
    
    # Regular expressions for parsing different WhatsApp export formats
    
    # Format 1: Desktop export with brackets [DD/MM/YYYY, HH:MM:SS]
    # Format 2: Mobile export with no brackets DD/MM/YY, HH:MM
    timestamp_pattern = r'^\[?(\d{1,2}/\d{1,2}/\d{2,4},\s\d{1,2}:\d{1,2}(?::\d{1,2})?)\]?'
    
    # Matches media attachments like <attached: 00000179-PHOTO-2025-04-24-16-21-11.jpg>
    # or VID-20230822-WA0001.mp4 (file attached)
    attachment_pattern_1 = r'<attached:\s(\d+-\w+-\d{4}-\d{2}-\d{2}-\d{2}-\d{2}-\d{2}\.\w+)>'
    attachment_pattern_2 = r'([\w-]+\.(?:mp4|jpg|jpeg|png|gif|pdf|doc|docx|xls|xlsx|ppt|pptx))\s*\(file attached\)'
    
    # Matches "image omitted", "<Media omitted>", etc.
    omitted_pattern_1 = r'(?:image|video|audio|document|GIF)\s+omitted'
    omitted_pattern_2 = r'<Media omitted>'
    
    messages = []
    current_message = None
    
    for line_num, line in enumerate(lines):
        line = line.strip()
        if not line:
            continue
        
        timestamp_match = re.match(timestamp_pattern, line)
        
        if timestamp_match:
            # If we found a timestamp, it's the start of a new message
            if current_message:
                messages.append(current_message)
            
            # Extract timestamp and message content
            timestamp_str = timestamp_match.group(1)
            
            # Remove brackets if present
            if timestamp_str.startswith('['):
                timestamp_str = timestamp_str[1:]
            if timestamp_str.endswith(']'):
                timestamp_str = timestamp_str[:-1]
                
            message_content = line[timestamp_match.end():].strip()
            
            # For desktop format, content starts with a colon
            # For mobile format, it starts with a dash
            if message_content.startswith(' - '):
                message_content = message_content[3:]
            elif message_content.startswith(':'):
                message_content = message_content[1:].strip()
            
            # Check for media file directly in message content (mobile format)
            file_attached_match = re.search(attachment_pattern_2, message_content)
            media_info = []
            
            if file_attached_match:
                media_file = file_attached_match.group(1)
                # Determine type from extension
                extension = media_file.split('.')[-1].lower()
                if extension in ['jpg', 'jpeg', 'png', 'gif']:
                    media_type = 'photo'
                elif extension in ['mp4', 'mov', 'avi']:
                    media_type = 'video'
                elif extension in ['mp3', 'wav', 'ogg']:
                    media_type = 'audio'
                else:
                    media_type = 'document'
                
                media_info.append({
                    'type': media_type,
                    'file': media_file
                })
                
                # Remove the file attachment text from content
                message_content = message_content.replace(file_attached_match.group(0), '').strip()
                print(f"Found mobile media in line {line_num+1}: {media_file} of type {media_type}")
            
            # Split the sender from the content
            parts = message_content.split(':', 1)
            if len(parts) > 1:
                sender = parts[0].strip()
                content = parts[1].strip()
            else:
                # This might be a system message or a sender without a message
                if ": " in line and not message_content:
                    # This is a case where the timestamp regex consumed part of the sender
                    # Attempt to reconstruct the original line
                    parts = line.split(": ", 1)
                    if len(parts) > 1:
                        sender = parts[0].replace(timestamp_str, '').strip()
                        if sender.startswith(' - '):
                            sender = sender[3:]
                        content = parts[1].strip()
                    else:
                        sender = "System"
                        content = message_content
                else:
                    sender = "System"
                    content = message_content
            
            current_message = {
                'timestamp': timestamp_str,
                'sender': sender,
                'content': content,
                'media': media_info
            }
        elif current_message:
            # This line is a continuation of the previous message or a media item
            attachment_match_1 = re.search(attachment_pattern_1, line)
            attachment_match_2 = re.search(attachment_pattern_2, line)
            omitted_match_1 = re.search(omitted_pattern_1, line)
            omitted_match_2 = re.search(omitted_pattern_2, line)
            
            if attachment_match_1:
                media_file = attachment_match_1.group(1)
                media_type = media_file.split('-')[1].lower()
                current_message['media'].append({
                    'type': media_type,
                    'file': media_file
                })
                print(f"Found desktop attachment in line {line_num+1}: {media_file}")
            elif attachment_match_2:
                media_file = attachment_match_2.group(1)
                # Determine type from extension
                extension = media_file.split('.')[-1].lower()
                if extension in ['jpg', 'jpeg', 'png', 'gif']:
                    media_type = 'photo'
                elif extension in ['mp4', 'mov', 'avi']:
                    media_type = 'video'
                elif extension in ['mp3', 'wav', 'ogg']:
                    media_type = 'audio'
                else:
                    media_type = 'document'
                
                current_message['media'].append({
                    'type': media_type,
                    'file': media_file
                })
                print(f"Found mobile attachment in line {line_num+1}: {media_file}")
            elif omitted_match_1 or omitted_match_2:
                # Determine media type
                if omitted_match_1:
                    media_type = omitted_match_1.group(0).split()[0].lower()
                else:
                    media_type = 'media'  # Generic type for <Media omitted>
                
                current_message['media'].append({
                    'type': media_type,
                    'file': None  # No file available
                })
            else:
                # Before appending, check if this line contains a file attached pattern
                file_attached_match = re.search(attachment_pattern_2, line)
                if file_attached_match:
                    media_file = file_attached_match.group(1)
                    # Determine type from extension
                    extension = media_file.split('.')[-1].lower()
                    if extension in ['jpg', 'jpeg', 'png', 'gif']:
                        media_type = 'photo'
                    elif extension in ['mp4', 'mov', 'avi']:
                        media_type = 'video'
                    elif extension in ['mp3', 'wav', 'ogg']:
                        media_type = 'audio'
                    else:
                        media_type = 'document'
                    
                    current_message['media'].append({
                        'type': media_type,
                        'file': media_file
                    })
                    print(f"Found follow-up mobile media in line {line_num+1}: {media_file}")
                else:
                    # Append to existing content
                    current_message['content'] += " " + line
    
    # Don't forget to add the last message
    if current_message:
        messages.append(current_message)
    
    print(f"Parsed {len(messages)} messages")
    
    # Final scan for media files in content
    for i, message in enumerate(messages):
        if '(file attached)' in message['content']:
            print(f"Message {i} may contain undetected media: {message['content']}")
            file_attached_match = re.search(r'([\w-]+\.(?:mp4|jpg|jpeg|png|gif|pdf|doc|docx|xls|xlsx|ppt|pptx))\s*\(file attached\)', message['content'])
            if file_attached_match:
                media_file = file_attached_match.group(1)
                # Determine type from extension
                extension = media_file.split('.')[-1].lower()
                if extension in ['jpg', 'jpeg', 'png', 'gif']:
                    media_type = 'photo'
                elif extension in ['mp4', 'mov', 'avi']:
                    media_type = 'video'
                elif extension in ['mp3', 'wav', 'ogg']:
                    media_type = 'audio'
                else:
                    media_type = 'document'
                
                message['media'].append({
                    'type': media_type,
                    'file': media_file
                })
                
                # Remove the file attachment text from content
                message['content'] = message['content'].replace(file_attached_match.group(0), '').strip()
                print(f"Added missing media to message {i}: {media_file}")
    
    return messages
