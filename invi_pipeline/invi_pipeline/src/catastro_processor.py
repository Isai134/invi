from __future__ import annotations

from pathlib import Path
import pandas as pd
import geopandas as gpd
from io_utils import read_csv_flexible, normalize_text_series


REQUIRED_COLUMNS = [
    "fid", "calle_numero", "colonia", "alcaldia", "sup_terreno", "sup_construccion",
    "anio_construccion", "valor_unitario_suelo", "valor_suelo"
]


class CatastroProcessor:
    def __init__(self, config: dict, logger):
        self.config = config
        self.logger = logger

    def load_catastro_csv(self, csv_path: Path) -> pd.DataFrame:
        df = read_csv_flexible(csv_path, self.config["encoding_candidates"])
        rename_map = {c.lower(): c.lower() for c in df.columns}
        df = df.rename(columns=rename_map)
        if "fid" not in df.columns and "FID" in df.columns:
            df = df.rename(columns={"FID": "fid"})
        for col in ["colonia", "alcaldia", "calle_numero"]:
            if col in df.columns:
                df[col] = normalize_text_series(df[col])
        for col in ["sup_terreno", "sup_construccion", "anio_construccion", "valor_unitario_suelo", "valor_suelo"]:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")
        missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
        if missing:
            self.logger.warning("Faltan columnas en catastro %s: %s", csv_path.name, missing)
        self.logger.info("Catastro cargado: %s (%s filas)", csv_path.name, len(df))
        return df

    def load_catastro_shp(self, shp_path: Path) -> gpd.GeoDataFrame:
        gdf = gpd.read_file(shp_path)
        gdf.columns = [c.lower() for c in gdf.columns]
        if "fid" not in gdf.columns and "objectid" in gdf.columns:
            gdf = gdf.rename(columns={"objectid": "fid"})
        self.logger.info("Shapefile catastral cargado: %s (%s geometrías)", shp_path.name, len(gdf))
        return gdf

    def merge_catastro(self, df: pd.DataFrame, gdf: gpd.GeoDataFrame | None = None) -> gpd.GeoDataFrame:
        if gdf is None:
            return gpd.GeoDataFrame(df.copy())
        if "fid" not in df.columns or "fid" not in gdf.columns:
            raise KeyError("Se requiere la columna 'fid' tanto en CSV como en Shapefile")
        merged = gdf.merge(df, on="fid", how="left", suffixes=("_geo", ""))
        if "alcaldia" in merged.columns:
            merged["alcaldia"] = normalize_text_series(merged["alcaldia"])
        if "colonia" in merged.columns:
            merged["colonia"] = normalize_text_series(merged["colonia"])
        if "calle_numero" in merged.columns:
            merged["calle_numero"] = normalize_text_series(merged["calle_numero"])
        merged["ratio_construccion_terreno"] = (
            merged["sup_construccion"] / merged["sup_terreno"]
        ).replace([float("inf"), -float("inf")], pd.NA)
        return merged
