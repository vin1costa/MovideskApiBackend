
import requests
from datetime import datetime
from tkinter import messagebox  # kept for parity with existing flow
from .validators import validate_date, validate_time, validate_ticket
from .constants import API_BASE, ATIVIDADE, WORK_TYPE
from .errors import AppError

def apontar_horas(cfg, ticket_id, descricao, data_str, hora_inicio, hora_fim, agente_id, texts):
    # Input validation
    if not validate_ticket(ticket_id):
        raise AppError(texts["invalid_ticket"])
    if not validate_date(data_str):
        raise AppError(texts["invalid_date"])
    if not (validate_time(hora_inicio) and validate_time(hora_fim)):
        raise AppError(texts["invalid_time"])

    # Build payload
    data_iso = datetime.strptime(data_str, "%d/%m/%Y").strftime("%Y-%m-%dT00:00:00")
    hora_inicio_iso = f"{hora_inicio}:00.0000000"
    hora_fim_iso = f"{hora_fim}:00.0000000"

    url = f"{API_BASE}?token={cfg['token']}&id={ticket_id}"
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
        resp = requests.patch(url, headers=headers, json=payload, timeout=30)
    except requests.RequestException as e:
        raise AppError(texts["network_fail"].format(err=e))

    if resp.status_code == 200:
        return True
    else:
        raise AppError(texts["apontamento_fail"].format(status=resp.status_code, body=resp.text))
