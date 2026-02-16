import time
import subprocess
import shutil
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def get_driver_path():
    """Dynamically finds the chromedriver path."""
    path = shutil.which("chromedriver") or shutil.which("chromium-chromedriver")
    if not path:
        # Check common fallback path
        import os
        fallback = "/usr/lib/chromium-browser/chromedriver"
        if os.path.exists(fallback):
            return fallback
    return path

def setup_driver():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    
    # Real user-agent to prevent being blocked by Google's anti-bot
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
    # Find the driver path
    driver_path = get_driver_path()
    if not driver_path:
        print("[ERROR] Could not find chromedriver. Ensure chromium-chromedriver is installed.")
        return None
    
    print(f"Using driver found at: {driver_path}")
    service = Service(driver_path)
    
    try:
        driver = webdriver.Chrome(service=service, options=chrome_options)
        return driver
    except Exception as e:
        print(f"\n[FATAL] Chrome failed to start: {e}")
        return None

def scan_issue(driver, issue_id):
    url = f"https://issuetracker.google.com/issues/{issue_id}"
    print(f"Scanning Issue {issue_id}...", end="\r")
    
    try:
        driver.get(url)
        
        # Wait for the issue title to load
        wait = WebDriverWait(driver, 20)
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "issue-view, .issue-title")))
        
        # Expand "show quoted text" (the dots) to see hidden content
        # Buganizer often uses dots (...) for this
        try:
            expand_buttons = driver.find_elements(By.CSS_SELECTOR, ".show-quoted-text-link, [aria-label*='quoted text']")
            for btn in expand_buttons:
                driver.execute_script("arguments[0].click();", btn)
            time.sleep(1) # wait for expansion
        except:
            pass

        # Search the entire page source for the keyword
        full_content = driver.page_source.lower()
        
        if "buganizer" in full_content:
            title = driver.title.replace(" - Issue Tracker", "").strip()
            return {"id": issue_id, "title": title, "match": True}
        
        return {"id": issue_id, "match": False}

    except Exception as e:
        return {"id": issue_id, "error": str(e)}

def main():
    ids_input = input("Enter Report IDs (comma-separated): ")
    ids = [i.strip() for i in ids_input.split(",") if i.strip()]
    
    driver = setup_driver()
    if not driver: return

    try:
        print(f"\n{'ID':<15} | {'Match?':<8} | {'Title'}")
        print("-" * 60)
        for eid in ids:
            res = scan_issue(driver, eid)
            if res.get("match"):
                print(f"{res['id']:<15} | YES      | {res['title']}")
            elif "error" in res:
                print(f"{res['id']:<15} | ERROR    | {res['error'][:30]}")
            else:
                print(f"{res['id']:<15} | NO       | ---")
    finally:
        driver.quit()

if __name__ == "__main__":
    main()
