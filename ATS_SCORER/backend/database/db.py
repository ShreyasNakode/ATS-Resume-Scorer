import json
import logging
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import httpx

from backend.core.config import DATABASE_URL, SUPABASE_KEY, SUPABASE_URL

logger = logging.getLogger("ats_resume_scorer")

# Database path for SQLite
DB_FILE = Path(__file__).resolve().parents[2] / "ats_history.db"


def _init_sqlite_db():
    """Ensure SQLite database and tables are created."""
    try:
        with sqlite3.connect(DB_FILE) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS analyses (
                    id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    filename TEXT NOT NULL,
                    ats_score REAL NOT NULL,
                    keyword_match REAL DEFAULT 0.0,
                    missing_keywords TEXT,
                    created_at TEXT NOT NULL,
                    analysis_result TEXT NOT NULL
                )
                """
            )
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_user_id ON analyses (user_id)")
            conn.commit()
    except Exception as exc:
        logger.error(f"Failed to initialize SQLite database: {exc}")


_init_sqlite_db()


def _get_supabase_headers():
    if not SUPABASE_URL or not SUPABASE_KEY:
        return None
    return {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=representation",
    }


async def save_analysis(user_id: str, filename: str, analysis_result: Dict[str, Any]) -> str:
    """Save an analysis record to Supabase if configured, otherwise to SQLite."""
    analysis_id = str(uuid.uuid4())
    now_iso = datetime.now(timezone.utc).isoformat()

    def _json_default(o):
        if hasattr(o, "model_dump"):
            return o.model_dump()
        return str(o)

    serialized_result = json.dumps(analysis_result, default=_json_default)
    ats_score = float(analysis_result.get("ats_score", analysis_result.get("ATS_score", 0.0)))
    keyword_match = float(analysis_result.get("keyword_match", 0.0))
    missing_keywords = analysis_result.get("missing_keywords", [])

    # 1. Try Supabase if configured
    sb_headers = _get_supabase_headers()
    if sb_headers:
        doc = {
            "user_id": user_id,
            "filename": filename,
            "ats_score": ats_score,
            "keyword_match": keyword_match,
            "missing_keywords": missing_keywords,
            "created_at": now_iso,
            "analysis_result": json.loads(serialized_result),
        }
        url = f"{SUPABASE_URL.rstrip('/')}/rest/v1/analyses"
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(url, headers=sb_headers, json=doc)
                resp.raise_for_status()
                data = resp.json()
                if data and len(data) > 0:
                    return str(data[0].get("id"))
        except Exception as exc:
            logger.warning(f"Supabase write failed, falling back to SQLite: {exc}")

    # 2. SQLite local fallback
    try:
        with sqlite3.connect(DB_FILE) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO analyses (id, user_id, filename, ats_score, keyword_match, missing_keywords, created_at, analysis_result)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    analysis_id,
                    user_id,
                    filename,
                    ats_score,
                    keyword_match,
                    json.dumps(missing_keywords),
                    now_iso,
                    serialized_result,
                ),
            )
            conn.commit()
            logger.info(f"Saved analysis {analysis_id} for user {user_id} in SQLite")
            return analysis_id
    except Exception as exc:
        logger.error(f"Failed to save analysis to SQLite: {exc}")
        return analysis_id


async def get_user_history(user_id: str) -> List[Dict[str, Any]]:
    """Retrieve history for a user from Supabase or SQLite."""
    # 1. Try Supabase
    sb_headers = _get_supabase_headers()
    if sb_headers:
        url = f"{SUPABASE_URL.rstrip('/')}/rest/v1/analyses"
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    url,
                    headers=sb_headers,
                    params={"user_id": f"eq.{user_id}", "order": "created_at.desc"},
                )
                resp.raise_for_status()
                docs = resp.json()
                return [
                    {
                        "id": str(d.get("id")),
                        "filename": d.get("filename", "resume"),
                        "ats_score": float(d.get("ats_score", 0)),
                        "keyword_match": float(d.get("keyword_match", 0)),
                        "missing_keywords": d.get("missing_keywords", []),
                        "created_at": d.get("created_at", ""),
                        "analysis_result": d.get("analysis_result", {}),
                    }
                    for d in docs
                ]
        except Exception as exc:
            logger.warning(f"Supabase read failed, trying SQLite: {exc}")

    # 2. SQLite fallback
    try:
        with sqlite3.connect(DB_FILE) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT id, filename, ats_score, keyword_match, missing_keywords, created_at, analysis_result
                FROM analyses
                WHERE user_id = ?
                ORDER BY created_at DESC
                """,
                (user_id,),
            )
            rows = cursor.fetchall()
            results = []
            for r in rows:
                try:
                    res_dict = json.loads(r["analysis_result"])
                except Exception:
                    res_dict = {}
                try:
                    missing_kw = json.loads(r["missing_keywords"])
                except Exception:
                    missing_kw = []

                results.append(
                    {
                        "id": r["id"],
                        "filename": r["filename"],
                        "ats_score": r["ats_score"],
                        "keyword_match": r["keyword_match"],
                        "missing_keywords": missing_kw,
                        "created_at": r["created_at"],
                        "analysis_result": res_dict,
                    }
                )
            return results
    except Exception as exc:
        logger.error(f"Failed to read history from SQLite: {exc}")
        return []


async def delete_analysis(analysis_id: str, user_id: str) -> bool:
    """Delete an analysis record belonging to a user."""
    # 1. Try Supabase
    sb_headers = _get_supabase_headers()
    if sb_headers:
        url = f"{SUPABASE_URL.rstrip('/')}/rest/v1/analyses"
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.delete(
                    url,
                    headers=sb_headers,
                    params={"id": f"eq.{analysis_id}", "user_id": f"eq.{user_id}"},
                )
                if resp.status_code in (200, 204):
                    return True
        except Exception as exc:
            logger.warning(f"Supabase delete failed: {exc}")

    # 2. SQLite fallback
    try:
        with sqlite3.connect(DB_FILE) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "DELETE FROM analyses WHERE id = ? AND user_id = ?",
                (analysis_id, user_id),
            )
            conn.commit()
            return cursor.rowcount > 0
    except Exception as exc:
        logger.error(f"Failed to delete analysis from SQLite: {exc}")
        return False
