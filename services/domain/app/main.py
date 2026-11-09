from __future__ import annotations

import os
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query, status

from .models import (
    HealthResponse,
    Hypothesis,
    HypothesisCreate,
    HypothesisStatus,
    TransitionEvent,
    TransitionRequest,
    TransitionResponse,
)
from .store import HypothesisNotFound, InvalidTransition, Store

SERVICE_NAME = "fin-agent-domain"
SERVICE_VERSION = "0.1.0"


def default_db_path() -> str:
    return os.getenv(
        "FINA_DB_PATH",
        str(Path(__file__).resolve().parent.parent / "data" / "domain.db"),
    )


def create_app(db_path: str | None = None) -> FastAPI:
    store = Store(db_path or default_db_path())
    app = FastAPI(
        title="Fin Agent Domain",
        version=SERVICE_VERSION,
        description="Hypotheses, evidence and approval state for Fin Agent Workbench.",
    )

    @app.get("/health", response_model=HealthResponse)
    def health() -> HealthResponse:
        return HealthResponse(
            ok=True,
            service=SERVICE_NAME,
            version=SERVICE_VERSION,
        )

    @app.post(
        "/api/v1/hypotheses",
        response_model=Hypothesis,
        status_code=status.HTTP_201_CREATED,
    )
    def create_hypothesis(payload: HypothesisCreate) -> Hypothesis:
        return store.create(payload)

    @app.get("/api/v1/hypotheses", response_model=list[Hypothesis])
    def list_hypotheses(
        status_filter: HypothesisStatus | None = Query(
            default=None,
            alias="status",
        ),
    ) -> list[Hypothesis]:
        return store.list(status_filter)

    @app.get("/api/v1/hypotheses/{hypothesis_id}", response_model=Hypothesis)
    def get_hypothesis(hypothesis_id: str) -> Hypothesis:
        try:
            return store.get(hypothesis_id)
        except HypothesisNotFound as exc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="hypothesis not found",
            ) from exc

    @app.post(
        "/api/v1/hypotheses/{hypothesis_id}/transitions",
        response_model=TransitionResponse,
    )
    def transition_hypothesis(
        hypothesis_id: str,
        payload: TransitionRequest,
    ) -> TransitionResponse:
        try:
            hypothesis, event = store.transition(hypothesis_id, payload)
        except HypothesisNotFound as exc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="hypothesis not found",
            ) from exc
        except InvalidTransition as exc:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=str(exc),
            ) from exc
        return TransitionResponse(hypothesis=hypothesis, event=event)

    @app.get(
        "/api/v1/hypotheses/{hypothesis_id}/events",
        response_model=list[TransitionEvent],
    )
    def list_events(hypothesis_id: str) -> list[TransitionEvent]:
        try:
            store.get(hypothesis_id)
        except HypothesisNotFound as exc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="hypothesis not found",
            ) from exc
        return store.events(hypothesis_id)

    return app


app = create_app()
