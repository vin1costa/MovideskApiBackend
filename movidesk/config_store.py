
import json, os
from typing import Dict, Any
from .constants import CONFIG_FILE, ENV_TOKEN
from .security import is_hashed, hash_password

DEFAULT_CONFIG = {
    "token": "",
    "usuarios": {
        "admin": {"senha": "admin", "agent_id": "", "admin": True},
    }
}

def _ensure_admin_flag(cfg: Dict[str, Any]) -> None:
    for nome, dados in cfg.get("usuarios", {}).items():
        if "admin" not in dados:
            dados["admin"] = (nome == "admin")

def _migrate_passwords(cfg: Dict[str, Any]) -> bool:
    """Hash legacy plaintext passwords. Returns True if changes were made."""
    changed = False
    for nome, user in cfg.get("usuarios", {}).items():
        pwd = user.get("senha", "")
        if pwd and not is_hashed(pwd):
            user["senha"] = hash_password(pwd)
            changed = True
    return changed

def load_config() -> Dict[str, Any]:
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            cfg = json.load(f)
    else:
        cfg = DEFAULT_CONFIG.copy()
    _ensure_admin_flag(cfg)
    if _migrate_passwords(cfg):
        save_config(cfg)
    # Prefer env token if present
    env_token = os.getenv(ENV_TOKEN, "").strip()
    if env_token:
        cfg["token"] = env_token
    return cfg

def save_config(cfg: Dict[str, Any]) -> None:
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=4, ensure_ascii=False)
