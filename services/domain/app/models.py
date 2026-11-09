from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class HypothesisStatus(str, Enum):
    """Lifecycle of a research hypothesis."""

    draft = "draft"
    submitted = "submitted"
    under_review = "under_review"
    approved = "approved"
    rejected = "rejected"
    conditional = "conditional"
    frozen = "frozen"


ALLOWED_TRANSITIONS: dict[HypothesisStatus, set[HypothesisStatus]] = {
    HypothesisStatus.draft: {HypothesisStatus.submitted},
    HypothesisStatus.submitted: {HypothesisStatus.under_review},
    HypothesisStatus.under_review: {
        HypothesisStatus.approved,
        HypothesisStatus.rejected,
        HypothesisStatus.conditional,
    },
    HypothesisStatus.conditional: {
        HypothesisStatus.approved,
        HypothesisStatus.rejected,
    },
    HypothesisStatus.approved: {HypothesisStatus.frozen},
    HypothesisStatus.rejected: {HypothesisStatus.draft},
    HypothesisStatus.frozen: set(),
}


class EvidenceRef(BaseModel):
    """A pointer to a source paragraph, table or filing."""

    source_id: str = Field(min_length=1)
    locator: str | None = None
    quote: str | None = None
    as_of: datetime | None = None


class ValuationImpact(BaseModel):
    """Optional valuation delta attached to a hypothesis."""

    model_config = ConfigDict(populate_by_name=True)

    metric: str = Field(min_length=1)
    from_value: float | None = Field(default=None, alias="from")
    to_value: float | None = Field(default=None, alias="to")


class HypothesisCreate(BaseModel):
    thesis: str = Field(min_length=1, max_length=2000)
    confidence: float = Field(default=0.5, ge=0, le=1)
    evidence_for: list[EvidenceRef] = Field(default_factory=list)
    evidence_against: list[EvidenceRef] = Field(default_factory=list)
    falsifiers: list[str] = Field(default_factory=list)
    valuation_impact: ValuationImpact | None = None
    created_by: str = Field(default="agent:lead", min_length=1)


class Hypothesis(HypothesisCreate):
    id: str
    status: HypothesisStatus = HypothesisStatus.draft
    created_at: datetime
    updated_at: datetime
    artifact_version: int | None = None


class TransitionRequest(BaseModel):
    to_status: HypothesisStatus
    actor: str = Field(min_length=1)
    reason: str | None = None


class TransitionEvent(BaseModel):
    id: int
    hypothesis_id: str
    from_status: HypothesisStatus
    to_status: HypothesisStatus
    actor: str
    reason: str | None = None
    at: datetime


class TransitionResponse(BaseModel):
    hypothesis: Hypothesis
    event: TransitionEvent


class HealthResponse(BaseModel):
    ok: bool
    service: str
    version: str


EvidenceKind = Literal["for", "against"]
