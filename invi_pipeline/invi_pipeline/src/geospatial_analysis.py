from __future__ import annotations

import pandas as pd
import geopandas as gpd
from shapely.geometry import Point


class GeospatialAnalyzer:
    def __init__(self, filters: dict, logger=None):
        self.filters = filters
        self.logger = logger

    def add_basic_metrics(self, gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
        gdf = gdf.copy()
        gdf["ratio_construccion_terreno"] = (
            gdf["sup_construccion"] / gdf["sup_terreno"]
        ).replace([float("inf"), -float("inf")], pd.NA)
        gdf["valor_m2_suelo_estimado"] = gdf["valor_suelo"] / gdf["sup_terreno"]
        return gdf

    def apply_filters(self, gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
        gdf = self.add_basic_metrics(gdf)
        out = gdf.copy()
        out = out[out["sup_terreno"] >= self.filters["superficie_min_m2"]]
        out = out[out["ratio_construccion_terreno"].fillna(0) <= self.filters["max_ratio_construccion_terreno"]]
        out = out[out["alcaldia"].isin(self.filters["alcaldias_objetivo"])]
        if self.filters.get("solo_predios_habitacionales") and "clasificacion_viabilidad" in out.columns:
            out = out[out["clasificacion_viabilidad"].isin(["viable", "revision manual"])]
        presupuesto = self.filters.get("presupuesto_max_m2", {})
        if presupuesto:
            out["presupuesto_max_m2_alcaldia"] = out["alcaldia"].map(presupuesto)
            out = out[
                out["valor_m2_suelo_estimado"].fillna(out["valor_unitario_suelo"]) <= out["presupuesto_max_m2_alcaldia"].fillna(float("inf"))
            ]
        if self.logger:
            self.logger.info("Shortlist geoespacial generada: %s predios", len(out))
        return out

    def add_accessibility_stub(self, gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
        gdf = gdf.copy()
        # Placeholder claro: reemplazar por distancias reales a transporte/equipamiento.
        if "longitud" in gdf.columns and "latitud" in gdf.columns:
            valid = gdf[["longitud", "latitud"]].notna().all(axis=1)
            gdf["accessibility_score"] = valid.astype(int) * 0.6 + 0.2
        else:
            gdf["accessibility_score"] = 0.5
        return gdf

    def add_risk_stub(self, gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
        gdf = gdf.copy()
        # Placeholder claro: integrar capas de riesgo reales (inundación, fallas, conservación, etc.).
        gdf["risk_score"] = 0.8
        return gdf
