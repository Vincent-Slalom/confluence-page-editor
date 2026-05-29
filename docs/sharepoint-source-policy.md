# SharePoint Source Policy

## Approved location

The only valid document source for this app is:

```
https://twodegrees1.sharepoint.com/teams/Enterprise-AIHackathonn-2026/Project%20Documents/
```

## Enforcement

Source restriction is enforced at two layers:

### Client (UI)

The URL field validates on every keystroke using this regex:

```js
/^https:\/\/twodegrees1\.sharepoint\.com\/teams\/Enterprise-AIHackathonn-2026\/Project%20Documents\//i
```

- An inline error is shown immediately if the URL does not match.
- The Generate button cannot submit a request with a non-matching URL.

### Server (`/api/generate`)

The same pattern is applied in Python before any template rendering:

```python
_URL_PATTERN = re.compile(
    r"^https://twodegrees1\.sharepoint\.com/teams/"
    r"Enterprise-AIHackathonn-2026/Project%20Documents/",
    re.IGNORECASE,
)
```

- A non-matching URL returns HTTP **403** with a JSON error body.
- This applies regardless of what the client sends.

## What is rejected

| Input | Outcome |
|-------|--------|
| URL from a different SharePoint tenant | 403 / client error |
| URL from a different team site | 403 / client error |
| URL from a different document library | 403 / client error |
| `file://` URL | 403 / client error |
| Arbitrary HTTPS URL | 403 / client error |
| URL that contains the approved prefix but does not start with it | 403 / client error |
| Empty URL | 400 |

## SharePoint proxy (`/api/sharepoint/docs`)

- The proxy only ever calls the approved SharePoint REST API endpoint.
- The endpoint is hardcoded in `src/server.py`; it cannot be overridden by the client.
- A caller-supplied Bearer token is forwarded to SharePoint. The server does not log or persist it.
- The proxy returns only file names and their approved-prefix URLs.
