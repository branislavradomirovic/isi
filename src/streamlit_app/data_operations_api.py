"""Fixed existing ingestion recovery endpoints and explicit observed time."""

from datetime import datetime, timezone
from urllib.parse import quote

from src.platform.data.schemas import (
    IngestionBackfillCreate,
    IngestionReplayCreate,
    IngestionDeadLetterRequeueRequest,
    IngestionDeadLetterResolveRequest,
)
from src.streamlit_app.api_client import request
from src.streamlit_app.data_api import _checked


def observed_time(value: str):
    if not value.strip():
        return None
    try:
        parsed = datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
        if parsed.tzinfo is None or parsed.utcoffset() is None:
            raise ValueError
    except ValueError:
        raise ValueError("Vreme opažanja mora biti ISO datum/vreme sa UTC pomakom; prazno znači nepoznato.") from None
    return parsed.astimezone(timezone.utc).isoformat()


def _path(source_id):
    return "/api/v1/data/sources/" + quote(str(source_id), safe="")


def list_dead_letters(token, *, source_id, scope):
    return _checked(
        request("GET", _path(source_id) + "/ingestion-dead-letters", token=token, params=scope),
        unavailable="Nije moguće učitati dead-letter pregled.",
    )


def recover(token, *, source_id, operation, scope, fields, artifact_id=None):
    suffix, schema = {
        "backfill": ("/ingestion-runs/backfill", IngestionBackfillCreate),
        "replay": ("/ingestion-runs/{id}/replay", IngestionReplayCreate),
        "requeue": ("/ingestion-dead-letters/{id}/requeue", IngestionDeadLetterRequeueRequest),
        "resolve": ("/ingestion-dead-letters/{id}/resolve", IngestionDeadLetterResolveRequest),
    }[operation]
    if "{id}" in suffix and artifact_id is None:
        raise ValueError("Izaberite obradu ili dead-letter stavku.")
    payload = schema.model_validate({**fields, **scope}).model_dump(mode="json")
    return _checked(
        request(
            "POST", _path(source_id) + suffix.format(id=quote(str(artifact_id), safe="")), token=token, json=payload
        ),
        unavailable="Zahtev je možda registrovan. Osvežite pregled pre ponavljanja.",
    )
