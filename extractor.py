"""Extraction adapters for LangExtract-ready workflows."""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Dict, List


@dataclass
class ExtractionResult:
    records: List[Dict[str, str]]
    logs: List[str]


class BaseExtractor:
    def extract(self, documents: List[Dict[str, str]], fields: List[str]) -> ExtractionResult:
        raise NotImplementedError


class LangExtractAdapter(BaseExtractor):
    """Adapter that uses langextract if available, else gracefully falls back."""

    def __init__(self) -> None:
        self._langextract = None
        try:
            import langextract as lx  # type: ignore

            self._langextract = lx
        except Exception:
            self._langextract = None

    def extract(self, documents: List[Dict[str, str]], fields: List[str]) -> ExtractionResult:
        logs: List[str] = []
        if self._langextract is None:
            logs.append(
                "langextract not available. Using fallback regex extractor. "
                "Install and configure langextract to switch to production extraction."
            )
            return RegexFallbackExtractor().extract(documents, fields)

        logs.append("langextract detected. Running extraction with LangExtract adapter.")
        records: List[Dict[str, str]] = []

        for doc in documents:
            row: Dict[str, str] = {"document": doc["name"]}
            text = doc["text"]
            for field in fields:
                # Placeholder integration point for project-specific schema prompts.
                entities = self._langextract.extract(text, target_schema={field: "entity"})
                value = ""
                if entities and field in entities:
                    value = "; ".join(str(v) for v in entities[field])
                row[field] = value
            records.append(row)

        return ExtractionResult(records=records, logs=logs)


class RegexFallbackExtractor(BaseExtractor):
    """Lightweight deterministic extractor for local development and demos."""

    ENTITY_PATTERN = re.compile(r"\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b")

    def extract(self, documents: List[Dict[str, str]], fields: List[str]) -> ExtractionResult:
        logs = ["Running fallback entity extraction rules."]
        records: List[Dict[str, str]] = []

        for doc in documents:
            row: Dict[str, str] = {"document": doc["name"]}
            entities = self.ENTITY_PATTERN.findall(doc["text"])
            uniq_entities = list(dict.fromkeys(entities))
            for i, field in enumerate(fields):
                match = ""
                if i < len(uniq_entities):
                    match = uniq_entities[i]
                row[field] = match
            records.append(row)

        logs.append(f"Generated {len(records)} extracted record(s).")
        return ExtractionResult(records=records, logs=logs)
