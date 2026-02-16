import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

def setup_driver():
    """Configures Selenium to work in a Linux/Cloud environment."""
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Required for cloud environments
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
    # Path for Chromium in most Linux/Colab environments
    chrome_options.binary_location = "/usr/bin/chromium-browser"

    try:
        # Attempt to use the system's chromedriver
        service = Service("/usr/lib/chromium-browser/chromedriver")
        driver = webdriver.Chrome(service=service, options=chrome_options)
    except Exception:
        # Fallback to auto-installer if system path fails
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
    return driver

def scan_issue(driver, issue_id):
    """Navigates to the issue, expands hidden text, and searches for keywords."""
    url = f"https://issuetracker.google.com/issues/{issue_id}"
    print(f"Checking ID: {issue_id}...", end="\r")
    
    try:
        driver.get(url)
        
        # Wait for the main issue content to load
        wait = WebDriverWait(driver, 15)
        wait.until(EC.presence_of_element_located((By.TAG_NAME, "issue-view")))
        
        # Look for all 'show quoted text' buttons and click them
        # This ensures we search inside the hidden sections you mentioned
        quoted_buttons = driver.find_elements(By.CSS_SELECTOR, ".show-quoted-text-link")
        for btn in quoted_buttons:
            try:
                driver.execute_script("arguments[0].click();", btn)
            except:
                continue 
        
        # Brief pause to allow text expansion
        time.sleep(1.5)
        
        # Get all text from the page
        page_text = driver.find_element(By.TAG_NAME, "body").text.lower()
        
        if "buganizer" in page_text:
            # Extract the page title (usually contains the bug summary)
            title = driver.title.replace(" - Issue Tracker", "").strip()
            return {"id": issue_id, "title": title, "match": True}
        
        return {"id": issue_id, "match": False}

    except Exception as e:
        return {"id": issue_id, "error": str(e)}

def main():
    print("--- Google Issue Tracker 'Buganizer' Scanner ---")
    ids_input = input("Enter Report IDs separated by commas: ")
    ids = [i.strip() for i in ids_input.split(",") if i.strip()]
    
    if not ids:
        print("No IDs provided. Exiting.")
        return

    driver = setup_driver()
    results = []

    try:
        for eid in ids:
            result = scan_issue(driver, eid)
            results.append(result)
            
        print("\n\nScan Results:")
        print("=" * 70)
        print(f"{'Report ID':<15} | {'Match':<10} | {'Title'}")
        print("-" * 70)
        
        for res in results:
            if "error" in res:
                print(f"{res['id']:<15} | ERROR      | {res['error'][:50]}...")
            elif res["match"]:
                print(f"{res['id']:<15} | [YES]      | {res['title']}")
            else:
                print(f"{res['id']:<15} | [NO]       | Keyword not found.")
                
    finally:
        driver.quit()

if __name__ == "__main__":
    main()
