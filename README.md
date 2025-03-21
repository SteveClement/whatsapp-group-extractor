# WhatsApp Group Members Extractor

This project is a Python script that uses Selenium WebDriver to extract group information and member details from WhatsApp Web. It automates browser interactions, allowing you to list groups, search for specific group chats, and retrieve group members.

## Features

- **Chrome WebDriver Integration:** Uses an existing Chrome user profile to maintain the WhatsApp Web login session.
- **QR Code Scanning:** Waits for you to scan the QR code on WhatsApp Web before proceeding.
- **Group Chat Operations:** Allows searching for a group chat by name, listing all group chats, and opening group info panels.
- **Group Members Extraction:** Expands group member lists and extracts individual member names.

## Prerequisites

- **Python 3.7+**
- **Google Chrome** installed on your system
- A WhatsApp account with access to WhatsApp Web

## Installation

1. **Clone the repository:**

    ```bash
    git clone https://github.com/SteveClement/whatsapp-group-extractor.git
    cd whatsapp-group-extractor
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

## Configuration

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