"""
Test de integración del pipeline completo.
Ejecuta todas las etapas y verifica resultados.
"""

import os
import tempfile

import pytest
import pandas as pd

from src.scraper import _sample_indicators
from src.parser import parse_indicators
from src.storage import store_indicators, load_history
from src.analytics import run_analytics
from src.validator import validate_data
from src.seed import generate_seed_data


@pytest.fixture
def tmp_dir():
    with tempfile.TemporaryDirectory() as d:
        yield d


class TestSampleData:
    def test_sample_indicators_not_empty(self):
        indicators = _sample_indicators()
        assert len(indicators) > 0

    def test_sample_has_required_fields(self):
        indicators = _sample_indicators()
        for ind in indicators:
            assert "seccion" in ind
            assert "indicador" in ind
            assert "valor_raw" in ind

    def test_sample_has_key_indicators(self):
        indicators = _sample_indicators()
        names = [i["indicador"] for i in indicators]
        assert "UF" in names
        assert "UTM" in names
        assert "Dólar Observado" in names
        assert "Euro" in names


class TestSeedData:
    def test_generates_csv(self, tmp_dir):
        generate_seed_data(tmp_dir, num_weeks=4)
        csv_path = os.path.join(tmp_dir, "indicadores_historico.csv")
        assert os.path.isfile(csv_path)

    def test_seed_has_multiple_dates(self, tmp_dir):
        generate_seed_data(tmp_dir, num_weeks=4)
        df = load_history(tmp_dir)
        assert df["fecha_extraccion"].nunique() >= 4

    def test_seed_no_overwrite(self, tmp_dir):
        generate_seed_data(tmp_dir, num_weeks=4)
        df1 = load_history(tmp_dir)
        generate_seed_data(tmp_dir, num_weeks=8)  # no debe sobrescribir
        df2 = load_history(tmp_dir)
        assert len(df1) == len(df2)


class TestFullPipeline:
    def test_pipeline_end_to_end(self, tmp_dir):
        """Ejecuta el pipeline completo y verifica cada etapa."""
        data_dir = os.path.join(tmp_dir, "data")
        output_dir = os.path.join(tmp_dir, "output")

        # Etapa 0: Seed
        generate_seed_data(data_dir, num_weeks=4)

        # Etapa 1: Scraping (sample)
        raw = _sample_indicators()
        assert len(raw) > 0

        # Etapa 2: Parsing
        parsed = parse_indicators(raw)
        assert len(parsed) > 0
        for p in parsed:
            assert "indicador" in p
            assert "valor" in p

        # Etapa 3: Storage
        result = store_indicators(parsed, data_dir)
        assert result["new_rows"] > 0
        assert result["total_rows"] > 0

        # Cargar histórico
        df = load_history(data_dir)
        assert not df.empty
        assert "valor" in df.columns
        assert "indicador" in df.columns

        # Etapa 4: Analytics
        stats = run_analytics(data_dir, df)
        assert "total_registros" in stats
        assert "series" in stats

        # Etapa 5: Validación
        validation = validate_data(data_dir, df)
        assert validation.is_valid is True

    def test_storage_append(self, tmp_dir):
        """Verifica que el storage hace append y no sobrescribe."""
        data_dir = os.path.join(tmp_dir, "data")

        raw = _sample_indicators()
        parsed = parse_indicators(raw)

        # Primera inserción
        r1 = store_indicators(parsed, data_dir)
        n1 = r1["total_rows"]

        # Segunda inserción
        r2 = store_indicators(parsed, data_dir)
        n2 = r2["total_rows"]

        assert n2 > n1
