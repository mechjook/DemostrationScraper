"""
Generador de datos seed históricos.
Crea un CSV con historial simulado de indicadores para que el dashboard
tenga series temporales desde la primera ejecución.
"""

import os
import csv
import random
from datetime import datetime, timedelta

from src.storage import CSV_COLUMNS, HISTORY_CSV


# Valores base (aproximados a valores reales de Chile 2024-2025)
BASE_VALUES = {
    "UF": {"base": 37800, "volatility": 0.001, "trend": 0.0003, "tipo": "monto", "unidad": "UF",
           "seccion": "Valores y Montos Actualizados"},
    "UTM": {"base": 65000, "volatility": 0.005, "trend": 0.002, "tipo": "monto", "unidad": "UTM",
            "seccion": "Valores y Montos Actualizados"},
    "UTA": {"base": 780000, "volatility": 0.005, "trend": 0.002, "tipo": "monto", "unidad": "UTA",
            "seccion": "Valores y Montos Actualizados"},
    "Dólar Observado": {"base": 920, "volatility": 0.008, "trend": 0.001, "tipo": "monto", "unidad": "USD",
                        "seccion": "Valores y Montos Actualizados"},
    "Euro": {"base": 1000, "volatility": 0.007, "trend": 0.0008, "tipo": "monto", "unidad": "EUR",
             "seccion": "Valores y Montos Actualizados"},
}

# Indicadores que no varían (o varían muy poco)
STATIC_INDICATORS = [
    {"seccion": "Rentas Topes Imponibles", "indicador": "Para afiliados a una AFP (UF 81,6)",
     "valor": 3147436, "tipo": "monto", "unidad": "CLP"},
    {"seccion": "Rentas Topes Imponibles", "indicador": "Para afiliados al IPS (UF 60)",
     "valor": 2314293, "tipo": "monto", "unidad": "CLP"},
    {"seccion": "Rentas Topes Imponibles", "indicador": "Para Seguro de Cesantía (UF 122,6)",
     "valor": 4728467, "tipo": "monto", "unidad": "CLP"},
    {"seccion": "Rentas Mínimas Imponibles", "indicador": "Trabajadores Dependientes e Independientes",
     "valor": 500000, "tipo": "monto", "unidad": "CLP"},
    {"seccion": "Rentas Mínimas Imponibles", "indicador": "Menores de 18 y Mayores de 65",
     "valor": 372989, "tipo": "monto", "unidad": "CLP"},
    {"seccion": "Rentas Mínimas Imponibles", "indicador": "Trabajadores de Casa Particular",
     "valor": 500000, "tipo": "monto", "unidad": "CLP"},
    {"seccion": "Rentas Mínimas Imponibles", "indicador": "Para fines no remuneracionales",
     "valor": 322295, "tipo": "monto", "unidad": "CLP"},
    {"seccion": "Tasas de Cotización Obligatoria AFP", "indicador": "Capital",
     "valor": 11.44, "tipo": "porcentaje", "unidad": "%"},
    {"seccion": "Tasas de Cotización Obligatoria AFP", "indicador": "Cuprum",
     "valor": 11.44, "tipo": "porcentaje", "unidad": "%"},
    {"seccion": "Tasas de Cotización Obligatoria AFP", "indicador": "Habitat",
     "valor": 11.27, "tipo": "porcentaje", "unidad": "%"},
    {"seccion": "Tasas de Cotización Obligatoria AFP", "indicador": "Modelo",
     "valor": 10.58, "tipo": "porcentaje", "unidad": "%"},
    {"seccion": "Tasas de Cotización Obligatoria AFP", "indicador": "PlanVital",
     "valor": 11.16, "tipo": "porcentaje", "unidad": "%"},
    {"seccion": "Tasas de Cotización Obligatoria AFP", "indicador": "ProVida",
     "valor": 11.45, "tipo": "porcentaje", "unidad": "%"},
    {"seccion": "Tasas de Cotización Obligatoria AFP", "indicador": "Uno",
     "valor": 10.69, "tipo": "porcentaje", "unidad": "%"},
    {"seccion": "Seguro de Cesantía (AFC)", "indicador": "Contrato Plazo Indefinido (Empleador)",
     "valor": 2.40, "tipo": "porcentaje", "unidad": "%"},
    {"seccion": "Seguro de Cesantía (AFC)", "indicador": "Contrato Plazo Indefinido (Trabajador)",
     "valor": 0.60, "tipo": "porcentaje", "unidad": "%"},
    {"seccion": "Seguro de Cesantía (AFC)", "indicador": "Contrato Plazo Fijo (Empleador)",
     "valor": 3.00, "tipo": "porcentaje", "unidad": "%"},
    {"seccion": "Cotización Salud", "indicador": "Cotización Obligatoria de Salud",
     "valor": 7.00, "tipo": "porcentaje", "unidad": "%"},
    {"seccion": "Ahorro Previsional Voluntario", "indicador": "APV Tope Mensual (UF 50)",
     "valor": 1928576, "tipo": "monto", "unidad": "CLP"},
    {"seccion": "Ahorro Previsional Voluntario", "indicador": "APV Tope Anual (UF 600)",
     "valor": 23142912, "tipo": "monto", "unidad": "CLP"},
    {"seccion": "Asignación Familiar", "indicador": "Tramo A (hasta $437.901)",
     "valor": 18832, "tipo": "monto", "unidad": "CLP"},
    {"seccion": "Asignación Familiar", "indicador": "Tramo B ($437.902 a $639.458)",
     "valor": 11553, "tipo": "monto", "unidad": "CLP"},
    {"seccion": "Asignación Familiar", "indicador": "Tramo C ($639.459 a $997.827)",
     "valor": 3651, "tipo": "monto", "unidad": "CLP"},
]


def _format_valor_raw(valor: float, tipo: str) -> str:
    """Formatea el valor como string chileno."""
    if tipo == "porcentaje":
        return f"{valor:.2f}%".replace(".", ",")
    if valor == int(valor):
        return f"${int(valor):,}".replace(",", ".")
    # Decimal
    integer = int(valor)
    decimal = int(round((valor - integer) * 100))
    return f"${integer:,}".replace(",", ".") + f",{decimal:02d}"


def generate_seed_data(data_dir: str, num_weeks: int = 26):
    """Genera datos históricos simulados de las últimas N semanas."""
    csv_path = os.path.join(data_dir, HISTORY_CSV)

    # No sobrescribir si ya existe con datos
    if os.path.isfile(csv_path) and os.path.getsize(csv_path) > 100:
        return

    os.makedirs(data_dir, exist_ok=True)
    random.seed(42)

    rows = []
    today = datetime.now()
    start_date = today - timedelta(weeks=num_weeks)

    # Generar una fecha por semana
    current_date = start_date
    while current_date <= today:
        fecha_str = current_date.strftime("%Y-%m-%d")
        weeks_elapsed = (current_date - start_date).days / 7

        # Indicadores variables (UF, UTM, Dólar, Euro, UTA)
        for name, config in BASE_VALUES.items():
            trend = config["base"] * config["trend"] * weeks_elapsed
            noise = config["base"] * config["volatility"] * random.gauss(0, 1)
            valor = round(config["base"] + trend + noise, 2)

            valor_raw = _format_valor_raw(valor, config["tipo"])
            rows.append({
                "fecha_extraccion": fecha_str,
                "seccion": config["seccion"],
                "indicador": name,
                "valor_raw": valor_raw,
                "valor": valor,
                "tipo": config["tipo"],
                "unidad": config["unidad"],
            })

        # Indicadores estáticos (se repiten igual cada semana)
        for ind in STATIC_INDICATORS:
            valor_raw = _format_valor_raw(ind["valor"], ind["tipo"])
            rows.append({
                "fecha_extraccion": fecha_str,
                "seccion": ind["seccion"],
                "indicador": ind["indicador"],
                "valor_raw": valor_raw,
                "valor": ind["valor"],
                "tipo": ind["tipo"],
                "unidad": ind["unidad"],
            })

        current_date += timedelta(weeks=1)

    # Escribir CSV
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)

    print(f"  Datos seed generados: {len(rows)} registros, {num_weeks} semanas")
    print(f"  Archivo: {csv_path}")
