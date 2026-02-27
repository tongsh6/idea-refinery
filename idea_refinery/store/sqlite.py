from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from ..models import Artifact, CR, Decision, Review, Round, Run


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
        self._conn.commit()

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
                                   summary, diff_summary, schema_coverage, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                artifact.schema_coverage,
                artifact.created_at.isoformat(),
            ),
        )
        self._conn.commit()

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

    def close(self) -> None:
        self._conn.close()
