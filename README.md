# WhatsApp Tools

This repository contains tools for working with WhatsApp data:

1. **WhatsApp Group Members Extractor**: A Python script that uses Selenium WebDriver to extract group information and member details from WhatsApp Web.
2. **WhatsApp Chat Export to HTML**: A Python script that converts WhatsApp chat exports to a feature-rich HTML viewer with JSON export capability.

## WhatsApp Group Members Extractor

This tool automates browser interactions, allowing you to list groups, search for specific group chats, and retrieve group members.

### Features

- **Chrome WebDriver Integration:** Uses an existing Chrome user profile to maintain the WhatsApp Web login session.
- **QR Code Scanning:** Waits for you to scan the QR code on WhatsApp Web before proceeding.
- **Group Chat Operations:** Allows searching for a group chat by name, listing all group chats, and opening group info panels.
- **Group Members Extraction:** Expands group member lists and extracts individual member names.

## WhatsApp Chat Export to HTML

This tool converts WhatsApp chat export files into a beautiful, interactive HTML viewer with powerful features.

### Features

- **Cross-Platform Compatibility:** Handles both desktop and mobile WhatsApp export formats automatically
- **Media Support:** Displays images, videos, and other media files inline
- **Chronological Control:** Toggle between newest-first and oldest-first message display
- **Dark/Light Mode:** Switch between light and dark themes with automatic night mode after 9 PM
- **JSON Export:** Generates structured JSON files with all chat data for further analysis
- **Chat Info Panel:** Displays chat information from info.txt if available
- **Custom Titles:** Uses the title from info.txt to personalize the display
- **Mobile Responsive:** Works well on both desktop and mobile browsers
- **Update Detection:** Add new messages to existing exports with visual highlighting
- **Message IDs:** Tracks messages uniquely for update detection and de-duplication
- **Enhanced Media Handling:** Improved detection and display of various media types
- **Metadata Storage:** Maintains chat history and processing information

## Prerequisites

- **Python 3.7+**
- **Google Chrome** installed on your system (for Group Members Extractor)
- A WhatsApp account with access to WhatsApp Web (for Group Members Extractor)
- WhatsApp chat export(s) in ZIP format (for Chat Export to HTML)

## Installation

1. **Clone the repository:**

    ```bash
    git clone https://github.com/SteveClement/whatsapp-tools.git
    cd whatsapp-tools
    ```

2. **(Optional) Create a virtual environment:**

    ```bash
    python3 -m venv venv
    source venv/bin/activate    # On Windows use: venv\Scripts\activate
    ```

3. **Install dependencies:**

    ```bash
    pip install -r requirements.txt
    ```

## Group Members Extractor Configuration

Create a `config.py` file in the project root with the following content. Adjust the values as needed:

```python
# config.py

# Path to your Chrome user profile directory
CHROME_PROFILE_PATH = "/path/to/your/chrome/profile"

# Chrome profile directory name (often "Default")
CHROME_PROFILE_DIR = "Default"

# The WhatsApp group name to search for (used in search operations)
GROUP_NAME = "Your Group Name"

# Wait times (in seconds)
SHORT_WAIT = 5
LONG_WAIT = 20

# Set to True to run Chrome in headless mode
HEADLESS = False

# Enable debug output for troubleshooting
DEBUG = True
```

## Chat Export to HTML Usage

The WhatsApp Chat Export to HTML tool converts your exported WhatsApp chats to an interactive HTML viewer.

### How to Use

1. **Export your WhatsApp chat**:
   - In WhatsApp, open the chat you want to export
   - Tap the three dots menu (⋮) > More > Export chat
   - Choose whether to include media
   - Share/export the ZIP file to your computer

2. **Create an info.txt file (optional)**:
   - Create a text file named `info.txt` with details about the chat
   - First line can include a title: `Title: My Chat Group Name`
   - Add any additional description or context

3. **Run the conversion script**:
   
   For new exports:
   ```bash
   python whatsapp_converter.py convert export.zip -o my_output_dir
   ```

   To update an existing export with new messages:
   ```bash
   python whatsapp_converter.py update export.zip -o my_output_dir --highlight subtle
   ```

4. **Open the generated HTML file**:
   - Navigate to the output directory
   - Open `whatsapp_chat.html` in your browser

### Command Line Options

```
Commands:
    convert             Process a new WhatsApp export
    update              Update an existing export with new messages

Arguments:
    ZIPFILE             Path to the WhatsApp export zip file
    
Options:
    --output-dir DIR    Output directory for HTML and JSON files [default: html]
    --info-file FILE    Optional path to a custom info.txt file
    --highlight LEVEL   How to highlight new messages (none, subtle, prominent) [default: subtle]
    -h, --help          Show this help message and exit
```

### Features in Detail

- **Timeline Control**: Click the ⏬/⏫ button to toggle between newest-first and oldest-first views
- **Theme Toggle**: Click the 🌙/☀️ button to switch between dark and light modes
- **Info Button**: If you included an info.txt file, click "Info" to see details about the chat
- **JSON Data**: Click "JSON" to download a JSON file containing all the chat data
- **Update Highlighting**: New messages are highlighted when updating an existing export
- **Mobile & Desktop Format Detection**: Automatically detects and handles both export formats

## Related Tools

- [WhatsTK](https://whatstk.readthedocs.io/en/latest/)
- [Obsolete but valid pointers](https://github.com/GabriellBP/whatsapp-web-scraping)
- [WPP Whatsapp](https://github.com/3mora2/WPP_Whatsapp) based on [wppconnect](https://github.com/wppconnect-team/wppconnect)

## Todo

### Group Members Extractor
- In a group list with more than 16 participants, you need to scroll down to fetch the full list. Possible pointers [here](https://stackoverflow.com/questions/61826721/how-to-scrape-elements-of-whatsapp-web-using-selenium).

### Chat Export to HTML
- Add search functionality to find specific messages
- Add message statistics and visualization
- Support for exporting to other formats (PDF, CSV)
- Add option to filter messages by sender
