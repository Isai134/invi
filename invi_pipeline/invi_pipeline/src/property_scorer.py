from __future__ import annotations

import numpy as np
import pandas as pd
import geopandas as gpd


class PropertyScorer:
    def __init__(self, weights: dict, logger=None):
        self.weights = weights
        self.logger = logger

    @staticmethod
    def _minmax(series: pd.Series) -> pd.Series:
        s = pd.to_numeric(series, errors="coerce")
        if s.notna().sum() == 0:
            return pd.Series(np.zeros(len(s)), index=s.index)
        min_v, max_v = s.min(), s.max()
        if pd.isna(min_v) or pd.isna(max_v) or max_v == min_v:
            return pd.Series(np.ones(len(s)) * 0.5, index=s.index)
        return (s - min_v) / (max_v - min_v)

    def score(self, gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
        gdf = gdf.copy()
        gdf["score_tamano"] = self._minmax(gdf["sup_terreno"])
        gdf["score_subutilizacion"] = 1 - self._minmax(gdf["ratio_construccion_terreno"].fillna(0))
        map_viability = {"viable": 1.0, "revision manual": 0.6, "no viable": 0.0}
        gdf["score_viabilidad_normativa"] = gdf.get("clasificacion_viabilidad", pd.Series(index=gdf.index)).map(map_viability).fillna(0.5)
        gdf["score_accesibilidad"] = gdf.get("accessibility_score", 0.5)
        gdf["score_riesgo"] = gdf.get("risk_score", 0.5)
        commercial_conf = gdf.get("commercial_confidence_score", pd.Series([0.0] * len(gdf), index=gdf.index))
        gdf["score_validacion_comercial"] = commercial_conf

        gdf["opportunity_score"] = (
            self.weights["tamano"] * gdf["score_tamano"]
            + self.weights["subutilizacion"] * gdf["score_subutilizacion"]
            + self.weights["viabilidad_normativa"] * gdf["score_viabilidad_normativa"]
            + self.weights["accesibilidad"] * gdf["score_accesibilidad"]
            + self.weights["riesgo"] * gdf["score_riesgo"]
            + self.weights["validacion_comercial"] * gdf["score_validacion_comercial"]
        )
        gdf = gdf.sort_values("opportunity_score", ascending=False)
        if self.logger:
            self.logger.info("Scoring completado para %s predios", len(gdf))
        return gdf
