from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import requests


@dataclass
class DownloadSpec:
    name: str
    url: str
    output_path: Path


class SIGDownloader:
    def __init__(self, logger, timeout: int = 60):
        self.logger = logger
        self.timeout = timeout

    def download(self, spec: DownloadSpec) -> Path:
        self.logger.info("Descargando %s desde %s", spec.name, spec.url)
        spec.output_path.parent.mkdir(parents=True, exist_ok=True)
        with requests.get(spec.url, timeout=self.timeout, stream=True) as response:
            response.raise_for_status()
            with open(spec.output_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
        self.logger.info("Descarga completada: %s", spec.output_path)
        return spec.output_path
