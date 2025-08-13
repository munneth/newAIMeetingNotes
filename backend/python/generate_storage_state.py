# save_storage_state.py
from playwright.sync_api import sync_playwright

STORAGE_PATH = "storage_state.json"  # Where the storage state will be saved

def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)  # Must be non-headless for login
        context = browser.new_context()

        page = context.new_page()
        page.goto("https://accounts.google.com/ServiceLogin")

        print("⚡ Log in manually in the opened browser window.")
        input("Press Enter here after logging in…")

        # Save storage state including cookies and localStorage for all visited domains
        context.storage_state(path=STORAGE_PATH)
        print(f"✅ Storage state saved to {STORAGE_PATH}")

        browser.close()

if __name__ == "__main__":
    main()
