from __future__ import annotations

import json
import sqlite3
from datetime import datetime
from pathlib import Path

from ..models import Artifact, CR, Decision, Review, ReviewScores, Round, Run, RunEvent


class SqliteStore:
    def __init__(self, db_path: str):
        self.db_path: str = db_path
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self._conn: sqlite3.Connection = sqlite3.connect(db_path)
        self._conn.row_factory = sqlite3.Row
        self._init_schema()

    def _init_schema(self) -> None:
        cur = self._conn.cursor()
        _ = cur.execute(
            """
            CREATE TABLE IF NOT EXISTS runs (
                id TEXT PRIMARY KEY,
                idea TEXT,
                config_json TEXT,
                status TEXT,
                cost_usd REAL,
                total_rounds INTEGER,
                stop_reason TEXT,
                error TEXT,
                created_at TEXT,
                updated_at TEXT
            )
            """
        )
        _ = cur.execute(
            """
            CREATE TABLE IF NOT EXISTS rounds (
                id TEXT PRIMARY KEY,
                run_id TEXT,
                step TEXT,
                role TEXT,
                provider_name TEXT,
                model TEXT,
                prompt_hash TEXT,
                input_tokens INTEGER,
                output_tokens INTEGER,
                cost_usd REAL,
                latency_ms INTEGER,
                raw_output TEXT,
                metadata_json TEXT,
                created_at TEXT
            )
            """
        )
        _ = cur.execute(
            """
            CREATE TABLE IF NOT EXISTS artifacts (
                id TEXT PRIMARY KEY,
                run_id TEXT,
                artifact_type TEXT,
                version INTEGER,
                content_json TEXT,
                raw_text TEXT,
                summary TEXT,
                diff_summary TEXT,
                previous_artifact_id TEXT,
                schema_coverage REAL,
                created_at TEXT
            )
            """
        )
        _ = cur.execute(
            """
            CREATE TABLE IF NOT EXISTS reviews (
                id TEXT PRIMARY KEY,
                round_id TEXT,
                artifact_id TEXT,
                hat TEXT,
                verdict TEXT,
                scores_json TEXT,
                blocking_count INTEGER,
                crs_json TEXT,
                summary TEXT,
                created_at TEXT
            )
            """
        )
        _ = cur.execute(
            """
            CREATE TABLE IF NOT EXISTS crs (
                id TEXT PRIMARY KEY,
                artifact_id TEXT,
                round_id TEXT,
                problem TEXT,
                rationale TEXT,
                change TEXT,
                acceptance TEXT,
                severity TEXT,
                dimension TEXT,
                status TEXT,
                resolution_note TEXT,
                resolved_at TEXT,
                created_at TEXT
            )
            """
        )
        _ = cur.execute(
            """
            CREATE TABLE IF NOT EXISTS decisions (
                id TEXT PRIMARY KEY,
                run_id TEXT,
                round_number INTEGER,
                decision TEXT,
                stop_reason TEXT,
                avg_score REAL,
                blocking_count INTEGER,
                reason TEXT,
                created_at TEXT
            )
            """
        )
        _ = cur.execute(
            """
            CREATE TABLE IF NOT EXISTS run_events (
                id TEXT PRIMARY KEY,
                run_id TEXT,
                step TEXT,
                event_type TEXT,
                round_number INTEGER,
                detail TEXT,
                payload_json TEXT,
                created_at TEXT
            )
            """
        )
        self._ensure_column(table="artifacts", column="previous_artifact_id", column_type="TEXT")
        self._conn.commit()

    def _ensure_column(self, *, table: str, column: str, column_type: str) -> None:
        cur = self._conn.cursor()
        rows = cur.execute(f"PRAGMA table_info({table})").fetchall()
        columns = {str(row["name"]) for row in rows}
        if column not in columns:
            _ = cur.execute(f"ALTER TABLE {table} ADD COLUMN {column} {column_type}")

    @staticmethod
    def _parse_datetime(value: str) -> datetime:
        return datetime.fromisoformat(value)

    @staticmethod
    def _load_dict(raw: str | None) -> dict[str, object]:
        if not raw:
            return {}
        data = json.loads(raw)
        if isinstance(data, dict):
            return {str(k): v for k, v in data.items()}
        return {}

    @staticmethod
    def _load_list(raw: str | None) -> list[object]:
        if not raw:
            return []
        data = json.loads(raw)
        if isinstance(data, list):
            return data
        return []

    def _row_to_run(self, row: sqlite3.Row) -> Run:
        return Run(
            id=row["id"],
            idea=row["idea"] or "",
            config_json=row["config_json"] or "",
            status=row["status"],
            cost_usd=float(row["cost_usd"] or 0.0),
            total_rounds=int(row["total_rounds"] or 0),
            stop_reason=row["stop_reason"],
            error=row["error"],
            created_at=self._parse_datetime(row["created_at"]),
            updated_at=self._parse_datetime(row["updated_at"]),
        )

    def _row_to_round(self, row: sqlite3.Row) -> Round:
        return Round(
            id=row["id"],
            run_id=row["run_id"],
            step=row["step"] or "",
            role=row["role"] or "",
            provider_name=row["provider_name"] or "",
            model=row["model"] or "",
            prompt_hash=row["prompt_hash"] or "",
            input_tokens=int(row["input_tokens"] or 0),
            output_tokens=int(row["output_tokens"] or 0),
            cost_usd=float(row["cost_usd"] or 0.0),
            latency_ms=int(row["latency_ms"] or 0),
            raw_output=row["raw_output"] or "",
            metadata=self._load_dict(row["metadata_json"]),
            created_at=self._parse_datetime(row["created_at"]),
        )

    def _row_to_artifact(self, row: sqlite3.Row) -> Artifact:
        return Artifact(
            id=row["id"],
            run_id=row["run_id"],
            artifact_type=row["artifact_type"],
            version=int(row["version"] or 1),
            content=self._load_dict(row["content_json"]),
            raw_text=row["raw_text"] or "",
            summary=row["summary"] or "",
            diff_summary=row["diff_summary"] or "",
            previous_artifact_id=row["previous_artifact_id"],
            schema_coverage=float(row["schema_coverage"] or 0.0),
            created_at=self._parse_datetime(row["created_at"]),
        )

    def _row_to_review(self, row: sqlite3.Row) -> Review:
        scores_data = self._load_dict(row["scores_json"])
        cr_list: list[CR] = []
        for item in self._load_list(row["crs_json"]):
            if isinstance(item, dict):
                cr_list.append(CR.model_validate(item))
        return Review(
            id=row["id"],
            round_id=row["round_id"],
            artifact_id=row["artifact_id"] or "",
            hat=row["hat"] or "",
            verdict=row["verdict"],
            scores=ReviewScores.model_validate(scores_data),
            blocking_count=int(row["blocking_count"] or 0),
            crs=cr_list,
            summary=row["summary"] or "",
            created_at=self._parse_datetime(row["created_at"]),
        )

    def _row_to_cr(self, row: sqlite3.Row) -> CR:
        resolved_at_raw = row["resolved_at"]
        resolved_at = None if resolved_at_raw is None else self._parse_datetime(str(resolved_at_raw))
        return CR(
            id=row["id"],
            artifact_id=row["artifact_id"] or "",
            round_id=row["round_id"],
            problem=row["problem"] or "",
            rationale=row["rationale"] or "",
            change=row["change"] or "",
            acceptance=row["acceptance"] or "",
            severity=row["severity"],
            dimension=row["dimension"] or "",
            status=row["status"],
            resolution_note=row["resolution_note"] or "",
            resolved_at=resolved_at,
            created_at=self._parse_datetime(row["created_at"]),
        )

    def _row_to_decision(self, row: sqlite3.Row) -> Decision:
        return Decision(
            id=row["id"],
            run_id=row["run_id"],
            round_number=int(row["round_number"] or 0),
            decision=row["decision"],
            stop_reason=row["stop_reason"],
            avg_score=float(row["avg_score"] or 0.0),
            blocking_count=int(row["blocking_count"] or 0),
            reason=row["reason"] or "",
            created_at=self._parse_datetime(row["created_at"]),
        )

    def _row_to_run_event(self, row: sqlite3.Row) -> RunEvent:
        return RunEvent(
            id=row["id"],
            run_id=row["run_id"],
            step=row["step"] or "",
            event_type=row["event_type"] or "",
            round_number=int(row["round_number"] or 0),
            detail=row["detail"] or "",
            payload=self._load_dict(row["payload_json"]),
            created_at=self._parse_datetime(row["created_at"]),
        )

    def insert_run(self, run: Run) -> None:
        self._conn.execute(
            """
            INSERT INTO runs (id, idea, config_json, status, cost_usd, total_rounds,
                              stop_reason, error, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run.id,
                run.idea,
                run.config_json,
                run.status,
                run.cost_usd,
                run.total_rounds,
                run.stop_reason,
                run.error,
                run.created_at.isoformat(),
                run.updated_at.isoformat(),
            ),
        )
        self._conn.commit()

    def update_run(self, run: Run) -> None:
        self._conn.execute(
            """
            UPDATE runs
               SET status = ?, cost_usd = ?, total_rounds = ?, stop_reason = ?,
                   error = ?, updated_at = ?
             WHERE id = ?
            """,
            (
                run.status,
                run.cost_usd,
                run.total_rounds,
                run.stop_reason,
                run.error,
                run.updated_at.isoformat(),
                run.id,
            ),
        )
        self._conn.commit()

    def insert_round(self, rnd: Round) -> None:
        self._conn.execute(
            """
            INSERT INTO rounds (id, run_id, step, role, provider_name, model, prompt_hash,
                                input_tokens, output_tokens, cost_usd, latency_ms, raw_output,
                                metadata_json, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                rnd.id,
                rnd.run_id,
                rnd.step,
                rnd.role,
                rnd.provider_name,
                rnd.model,
                rnd.prompt_hash,
                rnd.input_tokens,
                rnd.output_tokens,
                rnd.cost_usd,
                rnd.latency_ms,
                rnd.raw_output,
                json.dumps(rnd.metadata),
                rnd.created_at.isoformat(),
            ),
        )
        self._conn.commit()

    def insert_artifact(self, artifact: Artifact) -> None:
        self._conn.execute(
            """
            INSERT INTO artifacts (id, run_id, artifact_type, version, content_json, raw_text,
                                   summary, diff_summary, previous_artifact_id, schema_coverage,
                                   created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                artifact.id,
                artifact.run_id,
                artifact.artifact_type,
                artifact.version,
                json.dumps(artifact.content, ensure_ascii=False),
                artifact.raw_text,
                artifact.summary,
                artifact.diff_summary,
                artifact.previous_artifact_id,
                artifact.schema_coverage,
                artifact.created_at.isoformat(),
            ),
        )
        self._conn.commit()

    def get_run(self, run_id: str) -> Run | None:
        row = self._conn.execute("SELECT * FROM runs WHERE id = ?", (run_id,)).fetchone()
        if row is None:
            return None
        return self._row_to_run(row)

    def get_latest_run(self) -> Run | None:
        row = self._conn.execute(
            """
            SELECT *
              FROM runs
             ORDER BY updated_at DESC, created_at DESC
             LIMIT 1
            """
        ).fetchone()
        if row is None:
            return None
        return self._row_to_run(row)

    def get_round(self, round_id: str) -> Round | None:
        row = self._conn.execute("SELECT * FROM rounds WHERE id = ?", (round_id,)).fetchone()
        if row is None:
            return None
        return self._row_to_round(row)

    def get_artifact(self, artifact_id: str) -> Artifact | None:
        row = self._conn.execute("SELECT * FROM artifacts WHERE id = ?", (artifact_id,)).fetchone()
        if row is None:
            return None
        return self._row_to_artifact(row)

    def get_latest_artifact(self, run_id: str, artifact_type: str) -> Artifact | None:
        row = self._conn.execute(
            """
            SELECT *
              FROM artifacts
             WHERE run_id = ? AND artifact_type = ?
             ORDER BY version DESC, created_at DESC
             LIMIT 1
            """,
            (run_id, artifact_type),
        ).fetchone()
        if row is None:
            return None
        return self._row_to_artifact(row)

    def list_rounds(self, run_id: str) -> list[Round]:
        rows = self._conn.execute(
            "SELECT * FROM rounds WHERE run_id = ? ORDER BY created_at ASC",
            (run_id,),
        ).fetchall()
        return [self._row_to_round(row) for row in rows]

    def list_artifacts(self, run_id: str, artifact_type: str | None = None) -> list[Artifact]:
        if artifact_type is None:
            rows = self._conn.execute(
                "SELECT * FROM artifacts WHERE run_id = ? ORDER BY version ASC, created_at ASC",
                (run_id,),
            ).fetchall()
        else:
            rows = self._conn.execute(
                """
                SELECT *
                  FROM artifacts
                 WHERE run_id = ? AND artifact_type = ?
                 ORDER BY version ASC, created_at ASC
                """,
                (run_id, artifact_type),
            ).fetchall()
        return [self._row_to_artifact(row) for row in rows]

    def list_artifact_chain(self, artifact_id: str) -> list[Artifact]:
        chain: list[Artifact] = []
        current = self.get_artifact(artifact_id)
        while current is not None:
            chain.append(current)
            if current.previous_artifact_id is None:
                break
            current = self.get_artifact(current.previous_artifact_id)
        chain.reverse()
        return chain

    def list_reviews(self, run_id: str) -> list[Review]:
        rows = self._conn.execute(
            """
            SELECT rv.*
              FROM reviews rv
              JOIN rounds rd ON rd.id = rv.round_id
             WHERE rd.run_id = ?
             ORDER BY rv.created_at ASC
            """,
            (run_id,),
        ).fetchall()
        return [self._row_to_review(row) for row in rows]

    def list_crs(self, run_id: str) -> list[CR]:
        rows = self._conn.execute(
            """
            SELECT cr.*
              FROM crs cr
              JOIN rounds rd ON rd.id = cr.round_id
             WHERE rd.run_id = ?
             ORDER BY cr.created_at ASC
            """,
            (run_id,),
        ).fetchall()
        return [self._row_to_cr(row) for row in rows]

    def list_decisions(self, run_id: str) -> list[Decision]:
        rows = self._conn.execute(
            """
            SELECT *
              FROM decisions
             WHERE run_id = ?
             ORDER BY round_number ASC, created_at ASC
            """,
            (run_id,),
        ).fetchall()
        return [self._row_to_decision(row) for row in rows]

    def insert_review(self, review: Review) -> None:
        self._conn.execute(
            """
            INSERT INTO reviews (id, round_id, artifact_id, hat, verdict, scores_json,
                                 blocking_count, crs_json, summary, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                review.id,
                review.round_id,
                review.artifact_id,
                review.hat,
                review.verdict,
                review.scores.model_dump_json(),
                review.blocking_count,
                json.dumps(
                    [cr.model_dump(mode="json") for cr in review.crs],
                    ensure_ascii=False,
                ),
                review.summary,
                review.created_at.isoformat(),
            ),
        )
        self._conn.commit()

    def insert_cr(self, cr: CR) -> None:
        self._conn.execute(
            """
            INSERT INTO crs (id, artifact_id, round_id, problem, rationale, change,
                             acceptance, severity, dimension, status, resolution_note,
                             resolved_at, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                cr.id,
                cr.artifact_id,
                cr.round_id,
                cr.problem,
                cr.rationale,
                cr.change,
                cr.acceptance,
                cr.severity,
                cr.dimension,
                cr.status,
                cr.resolution_note,
                cr.resolved_at.isoformat() if cr.resolved_at else None,
                cr.created_at.isoformat(),
            ),
        )
        self._conn.commit()

    def insert_decision(self, decision: Decision) -> None:
        self._conn.execute(
            """
            INSERT INTO decisions (id, run_id, round_number, decision, stop_reason,
                                   avg_score, blocking_count, reason, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                decision.id,
                decision.run_id,
                decision.round_number,
                decision.decision,
                decision.stop_reason,
                decision.avg_score,
                decision.blocking_count,
                decision.reason,
                decision.created_at.isoformat(),
            ),
        )
        self._conn.commit()

    def insert_run_event(self, event: RunEvent) -> None:
        self._conn.execute(
            """
            INSERT INTO run_events (id, run_id, step, event_type, round_number, detail,
                                    payload_json, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                event.id,
                event.run_id,
                event.step,
                event.event_type,
                event.round_number,
                event.detail,
                json.dumps(event.payload, ensure_ascii=False),
                event.created_at.isoformat(),
            ),
        )
        self._conn.commit()

    def list_run_events(self, run_id: str) -> list[RunEvent]:
        rows = self._conn.execute(
            """
            SELECT *
              FROM run_events
             WHERE run_id = ?
             ORDER BY created_at ASC
            """,
            (run_id,),
        ).fetchall()
        return [self._row_to_run_event(row) for row in rows]

    def close(self) -> None:
        self._conn.close()
