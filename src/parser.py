"""
Etapa 2 — PARSER
Parsea y normaliza los valores extraídos del scraper.
Maneja formatos chilenos: montos ($1.234.567), porcentajes (11,44%), fechas.
"""

import re
from datetime import datetime


def parse_indicators(raw_indicators: list[dict]) -> list[dict]:
    """Parsea una lista de indicadores crudos y devuelve valores normalizados."""
    print("\n" + "=" * 60)
    print("ETAPA 2: PARSING Y NORMALIZACIÓN DE VALORES")
    print("=" * 60)

    parsed = []
    errors = 0

    for item in raw_indicators:
        try:
            result = parse_single(item)
            if result:
                parsed.append(result)
        except Exception as e:
            errors += 1
            print(f"  Error parseando '{item.get('indicador', '?')}': {e}")

    print(f"  Indicadores parseados: {len(parsed)}")
    if errors:
        print(f"  Errores de parsing: {errors}")

    return parsed


def parse_single(item: dict) -> dict | None:
    """Parsea un indicador individual."""
    valor_raw = item.get("valor_raw", "").strip()
    if not valor_raw:
        return None

    valor_numerico = parse_value(valor_raw)
    tipo = detect_type(valor_raw)
    unidad = detect_unit(valor_raw, item.get("indicador", ""))

    return {
        "seccion": item.get("seccion", ""),
        "indicador": clean_indicator_name(item.get("indicador", "")),
        "valor_raw": valor_raw,
        "valor": valor_numerico,
        "tipo": tipo,
        "unidad": unidad,
    }


def parse_value(raw: str) -> float | None:
    """Convierte un valor en formato chileno a float."""
    if not raw:
        return None

    text = raw.strip()

    # Porcentaje: "11,44%" → 11.44
    if "%" in text:
        return parse_percentage(text)

    # Monto: "$1.234.567" o "$38.571,52" → float
    if "$" in text or re.search(r"[\d.]", text):
        return parse_amount(text)

    return None


def parse_percentage(raw: str) -> float | None:
    """Parsea porcentaje chileno: '11,44%' → 11.44"""
    text = raw.replace("%", "").strip()
    text = text.replace(".", "").replace(",", ".")
    try:
        return round(float(text), 4)
    except ValueError:
        return None


def parse_amount(raw: str) -> float | None:
    """Parsea monto chileno: '$1.234.567' → 1234567.0, '$38.571,52' → 38571.52"""
    text = raw.replace("$", "").strip()

    # Detectar si tiene decimales con coma: "$38.571,52"
    if "," in text:
        # Separar parte entera y decimal
        parts = text.rsplit(",", 1)
        integer_part = parts[0].replace(".", "")
        decimal_part = parts[1] if len(parts) > 1 else "0"
        try:
            return round(float(f"{integer_part}.{decimal_part}"), 2)
        except ValueError:
            return None
    else:
        # Solo puntos como separador de miles: "$1.234.567"
        text = text.replace(".", "")
        try:
            return round(float(text), 2)
        except ValueError:
            return None


def detect_type(raw: str) -> str:
    """Detecta el tipo de valor: 'porcentaje', 'monto', 'otro'."""
    if "%" in raw:
        return "porcentaje"
    if "$" in raw or re.search(r"\d+\.\d{3}", raw):
        return "monto"
    return "otro"


def detect_unit(raw: str, indicator_name: str) -> str:
    """Detecta la unidad del indicador."""
    name_lower = indicator_name.lower()

    if "%" in raw:
        return "%"
    if "uf" in name_lower and "utm" not in name_lower:
        return "UF"
    if "utm" in name_lower:
        return "UTM"
    if "uta" in name_lower:
        return "UTA"
    if "dólar" in name_lower or "dolar" in name_lower:
        return "USD"
    if "euro" in name_lower:
        return "EUR"
    if "$" in raw:
        return "CLP"

    return "CLP"


def clean_indicator_name(name: str) -> str:
    """Limpia y normaliza el nombre del indicador."""
    # Remover espacios múltiples
    name = re.sub(r"\s+", " ", name).strip()
    # Remover caracteres especiales al inicio/final
    name = name.strip(".-–— ")
    return name


def format_clp(value: float | None) -> str:
    """Formatea un valor como monto chileno: 1234567 → '$1.234.567'."""
    if value is None:
        return "$0"
    if value == int(value):
        return f"${int(value):,.0f}".replace(",", ".")
    return f"${value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def format_percentage(value: float | None) -> str:
    """Formatea un valor como porcentaje: 11.44 → '11,44%'."""
    if value is None:
        return "0%"
    formatted = f"{value:.2f}".replace(".", ",")
    return f"{formatted}%"
