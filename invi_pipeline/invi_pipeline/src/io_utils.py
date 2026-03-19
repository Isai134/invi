from __future__ import annotations

from pathlib import Path
import pandas as pd
import geopandas as gpd


def read_csv_flexible(path: Path, encoding_candidates: list[str]) -> pd.DataFrame:
    last_error = None
    for encoding in encoding_candidates:
        try:
            return pd.read_csv(path, encoding=encoding, low_memory=False)
        except Exception as exc:
            last_error = exc
    raise ValueError(f"No se pudo leer {path} con encodings {encoding_candidates}: {last_error}")


def read_geofile(path: Path) -> gpd.GeoDataFrame:
    return gpd.read_file(path)


def normalize_text_series(series: pd.Series) -> pd.Series:
    return (
        series.astype(str)
        .str.strip()
        .str.upper()
        .str.replace(r"\s+", " ", regex=True)
    )
