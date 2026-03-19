from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
RESULTS_DIR = BASE_DIR / "results"
LOGS_DIR = BASE_DIR / "logs"

for path in [DATA_DIR, RAW_DIR, PROCESSED_DIR, RESULTS_DIR, LOGS_DIR]:
    path.mkdir(parents=True, exist_ok=True)

SIG_CONFIG = {
    "alcaldias_objetivo": ["TLALPAN", "IZTACALCO", "COYOACAN", "BENITO JUAREZ"],
    "encoding_candidates": ["utf-8", "utf-8-sig", "latin1", "cp1252"],
    "catastro_file_glob": "*catastro*.csv",
    "seduvi_csv_glob": "*.csv",
    "catastro_shp_glob": "*.shp",
    "seduvi_shp_glob": "*.shp",
}

FILTERS = {
    "superficie_min_m2": 800.0,
    "max_ratio_construccion_terreno": 0.45,
    "min_anio_construccion": None,
    "alcaldias_objetivo": ["TLALPAN", "IZTACALCO", "COYOACAN", "BENITO JUAREZ"],
    "presupuesto_max_m2": {
        "BENITO JUAREZ": 22000,
        "COYOACAN": 20000,
        "CUAUHTEMOC": 20000,
        "IZTACALCO": 18000,
        "MIGUEL HIDALGO": 18000,
        "TLALPAN": 17000,
    },
    "solo_predios_habitacionales": True,
}

SCORING_WEIGHTS = {
    "tamano": 0.20,
    "subutilizacion": 0.20,
    "viabilidad_normativa": 0.20,
    "accesibilidad": 0.15,
    "riesgo": 0.10,
    "validacion_comercial": 0.15,
}

# Catálogos simples y fáciles de mantener
VIABLE_KEYWORDS = [
    "H", "HC", "HM", "HABITACIONAL", "MIXTO", "VIVIENDA", "H/",
]
REVIEW_KEYWORDS = [
    "EQUIPAMIENTO", "CORREDOR", "CENTRO DE BARRIO", "MIXTO", "Z",
]
NO_VIABLE_KEYWORDS = [
    "AV", "AREA VERDE", "CONSERVACION", "INDUSTRIAL", "RIESGO", "PATRIMONIAL",
]

COMMERCIAL_SOURCES = {
    "google_maps": {"enabled": False},
    "inmuebles24": {"enabled": True},
    "lamudi": {"enabled": True},
    "mercado_libre_inmuebles": {"enabled": True},
}

SCRAPING = {
    "headless": True,
    "implicit_wait": 8,
    "page_load_timeout": 30,
    "max_retries": 3,
    "sleep_between_requests": 2.0,
    "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
}

OUTPUT = {
    "master_csv": RESULTS_DIR / "predios_maestro.csv",
    "shortlist_csv": RESULTS_DIR / "predios_shortlist.csv",
    "shortlist_geojson": RESULTS_DIR / "predios_shortlist.geojson",
    "commercial_matches_csv": RESULTS_DIR / "commercial_matches.csv",
    "interactive_map": RESULTS_DIR / "predios_shortlist_map.html",
    "log_file": LOGS_DIR / "pipeline.log",
}
