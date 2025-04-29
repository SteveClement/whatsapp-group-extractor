"""Main exporter functionality for WhatsApp chat exports."""

import os
import json
import shutil
import zipfile
import logging
import tempfile
import hashlib
import time
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple, Union

from .parser import find_chat_file, find_info_file, parse_chat
from .utils import extract_title_from_info
from .renderer import generate_html
from .models import Message, Chat, ChatMetadata

# Set up logging
logger = logging.getLogger(__name__)

def get_zip_info(zip_path: str) -> str:
    """Get formatted creation time of a zip file.
    
    Args:
        zip_path: Path to the zip file
        
    Returns:
        Formatted string with zip file creation time
    """
    try:
        # Get file modification time as a fallback
        file_mod_time = os.path.getmtime(zip_path)
        # Try to get file creation time if available
        try:
            # stat_result.st_birthtime works on macOS
            file_creation_time = os.stat(zip_path).st_birthtime
        except AttributeError:
            # Fallback to modification time on other systems
            file_creation_time = file_mod_time
        
        # Format the timestamp
        timestamp = datetime.fromtimestamp(file_creation_time)
        return timestamp.strftime("%d %B %Y at %H:%M")
    except Exception as e:
        logger.warning(f"Could not get zip file timestamp: {e}")
        # Return current time as fallback
        return datetime.now().strftime("%d %B %Y at %H:%M")

def extract_zip(zip_path: str) -> str:
    """Extract a WhatsApp export zip file to a temporary directory.
    
    Args:
        zip_path: Path to the WhatsApp export zip file
        
    Returns:
        Path to the extracted directory
        
    Raises:
        FileNotFoundError: If the zip file doesn't exist
        zipfile.BadZipFile: If the file is not a valid zip
    """
    if not os.path.exists(zip_path):
        raise FileNotFoundError(f"File not found: {zip_path}")
    
    # Create a temporary directory for extraction
    extract_dir = tempfile.mkdtemp(prefix="whatsapp_export_")
    
    logger.info(f"Extracting {zip_path} to {extract_dir}")
    
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_dir)
    except zipfile.BadZipFile:
        # Clean up the temp directory if extraction fails
        shutil.rmtree(extract_dir, ignore_errors=True)
        raise
    
    return extract_dir

def export_json(data: Union[List[Dict[str, Any]], Dict[str, Any]], output_file: str) -> None:
    """Export data to a JSON file.
    
    Args:
        data: Data to export (messages or chat object)
        output_file: Path to write the JSON output
    """
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    logger.info(f"Generated JSON file: {output_file}")

def create_chat(chat_file: str, info_file: Optional[str] = None) -> Chat:
    """Create a Chat object from a chat file and optional info file.
    
    Args:
        chat_file: Path to the chat file
        info_file: Optional path to the info file
        
    Returns:
        Chat object
    """
    # Parse the chat file
    messages = parse_chat(chat_file)
    
    # Read the info file if it exists
    info_text = None
    if info_file:
        try:
            with open(info_file, 'r', encoding='utf-8') as f:
                info_text = f.read()
        except (UnicodeDecodeError, IOError):
            logger.warning(f"Could not read info file: {info_file}")
    
    # Extract the chat title and description from info.txt
    chat_title = "WhatsApp Chat"
    chat_description = None
    
    if info_text:
        lines = info_text.splitlines()
        if lines and lines[0].startswith("Title:"):
            chat_title = lines[0][6:].strip()
            
            # Remaining lines form the description
            if len(lines) > 1:
                chat_description = "\n".join(lines[1:])
    
    # Create a chat ID based on the chat title
    chat_id = hashlib.md5(chat_title.encode()).hexdigest()
    
    # Create metadata
    metadata = ChatMetadata(
        chat_id=chat_id,
        title=chat_title,
        description=chat_description
    )
    
    # Create the chat and add all messages
    chat = Chat(metadata)
    chat.add_messages(messages)
    
    return chat

def check_for_updates(zip_path: str, output_dir: str, info_file_path: Optional[str] = None) -> Tuple[bool, Optional[Chat], Optional[Chat], Optional[str]]:
    """Check if the new export contains updates compared to existing data.
    
    Args:
        zip_path: Path to the new WhatsApp export zip file
        output_dir: Directory with existing export
        info_file_path: Optional path to a custom info.txt file
        
    Returns:
        Tuple of (has_updates, existing_chat, new_chat, extract_dir)
    """
    # Check if there's an existing export
    full_data_path = os.path.join(output_dir, "chat_data.json")
    
    if not os.path.exists(full_data_path):
        logger.info("No existing export found, will create new export")
        return False, None, None, None
    
    # Load the existing chat data
    try:
        existing_chat = Chat.load_from_file(full_data_path)
        if not existing_chat:
            logger.warning("Existing chat data is invalid, will create new export")
            return False, None, None, None
    except Exception as e:
        logger.error(f"Error loading existing chat data: {e}")
        return False, None, None, None
    
    # Extract the new export
    extract_dir = extract_zip(zip_path)
    
    try:
        # Find the chat file and info file
        chat_file = find_chat_file(extract_dir)
        info_file = find_info_file(extract_dir, info_file_path)
        
        # Create a Chat object from the new export
        new_chat = create_chat(chat_file, info_file)
        
        # Check if there are new messages
        existing_ids = existing_chat.metadata.message_ids
        new_ids = new_chat.metadata.message_ids
        
        # Find IDs that are in the new chat but not in the existing one
        new_message_ids = new_ids - existing_ids
        
        has_updates = len(new_message_ids) > 0
        logger.info(f"Update check: found {len(new_message_ids)} new messages")
        
        return has_updates, existing_chat, new_chat, extract_dir
    
    except Exception as e:
        logger.error(f"Error checking for updates: {e}")
        # In case of error, clean up the extraction directory
        shutil.rmtree(extract_dir, ignore_errors=True)
        return False, None, None, None

def process_export(zip_path: str, output_dir: str, info_file_path: Optional[str] = None) -> Tuple[str, str, str]:
    """Process a WhatsApp export zip file.
    
    Args:
        zip_path: Path to the WhatsApp export zip file
        output_dir: Directory to write the HTML and JSON output
        info_file_path: Optional path to a custom info.txt file
        
    Returns:
        Tuple of (HTML output path, JSON output path, metadata output path)
        
    Raises:
        FileNotFoundError: If the zip file or chat file isn't found
        ValueError: If the chat parsing fails
    """
    # Create the output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Define output file paths
    html_output = os.path.join(output_dir, "whatsapp_chat.html")
    json_output = os.path.join(output_dir, "whatsapp_chat.json")
    metadata_output = os.path.join(output_dir, "metadata.json")
    full_output = os.path.join(output_dir, "chat_data.json")
    
    # Extract the zip file
    extract_dir = extract_zip(zip_path)
    
    try:
        # Find the chat file
        chat_file = find_chat_file(extract_dir)
        
        # Find the info file
        info_file = find_info_file(extract_dir, info_file_path)
        
        # Create a Chat object
        chat = create_chat(chat_file, info_file)
        
        # Generate HTML from the messages
        message_dicts = [message.to_dict() for message in chat.messages]
        
        # We need to read the info text again for the HTML generation
        info_text = None
        if info_file:
            try:
                with open(info_file, 'r', encoding='utf-8') as f:
                    info_text = f.read()
            except (UnicodeDecodeError, IOError):
                logger.warning(f"Could not read info file for HTML generation: {info_file}")
        
        # Get the zip file timestamp
        zip_timestamp = get_zip_info(zip_path)
        
        # Generate HTML
        generate_html(message_dicts, extract_dir, html_output, info_text, chat.metadata.title, zip_timestamp=zip_timestamp)
        
        # Export the messages in the original format for backward compatibility
        export_json(message_dicts, json_output)
        
        # Export metadata separately
        export_json(chat.metadata.to_dict(), metadata_output)
        
        # Export the full chat data (including messages and metadata)
        try:
            export_json(chat.to_dict(), full_output)
        except Exception as e:
            logger.error(f"Error exporting full chat data: {e}")
            # This is not a critical error, we can continue
        
        return html_output, json_output, metadata_output
    
    finally:
        # We're not cleaning up the extracted directory so the HTML can reference media files
        pass

def process_update(zip_path: str, output_dir: str, info_file_path: Optional[str] = None, 
                  highlight_level: str = 'subtle') -> Tuple[str, str, str, int]:
    """Process an update to an existing export.
    
    Args:
        zip_path: Path to the new WhatsApp export zip file
        output_dir: Directory with existing export
        info_file_path: Optional path to a custom info.txt file
        highlight_level: How to highlight new messages (none, subtle, prominent)
        
    Returns:
        Tuple of (HTML output path, JSON output path, metadata output path, count of new messages)
        
    Raises:
        FileNotFoundError: If the zip file or chat file isn't found
        ValueError: If the chat parsing fails
    """
    try:
        # Check for updates
        has_updates, existing_chat, new_chat, extract_dir = check_for_updates(zip_path, output_dir, info_file_path)
        
        if not has_updates or not existing_chat or not new_chat or not extract_dir:
            # If there's no existing export or no updates, process as a new export
            html_output, json_output, metadata_output = process_export(zip_path, output_dir, info_file_path)
            logger.info("Created new export (no existing export or no updates)")
            # Return 4 values as required by the function signature
            return html_output, json_output, metadata_output, 0
        
        # We have updates - merge the chats
        logger.info(f"Using already extracted directory: {extract_dir}")
        
        # Find all messages in the new chat that aren't in the existing chat
        existing_ids = existing_chat.metadata.message_ids
        new_messages = [msg for msg in new_chat.messages if msg.id not in existing_ids]
        
        # Add the new messages to the existing chat
        new_message_count = existing_chat.add_messages(new_messages, is_update=True)
        
        logger.info(f"Added {new_message_count} new messages from update")
        
        # Mark the new messages
        for msg in existing_chat.messages:
            msg.is_new = msg.id not in existing_ids
        
        # Define output file paths
        html_output = os.path.join(output_dir, "whatsapp_chat.html")
        json_output = os.path.join(output_dir, "whatsapp_chat.json")
        metadata_output = os.path.join(output_dir, "metadata.json")
        full_output = os.path.join(output_dir, "chat_data.json")
        
        # We need to read the info file again for the HTML generation
        info_file = find_info_file(extract_dir, info_file_path)
        info_text = None
        if info_file:
            try:
                with open(info_file, 'r', encoding='utf-8') as f:
                    info_text = f.read()
            except (UnicodeDecodeError, IOError):
                logger.warning(f"Could not read info file for HTML generation: {info_file}")
        
        # Get zip file creation timestamp
        zip_timestamp = get_zip_info(zip_path)
        
        # Generate HTML with new messages highlighted
        message_dicts = [message.to_dict() for message in existing_chat.messages]
        generate_html(
            message_dicts, 
            extract_dir, 
            html_output, 
            info_text, 
            existing_chat.metadata.title,
            highlight_new=highlight_level,
            zip_timestamp=zip_timestamp
        )
        
        # Export the messages in the original format for backward compatibility
        export_json(message_dicts, json_output)
        
        # Export metadata separately
        export_json(existing_chat.metadata.to_dict(), metadata_output)
        
        # Export the full chat data (including messages and metadata)
        try:
            export_json(existing_chat.to_dict(), full_output)
        except Exception as e:
            logger.error(f"Error exporting full chat data: {e}")
            # This is not a critical error, we can continue
        
        return html_output, json_output, metadata_output, new_message_count
        
    except Exception as e:
        logger.error(f"Error in process_update: {e}")
        # In case of any error, fall back to process_export
        try:
            # Get zip file timestamp for the fallback export
            zip_timestamp = get_zip_info(zip_path)
            html_output, json_output, metadata_output = process_export(zip_path, output_dir, info_file_path)
            logger.info("Fallback to new export due to update error")
            
            # After creating a new export, if highlight level was specified,
            # try to update the HTML with the timestamp message
            if highlight_level != 'none':
                try:
                    with open(html_output, 'r', encoding='utf-8') as f:
                        html_content = f.read()
                    
                    # Insert the update timestamp before the closing </div> of chat-container
                    update_message = f"""        <div class="update-message">
            Export created on {zip_timestamp}.
        </div>
"""
                    html_content = html_content.replace('        </div>\n    </div>', f'        </div>\n{update_message}    </div>')
                    
                    with open(html_output, 'w', encoding='utf-8') as f:
                        f.write(html_content)
                except Exception as e:
                    logger.warning(f"Could not add timestamp to fallback HTML: {e}")
            
            return html_output, json_output, metadata_output, 0
        except Exception as fallback_e:
            logger.error(f"Even fallback failed: {fallback_e}")
            # Define default output paths for error case
            html_output = os.path.join(output_dir, "whatsapp_chat.html")
            json_output = os.path.join(output_dir, "whatsapp_chat.json")
            metadata_output = os.path.join(output_dir, "metadata.json")
            return html_output, json_output, metadata_output, 0
