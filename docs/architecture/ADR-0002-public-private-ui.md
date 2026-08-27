# ADR-0002 — Public / Private UI Separation

Status: Accepted

The public institutional website is implemented with FastAPI + Jinja2 + HTML/CSS/SVG/minimal JS. The authenticated application uses Streamlit over the shared FastAPI backend.

Rationale: the public institutional site requires full control over semantics, SEO, accessibility, responsive design, and visual composition; Streamlit remains appropriate for the authenticated analytical workspace.
