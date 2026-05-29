"""Tests for server.py — validation, template logic, and API routes."""

import json
import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), "src"))

from server import (
    app, _validate_sharepoint_url, _validate_file_extension,
    _build_confluence_page, TEMPLATES,
    LiveSharePointProvider, MockSharePointProvider, SharePointProvider,
)


@pytest.fixture()
def client():
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c


VALID_URL = (
    "https://twodegrees1.sharepoint.com/teams/"
    "Enterprise-AIHackathonn-2026/Project%20Documents/my-doc.docx"
)


class TestValidateSharePointUrl:
    def test_valid_url_accepted(self):
        assert _validate_sharepoint_url(VALID_URL) is True

    def test_valid_url_subpath(self):
        url = (
            "https://twodegrees1.sharepoint.com/teams/"
            "Enterprise-AIHackathonn-2026/Project%20Documents/subfolder/file.pdf"
        )
        assert _validate_sharepoint_url(url) is True

    def test_wrong_tenant_rejected(self):
        assert _validate_sharepoint_url(
            "https://contoso.sharepoint.com/teams/Enterprise-AIHackathonn-2026/Project%20Documents/x"
        ) is False

    def test_wrong_team_rejected(self):
        assert _validate_sharepoint_url(
            "https://twodegrees1.sharepoint.com/teams/Other-Team/Project%20Documents/x"
        ) is False

    def test_wrong_library_rejected(self):
        assert _validate_sharepoint_url(
            "https://twodegrees1.sharepoint.com/teams/Enterprise-AIHackathonn-2026/Shared%20Documents/x"
        ) is False

    def test_local_file_rejected(self):
        assert _validate_sharepoint_url("file:///etc/passwd") is False

    def test_arbitrary_url_rejected(self):
        assert _validate_sharepoint_url("https://evil.com/malware") is False

    def test_empty_string_rejected(self):
        assert _validate_sharepoint_url("") is False

    def test_partial_match_rejected(self):
        assert _validate_sharepoint_url(
            "https://phishing.com/?url=https://twodegrees1.sharepoint.com/teams/Enterprise-AIHackathonn-2026/Project%20Documents/x"
        ) is False


class TestBuildConfluencePage:
    def test_all_templates_render(self):
        for key in TEMPLATES:
            markup = _build_confluence_page(key, "doc.docx", VALID_URL)
            assert "<h1>" in markup
            assert "doc.docx" in markup
            assert VALID_URL in markup

    def test_architecture_sections(self):
        markup = _build_confluence_page("architecture", "arch.docx", VALID_URL)
        for section in TEMPLATES["architecture"]["sections"]:
            assert section in markup, f"Missing section: {section!r}"

    def test_poc_sections(self):
        markup = _build_confluence_page("poc", "poc.docx", VALID_URL)
        for section in TEMPLATES["poc"]["sections"]:
            assert section in markup, f"Missing section: {section!r}"

    def test_pov_sections(self):
        markup = _build_confluence_page("pov", "pov.docx", VALID_URL)
        for section in TEMPLATES["pov"]["sections"]:
            assert section in markup, f"Missing section: {section!r}"

    def test_data_dictionary_sections(self):
        markup = _build_confluence_page("data_dictionary", "dict.docx", VALID_URL)
        for section in TEMPLATES["data_dictionary"]["sections"]:
            assert section in markup, f"Missing section: {section!r}"

    def test_general_info_sections(self):
        markup = _build_confluence_page("general_info", "info.docx", VALID_URL)
        for section in TEMPLATES["general_info"]["sections"]:
            assert section in markup, f"Missing section: {section!r}"

    def test_info_macro_present(self):
        markup = _build_confluence_page("poc", "poc.docx", VALID_URL)
        assert "ac:structured-macro" in markup
        assert 'ac:name="info"' in markup


class TestTemplatesRoute:
    def test_returns_all_five(self, client):
        resp = client.get("/api/templates")
        assert resp.status_code == 200
        data = resp.get_json()
        assert set(data.keys()) == {"architecture", "poc", "pov", "data_dictionary", "general_info"}

    def test_labels_are_strings(self, client):
        data = client.get("/api/templates").get_json()
        for label in data.values():
            assert isinstance(label, str) and label


class TestGenerateRoute:
    def _post(self, client, payload):
        return client.post(
            "/api/generate",
            data=json.dumps(payload),
            content_type="application/json",
        )

    def test_valid_request_succeeds(self, client):
        resp = self._post(client, {"doc_url": VALID_URL, "template": "architecture"})
        assert resp.status_code == 200
        data = resp.get_json()
        assert "markup" in data
        assert "template" in data

    def test_wrong_source_rejected_403(self, client):
        resp = self._post(client, {"doc_url": "https://evil.com/doc.docx", "template": "poc"})
        assert resp.status_code == 403
        assert "approved" in resp.get_json()["error"].lower()

    def test_missing_url_returns_400(self, client):
        resp = self._post(client, {"template": "poc"})
        assert resp.status_code == 400

    def test_unknown_template_returns_400(self, client):
        resp = self._post(client, {"doc_url": VALID_URL, "template": "nonexistent"})
        assert resp.status_code == 400

    def test_empty_body_returns_400(self, client):
        resp = self._post(client, {})
        assert resp.status_code == 400

    def test_doc_name_inferred_from_url(self, client):
        resp = self._post(client, {"doc_url": VALID_URL, "template": "general_info"})
        assert "my-doc.docx" in resp.get_json()["markup"]

    def test_explicit_doc_name_used(self, client):
        resp = self._post(client, {"doc_url": VALID_URL, "doc_name": "My Custom Name.docx", "template": "pov"})
        assert resp.status_code == 200
        assert "My Custom Name.docx" in resp.get_json()["markup"]

    def test_local_file_url_rejected(self, client):
        resp = self._post(client, {"doc_url": "file:///etc/passwd", "template": "poc"})
        assert resp.status_code == 403

    def test_all_templates_via_api(self, client):
        for tpl in TEMPLATES:
            resp = self._post(client, {"doc_url": VALID_URL, "template": tpl})
            assert resp.status_code == 200, f"template {tpl!r} failed"


class TestSharePointDocsRoute:
    def test_missing_auth_returns_401(self, client):
        resp = client.get("/api/sharepoint/docs")
        assert resp.status_code == 401

    def test_non_bearer_returns_401(self, client):
        resp = client.get("/api/sharepoint/docs", headers={"Authorization": "Basic abc"})
        assert resp.status_code == 401


class TestValidateFileExtension:
    def test_docx_accepted(self):
        assert _validate_file_extension("report.docx") is True

    def test_pdf_accepted(self):
        assert _validate_file_extension("brief.pdf") is True

    def test_pptx_accepted(self):
        assert _validate_file_extension("deck.pptx") is True

    def test_xlsx_accepted(self):
        assert _validate_file_extension("data.xlsx") is True

    def test_exe_rejected(self):
        assert _validate_file_extension("malware.exe") is False

    def test_sh_rejected(self):
        assert _validate_file_extension("script.sh") is False

    def test_no_extension_rejected(self):
        assert _validate_file_extension("noextension") is False

    def test_case_insensitive(self):
        assert _validate_file_extension("REPORT.DOCX") is True


class TestUnsupportedFileTypeRoute:
    def _post(self, client, payload):
        return client.post(
            "/api/generate",
            data=json.dumps(payload),
            content_type="application/json",
        )

    def test_exe_returns_422(self, client):
        url = (
            "https://twodegrees1.sharepoint.com/teams/"
            "Enterprise-AIHackathonn-2026/Project%20Documents/bad.exe"
        )
        resp = self._post(client, {"doc_url": url, "doc_name": "bad.exe", "template": "poc"})
        assert resp.status_code == 422
        assert "unsupported file type" in resp.get_json()["error"].lower()

    def test_sh_returns_422(self, client):
        url = (
            "https://twodegrees1.sharepoint.com/teams/"
            "Enterprise-AIHackathonn-2026/Project%20Documents/run.sh"
        )
        resp = self._post(client, {"doc_url": url, "doc_name": "run.sh", "template": "general_info"})
        assert resp.status_code == 422

    def test_supported_ext_passes(self, client):
        url = (
            "https://twodegrees1.sharepoint.com/teams/"
            "Enterprise-AIHackathonn-2026/Project%20Documents/report.pdf"
        )
        resp = self._post(client, {"doc_url": url, "doc_name": "report.pdf", "template": "pov"})
        assert resp.status_code == 200


class TestSharePointProviderInterface:
    def test_mock_provider_is_sharepoint_provider(self):
        assert isinstance(MockSharePointProvider(), SharePointProvider)

    def test_live_provider_is_sharepoint_provider(self):
        assert isinstance(LiveSharePointProvider(), SharePointProvider)

    def test_mock_returns_approved_urls_only(self):
        docs = MockSharePointProvider().list_documents("Bearer fake")
        for doc in docs:
            assert _validate_sharepoint_url(doc["url"]), f"Mock URL not approved: {doc['url']}"

    def test_mock_returns_supported_extensions_only(self):
        docs = MockSharePointProvider().list_documents("Bearer fake")
        for doc in docs:
            assert _validate_file_extension(doc["name"]), f"Mock doc has unsupported ext: {doc['name']}"

    def test_mock_returns_non_empty_list(self):
        docs = MockSharePointProvider().list_documents("Bearer fake")
        assert len(docs) > 0

    def test_mock_flag_is_set(self):
        docs = MockSharePointProvider().list_documents("Bearer fake")
        assert all(d.get("_mock") is True for d in docs)

    def test_mock_docs_via_api(self, client, monkeypatch):
        import server as srv
        monkeypatch.setattr(srv, "_get_provider", lambda: MockSharePointProvider())
        resp = client.get("/api/sharepoint/docs", headers={"Authorization": "Bearer test"})
        assert resp.status_code == 200
        data = resp.get_json()
        assert len(data["docs"]) > 0
        assert data["docs"][0].get("_mock") is True
