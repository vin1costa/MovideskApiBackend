# movidesk/api_client.py
import requests
from datetime import datetime
from tkinter import messagebox  # mantido por compatibilidade com fluxos existentes
from .validators import validate_date, validate_time, validate_ticket
from .constants import API_BASE, ATIVIDADE, WORK_TYPE
from .errors import AppError

def apontar_horas(cfg, ticket_id, descricao, data_str, hora_inicio, hora_fim, agente_id, texts):
    # Validações de entrada (mesmo padrão que você já usava)
    if not validate_ticket(ticket_id):
        raise AppError(texts.get("invalid_ticket", "Ticket inválido."))
    if not validate_date(data_str):
        raise AppError(texts.get("invalid_date", "Data inválida."))
    if not (validate_time(hora_inicio) and validate_time(hora_fim)):
        raise AppError(texts.get("invalid_time", "Hora inválida."))

    # Garante token
    token = (cfg or {}).get("token", "").strip()
    if not token or token.lower().startswith("cole_aqui"):
        raise AppError("Token do Movidesk ausente/placeholder. Configure no config central (ou via F10).")

    # Montagem de datas/horas (idêntico ao seu código anterior)
    # data_str vem como "dd/MM/yyyy"
    try:
        data_iso = datetime.strptime(data_str, "%d/%m/%Y").strftime("%Y-%m-%dT00:00:00")
    except ValueError:
        raise AppError(texts.get("invalid_date", "Data inválida."))
    hora_inicio_iso = f"{hora_inicio}:00.0000000"
    hora_fim_iso    = f"{hora_fim}:00.0000000"

    # URL base e params em vez de concatenar manualmente a query string
    # Equivalente ao seu: f"{API_BASE}?token={cfg['token']}&id={ticket_id}"
    url = f"{API_BASE}"
    params = {
        "token": token,
        "id": ticket_id
    }

    # Payload: exatamente o mesmo que você usava
    payload = {
        "actions": [
            {
                "type": 2,
                "description": descricao,
                "createdBy": {"id": agente_id},
                "timeAppointments": [
                    {
                        "activity": ATIVIDADE,
                        "date": data_iso,
                        "periodStart": hora_inicio_iso,
                        "periodEnd": hora_fim_iso,
                        "workTypeName": WORK_TYPE,
                        "createdBy": {"id": agente_id},
                    }
                ],
            }
        ]
    }

    headers = {"Content-Type": "application/json"}

    try:
        resp = requests.patch(url, params=params, headers=headers, json=payload, timeout=30)
    except requests.RequestException as e:
        raise AppError(texts.get("network_fail", "Falha de rede: {err}").format(err=e))

    if resp.status_code == 200:
        return True
    elif resp.status_code == 401:
        raise AppError("401 não autorizado: verifique o token (valor e permissões) no config central.")
    else:
        raise AppError(texts.get("apontamento_fail", "Falha no apontamento (status {status}): {body}")
                       .format(status=resp.status_code, body=resp.text))
