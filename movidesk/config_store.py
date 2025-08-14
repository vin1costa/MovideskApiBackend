import os, json
from pathlib import Path
from typing import Dict, Any

APP_NAME = "MovideskApp"

# Onde salvar o config (sempre área do usuário, gravável)
def _user_config_dir() -> Path:
    base = os.getenv("APPDATA") or os.getenv("LOCALAPPDATA") or str(Path.home())
    p = Path(base) / APP_NAME
    p.mkdir(parents=True, exist_ok=True)
    return p

CONFIG_FILE = _user_config_dir() / "config.json"

# Config padrão mínima; ajuste se quiser defaults específicos
DEFAULT_CONFIG: Dict[str, Any] = {
    "usuarios": {
        # usuário admin padrão (sem senha definida)
        "admin": {"senha": "", "agent_id": "", "admin": True}
    },
    # outros campos que seu app possa usar:
    "token": "",
    "lang": "pt-BR",
}

def _ensure_minimum(cfg: Dict[str, Any]) -> None:
    # Garante chaves básicas
    cfg.setdefault("usuarios", {})
    if "admin" not in cfg["usuarios"]:
        cfg["usuarios"]["admin"] = {"senha": "", "agent_id": "", "admin": True}
    cfg.setdefault("token", "")
    cfg.setdefault("lang", "pt-BR")

def load_config() -> Dict[str, Any]:
    # Lê config do diretório do usuário; se não existir, cria com defaults
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                cfg = json.load(f)
        except Exception:
            cfg = DEFAULT_CONFIG.copy()
    else:
        cfg = DEFAULT_CONFIG.copy()
        save_config(cfg)  # persiste o padrão no primeiro uso
    _ensure_minimum(cfg)
    return cfg

def save_config(cfg: Dict[str, Any]) -> None:
    _ensure_minimum(cfg)
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2, ensure_ascii=False)
