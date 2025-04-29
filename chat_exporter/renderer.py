"""HTML rendering for WhatsApp chat exports."""

import html
import re
import os
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional

from .media import find_media_file
from .utils import parse_timestamp

def generate_css() -> str:
    """Generate CSS styles for the HTML output.
    
    Returns:
        CSS styles as a string
    """
    return """
    :root {
        --bg-color: #f0f0f0;
        --container-bg: #fff;
        --header-bg: #128C7E;
        --header-color: white;
        --message-user-bg: #DCF8C6;
        --message-other-bg: #FFFFFF;
        --message-other-border: #E2E2E2;
        --message-system-bg: #f1f1f1;
        --message-system-color: #666;
        --sender-color: #128C7E;
        --time-color: #999;
        --placeholder-bg: #f1f1f1;
        --placeholder-color: #555;
        --link-color: #128C7E;
        --date-color: #666;
        --date-line-color: #e0e0e0;
        --text-color: #000;
        --container-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
        --new-message-subtle: rgba(255, 193, 7, 0.25);
        --new-message-prominent: rgba(255, 193, 7, 0.5);
        --new-message-border: rgba(255, 130, 0, 0.7);
        --new-message-indicator: #FFC107;
    }
    
    [data-theme="dark"] {
        --bg-color: #121212;
        --container-bg: #1e1e1e;
        --header-bg: #075E54;
        --header-color: white;
        --message-user-bg: #056162;
        --message-other-bg: #2a2a2a;
        --message-other-border: #333;
        --message-system-bg: #2a2a2a;
        --message-system-color: #aaa;
        --sender-color: #25D366;
        --time-color: #808080;
        --placeholder-bg: #2a2a2a;
        --placeholder-color: #aaa;
        --link-color: #25D366;
        --date-color: #aaa;
        --date-line-color: #333;
        --text-color: #e0e0e0;
        --container-shadow: 0 1px 3px rgba(0, 0, 0, 0.3);
        --new-message-subtle: rgba(255, 193, 7, 0.2);
        --new-message-prominent: rgba(255, 193, 7, 0.35);
        --new-message-border: rgba(255, 152, 0, 0.6);
        --new-message-indicator: #FFC107;
    }
    
    * {
        box-sizing: border-box;
        margin: 0;
        padding: 0;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    
    body {
        background-color: var(--bg-color);
        padding: 20px;
        color: var(--text-color);
        transition: background-color 0.3s ease;
    }
    
    .chat-container {
        max-width: 800px;
        margin: 0 auto;
        background-color: var(--container-bg);
        border-radius: 10px;
        overflow: hidden;
        box-shadow: var(--container-shadow);
        transition: background-color 0.3s ease, box-shadow 0.3s ease;
    }
    
    .chat-header {
        background-color: var(--header-bg);
        color: var(--header-color);
        padding: 15px;
        text-align: center;
        display: flex;
        justify-content: space-between;
        align-items: center;
        transition: background-color 0.3s ease;
    }
    
    .chat-title {
        display: flex;
        align-items: center;
        gap: 10px;
    }
    
    .json-link, .info-button {
        font-size: 0.8em;
        color: rgba(255, 255, 255, 0.8);
        text-decoration: none;
        display: inline-flex;
        align-items: center;
        padding: 3px 8px;
        background: rgba(255, 255, 255, 0.2);
        border-radius: 4px;
        transition: background-color 0.2s;
        position: relative;
    }
    
    .json-link:hover, .info-button:hover {
        background: rgba(255, 255, 255, 0.3);
        text-decoration: none;
    }
    
    .info-tooltip {
        position: absolute;
        visibility: hidden;
        opacity: 0;
        width: 400px;
        background-color: var(--container-bg);
        color: var(--text-color);
        text-align: left;
        border-radius: 6px;
        padding: 15px;
        box-shadow: 0 3px 8px rgba(0, 0, 0, 0.3);
        z-index: 1;
        bottom: 125%;
        left: 50%;
        transform: translateX(-50%);
        transition: opacity 0.3s, visibility 0.3s;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        font-style: normal;
        font-weight: normal;
        font-size: 0.9em;
        line-height: 1.4;
        white-space: pre-wrap;
        overflow-y: auto;
        max-height: 500px;
        border: 1px solid var(--message-other-border);
    }
    
    .info-tooltip::after {
        content: "";
        position: absolute;
        top: 100%;
        left: 50%;
        margin-left: -5px;
        border-width: 5px;
        border-style: solid;
        border-color: var(--container-bg) transparent transparent transparent;
    }
    
    .modal {
        display: none;
        position: fixed;
        z-index: 10;
        left: 0;
        top: 0;
        width: 100%;
        height: 100%;
        overflow: auto;
        background-color: rgba(0, 0, 0, 0.5);
        backdrop-filter: blur(3px);
    }
    
    .modal-content {
        background-color: var(--container-bg);
        color: var(--text-color);
        margin: 10% auto;
        padding: 20px;
        border: 1px solid var(--message-other-border);
        border-radius: 10px;
        width: 80%;
        max-width: 700px;
        max-height: 70vh;
        box-shadow: 0 5px 15px rgba(0, 0, 0, 0.3);
        position: relative;
        transition: background-color 0.3s ease;
    }
    
    .close-button {
        color: var(--time-color);
        float: right;
        font-size: 28px;
        font-weight: bold;
        cursor: pointer;
        margin-top: -10px;
    }
    
    .close-button:hover {
        color: var(--sender-color);
    }
    
    .modal-body {
        margin-top: 15px;
        white-space: pre-wrap;
        overflow-y: auto;
        max-height: calc(70vh - 100px);
        line-height: 1.5;
    }
    
    .info-button {
        cursor: pointer;
    }
    
    .theme-toggle, .order-toggle {
        background: none;
        border: none;
        color: var(--header-color);
        cursor: pointer;
        font-size: 1.2em;
        display: flex;
        align-items: center;
        padding: 5px;
        border-radius: 50%;
        transition: background-color 0.2s;
    }
    
    .theme-toggle:hover, .order-toggle:hover {
        background-color: rgba(255, 255, 255, 0.1);
    }
    
    .theme-toggle i, .order-toggle i {
        font-style: normal;
    }
    
    .header-buttons {
        display: flex;
        gap: 5px;
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
        transition: background-color 0.3s ease, border-color 0.3s ease, color 0.3s ease;
    }
    
    .message.user {
        align-self: flex-end;
        background-color: var(--message-user-bg);
    }
    
    .message.other {
        align-self: flex-start;
        background-color: var(--message-other-bg);
        border: 1px solid var(--message-other-border);
    }
    
    .message.system {
        align-self: center;
        background-color: var(--message-system-bg);
        color: var(--message-system-color);
        font-style: italic;
        max-width: 90%;
        text-align: center;
    }
    
    .message-sender {
        font-weight: bold;
        margin-bottom: 3px;
        color: var(--sender-color);
        transition: color 0.3s ease;
    }
    
    .message-time {
        color: var(--time-color);
        font-size: 0.7em;
        margin-top: 5px;
        text-align: right;
        transition: color 0.3s ease;
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
        background-color: var(--placeholder-bg);
        border-radius: 5px;
        color: var(--placeholder-color);
        font-style: italic;
        transition: background-color 0.3s ease, color 0.3s ease;
    }
    
    a {
        color: var(--link-color);
        text-decoration: none;
        transition: color 0.3s ease;
    }
    
    a:hover {
        text-decoration: underline;
    }

    .date-separator {
        text-align: center;
        margin: 15px 0;
        color: var(--date-color);
        font-size: 0.8em;
        position: relative;
        transition: color 0.3s ease;
    }
    
    .date-separator:before, .date-separator:after {
        content: "";
        display: inline-block;
        height: 1px;
        background-color: var(--date-line-color);
        width: 35%;
        vertical-align: middle;
        margin: 0 10px;
        transition: background-color 0.3s ease;
    }
    
    /* New message highlighting */
    .message.new-message-subtle {
        position: relative;
        background-color: var(--new-message-subtle);
        border: 1px solid var(--new-message-border);
    }
    
    .message.new-message-prominent {
        position: relative;
        background-color: var(--new-message-prominent);
        border: 1px solid var(--new-message-border);
        animation: pulse-highlight 2s infinite;
    }
    
    .message.new-message-subtle::after,
    .message.new-message-prominent::after {
        content: "NEW";
        position: absolute;
        top: -8px;
        right: 10px;
        background-color: var(--new-message-indicator);
        color: #000;
        font-size: 10px;
        padding: 1px 5px;
        border-radius: 8px;
        font-weight: bold;
    }
    
    .update-timestamp {
        text-align: center;
        padding: 8px 12px;
        background-color: var(--header-bg);
        color: var(--header-color);
        margin: 15px auto;
        border-radius: 10px;
        font-weight: bold;
        width: 80%;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
        position: relative;
    }
    
    .update-message {
        text-align: center;
        padding: 10px 15px;
        color: var(--date-color);
        font-style: italic;
        font-size: 0.85em;
        margin: 25px auto 15px;
        border-top: 1px solid var(--date-line-color);
        max-width: 80%;
    }
    
    .new-messages-indicator {
        background-color: var(--header-bg);
        color: white;
        text-align: center;
        padding: 5px;
        font-weight: bold;
        position: sticky;
        top: 0;
        z-index: 10;
        box-shadow: 0 2px 5px rgba(0, 0, 0, 0.2);
    }
    
    @keyframes pulse-highlight {
        0% { box-shadow: 0 0 0 0 rgba(255, 193, 7, 0.4); }
        70% { box-shadow: 0 0 0 5px rgba(255, 193, 7, 0); }
        100% { box-shadow: 0 0 0 0 rgba(255, 193, 7, 0); }
    }
    """

def generate_javascript() -> str:
    """Generate JavaScript code for the HTML output.
    
    Returns:
        JavaScript code as a string
    """
    return """
        function toggleTheme() {
            const html = document.documentElement;
            const themeIcon = document.getElementById('theme-icon');
            
            if (html.getAttribute('data-theme') === 'dark') {
                html.removeAttribute('data-theme');
                themeIcon.textContent = '🌙'; // moon icon
                localStorage.setItem('theme', 'light');
            } else {
                html.setAttribute('data-theme', 'dark');
                themeIcon.textContent = '☀️'; // sun icon
                localStorage.setItem('theme', 'dark');
            }
        }
        
        // Function to scroll to the first new message
        function scrollToFirstNewMessage() {
            const newMessages = document.querySelectorAll('.new-message-subtle, .new-message-prominent');
            if (newMessages.length > 0) {
                newMessages[0].scrollIntoView({
                    behavior: 'smooth',
                    block: 'center'
                });
                
                // Add visual indicator
                const indicator = document.createElement('div');
                indicator.className = 'new-messages-indicator';
                indicator.textContent = `${newMessages.length} new messages`;
                
                const chatMessages = document.querySelector('.chat-messages');
                chatMessages.insertBefore(indicator, chatMessages.firstChild);
                
                // Add a close button to the indicator
                const closeButton = document.createElement('span');
                closeButton.innerHTML = ' &times;';
                closeButton.style.cursor = 'pointer';
                closeButton.style.float = 'right';
                closeButton.style.marginRight = '10px';
                closeButton.onclick = function() {
                    indicator.style.display = 'none';
                };
                indicator.appendChild(closeButton);
                
                // Add a "Next" button to navigate through new messages
                const nextButton = document.createElement('span');
                nextButton.innerHTML = ' Next ↓';
                nextButton.style.cursor = 'pointer';
                nextButton.style.float = 'right';
                nextButton.style.marginRight = '20px';
                
                let currentIndex = 0;
                nextButton.onclick = function() {
                    currentIndex = (currentIndex + 1) % newMessages.length;
                    newMessages[currentIndex].scrollIntoView({
                        behavior: 'smooth',
                        block: 'center'
                    });
                };
                
                indicator.appendChild(nextButton);
            }
        }
        
        function toggleChatOrder() {
            const chatMessages = document.querySelector('.chat-messages');
            const orderIcon = document.getElementById('order-icon');
            const currentOrder = localStorage.getItem('chatOrder') || 'reverse-chronological';
            
            // Convert children to array for easier manipulation
            const messagesArray = Array.from(chatMessages.children);
            
            // Get date separators and their corresponding messages
            const dateGroups = [];
            let currentGroup = [];
            let currentDate = null;
            
            messagesArray.forEach(element => {
                if (element.classList.contains('date-separator')) {
                    if (currentDate) {
                        dateGroups.push({
                            dateSeparator: currentDate,
                            messages: currentGroup
                        });
                    }
                    currentDate = element;
                    currentGroup = [];
                } else {
                    currentGroup.push(element);
                }
            });
            
            // Don't forget to add the last group
            if (currentDate) {
                dateGroups.push({
                    dateSeparator: currentDate,
                    messages: currentGroup
                });
            }
            
            // Clear the current content
            chatMessages.innerHTML = '';
            
            if (currentOrder === 'chronological') {
                // Reverse the order of date groups
                dateGroups.reverse();
                
                // For each date group, add the date separator and then the messages in reverse order
                dateGroups.forEach(group => {
                    chatMessages.appendChild(group.dateSeparator);
                    group.messages.reverse().forEach(message => {
                        chatMessages.appendChild(message);
                    });
                });
                
                orderIcon.textContent = '⏬'; // Down arrow
                localStorage.setItem('chatOrder', 'reverse-chronological');
            } else {
                // Restore chronological order
                dateGroups.reverse();
                
                dateGroups.forEach(group => {
                    chatMessages.appendChild(group.dateSeparator);
                    group.messages.reverse().forEach(message => {
                        chatMessages.appendChild(message);
                    });
                });
                
                orderIcon.textContent = '⏫'; // Up arrow
                localStorage.setItem('chatOrder', 'chronological');
            }
        }
        
        function toggleInfoModal() {
            const modal = document.getElementById('info-modal');
            if (modal) {
                modal.style.display = 'block';
            }
        }
        
        function closeInfoModal() {
            const modal = document.getElementById('info-modal');
            if (modal) {
                modal.style.display = 'none';
            }
        }
        
        // Close modal when clicking outside of it
        window.onclick = function(event) {
            const modal = document.getElementById('info-modal');
            if (modal && event.target === modal) {
                modal.style.display = 'none';
            }
        };
        
        // Function to set initial chat order
        function setInitialChatOrder() {
            const chatMessages = document.querySelector('.chat-messages');
            const orderIcon = document.getElementById('order-icon');
            const savedOrder = localStorage.getItem('chatOrder');
            
            // If no saved preference, set to reverse chronological by default
            if (!savedOrder) {
                localStorage.setItem('chatOrder', 'reverse-chronological');
            }
            
            // If we want reverse chronological (either by default or saved preference)
            if (!savedOrder || savedOrder === 'reverse-chronological') {
                // Directly manipulate the DOM instead of toggling
                const messagesArray = Array.from(chatMessages.children);
                
                // Get date separators and their corresponding messages
                const dateGroups = [];
                let currentGroup = [];
                let currentDate = null;
                
                messagesArray.forEach(element => {
                    if (element.classList.contains('date-separator')) {
                        if (currentDate) {
                            dateGroups.push({
                                dateSeparator: currentDate,
                                messages: currentGroup
                            });
                        }
                        currentDate = element;
                        currentGroup = [];
                    } else {
                        currentGroup.push(element);
                    }
                });
                
                // Don't forget to add the last group
                if (currentDate) {
                    dateGroups.push({
                        dateSeparator: currentDate,
                        messages: currentGroup
                    });
                }
                
                // Clear the current content
                chatMessages.innerHTML = '';
                
                // Reverse the order of date groups
                dateGroups.reverse();
                
                // For each date group, add the date separator and then the messages in reverse order
                dateGroups.forEach(group => {
                    chatMessages.appendChild(group.dateSeparator);
                    group.messages.reverse().forEach(message => {
                        chatMessages.appendChild(message);
                    });
                });
                
                // Set the icon to show we're in reverse-chronological mode
                orderIcon.textContent = '⏬'; // Down arrow
            }
        }
        
        // Set theme based on time or saved preference
        function setInitialTheme() {
            const savedTheme = localStorage.getItem('theme');
            const themeIcon = document.getElementById('theme-icon');
            const currentHour = new Date().getHours();
            
            // Apply dark mode if after 9 PM (21:00) or before 6 AM, or if user previously selected dark mode
            if (savedTheme === 'dark' || currentHour >= 21 || currentHour < 6) {
                document.documentElement.setAttribute('data-theme', 'dark');
                themeIcon.textContent = '☀️'; // sun icon
                localStorage.setItem('theme', 'dark');
            }
        }
        
        // Check for saved preferences
        document.addEventListener('DOMContentLoaded', () => {
            // Apply theme preference based on time or saved setting
            setInitialTheme();
            
            // Set initial chat order (newest first by default)
            setInitialChatOrder();
            
            // Scroll to first new message if there are any
            scrollToFirstNewMessage();
        });
    """

def generate_html(messages: List[Dict[str, Any]], extract_dir: str, output_file: str, 
                 info_text: Optional[str] = None, chat_title: str = "WhatsApp Chat",
                 highlight_new: str = 'none', zip_timestamp: Optional[str] = None) -> None:
    """Generate HTML from parsed messages.
    
    Args:
        messages: List of parsed message dictionaries
        extract_dir: Directory containing the extracted WhatsApp export
        output_file: Path to write the HTML output
        info_text: Optional content of info.txt file
        chat_title: Title of the chat
        highlight_new: How to highlight new messages (none, subtle, prominent)
        zip_timestamp: Optional timestamp of the zip file for update message
    """
    # Get relative path to JSON file
    json_file = os.path.basename(output_file).replace('.html', '.json')
    
    # Get CSS and JavaScript
    css = generate_css()
    js = generate_javascript()
    
    # Count new messages
    new_message_count = sum(1 for m in messages if m.get('_internal', {}).get('is_new', False))
    
    # Debug info for highlighting
    logger = logging.getLogger(__name__)
    logger.info(f"Highlight level: {highlight_new}, New messages detected: {new_message_count}")
    if new_message_count > 0:
        for i, m in enumerate(messages):
            if m.get('_internal', {}).get('is_new', False):
                logger.info(f"New message {i}: {m.get('content', '')[:30]}...")
    
    # Start building the HTML content
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{html.escape(chat_title)}</title>
    <style>{css}</style>
</head>
<body>
    <div class="chat-container">
        <div class="chat-header">
            <div class="chat-title">
                <h1>{html.escape(chat_title)}</h1>
                <a href="{json_file}" class="json-link" download>JSON</a>
                {f'''<div class="info-button" onclick="toggleInfoModal()">
                    Info
                    <div class="info-tooltip">{html.escape(info_text)}</div>
                </div>''' if info_text else ''}
            </div>
            <div class="header-buttons">
                <button class="order-toggle" onclick="toggleChatOrder()" title="Reverse chat order">
                    <i id="order-icon">⏬</i>
                </button>
                <button class="theme-toggle" onclick="toggleTheme()" title="Toggle dark/light mode">
                    <i id="theme-icon">🌙</i>
                </button>
            </div>
        </div>
        
        {f'''<div id="info-modal" class="modal">
            <div class="modal-content">
                <span class="close-button" onclick="closeInfoModal()">&times;</span>
                <h2>Chat Information</h2>
                <div class="modal-body">{html.escape(info_text)}</div>
            </div>
        </div>''' if info_text else ''}
        
        <div class="chat-messages">
"""

    current_date = None
    found_first_new = False
    update_timestamp_added = False
    
    for message in messages:
        # Parse and format the timestamp
        try:
            timestamp = parse_timestamp(message['timestamp'])
            if timestamp:
                message_date = timestamp.strftime('%d %B %Y')
                message_time = timestamp.strftime('%H:%M')
            else:
                # Fallback for unparseable dates
                message_date = message['timestamp'].split(',')[0].strip()
                message_time = message['timestamp'].split(',')[1].strip() if ',' in message['timestamp'] else ""
        except Exception as e:
            logger = logging.getLogger(__name__)
            logger.warning(f"Warning when formatting date: {e}")
            # Fallback for unparseable dates - use the original string
            message_date = message['timestamp'].split(',')[0].strip()
            message_time = message['timestamp'].split(',')[1].strip() if ',' in message['timestamp'] else ""
        
        # Add date separator if it's a new day
        if message_date != current_date:
            html_content += f'            <div class="date-separator">{message_date}</div>\n'
            current_date = message_date
        
        sender = message['sender']
        
        # Determine the message type
        message_type = "system"
        if "~" in sender:
            if ("added" in message['content'] or 
                "joined using this group's invite link" in message['content'] or 
                "left" in message['content'] or 
                "changed" in message['content']):
                message_type = "system"
            else:
                message_type = "other"  # Group message from someone else
        elif sender != "System":
            message_type = "user"  # Assume messages without "~" are from the user
        
        # Check if this is a new message
        new_message_class = ""
        is_new = message.get('_internal', {}).get('is_new', False)
        
        # Add update timestamp before the first new message
        if is_new and not update_timestamp_added and highlight_new != 'none':
            now = datetime.now().strftime("%d %B %Y, %H:%M")
            html_content += f'            <div class="update-timestamp">Updated on {now} ↓</div>\n'
            update_timestamp_added = True
        
        if is_new and highlight_new != 'none':
            if highlight_new == 'subtle':
                new_message_class = " new-message-subtle"
            elif highlight_new == 'prominent':
                new_message_class = " new-message-prominent"
        
        # Create the message HTML
        html_content += f'            <div class="message {message_type}{new_message_class}">\n'
        
        # Add sender if it's not a system message
        if message_type != "system":
            html_content += f'                <div class="message-sender">{html.escape(sender)}</div>\n'
        
        # Add message content if there is any
        content = message['content']
                
        # Handle special case for mobile format media files
        # Check if content ends with "(file attached)" pattern
        file_attached_match = re.search(r'([\w-]+\.(?:jpg|jpeg|png|gif|mp4|avi|mp3|wav|pdf|doc|docx))\s+\(file attached\)$', content)
        
        if file_attached_match and not message['media']:
            # This is a mobile format media message that wasn't caught during parsing
            # Extract the filename and add it to media
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
            
            # Add to media array
            message['media'].append({
                'type': media_type,
                'file': media_file
            })
            
            # Remove the file attachment text from content
            content = content.replace(file_attached_match.group(0), '').strip()
        
        if content:
            # First escape the HTML
            content = html.escape(content)
            
            # Then convert URLs to links
            url_pattern = r'(https?://[^\s]+)'
            content = re.sub(url_pattern, r'<a href="\1" target="_blank">\1</a>', content)
            
            html_content += f'                <div class="message-content">{content}</div>\n'
        
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
    
    # Close the chat messages div
    html_content += """        </div>
"""

    # Add export/update timestamp at the end if provided
    if zip_timestamp and highlight_new != 'none':
        html_content += f"""        <div class="update-message">
            Export updated on {zip_timestamp}.
        </div>
"""

    # Close the rest of the HTML document
    html_content += """    </div>
    
    <script>""" + js + """
    </script>
</body>
</html>"""
    
    # Write the HTML content to the output file
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    logger = logging.getLogger(__name__)
    logger.info(f"Generated HTML file: {output_file}")
