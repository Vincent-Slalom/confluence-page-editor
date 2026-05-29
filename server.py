"""
Confluence Page Generator - minimal Flask backend.

Responsibilities:
- Serve static index.html
- Proxy the SharePoint document library (read-only, approved location only)
- Generate Confluence-ready page markup from a validated SharePoint document URL
"""

import re
import os
import json
import logging
from flask import Flask, request, jsonify, send_from_directory, abort

try:
    import requests as http_client
    _HAS_REQUESTS = True
except ImportError:
    _HAS_REQUESTS = False

app = Flask(__name__, static_folder="static")
logging.basicConfig(level=logging.INFO)

# ---------------------------------------------------------------------------
# Source restriction
# ---------------------------------------------------------------------------

ALLOWED_SHAREPOINT_PREFIX = (
    "https://twodegrees1.sharepoint.com/teams/"
    "Enterprise-AIHackathonn-2026/Project%20Documents/"
)

ALLOWED_SHAREPOINT_API = (
    "https://twodegrees1.sharepoint.com/teams/Enterprise-AIHackathonn-2026/"
    "_api/web/GetFolderByServerRelativeUrl('Project%20Documents')/Files"
)

_URL_PATTERN = re.compile(
    r"^https://twodegrees1\.sharepoint\.com/teams/"
    r"Enterprise-AIHackathonn-2026/Project%20Documents/",
    re.IGNORECASE,
)


def _validate_sharepoint_url(url: str) -> bool:
    """Return True only if url is within the approved SharePoint library."""
    return bool(_URL_PATTERN.match(url))


# ---------------------------------------------------------------------------
# Templates
# ---------------------------------------------------------------------------

TEMPLATES = {
    "architecture": {
        "label": "Architecture Page",
        "sections": [
            "Executive Summary",
            "System Context",
            "Architecture Overview",
            "Key Components",
            "Integrations",
            "Data Flows",
            "Security / Access Considerations",
            "Assumptions",
            "Risks",
            "Open Questions",
            "Source Document Reference",
        ],
    },
    "poc": {
        "label": "Proof of Concept Page",
        "sections": [
            "Objective",
            "Hypothesis",
            "Scope",
            "Success Criteria",
            "Approach",
            "Prototype / Experiment Summary",
            "Findings",
            "Recommendation",
            "Next Steps",
            "Risks",
            "Source Document Reference",
        ],
    },
    "pov": {
        "label": "Point of View Page",
        "sections": [
            "Executive Position",
            "Context",
            "Recommendation",
            "Rationale",
            "Options Considered",
            "Benefits",
            "Tradeoffs",
            "Risks",
            "Decision Required",
            "Source Document Reference",
        ],
    },
    "data_dictionary": {
        "label": "Data Dictionary",
        "sections": [
            "Dataset / Object Name",
            "Business Description",
            "Field Table",
            "Data Type",
            "Definition",
            "Source System",
            "Owner",
            "Sensitivity / Classification",
            "Notes",
            "Source Document Reference",
        ],
    },
    "general_info": {
        "label": "General Info",
        "sections": [
            "Summary",
            "Background",
            "Key Details",
            "Stakeholders",
            "Related Documents",
            "Decisions / Notes",
            "Open Questions",
            "Source Document Reference",
        ],
    },
}


def _build_confluence_page(template_key: str, doc_name: str, doc_url: str) -> str:
    """Return Confluence Storage Format (XHTML) for the given template."""
    tpl = TEMPLATES[template_key]
    label = tpl["label"]
    sections_html = ""
    for section in tpl["sections"]:
        sections_html += (
            f"<h2>{section}</h2>"
            f'<p><em>Source document: <a href="{doc_url}">{doc_name}</a></em></p>'
            "<p></p>"
        )
    return (
        f"<h1>{label}: {doc_name}</h1>"
        f'<ac:structured-macro ac:name="info">'
        f"<ac:parameter ac:name=\"title\">Source</ac:parameter>"
        f'<ac:rich-text-body><p>Generated from approved SharePoint document: '
        f'<a href="{doc_url}">{doc_name}</a></p></ac:rich-text-body>'
        f"</ac:structured-macro>"
        + sections_html
    )


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.route("/")
def index():
    return send_from_directory(".", "index.html")


@app.route("/api/templates")
def list_templates():
    return jsonify({k: v["label"] for k, v in TEMPLATES.items()})


@app.route("/api/generate", methods=["POST"])
def generate():
    body = request.get_json(silent=True) or {}
    doc_url = (body.get("doc_url") or "").strip()
    doc_name = (body.get("doc_name") or "").strip()
    template_key = (body.get("template") or "").strip()

    if not doc_url:
        return jsonify({"error": "doc_url is required"}), 400
    if not _validate_sharepoint_url(doc_url):
        return jsonify({"error": "Document source is not from the approved SharePoint location."}), 403
    if template_key not in TEMPLATES:
        return jsonify({"error": f"Unknown template '{template_key}'. Valid: {list(TEMPLATES)}"}), 400
    if not doc_name:
        doc_name = doc_url.split("/")[-1] or "Untitled"

    markup = _build_confluence_page(template_key, doc_name, doc_url)
    return jsonify({"markup": markup, "template": TEMPLATES[template_key]["label"]})


@app.route("/api/sharepoint/docs")
def sharepoint_docs():
    """
    Proxy a read of the approved SharePoint document library.
    Requires a Bearer token supplied by the client (the server never stores credentials).
    Returns a list of {name, url} objects.
    """
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return jsonify({"error": "Authorization header with Bearer token required"}), 401

    if not _HAS_REQUESTS:
        return jsonify({"error": "requests library not available on server"}), 500

    try:
        resp = http_client.get(
            ALLOWED_SHAREPOINT_API,
            headers={
                "Authorization": auth_header,
                "Accept": "application/json;odata=verbose",
            },
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()
        files = data.get("d", {}).get("results", [])
        docs = [
            {
                "name": f.get("Name", ""),
                "url": ALLOWED_SHAREPOINT_PREFIX + f.get("Name", ""),
            }
            for f in files
        ]
        return jsonify({"docs": docs})
    except Exception as exc:  # noqa: BLE001
        logging.exception("SharePoint proxy error")
        return jsonify({"error": str(exc)}), 502


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
