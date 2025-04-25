import os
import zipfile
import shutil
import re
from pathlib import Path

# Unzip the provided file
zip_path = './export.zip'
html_output_folder = './html'
os.makedirs(html_output_folder, exist_ok=True)

with zipfile.ZipFile(zip_path, 'r') as zip_ref:
    zip_ref.extractall(html_output_folder)

# Locate the _chat.txt file
chat_file_path = os.path.join(html_output_folder, '_chat.txt')
if not os.path.exists(chat_file_path):
    raise FileNotFoundError("_chat.txt not found in the extracted content.")

# Load the chat text
with open(chat_file_path, 'r', encoding='utf-8') as f:
    chat_text = f.readlines()

# Create a basic HTML structure
html_content = ["""
<!DOCTYPE html>
<html lang=\"en\">
<head>
    <meta charset=\"UTF-8\">
    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">
    <title>WhatsApp Chat</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .message { margin-bottom: 10px; }
        .sender { font-weight: bold; }
        .timestamp { color: grey; font-size: 0.9em; }
        img, video { max-width: 400px; display: block; margin-top: 5px; }
    </style>
</head>
<body>
<h1>WhatsApp Chat Export</h1>
"""]

# Define a simple regex for parsing lines
message_pattern = re.compile(r'^(\d{1,2}/\d{1,2}/\d{2,4}), (\d{1,2}:\d{2}(?:\s?[APMapm]{2})?) - (.*?): (.*)$')

# Process each line
for line in chat_text:
    match = message_pattern.match(line)
    if match:
        date, time, sender, message = match.groups()
        html_content.append(
            f'<div class="message">'
            f'<span class="timestamp">[{date} {time}]</span> '
            f'<span class="sender">{sender}</span>: {message}'
            f'</div>'
        )

        # Check if message references a media file
        media_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.mp4', '.webm']
        for ext in media_extensions:
            if ext in message.lower():
                media_filename = message.strip()
                if os.path.exists(os.path.join(html_output_folder, media_filename)):
                    if ext in ['.jpg', '.jpeg', '.png', '.gif']:
                        html_content.append(f'<img src="{media_filename}" alt="Media">')
                    elif ext in ['.mp4', '.webm']:
                        html_content.append(f'<video controls><source src="{media_filename}" type="video/{ext[1:]}"></video>')

html_content.append("""
</body>
</html>
""")

# Write the HTML file
html_file_path = os.path.join(html_output_folder, 'chat.html')
with open(html_file_path, 'w', encoding='utf-8') as f:
    f.writelines(html_content)

# Remove _chat.txt
os.remove(chat_file_path)

print(f"Static HTML representation created at {html_file_path}")

