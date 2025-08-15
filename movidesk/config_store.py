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
ADMIN_KEY_SIDECAR: Optional[Path] = None  # definido em runtime

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
    """Busca config remoto; em sucesso salva cache. Em falha, tenta cache."""
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
    """Overlay seguro: token só se vier não-vazio; usuarios faz merge; demais chaves substituem."""
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
    # define sidecar da admin key (ao lado do .exe)
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
        save_config(cfg)  # cria arquivo local

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
    # 1) %APPDATA%\MovideskApp\admin.key
    if ADMIN_KEY_FILE.exists():
        k = ADMIN_KEY_FILE.read_text(encoding="utf-8").strip()
        if k:
            return k
    # 2) admin_key.txt ao lado do .exe
    if ADMIN_KEY_SIDECAR and ADMIN_KEY_SIDECAR.exists():
        k = ADMIN_KEY_SIDECAR.read_text(encoding="utf-8").strip()
        if k:
            return k
    return None

def publish_to_all(cfg: Dict[str, Any]) -> Tuple[bool, str]:
    """
    Envia alterações ao servidor (PUT /client-config).
    Requer:
      - backend.json com "remote_config_url"
      - admin.key em %APPDATA%/MovideskApp/ ou admin_key.txt ao lado do .exe
    Retorna (ok, mensagem).
    """
    bj = _read_backend_json()
    remote_url = (bj.get("remote_config_url") or "").strip()
    if not remote_url:
        return (False, "remote_config_url não definido em backend.json (ao lado do .exe).")

    admin_key = _load_admin_key()
    if not admin_key:
        return (False, "admin key não encontrada. Crie %APPDATA%/MovideskApp/admin.key ou admin_key.txt ao lado do .exe.")

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
            return (True, f"Publicado com sucesso: {r.text}")
        else:
            return (False, f"Falha ao publicar (status {r.status_code}): {r.text}")
    except Exception as e:
        return (False, f"Erro de rede ao publicar: {e}")

def save_config(cfg: Dict[str, Any]) -> None:
    """
    Salva somente localmente (explícito). Para propagar a todos, chame publish_to_all(cfg).
    """
    _save_local(cfg)

def refresh_remote_if_any() -> bool:
    """
    Força atualização do cache remoto (útil para um atalho F11).
    """
    bj = _read_backend_json()
    remote_url = (bj.get("remote_config_url") or "").strip()
    if not remote_url:
        return False
    _, ok = _fetch_remote(remote_url)
    return ok
