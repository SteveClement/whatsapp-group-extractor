import time
from config import CHROME_PROFILE_PATH, CHROME_PROFILE_DIR, GROUP_NAME, SHORT_WAIT, LONG_WAIT, HEADLESS, DEBUG, SLOW_MODE
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
import random


def init_driver(profile_path=None, profile_dir=None):
    """
    Initialize and return a Chrome WebDriver with the specified user profile.
    This uses an existing Chrome profile to maintain WhatsApp Web login session.
    """
    options = webdriver.ChromeOptions()
    options.headless = HEADLESS
    if profile_path:
        options.add_argument(f"--user-data-dir={profile_path}")
    if profile_dir:
        options.add_argument(f"--profile-directory={profile_dir}")
    # Initialize the Chrome driver using WebDriverManager to handle driver installation
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    # Navigate to WhatsApp Web
    driver.get("https://web.whatsapp.com/")
    return driver


def slow_send_keys(element, text, min_delay=0, max_delay=0.2):
    """
    Sends keys to the given element one character at a time with a random delay.

    Args:
        element: The WebElement to send keys to.
        text (str): The text to type.
        min_delay (float): Minimum delay in seconds between each keystroke.
        max_delay (float): Maximum delay in seconds between each keystroke.
    """
    if not SLOW_MODE:
        element.send_keys(text)
        return

    for char in text:
        element.send_keys(char)
        time.sleep(random.uniform(min_delay, max_delay))


def wait_for_qr_scan(driver, check_interval=SHORT_WAIT):
    """
    Pause script execution until the WhatsApp Web QR code is scanned by the user.
    The function repeatedly checks for the presence of the QR code canvas.
    It waits in a loop until the QR code element is no longer found, indicating a successful login.
    """
    while True:
        try:
            # Try to locate the QR code canvas on the page
            driver.find_element(By.CSS_SELECTOR, "canvas[aria-label='Scan this QR code to link a device!']")
            # If found, the user has not scanned the QR code yet
            print("Waiting for QR code scan...")
            time.sleep(check_interval)
        except NoSuchElementException:
            # QR code canvas not found, which likely means the QR was scanned and login is complete
            print("QR Code scanned! Proceeding...")
            break


def search_and_open_group(driver, group_name, timeout=SHORT_WAIT):
    """
    Search for a WhatsApp group by name and open the chat.
    Raises an Exception if the search box or group chat is not found.
    """
    # Wait for the search input box to be present and interactable
    try:
        search_box = WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div[contenteditable='true'][data-tab='3']"))
        )
    except TimeoutException:
        raise Exception("Search box not found on WhatsApp Web.")
    # Enter the group name into the search box and press Enter
    slow_send_keys(search_box, group_name)
    search_box.send_keys(Keys.ENTER)
    # Wait for the group chat to open (check for the group name in chat title)
    try:
        WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((By.XPATH, f"//span[@title='{group_name}']"))
        )
    except TimeoutException:
        raise Exception(f"Group chat '{group_name}' did not open in time.")
    # Go back
    try:
        back_button = WebDriverWait(driver, timeout).until(
            EC.element_to_be_clickable((By.XPATH, "//*[@id='side']/div[1]/div/div[2]/button/div[2]/span"))
        )
        back_button.click()
    except TimeoutException:
        # TODO: Handle this case more gracefully, for some reason the "Back" button is not always selectable
        # raise Exception("Back button not found on WhatsApp Web.")
        print("Back button not found on WhatsApp Web.")

    # slow_send_keys(search_box, group_name)
    try:
        clear_button = WebDriverWait(driver, timeout).until(
            EC.element_to_be_clickable((By.XPATH, "//*[@id='side']/div[1]/div/div[2]/span/button/span"))
        )
        clear_button.click()
    except TimeoutException:
        raise Exception("Clear button not found on WhatsApp Web.")
    # Enter the group name into the search box and press Enter
    print(f"Group chat '{group_name}' found and opened.")


def list_all_groups(driver, timeout=SHORT_WAIT):
    """
    Lists all group chats from the WhatsApp Web chat list.

    This function assumes that group chats are identifiable by an element with a
    data-testid attribute 'icon-group' within each chat's DOM structure.

    Returns:
        A list of group chat names.

    Note:
        The WhatsApp Web DOM can change over time. If no groups are found,
        verify that the XPath used to locate the group icon is still valid.
    """
    group_names = []
    try:
        # Wait for the group icon elements to appear in the chat list.
        group_menu = WebDriverWait(driver, timeout).until(
            EC.element_to_be_clickable((By.XPATH, "//*[@id='group-filter']/div/div"))
        )
        group_menu.click()
        chat_list = WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div[aria-label='Chat list']"))
        )

        # Extract the value of the aria-rowcount attribute
        row_count = chat_list.get_attribute("aria-rowcount")
        print("Total groups:", row_count)

        # Locate all chat items within the chat list container
        chat_items = chat_list.find_elements(By.XPATH, ".//div[@role='listitem']")

        # Iterate through each chat item and extract data
        for index, chat in enumerate(chat_items, start=1):
            try:
                # Extract the chat title (using a span with a title attribute or text)
                title_element = chat.find_element(By.XPATH, ".//span[@dir='auto']")
                chat_title = title_element.get_attribute("title") or title_element.text
                group_names += {chat_title}
            except Exception as e:
                if DEBUG:
                    print(f"Error extracting chat title: {e}")
                chat_title = "Title not found"

            try:
                # Extract the timestamp (assuming it is inside a div with a certain class)
                timestamp = chat.find_element(By.XPATH, ".//div[contains(@class, '_ak8i')]").text
            except Exception as e:
                if DEBUG:
                    print(f"Error extracting timestamp: {e}")
                timestamp = "Timestamp not found"

            try:
                # Extract the message preview text; this example assumes the preview is in a span after a colon.
                preview_element = chat.find_element(By.XPATH, ".//div[contains(@class, '_ak8j')]")
                message_preview = preview_element.text
            except Exception as e:
                if DEBUG:
                    print(f"Error extracting message preview: {e}")
                message_preview = "Message preview not found"

            print(f"Chat #{index}:")
            print(f"  Title: {chat_title}")
            print(f"  Timestamp: {timestamp}")
            print(f"  Preview: {message_preview}\n")
            print(group_names)

    except TimeoutException:
        print("No group icons were found in the chat list.")
    return group_names


def open_group_info_panel(driver, menu_timeout=SHORT_WAIT, info_timeout=LONG_WAIT):
    """
    Open the group info panel from within an open group chat.
    Clicks the chat menu (three-dot menu) and selects the "Group info" option.
    Raises an Exception if the menu button or the Group info option cannot be found or clicked.
    """
    # Click the "burger" menu (three dots) in the chat header
    try:
        menu_button = WebDriverWait(driver, menu_timeout).until(
            EC.element_to_be_clickable((By.XPATH, "//*[@id='main']/header/div[3]/div/div[3]/div/button/span"))
        )
        menu_button.click()
    except TimeoutException:
        raise Exception("Chat menu (three dots) button not found or not clickable.")
    # Click the "Group info" option in the dropdown menu
    try:
        info_button = WebDriverWait(driver, info_timeout).until(
            EC.element_to_be_clickable((By.XPATH, "//div[@aria-label='Group info']"))
        )
        info_button.click()
    except TimeoutException:
        raise Exception("'Group info' option not found or not clickable.")
    print("Group info panel opened.")


def expand_all_members(driver, timeout=SHORT_WAIT):
    """
    Expand the members list in the group info panel to show all participants.
    For large groups, WhatsApp Web shows a partial list of members with a "See all" button.
    This function clicks on the initial members list, then the "See all" button if it exists.
    """
    # Define XPaths for the members section button and the "See all members" button
    expand_members_xpath = (
        "//*[@id='app']/div/div[3]/div/div[5]/span/div/span/div/div/div/section/div[1]/div/div[3]/"
        "span/span/button"
    )
    all_members_xpath = (
        "//*[@id='app']/div/div[3]/div/div[5]/span/div/span/div/div/div/section/div[6]/div[2]/div[3]/"
        "div[2]/div/span/div"
    )
    # Click the initial members section to expand the members list
    try:
        members_section_button = WebDriverWait(driver, timeout).until(
            EC.element_to_be_clickable((By.XPATH, expand_members_xpath))
        )
        members_section_button.click()
        print(f"{members_section_button.text}")
    except TimeoutException:
        raise Exception("Members list section button not found or not clickable.")
    # Click the "See all members" button, if present (for groups with many members)
    try:
        all_members_button = WebDriverWait(driver, timeout).until(
            EC.element_to_be_clickable((By.XPATH, all_members_xpath))
        )
        all_members_button.click()
    except TimeoutException:
        # If this button isn't found, assume all members are already visible
        print("No 'See all members' button found (all members might already be visible).")
    # Close the members list
    try:
        close_button = WebDriverWait(driver, timeout).until(
            EC.element_to_be_clickable((By.XPATH, "//*[@id='app']/div/span[2]/div/span/div/div/div/div/div/div/header/div/div[1]/div/span"))
        )
        close_button.click()
    except TimeoutException:
        raise Exception("'Close member button not found or not clickable.")
    print("Member panel closed.")


def get_group_members(driver, timeout=LONG_WAIT):
    """
    Retrieve the list of member names from the expanded group members list.
    Returns a list of names. Raises an Exception if no members are found.
    """
    try:
        # Wait until at least one member entry is present in the members list
        member_elements = WebDriverWait(driver, timeout).until(
            EC.presence_of_all_elements_located((By.XPATH, "//div[@role='button']//span[@dir='auto']"))
        )
    except TimeoutException:
        raise Exception("No members found or the member list did not load.")
    # Extract and return member names, excluding any empty strings
    member_names = [elem.text for elem in member_elements if elem.text and elem.text.strip()]
    return member_names


def main():
    """Main function to drive the WhatsApp group members extraction script."""
    # Initialize WebDriver and navigate to WhatsApp Web
    driver = init_driver(CHROME_PROFILE_PATH, CHROME_PROFILE_DIR)
    try:
        # Wait for user to scan the WhatsApp Web QR code (if not already logged in)
        wait_for_qr_scan(driver)
        # Optional: list all group chats (for reference)
        all_groups = list_all_groups(driver)
        print("All Group Chats:")
        for group in all_groups:
            search_and_open_group(driver, group)
            open_group_info_panel(driver)
            expand_all_members(driver)
            members = get_group_members(driver)
            print("------")
            time.sleep(5)
        time.sleep(3)
        return
        # Search for the group chat by name and open it
        search_and_open_group(driver, GROUP_NAME)
        # Open the Group Info panel from within the chat
        open_group_info_panel(driver)
        # Expand the members list to ensure all members are visible
        expand_all_members(driver)
        # Retrieve the list of group member names
        members = get_group_members(driver)
        # Print the member list to the console
        print("Group Members:")
        for member in members:
            print(member)
            print("------")
    except Exception as err:
        # Print any errors encountered during the process
        print(f"Error: {err}")
    finally:
        # Optional: wait a few seconds before closing (e.g., to review the browser or console output)
        time.sleep(SHORT_WAIT)
        driver.quit()


if __name__ == "__main__":
    main()
