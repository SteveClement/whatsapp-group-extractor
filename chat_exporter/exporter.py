"""Main exporter functionality for WhatsApp chat exports."""

import os
import json
import shutil
import zipfile
import tempfile
from typing import Dict, Any, List, Optional, Tuple

from .parser import find_chat_file, find_info_file, parse_chat
from .utils import extract_title_from_info
from .renderer import generate_html

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
    
    print(f"Extracting {zip_path} to {extract_dir}")
    
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_dir)
    except zipfile.BadZipFile:
        # Clean up the temp directory if extraction fails
        shutil.rmtree(extract_dir, ignore_errors=True)
        raise
    
    return extract_dir

def export_json(messages: List[Dict[str, Any]], output_file: str) -> None:
    """Export messages to a JSON file.
    
    Args:
        messages: List of parsed message dictionaries
        output_file: Path to write the JSON output
    """
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(messages, f, indent=2, ensure_ascii=False)
    
    print(f"Generated JSON file: {output_file}")

def process_export(zip_path: str, output_dir: str, info_file_path: Optional[str] = None) -> Tuple[str, str]:
    """Process a WhatsApp export zip file.
    
    Args:
        zip_path: Path to the WhatsApp export zip file
        output_dir: Directory to write the HTML and JSON output
        info_file_path: Optional path to a custom info.txt file
        
    Returns:
        Tuple of (HTML output path, JSON output path)
        
    Raises:
        FileNotFoundError: If the zip file or chat file isn't found
        ValueError: If the chat parsing fails
    """
    # Create the output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Extract the zip file
    extract_dir = extract_zip(zip_path)
    
    try:
        # Find the chat file
        chat_file = find_chat_file(extract_dir)
        
        # Find the info file
        info_file = find_info_file(extract_dir, info_file_path)
        
        # Read the info file if it exists
        info_text = None
        if info_file:
            with open(info_file, 'r', encoding='utf-8') as f:
                info_text = f.read()
        
        # Extract the chat title from info.txt or use default
        chat_title = extract_title_from_info(info_text) if info_text else "WhatsApp Chat"
        
        # Parse the chat file
        messages = parse_chat(chat_file)
        
        # Define output file paths
        html_output = os.path.join(output_dir, "whatsapp_chat.html")
        json_output = os.path.join(output_dir, "whatsapp_chat.json")
        
        # Generate HTML
        generate_html(messages, extract_dir, html_output, info_text, chat_title)
        
        # Export JSON
        export_json(messages, json_output)
        
        # Copy media files
        # Note: We don't need to copy media files since generate_html already
        # creates references to their original location in the extracted directory
        
        return html_output, json_output
    
    finally:
        # Clean up: In a real implementation, you might want to keep the extracted
        # files around so the HTML can reference them. For simplicity in this example,
        # we're not removing them.
        # shutil.rmtree(extract_dir, ignore_errors=True)
        pass
