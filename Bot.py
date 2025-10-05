"""
Step 1: Automated Login Bot
This script demonstrates how to automatically log into a website using Selenium.
"""

import os
import sys
import threading

import time
from datetime import datetime
import schedule

import json

from dotenv import load_dotenv

from selenium import webdriver
from selenium.webdriver.chrome.options import Options

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager


class Bot:
    """A simple bot that demonstrates automated login."""
    
    def __init__(self, headless):
        """
        Initialize the bot.
        Always runs in headless mode (no GUI).
        """
        self.driver = None
        self.headless = headless
        self.wait_timeout = 120
        
        # Load .env file
        self.info = self.load_info()
        
        # Load config.json file
        config = self.load_config()
        self.event = config["Event"]
        self.dietary = config["Dietary"]

        print(f"Event: {self.event}")
        print(f"Dietary: {self.dietary}")
        
        self.url = self.info.get('URL', "https://example.com/login")
        self.email = self.info.get('EMAIL', "your_email")  
        self.password = self.info.get('PASSWORD', "your_password")

        print(f"✅ URL: {self.url}")
        print(f"✅ Email: {self.email}")
        print(f"✅ Password: {'*' * len(self.password) if self.password else 'Not Set'}")
    
    def load_config(self):
        config = {}
        with open('config.json', 'r', encoding='utf-8') as f:
            config = json.load(f)
        return config
        
    def load_info(self):
        info = {}
        load_dotenv()

        info = {
            'EMAIL': os.getenv('EMAIL'),
            'PASSWORD': os.getenv('PASSWORD'), 
            'URL': os.getenv('URL'),
        }
        
        # Check required configurations
        if not info['EMAIL'] or not info['PASSWORD']:
            raise RuntimeError("❌ Missing EMAIL or PASSWORD in .env file.")

        else:
            print(f"Load .env successful")
            print()
        
        return info
    
    def setup_browser(self):
        """Set up the Chrome browser with appropriate options."""
        print("Setting up Chrome browser...")
        
        # Configure Chrome options for headless mode (no GUI)
        chrome_options = Options()
        if self.headless:
            chrome_options.add_argument('--headless')  # no GUI
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')  # Disable GPU acceleration
        chrome_options.add_argument('--window-size=1920,1080')
        
        try:
            # Automatically download and set up ChromeDriver
            self.driver = webdriver.Chrome(options=chrome_options)

            
            # Set up wait object for waiting for elements
            self.wait = WebDriverWait(self.driver, self.wait_timeout)
            
            print("✓ Browser set up successfully!")
            return True
            
        except Exception as e:
            print(f"✗ Failed to set up browser: {e}")
            return False
    
    def connect_to_website(self):
        """Navigate to NTU SoC page."""
        try:
            print(f"Navigating to page: {self.url}")
            self.driver.get(self.url)
            
            # Wait for the page to load
            print("✓ Successfully navigated to NTU SoC page!")
            return True
            
        except Exception as e:
            print(f"✗ Failed to navigate to NTU SoC page: {e}")
            return False
    
    def find_login_elements(self):
        """
        Find the login form elements on the page.
        """
        try:
            print("Looking for login form elements...")
            email_input = self.wait.until(EC.element_to_be_clickable((By.ID, "login_email")))
            password_input = self.wait.until(EC.element_to_be_clickable((By.ID, "login_pw")))
            modal_login_btn = self.driver.find_element(By.XPATH, "//div[@class='modal-footer']//button[contains(@class, 'btn-primary') and contains(text(), '登入')]")

            print("✓ Found login form elements!")
            return email_input, password_input, modal_login_btn

        except Exception as e:
            print(f"✗ Error finding login elements: {e}")
            return None, None, None
    
    def fill_login_form(self, email_input, password_input):
        """Fill in the username and password fields."""
        try:
            print("Filling in login credentials...")
            
            # Clear any existing text and enter username
            email_input.clear()
            email_input.send_keys(self.email)
            print("✓ Email entered")
            
            # Clear any existing text and enter password
            password_input.clear()
            password_input.send_keys(self.password)
            print("✓ Password entered")
            
            return True
            
        except Exception as e:
            print(f"✗ Error filling login form: {e}")
            return False
    
    def submit_login(self, login_button):
        """Click the login button to submit the form."""
        try:
            print("Submitting login form...")
            login_button.click()

            print("✓ Login form submitted!")
            return True
            
        except Exception as e:
            print(f"✗ Error submitting login: {e}")
            return False
    
    def find_activity_event(self):
        """Find the activity event element after login."""
        try:
            print("Looking for activity event element...")
            card = self.wait.until(EC.element_to_be_clickable((By.XPATH, f"//div[@class='topcolbox ng-binding' and contains(text(), '{self.event}')]")))
            card.click()
            print("✓ Found activity event element!")
            return True
        except Exception as e:
            print(f"✗ Error finding activity event element: {e}")
            return False
        
    def select_meal_preference(self):
        """Select meal preference from dropdown."""
        try:
            print("Finding Registration Button")
            
            try:
                register_btn = self.wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(@class, 'btn-success') and contains(text(), '我要報名現場參加')]")))
                register_btn.click()
                self.capture_page_state(step_name="after_event_selection", save_screenshot=True, save_html=True)
                time.sleep(10)
                self.capture_page_state(step_name="after_registration_click", save_screenshot=True, save_html=True)

            except TimeoutException:
                print("✗ Registration button not found or not clickable.")
                return False

            print("Selecting meal preference...")
            
            print("✓ Meal preference selected!")
            return True
        except Exception as e:
            print(f"✗ Error selecting meal preference: {e}")
            return False
        
    def action(self):
        print("🤖 Start login process...")
        print("=" * 50)
        
        Check = False

        # Step 1: Set up browser
        if not self.setup_browser():
            return False
        try:
            # Step 2: Navigate to login page
            if not self.connect_to_website():
                return False
            
            login_btn = self.wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button.btn.btn-primary[data-target='#loginpanel']")))
            login_btn.click()
            print("✓ Clicked login button to open login form")
            
            # Step 3: Find login form elements
            email_input, password_input, modal_login_btn = self.find_login_elements()
            if not all([email_input, password_input, modal_login_btn]):
                print("Missing login form elements, cannot proceed.")
                return False
            
            # Step 4: Fill in credentials
            if not self.fill_login_form(email_input, password_input):
                return False
            
            # Step 5: Submit the form
            if not self.submit_login(modal_login_btn):
                return False
            
            print("\n🎉 LOGIN SUCCESSFUL!")

            # Wait for loading overlay to disappear
            self.wait.until(EC.invisibility_of_element_located((By.CSS_SELECTOR, ".loader")))

            # Step 6: Find the activity event element
            if not self.find_activity_event():
                return False

            # Step 7: Select Meal Preference
            Check = self.select_meal_preference()
            if not Check:
                return False


        except Exception as e:
            print(f"\n💥 Unexpected error during login: {e}")
            return False
        
        finally:
            self.close_browser()
            return Check
    
    def get_page_html(self, filename_prefix="page_html", save_to_file=True):
        """
        Get the current page's HTML content.
        
        Args:
            filename_prefix (str): Prefix for the HTML file name
            save_to_file (bool): Whether to save HTML to file
            
        Returns:
            str: The complete HTML source of the current page
        """
        try:
            if not self.driver:
                print("✗ Browser driver not initialized")
                return None
                
            # Get the complete HTML source
            html_content = self.driver.page_source
            
            if save_to_file:
                # Create timestamp for unique filename
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"{filename_prefix}_{timestamp}.html"
                
                # Save HTML to file
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(html_content)
                
                print(f"✓ Page HTML saved to: {filename}")
                print(f"✓ HTML content length: {len(html_content)} characters")
            
            return html_content
            
        except Exception as e:
            print(f"✗ Error getting page HTML: {e}")
            return None
    
    def capture_page_state(self, step_name="unknown", save_screenshot=True, save_html=True):
        """
        Capture the current page state (HTML + screenshot if needed).
        
        Args:
            step_name (str): Name of the current step for file naming
        """
        try:
            print(f"📸 Capturing page state for step: {step_name}")
            
            # Get HTML content
            html_content = self.get_page_html(f"step_{step_name}", save_to_file=save_html)
            
            # Optionally take a screenshot
            if not self.headless and save_screenshot:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                screenshot_filename = f"screenshot_{step_name}_{timestamp}.png"
                self.driver.save_screenshot(screenshot_filename)
                print(f"✓ Screenshot saved to: {screenshot_filename}")
            
            return html_content
            
        except Exception as e:
            print(f"✗ Error capturing page state: {e}")
            return None

    def close_browser(self):
        """Close the browser and clean up."""
        if self.driver:
            try:
                self.driver.quit()
                print("✓ Browser closed successfully")
            except Exception as e:
                print(f"Warning: Error closing browser: {e}")


def job():
    """Main function to run the bot."""
    print("Start to Login")
    print("=" * 50)
    
    # IMPORTANT: Update these values before running!
    print("⚠️  BEFORE RUNNING:")
    print("1. Update URL in the .env file")
    print("2. Update username and password")
    print()
    
    # Create and run the bot (headless mode - no GUI)
    bot = Bot(headless=False)
    
    success = bot.action()
    
    if success:
        print("\n✅ Register successfully!\n")
    else:
        print("\n❌ Failed. Check the error messages above.\n")

def multi_thread_run(num_bots=3):
    def run_bot_instance():
        bot = Bot(headless=False)
        bot.action()

    threads = []
    for _ in range(num_bots):
        t = threading.Thread(target=run_bot_instance)
        t.start()
        threads.append(t)

    for t in threads:
        t.join()

if __name__ == "__main__":
    target_time = ""
    with open('config.json', 'r', encoding='utf-8') as f:
        target_time = json.load(f)["Time"]
    print(f"Target Time from config.json: {target_time}")

    while True:
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if now >= target_time:
            # Single thread
            job()

            # Multi-threaded example
            # multi_thread_run(num_bots=3)

            break
        time.sleep(1)
        print(now, end="\r", flush=True)

