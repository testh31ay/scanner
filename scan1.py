from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import time

def setup_driver():
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Runs without a window
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    # Adding a realistic user agent
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=chrome_options)

def scan_issue(driver, issue_id):
    url = f"https://issuetracker.google.com/issues/{issue_id}"
    print(f"Checking ID: {issue_id}...", end="\r")
    
    try:
        driver.get(url)
        
        # Wait up to 10 seconds for the main content to appear
        wait = WebDriverWait(driver, 10)
        wait.until(EC.presence_of_element_located((By.TAG_NAME, "issue-view")))
        
        # Expand any "show quoted text" buttons found in the comments
        quoted_buttons = driver.find_elements(By.CSS_SELECTOR, ".show-quoted-text-link")
        for btn in quoted_buttons:
            try:
                driver.execute_script("arguments[0].click();", btn)
            except:
                pass # Button might not be clickable or already expanded
        
        # Give it a moment to expand
        time.sleep(1)
        
        # Get the full page text
        page_source = driver.page_source.lower()
        full_text = driver.find_element(By.TAG_NAME, "body").text.lower()
        
        if "buganizer-syatem@google.com" in full_text or "buganizer-system@google.com" in page_source:
            # Extract Title
            title = driver.title.replace(" - Issue Tracker", "").strip()
            return {"id": issue_id, "title": title, "match": True}
        
        return {"id": issue_id, "match": False}

    except Exception as e:
        return {"id": issue_id, "error": str(e)}

def main():
    print("--- Advanced Google Issue Tracker Scanner ---")
    ids_input = input("Enter Report IDs separated by commas: ")
    ids = [i.strip() for i in ids_input.split(",")]
    
    driver = setup_driver()
    results = []

    try:
        for eid in ids:
            result = scan_issue(driver, eid)
            results.append(result)
            
        print("\n\nScan Results:")
        print("-" * 60)
        for res in results:
            if "error" in res:
                print(f"ID {res['id']}: Error - {res['error'][:50]}...")
            elif res["match"]:
                print(f"ID {res['id']}: [FOUND BUGANIZER] - {res['title']}")
            else:
                print(f"ID {res['id']}: [NOT FOUND]")
                
    finally:
        driver.quit()

if __name__ == "__main__":
    main()
