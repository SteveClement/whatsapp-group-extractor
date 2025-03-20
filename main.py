from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from webdriver_manager.chrome import ChromeDriverManager
import time

# Setup Selenium WebDriver
options = webdriver.ChromeOptions()
options.add_argument("--user-data-dir=/Users/steve/Library/Application Support/Google/ChromeAutomaton")  # Path to your Chrome profile
options.add_argument("--profile-directory=Default")  # Uses your Chrome session to keep WhatsApp logged in

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
driver.get("https://web.whatsapp.com/")

waitTime = 5
# Locate the group chat
group_name = "Quartier Gare - sécurité & propreté"  # Replace with your group name
group_name = "X8823"

# Function to check if the QR code canvas is present
def is_qr_code_present():
    try:
        WebDriverWait(driver, waitTime).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "canvas[aria-label='Scan this QR code to link a device!']"))
        )
        return True
    except:
        return False


# Wait until the user scans the QR code
while is_qr_code_present():
    print("Waiting for QR code scan...")
    time.sleep(3)

print("QR Code scanned! Proceeding...")

print("Searching for group chat...")
try:
    # Wait for the search box to be present and interactable
    search_box = WebDriverWait(driver, waitTime).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "div[contenteditable='true'][data-tab='3']"))
    )
    search_box.clear()
    search_box.send_keys(group_name)
    search_box.send_keys(Keys.ENTER)
except:
    print("Search box not found or group name not found!")
    driver.quit()
    exit()

print("Group chat found!")
# Wait for the group chat to load
try:
    WebDriverWait(driver, waitTime).until(
        EC.presence_of_element_located((By.XPATH, f"//span[@title='{group_name}']"))
    )
except:
    print("Group chat did not load in time!")
    driver.quit()
    exit()

print("Opening group chat burger menu...")
# Click the "Burger" menu (three-dot menu) in the chat header
try:
    burger_menu_button = WebDriverWait(driver, waitTime).until(
        EC.element_to_be_clickable((By.XPATH, "//*[@id='main']/header/div[3]/div/div[3]/div/button/span"))
    )
    burger_menu_button.click()
except:
    print("Burger menu button not found!")
    sleep(30)
    driver.quit()
    exit()

print("Opening group info...")
# Click the "Group info" option from the dropdown
try:
    group_info_button = WebDriverWait(driver, 20).until(
        EC.element_to_be_clickable((By.XPATH, "//div[@aria-label='Group info']"))
    )
    group_info_button.click()
except:
    print("Group info button not found!")
    driver.quit()
    exit()

print("Extracting group members...")
# Wait for the group info to load
try:
    WebDriverWait(driver, waitTime).until(
        EC.presence_of_element_located((By.XPATH, "//div[@id='app']"))
    )
except:
    print("Group info did not load in time!")
    driver.quit()
    exit()



print("Opening group members menu...")
try:
    members = WebDriverWait(driver, waitTime).until(
        EC.element_to_be_clickable((By.XPATH, "//*[@id='app']/div/div[3]/div/div[5]/span/div/span/div/div/div/section/div[1]/div/div[3]/span/span/button"))
    )
    members.click()
except:
    print("Members button not found!")
    sleep(30)
    driver.quit()
    exit()


print("Opening all members menu...")
try:
    members = WebDriverWait(driver, waitTime).until(
        EC.element_to_be_clickable((By.XPATH, "//*[@id='app']/div/div[3]/div/div[5]/span/div/span/div/div/div/section/div[6]/div[2]/div[3]/div[2]/div/span/div"))
    )
    members.click()
except:
    print("Members all button not found!")
    sleep(30)
    driver.quit()
    exit()

print("Extracting group members...")
# Extract the member list
try:
    members_panel = WebDriverWait(driver, waitTime).until(
        #EC.presence_of_element_located((By.XPATH, '//div[contains(@aria-label, "Group members")]'))
        EC.presence_of_element_located((By.XPATH, '//*[@id="app"]/div/span[2]/div/span/div/div/div/div/div/div/header/div/div[2]/h1'))
    )
    members = members_panel.find_elements(By.XPATH, './/div[@role="button"]//span[@dir="auto"]')
    member_list = [member.text for member in members if member.text.strip()]

    # Print the member list
    print("Group Members:")
    for member in member_list:
        print(member)
except:
    print("No members found or unable to extract member list!")


sleep(30)
# Close the driver
driver.quit()