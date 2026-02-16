import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def setup_driver():
    """Heavy-duty configuration for Cloud/Linux environments."""
    chrome_options = Options()
    
    # Critical flags for Cloud Environments
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--remote-debugging-port=9222")
    
    # Identifying as a real user
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
    # Path settings for standard Linux installations
    chrome_options.binary_location = "/usr/bin/chromium-browser"
    
    # Point directly to the driver installed via apt-get
    service = Service("/usr/lib/chromium-browser/chromedriver")
    
    try:
        driver = webdriver.Chrome(service=service, options=chrome_options)
        return driver
    except Exception as e:
        print(f"\n[FATAL] Chrome failed to start: {e}")
        return None

def scan_issue(driver, issue_id):
    url = f"https://issuetracker.google.com/issues/{issue_id}"
    print(f"Checking ID: {issue_id}...", end="\r")
    
    try:
        driver.get(url)
        
        # Wait for content to render
        wait = WebDriverWait(driver, 20)
        wait.until(EC.presence_of_element_located((By.TAG_NAME, "issue-view")))
        
        # Click "show quoted text" to find keywords hidden in thread replies
        quoted_buttons = driver.find_elements(By.CSS_SELECTOR, ".show-quoted-text-link")
        for btn in quoted_buttons:
            try:
                driver.execute_script("arguments[0].click();", btn)
            except:
                continue 
        
        time.sleep(2) # Allow expansion
        
        # Check both the visible text and the raw HTML for the keyword
        page_source = driver.page_source.lower()
        visible_text = driver.find_element(By.TAG_NAME, "body").text.lower()
        
        if "buganizer" in visible_text or "buganizer" in page_source:
            title = driver.title.replace(" - Issue Tracker", "").strip()
            return {"id": issue_id, "title": title, "match": True}
        
        return {"id": issue_id, "match": False}

    except Exception as e:
        return {"id": issue_id, "error": str(e)}

def main():
    print("--- Buganizer Scanner (Cloud Optimized) ---")
    ids_input = input("Enter Report IDs (comma-separated): ")
    ids = [i.strip() for i in ids_input.split(",") if i.strip()]
    
    driver = setup_driver()
    if not driver:
        return

    results = []
    try:
        for eid in ids:
            result = scan_issue(driver, eid)
            results.append(result)
            
        print("\n" + "="*70)
        print(f"{'Report ID':<15} | {'Found?':<8} | {'Title'}")
        print("-" * 70)
        
        for res in results:
            if "error" in res:
                print(f"{res['id']:<15} | ERROR    | {res['error'][:40]}...")
            elif res["match"]:
                print(f"{res['id']:<15} | YES      | {res['title']}")
            else:
                print(f"{res['id']:<15} | NO       | (Keyword not found)")
                
    finally:
        if driver:
            driver.quit()

if __name__ == "__main__":
    main()
