"""
Etapa 1 — SCRAPER
Extrae indicadores económicos y previsionales desde Previred.
Incluye manejo de errores, reintentos y fallback a datos de ejemplo.
"""

import time
import requests
from bs4 import BeautifulSoup

URL = "https://www.previred.com/indicadores-previsionales/"
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
}
MAX_RETRIES = 3
RETRY_DELAY = 2


def fetch_page(url: str = URL, retries: int = MAX_RETRIES) -> str | None:
    """Descarga el HTML de la página con reintentos."""
    for attempt in range(1, retries + 1):
        try:
            print(f"  Intento {attempt}/{retries} — GET {url}")
            resp = requests.get(url, headers=HEADERS, timeout=15)
            resp.raise_for_status()
            print(f"  Status: {resp.status_code} — {len(resp.text):,} bytes")
            return resp.text
        except requests.RequestException as e:
            print(f"  Error: {e}")
            if attempt < retries:
                time.sleep(RETRY_DELAY * attempt)
    return None


def extract_tables(html: str) -> list[dict]:
    """Extrae todas las tablas de indicadores del HTML de Previred."""
    soup = BeautifulSoup(html, "lxml")
    indicators = []

    tables = soup.find_all("table")
    for table in tables:
        section = _find_section_title(table)
        rows = table.find_all("tr")
        for row in rows:
            cells = row.find_all(["td", "th"])
            if len(cells) >= 2:
                name = cells[0].get_text(strip=True)
                value = cells[1].get_text(strip=True)
                if name and value and not _is_header(name):
                    indicators.append({
                        "seccion": section,
                        "indicador": name,
                        "valor_raw": value,
                    })

    return indicators


def _find_section_title(table_element) -> str:
    """Busca el título de sección más cercano antes de la tabla."""
    for sibling in table_element.find_all_previous(["h2", "h3", "h4", "strong"]):
        text = sibling.get_text(strip=True)
        if text and len(text) > 3:
            return text
    return "General"


def _is_header(text: str) -> bool:
    """Detecta si una fila es encabezado de tabla."""
    headers = {"indicador", "valor", "monto", "concepto", "tasa", "porcentaje",
               "item", "detalle", "descripción", "nombre"}
    return text.lower().strip() in headers


def scrape_indicators() -> list[dict]:
    """Pipeline principal: descarga + extracción de indicadores."""
    print("\n  Descargando página de Previred...")
    html = fetch_page()

    if html is None:
        print("  No se pudo acceder a Previred — usando datos de ejemplo")
        return _sample_indicators()

    indicators = extract_tables(html)

    if not indicators:
        print("  No se encontraron indicadores en el HTML — usando datos de ejemplo")
        return _sample_indicators()

    print(f"  Indicadores extraídos: {len(indicators)}")
    return indicators


def _sample_indicators() -> list[dict]:
    """Datos de ejemplo realistas para cuando Previred no está disponible."""
    return [
        # Indicadores Económicos
        {"seccion": "Valores y Montos Actualizados", "indicador": "UF", "valor_raw": "$38.571,52"},
        {"seccion": "Valores y Montos Actualizados", "indicador": "UTM", "valor_raw": "$67.294"},
        {"seccion": "Valores y Montos Actualizados", "indicador": "UTA", "valor_raw": "$807.528"},
        {"seccion": "Valores y Montos Actualizados", "indicador": "Dólar Observado", "valor_raw": "$953,75"},
        {"seccion": "Valores y Montos Actualizados", "indicador": "Euro", "valor_raw": "$1.038,42"},
        # Rentas Topes Imponibles
        {"seccion": "Rentas Topes Imponibles", "indicador": "Para afiliados a una AFP (UF 81,6)", "valor_raw": "$3.147.436"},
        {"seccion": "Rentas Topes Imponibles", "indicador": "Para afiliados al IPS (UF 60)", "valor_raw": "$2.314.293"},
        {"seccion": "Rentas Topes Imponibles", "indicador": "Para Seguro de Cesantía (UF 122,6)", "valor_raw": "$4.728.467"},
        # Rentas Mínimas Imponibles
        {"seccion": "Rentas Mínimas Imponibles", "indicador": "Trabajadores Dependientes e Independientes", "valor_raw": "$500.000"},
        {"seccion": "Rentas Mínimas Imponibles", "indicador": "Menores de 18 y Mayores de 65", "valor_raw": "$372.989"},
        {"seccion": "Rentas Mínimas Imponibles", "indicador": "Trabajadores de Casa Particular", "valor_raw": "$500.000"},
        {"seccion": "Rentas Mínimas Imponibles", "indicador": "Para fines no remuneracionales", "valor_raw": "$322.295"},
        # AFP
        {"seccion": "Tasas de Cotización Obligatoria AFP", "indicador": "Capital", "valor_raw": "11,44%"},
        {"seccion": "Tasas de Cotización Obligatoria AFP", "indicador": "Cuprum", "valor_raw": "11,44%"},
        {"seccion": "Tasas de Cotización Obligatoria AFP", "indicador": "Habitat", "valor_raw": "11,27%"},
        {"seccion": "Tasas de Cotización Obligatoria AFP", "indicador": "Modelo", "valor_raw": "10,58%"},
        {"seccion": "Tasas de Cotización Obligatoria AFP", "indicador": "PlanVital", "valor_raw": "11,16%"},
        {"seccion": "Tasas de Cotización Obligatoria AFP", "indicador": "ProVida", "valor_raw": "11,45%"},
        {"seccion": "Tasas de Cotización Obligatoria AFP", "indicador": "Uno", "valor_raw": "10,69%"},
        # AFC
        {"seccion": "Seguro de Cesantía (AFC)", "indicador": "Contrato Plazo Indefinido (Empleador)", "valor_raw": "2,40%"},
        {"seccion": "Seguro de Cesantía (AFC)", "indicador": "Contrato Plazo Indefinido (Trabajador)", "valor_raw": "0,60%"},
        {"seccion": "Seguro de Cesantía (AFC)", "indicador": "Contrato Plazo Fijo (Empleador)", "valor_raw": "3,00%"},
        {"seccion": "Seguro de Cesantía (AFC)", "indicador": "Contrato Plazo Fijo (Trabajador)", "valor_raw": "0,00%"},
        # Tasa Cotización Salud
        {"seccion": "Cotización Salud", "indicador": "Cotización Obligatoria de Salud", "valor_raw": "7,00%"},
        # Ahorro Previsional Voluntario
        {"seccion": "Ahorro Previsional Voluntario", "indicador": "APV Tope Mensual (UF 50)", "valor_raw": "$1.928.576"},
        {"seccion": "Ahorro Previsional Voluntario", "indicador": "APV Tope Anual (UF 600)", "valor_raw": "$23.142.912"},
        # Asignación Familiar
        {"seccion": "Asignación Familiar", "indicador": "Tramo A (hasta $437.901)", "valor_raw": "$18.832"},
        {"seccion": "Asignación Familiar", "indicador": "Tramo B ($437.902 a $639.458)", "valor_raw": "$11.553"},
        {"seccion": "Asignación Familiar", "indicador": "Tramo C ($639.459 a $997.827)", "valor_raw": "$3.651"},
        {"seccion": "Asignación Familiar", "indicador": "Tramo D (mayor a $997.827)", "valor_raw": "$0"},
    ]
