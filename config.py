import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

# --- secrets ---
FENIX_USERNAME = os.environ.get("FENIX_USERNAME", "")
FENIX_PASSWORD = os.environ.get("FENIX_PASSWORD", "")

LEIC_WEBHOOK = os.environ.get("LEIC_WEBHOOK", "")
LMAC_WEBHOOK = os.environ.get("LMAC_WEBHOOK", "")
HEALTHCHECK_URL = os.environ.get("HEALTHCHECK_URL", "")
# --- non-secret config ---
DB_FILE = os.environ.get("SEEN_GUIDS_FILE", str(BASE_DIR / "seen_guids.txt"))
FETCH_INTERVAL = int(os.environ.get("FETCH_INTERVAL_SECONDS", "300"))
DRY_RUN = os.environ.get("DRY_RUN") == "1"
SEED_SEEN = os.environ.get("SEED_SEEN") == "1"

IST_BLUE = 0x009DE0

# --- courses ---
# Each entry: url (Fenix course page), role_id (Discord role, or None),
# webhooks (names into WEBHOOKS below).
COURSES = {
    "AL11":             {"url": "https://fenix.tecnico.ulisboa.pt/disciplinas/AL11/2026-2027/1-semestre",             "role_id": "1550996497242259536", "webhooks": ["leic"]},
    "CDI18":            {"url": "https://fenix.tecnico.ulisboa.pt/disciplinas/CDI18/2026-2027/1-semestre",            "role_id": "1497620447724834856", "webhooks": ["leic"]},
    "SO":               {"url": "https://fenix.tecnico.ulisboa.pt/disciplinas/SO/2026-2027/1-semestre",               "role_id": "1550994740265226270", "webhooks": ["leic"]},
    "PO":               {"url": "https://fenix.tecnico.ulisboa.pt/disciplinas/PO/2026-2027/1-semestre",               "role_id": "1550994730106626191", "webhooks": ["leic"]},
    "Fis9":             {"url": "https://fenix.tecnico.ulisboa.pt/disciplinas/Fis9/2026-2027/1-semestre",             "role_id": "1550994631838404689", "webhooks": ["leic"]},
    "CDI17":            {"url": "https://fenix.tecnico.ulisboa.pt/disciplinas/CDI17/2026-2027/1-semestre",            "role_id": "1550993255469023252", "webhooks": ["leic"]},
    "ASA":              {"url": "https://fenix.tecnico.ulisboa.pt/disciplinas/ASA/2026-2027/1-semestre",              "role_id": "1550994770976055407", "webhooks": ["leic"]},
    "CDI14":            {"url": "https://fenix.tecnico.ulisboa.pt/disciplinas/CDI14/2026-2027/1-semestre",            "role_id": "1550993186166415412", "webhooks": ["lmac"]},
    "Ges":              {"url": "https://fenix.tecnico.ulisboa.pt/disciplinas/Ges/2026-2027/1-semestre",              "role_id": None,                  "webhooks": ["lmac"]},
    "IACom":            {"url": "https://fenix.tecnico.ulisboa.pt/disciplinas/IACom/2026-2027/1-semestre",            "role_id": "1550993366261567648", "webhooks": ["lmac"]},
    "IG":               {"url": "https://fenix.tecnico.ulisboa.pt/disciplinas/IG/2026-2027/1-semestre",               "role_id": "1550994780203388928", "webhooks": ["lmac"]},
    "PEstatisticad3":   {"url": "https://fenix.tecnico.ulisboa.pt/disciplinas/PEstatisticad3/2026-2027/1-semestre",   "role_id": "1550994789070274611", "webhooks": ["lmac"]},
    "TFE":              {"url": "https://fenix.tecnico.ulisboa.pt/disciplinas/TFE/2026-2027/1-semestre",              "role_id": "1550994486212038826", "webhooks": ["lmac"]},
    "noticias":         {"url": "https://fenix.tecnico.ulisboa.pt/messaging/news/cms-newshttps://fenix.tecnico.ulisboa.pt/noticias",                                          "role_id": None,                  "webhooks": ["leic", "lmac"]},
}

WEBHOOKS = {
    "leic": LEIC_WEBHOOK,
    "lmac": LMAC_WEBHOOK,
}
