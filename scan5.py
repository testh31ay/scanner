import time
import shutil
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def setup_driver():
    chrome_options = Options()
    
    # These flags are non-negotiable for Cloud/Linux environments
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--remote-debugging-port=9222")
    
    # Mimic a real browser to avoid being flagged as a bot
    chrome_options.add_argument("user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
    # Force the binary location
    chrome_options.binary_location = "/usr/bin/chromium-browser"
    
    # Point to the driver
    driver_path = "/usr/bin/chromedriver"
    service = Service(driver_path)
    
    try:
        driver = webdriver.Chrome(service=service, options=chrome_options)
        return driver
    except Exception as e:
        print(f"\n[FATAL] Chrome failed to start: {e}")
        print("\nTIP: Ensure you ran '!apt-get install -y chromium-browser chromium-chromedriver' first.")
        return None

def scan_issue(driver, issue_id):
    url = f"https://issuetracker.google.com/issues/{issue_id}"
    print(f"Scanning Issue {issue_id}...", end="\r")
    
    try:
        driver.get(url)
        
        # Wait for the issue page to render (up to 20 seconds)
        wait = WebDriverWait(driver, 20)
        wait.until(EC.presence_of_element_located((By.TAG_NAME, "issue-view")))
        
        # Action: Click all 'show quoted text' buttons to reveal hidden "buganizer" keywords
        try:
            # We use JS click because it's more reliable for hidden elements
            driver.execute_script("""
                let buttons = document.querySelectorAll('.show-quoted-text-link, [aria-label*="quoted text"]');
                buttons.forEach(btn => btn.click());
            """)
            time.sleep(2) # Wait for text to expand
        except:
            pass

        # Capture both raw source and visible text
        content = driver.page_source.lower()
        
        if "buganizer" in content:
            title = driver.title.replace(" - Issue Tracker", "").strip()
            return {"id": issue_id, "title": title, "match": True}
        
        return {"id": issue_id, "match": False}

    except Exception as e:
        return {"id": issue_id, "error": str(e)}

def main():
    ids_input = input("Enter Report IDs (e.g., 484730419): ")
    ids = [i.strip() for i in ids_input.split(",") if i.strip()]
    
    driver = setup_driver()
    if not driver: return

    try:
        print(f"\n{'ID':<15} | {'Match?':<8} | {'Title'}")
        print("-" * 70)
        for eid in ids:
            res = scan_issue(driver, eid)
            if res.get("match"):
                print(f"{res['id']:<15} | YES      | {res['title']}")
            elif "error" in res:
                # Truncate error for cleaner output
                err_msg = str(res['error'])[:40]
                print(f"{res['id']:<15} | ERROR    | {err_msg}...")
            else:
                print(f"{res['id']:<15} | NO       | (Keyword not found)")
    finally:
        driver.quit()

if __name__ == "__main__":
    main()
