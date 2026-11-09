from __future__ import annotations

import sqlite3
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator

from .models import (
    ALLOWED_TRANSITIONS,
    Hypothesis,
    HypothesisCreate,
    HypothesisStatus,
    TransitionEvent,
    TransitionRequest,
)


class HypothesisNotFound(Exception):
    """Raised when a hypothesis id does not exist."""


class InvalidTransition(Exception):
    """Raised when a state transition is not allowed."""


SCHEMA = """
CREATE TABLE IF NOT EXISTS hypotheses (
    id TEXT PRIMARY KEY,
    status TEXT NOT NULL,
    payload TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_hypotheses_status ON hypotheses(status);

CREATE TABLE IF NOT EXISTS hypothesis_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    hypothesis_id TEXT NOT NULL,
    from_status TEXT NOT NULL,
    to_status TEXT NOT NULL,
    actor TEXT NOT NULL,
    reason TEXT,
    at TEXT NOT NULL,
    FOREIGN KEY (hypothesis_id) REFERENCES hypotheses(id)
);

CREATE INDEX IF NOT EXISTS idx_hypothesis_events_hid
    ON hypothesis_events(hypothesis_id);
"""


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Store:
    """SQLite-backed hypothesis store.

    The payload is the canonical JSON document; the status column exists for
    filtering and is kept in sync inside the same transaction.
    """

    def __init__(self, db_path: str | Path) -> None:
        self.db_path = str(db_path)
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as conn:
            conn.execute("PRAGMA journal_mode = WAL")
            conn.executescript(SCHEMA)

    @contextmanager
    def _connect(self) -> Iterator[sqlite3.Connection]:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def create(self, payload: HypothesisCreate) -> Hypothesis:
        now = utcnow()
        hypothesis = Hypothesis(
            id=f"h_{uuid.uuid4().hex[:12]}",
            status=HypothesisStatus.draft,
            created_at=now,
            updated_at=now,
            **payload.model_dump(),
        )
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO hypotheses
                    (id, status, payload, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    hypothesis.id,
                    hypothesis.status.value,
                    hypothesis.model_dump_json(by_alias=True),
                    hypothesis.created_at.isoformat(),
                    hypothesis.updated_at.isoformat(),
                ),
            )
        return hypothesis

    def list(self, status: HypothesisStatus | None = None) -> list[Hypothesis]:
        query = "SELECT payload FROM hypotheses"
        params: tuple[str, ...] = ()
        if status is not None:
            query += " WHERE status = ?"
            params = (status.value,)
        query += " ORDER BY created_at DESC"

        with self._connect() as conn:
            rows = conn.execute(query, params).fetchall()
        return [Hypothesis.model_validate_json(row["payload"]) for row in rows]

    def get(self, hypothesis_id: str) -> Hypothesis:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT payload FROM hypotheses WHERE id = ?",
                (hypothesis_id,),
            ).fetchone()
        if row is None:
            raise HypothesisNotFound(hypothesis_id)
        return Hypothesis.model_validate_json(row["payload"])

    def transition(
        self,
        hypothesis_id: str,
        request: TransitionRequest,
    ) -> tuple[Hypothesis, TransitionEvent]:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT payload FROM hypotheses WHERE id = ?",
                (hypothesis_id,),
            ).fetchone()
            if row is None:
                raise HypothesisNotFound(hypothesis_id)

            hypothesis = Hypothesis.model_validate_json(row["payload"])
            allowed = ALLOWED_TRANSITIONS[hypothesis.status]
            if request.to_status not in allowed:
                raise InvalidTransition(
                    f"{hypothesis.status.value} -> {request.to_status.value}"
                )
            if (
                request.to_status is HypothesisStatus.submitted
                and not hypothesis.falsifiers
            ):
                raise InvalidTransition(
                    "submission requires at least one falsifier"
                )

            now = utcnow()
            updated = hypothesis.model_copy(
                update={"status": request.to_status, "updated_at": now}
            )
            conn.execute(
                """
                UPDATE hypotheses
                SET status = ?, payload = ?, updated_at = ?
                WHERE id = ?
                """,
                (
                    updated.status.value,
                    updated.model_dump_json(by_alias=True),
                    now.isoformat(),
                    hypothesis_id,
                ),
            )
            cursor = conn.execute(
                """
                INSERT INTO hypothesis_events
                    (hypothesis_id, from_status, to_status, actor, reason, at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    hypothesis_id,
                    hypothesis.status.value,
                    request.to_status.value,
                    request.actor,
                    request.reason,
                    now.isoformat(),
                ),
            )
            event = TransitionEvent(
                id=int(cursor.lastrowid),
                hypothesis_id=hypothesis_id,
                from_status=hypothesis.status,
                to_status=request.to_status,
                actor=request.actor,
                reason=request.reason,
                at=now,
            )
        return updated, event

    def events(self, hypothesis_id: str) -> list[TransitionEvent]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT * FROM hypothesis_events
                WHERE hypothesis_id = ?
                ORDER BY id ASC
                """,
                (hypothesis_id,),
            ).fetchall()
        return [
            TransitionEvent(
                id=row["id"],
                hypothesis_id=row["hypothesis_id"],
                from_status=HypothesisStatus(row["from_status"]),
                to_status=HypothesisStatus(row["to_status"]),
                actor=row["actor"],
                reason=row["reason"],
                at=datetime.fromisoformat(row["at"]),
            )
            for row in rows
        ]
