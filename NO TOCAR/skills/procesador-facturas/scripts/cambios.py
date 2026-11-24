"""Tipos diarios BCE expresados en USD por EUR, con consulta de fechas nuevas."""
import csv
import io
from datetime import date
from decimal import Decimal, ROUND_HALF_UP
from functools import lru_cache
from pathlib import Path
from urllib.request import urlopen

HISTORICO = Path(__file__).resolve().parents[1] / 'references/eur-usd.csv'
FUENTE = 'https://data-api.ecb.europa.eu/service/data/EXR/D.USD.EUR.SP00.A'


def leer_tipos(rows, fecha_key, tipo_key):
    rates = {}
    for row in rows:
        day = date.fromisoformat(row[fecha_key])
        rate = Decimal(row[tipo_key])
        if not rate.is_finite() or rate <= 0:
            raise ValueError('Tipo BCE inválido')
        if day in rates and rates[day] != rate:
            raise ValueError('Tipos BCE contradictorios')
        rates[day] = rate
    if not rates:
        raise ValueError('Histórico BCE vacío')
    return rates


@lru_cache(maxsize=512)
def tipo_cambio(fecha):
    requested = date.fromisoformat(fecha)
    if requested > date.today():
        raise ValueError('La fecha de factura es futura')
    with HISTORICO.open(encoding='utf-8') as stream:
        rates = leer_tipos(csv.DictReader(stream), 'fecha', 'usd_por_eur')
    eligible = [day for day in rates if day <= requested]
    selected = max(eligible) if eligible else None
    if requested > max(rates) or selected is None or (requested - selected).days > 7:
        # Consulta acotada a la fecha requerida y su semana anterior. No extrapolar.
        from datetime import timedelta
        start = (requested - timedelta(days=7)).isoformat()
        url = FUENTE + '?startPeriod=' + start + '&endPeriod=' + requested.isoformat() + '&format=csvdata'
        with urlopen(url, timeout=30) as response:
            text = response.read(2_000_000).decode('utf-8-sig')
        fresh = leer_tipos(csv.DictReader(io.StringIO(text)), 'TIME_PERIOD', 'OBS_VALUE')
        # La serie solicitada es USD/EUR. Comprobar además su identidad en respuesta.
        rows = list(csv.DictReader(io.StringIO(text)))
        if any(r.get('CURRENCY') != 'USD' or r.get('CURRENCY_DENOM') != 'EUR' for r in rows):
            raise ValueError('La respuesta BCE contiene una divisa distinta')
        rates.update(fresh)
        eligible = [day for day in rates if day <= requested]
        selected = max(eligible) if eligible else None
    if selected is None or (requested - selected).days > 7:
        raise ValueError('Falta tipo BCE cercano anterior a la fecha')
    return selected.isoformat(), rates[selected]


@lru_cache(maxsize=512)
def convertir(fecha, total, base):
    """Devuelve importes originales, EUR y nota de trazabilidad, incluso si falla la red."""
    try:
        applied, rate = tipo_cambio(fecha)
    except (ValueError, TypeError, OSError, ArithmeticError, KeyError, UnicodeError) as error:
        return total, base, None, None, 'Conversión USD/EUR pendiente: ' + str(error)

    def euros(value):
        if value is None:
            return None
        return float((Decimal(str(value)) / rate).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))

    note = f'BCE {applied}: 1 EUR = {rate} USD. EUR = USD / {rate}. Fuente: {FUENTE}'
    return total, base, euros(total), euros(base), note
