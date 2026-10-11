from __future__ import annotations

from typing import Any
from uuid import UUID

from pydantic import ValidationError
from src.platform.ai.schemas import AIScope, AIJobCreateRequest, AIEvaluationReviewCreateRequest

from src.streamlit_app.api_client import AccessDenied, ApiUnavailable, AuthenticationRequired, request


def _checked(response, *, unavailable: str) -> Any:
    if response.status_code == 401:
        raise AuthenticationRequired("Sesija je istekla.")
    if response.status_code == 403:
        raise AccessDenied("Nemate dozvolu za ovu AI operaciju.")
    if response.status_code >= 500:
        raise ApiUnavailable(unavailable)
    if response.status_code >= 400:
        try:
            code = response.json().get("detail")
        except (ValueError, AttributeError):
            code = None
        messages = {
            "evaluation_reviewed_evidence_changed": "Dokaz se promenio od pregleda. Osvežite i ponovo pregledajte pre potvrde.",
            "final_evaluation_review_immutable": "Vaš konačni pregled je već sačuvan i ne može se prepisati.",
            "final_evaluation_review_requires_terminal_run": "Konačni pregled zahteva završen ili neuspešan evaluacioni run.",
            "final_evaluation_review_evidence_reference_required": "Konačni pregled zahteva referencu dokaza.",
        }
        raise AccessDenied(
            messages.get(code, "AI zahtev je odbijen; proverite ovlašćenja i aktuelan dokaz.")
            if isinstance(code, str)
            else "AI zahtev je odbijen; proverite polja i ovlašćenja."
        )
    return response.json()


def _scope_params(*, organization_id: str, product_code: str, workspace_id: str) -> dict[str, str]:
    try:
        return AIScope.model_validate(
            dict(organization_id=organization_id, product_code=product_code, workspace_id=workspace_id)
        ).model_dump(mode="json")
    except ValidationError:
        raise AccessDenied("Izaberite važeću organizaciju, proizvod i radni prostor.") from None


def capabilities(token: str, *, organization_id: str, product_code: str, workspace_id: str):
    response = request(
        "GET",
        "/api/v1/ai/capabilities",
        token=token,
        params=_scope_params(organization_id=organization_id, product_code=product_code, workspace_id=workspace_id),
    )
    return _checked(response, unavailable="Nije moguće učitati AI capability stanje.")


def models(token: str, *, organization_id: str, product_code: str, workspace_id: str):
    response = request(
        "GET",
        "/api/v1/ai/models",
        token=token,
        params=_scope_params(organization_id=organization_id, product_code=product_code, workspace_id=workspace_id),
    )
    return _checked(response, unavailable="Nije moguće učitati AI model registry.")


def prompts(token: str, *, organization_id: str, product_code: str, workspace_id: str):
    response = request(
        "GET",
        "/api/v1/ai/prompts",
        token=token,
        params=_scope_params(organization_id=organization_id, product_code=product_code, workspace_id=workspace_id),
    )
    return _checked(response, unavailable="Nije moguće učitati AI prompt registry.")


def jobs(token: str, *, organization_id: str, product_code: str, workspace_id: str):
    response = request(
        "GET",
        "/api/v1/ai/jobs",
        token=token,
        params=_scope_params(organization_id=organization_id, product_code=product_code, workspace_id=workspace_id),
    )
    return _checked(response, unavailable="Nije moguće učitati AI job istoriju.")


def create_job(
    token: str,
    *,
    organization_id: str,
    product_code: str,
    workspace_id: str,
    input_text: str,
    sensitivity: str = "internal",
    model_key: str | None = None,
    prompt_key: str = "foundation.diagnostic",
):
    payload: dict[str, Any] = {
        "organization_id": organization_id,
        "product_code": product_code,
        "workspace_id": workspace_id,
        "input_text": input_text,
        "sensitivity": sensitivity,
        "prompt_key": prompt_key,
    }
    if model_key:
        payload["model_key"] = model_key
    try:
        payload = AIJobCreateRequest.model_validate(payload).model_dump(mode="json")
    except ValidationError:
        raise AccessDenied("Nevažeća AI polja; zahtev nije poslat.") from None
    response = request("POST", "/api/v1/ai/jobs", token=token, json=payload)
    return _checked(response, unavailable="AI job nije moguće izvršiti.")


def _record_id(value: str) -> str:
    try:
        return str(UUID(value))
    except (ValueError, TypeError, AttributeError):
        raise AccessDenied("Izaberite važeći zapis.") from None


def evidence_get(token: str, *, scope: dict, kind: str, record_id: str | None = None):
    paths = {"registrations": "/governance/registrations", "runs": "/evaluation/runs"}
    if kind in {"run", "results", "reviews", "evaluation_xai", "job_xai"}:
        identity = _record_id(record_id)
        paths.update(
            run=f"/evaluation/runs/{identity}",
            results=f"/evaluation/runs/{identity}/results",
            reviews=f"/evaluation/runs/{identity}/reviews",
            evaluation_xai=f"/xai/evaluations/{identity}",
            job_xai=f"/xai/jobs/{identity}",
        )
    if kind not in paths:
        raise AccessDenied("Nepodržan pregled.")
    return _checked(
        request("GET", "/api/v1/ai" + paths[kind], token=token, params=_scope_params(**scope)),
        unavailable="AI dokaz nije dostupan; osvežite pregled.",
    )


def review_evaluation(token: str, *, scope: dict, run: dict, decision: str, notes: str, evidence_reference: str):
    try:
        payload = AIEvaluationReviewCreateRequest.model_validate(
            dict(
                **_scope_params(**scope),
                reviewed_status=run["status"],
                reviewed_result_fingerprint=run.get("result_fingerprint"),
                decision=decision,
                notes=notes,
                evidence_reference=evidence_reference,
            )
        ).model_dump(mode="json")
    except ValidationError:
        raise AccessDenied("Nevažeća polja pregleda; zahtev nije poslat.") from None
    if decision != "pending" and not evidence_reference.strip():
        raise AccessDenied("Konačni pregled zahteva referencu dokaza; zahtev nije poslat.")
    return _checked(
        request("POST", f"/api/v1/ai/evaluation/runs/{_record_id(run['id'])}/reviews", token=token, json=payload),
        unavailable="Pregled nije potvrđen. Proverite evidenciju pre ponavljanja.",
    )


def job(token: str, *, scope: dict, job_id: str):
    return _checked(
        request("GET", f"/api/v1/ai/jobs/{_record_id(job_id)}", token=token, params=_scope_params(**scope)),
        unavailable="AI rezultat nije dostupan; osvežite pregled.",
    )
