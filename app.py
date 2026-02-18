from __future__ import annotations

import io
import json
from typing import Dict, List

import pandas as pd
from flask import Flask, jsonify, render_template, request, send_file

from extractor import ExtractionPipelineError, LangExtractAdapter

app = Flask(__name__)
extractor = LangExtractAdapter()


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/extract", methods=["POST"])
def extract():
    raw_fields = request.form.get("fields", "[]")
    try:
        parsed_fields = json.loads(raw_fields)
    except json.JSONDecodeError:
        return jsonify({"error": "Invalid fields format. Send a JSON array."}), 400

    fields: List[str] = []
    for field in parsed_fields if isinstance(parsed_fields, list) else []:
        cleaned = str(field).strip()
        if cleaned and cleaned not in fields:
            fields.append(cleaned)

    uploaded_files = request.files.getlist("documents")
    documents: List[Dict[str, str]] = []

    for file in uploaded_files:
        text = file.read().decode("utf-8", errors="ignore")
        documents.append({"name": file.filename or "unnamed.txt", "text": text})

    if not fields:
        return jsonify({"error": "Please provide at least one valid field."}), 400
    if not documents:
        return jsonify({"error": "Please upload at least one document."}), 400

    try:
        result = extractor.extract(documents=documents, fields=fields)
    except ExtractionPipelineError as err:
        return jsonify({"error": str(err)}), 400
    except Exception as err:  # noqa: BLE001
        return jsonify({"error": f"Unexpected extraction failure: {err}"}), 500

    return jsonify(
        {
            "fields": ["document", *fields],
            "records": result.records,
            "logs": result.logs,
            "engine": result.engine,
            "status": "completed",
        }
    )


@app.route("/api/export/csv", methods=["POST"])
def export_csv():
    payload = request.get_json(silent=True)
    if not payload:
        return jsonify({"error": "Missing JSON body."}), 400

    records = payload.get("records", [])
    if not records:
        return jsonify({"error": "No records to export."}), 400

    df = pd.DataFrame(records)
    csv_data = df.to_csv(index=False)

    return send_file(
        io.BytesIO(csv_data.encode("utf-8")),
        mimetype="text/csv",
        as_attachment=True,
        download_name="extracted_entities.csv",
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
