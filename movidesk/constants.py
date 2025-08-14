
import os
from pathlib import Path

# ===== Paths & Files =====
APP_DIR = Path(__file__).resolve().parent
CONFIG_FILE = APP_DIR / "config.json"

# ===== API & App Constants =====
API_BASE = "https://api.movidesk.com/public/v1/tickets"
ATIVIDADE = "AMS Sustentacao"
WORK_TYPE = "normal"

# ===== Env Vars =====
ENV_TOKEN = "MOVIDESK_TOKEN"

# ===== Validation Patterns =====
TIME_PATTERN = r"^(?:[01]\d|2[0-3]):[0-5]\d$"   # HH:MM 00:00..23:59
DATE_PATTERN = r"^\d{2}/\d{2}/\d{4}$"           # DD/MM/YYYY
TICKET_PATTERN = r"^\d+$"                         # numeric

# ===== Password Hashing =====
HASH_PREFIX = "sha256$"

# ===== Text Keys (i18n) =====
# Keeping Portuguese defaults now, but all UI strings should come from i18n.TEXTS
