# movidesk/config_store.py
import os, json
from pathlib import Path
from typing import Dict, Any
from .security import is_hashed, hash_password

APP_NAME = "MovideskApp"

def _user_config_dir() -> Path:
    base = os.getenv("APPDATA") or os.getenv("LOCALAPPDATA") or str(Path.home())
    p = Path(base) / APP_NAME
    p.mkdir(parents=True, exist_ok=True)
    return p

CONFIG_FILE = _user_config_dir() / "config.json"

DEFAULT_CONFIG: Dict[str, Any] = {
    "usuarios": {
        "admin": {"senha": "", "agent_id": "", "admin": True}
    },
    "token": "",
    "lang": "pt-BR",
}

def _ensure_minimum(cfg: Dict[str, Any]) -> None:
    cfg.setdefault("usuarios", {})
    if "admin" not in cfg["usuarios"]:
        cfg["usuarios"]["admin"] = {"senha": "", "agent_id": "", "admin": True}
    cfg.setdefault("token", "")
    cfg.setdefault("lang", "pt-BR")

def _migrate_passwords(cfg: Dict[str, Any]) -> bool:
    changed = False
    users = cfg.get("usuarios", {})
    for name, u in list(users.items()):
        pw = (u or {}).get("senha", "")
        if pw and not is_hashed(pw):
            u["senha"] = hash_password(pw)
            changed = True
    return changed

def load_config() -> Dict[str, Any]:
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                cfg = json.load(f)
        except Exception:
            cfg = DEFAULT_CONFIG.copy()
    else:
        cfg = DEFAULT_CONFIG.copy()
        save_config(cfg)
    _ensure_minimum(cfg)
    if _migrate_passwords(cfg):
        save_config(cfg)
    return cfg

def save_config(cfg: Dict[str, Any]) -> None:
    _ensure_minimum(cfg)
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2, ensure_ascii=False)
