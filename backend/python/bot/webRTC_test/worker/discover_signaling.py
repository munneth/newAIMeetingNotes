# discover_signaling.py
from playwright.sync_api import sync_playwright
import json
import sys, time

MEET_LINK = sys.argv[1] if len(sys.argv) > 1 else None
if not MEET_LINK:
    print("Usage: python discover_signaling.py https://meet.google.com/xxxxx")
    sys.exit(1)

with sync_playwright() as p:
    browser = p.chromium.launch_persistent_context(user_data_dir="/tmp/meet_profile_local", headless=False)
    page = browser.new_page()
    captured = []

    def on_request(req):
        try:
            # inspect XHRs
            if req.resource_type == "xhr" or req.url.startswith("https://") and "meet" in req.url:
                # We record requests with json bodies if present
                payload = req.post_data or ""
                captured.append({
                    "url": req.url,
                    "method": req.method,
                    "headers": dict(req.headers),
                    "post_data": payload[:5000]  # truncate for safety
                })
        except Exception as e:
            print("req hook err", e)

    page.on("request", on_request)
    page.goto(MEET_LINK)
    print("Open the Meet join flow manually in the opened browser window. When you click 'Join', the script will capture XHR calls.")
    # wait for user action
    time.sleep(60)  # give you time to click 'Join' and let requests be made

    # write captured requests to file
    with open("captured_signaling.json", "w") as f:
        json.dump(captured, f, indent=2)

    print("Captured requests written to captured_signaling.json — inspect this file for the join POST that contains SDP/ICE.")
    browser.close()
