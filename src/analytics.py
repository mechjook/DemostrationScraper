"""
Etapa 4 — ANALYTICS
Calcula variaciones, tendencias, máximos/mínimos históricos y KPIs.
"""

import pandas as pd
import numpy as np


# Indicadores clave para tracking de evolución temporal
KEY_INDICATORS = ["UF", "UTM", "Dólar Observado", "Euro"]


def run_analytics(data_dir: str, df_history: pd.DataFrame) -> dict:
    """Ejecuta análisis completo sobre los datos históricos."""
    print("\n" + "=" * 60)
    print("ETAPA 4: ANÁLISIS Y CÁLCULO DE VARIACIONES")
    print("=" * 60)

    stats = {}

    if df_history.empty:
        print("  Sin datos históricos para analizar")
        return stats

    # Resumen general
    stats["total_registros"] = len(df_history)
    stats["total_indicadores"] = df_history["indicador"].nunique()
    stats["fechas_extraccion"] = sorted(
        df_history["fecha_extraccion"].dropna().dt.strftime("%Y-%m-%d").unique().tolist()
    )
    stats["total_fechas"] = len(stats["fechas_extraccion"])
    print(f"  Registros totales: {stats['total_registros']}")
    print(f"  Indicadores únicos: {stats['total_indicadores']}")
    print(f"  Fechas de extracción: {stats['total_fechas']}")

    # Valores actuales (última extracción)
    latest_date = df_history["fecha_extraccion"].max()
    latest = df_history[df_history["fecha_extraccion"] == latest_date]
    stats["fecha_actual"] = latest_date.strftime("%Y-%m-%d") if pd.notna(latest_date) else ""
    stats["indicadores_actuales"] = len(latest)

    # Análisis por indicador clave
    stats["series"] = {}
    stats["variaciones"] = {}

    for key_name in KEY_INDICATORS:
        series = _get_series(df_history, key_name)
        if series.empty:
            continue

        serie_data = _analyze_series(series, key_name)
        stats["series"][key_name] = serie_data

        # Variación vs extracción anterior
        variation = _calculate_variation(series)
        stats["variaciones"][key_name] = variation

        direction = "↑" if variation.get("cambio_pct", 0) > 0 else "↓" if variation.get("cambio_pct", 0) < 0 else "="
        print(f"  {key_name}: {variation.get('valor_actual', 0):,.2f} {direction} ({variation.get('cambio_pct', 0):+.2f}%)")

    # Tabla de todos los indicadores actuales con variación
    stats["tabla_actual"] = _build_current_table(df_history)

    # Distribución por sección
    stats["por_seccion"] = _count_by_section(latest)

    print(f"  Análisis completado: {len(stats['series'])} series temporales")
    return stats


def _get_series(df: pd.DataFrame, indicator_name: str) -> pd.DataFrame:
    """Obtiene la serie temporal de un indicador."""
    mask = df["indicador"].str.contains(indicator_name, case=False, na=False)
    # Si hay match exacto, preferirlo
    exact = df[df["indicador"] == indicator_name]
    if not exact.empty:
        return exact.sort_values("fecha_extraccion")
    return df[mask].sort_values("fecha_extraccion")


def _analyze_series(series: pd.DataFrame, name: str) -> dict:
    """Analiza una serie temporal individual."""
    values = series["valor"].dropna()
    dates = series["fecha_extraccion"].dropna()

    if values.empty:
        return {}

    return {
        "nombre": name,
        "fechas": dates.dt.strftime("%Y-%m-%d").tolist(),
        "valores": [round(float(v), 2) for v in values],
        "min": round(float(values.min()), 2),
        "max": round(float(values.max()), 2),
        "mean": round(float(values.mean()), 2),
        "std": round(float(values.std()), 2) if len(values) > 1 else 0.0,
        "first": round(float(values.iloc[0]), 2),
        "last": round(float(values.iloc[-1]), 2),
        "count": len(values),
    }


def _calculate_variation(series: pd.DataFrame) -> dict:
    """Calcula la variación entre las dos últimas extracciones."""
    values = series["valor"].dropna()

    if len(values) < 2:
        current = float(values.iloc[-1]) if len(values) == 1 else 0
        return {"valor_actual": current, "valor_anterior": current, "cambio_abs": 0, "cambio_pct": 0}

    current = float(values.iloc[-1])
    previous = float(values.iloc[-2])
    change_abs = current - previous
    change_pct = (change_abs / previous * 100) if previous != 0 else 0

    return {
        "valor_actual": round(current, 2),
        "valor_anterior": round(previous, 2),
        "cambio_abs": round(change_abs, 2),
        "cambio_pct": round(change_pct, 4),
    }


def _build_current_table(df: pd.DataFrame) -> list[dict]:
    """Construye tabla con valores actuales y variaciones."""
    latest_date = df["fecha_extraccion"].max()
    latest = df[df["fecha_extraccion"] == latest_date]

    dates = sorted(df["fecha_extraccion"].dropna().unique())
    previous_date = dates[-2] if len(dates) >= 2 else None

    rows = []
    for _, row in latest.iterrows():
        entry = {
            "seccion": row.get("seccion", ""),
            "indicador": row.get("indicador", ""),
            "valor_raw": row.get("valor_raw", ""),
            "valor": round(float(row["valor"]), 2) if pd.notna(row.get("valor")) else None,
            "tipo": row.get("tipo", ""),
            "unidad": row.get("unidad", ""),
            "cambio_pct": 0,
            "direccion": "=",
        }

        if previous_date is not None:
            prev = df[
                (df["fecha_extraccion"] == previous_date) &
                (df["indicador"] == row["indicador"])
            ]
            if not prev.empty and pd.notna(prev.iloc[0]["valor"]) and pd.notna(row["valor"]):
                prev_val = float(prev.iloc[0]["valor"])
                curr_val = float(row["valor"])
                if prev_val != 0:
                    pct = (curr_val - prev_val) / prev_val * 100
                    entry["cambio_pct"] = round(pct, 4)
                    entry["direccion"] = "up" if pct > 0 else "down" if pct < 0 else "="

        rows.append(entry)

    return rows


def _count_by_section(df: pd.DataFrame) -> dict:
    """Cuenta indicadores por sección."""
    if df.empty:
        return {}
    counts = df.groupby("seccion").size().to_dict()
    return {str(k): int(v) for k, v in counts.items()}
