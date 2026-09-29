import logging
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

log = logging.getLogger("istbot")

TIMEOUT = 10
LOGIN_URL = "https://fenix.tecnico.ulisboa.pt/login"
GATE_MARKER = "Este artigo é privado"
SECTION_TITLE = "últimos anúncios"
POST_MARKER = "ver-post"
HEADINGS = ("h1", "h2", "h3", "h4", "h5", "h6")


class AuthError(RuntimeError):
    

class GatedError(RuntimeError):
    


def _is_section_heading(tag):
    return (getattr(tag, "name", None) in HEADINGS
            and SECTION_TITLE in tag.get_text(strip=True).lower())


def _is_credential_form(tag):
    if getattr(tag, "name", None) != "form":
        return False
    names = {i.get("name") for i in tag.find_all("input")}
    return "username" in names and "password" in names


def login(session, username, password):
    try:
        response = session.get(LOGIN_URL, timeout=TIMEOUT)
    except requests.RequestException as e:
        raise AuthError(f"Could not reach Fenix login (network): {e}") from e
    for _ in range(4):
        url, html = response.url, response.text
        soup = BeautifulSoup(html, "html.parser")
        if soup.find(_is_credential_form):
            form = soup.find(_is_credential_form)
            action = urljoin(url, form.get("action") or url)
            payload = {i.get("name"): i.get("value") or ""
                       for i in form.find_all("input") if i.get("name")}
            payload.update(username=username, password=password,
                           _eventId="submit")
            try:
                response = session.post(action, data=payload, timeout=TIMEOUT)
            except requests.RequestException as e:
                raise AuthError(f"CAS login POST failed (network): {e}") from e
            if BeautifulSoup(response.text, "html.parser").find(
                    _is_credential_form):
                raise AuthError("Fenix login failed: credentials rejected")
            log.info("Fenix login OK (user %s)", username)
            return
        next_hop = None
        for link in soup.find_all("a", href=True):
            if "cas/login" in link["href"] or "id.tecnico.ulisboa.pt" in link["href"]:
                next_hop = urljoin(url, link["href"])
                break
        if next_hop is None:
            raise AuthError(f"Login flow stalled at {url} (no CAS link)")
        try:
            response = session.get(next_hop, timeout=TIMEOUT)
        except requests.RequestException as e:
            raise AuthError(f"Login redirect failed (network): {e}") from e
    raise AuthError("Login flow did not reach a credential form in time")


def parse_listing(html, page_url):
    soup = BeautifulSoup(html, "html.parser")
    heading = soup.find(_is_section_heading)
    if heading is None:
        return []
    entries, pending = [], None
    for sibling in heading.next_siblings:
        name = getattr(sibling, "name", None)
        if name in HEADINGS:
            break
        if name is None:
            continue
        for h5 in sibling.find_all("h5") if name != "h5" else [sibling]:
            a = h5.find("a", href=True)
            if not a or POST_MARKER not in a["href"]:
                continue
            if pending is not None:
                entries.append(pending)
            link = urljoin(page_url, a["href"])
            date = h5.find_next_sibling("p")
            pending = {"guid": link, "title": a.get_text(strip=True) or link,
                       "link": link,
                       "published": date.get_text(strip=True) if date else "",
                       "summary": ""}
    if pending is not None:
        entries.append(pending)
    return entries


def fetch_listing(page_url, session):
    response = None
    for attempt in range(2):
        try:
            response = session.get(page_url, timeout=TIMEOUT)
            break
        except requests.RequestException as e:
            if attempt == 0:
                log.debug("Retrying %s after: %s", page_url, e)
                continue
            log.warning("Skipping %s: fetch failed: %s", page_url, e)
            return []
    if response.status_code >= 400:
        log.warning("Skipping %s: HTTP %s", page_url, response.status_code)
        return []
    entries = parse_listing(response.text, page_url)
    if not entries:
        if BeautifulSoup(response.text, "html.parser").find(
                _is_section_heading) is None:
            log.warning("Skipping %s: no 'Últimos anúncios' section "
                        "(page structure may have changed)", page_url)
        else:
            log.debug("No announcements yet on %s", page_url)
    return entries


def parse_body(html):
    soup = BeautifulSoup(html, "html.parser")
    for chrome in soup(["script", "style", "nav", "header", "footer", "aside"]):
        chrome.decompose()
    candidates = []
    if soup.find("article") is not None:
        candidates.append(soup.find("article"))
    for selector in ("main", "[role=main]", ".main-content", ".content"):
        el = soup.select_one(selector)
        if el is not None:
            candidates.append(el)
    if not candidates:
        divs = [d for d in soup.find_all("div")
                if len(d.get_text(strip=True)) > 200]
        if divs:
            candidates.append(max(divs, key=lambda d: len(d.get_text())))
    for el in candidates:
        for meta in el.select("p.small"):
            meta.decompose()
        for heading in el.select("h1, h2, h3, h4, h5, h6"):
            heading.decompose()
        text = " ".join(el.get_text(separator=" ", strip=True).split())
        if len(text) >= 40:
            return text
    return ""


def fetch_body(session, ver_post_url):
    response = None
    for attempt in range(2):
        try:
            response = session.get(ver_post_url, timeout=TIMEOUT)
            break
        except requests.RequestException as e:
            if attempt == 0:
                log.debug("Retrying body fetch %s after: %s",
                          ver_post_url, e)
                continue
            log.debug("Body fetch failed for %s: %s", ver_post_url, e)
            return ""
    if response.status_code >= 400:
        log.debug("Body fetch HTTP %s for %s",
                  response.status_code, ver_post_url)
        return ""
    if GATE_MARKER in response.text:
        raise GatedError(ver_post_url)
    body = parse_body(response.text)
    if not body:
        log.debug("No body parsed from %s (layout changed?)", ver_post_url)
    return body
