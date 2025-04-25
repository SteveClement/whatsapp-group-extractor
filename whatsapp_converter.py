import os
import re
import zipfile
import html
import shutil
from datetime import datetime
from pathlib import Path

def extract_zip(zip_path, extract_dir):
    """Extract the WhatsApp export zip file to the specified directory."""
    os.makedirs(extract_dir, exist_ok=True)
    
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(extract_dir)
    
    print(f"Extracted zip file to {extract_dir}")

def find_chat_file(extract_dir):
    """Find the WhatsApp chat text file in the extract directory."""
    # Look for a file named _chat.txt or similar
    for root, _, files in os.walk(extract_dir):
        for file in files:
            if file.endswith('_chat.txt'):
                return os.path.join(root, file)
    
    raise FileNotFoundError("Could not find _chat.txt file in the extracted directory")

def parse_chat(chat_file_path):
    """Parse the WhatsApp chat file and return structured data."""
    with open(chat_file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Regular expressions for parsing
    # Matches timestamps like [16/04/2024, 11:59:24]
    timestamp_pattern = r'^\[(\d{2}/\d{2}/\d{4}, \d{2}:\d{2}:\d{2})\]'
    # Matches media attachments like <attached: 00000179-PHOTO-2024-04-24-16-21-11.jpg>
    attachment_pattern = r'<attached: (\d+-\w+-\d{4}-\d{2}-\d{2}-\d{2}-\d{2}-\d{2}\.\w+)>'
    # Matches "image omitted" or "video omitted" placeholders
    omitted_pattern = r'(image|video|audio|document|GIF) omitted'
    
    messages = []
    current_message = None
    
    for line in lines:
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
            message_content = line[timestamp_match.end():].strip()
            
            # Split the sender from the content
            parts = message_content.split(':', 1)
            if len(parts) > 1:
                sender = parts[0].strip()
                content = parts[1].strip()
            else:
                # This might be a system message with no sender
                sender = "System"
                content = message_content
            
            current_message = {
                'timestamp': timestamp_str,
                'sender': sender,
                'content': content,
                'media': []
            }
        elif current_message:
            # This line is a continuation of the previous message or a media item
            attachment_match = re.search(attachment_pattern, line)
            omitted_match = re.search(omitted_pattern, line)
            
            if attachment_match:
                media_file = attachment_match.group(1)
                current_message['media'].append({
                    'type': media_file.split('-')[1].lower(),
                    'file': media_file
                })
            elif omitted_match:
                media_type = omitted_match.group(1).lower()
                current_message['media'].append({
                    'type': media_type,
                    'file': None  # No file available
                })
            else:
                # Append to existing content
                current_message['content'] += " " + line
    
    # Don't forget to add the last message
    if current_message:
        messages.append(current_message)
    
    return messages

def generate_html(messages, extract_dir, output_file):
    """Generate a nice HTML page from the parsed messages."""
    # Create CSS styles
    css = """
    * {
        box-sizing: border-box;
        margin: 0;
        padding: 0;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    
    body {
        background-color: #f0f0f0;
        padding: 20px;
    }
    
    .chat-container {
        max-width: 800px;
        margin: 0 auto;
        background-color: #fff;
        border-radius: 10px;
        overflow: hidden;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
    }
    
    .chat-header {
        background-color: #128C7E;
        color: white;
        padding: 15px;
        text-align: center;
    }
    
    .chat-messages {
        padding: 15px;
        overflow-y: auto;
        display: flex;
        flex-direction: column;
        gap: 10px;
    }
    
    .message {
        padding: 8px 12px;
        border-radius: 7.5px;
        position: relative;
        max-width: 75%;
        word-wrap: break-word;
    }
    
    .message.user {
        align-self: flex-end;
        background-color: #DCF8C6;
    }
    
    .message.other {
        align-self: flex-start;
        background-color: #FFFFFF;
        border: 1px solid #E2E2E2;
    }
    
    .message.system {
        align-self: center;
        background-color: #f1f1f1;
        color: #666;
        font-style: italic;
        max-width: 90%;
        text-align: center;
    }
    
    .message-sender {
        font-weight: bold;
        margin-bottom: 3px;
        color: #128C7E;
    }
    
    .message-time {
        color: #999;
        font-size: 0.7em;
        margin-top: 5px;
        text-align: right;
    }
    
    .message-content {
        margin-bottom: 5px;
    }
    
    .media-container {
        margin-top: 5px;
        margin-bottom: 5px;
    }
    
    .media-image {
        max-width: 100%;
        max-height: 300px;
        border-radius: 5px;
    }
    
    .media-video {
        max-width: 100%;
        max-height: 300px;
        border-radius: 5px;
    }
    
    .media-placeholder {
        padding: 10px;
        background-color: #f1f1f1;
        border-radius: 5px;
        color: #555;
        font-style: italic;
    }
    
    a {
        color: #128C7E;
        text-decoration: none;
    }
    
    a:hover {
        text-decoration: underline;
    }

    .date-separator {
        text-align: center;
        margin: 15px 0;
        color: #666;
        font-size: 0.8em;
        position: relative;
    }
    
    .date-separator:before, .date-separator:after {
        content: "";
        display: inline-block;
        height: 1px;
        background-color: #e0e0e0;
        width: 35%;
        vertical-align: middle;
        margin: 0 10px;
    }
    """
    
    # Start building the HTML content
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>WhatsApp Chat Export</title>
    <style>{css}</style>
</head>
<body>
    <div class="chat-container">
        <div class="chat-header">
            <h1>WhatsApp Chat</h1>
        </div>
        <div class="chat-messages">
"""

    current_date = None
    
    for message in messages:
        # Parse and format the timestamp
        timestamp = datetime.strptime(message['timestamp'], '%d/%m/%Y, %H:%M:%S')
        message_date = timestamp.strftime('%d %B %Y')
        message_time = timestamp.strftime('%H:%M')
        
        # Add date separator if it's a new day
        if message_date != current_date:
            html_content += f'            <div class="date-separator">{message_date}</div>\n'
            current_date = message_date
        
        sender = message['sender']
        
        # Determine the message type
        message_type = "system"
        if "~" in sender:
            if "added" in message['content'] or "joined using this group's invite link" in message['content'] or "left" in message['content'] or "changed" in message['content']:
                message_type = "system"
            else:
                message_type = "other"  # Group message from someone else
        elif sender != "System":
            message_type = "user"  # Assume messages without "~" are from the user
        
        # Create the message HTML
        html_content += f'            <div class="message {message_type}">\n'
        
        # Add sender if it's not a system message
        if message_type != "system":
            html_content += f'                <div class="message-sender">{html.escape(sender)}</div>\n'
        
        # Add message content if there is any
        content = message['content']
        if content:
            # Convert URLs to links
            url_pattern = r'(https?://[^\s]+)'
            content = re.sub(url_pattern, r'<a href="\1" target="_blank">\1</a>', content)
            
            html_content += f'                <div class="message-content">{html.escape(content)}</div>\n'
        
        # Add media files if there are any
        if message['media']:
            for media in message['media']:
                html_content += '                <div class="media-container">\n'
                
                if media['file']:
                    media_path = find_media_file(extract_dir, media['file'])
                    if media_path:
                        # Get the relative path from output file to media file
                        rel_path = os.path.relpath(
                            media_path, 
                            os.path.dirname(output_file)
                        )
                        
                        if media['type'] == 'photo':
                            html_content += f'                    <img class="media-image" src="{rel_path}" alt="Image">\n'
                        elif media['type'] == 'video':
                            html_content += f"""                    <video class="media-video" controls>
                        <source src="{rel_path}" type="video/mp4">
                        Your browser does not support video playback.
                    </video>\n"""
                        elif media['type'] == 'audio':
                            html_content += f"""                    <audio controls>
                        <source src="{rel_path}" type="audio/mpeg">
                        Your browser does not support audio playback.
                    </audio>\n"""
                        else:
                            html_content += f'                    <div class="media-placeholder">{media["type"]} file: <a href="{rel_path}" target="_blank">Open {media["file"]}</a></div>\n'
                    else:
                        html_content += f'                    <div class="media-placeholder">{media["type"]} file not found: {media["file"]}</div>\n'
                else:
                    html_content += f'                    <div class="media-placeholder">{media["type"]} file not available</div>\n'
                
                html_content += '                </div>\n'
        
        # Add message time
        html_content += f'                <div class="message-time">{message_time}</div>\n'
        html_content += '            </div>\n'
    
    # Close the HTML document
    html_content += """        </div>
    </div>
</body>
</html>"""
    
    # Write the HTML content to the output file
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"Generated HTML file: {output_file}")

def find_media_file(extract_dir, filename):
    """Find a media file in the extract directory."""
    for root, _, files in os.walk(extract_dir):
        if filename in files:
            return os.path.join(root, filename)
    
    # Try alternative approaches - some WhatsApp exports use different naming patterns
    file_id, file_type, *date_parts = filename.split('-')
    
    # Try matching just by the file ID and type
    for root, _, files in os.walk(extract_dir):
        for file in files:
            if file.startswith(file_id) and file_type.lower() in file.lower():
                return os.path.join(root, file)
    
    return None

def main():
    # Get input from user
    zip_path = input("Enter path to WhatsApp export zip file: ")
    
    # Define paths
    script_dir = os.path.dirname(os.path.abspath(__file__))
    extract_dir = os.path.join(script_dir, "html")
    output_file = os.path.join(extract_dir, "whatsapp_chat.html")
    
    # Clean any existing extract directory
    if os.path.exists(extract_dir):
        shutil.rmtree(extract_dir)
    
    # Process the export
    try:
        extract_zip(zip_path, extract_dir)
        chat_file = find_chat_file(extract_dir)
        messages = parse_chat(chat_file)
        generate_html(messages, extract_dir, output_file)
        
        print("\nProcessing complete!")
        print(f"Open {output_file} in your web browser to view the chat.")
    
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
