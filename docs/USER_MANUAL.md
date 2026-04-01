# TYMATE User Manual

TYMATE is a time-budgeting and task-tracking application designed to help students and working learners plan realistically around sleep, deadlines, and study goals.

This manual explains how to install, use, and manage TYMATE in day-to-day use.

---

## Table of Contents
1. [Who This Manual Is For](#who-this-manual-is-for)
2. [Roles and Access](#roles-and-access)
3. [Install and Run TYMATE](#install-and-run-tymate)
4. [First Login and Setup](#first-login-and-setup)
5. [Navigation Overview](#navigation-overview)
6. [Regular User Guide](#regular-user-guide)
7. [Admin Guide](#admin-guide)
8. [Account Security and Lockouts](#account-security-and-lockouts)
9. [Troubleshooting](#troubleshooting)
10. [More Documentation](#more-documentation)

---

## Who This Manual Is For

- Students and users who want to manage daily workload with realistic time limits.
- Admin users responsible for maintaining accounts and monitoring activity.
- First-time users who need step-by-step onboarding and task workflows.

---

## Roles and Access

TYMATE supports role-based access.

### Regular Users

Users with the `user` role can:

- Sign in and maintain their own profile.
- Complete onboarding and configure sleep/wake schedule.
- Create, edit, complete, and soft-delete tasks.
- Use Time It to log task sessions.
- View dashboard and personal analytics.
- Change their own password in Settings.

Users cannot access Admin pages.

### Admin Users

Admins can:

- Access Admin, User Activity, and Audit Logs pages.
- Create new users.
- Enable or disable user accounts.
- Unlock locked accounts.
- Reset a user's password from the Admin page.
- Delete users.

Admins do not use the regular task workflow as a primary path.

---

## Install and Run TYMATE

### Prerequisites

- Python 3.8+
- pip
- Terminal or command prompt

### 1. Open the project directory

```bash
cd tymate
```

### 2. Create and activate a virtual environment

```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# Mac/Linux
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Optional: generate sample data

```bash
python tests/generate_sample_db.py
```

This creates demo users and tasks for testing.

### 5. Run the app

```bash
# Desktop-style app
python main.py

# Browser mode
flet run main.py --web
```

---

## First Login and Setup

### If you are a new user

1. Open the Login screen.
2. Switch to Sign Up.
3. Enter username and password (email and full name are optional).
4. Submit registration.
5. Complete onboarding:
   - Set sleep hours.
   - Set wake time.
   - Review computed daily time budget.

### If you are using sample data

If sample data was generated, a default admin account exists.

- Username: `admin`
- Password: `admin123`

Change this password immediately after first login.

---

## Navigation Overview

### Regular User Navigation

- Home (Dashboard)
- Tasks
- Time It
- Analytics
- Account (Settings)

### Admin Navigation

- Admin
- Activity
- Audit
- Account (Settings)

---

## Regular User Guide

### 1. Dashboard (Home)

The dashboard gives a live overview of your day:

- Current time and date
- Time status message based on wake and bedtime
- Remaining budget indicators
- Upcoming tasks
- Quick productivity summary

Use this page to decide what to work on next.

### 2. Create and Manage Tasks

Go to Tasks and use Add Task to create a new item.

Typical fields:

- Title
- Source (for example, course, work, personal)
- Category
- Date Given / Date Due
- Description (optional)
- Estimated Time (minutes)
- Recurrence settings (if needed)

From Tasks, you can:

- Search and filter task lists
- Sort by due date or estimated time
- Open task details
- Update status (Not Started, In Progress, Completed)
- Soft-delete tasks

### 3. Log Work with Time It

Time It supports two modes:

- Timer mode: start, pause/resume, and save a timed session
- Log mode: manually enter duration and notes

Each session is linked to a task and contributes to your history and analytics.

### 4. View Analytics

Analytics provides personal behavior insights, such as:

- Completion trends
- Task velocity
- On-time completion rate
- Category-level performance
- Recommendation/tip-style feedback

Use this page weekly to adjust workload planning.

### 5. Manage Account in Settings

In Settings, you can:

- Update username, email, and full name
- Change your password
- Upload or remove profile photo
- Update onboarding/time budget inputs

---

## Admin Guide

### 1. Admin Page: User Management

On the Admin page, each user row includes actions:

- Disable/Enable account
- Unlock account
- Reset password
- Delete user

Admins can also create new users and assign role (`user` or `admin`).

### 2. Reset a User Password (New)

To reset a password for another user:

1. Go to Admin page.
2. Find the target user.
3. Click the key icon (Reset Password).
4. Enter a new password and confirm it.
5. Submit reset.

Notes:

- The new password must satisfy password rules.
- Reset action also clears lock state and failed login attempts for the target user.
- Admins cannot reset their own password through this Admin button; use Settings for own password.

### 3. User Activity Page

Use Activity to review:

- Last login timing
- Failed login patterns
- Current lock/active status
- Recent login history per user

### 4. Audit Logs Page

Use Audit to review system events such as:

- Logins
- Account creation
- Profile updates
- Password changes and admin resets
- User status changes and deletions

Filters are available by username, action, and date range.

---

## Account Security and Lockouts

- Failed login attempts are tracked.
- After repeated failed attempts, accounts may become temporarily locked.
- Locked users can:
  - Wait for automatic unlock period, or
  - Ask an admin to unlock immediately.

Best practices:

- Use a unique password.
- Do not share credentials.
- For shared environments, rotate admin passwords regularly.

---

## Troubleshooting

### App does not start

- Confirm virtual environment is activated.
- Reinstall dependencies:

```bash
pip install -r requirements.txt
```

### Login fails unexpectedly

- Verify username and password.
- Check if account is locked.
- Ask an admin to unlock or reset password if needed.

### No data appears in dashboard/analytics

- Complete onboarding first.
- Add tasks and log sessions in Time It.
- Ensure you are signed in with the correct account.

### Profile image upload fails

- Use supported image formats.
- Keep file size within allowed limit.
- Try another image and retry upload.

---

## More Documentation

- Project overview and developer notes: [../README.md](../README.md)
- Security-focused notes: [SECURITY_REPORT.md](SECURITY_REPORT.md)
- Manual QA checklist: [manual_test_checklist.md](manual_test_checklist.md)
