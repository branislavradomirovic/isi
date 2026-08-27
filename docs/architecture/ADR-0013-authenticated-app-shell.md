# ADR-0013 — Authenticated App Shell

## Decision
The private ISI application uses Streamlit as the authenticated presentation shell over the existing FastAPI authentication and app-context APIs.

The browser-facing Streamlit process is never the authority for tenant, product or workspace access. Every shell selection is revalidated by FastAPI through the shared application-context service.

## Boundaries
- ISI identity/auth/session logic remains shared.
- Organization membership remains the tenant boundary.
- Product entitlement remains independent of roles.
- SIMPA and ORDO share the shell but keep separate future domain modules.
- Streamlit owns presentation/session convenience only; FastAPI owns authorization truth.

## Selection behavior
- one accessible organization + one accessible product -> direct product entry;
- multiple organizations -> organization selector;
- multiple accessible products -> product switcher;
- one workspace -> direct workspace entry;
- multiple workspaces -> workspace selector;
- no workspace -> product shell stays accessible but domain actions are unavailable.

## Navigation
Navigation is generated from server-returned permissions. A visual item in the shell is not a substitute for authorization on future API endpoints.

## Security
Cross-tenant and cross-product selections are rejected server-side. Session tokens are held only in Streamlit server session state and sent to the FastAPI backend as bearer tokens.

## Consequence
ISI-05 creates the durable authenticated shell without pulling SIMPA or ORDO domain logic forward from ISI-08/10.
