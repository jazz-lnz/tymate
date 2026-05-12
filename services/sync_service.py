"""
services/sync_service.py

Client-side sync service for Tymate.
Handles push/pull with the Azure sync server.
Call sync_service.push() after any write, sync_service.pull() on app open.
"""

import json
import os
import requests
from datetime import datetime
from typing import Optional
from storage.sqlite import get_database

SYNC_SERVER_URL = os.getenv("TYMATE_SYNC_URL", "")  # e.g. https://tymate-sync.azurewebsites.net
_token: Optional[str] = None
_user_id: Optional[int] = None


# ==================== Auth ====================

def set_auth(token: str, user_id: int):
    """Call this right after login/register with the server token."""
    global _token, _user_id
    _token = token
    _user_id = user_id


def clear_auth():
    global _token, _user_id
    _token = None
    _user_id = None


def is_authenticated() -> bool:
    return bool(_token and _user_id and SYNC_SERVER_URL)


def _headers() -> dict:
    return {"Authorization": f"Bearer {_token}", "Content-Type": "application/json"}


# ==================== Server Auth ====================

def register_on_server(username: str, password: str, email: str = None, full_name: str = None) -> tuple[bool, str, dict]:
    """Register a new account on the sync server."""
    if not SYNC_SERVER_URL:
        return False, "Sync server not configured", {}
    try:
        resp = requests.post(f"{SYNC_SERVER_URL}/auth/register", json={
            "username": username,
            "password": password,
            "email": email,
            "full_name": full_name,
        }, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            set_auth(data["token"], data["user_id"])
            _save_sync_token(data["token"], data["user_id"])
            return True, "Registered successfully", data
        return False, resp.json().get("detail", "Registration failed"), {}
    except requests.exceptions.ConnectionError:
        return False, "Could not reach sync server — working offline", {}
    except Exception as e:
        return False, str(e), {}


def login_on_server(username: str, password: str) -> tuple[bool, str, dict]:
    """Login against the sync server and get a JWT."""
    if not SYNC_SERVER_URL:
        return False, "Sync server not configured", {}
    try:
        resp = requests.post(f"{SYNC_SERVER_URL}/auth/login", json={
            "username": username,
            "password": password,
        }, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            set_auth(data["token"], data["user_id"])
            _save_sync_token(data["token"], data["user_id"])
            return True, "Logged in", data
        return False, resp.json().get("detail", "Login failed"), {}
    except requests.exceptions.ConnectionError:
        return False, "Could not reach sync server — working offline", {}
    except Exception as e:
        return False, str(e), {}


# ==================== Push ====================

def push(user_id: int) -> tuple[bool, str]:
    """
    Push all unsynced local operations to the server.
    Call this after any task write (create/update/delete).
    Silently succeeds if offline — items stay in sync_queue.
    """
    if not is_authenticated():
        return False, "Not authenticated or sync not configured"

    db = get_database()
    pending = db.fetch_all(
        "SELECT * FROM sync_queue WHERE user_id = ? AND synced = 0 ORDER BY timestamp ASC",
        (user_id,)
    )

    if not pending:
        return True, "Nothing to push"

    operations = [
        {
            "operation_type": op["operation_type"],
            "table_name": op["table_name"],
            "record_id": op["record_id"],
            "data": op["data"],
            "timestamp": op["timestamp"],
        }
        for op in pending
    ]

    try:
        resp = requests.post(
            f"{SYNC_SERVER_URL}/sync/push",
            json={"operations": operations},
            headers=_headers(),
            timeout=15,
        )

        if resp.status_code == 200:
            # Mark all as synced
            ids = tuple(op["id"] for op in pending)
            placeholders = ",".join("?" * len(ids))
            db.execute_query(
                f"UPDATE sync_queue SET synced = 1, synced_at = ? WHERE id IN ({placeholders})",
                (datetime.now().isoformat(), *ids)
            )
            db.commit()
            result = resp.json()
            return True, f"Pushed {result.get('applied', 0)} operations"
        else:
            return False, f"Server error: {resp.status_code}"

    except requests.exceptions.ConnectionError:
        return False, "Offline — will sync when connected"
    except Exception as e:
        return False, str(e)


# ==================== Pull ====================

def pull(user_id: int) -> tuple[bool, str]:
    """
    Pull latest data from server and merge into local SQLite.
    Call this on app open / after login.
    Last-write-wins: server data overwrites local for same records.
    """
    if not is_authenticated():
        return False, "Not authenticated or sync not configured"

    db = get_database()
    last_synced = _get_last_synced_at(user_id)

    try:
        params = {}
        if last_synced:
            params["last_synced_at"] = last_synced

        resp = requests.get(
            f"{SYNC_SERVER_URL}/sync/pull",
            params=params,
            headers=_headers(),
            timeout=15,
        )

        if resp.status_code != 200:
            return False, f"Server error: {resp.status_code}"

        data = resp.json()
        _merge_tasks(db, data.get("tasks", []), user_id)
        _merge_sessions(db, data.get("task_sessions", []), user_id)
        _merge_events(db, data.get("task_events", []), user_id)
        _merge_users(db, data.get("users", []), user_id)
        _merge_settings(db, data.get("settings", []), user_id)

        synced_at = data.get("synced_at", datetime.now().isoformat())
        _save_last_synced_at(user_id, synced_at)

        total = len(data["tasks"]) + len(data["task_sessions"]) + len(data["task_events"])
        return True, f"Pulled {total} records from server"

    except requests.exceptions.ConnectionError:
        return False, "Offline — using local data"
    except Exception as e:
        return False, str(e)


# ==================== Queue Helper ====================

def enqueue(user_id: int, operation_type: str, table_name: str, record_id: int, record_data: dict):
    """
    Add an operation to the sync_queue.
    Call this from task_manager.py after every write.
    """
    db = get_database()
    db.insert("sync_queue", {
        "user_id": user_id,
        "operation_type": operation_type,
        "table_name": table_name,
        "record_id": record_id,
        "data": json.dumps(record_data, default=str),
        "timestamp": datetime.now().isoformat(),
        "synced": 0,
    })


# ==================== Merge Helpers ====================

def _merge_tasks(db, tasks: list, user_id: int):
    for task in tasks:
        client_id = task.get("client_id")
        if client_id:
            existing = db.fetch_one(
                "SELECT id, updated_at FROM tasks WHERE id = ? AND user_id = ?",
                (client_id, user_id)
            )
            if existing:
                # Only overwrite if server record is newer
                if task.get("updated_at", "") >= existing.get("updated_at", ""):
                    task_data = {k: v for k, v in task.items() if k not in ("id", "client_id")}
                    task_data["user_id"] = user_id
                    db.update("tasks", task_data, "id = ? AND user_id = ?", (client_id, user_id))
            else:
                # Insert with the original local id preserved
                task_data = {k: v for k, v in task.items() if k != "client_id"}
                task_data["id"] = client_id
                task_data["user_id"] = user_id
                try:
                    db.execute_query(
                        f"INSERT OR IGNORE INTO tasks ({','.join(task_data.keys())}) VALUES ({','.join(['?']*len(task_data))})",
                        tuple(task_data.values())
                    )
                    db.commit()
                except Exception:
                    pass


def _merge_sessions(db, sessions: list, user_id: int):
    for session in sessions:
        client_id = session.get("client_id")
        if not client_id:
            continue
        existing = db.fetch_one(
            "SELECT id FROM task_sessions WHERE id = ? AND user_id = ?",
            (client_id, user_id)
        )
        if not existing:
            session_data = {k: v for k, v in session.items() if k not in ("client_id", "task_client_id")}
            session_data["id"] = client_id
            session_data["user_id"] = user_id
            session_data["task_id"] = session.get("task_client_id")
            try:
                db.execute_query(
                    f"INSERT OR IGNORE INTO task_sessions ({','.join(session_data.keys())}) VALUES ({','.join(['?']*len(session_data))})",
                    tuple(session_data.values())
                )
                db.commit()
            except Exception:
                pass


def _merge_events(db, events: list, user_id: int):
    for event in events:
        client_id = event.get("client_id")
        if not client_id:
            continue
        existing = db.fetch_one(
            "SELECT id FROM task_events WHERE id = ? AND user_id = ?",
            (client_id, user_id)
        )
        if not existing:
            event_data = {k: v for k, v in event.items() if k not in ("client_id", "task_client_id")}
            event_data["id"] = client_id
            event_data["user_id"] = user_id
            event_data["task_id"] = event.get("task_client_id")
            try:
                db.execute_query(
                    f"INSERT OR IGNORE INTO task_events ({','.join(event_data.keys())}) VALUES ({','.join(['?']*len(event_data))})",
                    tuple(event_data.values())
                )
                db.commit()
            except Exception:
                pass


def _merge_users(db, users: list, user_id: int):
    """
    Merge user profile updates from server into local users table.
    Only merges records for the current user (safety).
    """
    for user in users:
        client_id = user.get("client_id") or user.get("id")
        if not client_id:
            continue
        # Only merge the currently authenticated user's profile
        try:
            if int(client_id) != int(user_id):
                continue
        except Exception:
            continue

        existing = db.fetch_one(
            "SELECT id, updated_at FROM users WHERE id = ?",
            (client_id,)
        )

        # Strip sensitive fields before applying
        user_data = {k: v for k, v in user.items() if k not in ("id", "client_id", "password_hash")}
        user_data["id"] = client_id

        if existing:
            # Only overwrite if server record is newer
            if user.get("updated_at", "") >= existing.get("updated_at", ""):
                try:
                    db.update("users", user_data, "id = ?", (client_id,))
                except Exception:
                    pass
        else:
            try:
                db.execute_query(
                    f"INSERT OR IGNORE INTO users ({','.join(user_data.keys())}) VALUES ({','.join(['?']*len(user_data))})",
                    tuple(user_data.values()),
                )
                db.commit()
            except Exception:
                pass


def _merge_settings(db, settings: list, user_id: int):
    """Merge settings records from server into local `settings` table."""
    for s in settings:
        try:
            key = s.get("setting_key") or s.get("key")
            val = s.get("setting_value") or s.get("value")
            updated_at = s.get("updated_at") or datetime.now().isoformat()
            if not key:
                continue
            db.execute_query(
                "INSERT OR REPLACE INTO settings (user_id, setting_key, setting_value, updated_at) VALUES (?, ?, ?, ?)",
                (user_id, key, val, updated_at),
            )
        except Exception:
            pass
    try:
        db.commit()
    except Exception:
        pass


# ==================== Persistence Helpers ====================

def _save_sync_token(token: str, user_id: int):
    db = get_database()
    db.execute_query(
        "INSERT OR REPLACE INTO settings (user_id, setting_key, setting_value, updated_at) VALUES (?, ?, ?, ?)",
        (user_id, "sync_token", token, datetime.now().isoformat())
    )
    db.commit()


def _get_last_synced_at(user_id: int) -> Optional[str]:
    db = get_database()
    row = db.fetch_one(
        "SELECT setting_value FROM settings WHERE user_id = ? AND setting_key = 'last_synced_at'",
        (user_id,)
    )
    return row["setting_value"] if row else None


def _save_last_synced_at(user_id: int, synced_at: str):
    db = get_database()
    db.execute_query(
        "INSERT OR REPLACE INTO settings (user_id, setting_key, setting_value, updated_at) VALUES (?, ?, ?, ?)",
        (user_id, "last_synced_at", synced_at, datetime.now().isoformat())
    )
    db.commit()


def load_token_from_db(user_id: int):
    """On app restart, reload token from local settings so user stays logged in."""
    db = get_database()
    row = db.fetch_one(
        "SELECT setting_value FROM settings WHERE user_id = ? AND setting_key = 'sync_token'",
        (user_id,)
    )
    if row:
        set_auth(row["setting_value"], user_id)