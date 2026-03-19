from __future__ import annotations

import folium
import geopandas as gpd


class Visualizer:
    def __init__(self, logger=None):
        self.logger = logger

    def build_map(self, gdf: gpd.GeoDataFrame, output_html):
        if gdf.empty:
            raise ValueError("No hay predios para mapear")
        centroid = gdf.to_crs(4326).geometry.centroid
        start = [centroid.y.mean(), centroid.x.mean()]
        fmap = folium.Map(location=start, zoom_start=12, tiles="CartoDB positron")
        for _, row in gdf.to_crs(4326).iterrows():
            popup = folium.Popup(
                html=(
                    f"<b>FID:</b> {row.get('fid')}<br>"
                    f"<b>Dirección:</b> {row.get('calle_numero', 'N/D')}<br>"
                    f"<b>Colonia:</b> {row.get('colonia', 'N/D')}<br>"
                    f"<b>Alcaldía:</b> {row.get('alcaldia', 'N/D')}<br>"
                    f"<b>Superficie:</b> {row.get('sup_terreno', 'N/D')} m²<br>"
                    f"<b>Score:</b> {round(row.get('opportunity_score', 0), 3)}<br>"
                    f"<b>Viabilidad:</b> {row.get('clasificacion_viabilidad', 'N/D')}"
                ),
                max_width=320,
            )
            geom = row.geometry
            if geom.geom_type in {"Polygon", "MultiPolygon"}:
                folium.GeoJson(geom.__geo_interface__, popup=popup).add_to(fmap)
            else:
                folium.CircleMarker(
                    location=[geom.y, geom.x], radius=4, popup=popup, fill=True
                ).add_to(fmap)
        fmap.save(str(output_html))
        if self.logger:
            self.logger.info("Mapa guardado en %s", output_html)
