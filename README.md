# Confluence Page Generator App

## Purpose

Build a web app that generates Confluence-ready pages from approved project documents.

The app supports five page templates:

1. Architecture Page
2. Proof of Concept Page
3. Point of View Page
4. Data Dictionary
5. General Info

## Source restriction

The app must only use documents from this SharePoint folder:

https://twodegrees1.sharepoint.com/teams/Enterprise-AIHackathonn-2026/Project%20Documents/Forms/AllItems.aspx

Users must not be able to upload arbitrary files, select local files, paste external URLs, or load documents from any other source.

## Core flow

1. User opens the app.
2. User selects a page template.
3. App lists available documents from the approved SharePoint folder.
4. User selects one document.
5. App generates a Confluence-ready page draft.
6. User previews the generated page.
7. User copies or exports the page content for Confluence.

## Key constraints

- Optimize preview performance.
- Avoid unnecessary packages.
- Avoid heavy runtime dependencies.
- Do not install packages during preview.
- Do not use external data sources.
- Generated pages must clearly reflect the selected template.
- The app should fail closed if SharePoint access is unavailable.
