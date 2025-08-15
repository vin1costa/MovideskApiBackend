# server.py (com rota client-config)
import os
import sqlite3
from typing import List
from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.responses import JSONResponse
import json

# --- Config ---
DB_PATH = os.getenv("DB_PATH", "usuarios.db")
app = FastAPI(title="Minha API LAN", docs_url="/", redoc_url=None)

# --- DB helpers ---
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL
        )
    """)
    return conn

# --- Models ---
class UsuarioIn(BaseModel):
    nome: str

class UsuarioOut(BaseModel):
    id: int
    nome: str

# --- Routes ---
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

# --- Config central para clientes ---
@app.get("/client-config")
def client_config():
    try:
        with open("client-config.json", "r", encoding="utf-8") as f:
            data = json.load(f)
        return JSONResponse(content=data)
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)

# --- Local dev convenience ---
if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run("server:app", host="0.0.0.0", port=port, reload=True)
