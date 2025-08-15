import os
import sys
import json
from pathlib import Path
from typing import Dict, Any, Tuple

import requests
from .security import is_hashed, hash_password

APP_NAME = "MovideskApp"

def _user_config_dir() -> Path:
    base = os.getenv("APPDATA") or os.getenv("LOCALAPPDATA") or str(Path.home())
    p = Path(base) / APP_NAME
    p.mkdir(parents=True, exist_ok=True)
    return p

CONFIG_FILE = _user_config_dir() / "config.json"
REMOTE_CACHE = _user_config_dir() / "remote_config.cache.json"

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
    for _, u in list(users.items()):
        pw = (u or {}).get("senha", "")
        if pw and not is_hashed(pw):
            u["senha"] = hash_password(pw)
            changed = True
    return changed

def _exe_dir() -> Path:
    # diretório do executável (ou do script em dev)
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).resolve().parent

def _read_backend_json() -> Dict[str, Any]:
    path = _exe_dir() / "backend.json"
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}

def _fetch_remote(url: str, timeout=8) -> Tuple[Dict[str, Any], bool]:
    """Tenta buscar config remoto. Em sucesso, atualiza cache local e retorna (data, True).
       Em falha, tenta cache; se indisponível, retorna ({}, False)."""
    try:
        r = requests.get(url, timeout=timeout)
        r.raise_for_status()
        data = r.json()
        REMOTE_CACHE.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
        return data, True
    except Exception:
        if REMOTE_CACHE.exists():
            try:
                return json.loads(REMOTE_CACHE.read_text(encoding="utf-8")), True
            except Exception:
                pass
        return {}, False

def _overlay(base_cfg: Dict[str, Any], overlay_cfg: Dict[str, Any]) -> Dict[str, Any]:
    """
    Aplica overlay de forma segura:
    - 'token': só sobrescreve se overlay trouxer string não vazia.
    - 'usuarios': merge (sobrescreve usuários por nome, mas mantém os demais).
    - demais chaves: sobrescreve normal.
    """
    out = {**base_cfg}
    for k, v in overlay_cfg.items():
        if k == "token":
            if isinstance(v, str) and v.strip():
                out["token"] = v.strip()
        elif k == "usuarios" and isinstance(v, dict):
            base_users = dict(out.get("usuarios", {}))
            base_users.update(v)
            out["usuarios"] = base_users
        else:
            out[k] = v
    return out

def load_config() -> Dict[str, Any]:
    # 1) base local
    if CONFIG_FILE.exists():
        try:
            cfg = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
        except Exception:
            cfg = DEFAULT_CONFIG.copy()
    else:
        cfg = DEFAULT_CONFIG.copy()
        save_config(cfg)

    _ensure_minimum(cfg)
    if _migrate_passwords(cfg):
        save_config(cfg)

    # 2) remoto (se definido em backend.json)
    remote_url = (_read_backend_json().get("remote_config_url") or "").strip()
    if remote_url:
        remote_cfg, ok = _fetch_remote(remote_url)
        if ok and isinstance(remote_cfg, dict):
            cfg = _overlay(cfg, remote_cfg)
            _ensure_minimum(cfg)  # garante admin mínimo

    return cfg

def save_config(cfg: Dict[str, Any]) -> None:
    _ensure_minimum(cfg)
    CONFIG_FILE.write_text(json.dumps(cfg, indent=2, ensure_ascii=False), encoding="utf-8")

# opcional: força refresh do remoto (útil para atalho F11)
def refresh_remote_if_any() -> bool:
    remote_url = (_read_backend_json().get("remote_config_url") or "").strip()
    if not remote_url:
        return False
    _, ok = _fetch_remote(remote_url)
    return ok
