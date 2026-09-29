from config import COURSES, WEBHOOKS, IST_BLUE
import time

POST_TIMEOUT = 15
RETRY_BASE = 5.0


def _truncate(text, limit=300):
    text = str(text or "")
    return text[:limit] + "..." if len(text) > limit else text


def build_payload(entry, course_name):
    course_data = COURSES.get(course_name, {"role_id": None, "webhooks": []})
    role_id = course_data.get("role_id")
    mention = f"<@&{role_id}>" if role_id else ""

    if entry.get("summary"):
        description = _truncate(entry["summary"], 300)
    elif entry.get("published"):
        description = (f"{entry['published']} — full text visible to "
                       f"logged-in Fénix users only.")
    else:
        description = "New announcement — open the link for details."

    return {
        "content": f"🚨 **Acordem, dropou anúncio de {course_name}** {mention}:",
        "embeds": [{
            "title": _truncate(entry["title"], 256),
            "url": entry["link"],
            "description": description,
            "color": IST_BLUE,
            "footer": {"text": "Tele com capa de Gatinho | CMTV"},
        }],
    }



def post_to_discord(entry, course_name, session):
    course_data = COURSES.get(course_name, {"role_id": None, "webhooks": []})
    payload = build_payload(entry, course_name)

    ok = True
    for name in course_data.get("webhooks", []):
        url = WEBHOOKS.get(name)
        if not url:
            print(f"Webhook {name!r} not configured in .env — skipping")
            ok = False
            continue
        try:
            r = session.post(url, json=payload, timeout=POST_TIMEOUT)
            if r.status_code == 429:
                try:
                    retry_after = float(r.json().get("retry_after", RETRY_BASE)) + 0.5
                except Exception:
                    retry_after = RETRY_BASE + 0.5
                time.sleep(retry_after)
                r = session.post(url, json=payload, timeout=POST_TIMEOUT)
            r.raise_for_status()
            time.sleep(1.0)   
        except Exception as e:
            print(f"Error posting to {name}: {e}")
            ok = False
    return ok
