from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)  # headless=False lets you see the browser
    context = browser.new_context(storage_state="storage_state.json")
    page = context.new_page()

    # Go to Google Meet
    page.goto("https://meet.google.com")

    # Wait a few seconds to see if logged in
    page.wait_for_timeout(5000)  # 5 seconds

    # Take a screenshot to confirm login
    page.screenshot(path="meet_test.png")

    print("Check meet_test.png to see if you are logged in!")

    browser.close()
