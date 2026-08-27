# ISI-05 Browser QA Matrix

Do not record QA PASS until every applicable item below is checked.

## Services
- [ ] FastAPI is running against native local PostgreSQL.
- [ ] Streamlit is running with `API_BASE_URL` pointing to that FastAPI instance.
- [ ] Public website still opens independently.
- [ ] `/api/v1/health` is healthy.

## Login
- [ ] Official ISI transparent logo is visible.
- [ ] Login form is visually aligned with the ISI public design system.
- [ ] Invalid credentials show a controlled error.
- [ ] Valid credentials enter the private application.
- [ ] Password is not echoed or retained visibly.

## SIMPA-only profile
- [ ] User enters SIMPA directly.
- [ ] ORDO is not offered.
- [ ] Organization selector is not shown when there is only one organization.
- [ ] Product selector is not shown when there is only one product.
- [ ] Workspace is selected directly when there is exactly one accessible workspace.

## ORDO-only profile
- [ ] User enters ORDO directly.
- [ ] SIMPA is not offered.

## Dual-product profile
- [ ] SIMPA and ORDO are both visible.
- [ ] Product switcher changes the active product.
- [ ] SIMPA and ORDO marks are visible and distinct.
- [ ] Switching product updates workspace and navigation context without leaking the other product state.

## Authorization / isolation
- [ ] Navigation reflects the user's permission set.
- [ ] A client cannot enter an inaccessible organization.
- [ ] A client cannot enter an inaccessible product.
- [ ] A client cannot enter another tenant's workspace.
- [ ] Expired/invalid session returns to login.
- [ ] No-access account receives a clear access message rather than a broken screen.

## Shell
- [ ] User name and email are shown correctly.
- [ ] Organization and product context are clear.
- [ ] Workspace context is clear.
- [ ] Role and permission summary is understandable.
- [ ] No fake domain statistics are displayed.
- [ ] Future sections are clearly marked as foundations/placeholders rather than implemented features.
- [ ] Logout revokes the backend session and clears local state.

## Responsive / visual
- [ ] Desktop layout is clean at 1440x900.
- [ ] Laptop layout is clean around 1280x800.
- [ ] Sidebar remains usable on a narrow window.
- [ ] No text overlaps product marks.
- [ ] SIMPA and ORDO branding remains subordinate to ISI parent branding.
