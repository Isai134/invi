from __future__ import annotations

import re
import time
from dataclasses import dataclass, asdict
from datetime import datetime
from difflib import SequenceMatcher
from typing import Iterable
import pandas as pd
import requests
from bs4 import BeautifulSoup


@dataclass
class CommercialMatch:
    fid: int
    source: str
    query: str
    url: str | None
    title: str | None
    price: str | None
    surface_advertised: str | None
    phone_or_contact: str | None
    extracted_at: str
    match_score: float
    match_confidence: str


class CommercialScraper:
    def __init__(self, config: dict, logger=None):
        self.config = config
        self.logger = logger
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": config["user_agent"]})

    @staticmethod
    def _clean(text: str) -> str:
        return re.sub(r"\s+", " ", str(text).strip().upper())

    def build_query(self, row: pd.Series) -> str:
        parts = [row.get("calle_numero", ""), row.get("colonia", ""), row.get("alcaldia", ""), "TERRENO", "PREDIO"]
        return " ".join([self._clean(p) for p in parts if str(p).strip()])

    def compute_match_score(self, property_row: pd.Series, listing_text: str) -> float:
        target = self.build_query(property_row)
        listing_text = self._clean(listing_text)
        score = SequenceMatcher(None, target, listing_text).ratio()
        if str(property_row.get("colonia", "")).upper() in listing_text:
            score += 0.10
        if str(property_row.get("alcaldia", "")).upper() in listing_text:
            score += 0.10
        if str(property_row.get("calle_numero", "")).upper()[:15] in listing_text:
            score += 0.15
        return min(score, 1.0)

    @staticmethod
    def confidence_label(score: float) -> str:
        if score >= 0.80:
            return "alto"
        if score >= 0.60:
            return "medio"
        return "bajo"

    def scrape_generic_html(self, url: str, property_row: pd.Series, source_name: str) -> list[CommercialMatch]:
        matches: list[CommercialMatch] = []
        response = self.session.get(url, timeout=30)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        candidates = soup.find_all(["article", "div", "li"])
        now = datetime.utcnow().isoformat()
        for node in candidates[:200]:
            text = self._clean(node.get_text(" ", strip=True))
            if not text:
                continue
            score = self.compute_match_score(property_row, text)
            if score < 0.45:
                continue
            title = node.find(["h1", "h2", "h3", "a"])
            href = None
            title_text = None
            if title:
                title_text = title.get_text(" ", strip=True)
                href = title.get("href")
            matches.append(
                CommercialMatch(
                    fid=int(property_row["fid"]),
                    source=source_name,
                    query=self.build_query(property_row),
                    url=href,
                    title=title_text,
                    price=None,
                    surface_advertised=None,
                    phone_or_contact=None,
                    extracted_at=now,
                    match_score=score,
                    match_confidence=self.confidence_label(score),
                )
            )
        return matches

    def run(self, candidate_properties: pd.DataFrame, source_urls: dict[str, str]) -> pd.DataFrame:
        all_matches: list[dict] = []
        for _, row in candidate_properties.iterrows():
            for source_name, url in source_urls.items():
                try:
                    hits = self.scrape_generic_html(url, row, source_name)
                    all_matches.extend(asdict(h) for h in hits)
                    time.sleep(self.config["sleep_between_requests"])
                except Exception as exc:
                    if self.logger:
                        self.logger.warning("Error scraping %s para fid=%s: %s", source_name, row.get("fid"), exc)
        return pd.DataFrame(all_matches)
