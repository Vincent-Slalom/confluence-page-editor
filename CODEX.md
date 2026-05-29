# CODEX — Developer Reference

## Architecture

| Layer | File | Responsibility |
|-------|------|----------------|
| Backend | `src/server.py` | Flask app — source validation, template rendering, SharePoint proxy |
| Frontend | `src/index.html` | Single-page UI — form, instant DOM preview, copy markup |
| Tests | `tests/test_server.py` | 29 pytest tests |

## Source restriction

All document URLs are validated against a strict regex on **both** client and server before any processing occurs:

```
^https://twodegrees1\.sharepoint\.com/teams/Enterprise-AIHackathonn-2026/Project%20Documents/
```

`/api/generate` returns HTTP 403 for any URL that does not match. The client also blocks submission before the request is sent.

## API routes

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/` | Serve `src/index.html` |
| `GET` | `/api/templates` | Return `{key: label}` for all 5 templates |
| `POST` | `/api/generate` | Validate URL + generate Confluence markup |
| `GET` | `/api/sharepoint/docs` | Proxy SharePoint file list (Bearer token required) |

### `/api/generate` request body

```json
{
  "doc_url":  "https://twodegrees1.sharepoint.com/teams/Enterprise-AIHackathonn-2026/Project%20Documents/my-file.docx",
  "doc_name": "My File",
  "template": "architecture"
}
```

### `/api/generate` response

```json
{
  "markup":   "<h1>Architecture Page: My File</h1>...",
  "template": "Architecture Page"
}
```

## Templates

Defined in `src/server.py` as `TEMPLATES`. Sections are the authoritative list from `docs/templates.md`. Adding a template requires:
1. Add an entry to `TEMPLATES` in `server.py`
2. Add the corresponding `<option>` in `index.html`
3. Add a section-coverage test in `tests/test_server.py`

## Performance notes

- Preview renders via pure DOM (`innerHTML`) — no parsing library, sub-millisecond.
- Generation is a single in-process string concatenation — no file I/O, no external calls.
- SharePoint proxy is the only network call; it is gated behind an explicit user action (button click + Bearer token).

## Dependencies

| Package | Use |
|---------|-----|
| `flask` | HTTP server |
| `requests` | SharePoint proxy |

No npm, no build step, no transpilation.

## Running locally

```bash
pip install -r requirements.txt
python src/server.py          # default port 5000
PORT=8080 python src/server.py
```

## Running tests

```bash
python -m pytest tests/ -v
```
