#  Tymate — A Time Budgeting App

Tymate is a time‑aware activity tracker designed for working students and regular students in academic settings. It helps users create and organize tasks, assign estimated time values, and monitor how their time is distributed throughout the day or week. 

The system supports comprehensive task management, intelligent time budgeting, predictive analytics, and real-time progress tracking to help users stay aware of their workload and optimize productivity.

## Core Concept
Just like a bank account or budgeting app shows:
- **Balance**: How much money you have left
- **Deposits**: Money coming in
- **Withdrawals**: Money going out

TYMATE shows:
- **Balance**: How many free hours you have left today
- **Budget**: Your total available time (calculated from sleep and wake time)
- **Spent**: Hours you've logged to tasks

The app adapts to your **wake time and bedtime**, showing realistic remaining hours throughout the day.

---

## ✨ Features

### 🎯 Task Management
- **Invoice-Style Task Entry**: Tasks include required fields like source (who assigned it), category, date given, and due date
- **Categories**: School-related (quiz, LT, project), and then 'Others'
- **Status Tracking**: Not Started, In Progress, Completed
- **Time Estimation**: Set estimated and actual time spent
- **Filter**: Filter by status
- **Soft Delete**: Tasks are archived, not permanently deleted

### ⏰ Real-Time Budget Tracking
- **Dynamic Time Calculations**: Shows remaining hours until bedtime
- **Wake/Sleep Awareness**: Accounts for your wake time and sleep schedule
- **Status Messages**: 
  - "Day hasn't started yet. Wake in X hours" (before wake time)
  - "X hours remaining today" (during active hours)
  - "Only X hours until bedtime!" (near end of day)
  - "Past bedtime! Time to sleep" (after bedtime)
- **Study Goal Tracking**: Monitor progress toward daily study goals

### 📊 Advanced Analytics
- **Completion Metrics**:
  - Tasks completed (last 30 days)
  - Task velocity (tasks per week)
  - Average completion time
  - On-time completion rate
- **30-Day Activity Chart**: Visual bar chart showing daily task completions
- **Procrastination Score**: 0-100 scale analyzing last-minute vs early completion patterns
- **Time Estimation Accuracy**: Compare estimated vs actual time spent
- **Category Performance**: See which task types you complete most effectively
- **Smart Recommendations**: AI-generated tips based on your patterns

### 👤 User Profile & Settings
- **Profile Management**: Update name, email, password
- **Profile Picture**: Upload and manage avatar (max 5MB, supports jpg/png/gif/webp)
- **Time Budget Customization**: Adjust sleep hours, wake time, study goals
- **Session Management**: Secure authentication with password hashing

### 📱 Dashboard Overview
- **Real-Time Clock**: Updates every second with current date/time
- **Upcoming Tasks**: Next 5 tasks sorted by due date
- **Analytics Preview**: 7-day completion chart
- **Summary Cards**:
  - Total active tasks
  - Tasks completed today
  - Hours logged this week
  - 30-day completion rate

### 🔐 Security Features
- **Password Hashing**: Secure password storage with bcrypt
- **Session Management**: Token-based authentication
- **Soft Deletes**: Data retention and recovery
- **Role-Based Access**: User, Admin roles

---

##  Getting Started

### Prerequisites
- Python 3.8 or higher
- pip (Python package installer)

### 1. Create and activate a virtual environment
```bash
python -m venv .venv

# Mac/Linux
source .venv/bin/activate

# Windows
.venv\Scripts\activate
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Run the app
```bash
# As a Desktop App
python main.py

# As a Web App
flet run main.py --web
```

---

## 📖 User Manual

### First-Time Setup (Onboarding)

1. **Register**: Create an account with username, email, and password
2. **Onboarding Wizard**:
   - **Step 1**: Set your sleep hours and wake time
   - **Step 2**: Review your calculated time budget

### Creating Tasks

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

### Managing Tasks

- **Edit**: Click task card → Update fields → Save
- **Mark In Progress**: Click **Edit** button → Change Status to "In Progress" → Save
- **Complete**: Click **Task Checkbox** → Optionally enter actual time spent
- **Delete**: Click **🗑️ Delete** (soft delete)
- **Sort & Filter**: Always sorted by earliest due date; Can use Status filters

### Understanding Your Dashboard

**Time Status Indicators**:
- 🔵 **Blue**: Before wake time
- 🟢 **Green**: Plenty of time remaining (4+ hours)
- 🟡 **Yellow**: Getting late (2-4 hours)
- 🟠 **Orange**: Running out of time (<2 hours)
- 🔴 **Red**: Past bedtime

**Summary Cards**:
- **Total Tasks**: Your active upcoming tasks
- **Completed Today**: Tasks finished today
- **Hours This Week**: Time logged (to finish tasks) since Monday
- **Completion Rate**: % of tasks completed in last 30 days

### Viewing Analytics

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

### Updating Settings

1. Go to **⚙️ Settings**
2. **Profile Tab**: Update name, email, password, or photo
3. **Time Budget Tab**: Adjust sleep hours, wake time, or study goal
4. Click **Save** to update information

### Tips for Success

✅ **Daily Habits**:
- Check dashboard each morning to see remaining time
- Update task status as you work
- Log actual time when completing tasks

✅ **Weekly Review**:
- Check analytics to identify patterns
- Adjust study goals if needed
- Review procrastination score

✅ **Time Estimation**:
- Start with rough estimates
- Log actual time to improve accuracy
- Use analytics to calibrate future estimates

---

## 🧪 Running Tests

### Remove existing database (if needed)
```bash
# Windows
del data\tymate.db

# Mac/Linux
rm data/tymate.db
```

### Run Test Suite
```bash
# Database Test
python -m tests.test_database

# Onboarding Feature Test
python -m tests.test_onboarding

# Authentication Test
python -m tests.test_auth

# Generate Sample Database with Test Data
python -m tests.generate_sample_db
python main.py      # Login with generated test credentials
```

---

## 📂 Project Structure

```
tymate/
├── main.py                 # Application entry point
├── requirements.txt        # Python dependencies
├── README.md              # Documentation
├── components/            # Reusable UI components
│   ├── navbar.py
│   └── task_card.py
├── data/                  # Database storage
│   └── tymate.db
├── models/                # Data models
│   ├── task.py
│   └── user.py
├── services/              # Business logic
│   └── analytics_engine.py
├── state/                 # State management
│   ├── auth_manager.py
│   ├── onboarding_manager.py
│   └── task_manager.py
├── storage/               # Database layer
│   └── sqlite.py
├── tests/                 # Test suite
│   ├── test_auth.py
│   ├── test_database.py
│   ├── test_onboarding.py
│   └── generate_sample_db.py
└── views/                 # UI pages
    ├── analytics.py
    ├── dashboard.py
    ├── login.py
    ├── log_hours.py
    ├── onboarding.py
    ├── settings.py
    └── tasks.py
```

---

## 🛠️ Technologies Used

- **Framework**: [Flet](https://flet.dev/) (Python UI framework)
- **Database**: SQLite3
- **Security**: bcrypt (password hashing)
- **Analytics**: Built-in Python statistics module
- **Architecture**: MVC pattern with service layer

---

## 📝 License

This project is developed as part of academic coursework.

---

## 👥 Credits

Developed by Jessica Lanuzo  
Bachelor of Science in Computer Science, Year 3