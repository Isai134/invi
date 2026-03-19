# Sistema INVI de Identificación de Predios con Potencial de Vivienda Social

Pipeline híbrido en Python para:

1. integrar catastro + geografía oficial del SIG CDMX,
2. filtrar predios grandes y subutilizados,
3. clasificar viabilidad normativa con SEDUVI,
4. asignar un score multicriterio,
5. exportar shortlist en CSV, GeoJSON y mapa HTML,
6. validar comercialización posterior mediante scraping modular.

## Arquitectura

- `src/config.py`: parámetros globales, pesos, filtros y salidas.
- `src/logging_utils.py`: logging robusto UTF-8 para Windows.
- `src/io_utils.py`: lectura flexible de CSV y normalización.
- `src/sig_downloader.py`: descargas reproducibles desde SIG CDMX.
- `src/catastro_processor.py`: carga y unión de catastro CSV/SHP por `fid`.
- `src/seduvi_processor.py`: cruce con uso de suelo y clasificación normativa.
- `src/geospatial_analysis.py`: métricas y filtros geoespaciales.
- `src/property_scorer.py`: score multicriterio justificable.
- `src/commercial_scraper.py`: scraping desacoplado de fuentes comerciales.
- `src/visualization.py`: mapa HTML interactivo con Folium.
- `src/main.py`: pipeline end-to-end.

## Modelo de scoring propuesto

Score final de oportunidad:

```text
Score = 0.20*Tamaño
      + 0.20*Subutilización
      + 0.20*Viabilidad normativa
      + 0.15*Accesibilidad
      + 0.10*Riesgo
      + 0.15*Validación comercial
```

### Definiciones

- **Tamaño**: min-max sobre `sup_terreno`.
- **Subutilización**: `1 - normalized(sup_construccion / sup_terreno)`.
- **Viabilidad normativa**:
  - viable = 1.0
  - revisión manual = 0.6
  - no viable = 0.0
- **Accesibilidad**: idealmente debe calcularse con distancia a Metro, Metrobús, CETRAM, escuelas, hospitales y equipamiento.
- **Riesgo**: debe integrar capas oficiales de inundación, grietas, conservación, fallas, etc.
- **Validación comercial**: fuerza del match con anuncios reales.

## Flujo recomendado

### Fase 1. Integración SIG

- Descargar catastro CSV + Shapefile por alcaldía.
- Descargar uso de suelo SEDUVI CSV + Shapefile.
- Unir por `fid`.
- Generar base maestra.

### Fase 2. Filtro técnico

Filtros iniciales sugeridos:

- superficie mínima = `800 m²`
- ratio construcción/terreno <= `0.45`
- alcaldías objetivo configurables
- tope máximo de valor por m² según alcaldía

Tope presupuestal precargado en `config.py`:

- Benito Juárez: 22,000/m²
- Coyoacán: 20,000/m²
- Cuauhtémoc: 20,000/m²
- Iztacalco: 18,000/m²
- Miguel Hidalgo: 18,000/m²
- Tlalpan: 17,000/m²

### Fase 3. Viabilidad normativa

Se clasifica cada predio como:

- `viable`
- `revision manual`
- `no viable`

con base en palabras clave del uso de suelo, dejando el sistema fácil de mantener.

### Fase 4. Validación comercial

La búsqueda comercial **parte del shortlist**, no de búsquedas genéricas.
Cada consulta usa dirección + colonia + alcaldía + palabras clave.

Campos mínimos guardados:

- URL del anuncio
- título
- precio
- superficie anunciada
- fuente
- teléfono/contacto
- fecha de extracción
- score de match
- confianza: alto / medio / bajo

## Cómo correrlo

### 1. Crear entorno

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Estructura de datos sugerida

```text
invi_pipeline/
  data/
    raw/
      catastro/
      seduvi/
  results/
  logs/
  src/
```

### 3. Ejecutar demo con CSV

```bash
python src/main.py /ruta/a/catastro.csv /ruta/a/seduvi.csv
```

Si todavía no tienes SEDUVI unificado por `fid`:

```bash
python src/main.py /ruta/a/catastro.csv
```

### 4. Salidas

- `results/predios_shortlist.csv`
- `results/predios_shortlist.geojson`
- `results/predios_shortlist_map.html`
- `logs/pipeline.log`

## Recomendaciones para mejorar el matching catastro ↔ anuncios

1. Normalizar calle, número, colonia y alcaldía con reglas consistentes.
2. Quitar abreviaturas y variantes comunes: `AV.`, `AVENIDA`, `NO.`, `NÚMERO`, etc.
3. Calcular similitud por componentes, no solo por string completo.
4. Dar más peso a coincidencias de colonia y alcaldía.
5. Cruzar superficie anunciada vs `sup_terreno` con tolerancia de ±20%.
6. Cuando exista geolocalización del anuncio, medir distancia real al predio.
7. Guardar HTML crudo o snapshot del anuncio para auditoría.
8. Versionar selectores CSS/XPath por portal para mantenimiento.
9. Agregar revisión manual para matches medios.
10. Mantener una tabla histórica de anuncios vistos para detectar persistencia en venta.

## Mejora prioritaria siguiente

Cambiar los *stubs* de accesibilidad y riesgo por capas reales del SIG/CDMX:

- estaciones Metro/Metrobús
- hospitales
- escuelas
- mercados
- equipamiento
- Atlas de Riesgo
- conservación patrimonial
- áreas naturales / restricción normativa

