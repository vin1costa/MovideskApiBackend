
import re
from datetime import datetime
from .constants import TIME_PATTERN, DATE_PATTERN, TICKET_PATTERN

def validate_date(date_str: str) -> bool:
    if not re.match(DATE_PATTERN, date_str or ""):
        return False
    try:
        datetime.strptime(date_str, "%d/%m/%Y")
        return True
    except ValueError:
        return False

def validate_time(time_str: str) -> bool:
    return bool(re.match(TIME_PATTERN, time_str or ""))

def validate_ticket(ticket: str) -> bool:
    return bool(re.match(TICKET_PATTERN, ticket or ""))
