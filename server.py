import os
import json
import sqlite3
from threading import Lock
from typing import List, Optional, Dict, Any

from fastapi import FastAPI, Header, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel

# =========================
# Configurações do servidor
# =========================
DB_PATH = os.getenv("DB_PATH", "usuarios.db")
CONFIG_PATH = os.getenv("CLIENT_CONFIG_PATH", "client-config.json")  # ex.: /data/client-config.json se usar Volume
CONFIG_ADMIN_KEY = os.getenv("CONFIG_ADMIN_KEY", "")  # defina no Railway → Variables
_config_lock = Lock()

app = FastAPI(title="Minha API LAN", docs_url="/", redoc_url=None)

# =========================
# Camada de dados (SQLite)
# =========================
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL
        )
        """
    )
    return conn

class UsuarioIn(BaseModel):
    nome: str

class UsuarioOut(BaseModel):
    id: int
    nome: str

# =========================
# Rotas de exemplo (usuarios)
# =========================
@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/usuarios", response_model=UsuarioOut)
def criar_usuario(usuario: UsuarioIn):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("INSERT INTO usuarios (nome) VALUES (?)", (usuario.nome,))
    conn.commit()
    user_id = cur.lastrowid
    conn.close()
    return {"id": user_id, "nome": usuario.nome}

@app.get("/usuarios", response_model=List[UsuarioOut])
def listar_usuarios():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT id, nome FROM usuarios")
    rows = cur.fetchall()
    conn.close()
    return [{"id": r[0], "nome": r[1]} for r in rows]

# =========================
# Config central GET/PUT
# =========================
def _load_central_config() -> Dict[str, Any]:
    if not os.path.exists(CONFIG_PATH):
        data = {
            "version": 1,
            "usuarios": {"admin": {"senha": "", "agent_id": "", "admin": True}},
            "token": "",
            "lang": "pt-BR",
        }
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return data
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def _save_central_config(data: Dict[str, Any]) -> None:
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

@app.get("/client-config")
def get_client_config():
    with _config_lock:
        data = _load_central_config()
    return JSONResponse(content=data)

class ClientConfigIn(BaseModel):
    version: Optional[int] = None
    usuarios: Optional[Dict[str, Any]] = None
    token: Optional[str] = None
    lang: Optional[str] = None

def _secure_merge(base: Dict[str, Any], inc: Dict[str, Any]) -> Dict[str, Any]:
    """
    Merge seguro:
    - usuarios: merge por nome (mantém os existentes e sobrescreve os que vierem)
    - token: só substitui se o novo vier não-vazio
    - lang: substitui se vier
    - version: incrementa sempre que salvar
    """
    out = dict(base)
    # usuarios
    if isinstance(inc.get("usuarios"), dict):
        merged_users = dict(out.get("usuarios", {}))
        merged_users.update(inc["usuarios"])
        out["usuarios"] = merged_users
    # token
    if isinstance(inc.get("token"), str) and inc["token"].strip():
        out["token"] = inc["token"].strip()
    # lang
    if isinstance(inc.get("lang"), str):
        out["lang"] = inc["lang"]
    # version
    out["version"] = int(out.get("version", 0)) + 1
    return out

@app.put("/client-config")
def put_client_config(
    payload: ClientConfigIn,
    x_config_key: Optional[str] = Header(default=None, convert_underscores=False),
):
    # Proteção simples por chave
    if not CONFIG_ADMIN_KEY or x_config_key != CONFIG_ADMIN_KEY:
        raise HTTPException(status_code=401, detail="unauthorized")

    with _config_lock:
        current = _load_central_config()
        merged = _secure_merge(current, payload.dict(exclude_unset=True))
        _save_central_config(merged)

    return JSONResponse(
        content={
            "status": "ok",
            "version": merged["version"],
            "usuarios_count": len(merged.get("usuarios", {})),
            "has_token": bool(merged.get("token", "").strip()),
        }
    )

# =========================
# Execução local
# =========================
if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run("server:app", host="0.0.0.0", port=port, reload=True)
