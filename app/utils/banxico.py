import json
import urllib.request
from datetime import date, timedelta
from decimal import Decimal, InvalidOperation

from app.core.config import settings

_BANXICO_URL = "https://www.banxico.org.mx/SieAPIRest/service/v1/series/SF63528/datos/oportuno"


def get_previous_business_day(from_date: date) -> date:
    """Return the previous business day (Mon→Fri, Tue-Fri→previous day)."""
    delta = timedelta(days=3 if from_date.weekday() == 0 else 1)
    return from_date - delta


def fetch_usd_exchange_rate() -> Decimal:
    """
    Fetch the most recent USD/MXN fix rate from Banxico (SF63528).
    Raises RuntimeError if the request fails or the response is malformed.
    """
    if not settings.TOKEN_BANXICO:
        raise RuntimeError("TOKEN_BANXICO no está configurado en las variables de entorno")

    req = urllib.request.Request(
        _BANXICO_URL,
        headers={
            "Accept": "application/json",
            "Bmx-Token": settings.TOKEN_BANXICO,
        },
    )

    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            payload = json.loads(response.read().decode())
    except urllib.error.URLError as exc:
        raise RuntimeError(f"No se pudo conectar a Banxico: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Respuesta inválida de Banxico: {exc}") from exc

    try:
        dato = payload["bmx"]["series"][0]["datos"][0]["dato"]
        return Decimal(dato)
    except (KeyError, IndexError) as exc:
        raise RuntimeError(f"Formato inesperado en respuesta de Banxico: {exc}") from exc
    except InvalidOperation as exc:
        raise RuntimeError(f"Valor de tipo de cambio inválido: {dato!r}") from exc
