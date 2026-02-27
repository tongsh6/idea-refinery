from pathlib import Path

from idea_refinery.models import Artifact
from idea_refinery.store import SqliteStore


def test_artifact_version_chain_queries(tmp_path: Path) -> None:
    db_path = tmp_path / "refinery.db"
    store = SqliteStore(str(db_path))

    run_id = "run-v"
    v1 = Artifact(
        run_id=run_id,
        artifact_type="PRD",
        version=1,
        content={"tldr": "v1"},
        raw_text="# v1",
    )
    store.insert_artifact(v1)

    v2 = Artifact(
        run_id=run_id,
        artifact_type="PRD",
        version=2,
        content={"tldr": "v2"},
        raw_text="# v2",
        previous_artifact_id=v1.id,
        diff_summary="v1->v2",
    )
    store.insert_artifact(v2)

    v3 = Artifact(
        run_id=run_id,
        artifact_type="PRD",
        version=3,
        content={"tldr": "v3"},
        raw_text="# v3",
        previous_artifact_id=v2.id,
        diff_summary="v2->v3",
    )
    store.insert_artifact(v3)

    latest = store.get_latest_artifact(run_id, "PRD")
    assert latest is not None
    assert latest.id == v3.id

    chain = store.list_artifact_chain(v3.id)
    assert [item.id for item in chain] == [v1.id, v2.id, v3.id]
    assert chain[-1].previous_artifact_id == v2.id

    all_versions = store.list_artifacts(run_id, "PRD")
    assert [item.version for item in all_versions] == [1, 2, 3]

    store.close()
