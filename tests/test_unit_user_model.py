import unittest
from models.user import User


class TestUserModel(unittest.TestCase):
    def test_validate_password_min_length(self):
        valid, msg = User.validate_password_complexity("12345")
        self.assertFalse(valid)
        self.assertIn("6 characters", msg)

    def test_validate_password_accepts_minimum(self):
        valid, msg = User.validate_password_complexity("123456")
        self.assertTrue(valid)
        self.assertEqual(msg, "Password accepted")

    def test_password_hash_and_verify(self):
        raw = "secret123"
        hashed = User.hash_password(raw)
        user = User(username="tester", password_hash=hashed)
        self.assertTrue(user.verify_password(raw))
        self.assertFalse(user.verify_password("wrong"))

    def test_role_permissions(self):
        admin = User(username="admin", password_hash=User.hash_password("x"), role="admin")
        premium = User(username="premium", password_hash=User.hash_password("x"), role="premium")
        self.assertTrue(admin.has_permission("any-permission"))
        self.assertTrue(premium.has_permission("create_tasks"))
        self.assertFalse(premium.has_permission("manage_users"))


if __name__ == "__main__":
    unittest.main()
