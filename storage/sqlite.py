import sqlite3
import os
from datetime import datetime
from typing import List, Dict, Optional, Any

class Database:
    """ TYMATE SQLite Database Handler """
    
    def __init__(self, db_path: str = "data/tymate.db"):
        """
        Initialize database connection and create tables if needed
        
        Args:
            db_path: Path to SQLite database file
        """
        # Ensure data directory exists
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
        self.db_path = db_path
        self.connection = None
        self.cursor = None
        
        # Connect and initialize tables
        self.connect()
        self.create_tables()
    
    def connect(self):
        """Establish database connection"""
        self.connection = sqlite3.connect(self.db_path, check_same_thread=False)
        self.connection.row_factory = sqlite3.Row  # Enable column access by name
        self.cursor = self.connection.cursor()
    
    def close(self):
        """Close database connection"""
        if self.connection:
            self.connection.close()
    
    def create_tables(self):
        """
        Create all required database tables
        Compliant with CS 319, CSAC 3211, and SRS requirements
        """
        
        # ==================== CS 319: RBAC & User Management ====================
        
        # Users table (CS 319: Authentication, Profile Management)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL DEFAULT 'user',
                full_name TEXT,
                profile_photo TEXT,
                sleep_hours REAL DEFAULT 8.0,
                wake_time TEXT DEFAULT '07:00',
                has_work INTEGER DEFAULT 0,
                work_hours_per_week REAL DEFAULT 0.0,
                work_days_per_week INTEGER DEFAULT 0,
                study_goal_hours_per_day REAL DEFAULT 0.0,
                is_active INTEGER DEFAULT 1,
                is_locked INTEGER DEFAULT 0,
                failed_login_attempts INTEGER DEFAULT 0,
                last_login TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                created_by INTEGER,
                FOREIGN KEY (created_by) REFERENCES users (id)
            )
        """)
        
        # Roles table (CS 319: RBAC)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS roles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                description TEXT,
                permissions TEXT NOT NULL
            )
        """)
        
        # Audit logs table (CS 319: Security Controls, Logging)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS audit_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                username TEXT,
                action TEXT NOT NULL,
                table_name TEXT,
                record_id INTEGER,
                old_value TEXT,
                new_value TEXT,
                ip_address TEXT,
                timestamp TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        """)
        
        # Login attempts table (CS 319: Security Controls)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS login_attempts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                success INTEGER NOT NULL,
                failure_reason TEXT,
                ip_address TEXT,
                timestamp TEXT NOT NULL
            )
        """)
        
        # Sessions table (CS 319: Session Management)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                session_token TEXT UNIQUE NOT NULL,
                created_at TEXT NOT NULL,
                expires_at TEXT NOT NULL,
                last_activity TEXT NOT NULL,
                is_active INTEGER DEFAULT 1,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        """)
        
        # ==================== SRS: Task Management ====================
        
        # Tasks table (FR-001 to FR-005) - Invoice Style
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                source TEXT NOT NULL,
                category TEXT NOT NULL,
                date_given TEXT NOT NULL,
                date_due TEXT NOT NULL,
                description TEXT,
                estimated_time REAL,
                actual_time REAL,
                status TEXT DEFAULT 'Not Started',
                completed_at TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                is_deleted INTEGER DEFAULT 0,
                deleted_at TEXT,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        """)
        
        # Task tags table (FR-005: Tagging)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS task_tags (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id INTEGER NOT NULL,
                tag TEXT NOT NULL,
                FOREIGN KEY (task_id) REFERENCES tasks (id) ON DELETE CASCADE
            )
        """)
        
        # File attachments table (FR-006: Upload Attachments)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS attachments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id INTEGER NOT NULL,
                filename TEXT NOT NULL,
                file_path TEXT NOT NULL,
                file_type TEXT NOT NULL,
                file_size INTEGER,
                extracted_data TEXT,
                uploaded_at TEXT NOT NULL,
                FOREIGN KEY (task_id) REFERENCES tasks (id) ON DELETE CASCADE
            )
        """)
        
        # ==================== SRS: Time Tracking ====================
        
        # Time logs table (FR-010: Work-Hour Logging)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS time_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                task_id INTEGER,
                category TEXT NOT NULL,
                hours REAL NOT NULL,
                date TEXT NOT NULL,
                start_time TEXT,
                end_time TEXT,
                notes TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users (id),
                FOREIGN KEY (task_id) REFERENCES tasks (id)
            )
        """)
        
        # Time budgets table (FR-009: Time Budgeting)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS time_budgets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                category TEXT NOT NULL,
                budget_type TEXT NOT NULL,
                budget_hours REAL NOT NULL,
                start_date TEXT NOT NULL,
                end_date TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        """)
        
        # ==================== SRS: Smart Tips & Analytics ====================
        
        # Smart tips table (FR-012: Smart Tips)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS smart_tips (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                tip_type TEXT NOT NULL,
                tip_message TEXT NOT NULL,
                is_read INTEGER DEFAULT 0,
                created_at TEXT NOT NULL,
                read_at TEXT,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        """)
        
        # ==================== SRS: User Settings ====================
        
        # Settings table (User Preferences)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                setting_key TEXT NOT NULL,
                setting_value TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users (id),
                UNIQUE(user_id, setting_key)
            )
        """)
        
        # ==================== SRS: Offline Sync ====================
        
        # Sync queue table (FR-013: Offline Logging and Synchronization)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS sync_queue (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                operation_type TEXT NOT NULL,
                table_name TEXT NOT NULL,
                record_id INTEGER,
                data TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                synced INTEGER DEFAULT 0,
                synced_at TEXT,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        """)
        
        # ==================== CSAC 3211: Research Data ====================
        
        # Usage analytics table (Research: User behavior tracking)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS usage_analytics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                feature TEXT NOT NULL,
                action TEXT NOT NULL,
                metadata TEXT,
                timestamp TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        """)
        
        self.connection.commit()
        
        # Seed default roles
        self._seed_roles()
    
    def _seed_roles(self):
        """Seed default roles for RBAC (CS 319 requirement)"""
        roles_data = [
            {
                "name": "admin",
                "description": "System administrator with full access",
                "permissions": '["manage_users", "view_all_logs", "system_settings", "export_data", "manage_smart_tips", "view_analytics"]'
            },
            {
                "name": "premium",
                "description": "Premium user with Smart Tips access",
                "permissions": '["create_tasks", "view_analytics", "smart_tips", "file_upload", "unlimited_tasks"]'
            },
            {
                "name": "user",
                "description": "Regular user with basic features",
                "permissions": '["create_tasks", "view_own_analytics", "file_upload"]'
            }
        ]
        
        for role in roles_data:
            self.cursor.execute(
                "INSERT OR IGNORE INTO roles (name, description, permissions) VALUES (?, ?, ?)",
                (role["name"], role["description"], role["permissions"])
            )
        
        self.connection.commit()
    
    # ==================== Basic CRUD Operations ====================
    
    def execute_query(self, query: str, params: tuple = ()) -> sqlite3.Cursor:
        """Execute a SQL query and return cursor"""
        return self.cursor.execute(query, params)
    
    def fetch_one(self, query: str, params: tuple = ()) -> Optional[Dict[str, Any]]:
        """Execute query and fetch one result"""
        self.cursor.execute(query, params)
        row = self.cursor.fetchone()
        return dict(row) if row else None
    
    def fetch_all(self, query: str, params: tuple = ()) -> List[Dict[str, Any]]:
        """Execute query and fetch all results"""
        self.cursor.execute(query, params)
        rows = self.cursor.fetchall()
        return [dict(row) for row in rows]
    
    def insert(self, table: str, data: Dict[str, Any]) -> int:
        """Insert a new record into table"""
        columns = ', '.join(data.keys())
        placeholders = ', '.join(['?' for _ in data])
        query = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"
        
        self.cursor.execute(query, tuple(data.values()))
        self.connection.commit()
        return self.cursor.lastrowid
    
    def update(self, table: str, data: Dict[str, Any], where: str, where_params: tuple = ()) -> int:
        """Update records in table"""
        set_clause = ', '.join([f"{key} = ?" for key in data.keys()])
        query = f"UPDATE {table} SET {set_clause} WHERE {where}"
        
        params = tuple(data.values()) + where_params
        self.cursor.execute(query, params)
        self.connection.commit()
        return self.cursor.rowcount
    
    def delete(self, table: str, where: str, where_params: tuple = ()) -> int:
        """Delete records from table"""
        query = f"DELETE FROM {table} WHERE {where}"
        
        self.cursor.execute(query, where_params)
        self.connection.commit()
        return self.cursor.rowcount
    
    def get_by_id(self, table: str, record_id: int) -> Optional[Dict[str, Any]]:
        """Get a single record by ID"""
        query = f"SELECT * FROM {table} WHERE id = ?"
        return self.fetch_one(query, (record_id,))
    
    def count(self, table: str, where: str = "", where_params: tuple = ()) -> int:
        """Count records in table"""
        query = f"SELECT COUNT(*) as count FROM {table}"
        if where:
            query += f" WHERE {where}"
        
        result = self.fetch_one(query, where_params)
        return result['count'] if result else 0
    
    def commit(self):
        """Commit current transaction"""
        self.connection.commit()
    
    def rollback(self):
        """Rollback current transaction"""
        self.connection.rollback()


# Singleton instance
_db_instance = None

def get_database(db_path: str = "data/tymate.db") -> Database:
    """
    Get singleton database instance
    
    Args:
        db_path: Path to database file
        
    Returns:
        Database instance
    """
    global _db_instance
    if _db_instance is None:
        _db_instance = Database(db_path)
    return _db_instance