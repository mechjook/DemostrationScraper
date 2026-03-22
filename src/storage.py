"""
Etapa 3 — STORAGE
Almacena indicadores como serie temporal en CSV y JSON.
Append por fecha de extracción, sin sobrescribir datos anteriores.
"""

import os
import csv
import json
from datetime import datetime

import pandas as pd

HISTORY_CSV = "indicadores_historico.csv"
LATEST_JSON = "indicadores_latest.json"
CSV_COLUMNS = ["fecha_extraccion", "seccion", "indicador", "valor_raw", "valor", "tipo", "unidad"]


def store_indicators(indicators: list[dict], data_dir: str) -> dict:
    """Almacena indicadores: append al CSV histórico + snapshot JSON."""
    print("\n" + "=" * 60)
    print("ETAPA 3: ALMACENAMIENTO DE DATOS")
    print("=" * 60)

    os.makedirs(data_dir, exist_ok=True)

    fecha = datetime.now().strftime("%Y-%m-%d")

    # Agregar fecha de extracción a cada registro
    records = []
    for ind in indicators:
        record = {**ind, "fecha_extraccion": fecha}
        records.append(record)

    # Append al CSV histórico
    csv_path = os.path.join(data_dir, HISTORY_CSV)
    new_rows = _append_csv(csv_path, records)
    print(f"  CSV histórico: {csv_path}")
    print(f"  Registros nuevos: {new_rows}")

    # Snapshot JSON con datos actuales
    json_path = os.path.join(data_dir, LATEST_JSON)
    _save_json(json_path, records, fecha)
    print(f"  Snapshot JSON: {json_path}")

    # Leer histórico completo
    df = load_history(data_dir)
    total_rows = len(df)
    unique_dates = df["fecha_extraccion"].nunique() if len(df) > 0 else 0
    print(f"  Total registros históricos: {total_rows}")
    print(f"  Fechas de extracción: {unique_dates}")

    return {
        "csv_path": csv_path,
        "json_path": json_path,
        "new_rows": new_rows,
        "total_rows": total_rows,
        "unique_dates": unique_dates,
    }


def _append_csv(path: str, records: list[dict]) -> int:
    """Agrega registros al CSV histórico. Crea el archivo si no existe."""
    file_exists = os.path.isfile(path)

    with open(path, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS, extrasaction="ignore")
        if not file_exists:
            writer.writeheader()
        for record in records:
            writer.writerow(record)

    return len(records)


def _save_json(path: str, records: list[dict], fecha: str):
    """Guarda snapshot JSON con los datos actuales."""
    snapshot = {
        "fecha_extraccion": fecha,
        "total_indicadores": len(records),
        "indicadores": records,
    }

    with open(path, "w", encoding="utf-8") as f:
        json.dump(snapshot, f, ensure_ascii=False, indent=2, default=str)


def load_history(data_dir: str) -> pd.DataFrame:
    """Carga el CSV histórico como DataFrame."""
    csv_path = os.path.join(data_dir, HISTORY_CSV)

    if not os.path.isfile(csv_path):
        return pd.DataFrame(columns=CSV_COLUMNS)

    df = pd.read_csv(csv_path, encoding="utf-8")

    # Asegurar tipos
    if "valor" in df.columns:
        df["valor"] = pd.to_numeric(df["valor"], errors="coerce")
    if "fecha_extraccion" in df.columns:
        df["fecha_extraccion"] = pd.to_datetime(df["fecha_extraccion"], errors="coerce")

    return df


def get_latest_values(data_dir: str) -> pd.DataFrame:
    """Obtiene los valores más recientes de cada indicador."""
    df = load_history(data_dir)
    if df.empty:
        return df

    latest_date = df["fecha_extraccion"].max()
    return df[df["fecha_extraccion"] == latest_date].copy()


def get_indicator_series(data_dir: str, indicator_name: str) -> pd.DataFrame:
    """Obtiene la serie temporal de un indicador específico."""
    df = load_history(data_dir)
    if df.empty:
        return df

    mask = df["indicador"].str.contains(indicator_name, case=False, na=False)
    series = df[mask].sort_values("fecha_extraccion")
    return series
