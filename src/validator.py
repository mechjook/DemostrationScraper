"""
Etapa 5 — VALIDADOR
Verifica integridad y consistencia de los datos almacenados.
"""

import os
import pandas as pd


class ValidationResult:
    """Resultado de una validación."""

    def __init__(self, name: str):
        self.name = name
        self.is_valid = True
        self.errors: list[str] = []
        self.warnings: list[str] = []

    def error(self, msg: str):
        self.is_valid = False
        self.errors.append(msg)

    def warn(self, msg: str):
        self.warnings.append(msg)


def validate_data(data_dir: str, df: pd.DataFrame) -> ValidationResult:
    """Ejecuta todas las validaciones sobre los datos almacenados."""
    print("\n" + "=" * 60)
    print("ETAPA 5: VALIDACIÓN DE INTEGRIDAD")
    print("=" * 60)

    result = ValidationResult("Validación de datos")

    # 1. Verificar que el archivo existe
    _validate_file_exists(data_dir, result)

    # 2. Verificar estructura del DataFrame
    _validate_schema(df, result)

    # 3. Verificar que no hay registros vacíos
    _validate_no_nulls(df, result)

    # 4. Verificar consistencia de valores
    _validate_values(df, result)

    # 5. Verificar fechas
    _validate_dates(df, result)

    # 6. Verificar duplicados
    _validate_duplicates(df, result)

    # Resumen
    if result.is_valid:
        print(f"  VALIDACIÓN OK — {len(result.warnings)} advertencias")
    else:
        print(f"  VALIDACIÓN FALLIDA — {len(result.errors)} errores, {len(result.warnings)} advertencias")

    for err in result.errors:
        print(f"    ERROR: {err}")
    for warn in result.warnings:
        print(f"    WARN: {warn}")

    return result


def _validate_file_exists(data_dir: str, result: ValidationResult):
    """Verifica que el directorio de datos y el CSV existen."""
    if not os.path.isdir(data_dir):
        result.error(f"Directorio no existe: {data_dir}")
        return

    csv_path = os.path.join(data_dir, "indicadores_historico.csv")
    if not os.path.isfile(csv_path):
        result.warn("CSV histórico no existe aún (primera ejecución)")


def _validate_schema(df: pd.DataFrame, result: ValidationResult):
    """Verifica que el DataFrame tiene las columnas esperadas."""
    required = {"fecha_extraccion", "indicador", "valor", "tipo"}

    if df.empty:
        result.warn("DataFrame vacío — sin datos para validar")
        return

    missing = required - set(df.columns)
    if missing:
        result.error(f"Columnas faltantes: {missing}")


def _validate_no_nulls(df: pd.DataFrame, result: ValidationResult):
    """Verifica que los campos clave no tengan valores nulos."""
    if df.empty:
        return

    for col in ["indicador", "fecha_extraccion"]:
        if col in df.columns:
            nulls = df[col].isna().sum()
            if nulls > 0:
                result.error(f"Columna '{col}' tiene {nulls} valores nulos")

    # Valor puede ser nulo (indicadores sin valor numérico)
    if "valor" in df.columns:
        nulls = df["valor"].isna().sum()
        if nulls > 0:
            result.warn(f"Columna 'valor' tiene {nulls} valores nulos")


def _validate_values(df: pd.DataFrame, result: ValidationResult):
    """Verifica consistencia de valores numéricos."""
    if df.empty or "valor" not in df.columns:
        return

    # Valores negativos inesperados
    negatives = (df["valor"].dropna() < 0).sum()
    if negatives > 0:
        result.warn(f"{negatives} valores negativos encontrados")

    # Valores extremadamente grandes (posible error de parsing)
    threshold = 1e12  # 1 billón
    outliers = (df["valor"].dropna().abs() > threshold).sum()
    if outliers > 0:
        result.error(f"{outliers} valores superan el umbral de {threshold:,.0f}")

    # Tipos válidos
    if "tipo" in df.columns:
        valid_types = {"monto", "porcentaje", "otro"}
        invalid = df[~df["tipo"].isin(valid_types)]["tipo"].unique()
        if len(invalid) > 0:
            result.warn(f"Tipos no reconocidos: {invalid.tolist()}")


def _validate_dates(df: pd.DataFrame, result: ValidationResult):
    """Verifica consistencia de fechas de extracción."""
    if df.empty or "fecha_extraccion" not in df.columns:
        return

    dates = pd.to_datetime(df["fecha_extraccion"], errors="coerce")
    invalid_dates = dates.isna().sum()
    if invalid_dates > 0:
        result.error(f"{invalid_dates} fechas de extracción inválidas")

    # Fechas futuras
    future = (dates.dropna() > pd.Timestamp.now()).sum()
    if future > 0:
        result.warn(f"{future} registros con fechas futuras")


def _validate_duplicates(df: pd.DataFrame, result: ValidationResult):
    """Verifica duplicados exactos en la misma fecha."""
    if df.empty:
        return

    key_cols = ["fecha_extraccion", "indicador"]
    if all(c in df.columns for c in key_cols):
        dupes = df.duplicated(subset=key_cols, keep=False).sum()
        if dupes > 0:
            result.warn(f"{dupes} registros duplicados (misma fecha + indicador)")


def validate_parsed_indicators(indicators: list[dict]) -> ValidationResult:
    """Valida una lista de indicadores parseados antes de almacenar."""
    result = ValidationResult("Validación pre-almacenamiento")

    if not indicators:
        result.error("Lista de indicadores vacía")
        return result

    for i, ind in enumerate(indicators):
        if not ind.get("indicador"):
            result.error(f"Indicador #{i} sin nombre")
        if ind.get("valor") is None:
            result.warn(f"Indicador '{ind.get('indicador', '?')}' sin valor numérico")

    return result
