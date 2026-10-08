"""Closed nested extraction schema. Anchors refer to exact immutable source units."""

from __future__ import annotations
import hashlib
import json
from typing import Literal
from uuid import UUID
from datetime import date
from pydantic import BaseModel, ConfigDict, Field, model_validator


class ExtractionError(ValueError):
    pass


class Strict(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


def digest(value):
    return hashlib.sha256(canonical(value).encode()).hexdigest()


class Anchor(Strict):
    unit: str = Field(min_length=1, max_length=180)
    start: int = Field(ge=0)
    end: int = Field(gt=0)
    quote: str = Field(min_length=1, max_length=2000)


class Mention(Strict):
    id: str = Field(pattern="^m[0-9]{1,4}$")
    kind: str = Field(min_length=1, max_length=40)
    anchor: Anchor


class Citation(Strict):
    relation: Literal["supporting", "contradicting"]
    anchor: Anchor


class Claim(Strict):
    id: str = Field(pattern="^c[0-9]{1,4}$")
    kind: Literal["observation", "model_output", "assumption", "AI_inference"]
    statement: Anchor
    subject: Anchor
    predicate: Anchor
    value: Anchor | None = None
    unit: Anchor | None = None
    period: Anchor | None = None
    territory_mention: str | None = Field(default=None, pattern="^m[0-9]{1,4}$")
    citations: list[Citation] = Field(min_length=1, max_length=20)
    limitations: str = Field(min_length=1, max_length=1000)


class Output(Strict):
    mentions: list[Mention] = Field(max_length=100)
    claims: list[Claim] = Field(max_length=100)


def validate_output(value, units, kinds):
    try:
        if len(canonical(value).encode()) > 200000:
            raise ExtractionError("output_limit")
        output = Output.model_validate(value)
        mids = [m.id for m in output.mentions]
        cids = [c.id for c in output.claims]
        if len(set(mids)) != len(mids) or len(set(cids)) != len(cids):
            raise ExtractionError("duplicate_id")

        def check(a):
            if (
                a.unit not in units
                or a.end <= a.start
                or a.end > len(units[a.unit]["text"])
                or units[a.unit]["text"][a.start : a.end] != a.quote
            ):
                raise ExtractionError("anchor_mismatch")

        for m in output.mentions:
            if m.kind not in kinds:
                raise ExtractionError("entity_type_not_supported")
            check(m.anchor)
        for c in output.claims:
            check(c.statement)
            for field in ["subject", "predicate", "value", "unit", "period"]:
                a = getattr(c, field)
                if a:
                    check(a)
                    if field in {"value", "period"} and any(ch.isdigit() for ch in a.quote):
                        text = units[a.unit]["text"]
                        before, after = text[: a.start], text[a.end :]
                        joining = ".,:/+-−–—"
                        if (
                            (before and before[-1].isdigit())
                            or (after and after[0].isdigit())
                            or (before and before[-1] in "+-−" and a.quote[0].isdigit())
                            or (len(before) > 1 and before[-1] in joining and before[-2].isdigit())
                            or (len(after) > 1 and after[0] in joining and after[1].isdigit())
                        ):
                            raise ExtractionError("partial_numeric_token")
                    # Atomic field must occur in the stated finding, not elsewhere in a long document.
                    same_statement = (
                        a.unit == c.statement.unit and c.statement.start <= a.start < a.end <= c.statement.end
                    )
                    left, right = units[a.unit], units[c.statement.unit]
                    same_record = (
                        left.get("record_id") is not None
                        and left.get("record_id") == right.get("record_id")
                        and left["source"] == right["source"]
                    )
                    cited_cell = any(x.relation == "supporting" and x.anchor == a for x in c.citations)
                    if not same_statement and not (same_record and cited_cell):
                        raise ExtractionError("field_outside_statement")
            if c.territory_mention and c.territory_mention not in mids:
                raise ExtractionError("territory_mention_missing")
            if not any(x.relation == "supporting" for x in c.citations):
                raise ExtractionError("supporting_citation_required")
            for citation in c.citations:
                check(citation.anchor)
            if not any(x.relation == "supporting" and x.anchor == c.statement for x in c.citations):
                raise ExtractionError("statement_citation_required")
        return output.model_dump(mode="json")
    except (ValueError, TypeError, KeyError, OverflowError) as exc:
        if isinstance(exc, ExtractionError):
            raise
        raise ExtractionError("invalid_structured_extraction") from None


class Create(BaseModel):
    model_config = ConfigDict(extra="forbid")
    organization_id: UUID
    workspace_id: UUID
    input_kind: Literal["document", "snapshot"]
    input_id: UUID
    language: Literal["sr-Latn", "sr-Cyrl", "en"]
    model_key: str = Field(min_length=1, max_length=160)
    request_key: UUID


class Territory(BaseModel):
    model_config = ConfigDict(extra="forbid")
    claim_id: str = Field(pattern="^c[0-9]{1,4}$")
    geometry_id: UUID
    at_date: date
    scope_note: str = Field(min_length=1, max_length=1000, pattern=r"\S")


class EntityLink(BaseModel):
    model_config = ConfigDict(extra="forbid")
    mention_id: str = Field(pattern="^m[0-9]{1,4}$")
    domain_kind: str = Field(min_length=1, max_length=80)
    domain_id: UUID
    evidence_note: str = Field(min_length=1, max_length=1000, pattern=r"\S")


class Review(BaseModel):
    model_config = ConfigDict(extra="forbid")
    fingerprint: str = Field(pattern="^[0-9a-f]{64}$")
    decision: Literal["REVIEWED_ACCEPTED", "REJECTED"]
    attested: bool = Field(strict=True)
    note: str = Field(min_length=1, max_length=1000, pattern=r"\S")
    territories: list[Territory] = Field(default_factory=list, max_length=100)

    entity_links: list[EntityLink] = Field(default_factory=list, max_length=100)

    @model_validator(mode="after")
    def valid(self):
        if len({t.claim_id for t in self.territories}) != len(self.territories):
            raise ValueError("duplicate_claim_territory")
        if len({x.mention_id for x in self.entity_links}) != len(self.entity_links):
            raise ValueError("duplicate_entity_link")
        if self.decision == "REJECTED" and (self.territories or self.entity_links):
            raise ValueError("rejected_territories_forbidden")
        return self
