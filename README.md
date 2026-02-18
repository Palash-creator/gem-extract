# gem-extract

A polished Flask web app for document upload + field-driven named entity extraction.

## Features
- Upload one or more text-based documents.
- Add custom extraction fields.
- Run extraction with live status, progress bar, and logs.
- View extraction output in JSON and a tabular preview.
- Export extracted rows as CSV.
- Includes `LangExtractAdapter` infrastructure that auto-uses `langextract` when installed and falls back to deterministic regex rules for local demos.

## Run locally
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

Open http://localhost:5000.

## LangExtract infrastructure notes
`extractor.py` provides a dedicated adapter class (`LangExtractAdapter`) where you can wire your LangExtract schema prompts and provider configuration. If `langextract` is not installed/configured, the app still works via fallback mode so UX can be built and tested end-to-end.
