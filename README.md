# gem-extract

A polished Flask web app for document upload + field-driven named entity extraction.

## Features
- Upload one or more text-based documents.
- Add custom extraction fields.
- Run extraction with live status, progress bar, and logs.
- View extraction output in JSON and a tabular preview.
- Export extracted rows as CSV.
- Production pipeline uses **LangExtract + Gemini** when `LANGEXTRACT_API_KEY` or `GEMINI_API_KEY` is present.
- Safe deterministic fallback keeps the app working if model access fails.

## Run locally
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export GEMINI_API_KEY="your-key-here"
python app.py
```

Open http://localhost:5000.

## LangExtract pipeline details
`extractor.py` contains `LangExtractAdapter` with:
- robust input validation,
- Gemini model execution (`gemini-2.5-flash` by default),
- per-document error isolation,
- deterministic fallback per failing document,
- extraction-class-to-field mapping that de-duplicates entities.

This gives complete end-to-end behavior while remaining resilient when API/network/model errors occur.
