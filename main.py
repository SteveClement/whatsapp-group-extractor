#!/usr/bin/env python
import time

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Setup Selenium WebDriver
options = webdriver.ChromeOptions()
options.add_argument("--user-data-dir=/Users/steve/Library/Application Support/Google/ChromeAutomaton")  # Path to your Chrome profile
options.add_argument("--profile-directory=Default")  # Uses your Chrome session to keep WhatsApp logged in

# Open WhatsApp Web
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
driver.get("https://web.whatsapp.com/")

# Function to check if the QR code canvas is present
def is_qr_code_present():
    try:
        # Wait for the canvas element to be present
        canvas = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "canvas[aria-label='Scan this QR code to link a device!']"))
        )
        return True
    except NoSuchElementException:
        return False
    except Exception as e:
        print(f"An error occurred: {e}")
        return False


# Wait until the user scans the QR code
time.sleep(3)
while is_qr_code_present():
    print("Waiting for QR code scan...")
    time.sleep(3)

print("QR Code scanned! Proceeding...")

# Locate the group chat
group_name = "Quartier Gare - sécurité & propreté"  # Replace with your group name

# Define the XPath to search for elements
xpath_query = "/html/body/div[1]/div/div/div[3]/div/div[3]/div/div[1]/div/div[2]/button"

try:
    # Find elements matching the XPath
    search_box = elements = driver.find_elements(By.XPATH, xpath_query)

    if not elements:
        print("No elements found for XPath:", xpath_query)
    else:
        print(f"Found {len(elements)} elements matching XPath: {xpath_query}")
except Exception as e:
    print("Error while searching for elements:", e)
    driver.quit()
    raise SystemExit("Search box not found! Exiting...")

search_box.click()
search_box.send_keys(group_name)
search_box.send_keys(Keys.ENTER)

# Wait for the group chat to load
time.sleep(300)

# Open group info
group_info_button = driver.find_element(By.XPATH, '//header//div[@role="button"][@title="Group info"]')
group_info_button.click()

# Wait for the group info to load
time.sleep(10)

# Extract the member list
members = driver.find_elements(By.XPATH, '//div[@class="_2nY6U"]//span[@class="_3Whw5"]')
member_list = [member.text for member in members]

# Print the member list
print("Group Members:")
for member in member_list:
    print(member)

# Close the driver
driver.quit()