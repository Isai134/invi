from __future__ import annotations

import sys
from pathlib import Path
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point

from config import SIG_CONFIG, FILTERS, SCORING_WEIGHTS, VIABLE_KEYWORDS, REVIEW_KEYWORDS, NO_VIABLE_KEYWORDS, OUTPUT
from logging_utils import setup_logger
from catastro_processor import CatastroProcessor
from seduvi_processor import SEDUVIProcessor
from geospatial_analysis import GeospatialAnalyzer
from property_scorer import PropertyScorer
from visualization import Visualizer


def build_geometry_from_latlon(df: pd.DataFrame) -> gpd.GeoDataFrame:
    if {"longitud", "latitud"}.issubset(df.columns):
        geom = [Point(xy) if pd.notna(xy[0]) and pd.notna(xy[1]) else None for xy in zip(df["longitud"], df["latitud"])]
        return gpd.GeoDataFrame(df.copy(), geometry=geom, crs="EPSG:4326")
    return gpd.GeoDataFrame(df.copy())


def demo_pipeline(catastro_csv: Path, seduvi_csv: Path | None = None):
    logger = setup_logger(OUTPUT["log_file"])
    logger.info("Iniciando pipeline demo INVI")

    cp = CatastroProcessor(SIG_CONFIG, logger)
    sp = SEDUVIProcessor(SIG_CONFIG, VIABLE_KEYWORDS, REVIEW_KEYWORDS, NO_VIABLE_KEYWORDS, logger)
    ga = GeospatialAnalyzer(FILTERS, logger)
    scorer = PropertyScorer(SCORING_WEIGHTS, logger)
    viz = Visualizer(logger)

    cat_df = cp.load_catastro_csv(catastro_csv)
    gdf = build_geometry_from_latlon(cat_df)

    if seduvi_csv and seduvi_csv.exists():
        seduvi_df = sp.load_csv(seduvi_csv)
        if "alcaldia" in seduvi_df.columns:
            seduvi_df["alcaldia"] = seduvi_df["alcaldia"].astype(str).str.upper()
        gdf = sp.enrich_with_seduvi(gdf, seduvi_df)
    else:
        gdf["uso_suelo_raw"] = pd.NA
        gdf["clasificacion_viabilidad"] = "revision manual"

    shortlist = ga.apply_filters(gdf)
    shortlist = gpd.GeoDataFrame(shortlist, geometry=getattr(shortlist, "geometry", None), crs=getattr(gdf, "crs", None)) if "geometry" in shortlist.columns else gpd.GeoDataFrame(shortlist)
    shortlist = ga.add_accessibility_stub(shortlist)
    shortlist = ga.add_risk_stub(shortlist)
    shortlist["commercial_confidence_score"] = 0.0
    shortlist = scorer.score(shortlist)

    shortlist.to_csv(OUTPUT["shortlist_csv"], index=False, encoding="utf-8-sig")
    try:
        if isinstance(shortlist, gpd.GeoDataFrame) and "geometry" in shortlist.columns and shortlist.geometry.notna().any():
            shortlist.to_file(OUTPUT["shortlist_geojson"], driver="GeoJSON")
        else:
            logger.info("No hay geometría disponible; se omite exportación GeoJSON")
    except Exception as exc:
        logger.warning("No fue posible exportar GeoJSON: %s", exc)

    if isinstance(shortlist, gpd.GeoDataFrame) and "geometry" in shortlist.columns and shortlist.geometry.notna().any():
        viz.build_map(shortlist[shortlist.geometry.notna()].copy(), OUTPUT["interactive_map"])

    logger.info("Pipeline finalizado. Shortlist: %s predios", len(shortlist))
    print(f"Shortlist guardado en: {OUTPUT['shortlist_csv']}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python src/main.py <catastro_csv> [seduvi_csv]")
        sys.exit(1)
    catastro_csv = Path(sys.argv[1])
    seduvi_csv = Path(sys.argv[2]) if len(sys.argv) > 2 else None
    demo_pipeline(catastro_csv, seduvi_csv)
