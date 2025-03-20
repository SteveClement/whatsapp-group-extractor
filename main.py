#!/usr/bin/env python
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import NoSuchElementException, TimeoutException

# Setup Selenium WebDriver
options = webdriver.ChromeOptions()
options.add_argument("--user-data-dir=/Users/steve/Library/Application Support/Google/ChromeAutomaton")  # Path to your Chrome profile
options.add_argument("--profile-directory=Default")  # Uses your Chrome session to keep WhatsApp logged in

# Initialize the WebDriver
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
driver.get("https://web.whatsapp.com/")

# Function to check if the QR code canvas is present
def is_qr_code_present():
    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "canvas[aria-label='Scan this QR code to link a device!']"))
        )
        return True
    except TimeoutException:
        return False

# Wait until the user scans the QR code
while is_qr_code_present():
    print("Waiting for QR code scan...")
    time.sleep(3)

print("QR Code scanned! Proceeding...")

# Locate the group chat
group_name = "Quartier Gare - sécurité & propreté"  # Replace with your group name

try:
    print("# Wait for the search box to be present and interactable")
    search_box = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "div[contenteditable='true'][data-tab='3']"))
    )
    search_box.clear()
    search_box.send_keys(group_name)
    search_box.send_keys(Keys.ENTER)
except TimeoutException:
    print("Search box not found or group name not found!")
    driver.quit()
    exit()

print("# Wait for the group chat to load")
try:
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH, f"//span[@title='{group_name}']"))
    )
except TimeoutException:
    print("Group chat did not load in time!")
    driver.quit()
    exit()

print("# Open group info")
try:
    group_info_button = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH, '//header//div[@role="button"][@title="Group info"]'))
    )
    group_info_button.click()
except TimeoutException:
    print("Group info button not found!")
    driver.quit()
    exit()

# Wait for the group info to load
try:
    WebDriverWait(driver, 20).until(
        EC.presence_of_element_located((By.XPATH, '//div[@id="app"]'))
    )
except TimeoutException:
    print("Group info did not load in time!")
    driver.quit()
    exit()

# Extract the member list
try:
    members_panel = WebDriverWait(driver, 20).until(
        EC.presence_of_element_located((By.XPATH, '//div[contains(@aria-label, "Group members")]'))
    )
    members = members_panel.find_elements(By.XPATH, './/div[@role="button"]//span[@dir="auto"]')
    member_list = [member.text for member in members if member.text.strip()]

    # Print the member list
    print("Group Members:")
    for member in member_list:
        print(member)
except NoSuchElementException:
    print("No members found or unable to extract member list!")

# Close the driver
driver.quit()