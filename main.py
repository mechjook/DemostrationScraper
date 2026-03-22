"""
Web Scraper Indicadores Previsionales Chile — Pipeline Principal
================================================================
Demostración de capacidades de web scraping, monitoreo de datos
variables en el tiempo y visualización de series temporales.

Etapas:
  0. Generación de datos seed (historial simulado)
  1. Scraping de indicadores desde Previred
  2. Parsing y normalización de valores
  3. Almacenamiento como serie temporal
  4. Análisis y cálculo de variaciones
  5. Validación de integridad
  6. Generación de dashboard HTML interactivo

Autor: José Nicolás Candia (@mechjook)
"""

import os
import sys
import time

# Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")


def main():
    start = time.time()

    print("╔══════════════════════════════════════════════════════════════╗")
    print("║   SCRAPER INDICADORES PREVISIONALES — PIPELINE AUTOMÁTICO   ║")
    print("╚══════════════════════════════════════════════════════════════╝")

    # --- Etapa 0: Datos seed ---
    from src.seed import generate_seed_data
    print("\n" + "=" * 60)
    print("ETAPA 0: GENERACIÓN DE DATOS SEED")
    print("=" * 60)
    generate_seed_data(DATA_DIR)

    # --- Etapa 1: Scraping ---
    from src.scraper import scrape_indicators
    print("\n" + "=" * 60)
    print("ETAPA 1: SCRAPING DE INDICADORES")
    print("=" * 60)
    raw_indicators = scrape_indicators()
    print(f"  Indicadores crudos: {len(raw_indicators)}")

    # --- Etapa 2: Parsing ---
    from src.parser import parse_indicators
    parsed = parse_indicators(raw_indicators)

    # --- Etapa 3: Storage ---
    from src.storage import store_indicators, load_history
    storage_result = store_indicators(parsed, DATA_DIR)

    # Cargar histórico completo
    df_history = load_history(DATA_DIR)

    # --- Etapa 4: Analytics ---
    from src.analytics import run_analytics
    stats = run_analytics(DATA_DIR, df_history)

    # --- Etapa 5: Validación ---
    from src.validator import validate_data
    validation = validate_data(DATA_DIR, df_history)

    if not validation.is_valid:
        print("\n⚠ DATOS INVÁLIDOS — revise los errores anteriores")

    # --- Etapa 6: Dashboard ---
    from src.dashboard import generate_dashboard
    dashboard_path = generate_dashboard(stats, df_history, OUTPUT_DIR)

    # --- Resumen final ---
    elapsed = time.time() - start
    print("\n" + "=" * 60)
    print("PIPELINE COMPLETADO")
    print("=" * 60)
    print(f"  Tiempo total       : {elapsed:.2f}s")
    print(f"  Indicadores        : {len(parsed)}")
    print(f"  Registros hist.    : {storage_result['total_rows']}")
    print(f"  Extracciones       : {storage_result['unique_dates']}")
    print(f"  Validación         : {'OK' if validation.is_valid else 'ERRORES'}")
    print(f"  Dashboard          : {dashboard_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
