# Claude Code Instructions

You are working on the Confluence Page Generator App.

## Non-negotiable requirements

- Do not add a local file upload feature.
- Do not allow arbitrary URL ingestion.
- Do not use mock external content as if it were real source material.
- The only allowed document source is the approved SharePoint folder:
  https://twodegrees1.sharepoint.com/teams/Enterprise-AIHackathonn-2026/Project%20Documents/Forms/AllItems.aspx
- If SharePoint integration cannot be completed locally, implement a clean adapter interface and a safe mock provider clearly marked for development only.

## Performance priority

The previous version had slow preview behavior and appeared to install packages unnecessarily. Keep the implementation lightweight.

Prefer:
- Native browser APIs where possible.
- Static template rendering.
- Minimal dependencies.
- Lazy loading only when needed.
- Fast preview rendering.

Avoid:
- Large UI frameworks unless already present.
- Runtime package installation.
- Heavy document parsing in the preview path.
- Re-rendering the entire app on every input change.

## Required templates

Implement these template modes:

1. Architecture Page
2. Proof of Concept Page
3. Point of View Page
4. Data Dictionary
5. General Info

Each template should produce structured Confluence-ready content with headings, summary sections, source references, assumptions, risks, and open questions where relevant.

## Acceptance criteria

- User can select one of the five templates.
- User can select a document only from the approved SharePoint source.
- User cannot upload local files.
- User cannot paste arbitrary URLs.
- Preview appears quickly after template/document selection.
- Generated output is structured and readable.
- The app has clear error states for missing access, empty folder, unsupported file type, and generation failure.
- Tests cover template selection, source restriction, preview rendering, and blocked external input.
