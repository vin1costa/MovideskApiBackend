# movidesk/config_store.py
import os
import sys
import json
from pathlib import Path
from typing import Dict, Any, Tuple, Optional

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
ADMIN_KEY_FILE = _user_config_dir() / "admin.key"  # preferencial
ADMIN_KEY_SIDECAR = None  # definido dinamicamente no _exe_dir()

DEFAULT_CONFIG: Dict[str, Any] = {
    "usuarios": {"admin": {"senha": "", "agent_id": "", "admin": True}},
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
    out = {**base_cfg}
    for k, v in overlay_cfg.items():
        if k == "token":
            if isinstance(v, str) and v.strip():
                out["token"] = v.strip()
        elif k == "usuarios" and isinstance(v, dict):
            u = dict(out.get("usuarios", {}))
            u.update(v)
            out["usuarios"] = u
        else:
            out[k] = v
    return out

def load_config() -> Dict[str, Any]:
    global ADMIN_KEY_SIDECAR
    ADMIN_KEY_SIDECAR = _exe_dir() / "admin_key.txt"

    # base local
    if CONFIG_FILE.exists():
        try:
            cfg = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
        except Exception:
            cfg = DEFAULT_CONFIG.copy()
    else:
        cfg = DEFAULT_CONFIG.copy()
        save_config(cfg)  # cria o local

    _ensure_minimum(cfg)
    if _migrate_passwords(cfg):
        _save_local(cfg)

    # remoto (se backend.json definir)
    remote_url = (_read_backend_json().get("remote_config_url") or "").strip()
    if remote_url:
        remote_cfg, ok = _fetch_remote(remote_url)
        if ok and isinstance(remote_cfg, dict):
            cfg = _overlay(cfg, remote_cfg)
            _ensure_minimum(cfg)

    return cfg

def _save_local(cfg: Dict[str, Any]) -> None:
    _ensure_minimum(cfg)
    CONFIG_FILE.write_text(json.dumps(cfg, indent=2, ensure_ascii=False), encoding="utf-8")

def _load_admin_key() -> Optional[str]:
    # prioridade: %APPDATA%\MovideskApp\admin.key
    if ADMIN_KEY_FILE.exists():
        k = ADMIN_KEY_FILE.read_text(encoding="utf-8").strip()
        if k:
            return k
    # fallback: admin_key.txt ao lado do .exe
    if ADMIN_KEY_SIDECAR and ADMIN_KEY_SIDECAR.exists():
        k = ADMIN_KEY_SIDECAR.read_text(encoding="utf-8").strip()
        if k:
            return k
    return None

def _push_remote(cfg: Dict[str, Any]) -> bool:
    """
    Envia alterações ao servidor (PUT /client-config).
    Requer backend.json.remote_config_url e admin key.
    Retorna True em sucesso, False em falha.
    """
    bj = _read_backend_json()
    remote_url = (bj.get("remote_config_url") or "").strip()
    if not remote_url:
        return False

    admin_key = _load_admin_key()
    if not admin_key:
        return False

    # enviamos apenas campos de interesse; o servidor faz merge e incrementa versão
    payload = {
        "usuarios": cfg.get("usuarios", {}),
        "token": cfg.get("token", ""),
        "lang": cfg.get("lang", "pt-BR"),
    }
    headers = {
        "Content-Type": "application/json",
        "X-Config-Key": admin_key,
    }
    try:
        r = requests.put(remote_url, headers=headers, json=payload, timeout=10)
        if r.status_code == 200:
            return True
        return False
    except Exception:
        return False

def save_config(cfg: Dict[str, Any]) -> None:
    """
    Salva localmente e tenta publicar no servidor.
    Assim, quem tiver a admin key fará a publicação central.
    Quem não tiver, ao menos salva local.
    """
    _save_local(cfg)
    _push_remote(cfg)

# utilitário opcional (p/ atalho F11)
def refresh_remote_if_any() -> bool:
    bj = _read_backend_json()
    remote_url = (bj.get("remote_config_url") or "").strip()
    if not remote_url:
        return False
    data, ok = _fetch_remote(remote_url)
    return ok
