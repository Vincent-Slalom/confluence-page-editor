# Acceptance Criteria

## Source restriction

- [ ] App only accepts document URLs that begin with the approved SharePoint prefix.
- [ ] Any URL that does not match the approved prefix is rejected with a clear error before generation.
- [ ] Rejection occurs on both client (before the request is sent) and server (HTTP 403).
- [ ] Local file upload is not present in the UI.
- [ ] Pasting arbitrary URLs from other domains is rejected.
- [ ] `file://`, `http://`, and other non-approved schemes are rejected.

## Templates

- [ ] All five templates are selectable: Architecture, PoC, PoV, Data Dictionary, General Info.
- [ ] Each generated page contains all required sections as defined in `docs/templates.md`.
- [ ] The page title includes the template name and the document name.
- [ ] An info banner identifies the source document and its URL.

## Preview

- [ ] Preview renders immediately after generation with no perceptible delay.
- [ ] Preview does not require a network call or package installation.
- [ ] Rendered preview and raw Confluence markup are both accessible via tabs.

## Copy / export

- [ ] "Copy Confluence markup" button copies the raw markup to the clipboard.
- [ ] Button provides visual confirmation after copy.

## SharePoint document list

- [ ] "Load documents" fetches only from the approved SharePoint library.
- [ ] A Bearer token is required; the app does not store credentials.
- [ ] Selecting a document from the list populates the URL and name fields.
- [ ] If SharePoint is unavailable, the app shows a clear error and remains usable (manual URL entry still works).

## Performance

- [ ] No npm packages or build step required to run.
- [ ] No packages are installed at preview time.
- [ ] Dependencies are limited to `flask` and `requests`.

## Security

- [ ] Server enforces source restriction independently of the client.
- [ ] SharePoint proxy forwards the user's Bearer token; the server never stores it.
- [ ] No user-supplied content is executed or rendered as server-side code.
