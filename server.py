"""
P3/P4 Maths Practice — FastAPI backend
=======================================
Run locally:   uvicorn server:app --reload --port 8000
Deploy:        Render / Railway via Procfile
"""
from __future__ import annotations

import dataclasses
import json
import math
import os
import random
import re
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path
import pathlib
from typing import Any, Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

# ── Paths ────────────────────────────────────────────────────────────────────
BASE         = Path(__file__).parent
TAXONOMY_PATH = BASE / "taxonomy.json"
BANKS_PATH   = BASE / "question_banks"
# On Render the persistent disk is mounted at /opt/render/project/src/data
_render_data = pathlib.Path("/opt/render/project/src/data")
DB_PATH      = (_render_data if _render_data.exists() else BASE / "data") / "sessions.db"
STATIC_PATH  = BASE / "static"

# ── Import generators ─────────────────────────────────────────────────────────
sys.path.insert(0, str(BASE))
from generators import _RANDOM_GENERATORS  # noqa: E402

# ── Load taxonomy ─────────────────────────────────────────────────────────────
taxonomy: dict = {}
if TAXONOMY_PATH.exists():
    taxonomy = json.loads(TAXONOMY_PATH.read_text())

def get_taxonomy_topic(topic_id: str) -> dict:
    """Return taxonomy metadata for a topic ID."""
    topics = taxonomy.get("topics", {})
    return topics.get(topic_id, {})

def get_taxonomy_structure(structure_id: str) -> dict:
    """Return taxonomy metadata for a question structure ID."""
    structures = taxonomy.get("question_structures", {})
    return structures.get(structure_id, {})

# ── Load manifests ────────────────────────────────────────────────────────────
def load_manifests() -> list[dict]:
    manifests = []
    if BANKS_PATH.exists():
        for f in sorted(BANKS_PATH.rglob("manifest.json")):
            try:
                manifests.append(json.loads(f.read_text()))
            except Exception as e:
                print(f"WARNING: could not load {f}: {e}")
    return manifests

MANIFESTS = load_manifests()

# Build lookup: grade → assessment → [topic_dict, ...]
TOPIC_INDEX: dict[str, dict[str, list[dict]]] = {}
for _m in MANIFESTS:
    g, a = _m["grade"], _m["assessment"]
    TOPIC_INDEX.setdefault(g, {}).setdefault(a, []).extend(_m["topics"])

# Validate structure_ids against _RANDOM_GENERATORS
for _m in MANIFESTS:
    for _t in _m["topics"]:
        for _sid in _t["structure_ids"]:
            if _sid not in _RANDOM_GENERATORS:
                print(f"WARNING: structure_id '{_sid}' in manifest not in _RANDOM_GENERATORS")

# ── Database ──────────────────────────────────────────────────────────────────
DB_PATH.parent.mkdir(parents=True, exist_ok=True)

def get_db() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn

def init_db() -> None:
    with get_db() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS students (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                name       TEXT NOT NULL UNIQUE COLLATE NOCASE,
                created_at TEXT DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS sessions (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id      INTEGER NOT NULL,
                grade           TEXT NOT NULL,
                assessment      TEXT NOT NULL,
                topic_key       TEXT NOT NULL,
                topic_label     TEXT NOT NULL,
                mode            TEXT NOT NULL DEFAULT 'generated',
                questions_json  TEXT NOT NULL,
                started_at      TEXT DEFAULT (datetime('now')),
                ended_at        TEXT,
                score           INTEGER,
                max_score       INTEGER,
                FOREIGN KEY (student_id) REFERENCES students(id)
            );

            CREATE TABLE IF NOT EXISTS responses (
                id               INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id       INTEGER NOT NULL,
                question_index   INTEGER NOT NULL,
                structure_id     TEXT NOT NULL,
                topic_key        TEXT NOT NULL,
                question_text    TEXT NOT NULL,
                user_answer      TEXT,
                correct_answer   TEXT NOT NULL,
                is_correct       INTEGER NOT NULL DEFAULT 0,
                marks_earned     INTEGER NOT NULL DEFAULT 0,
                marks_available  INTEGER NOT NULL DEFAULT 1,
                FOREIGN KEY (session_id) REFERENCES sessions(id),
                UNIQUE (session_id, question_index)
            );
        """)

init_db()

# ── Bank question loading ─────────────────────────────────────────────────────

def load_bank_questions(grade: str, assessment: str, structure_ids: list[str]) -> list[dict]:
    """
    Load static exam questions from JSON files in question_banks/{grade}/{assessment}/.
    Each file (except manifest.json) is expected to have a top-level "questions" list.
    Filters to questions whose structure_id is in the topic's structure_ids.
    Static files store correct_option as 0-indexed — no conversion needed.
    """
    folder = BANKS_PATH / grade / assessment
    if not folder.exists():
        return []
    questions: list[dict] = []
    for f in sorted(folder.glob("*.json")):
        if f.name == "manifest.json":
            continue
        try:
            data = json.loads(f.read_text())
            source = data.get("source", f.stem)
            for q in data.get("questions", []):
                if q.get("structure_id") in structure_ids:
                    q = dict(q)          # don't mutate the parsed data
                    q.setdefault("source", source)
                    q.setdefault("working", "")
                    q.setdefault("section", "A")
                    questions.append(q)
        except Exception as e:
            print(f"WARNING: could not load bank file {f}: {e}")
    return questions

# ── Question generation ───────────────────────────────────────────────────────
def question_to_dict(q) -> dict:
    """Convert Question dataclass → dict, normalising correct_option to 0-indexed."""
    d = dataclasses.asdict(q)
    # Python generators use 1-indexed correct_option; convert for JS
    if d.get("correct_option") is not None:
        d["correct_option"] = d["correct_option"] - 1   # now 0-indexed
    return d

def generate_questions(structure_ids: list[str], n: int = 20) -> list[dict]:
    """Round-robin through structure_ids, generate n questions."""
    questions = []
    pool = list(structure_ids)
    random.shuffle(pool)
    for i in range(n):
        sid = pool[i % len(pool)]
        gen = _RANDOM_GENERATORS.get(sid)
        if gen is None:
            continue
        try:
            questions.append(question_to_dict(gen()))
        except Exception as e:
            print(f"WARNING: generator '{sid}' failed: {e}")
    return questions

def strip_answers(questions: list[dict]) -> list[dict]:
    """Remove answer fields before sending to client — server checks answers."""
    safe_keys = {"structure_id", "topic", "text", "options", "marks", "section"}
    return [{k: v for k, v in q.items() if k in safe_keys} for q in questions]

# ── Answer checking ───────────────────────────────────────────────────────────
def check_answer(q: dict, user_answer: str) -> bool:
    """Return True if user_answer matches the question's correct answer."""
    if q.get("options") is not None:
        # MCQ: user sends 0-indexed selected option as string
        try:
            return int(user_answer) == q["correct_option"]
        except (ValueError, TypeError):
            return False

    # Short answer
    ua = str(user_answer).strip().lower()
    ca = str(q["answer"]).strip().lower()
    if not ua:
        return False
    if ua == ca:
        return True

    # Numeric / money ($X.XX)
    try:
        un = float(ua.replace("$", "").replace(",", ""))
        cn = float(ca.replace("$", "").replace(",", ""))
        return abs(un - cn) < 0.005
    except ValueError:
        pass

    # Fraction: cross-multiply
    frac = lambda s: re.match(r"^(\d+)/(\d+)$", s)
    uf, cf = frac(ua), frac(ca)
    if uf and cf:
        return int(uf.group(1)) * int(cf.group(2)) == int(cf.group(1)) * int(uf.group(2))

    return False

# ── FastAPI app ───────────────────────────────────────────────────────────────
app = FastAPI(title="P3/P4 Maths Practice", version="1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── API: Curriculum ───────────────────────────────────────────────────────────

@app.get("/api/grades")
def list_grades():
    """All grades and their available assessments."""
    return [
        {"grade": g, "assessments": sorted(TOPIC_INDEX[g].keys())}
        for g in sorted(TOPIC_INDEX)
    ]

@app.get("/api/topics")
def list_topics(grade: str = Query(...), assessment: str = Query(...)):
    """Topics available for a given grade + assessment, with bank question counts."""
    topics = TOPIC_INDEX.get(grade, {}).get(assessment)
    if not topics:
        raise HTTPException(404, f"No topics for {grade} {assessment}")
    result = []
    for t in topics:
        entry = dict(t)
        tx = get_taxonomy_topic(t.get("taxonomy_topic") or "")
        entry["taxonomy_label"] = tx.get("label", "")
        entry["taxonomy_description"] = tx.get("description", "")
        # Count available bank questions so the UI can show/grey-out the toggle
        entry["bank_count"] = len(load_bank_questions(grade, assessment, t["structure_ids"]))
        result.append(entry)
    return result

@app.get("/api/taxonomy/structure/{structure_id}")
def taxonomy_structure(structure_id: str):
    """Taxonomy metadata for a structure ID — for future misconception mapping."""
    s = get_taxonomy_structure(structure_id)
    if not s:
        raise HTTPException(404, f"No taxonomy entry for '{structure_id}'")
    return s

# ── API: Students ─────────────────────────────────────────────────────────────

class StudentIn(BaseModel):
    name: str

@app.get("/api/students")
def list_students():
    with get_db() as db:
        rows = db.execute(
            "SELECT id, name, created_at FROM students ORDER BY name COLLATE NOCASE"
        ).fetchall()
    return [dict(r) for r in rows]

@app.post("/api/students", status_code=201)
def get_or_create_student(body: StudentIn):
    name = body.name.strip()
    if not name:
        raise HTTPException(400, "Name cannot be empty")
    with get_db() as db:
        row = db.execute(
            "SELECT id, name FROM students WHERE name = ? COLLATE NOCASE", (name,)
        ).fetchone()
        if row:
            return {"id": row["id"], "name": row["name"], "is_new": False}
        cur = db.execute("INSERT INTO students (name) VALUES (?)", (name,))
        return {"id": cur.lastrowid, "name": name, "is_new": True}

# ── API: Sessions ─────────────────────────────────────────────────────────────

class SessionIn(BaseModel):
    student_id: int
    grade: str
    assessment: str
    topic_key: str
    mode: str = "generated"   # "generated" | "bank"

@app.post("/api/sessions", status_code=201)
def create_session(body: SessionIn):
    topics = TOPIC_INDEX.get(body.grade, {}).get(body.assessment, [])
    topic = next((t for t in topics if t["key"] == body.topic_key), None)
    if not topic:
        raise HTTPException(404, f"Topic '{body.topic_key}' not found in {body.grade} {body.assessment}")

    if body.mode == "bank":
        bank_qs = load_bank_questions(body.grade, body.assessment, topic["structure_ids"])
        if not bank_qs:
            raise HTTPException(404, f"No exam bank questions for '{topic['label']}' yet. "
                                     "Add a JSON file to question_banks/{grade}/{assessment}/.")
        random.shuffle(bank_qs)
        questions = bank_qs[:20]   # cap at 20; serve all if fewer
    else:
        questions = generate_questions(topic["structure_ids"], n=20)

    if not questions:
        raise HTTPException(500, "Failed to generate questions — check generator registration")

    with get_db() as db:
        cur = db.execute(
            """INSERT INTO sessions
               (student_id, grade, assessment, topic_key, topic_label, mode, questions_json)
               VALUES (?,?,?,?,?,?,?)""",
            (body.student_id, body.grade, body.assessment,
             body.topic_key, topic["label"], body.mode, json.dumps(questions)),
        )
        session_id = cur.lastrowid

    return {
        "session_id": session_id,
        "questions": strip_answers(questions),
        "total": len(questions),
    }

class AnswerIn(BaseModel):
    question_index: int
    user_answer: str   # 0-indexed option index (str) for MCQ; text for short answer

@app.post("/api/sessions/{session_id}/responses")
def submit_response(session_id: int, body: AnswerIn):
    with get_db() as db:
        session = db.execute(
            "SELECT questions_json, ended_at FROM sessions WHERE id = ?", (session_id,)
        ).fetchone()
        if not session:
            raise HTTPException(404, "Session not found")
        if session["ended_at"]:
            raise HTTPException(400, "Session already ended")

        questions = json.loads(session["questions_json"])
        if not (0 <= body.question_index < len(questions)):
            raise HTTPException(400, "question_index out of range")

        q = questions[body.question_index]
        correct = check_answer(q, body.user_answer)
        marks_earned = q["marks"] if correct else 0

        # Upsert (ignore duplicate submissions for the same question)
        db.execute(
            """INSERT OR IGNORE INTO responses
               (session_id, question_index, structure_id, topic_key,
                question_text, user_answer, correct_answer,
                is_correct, marks_earned, marks_available)
               VALUES (?,?,?,?,?,?,?,?,?,?)""",
            (session_id, body.question_index, q["structure_id"], q["topic"],
             q["text"], body.user_answer, q["answer"],
             1 if correct else 0, marks_earned, q["marks"]),
        )

    return {
        "correct": correct,
        "correct_answer": q["answer"],
        "working": q.get("working", ""),
        "marks_earned": marks_earned,
        "marks_available": q["marks"],
    }

class EndIn(BaseModel):
    duration_seconds: int = 0

@app.patch("/api/sessions/{session_id}/end")
def end_session(session_id: int, body: EndIn):
    with get_db() as db:
        row = db.execute(
            """SELECT COALESCE(SUM(marks_earned),0) AS earned,
                      COALESCE(SUM(marks_available),0) AS total
               FROM responses WHERE session_id=?""",
            (session_id,),
        ).fetchone()
        db.execute(
            "UPDATE sessions SET ended_at=datetime('now'), score=?, max_score=? WHERE id=?",
            (row["earned"], row["total"], session_id),
        )
    return {"ok": True, "score": row["earned"], "max_score": row["total"]}

# ── API: Student history & stats ──────────────────────────────────────────────

@app.get("/api/students/{student_id}/history")
def get_history(student_id: int):
    with get_db() as db:
        rows = db.execute(
            """SELECT s.id, s.grade, s.assessment, s.topic_label, s.mode,
                      s.score, s.max_score, s.started_at,
                      COUNT(r.id) AS questions_attempted
               FROM sessions s
               LEFT JOIN responses r ON r.session_id = s.id
               WHERE s.student_id = ? AND s.ended_at IS NOT NULL
               GROUP BY s.id
               ORDER BY s.started_at DESC
               LIMIT 100""",
            (student_id,),
        ).fetchall()
    return [dict(r) for r in rows]

@app.get("/api/students/{student_id}/stats")
def get_stats(student_id: int):
    """Per-topic accuracy — ready for misconception mapping."""
    with get_db() as db:
        rows = db.execute(
            """SELECT r.topic_key,
                      r.structure_id,
                      COUNT(*)              AS attempts,
                      SUM(r.is_correct)     AS correct,
                      SUM(r.marks_earned)   AS earned,
                      SUM(r.marks_available) AS available
               FROM responses r
               JOIN sessions s ON s.id = r.session_id
               WHERE s.student_id = ? AND s.ended_at IS NOT NULL
               GROUP BY r.topic_key, r.structure_id
               ORDER BY r.topic_key, r.structure_id""",
            (student_id,),
        ).fetchall()
    result = []
    for r in rows:
        d = dict(r)
        # Attach taxonomy metadata for future misconception mapping
        d["taxonomy"] = get_taxonomy_structure(d["structure_id"])
        result.append(d)
    return result

@app.get("/api/students/{student_id}/responses")
def get_responses(student_id: int, session_id: Optional[int] = None):
    """
    Raw responses — primary hook for misconception mapping.
    Each row has structure_id, topic_key, user_answer, correct_answer, is_correct.
    """
    with get_db() as db:
        if session_id:
            rows = db.execute(
                """SELECT r.* FROM responses r
                   JOIN sessions s ON s.id = r.session_id
                   WHERE s.student_id=? AND r.session_id=?
                   ORDER BY r.question_index""",
                (student_id, session_id),
            ).fetchall()
        else:
            rows = db.execute(
                """SELECT r.*, s.grade, s.assessment, s.topic_label, s.started_at
                   FROM responses r
                   JOIN sessions s ON s.id = r.session_id
                   WHERE s.student_id=? AND s.ended_at IS NOT NULL
                   ORDER BY s.started_at DESC, r.question_index""",
                (student_id,),
            ).fetchall()
    result = []
    for r in rows:
        d = dict(r)
        # Attach taxonomy structure data alongside each response
        d["taxonomy"] = get_taxonomy_structure(d["structure_id"])
        result.append(d)
    return result

# ── Serve static files (must be last — catches all remaining routes) ───────────
if STATIC_PATH.exists():
    app.mount("/", StaticFiles(directory=str(STATIC_PATH), html=True), name="static")
