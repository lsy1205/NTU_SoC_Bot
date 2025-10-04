"""
Step 1: Automated Login Bot
This script demonstrates how to automatically log into a website using Selenium.
"""

import os
import time
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
        self.headless = headless  # 始终使用headless模式
        self.wait_timeout = 10
        
        # Load configuration from .env file
        self.config = self.load_config()
        
        self.url = self.config.get('URL', "https://example.com/login")
        self.email = self.config.get('EMAIL', "your_email")  
        self.password = self.config.get('PASSWORD', "your_password")

        print(f"✅ URL: {self.url}")
        print(f"✅ Email: {self.email}")
        print(f"✅ Password: {'*' * len(self.password) if self.password else 'Not Set'}")
    
    def load_config(self):
        config = {}
        load_dotenv()

        config = {
            'EMAIL': os.getenv('EMAIL'),
            'PASSWORD': os.getenv('PASSWORD'), 
            'URL': os.getenv('URL'),
        }
        
        # Check required configurations
        if not config['EMAIL'] or not config['PASSWORD']:
            raise RuntimeError("❌ Missing EMAIL or PASSWORD in .env file.")

        else:
            print(f"Load .env successful")
            print()
        
        return config
    
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
    
    def action(self):
        print("🤖 Start login process...")
        print("=" * 50)
        
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



        except Exception as e:
            print(f"\n💥 Unexpected error during login: {e}")
            return False
        
        finally:
            self.close_browser()
            return True
    
    def close_browser(self):
        """Close the browser and clean up."""
        if self.driver:
            try:
                self.driver.quit()
                print("✓ Browser closed successfully")
            except Exception as e:
                print(f"Warning: Error closing browser: {e}")


def main():
    """Main function to run the login bot."""
    print("Start to Login")
    print("=" * 50)
    
    # IMPORTANT: Update these values before running!
    print("⚠️  BEFORE RUNNING:")
    print("1. Update URL in the .env file")
    print("2. Update username and password")
    print()
    
    # Create and run the bot (headless mode - no GUI)
    bot = Bot(headless=True)
    
    success = bot.action()
    
    if success:
        print("\n✅ Login successfully!\n")
    else:
        print("\n❌ Login failed. Check the error messages above.\n")


if __name__ == "__main__":
    main()
