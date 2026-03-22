"""
Tests unitarios del validador de datos.
"""

import pytest
import pandas as pd
import numpy as np

from src.validator import (
    ValidationResult,
    validate_parsed_indicators,
    _validate_schema,
    _validate_no_nulls,
    _validate_values,
    _validate_dates,
    _validate_duplicates,
)


# ──────────────────────────────────────────────
# Tests de ValidationResult
# ──────────────────────────────────────────────

class TestValidationResult:
    def test_initial_state(self):
        r = ValidationResult("test")
        assert r.is_valid is True
        assert r.errors == []
        assert r.warnings == []

    def test_error_marks_invalid(self):
        r = ValidationResult("test")
        r.error("algo falló")
        assert r.is_valid is False
        assert len(r.errors) == 1

    def test_warning_keeps_valid(self):
        r = ValidationResult("test")
        r.warn("algo raro")
        assert r.is_valid is True
        assert len(r.warnings) == 1


# ──────────────────────────────────────────────
# Tests de validate_parsed_indicators
# ──────────────────────────────────────────────

class TestValidateParsedIndicators:
    def test_lista_vacia(self):
        result = validate_parsed_indicators([])
        assert result.is_valid is False

    def test_indicador_sin_nombre(self):
        result = validate_parsed_indicators([{"indicador": "", "valor": 100}])
        assert result.is_valid is False

    def test_indicador_sin_valor(self):
        result = validate_parsed_indicators([{"indicador": "UF", "valor": None}])
        assert result.is_valid is True  # warn, no error
        assert len(result.warnings) == 1

    def test_indicador_valido(self):
        result = validate_parsed_indicators([{"indicador": "UF", "valor": 38571.52}])
        assert result.is_valid is True
        assert len(result.warnings) == 0


# ──────────────────────────────────────────────
# Tests de validaciones internas
# ──────────────────────────────────────────────

class TestValidateSchema:
    def test_schema_valido(self):
        df = pd.DataFrame({
            "fecha_extraccion": ["2025-01-01"],
            "indicador": ["UF"],
            "valor": [38571.52],
            "tipo": ["monto"],
        })
        result = ValidationResult("test")
        _validate_schema(df, result)
        assert result.is_valid is True

    def test_columna_faltante(self):
        df = pd.DataFrame({"indicador": ["UF"]})
        result = ValidationResult("test")
        _validate_schema(df, result)
        assert result.is_valid is False

    def test_dataframe_vacio(self):
        df = pd.DataFrame()
        result = ValidationResult("test")
        _validate_schema(df, result)
        assert result.is_valid is True  # solo warn


class TestValidateNoNulls:
    def test_sin_nulos(self):
        df = pd.DataFrame({
            "indicador": ["UF", "UTM"],
            "fecha_extraccion": ["2025-01-01", "2025-01-01"],
            "valor": [38571, 67294],
        })
        result = ValidationResult("test")
        _validate_no_nulls(df, result)
        assert result.is_valid is True

    def test_indicador_nulo(self):
        df = pd.DataFrame({
            "indicador": [None, "UTM"],
            "fecha_extraccion": ["2025-01-01", "2025-01-01"],
        })
        result = ValidationResult("test")
        _validate_no_nulls(df, result)
        assert result.is_valid is False


class TestValidateValues:
    def test_valores_normales(self):
        df = pd.DataFrame({
            "valor": [38571, 67294, 11.44],
            "tipo": ["monto", "monto", "porcentaje"],
        })
        result = ValidationResult("test")
        _validate_values(df, result)
        assert result.is_valid is True

    def test_valor_extremo(self):
        df = pd.DataFrame({
            "valor": [1e13],
            "tipo": ["monto"],
        })
        result = ValidationResult("test")
        _validate_values(df, result)
        assert result.is_valid is False


class TestValidateDates:
    def test_fechas_validas(self):
        df = pd.DataFrame({
            "fecha_extraccion": pd.to_datetime(["2025-01-01", "2025-02-01"]),
        })
        result = ValidationResult("test")
        _validate_dates(df, result)
        assert result.is_valid is True


class TestValidateDuplicates:
    def test_sin_duplicados(self):
        df = pd.DataFrame({
            "fecha_extraccion": ["2025-01-01", "2025-01-01"],
            "indicador": ["UF", "UTM"],
        })
        result = ValidationResult("test")
        _validate_duplicates(df, result)
        assert result.is_valid is True
        assert len(result.warnings) == 0

    def test_con_duplicados(self):
        df = pd.DataFrame({
            "fecha_extraccion": ["2025-01-01", "2025-01-01"],
            "indicador": ["UF", "UF"],
        })
        result = ValidationResult("test")
        _validate_duplicates(df, result)
        assert len(result.warnings) == 1
