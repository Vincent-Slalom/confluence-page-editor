"""
Confluence Page Generator - minimal Flask backend.

Responsibilities:
- Serve static index.html
- Proxy the SharePoint document library via a provider interface (live or dev mock)
- Generate Confluence-ready page markup from a validated SharePoint document URL
"""

import re
import os
import logging
from abc import ABC, abstractmethod
from flask import Flask, request, jsonify, send_from_directory

try:
    import requests as http_client
    _HAS_REQUESTS = True
except ImportError:
    _HAS_REQUESTS = False

_HERE = os.path.dirname(os.path.abspath(__file__))

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

SUPPORTED_EXTENSIONS = {".docx", ".doc", ".pdf", ".pptx", ".xlsx", ".txt", ".md"}

_URL_PATTERN = re.compile(
    r"^https://twodegrees1\.sharepoint\.com/teams/"
    r"Enterprise-AIHackathonn-2026/Project%20Documents/",
    re.IGNORECASE,
)


def _validate_sharepoint_url(url: str) -> bool:
    """Return True only if url is within the approved SharePoint library."""
    return bool(_URL_PATTERN.match(url))


def _validate_file_extension(filename: str) -> bool:
    """Return True if the file extension is in the supported set."""
    _, ext = os.path.splitext(filename.lower())
    return ext in SUPPORTED_EXTENSIONS


# ---------------------------------------------------------------------------
# SharePoint provider interface
# ---------------------------------------------------------------------------

class SharePointProvider(ABC):
    """Abstract interface for listing documents from the approved library."""

    @abstractmethod
    def list_documents(self, auth_header: str) -> list[dict]:
        """Return a list of {name, url} dicts from the approved library."""


class LiveSharePointProvider(SharePointProvider):
    """Calls the real SharePoint REST API. Requires a valid Bearer token."""

    def list_documents(self, auth_header: str) -> list[dict]:
        if not _HAS_REQUESTS:
            raise RuntimeError("requests library is not installed")
        resp = http_client.get(
            ALLOWED_SHAREPOINT_API,
            headers={
                "Authorization": auth_header,
                "Accept": "application/json;odata=verbose",
            },
            timeout=10,
        )
        resp.raise_for_status()
        files = resp.json().get("d", {}).get("results", [])
        return [
            {
                "name": f.get("Name", ""),
                "url": ALLOWED_SHAREPOINT_PREFIX + f.get("Name", ""),
            }
            for f in files
            if _validate_file_extension(f.get("Name", ""))
        ]


class MockSharePointProvider(SharePointProvider):
    """
    DEV-ONLY mock provider. Never returns real document content.
    Active only when the environment variable USE_MOCK_SHAREPOINT=1 is set.
    """

    _MOCK_DOCS = [
        "Architecture-Overview.docx",
        "PoC-Results-Q1.docx",
        "AI-Platform-PoV.docx",
        "Data-Dictionary-v2.xlsx",
        "Project-General-Info.docx",
    ]

    def list_documents(self, auth_header: str) -> list[dict]:
        return [
            {
                "name": name,
                "url": ALLOWED_SHAREPOINT_PREFIX + name,
                "_mock": True,
            }
            for name in self._MOCK_DOCS
        ]


def _get_provider() -> SharePointProvider:
    if os.environ.get("USE_MOCK_SHAREPOINT") == "1":
        logging.warning("Using MockSharePointProvider — DEV ONLY, not real data")
        return MockSharePointProvider()
    return LiveSharePointProvider()


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
        f'<ac:parameter ac:name="title">Source</ac:parameter>'
        f"<ac:rich-text-body><p>Generated from approved SharePoint document: "
        f'<a href="{doc_url}">{doc_name}</a></p></ac:rich-text-body>'
        f"</ac:structured-macro>"
        + sections_html
    )


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.route("/")
def index():
    return send_from_directory(_HERE, "index.html")


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
    if not doc_name:
        doc_name = doc_url.split("/")[-1] or "Untitled"
    if not _validate_file_extension(doc_name):
        _, ext = os.path.splitext(doc_name)
        return jsonify({
            "error": f"Unsupported file type '{ext or '(none)'}'. "
                     f"Supported: {', '.join(sorted(SUPPORTED_EXTENSIONS))}"
        }), 422
    if template_key not in TEMPLATES:
        return jsonify({"error": f"Unknown template '{template_key}'. Valid: {list(TEMPLATES)}"}), 400

    markup = _build_confluence_page(template_key, doc_name, doc_url)
    return jsonify({"markup": markup, "template": TEMPLATES[template_key]["label"]})


@app.route("/api/sharepoint/docs")
def sharepoint_docs():
    """
    List documents from the approved SharePoint library via the provider interface.
    Requires a Bearer token supplied by the client (never stored server-side).
    """
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return jsonify({"error": "Authorization header with Bearer token required"}), 401

    provider = _get_provider()
    try:
        docs = provider.list_documents(auth_header)
        if not docs:
            return jsonify({"docs": [], "warning": "No supported documents found in the approved SharePoint library."})
        return jsonify({"docs": docs})
    except Exception as exc:  # noqa: BLE001
        logging.exception("SharePoint provider error")
        return jsonify({"error": str(exc)}), 502


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
