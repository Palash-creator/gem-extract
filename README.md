# gem-extract

A polished Flask web app for document upload + field-driven named entity extraction.

## Features
- Upload one or more text-based documents.
- Add custom extraction fields.
- Optional in-app Gemini API key input (paste key per run).
- Run extraction with live status, progress bar, and logs.
- View extraction output in JSON and a tabular preview.
- Export extracted rows as CSV.
- Production pipeline uses **LangExtract + Gemini** when a key is supplied.
- Safe deterministic fallback keeps the app working if model access fails.

## Windows (PowerShell) quick start
```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
# Optional: set a default key for this shell session
$env:GEMINI_API_KEY="your-key-here"
py app.py
```

## Windows (Command Prompt / cmd) quick start
```cmd
py -m venv .venv
.venv\Scripts\activate.bat
pip install -r requirements.txt
REM Optional: set a default key for this shell session
set GEMINI_API_KEY=your-key-here
py app.py
```

Open http://localhost:5000.

## API key usage (simplified)
You can now use either option:
1. **Easiest:** paste your Gemini API key directly in the app UI before clicking **Run Extraction**.
2. **Default key:** set `GEMINI_API_KEY` or `LANGEXTRACT_API_KEY` in your environment.

If no key is available, the app runs deterministic fallback extraction instead of failing.

## LangExtract pipeline details
`extractor.py` contains `LangExtractAdapter` with:
- robust input validation,
- Gemini model execution (`gemini-2.5-flash` by default),
- per-document error isolation,
- deterministic fallback per failing document,
- extraction-class-to-field mapping that de-duplicates entities.
