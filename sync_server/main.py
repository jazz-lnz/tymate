"""
Tymate Sync Server — FastAPI
Handles shared auth and task sync across devices via Azure PostgreSQL.
"""

from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Any
from datetime import datetime, timedelta
import psycopg2
import psycopg2.extras
import bcrypt
import jwt
import json
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="Tymate Sync Server", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DATABASE_URL = os.getenv("DATABASE_URL")  # Azure PostgreSQL connection string
JWT_SECRET = os.getenv("JWT_SECRET", "change-this-in-production")
JWT_EXPIRY_DAYS = 30


# ==================== DB ====================

def get_db():
    conn = psycopg2.connect(DATABASE_URL)
    conn.autocommit = False
    try:
        yield conn
    finally:
        conn.close()


def init_db():
    """Create tables on startup if they don't exist."""
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'user',
            full_name TEXT,
            sleep_hours REAL DEFAULT 8.0,
            wake_time TEXT DEFAULT '07:00',
            has_work INTEGER DEFAULT 0,
            work_hours_per_week REAL DEFAULT 0.0,
            work_days_per_week INTEGER DEFAULT 0,
            study_goal_hours_per_day REAL DEFAULT 0.0,
            is_active INTEGER DEFAULT 1,
            is_locked INTEGER DEFAULT 0,
            failed_login_attempts INTEGER DEFAULT 0,
            locked_at TEXT,
            last_login TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id SERIAL PRIMARY KEY,
            client_id INTEGER,
            user_id INTEGER NOT NULL REFERENCES users(id),
            title TEXT NOT NULL,
            source TEXT NOT NULL,
            category TEXT NOT NULL,
            date_given TEXT NOT NULL,
            date_due TEXT,
            description TEXT,
            estimated_time INTEGER,
            status TEXT DEFAULT 'Not Started',
            is_recurring INTEGER DEFAULT 0,
            recurrence_type TEXT,
            recurrence_interval INTEGER DEFAULT 1,
            recurrence_until TEXT,
            completed_at TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            is_deleted INTEGER DEFAULT 0,
            deleted_at TEXT
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS task_sessions (
            id SERIAL PRIMARY KEY,
            client_id INTEGER,
            user_id INTEGER NOT NULL REFERENCES users(id),
            task_client_id INTEGER,
            duration_minutes INTEGER NOT NULL,
            notes TEXT,
            logged_at TEXT,
            created_at TEXT NOT NULL,
            is_deleted INTEGER DEFAULT 0,
            deleted_at TEXT
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS task_events (
            id SERIAL PRIMARY KEY,
            client_id INTEGER,
            user_id INTEGER NOT NULL REFERENCES users(id),
            task_client_id INTEGER,
            event_type TEXT NOT NULL,
            message TEXT,
            metadata TEXT,
            created_at TEXT NOT NULL
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL REFERENCES users(id),
            setting_key TEXT NOT NULL,
            setting_value TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            UNIQUE(user_id, setting_key)
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS sync_log (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL REFERENCES users(id),
            synced_at TEXT NOT NULL
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS class_schedule (
            id SERIAL PRIMARY KEY,
            client_id INTEGER,
            user_id INTEGER NOT NULL REFERENCES users(id),
            day_of_week INTEGER NOT NULL,
            start_time TEXT NOT NULL,
            end_time TEXT NOT NULL,
            course_name TEXT,
            location TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            is_deleted INTEGER DEFAULT 0,
            deleted_at TEXT
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS work_schedule (
            id SERIAL PRIMARY KEY,
            client_id INTEGER,
            user_id INTEGER NOT NULL REFERENCES users(id),
            schedule_type TEXT NOT NULL,
            day_of_week INTEGER,
            start_time TEXT,
            end_time TEXT,
            weekly_hours_target REAL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            is_deleted INTEGER DEFAULT 0,
            deleted_at TEXT
        )
    """)

    conn.commit()
    cur.close()
    conn.close()


@app.on_event("startup")
def startup():
    init_db()


# ==================== AUTH MODELS ====================

class RegisterRequest(BaseModel):
    username: str
    password: str
    email: Optional[str] = None
    full_name: Optional[str] = None

class LoginRequest(BaseModel):
    username: str
    password: str

class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str

class AuthResponse(BaseModel):
    token: str
    user_id: int
    username: str
    full_name: Optional[str]


# ==================== SYNC MODELS ====================

class SyncOperation(BaseModel):
    operation_type: str          # INSERT, UPDATE, DELETE
    table_name: str              # tasks, task_sessions, task_events
    record_id: Optional[int]     # client-side local ID
    data: str                    # JSON string of the record
    timestamp: str

class PushRequest(BaseModel):
    operations: List[SyncOperation]
    last_synced_at: Optional[str] = None

class PullResponse(BaseModel):
    users: List[dict]
    tasks: List[dict]
    task_sessions: List[dict]
    task_events: List[dict]
    settings: List[dict] = []
    class_schedule: List[dict] = []
    work_schedule: List[dict] = []
    synced_at: str


# ==================== AUTH HELPERS ====================

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode(), hashed.encode())

def create_token(user_id: int, username: str) -> str:
    payload = {
        "user_id": user_id,
        "username": username,
        "exp": datetime.utcnow() + timedelta(days=JWT_EXPIRY_DAYS)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm="HS256")

def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

def get_current_user(authorization: str = Header(...)):
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid auth header")
    token = authorization[7:]
    return decode_token(token)


# ==================== AUTH ROUTES ====================

@app.post("/auth/register", response_model=AuthResponse)
def register(req: RegisterRequest, conn=Depends(get_db)):
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    now = datetime.now().isoformat()

    cur.execute("SELECT id FROM users WHERE username = %s", (req.username,))
    if cur.fetchone():
        raise HTTPException(status_code=409, detail="Username already taken")

    cur.execute("""
        INSERT INTO users (username, email, password_hash, full_name, created_at, updated_at)
        VALUES (%s, %s, %s, %s, %s, %s) RETURNING id
    """, (req.username, req.email, hash_password(req.password), req.full_name, now, now))

    user_id = cur.fetchone()["id"]
    conn.commit()

    return AuthResponse(
        token=create_token(user_id, req.username),
        user_id=user_id,
        username=req.username,
        full_name=req.full_name
    )


@app.post("/auth/login", response_model=AuthResponse)
def login(req: LoginRequest, conn=Depends(get_db)):
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    cur.execute("SELECT * FROM users WHERE username = %s", (req.username,))
    user = cur.fetchone()

    if not user or not verify_password(req.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid username or password")

    if user["is_locked"]:
        raise HTTPException(status_code=403, detail="Account is locked")

    cur.execute("UPDATE users SET last_login = %s WHERE id = %s",
                (datetime.now().isoformat(), user["id"]))
    conn.commit()

    return AuthResponse(
        token=create_token(user["id"], user["username"]),
        user_id=user["id"],
        username=user["username"],
        full_name=user.get("full_name")
    )


@app.post("/auth/change-password")
def change_password(req: ChangePasswordRequest, user=Depends(get_current_user), conn=Depends(get_db)):
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("SELECT id, password_hash FROM users WHERE id = %s", (user["user_id"],))
    current_user = cur.fetchone()
    if not current_user:
        raise HTTPException(status_code=404, detail="User not found")

    if not verify_password(req.old_password, current_user["password_hash"]):
        raise HTTPException(status_code=401, detail="Current password is incorrect")

    cur.execute(
        "UPDATE users SET password_hash = %s, updated_at = %s WHERE id = %s",
        (hash_password(req.new_password), datetime.now().isoformat(), user["user_id"]),
    )
    conn.commit()
    return {"detail": "Password changed successfully"}


# ==================== SYNC ROUTES ====================

@app.post("/sync/push")
def push(req: PushRequest, user=Depends(get_current_user), conn=Depends(get_db)):
    """
    Client sends unsynced operations. Server applies them to PostgreSQL.
    Uses client_id to avoid duplicates on re-push.
    """
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    user_id = user["user_id"]
    applied = 0

    for op in req.operations:
        try:
            data = json.loads(op.data)
            table = op.table_name

            if table == "tasks":
                _apply_task_op(cur, op.operation_type, data, user_id)
            elif table == "task_sessions":
                _apply_session_op(cur, op.operation_type, data, user_id)
            elif table == "task_events":
                _apply_event_op(cur, op.operation_type, data, user_id)
            elif table == "class_schedule":
                _apply_schedule_op(cur, op.operation_type, data, user_id, table_name="class_schedule")
            elif table == "work_schedule":
                _apply_schedule_op(cur, op.operation_type, data, user_id, table_name="work_schedule")
            elif table == "users":
                _apply_user_op(cur, op.operation_type, data, user_id)
            elif table == "settings":
                _apply_setting_op(cur, op.operation_type, data, user_id)

            applied += 1
        except Exception as e:
            # Log and continue — don't let one bad op block the rest
            print(f"[PUSH] Error applying op {op.operation_type} on {op.table_name}: {e}")
            continue

    conn.commit()
    return {"applied": applied, "total": len(req.operations)}


@app.get("/sync/pull", response_model=PullResponse)
def pull(last_synced_at: Optional[str] = None, user=Depends(get_current_user), conn=Depends(get_db)):
    """
    Returns all user records updated since last_synced_at.
    If no timestamp, returns everything (first sync).
    """
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    user_id = user["user_id"]
    since = last_synced_at or "1970-01-01T00:00:00"

    cur.execute("""
        SELECT * FROM users WHERE id = %s
    """, (user_id,))
    users = [dict(r) for r in cur.fetchall()]

    cur.execute("""
        SELECT * FROM tasks WHERE user_id = %s AND updated_at > %s
    """, (user_id, since))
    tasks = [dict(r) for r in cur.fetchall()]

    cur.execute("""
        SELECT * FROM task_sessions WHERE user_id = %s AND created_at > %s
    """, (user_id, since))
    sessions = [dict(r) for r in cur.fetchall()]

    cur.execute("""
        SELECT * FROM task_events WHERE user_id = %s AND created_at > %s
    """, (user_id, since))
    events = [dict(r) for r in cur.fetchall()]

    cur.execute("""
        SELECT * FROM settings WHERE user_id = %s AND updated_at > %s
    """, (user_id, since))
    settings = [dict(r) for r in cur.fetchall()]

    cur.execute("""
        SELECT * FROM class_schedule WHERE user_id = %s AND updated_at > %s
    """, (user_id, since))
    class_schedule = [dict(r) for r in cur.fetchall()]

    cur.execute("""
        SELECT * FROM work_schedule WHERE user_id = %s AND updated_at > %s
    """, (user_id, since))
    work_schedule = [dict(r) for r in cur.fetchall()]

    return PullResponse(
        users=users,
        tasks=tasks,
        task_sessions=sessions,
        task_events=events,
        settings=settings,
        class_schedule=class_schedule,
        work_schedule=work_schedule,
        synced_at=datetime.now().isoformat()
    )


@app.get("/health")
def health():
    return {"status": "ok", "service": "Tymate Sync Server"}


# ==================== OPERATION APPLIERS ====================

def _apply_task_op(cur, op_type: str, data: dict, user_id: int):
    client_id = data.get("id")
    data["user_id"] = user_id  # enforce ownership

    if op_type == "INSERT":
        cur.execute("SELECT id FROM tasks WHERE client_id = %s AND user_id = %s",
                    (client_id, user_id))
        if cur.fetchone():
            return  # already synced, skip

        cur.execute("""
            INSERT INTO tasks (client_id, user_id, title, source, category, date_given, date_due,
                description, estimated_time, status, is_recurring, recurrence_type,
                recurrence_interval, recurrence_until, completed_at, created_at, updated_at,
                is_deleted, deleted_at)
            VALUES (%(client_id)s, %(user_id)s, %(title)s, %(source)s, %(category)s,
                %(date_given)s, %(date_due)s, %(description)s, %(estimated_time)s,
                %(status)s, %(is_recurring)s, %(recurrence_type)s, %(recurrence_interval)s,
                %(recurrence_until)s, %(completed_at)s, %(created_at)s, %(updated_at)s,
                %(is_deleted)s, %(deleted_at)s)
        """, {**data, "client_id": client_id})

    elif op_type == "UPDATE":
        cur.execute("""
            UPDATE tasks SET
                title=%(title)s, status=%(status)s, description=%(description)s,
                estimated_time=%(estimated_time)s, date_due=%(date_due)s,
                completed_at=%(completed_at)s, updated_at=%(updated_at)s,
                is_deleted=%(is_deleted)s, deleted_at=%(deleted_at)s,
                is_recurring=%(is_recurring)s, recurrence_type=%(recurrence_type)s,
                recurrence_interval=%(recurrence_interval)s, recurrence_until=%(recurrence_until)s
            WHERE client_id=%(client_id)s AND user_id=%(user_id)s
        """, {**data, "client_id": client_id})

    elif op_type == "DELETE":
        cur.execute("UPDATE tasks SET is_deleted=1 WHERE client_id=%s AND user_id=%s",
                    (client_id, user_id))


def _apply_session_op(cur, op_type: str, data: dict, user_id: int):
    client_id = data.get("id")
    if op_type == "INSERT":
        cur.execute("SELECT id FROM task_sessions WHERE client_id=%s AND user_id=%s",
                    (client_id, user_id))
        if cur.fetchone():
            return
        cur.execute("""
            INSERT INTO task_sessions (client_id, user_id, task_client_id, duration_minutes,
                notes, logged_at, created_at, is_deleted)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (client_id, user_id, data.get("task_id"), data.get("duration_minutes"),
              data.get("notes"), data.get("logged_at"), data.get("created_at"),
              data.get("is_deleted", 0)))
    elif op_type == "UPDATE":
        # Update session fields based on client_id
        cur.execute("""
            UPDATE task_sessions SET
                task_client_id=%s, duration_minutes=%s, notes=%s, logged_at=%s, is_deleted=%s, deleted_at=%s
            WHERE client_id=%s AND user_id=%s
        """, (data.get("task_id"), data.get("duration_minutes"), data.get("notes"), data.get("logged_at"),
              data.get("is_deleted", 0), data.get("deleted_at"), client_id, user_id))
    elif op_type == "DELETE":
        cur.execute("""
            UPDATE task_sessions SET is_deleted=1, deleted_at=%s WHERE client_id=%s AND user_id=%s
        """, (data.get("deleted_at") or datetime.now().isoformat(), client_id, user_id))


def _apply_event_op(cur, op_type: str, data: dict, user_id: int):
    client_id = data.get("id")
    if op_type == "INSERT":
        cur.execute("SELECT id FROM task_events WHERE client_id=%s AND user_id=%s",
                    (client_id, user_id))
        if cur.fetchone():
            return
        cur.execute("""
            INSERT INTO task_events (client_id, user_id, task_client_id, event_type,
                message, metadata, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (client_id, user_id, data.get("task_id"), data.get("event_type"),
              data.get("message"), data.get("metadata"), data.get("created_at")))


def _apply_schedule_op(cur, op_type: str, data: dict, user_id: int, table_name: str = "class_schedule"):
    client_id = data.get("id") or data.get("client_id")
    if not client_id:
        return

    if op_type == "INSERT":
        cur.execute(f"SELECT id FROM {table_name} WHERE client_id = %s AND user_id = %s", (client_id, user_id))
        if cur.fetchone():
            return
        if table_name == "class_schedule":
            cur.execute("""
                INSERT INTO class_schedule (client_id, user_id, day_of_week, start_time, end_time, course_name, location, created_at, updated_at, is_deleted)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                client_id, user_id, data.get("day_of_week"), data.get("start_time"), data.get("end_time"),
                data.get("course_name"), data.get("location"), data.get("created_at"), data.get("updated_at"), data.get("is_deleted", 0)
            ))
        else:
            cur.execute("""
                INSERT INTO work_schedule (client_id, user_id, schedule_type, day_of_week, start_time, end_time, weekly_hours_target, created_at, updated_at, is_deleted)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                client_id, user_id, data.get("schedule_type"), data.get("day_of_week"), data.get("start_time"), data.get("end_time"),
                data.get("weekly_hours_target"), data.get("created_at"), data.get("updated_at"), data.get("is_deleted", 0)
            ))

    elif op_type == "UPDATE":
        if table_name == "class_schedule":
            cur.execute("""
                UPDATE class_schedule SET day_of_week=%s, start_time=%s, end_time=%s, course_name=%s, location=%s, updated_at=%s, is_deleted=%s, deleted_at=%s
                WHERE client_id=%s AND user_id=%s
            """, (
                data.get("day_of_week"), data.get("start_time"), data.get("end_time"), data.get("course_name"), data.get("location"),
                data.get("updated_at"), data.get("is_deleted", 0), data.get("deleted_at"), client_id, user_id
            ))
        else:
            cur.execute("""
                UPDATE work_schedule SET schedule_type=%s, day_of_week=%s, start_time=%s, end_time=%s, weekly_hours_target=%s, updated_at=%s, is_deleted=%s, deleted_at=%s
                WHERE client_id=%s AND user_id=%s
            """, (
                data.get("schedule_type"), data.get("day_of_week"), data.get("start_time"), data.get("end_time"), data.get("weekly_hours_target"),
                data.get("updated_at"), data.get("is_deleted", 0), data.get("deleted_at"), client_id, user_id
            ))

    elif op_type == "DELETE":
        # Soft-delete by marking is_deleted and setting deleted_at
        deleted_at = data.get("deleted_at") or datetime.now().isoformat()
        cur.execute(f"UPDATE {table_name} SET is_deleted=1, deleted_at=%s WHERE client_id=%s AND user_id=%s", (deleted_at, client_id, user_id))


def _apply_user_op(cur, op_type: str, data: dict, user_id: int):
    # Only allow updating the authenticated user's profile fields
    if op_type == "UPDATE":
        # Whitelist permissible profile fields that can be synced
        allowed = {"full_name", "email", "profile_photo", "sleep_hours", "wake_time", "has_work", "work_hours_per_week", "work_days_per_week", "study_goal_hours_per_day"}
        updates = {k: data.get(k) for k in allowed if k in data}
        if not updates:
            return
        set_clause = ", ".join([f"{k} = %s" for k in updates.keys()])
        params = list(updates.values()) + [datetime.now().isoformat(), user_id]
        # Ensure updated_at is set
        try:
            cur.execute(f"UPDATE users SET {set_clause}, updated_at = %s WHERE id = %s", tuple(params))
        except Exception:
            pass


def _apply_setting_op(cur, op_type: str, data: dict, user_id: int):
    # Expect data to contain setting_key and setting_value
    key = data.get("setting_key") or data.get("key")
    val = data.get("setting_value") or data.get("value")
    updated_at = data.get("updated_at") or datetime.now().isoformat()
    if not key:
        return
    try:
        cur.execute("INSERT INTO settings (user_id, setting_key, setting_value, updated_at) VALUES (%s, %s, %s, %s) ON CONFLICT (user_id, setting_key) DO UPDATE SET setting_value = EXCLUDED.setting_value, updated_at = EXCLUDED.updated_at", (user_id, key, val, updated_at))
    except Exception:
        pass
