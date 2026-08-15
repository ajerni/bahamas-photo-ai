from __future__ import annotations

from sqlalchemy import create_engine

from backend.app.db.compat import ensure_sqlite_compat


def test_sqlite_compat_adds_usefulness_columns_to_old_schema(tmp_path):
    db_path = tmp_path / "old_private_memory_map.db"
    engine = create_engine(f"sqlite:///{db_path.as_posix()}")

    with engine.begin() as connection:
        connection.exec_driver_sql(
            "CREATE TABLE trip (id INTEGER PRIMARY KEY, title VARCHAR, "
            "description VARCHAR, created_at DATETIME)"
        )
        connection.exec_driver_sql(
            "CREATE TABLE photo (id INTEGER PRIMARY KEY, trip_id INTEGER, "
            "filename VARCHAR, stored_path VARCHAR, created_at DATETIME)"
        )
        connection.exec_driver_sql(
            "CREATE TABLE photoanalysis (photo_id INTEGER PRIMARY KEY, scene VARCHAR, "
            "activities JSON, objects JSON, mood VARCHAR, memory_prompt VARCHAR, "
            "confidence FLOAT, raw_model_json JSON)"
        )
        connection.exec_driver_sql(
            "CREATE TABLE tripmemory (trip_id INTEGER PRIMARY KEY, "
            "narrative_summary VARCHAR, inferred_interests JSON, recurring_themes JSON, "
            "memorable_moments JSON, evidence_photo_ids JSON, uncertainty_notes JSON, "
            "raw_model_json JSON, prompt_version VARCHAR, created_at DATETIME, "
            "updated_at DATETIME)"
        )
        connection.exec_driver_sql(
            "CREATE TABLE analysisjob (id INTEGER PRIMARY KEY, trip_id INTEGER, "
            "status VARCHAR, current_step VARCHAR, completed_steps INTEGER, "
            "total_steps INTEGER, error VARCHAR, created_at DATETIME, updated_at DATETIME)"
        )

    ensure_sqlite_compat(engine)

    assert _columns(engine, "trip") >= {"cover_photo_id"}
    assert _columns(engine, "photo") >= {
        "content_sha256",
        "byte_size",
        "mime_type",
        "is_favorite",
    }
    assert _columns(engine, "photoanalysis") >= {
        "user_memory_caption",
        "user_scene_summary",
        "user_mood",
        "user_note",
        "updated_at",
    }
    assert _columns(engine, "tripmemory") >= {
        "user_narrative_summary",
        "user_note",
    }
    assert _columns(engine, "analysisjob") >= {"mode"}


def _columns(engine, table_name: str) -> set[str]:
    with engine.begin() as connection:
        return {
            row[1]
            for row in connection.exec_driver_sql(f'PRAGMA table_info("{table_name}")')
        }
