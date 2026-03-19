from __future__ import annotations

from pathlib import Path
import pandas as pd
import geopandas as gpd
from io_utils import read_csv_flexible, normalize_text_series


class SEDUVIProcessor:
    def __init__(self, config: dict, viable_keywords: list[str], review_keywords: list[str], no_viable_keywords: list[str], logger=None):
        self.config = config
        self.viable_keywords = [k.upper() for k in viable_keywords]
        self.review_keywords = [k.upper() for k in review_keywords]
        self.no_viable_keywords = [k.upper() for k in no_viable_keywords]
        self.logger = logger

    def load_csv(self, csv_path: Path) -> pd.DataFrame:
        df = read_csv_flexible(csv_path, self.config["encoding_candidates"])
        df.columns = [c.lower() for c in df.columns]
        if "fid" not in df.columns:
            candidates = [c for c in df.columns if c.lower() in {"fid_predio", "id", "objectid"}]
            if candidates:
                df = df.rename(columns={candidates[0]: "fid"})
        return df

    def load_shp(self, shp_path: Path) -> gpd.GeoDataFrame:
        gdf = gpd.read_file(shp_path)
        gdf.columns = [c.lower() for c in gdf.columns]
        if "fid" not in gdf.columns and "objectid" in gdf.columns:
            gdf = gdf.rename(columns={"objectid": "fid"})
        return gdf

    def classify_normative_viability(self, text: str) -> str:
        raw = str(text).upper()
        if any(k in raw for k in self.no_viable_keywords):
            return "no viable"
        if any(k in raw for k in self.viable_keywords):
            return "viable"
        if any(k in raw for k in self.review_keywords):
            return "revision manual"
        return "revision manual"

    def enrich_with_seduvi(self, predios: gpd.GeoDataFrame, seduvi_df: pd.DataFrame) -> gpd.GeoDataFrame:
        seduvi_df = seduvi_df.copy()
        seduvi_df.columns = [c.lower() for c in seduvi_df.columns]
        uso_col_candidates = [c for c in seduvi_df.columns if "uso" in c or "zon" in c or "norm" in c]
        uso_col = uso_col_candidates[0] if uso_col_candidates else None
        if uso_col is None:
            raise KeyError("No se encontró columna normativa / uso de suelo en SEDUVI")
        if "fid" not in seduvi_df.columns:
            raise KeyError("SEDUVI debe incluir columna 'fid' para cruce directo")
        seduvi_df["uso_suelo_raw"] = seduvi_df[uso_col].astype(str)
        seduvi_df["clasificacion_viabilidad"] = seduvi_df["uso_suelo_raw"].apply(self.classify_normative_viability)
        merged = predios.merge(
            seduvi_df[["fid", "uso_suelo_raw", "clasificacion_viabilidad"]].drop_duplicates("fid"),
            on="fid",
            how="left",
        )
        return merged
