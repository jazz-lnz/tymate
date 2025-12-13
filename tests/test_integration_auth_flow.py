import os
import shutil
import tempfile
import unittest
from datetime import datetime

from state.auth_manager import AuthManager
from state.task_manager import TaskManager
from storage import sqlite


class AuthFlowIntegrationTest(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp(prefix="tymate_test_")
        self.db_path = os.path.join(self.tmpdir, "tymate.db")
        os.environ["TYMATE_DB_PATH"] = self.db_path
        sqlite._db_instance = None  # reset singleton for isolated DB
        self.auth = AuthManager()
        self.task_manager = TaskManager()

    def tearDown(self):
        try:
            if hasattr(self.auth, "db") and self.auth.db:
                self.auth.db.close()
        finally:
            sqlite._db_instance = None
            shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_register_and_login_flow(self):
        """Test user registration and login workflow"""
        ok, msg, user = self.auth.register_user(
            username="flowuser",
            password="flowpass123",
            email="flow@example.com",
            full_name="Flow User",
        )
        self.assertTrue(ok, msg)
        self.assertIsNotNone(user.id)

        ok, msg, user, token = self.auth.login("flowuser", "flowpass123")
        self.assertTrue(ok, msg)
        self.assertIsNotNone(token)

        session_user = self.auth.get_user_by_session(token)
        self.assertIsNotNone(session_user)
        self.assertEqual(session_user.username, "flowuser")

    def test_account_lockout_after_failures(self):
        """Test account lockout after max failed login attempts"""
        ok, msg, user = self.auth.register_user(username="lockme", password="lockpass123")
        self.assertTrue(ok, msg)

        for i in range(self.auth.MAX_FAILED_ATTEMPTS):
            ok, msg, _, _ = self.auth.login("lockme", "wrongpass")
            self.assertFalse(ok)
            if i < self.auth.MAX_FAILED_ATTEMPTS - 1:
                self.assertIn("Invalid password", msg)
            else:
                self.assertIn("locked", msg.lower())

        ok, msg, _, _ = self.auth.login("lockme", "lockpass123")
        self.assertFalse(ok)
        self.assertIn("locked", msg.lower())

    def test_task_creation_and_lifecycle(self):
        """Test task creation, status updates, and completion workflow"""
        # Register and login user
        ok, msg, user = self.auth.register_user(
            username="taskuser",
            password="taskpass123",
            email="task@example.com",
        )
        self.assertTrue(ok, msg)
        user_id = user.id

        ok, msg, user, token = self.auth.login("taskuser", "taskpass123")
        self.assertTrue(ok, msg)

        # Create task
        ok, msg, task = self.task_manager.create_task(
            user_id=user_id,
            title="Complete Project",
            source="CS 319",
            category="School",
            date_given="2025-12-05",
            date_due="2025-12-20",
            estimated_time=10.0,
        )
        self.assertTrue(ok, f"Task creation failed: {msg}")
        self.assertIsNotNone(task)
        task_id = task.id

        # Verify task was created
        task = self.task_manager.get_task(task_id)
        self.assertIsNotNone(task)
        self.assertEqual(task.title, "Complete Project")
        self.assertEqual(task.status, "Not Started")
        self.assertEqual(task.estimated_time, 10.0)

        # Update task status to In Progress
        ok, msg = self.task_manager.update_task(task_id, status="In Progress")
        self.assertTrue(ok)

        task = self.task_manager.get_task(task_id)
        self.assertEqual(task.status, "In Progress")

        # Mark task as completed with actual time
        ok, msg = self.task_manager.mark_complete(task_id, actual_time=8.0)
        self.assertTrue(ok)

        task = self.task_manager.get_task(task_id)
        self.assertEqual(task.status, "Completed")

        # Verify user can view all their tasks
        user_tasks = self.task_manager.get_user_tasks(user_id)
        self.assertGreaterEqual(len(user_tasks), 1)
        task_titles = [t.title for t in user_tasks]
        self.assertIn("Complete Project", task_titles)

        # Verify task stats
        stats = self.task_manager.get_task_stats(user_id)
        self.assertEqual(stats["total"], 1)
        self.assertEqual(stats["completed"], 1)


if __name__ == "__main__":
    unittest.main()
