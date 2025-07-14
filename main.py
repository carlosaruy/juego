"""Aplicacion principal del quiz con FastAPI."""
import json
import sqlite3
import asyncio
from datetime import datetime
from typing import Dict, List

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from sse_starlette.sse import EventSourceResponse

from questions_data import QUESTION_OPTIONS

# TODO: implementar autenticacion real con JWT

COEFFICIENTS = [1.0, 0.7, 0.4, 0.1, 0]
MAX_ATTEMPTS = 4

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="static"), name="static")


# Diccionario de listeners para SSE por grupo
listeners: Dict[int, List[asyncio.Queue]] = {}

def get_db():
    conn = sqlite3.connect("quiz.db", check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def ensure_user(conn: sqlite3.Connection, name: str, group_id: int) -> int:
    """Obtiene el id de usuario o lo crea si no existe."""
    cur = conn.cursor()
    cur.execute('SELECT id FROM "User" WHERE name=? AND group_id=?', (name, group_id))
    row = cur.fetchone()
    if row:
        return row["id"]
    cur.execute('INSERT INTO "User"(name, group_id) VALUES (?, ?)', (name, group_id))
    conn.commit()
    return cur.lastrowid


def compute_scoreboard(conn: sqlite3.Connection, group_id: int):
    """Calcula el puntaje total por usuario en el grupo."""
    cur = conn.cursor()
    cur.execute('SELECT id, name FROM "User" WHERE group_id=?', (group_id,))
    users = cur.fetchall()
    scoreboard = []
    for u in users:
        total = 0
        cur.execute(
            "SELECT question_id, option, is_correct, created_at FROM Attempt WHERE user_id=? ORDER BY question_id, created_at",
            (u["id"],),
        )
        by_question: Dict[int, List[sqlite3.Row]] = {}
        for row in cur.fetchall():
            by_question.setdefault(row["question_id"], []).append(row)
        for q_attempts in by_question.values():
            for idx, att in enumerate(q_attempts):
                if att["is_correct"]:
                    coef = COEFFICIENTS[idx]
                    total += int(100 * coef)
                    break
        scoreboard.append({"user": u["name"], "points": total})
    return scoreboard


async def broadcast_scoreboard(group_id: int):
    """Envia la tabla de puntajes a todos los listeners del grupo."""
    conn = get_db()
    scoreboard = compute_scoreboard(conn, group_id)
    conn.close()
    data = json.dumps(scoreboard)
    queues = listeners.get(group_id, [])
    for q in queues:
        await q.put(data)


@app.get("/questions/{question_id}")
async def get_question(question_id: int):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT id, text, correct_option FROM Question WHERE id=?", (question_id,))
    row = cur.fetchone()
    conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="Pregunta no encontrada")
    options = QUESTION_OPTIONS.get(question_id, [])
    return {"id": row["id"], "text": row["text"], "options": options}


@app.post("/attempts")
async def attempt(request: Request):
    data = await request.json()
    user_name = data.get("user_name")
    group_id = data.get("group_id")
    question_id = data.get("question_id")
    option = data.get("option")
    if not user_name or group_id is None or question_id is None or option is None:
        raise HTTPException(status_code=400, detail="Datos incompletos")

    conn = get_db()
    user_id = ensure_user(conn, user_name, group_id)
    cur = conn.cursor()
    cur.execute("SELECT correct_option FROM Question WHERE id=?", (question_id,))
    q = cur.fetchone()
    if not q:
        conn.close()
        raise HTTPException(status_code=404, detail="Pregunta no encontrada")

    cur.execute(
        "SELECT COUNT(*) FROM Attempt WHERE user_id=? AND question_id=?",
        (user_id, question_id),
    )
    prev_attempts = cur.fetchone()[0]
    if prev_attempts >= MAX_ATTEMPTS:
        conn.close()
        raise HTTPException(status_code=400, detail="Maximo de intentos alcanzado")

    correct = option == q["correct_option"]
    coef = COEFFICIENTS[prev_attempts]
    gained_points = int(100 * coef) if correct else 0
    cur.execute(
        """INSERT INTO Attempt(user_id, question_id, option, is_correct, created_at)
           VALUES (?,?,?,?,?)""",
        (user_id, question_id, option, int(correct), datetime.utcnow().isoformat()),
    )
    conn.commit()

    # determinar grupo del usuario para notificar
    cur.execute('SELECT group_id FROM "User" WHERE id=?', (user_id,))
    user_row = cur.fetchone()
    group_id = user_row["group_id"] if user_row else None
    conn.close()

    if group_id:
        await broadcast_scoreboard(group_id)

    attempts_left = MAX_ATTEMPTS - prev_attempts - 1
    return JSONResponse(
        {
            "correct": correct,
            "gained_points": gained_points,
            "attempts_left": attempts_left,
            "option": option,
        }
    )


@app.get("/events/group/{group_id}")
async def scoreboard_events(group_id: int):
    """Endpoint SSE para enviar la tabla de puntajes del grupo."""
    queue: asyncio.Queue = asyncio.Queue()
    listeners.setdefault(group_id, []).append(queue)

    async def event_generator():
        try:
            await broadcast_scoreboard(group_id)
            while True:
                try:
                    data = await asyncio.wait_for(queue.get(), timeout=15)
                    yield {"event": "scoreboard", "data": data}
                except asyncio.TimeoutError:
                    yield {"event": "ping", "data": "keep"}
        finally:
            listeners[group_id].remove(queue)

    return EventSourceResponse(event_generator())


# Ruta principal para SPA
@app.get("/")
async def root():
    """Devuelve la pagina principal de la SPA."""
    return FileResponse("static/index.html")
