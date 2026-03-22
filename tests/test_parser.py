"""
Tests unitarios del parser de indicadores.
Valida parsing de montos chilenos, porcentajes y detección de tipos.
"""

import pytest
from src.parser import (
    parse_amount,
    parse_percentage,
    parse_value,
    detect_type,
    detect_unit,
    clean_indicator_name,
    format_clp,
    format_percentage,
    parse_single,
)


# ──────────────────────────────────────────────
# Tests de parse_amount
# ──────────────────────────────────────────────

class TestParseAmount:
    def test_monto_entero_simple(self):
        assert parse_amount("$500.000") == 500000.0

    def test_monto_entero_grande(self):
        assert parse_amount("$1.234.567") == 1234567.0

    def test_monto_con_decimales(self):
        assert parse_amount("$38.571,52") == 38571.52

    def test_monto_sin_signo(self):
        assert parse_amount("1.234.567") == 1234567.0

    def test_monto_cero(self):
        assert parse_amount("$0") == 0.0

    def test_monto_pequeño(self):
        assert parse_amount("$953,75") == 953.75

    def test_monto_sin_puntos(self):
        assert parse_amount("$500000") == 500000.0

    def test_monto_vacio(self):
        assert parse_amount("") is None

    def test_monto_invalido(self):
        assert parse_amount("abc") is None


# ──────────────────────────────────────────────
# Tests de parse_percentage
# ──────────────────────────────────────────────

class TestParsePercentage:
    def test_porcentaje_con_decimales(self):
        assert parse_percentage("11,44%") == 11.44

    def test_porcentaje_entero(self):
        assert parse_percentage("7,00%") == 7.0

    def test_porcentaje_cero(self):
        assert parse_percentage("0,00%") == 0.0

    def test_porcentaje_pequeño(self):
        assert parse_percentage("0,60%") == 0.6

    def test_porcentaje_con_espacios(self):
        assert parse_percentage(" 3,00% ") == 3.0


# ──────────────────────────────────────────────
# Tests de parse_value
# ──────────────────────────────────────────────

class TestParseValue:
    def test_detecta_porcentaje(self):
        assert parse_value("11,44%") == 11.44

    def test_detecta_monto(self):
        assert parse_value("$38.571,52") == 38571.52

    def test_valor_vacio(self):
        assert parse_value("") is None

    def test_valor_none(self):
        assert parse_value(None) is None


# ──────────────────────────────────────────────
# Tests de detect_type
# ──────────────────────────────────────────────

class TestDetectType:
    def test_tipo_porcentaje(self):
        assert detect_type("11,44%") == "porcentaje"

    def test_tipo_monto_con_peso(self):
        assert detect_type("$500.000") == "monto"

    def test_tipo_monto_sin_peso(self):
        assert detect_type("1.234.567") == "monto"

    def test_tipo_otro(self):
        assert detect_type("texto") == "otro"


# ──────────────────────────────────────────────
# Tests de detect_unit
# ──────────────────────────────────────────────

class TestDetectUnit:
    def test_unidad_porcentaje(self):
        assert detect_unit("11,44%", "Capital") == "%"

    def test_unidad_uf(self):
        assert detect_unit("$38.571,52", "UF") == "UF"

    def test_unidad_utm(self):
        assert detect_unit("$67.294", "UTM") == "UTM"

    def test_unidad_dolar(self):
        assert detect_unit("$953,75", "Dólar Observado") == "USD"

    def test_unidad_euro(self):
        assert detect_unit("$1.038,42", "Euro") == "EUR"

    def test_unidad_clp_default(self):
        assert detect_unit("$500.000", "Renta Mínima") == "CLP"


# ──────────────────────────────────────────────
# Tests de clean_indicator_name
# ──────────────────────────────────────────────

class TestCleanIndicatorName:
    def test_limpia_espacios_multiples(self):
        assert clean_indicator_name("Capital   AFP") == "Capital AFP"

    def test_limpia_guiones_inicio(self):
        assert clean_indicator_name("- Capital") == "Capital"

    def test_limpia_puntos_final(self):
        assert clean_indicator_name("Capital.") == "Capital"

    def test_preserva_texto_normal(self):
        assert clean_indicator_name("UF") == "UF"


# ──────────────────────────────────────────────
# Tests de format_clp
# ──────────────────────────────────────────────

class TestFormatCLP:
    def test_formato_entero(self):
        result = format_clp(1234567)
        assert result == "$1.234.567"

    def test_formato_cero(self):
        assert format_clp(0) == "$0"

    def test_formato_none(self):
        assert format_clp(None) == "$0"

    def test_formato_decimal(self):
        result = format_clp(38571.52)
        assert "38.571" in result


# ──────────────────────────────────────────────
# Tests de format_percentage
# ──────────────────────────────────────────────

class TestFormatPercentage:
    def test_formato_porcentaje(self):
        assert format_percentage(11.44) == "11,44%"

    def test_formato_cero(self):
        assert format_percentage(0) == "0,00%"

    def test_formato_none(self):
        assert format_percentage(None) == "0%"


# ──────────────────────────────────────────────
# Tests de parse_single
# ──────────────────────────────────────────────

class TestParseSingle:
    def test_parse_indicador_monto(self):
        item = {"seccion": "Test", "indicador": "UF", "valor_raw": "$38.571,52"}
        result = parse_single(item)
        assert result is not None
        assert result["valor"] == 38571.52
        assert result["tipo"] == "monto"
        assert result["unidad"] == "UF"

    def test_parse_indicador_porcentaje(self):
        item = {"seccion": "AFP", "indicador": "Capital", "valor_raw": "11,44%"}
        result = parse_single(item)
        assert result is not None
        assert result["valor"] == 11.44
        assert result["tipo"] == "porcentaje"

    def test_parse_indicador_vacio(self):
        item = {"seccion": "Test", "indicador": "X", "valor_raw": ""}
        result = parse_single(item)
        assert result is None
