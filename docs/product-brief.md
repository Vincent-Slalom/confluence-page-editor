# Product Brief — Confluence Page Generator

## Problem

Project teams produce documents in SharePoint but need to publish structured pages in Confluence. Manually reformatting documents into Confluence's section-based format is slow and inconsistent.

## Solution

A lightweight web app that takes an approved SharePoint document URL and a chosen template, and generates Confluence Storage Format markup ready to paste into Confluence.

## Users

Slalom project team members participating in the Enterprise AI Hackathon 2026.

## Approved document source

```
https://twodegrees1.sharepoint.com/teams/Enterprise-AIHackathonn-2026/Project%20Documents/
```

## Templates supported

1. Architecture Page
2. Proof of Concept Page
3. Point of View Page
4. Data Dictionary
5. General Info

## Core flow

1. User opens the app.
2. User selects a page template.
3. App lists available documents from the approved SharePoint folder.
4. User selects one document.
5. App generates a Confluence-ready page draft.
6. User previews the generated page.
7. User copies the markup for Confluence.

## Non-goals

- No file upload
- No local file browsing
- No pasted document content
- No external data sources beyond the approved SharePoint library
- No Confluence API integration (copy-paste workflow only)
