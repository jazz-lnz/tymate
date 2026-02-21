import sqlite3
import unittest
from datetime import date
from unittest.mock import patch

from managers.schedule_manager import ScheduleManager


class InMemoryDB:
    """Minimal DB adapter matching the methods used by ScheduleManager."""

    def __init__(self):
        self.connection = sqlite3.connect(":memory:")
        self.connection.row_factory = sqlite3.Row
        self._create_schema()

    def _create_schema(self):
        cursor = self.connection.cursor()
        cursor.execute(
            """
            CREATE TABLE users (
                id INTEGER PRIMARY KEY,
                wake_time TEXT DEFAULT '07:00',
                sleep_hours REAL DEFAULT 8.0
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE class_schedule (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                day_of_week INTEGER NOT NULL,
                start_time TEXT NOT NULL,
                end_time TEXT NOT NULL,
                course_name TEXT,
                location TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )
        self.connection.commit()

    def insert(self, table: str, data: dict) -> int:
        columns = ", ".join(data.keys())
        placeholders = ", ".join(["?" for _ in data])
        query = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"
        cursor = self.connection.cursor()
        cursor.execute(query, tuple(data.values()))
        self.connection.commit()
        return cursor.lastrowid

    def fetch_all(self, query: str, params: tuple = ()):
        cursor = self.connection.cursor()
        cursor.execute(query, params)
        return [dict(row) for row in cursor.fetchall()]

    def fetch_one(self, query: str, params: tuple = ()):
        cursor = self.connection.cursor()
        cursor.execute(query, params)
        row = cursor.fetchone()
        return dict(row) if row else None

    def delete(self, table: str, where: str, where_params: tuple = ()) -> int:
        query = f"DELETE FROM {table} WHERE {where}"
        cursor = self.connection.cursor()
        cursor.execute(query, where_params)
        self.connection.commit()
        return cursor.rowcount


class TestScheduleManager(unittest.TestCase):
    def setUp(self):
        self.db = InMemoryDB()
        self.patcher = patch("managers.schedule_manager.get_database", return_value=self.db)
        self.patcher.start()
        self.manager = ScheduleManager()

        self.db.insert(
            "users",
            {
                "id": 1,
                "wake_time": "07:00",
                "sleep_hours": 8.0,
            },
        )

    def tearDown(self):
        self.patcher.stop()
        self.db.connection.close()

    def test_add_and_get_classes_normalizes_to_hh_mm(self):
        ok, msg, block_id = self.manager.add_class_block(
            user_id=1,
            day_of_week=0,
            start_time="09:00:00",
            end_time="10:30:00",
            course_name="Math",
        )

        self.assertTrue(ok, msg)
        self.assertIsNotNone(block_id)

        blocks = self.manager.get_classes_for_day(1, 0)
        self.assertEqual(len(blocks), 1)
        self.assertEqual(blocks[0]["start_time"], "09:00")
        self.assertEqual(blocks[0]["end_time"], "10:30")

    def test_add_class_block_rejects_overnight_block(self):
        with self.assertRaises(ValueError):
            self.manager.add_class_block(
                user_id=1,
                day_of_week=0,
                start_time="21:00",
                end_time="08:00",
                course_name="Overnight",
            )

    def test_add_class_block_rejects_zero_duration(self):
        with self.assertRaises(ValueError):
            self.manager.add_class_block(
                user_id=1,
                day_of_week=0,
                start_time="09:00",
                end_time="09:00",
                course_name="Zero",
            )

    def test_compute_free_time_today_single_block(self):
        self.manager.add_class_block(
            user_id=1,
            day_of_week=0,
            start_time="09:00",
            end_time="10:30",
            course_name="Physics",
        )

        # Awake minutes = (24-8)*60 = 960
        # Class minutes = 90
        # Buffer = 90
        # Free = 780
        free_minutes = self.manager.compute_free_time_today(1, date(2026, 2, 23))  # Monday
        self.assertEqual(free_minutes, 780)

    def test_compute_free_time_today_merges_overlaps(self):
        self.manager.add_class_block(
            user_id=1,
            day_of_week=0,
            start_time="09:00",
            end_time="10:30",
            course_name="Block A",
        )
        self.manager.add_class_block(
            user_id=1,
            day_of_week=0,
            start_time="10:00",
            end_time="11:00",
            course_name="Block B",
        )

        # Merged class interval is 09:00-11:00 = 120 minutes (not 150)
        # Free = 960 - 120 - 90 = 750
        free_minutes = self.manager.compute_free_time_today(1, date(2026, 2, 23))
        self.assertEqual(free_minutes, 750)

    def test_delete_class_block_removes_block(self):
        ok, msg, block_id = self.manager.add_class_block(
            user_id=1,
            day_of_week=2,
            start_time="13:00",
            end_time="14:00",
            course_name="Chem",
        )
        self.assertTrue(ok, msg)
        self.assertIsNotNone(block_id)

        ok, msg = self.manager.delete_class_block(block_id)
        self.assertTrue(ok, msg)

        blocks = self.manager.get_classes_for_day(1, 2)
        self.assertEqual(blocks, [])


if __name__ == "__main__":
    unittest.main()
