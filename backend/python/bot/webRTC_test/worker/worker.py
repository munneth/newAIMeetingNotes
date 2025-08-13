# worker.py
import redis
import json
import os
import time
import asyncio
from playwright.sync_api import sync_playwright
from aiortc import RTCPeerConnection, RTCSessionDescription
from aiortc.contrib.media import MediaRecorder

# -----------------------------
# Configuration
# -----------------------------
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
r = redis.from_url(REDIS_URL)

OFFER_PATH = "/tmp/offer.sdp"
ANSWER_PATH = "/tmp/answer.sdp"

# -----------------------------
# Storage state handling
# -----------------------------
def _apply_storage_state_to_persistent_context(context, storage_state):
    """
    Apply cookies and localStorage from a Playwright storage_state.
    Accepts either JSON string, dict, or path to a JSON file.
    """
    if not storage_state:
        print("No storage_state provided, cannot sign in")
        return

    if os.path.exists(storage_state):
        try:
            with open(storage_state, "r", encoding="utf-8") as f:
                state = json.load(f)
        except Exception as e:
            print("Failed to read storage_state file:", e)
            return
    elif isinstance(storage_state, str):
        try:
            state = json.loads(storage_state)
        except Exception as e:
            print("Failed to parse storage_state string:", e)
            return
    else:
        state = storage_state

    cookies = state.get("cookies") or []
    if cookies:
        context.add_cookies(cookies)
        print(f"Applied {len(cookies)} cookies")

    origins = state.get("origins") or []
    for origin_entry in origins:
        origin = origin_entry.get("origin")
        local_storage = origin_entry.get("localStorage", [])
        if not origin:
            continue
        page_tmp = context.new_page()
        page_tmp.goto(origin, wait_until="domcontentloaded")
        for item in local_storage:
            key = item.get("name")
            val = item.get("value")
            if key is not None and val is not None:
                page_tmp.evaluate(
                    """([k,v]) => { try { localStorage.setItem(k,v); } catch(e) {} }""",
                    [key, val]
                )
        page_tmp.close()
    print("Applied storage_state successfully")

# -----------------------------
# Capture Google Meet offer
# -----------------------------
def capture_offer_with_playwright(meet_link, storage_state=None, timeout=180):
    with sync_playwright() as p:
        user_data_dir = "/tmp/meet_profile"

        context = p.chromium.launch_persistent_context(
            user_data_dir=user_data_dir,
            headless=False,
            args=[
                "--use-fake-ui-for-media-stream",
                "--use-fake-device-for-media-stream",
                "--no-sandbox",
                "--disable-dev-shm-usage",
                "--enable-logging",
            ],
        )

        _apply_storage_state_to_persistent_context(context, storage_state)
        page = context.new_page()

        # Warm up cookies by visiting Google Accounts
        try:
            page.goto("https://accounts.google.com/", wait_until="domcontentloaded")
            print("Visited Google Accounts page to warm up cookies")
        except Exception as e:
            print("Could not visit Google Accounts:", e)

        # Inject JS to capture SDP offer
        hook_js = """
        (function() {
            const PC = window.RTCPeerConnection || window.webkitRTCPeerConnection;
            if (!PC) return;
            const origSetRemote = PC.prototype && PC.prototype.setRemoteDescription;
            if (!origSetRemote) return;

            if (!window.__meet_hook_installed) {
                window.__meet_hook_installed = true;
                window.__captured_offer = null;

                PC.prototype.setRemoteDescription = function(desc) {
                    try {
                        if (desc && desc.type === 'offer' && desc.sdp) {
                            window.__captured_offer = { sdp: desc.sdp, type: 'offer' };
                            try { console.debug('MeetHook: captured offer'); } catch(_) {}
                        }
                    } catch (e) {
                        try { console.error('MeetHook error', e); } catch(_) {}
                    }
                    return origSetRemote.apply(this, arguments);
                };
            }
        })();
        """
        context.add_init_script(hook_js)
        page.set_default_timeout(timeout * 1000)

        signaling_calls = []

        def on_request(req):
            try:
                if any(x in req.url for x in ["securetoken", "v1/meet", "join", "screencast"]):
                    signaling_calls.append({
                        "url": req.url,
                        "method": req.method,
                        "headers": dict(req.headers),
                        "post_data": req.post_data
                    })
            except Exception:
                pass

        page.on("request", on_request)

        # Navigate to Meet
        page.goto(meet_link, wait_until="domcontentloaded")

        # Debug save
        try:
            page.screenshot(path="/tmp/debug_meet_page.png")
            html = page.content()
            with open("/tmp/debug_meet_page.html", "w", encoding="utf-8") as f:
                f.write(html)
            print("Saved debug screenshot and HTML of meeting page")
        except Exception as e:
            print("Failed to save debug page info:", e)

        # Wait for and click 'Ask to join' or 'Join now'
        try:
            button = page.wait_for_selector('button:has-text("Ask to join")', timeout=60000)
            button.click()
            print("Ask to join button appeared and clicked")
            page.wait_for_timeout(5000)  # wait 5s after click
        except Exception:
            try:
                button = page.wait_for_selector('button:has-text("Join now")', timeout=60000)
                button.click()
                print("Join now button appeared and clicked")
                page.wait_for_timeout(5000)
            except Exception:
                print("No 'Ask to join' or 'Join now' button found; continuing")

        # Wait for offer capture
        offer = None
        start = time.time()
        while time.time() - start < timeout:
            try:
                offer = page.evaluate("() => window.__captured_offer && window.__captured_offer.sdp")
            except Exception:
                offer = None
            if offer:
                break
            time.sleep(0.5)

        try:
            cookies = context.cookies()
        except Exception:
            cookies = []
        try:
            storage = context.storage_state()
        except Exception:
            storage = None

        context.close()

        return offer, {
            "signaling_candidates": signaling_calls,
            "cookies": cookies,
            "storage_state": storage
        }

# -----------------------------
# WebRTC answer creation
# -----------------------------
async def create_answer_sdp(offer_sdp_text, save_audio_to=None):
    pc = RTCPeerConnection()
    recorder = None
    if save_audio_to:
        recorder = MediaRecorder(save_audio_to)

    @pc.on("track")
    def on_track(track):
        print("Received track:", track.kind)
        if recorder:
            recorder.addTrack(track)

        @track.on("ended")
        async def _ended():
            print("Track ended")

    offer = RTCSessionDescription(sdp=offer_sdp_text, type="offer")
    await pc.setRemoteDescription(offer)
    answer = await pc.createAnswer()
    await pc.setLocalDescription(answer)
    await asyncio.sleep(1.0)
    if recorder:
        await recorder.start()

    return pc.localDescription.sdp, pc, recorder

# -----------------------------
# Dummy signaling handler
# -----------------------------
def send_answer_via_signaling(signaling_meta, answer_sdp):
    print("Captured signaling calls (first 5):")
    for c in signaling_meta.get("signaling_candidates", [])[:5]:
        print(c["method"], c["url"])

    example_url = None
    for c in signaling_meta.get("signaling_candidates", []):
        if c["method"].upper() == "POST" and "join" in c["url"]:
            example_url = c["url"]
            break

    if not example_url:
        print("No obvious join POST found; examine signaling_candidates above.")
        return False

    print("You should POST the answer to:", example_url)
    print("Construct a body JSON matching the original payload but replace offer SDP with the answer.")
    return True

# -----------------------------
# Worker loop
# -----------------------------
def worker_loop():
    print("Worker starting — polling Redis for jobs...")
    while True:
        _, payload = r.blpop("meet_jobs")  # blocking pop
        job = json.loads(payload)
        try:
            print("Picked job:", job.get("job_id"))
            meet_link = job["meet_link"]
            storage_state = job.get("profile_storage_state")

            offer_sdp, meta = capture_offer_with_playwright(
                meet_link, storage_state=storage_state, timeout=180
            )
            if not offer_sdp:
                print("Failed to capture offer; skipping job")
                continue

            with open(OFFER_PATH, "w") as f:
                f.write(offer_sdp)

            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            answer_sdp, pc, recorder = loop.run_until_complete(
                create_answer_sdp(offer_sdp, save_audio_to="/tmp/meeting_audio.mp4")
            )
            with open(ANSWER_PATH, "w") as f:
                f.write(answer_sdp)

            ok = send_answer_via_signaling(meta, answer_sdp)
            if not ok:
                print("Could not automatically POST answer - manual reverse engineering needed.")
            else:
                print("Answer POSTed (theoretically). Waiting for tracks and processing audio.")
                time.sleep(30)
                loop.run_until_complete(pc.close())
                if recorder:
                    loop.run_until_complete(recorder.stop())

            print("Job complete")

        except Exception as exc:
            print("Worker error:", exc)
            continue

# -----------------------------
# Entry point
# -----------------------------
if __name__ == "__main__":
    worker_loop()
