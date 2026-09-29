import argparse
import time
import requests

import fenix
from fenix import AuthError, GatedError
from config import (
    COURSES, FETCH_INTERVAL,
    FENIX_USERNAME, FENIX_PASSWORD, DRY_RUN, SEED_SEEN,
    HEALTHCHECK_URL,
)
from database import GUIDTracker
from notifier import post_to_discord


class Bot:
    def __init__(self):
        self.db = GUIDTracker()
        self.session = requests.Session()
        self.session.headers["User-Agent"] = "ist-announcements-webhook/2.0"
        self.session.headers["Connection"] = "close"
        self.authed = False

    def ensure_auth(self):
        if not FENIX_USERNAME or self.authed:
            return self.authed
        try:
            fenix.login(self.session, FENIX_USERNAME, FENIX_PASSWORD)
        except AuthError as e:
            print(f"Fenix login failed: {e}")
            return False
        self.authed = True
        print("Fenix login OK")
        return True

    def enrich(self, entry):
        
        if entry.get("summary") or not self.ensure_auth():
            return entry
        try:
            body = fenix.fetch_body(self.session, entry["link"])
        except GatedError:
            print("Session gated, re-logging in")
            self.authed = False
            if not self.ensure_auth():
                return entry
            try:
                body = fenix.fetch_body(self.session, entry["link"])
            except GatedError:
                return entry
        if body:
            entry = {**entry, "summary": body}
        return entry

    def process_entry(self, entry, course):
        guid = entry["guid"]
        if not self.db.is_new(guid):
            return False
        entry = self.enrich(entry)
        if DRY_RUN or SEED_SEEN:
            print(f"[{course}] {entry['title']} ({guid})")
        else:
            if not post_to_discord(entry, course, self.session):
                return False  
        if not DRY_RUN:
            self.db.add(guid)
        return True

    def sweep(self):
        posted = 0
        for course, info in COURSES.items():
            url = info["url"]
            try:
                entries = fenix.fetch_listing(url, self.session)
            except Exception as e:
                print(f"Error fetching {url}: {e}")
                continue
            for entry in reversed(entries):
                try:
                    if self.process_entry(entry, course):
                        posted += 1
                except Exception as e:
                    print(f"Error processing {entry.get('guid')}: {e}")
        if HEALTHCHECK_URL:
            try:
                requests.get(HEALTHCHECK_URL, timeout=10)
            except Exception as e:
                print(f"Healthcheck ping failed: {e}")
        return posted
        
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--once", action="store_true")
    args = parser.parse_args()

    bot = Bot()

    if FENIX_USERNAME and not bot.ensure_auth():
        print("Cannot start without Fenix auth.")
        return 2

    mode = " [DRY RUN]" if DRY_RUN else " [SEED SEEN]" if SEED_SEEN else ""
    print(f"Bot Started. Monitoring {len(COURSES)} course pages...{mode}")

    if args.once:
        n = bot.sweep()
        print(f"Sweep complete ({n} new).")
        return 0

    while True:
        n = bot.sweep()
        print(f"Sweep complete ({n} new). Sleeping {FETCH_INTERVAL}s...")
        time.sleep(FETCH_INTERVAL)


if __name__ == "__main__":
    raise SystemExit(main())
