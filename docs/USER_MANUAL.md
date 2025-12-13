# TYMATE User Manual

Complete guide to using TYMATE for time management and task tracking.

---

## Table of Contents
1. [User Types & Capabilities](#user-types--capabilities)
2. [Installation & Setup](#installation--setup)
3. [First-Time Setup](#first-time-setup)
4. [Creating Tasks](#creating-tasks)
5. [Managing Tasks](#managing-tasks)
6. [Understanding Your Dashboard](#understanding-your-dashboard)
7. [Viewing Analytics](#viewing-analytics)
8. [Updating Settings](#updating-settings)
9. [Tips for Success](#tips-for-success)

---

## User Types & Capabilities

### Regular User
- **Personal task management**: Create, edit, and manage your own tasks
- **Personal dashboard**: View your time budget and task overview
- **Personal analytics**: See insights based only on your task data
- **Profile management**: Update your own profile, password, and photo
- **Settings**: Customize your sleep schedule and study goals
- **Cannot**: View other users' data or access admin features

### Admin User
- **Account Management**: Create, view, and manage user accounts
- **Audit Logs**: View and export audit trail of all system actions
- **User Activity Monitoring**: Track user registrations, logins, and task activity
- **Admin Panel**: Access to system-wide statistics and management tools
- **Cannot**: Create personal tasks, view personal analytics, or manage own tasks (admin-only focus)

### How to Know Your Role
Your user role is displayed in your profile settings. Most users are "Regular" users. Admin accounts are created during system setup.

---

## Installation & Setup

### Prerequisites
- **Python 3.8 or higher** — Download from [python.org](https://www.python.org/)
- **pip** — Comes with Python
- **A code editor or terminal** — For running commands

### Step 1: Download or Clone the Project
```bash
# Option A: If you have the code as a folder
# Just extract/copy the tymate folder to your computer

# Option B: If cloning from git
git clone <repository-url>
cd tymate
```

### Step 2: Create a Virtual Environment
A virtual environment keeps TYMATE's dependencies separate from your system Python.

```bash
python -m venv .venv

# Activate it:
# On Mac/Linux:
source .venv/bin/activate

# On Windows:
.venv\Scripts\activate
```

### Step 3: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 4: Initialize Database with Sample Data
```bash
python tests/generate_sample_db.py
```

This creates the database with:
- **Admin account**: username `admin`, password `admin123`
- **Sample users**: jessica, john (for testing)
- **Sample tasks**: Realistic tasks with various statuses

### Step 5: Run TYMATE
```bash
# As a Desktop App (recommended for first-time users)
python main.py

# Or as a Web App (runs in your browser)
flet run main.py --web
```

The app will launch! Log in with your credentials and start tracking your time.

### Step 6: Create Your Account (Optional)
If you want to create a fresh account instead of using the sample data:
1. Click **Sign Up** on the login screen
2. Enter a username, email (optional), and password
3. Complete the onboarding wizard (set your sleep schedule)
4. Start adding tasks!
### ⚠️ Important: Change Default Admin Password

During setup, an admin account is created with default credentials:
- **Username**: `admin`
- **Password**: `admin123`

**If you share your computer with others, change this password immediately**:
1. Log in with `admin` / `admin123`
2. Go to **Settings** → **Profile Tab** → Change Password
3. Log out and back in to confirm

#### *This prevents others from accessing the admin panel and your task data. It's like changing your WiFi password on a shared network.*
---

## First-Time Setup (Onboarding)

1. **Register**: Create an account with username, email, and password
2. **Onboarding Wizard**:
   - **Step 1**: Set your sleep hours and wake time
   - **Step 2**: Review your calculated time budget

---

## Creating Tasks

1. Navigate to **Tasks** page (📋 icon in navigation)
2. Click **➕ Add Task** button
3. Fill in required fields:
   - **Title**: Task name
   - **Source**: Who assigned it (e.g., "CS 319", "Coffee Shop", "Personal")
   - **Category**: Select from dropdown (School, Work, Personal, etc.)
   - **Date Given**: When you received the task
   - **Date Due**: Deadline
   - **Description**: Optional details
   - **Estimated Time**: Optional hours estimate
4. Click **Create Task**

---

## Managing Tasks

- **Edit**: Click task card → Update fields → Save
- **Mark In Progress**: Click **Edit** button → Change Status to "In Progress" → Save
- **Complete**: Click **Task Checkbox** → Optionally enter actual time spent
- **Delete**: Click **🗑️ Delete** (soft delete)
- **Sort & Filter**: Always sorted by earliest due date; Can use Status filters

---

## Understanding Your Dashboard

### Time Status Indicators
- 🔵 **Blue**: Before wake time
- 🟢 **Green**: Plenty of time remaining (4+ hours)
- 🟡 **Yellow**: Getting late (2-4 hours)
- 🟠 **Orange**: Running out of time (<2 hours)
- 🔴 **Red**: Past bedtime

### Summary Cards
- **Total Tasks**: Your active upcoming tasks
- **Completed Today**: Tasks finished today
- **Hours This Week**: Time logged (to finish tasks) since Monday
- **Completion Rate**: % of tasks completed in last 30 days

---

## Viewing Analytics

1. Click **📊 Analytics** in navigation
2. Review insights:
   - **Tasks Completed**: 30-day total
   - **Task Velocity**: Average tasks per week
   - **On-Time Rate**: % completed before deadline
   - **30-Day Activity**: Daily completion bar chart
   - **Procrastination Analysis**: Your tendency to delay
   - **Time Estimation**: How accurate your estimates are
   - **Category Performance**: Best and worst task types
   - **Smart Recommendations**: Personalized improvement tips

---

## Updating Settings

1. Go to **⚙️ Settings**
2. **Profile Tab**: Update name, email, password, or photo
3. **Time Budget Tab**: Adjust sleep hours, wake time, or study goal
4. Click **Save** to update information

---

## Account Security

### What Happens If You Forget Your Password?

Try logging in with your correct username and your best guess at the password. If you fail 5 times, your account temporarily locks.

### Account Lockout
- **Why it happens**: After 5 failed login attempts, your account locks to prevent someone from guessing your password
- **How long it lasts**: 30 minutes (automatic unlock)
- **What to do**:
  - **Option 1**: Wait 30 minutes and try again
  - **Option 2**: Ask an admin to unlock your account immediately
- **Getting help**: Contact your system administrator if you're locked out and need immediate access

---

## Tips for Success

### ✅ Daily Habits
- Check dashboard each morning to see remaining time
- Update task status as you work
- Log actual time when completing tasks

### ✅ Weekly Review
- Check analytics to identify patterns
- Adjust study goals if needed
- Review procrastination score

### ✅ Time Estimation
- Start with rough estimates
- Log actual time to improve accuracy
- Use analytics to calibrate future estimates

---

## Need Help?

For technical documentation and setup instructions, see [README.md](README.md).
