"""Production-ready extraction pipeline with LangExtract + Gemini support."""

from __future__ import annotations

from dataclasses import dataclass
import os
import re
from typing import Dict, Iterable, List


@dataclass
class ExtractionResult:
    records: List[Dict[str, str]]
    logs: List[str]
    engine: str


class ExtractionPipelineError(RuntimeError):
    """Raised when extraction cannot be completed safely."""


class BaseExtractor:
    def extract(
        self,
        documents: List[Dict[str, str]],
        fields: List[str],
        api_key_override: str | None = None,
    ) -> ExtractionResult:
        raise NotImplementedError


class LangExtractAdapter(BaseExtractor):
    """Gemini-backed LangExtract adapter with deterministic fallback behavior."""

    def __init__(self, model_id: str = "gemini-2.5-flash") -> None:
        self.model_id = model_id
        self._langextract = None
        try:
            import langextract as lx  # type: ignore

            self._langextract = lx
        except Exception:
            self._langextract = None

    def extract(
        self,
        documents: List[Dict[str, str]],
        fields: List[str],
        api_key_override: str | None = None,
    ) -> ExtractionResult:
        if not documents:
            raise ExtractionPipelineError("No documents were provided for extraction.")
        if not fields:
            raise ExtractionPipelineError("No extraction fields were provided.")

        if self._langextract is None:
            fallback = RegexFallbackExtractor()
            result = fallback.extract(documents, fields)
            result.logs.insert(
                0,
                "langextract package unavailable. Running deterministic fallback engine.",
            )
            return result

        api_key = (api_key_override or "").strip() or os.getenv("LANGEXTRACT_API_KEY") or os.getenv("GEMINI_API_KEY")
        if not api_key:
            fallback = RegexFallbackExtractor()
            result = fallback.extract(documents, fields)
            result.logs.insert(
                0,
                "Gemini key not found (set LANGEXTRACT_API_KEY or GEMINI_API_KEY). "
                "Running deterministic fallback engine.",
            )
            return result

        logs: List[str] = [
            f"LangExtract available. Using Gemini model '{self.model_id}'.",
            f"Processing {len(documents)} document(s) and {len(fields)} field(s).",
        ]
        records: List[Dict[str, str]] = []

        prompt_description = self._build_prompt(fields)

        for doc in documents:
            row: Dict[str, str] = {"document": doc["name"]}
            for field in fields:
                row[field] = ""

            text = doc.get("text", "")
            if not text.strip():
                logs.append(f"Skipped '{doc['name']}' because it is empty.")
                records.append(row)
                continue

            try:
                annotated = self._langextract.extract(
                    text,
                    prompt_description=prompt_description,
                    api_key=api_key,
                    model_id=self.model_id,
                    extraction_passes=1,
                    max_workers=4,
                    batch_length=4,
                    show_progress=False,
                )
                extracted_map = self._map_entities_to_fields(annotated, fields)
                for field in fields:
                    values = extracted_map.get(field, [])
                    row[field] = "; ".join(values)

                total = sum(len(v) for v in extracted_map.values())
                logs.append(f"Processed '{doc['name']}' successfully with {total} extracted mention(s).")
            except Exception as err:  # noqa: BLE001
                logs.append(
                    f"LangExtract failed on '{doc['name']}' ({err}). "
                    "Using deterministic fallback for this document."
                )
                fallback_row = RegexFallbackExtractor().extract([doc], fields).records[0]
                row.update({k: v for k, v in fallback_row.items() if k in fields})

            records.append(row)

        return ExtractionResult(records=records, logs=logs, engine="langextract-gemini")

    @staticmethod
    def _build_prompt(fields: List[str]) -> str:
        field_list = ", ".join(fields)
        return (
            "Extract named entities from the text for the requested business fields. "
            "Use exactly one extraction per mention. "
            "Set extraction_class exactly to one of these field names: "
            f"{field_list}. "
            "Do not invent fields. Do not include values outside the source text."
        )

    @staticmethod
    def _map_entities_to_fields(annotated_doc: object, fields: List[str]) -> Dict[str, List[str]]:
        field_lookup = {f.lower(): f for f in fields}
        output: Dict[str, List[str]] = {f: [] for f in fields}

        docs: Iterable[object]
        if isinstance(annotated_doc, list):
            docs = annotated_doc
        else:
            docs = [annotated_doc]

        for doc in docs:
            extractions = getattr(doc, "extractions", []) or []
            for ex in extractions:
                klass = str(getattr(ex, "extraction_class", "")).strip()
                text = str(getattr(ex, "extraction_text", "")).strip()
                if not klass or not text:
                    continue

                key = field_lookup.get(klass.lower())
                if not key:
                    continue

                if text not in output[key]:
                    output[key].append(text)

        return output


class RegexFallbackExtractor(BaseExtractor):
    """Deterministic extractor used when model access is not available."""

    ENTITY_PATTERN = re.compile(r"\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b")

    def extract(
        self,
        documents: List[Dict[str, str]],
        fields: List[str],
        api_key_override: str | None = None,
    ) -> ExtractionResult:
        logs = ["Running fallback extraction engine."]
        records: List[Dict[str, str]] = []

        for doc in documents:
            row: Dict[str, str] = {"document": doc["name"]}
            entities = self.ENTITY_PATTERN.findall(doc.get("text", ""))
            uniq_entities = list(dict.fromkeys(entities))
            for i, field in enumerate(fields):
                row[field] = uniq_entities[i] if i < len(uniq_entities) else ""
            records.append(row)

        logs.append(f"Fallback generated {len(records)} record(s).")
        return ExtractionResult(records=records, logs=logs, engine="fallback-regex")
