#  TYMATE — A Time Budgeting App for Students

## 📋 Table of Contents
1. [Project Overview](#project-overview)
2. [Feature List & Scope](#feature-list--scope)
3. [Architecture](#architecture)
4. [Data Model](#data-model)
5. [Emerging Technology](#emerging-technology)
6. [Setup & Run Instructions](#setup--run-instructions)
7. [Testing Summary](#testing-summary)
8. [Team Roles & Contributions](#team-roles--contributions)
9. [Risks & Constraints](#risks--constraints)
10. [Individual Reflection](#reflections)

**📋 Additional Documentation**:
- **[Software Requirements Specification (SRS)](docs/Tymate%20SRS%20(Software%20Requirements%20Specification).pdf)** — Complete project specification
- **[User Manual](docs/USER_MANUAL.md)** — Installation & usage guide
- **[Security Report](docs/SECURITY_REPORT.md)** — Threat model, authentication, OWASP Top 10 analysis

---

## Project Overview

### Problem Statement
Working students and regular students struggle with time management due to competing demands (sleep, work, studies). Current task managers don't account for realistic available time or provide intelligent budgeting. TYMATE solves this by:

1. **Modeling available time like a bank account** — showing remaining hours after accounting for sleep and daily commitments
2. **Providing real-time awareness** — dynamic status messages adapt to time of day
3. **Intelligent analytics** — identifying procrastination patterns, time estimation accuracy, and per-category performance
4. **Smart recommendations** — AI-generated improvement tips based on user behavior

### Core Concept
Just like a bank account shows balance, deposits, and withdrawals:
- **Balance**: How many free hours you have left today
- **Budget**: Your total available time (calculated from sleep and wake time)
- **Spent**: Hours you've logged to tasks

TYMATE adapts to your **wake time and bedtime**, showing realistic remaining hours throughout the day.

---

## Feature List & Scope

### ✅ In Scope (Implemented)

| Feature | Status | Priority |
|---------|--------|----------|
| User Registration & Login | ✅ Complete | P0 |
| Task Management (CRUD) | ✅ Complete | P0 |
| Real-Time Time Budget Display | ✅ Complete | P0 |
| Dashboard with Overview | ✅ Complete | P0 |
| Analytics & Performance Metrics | ✅ Complete | P1 |
| Profile Management | ✅ Complete | P1 |
| Settings & Customization | ✅ Complete | P1 |
| Password Hashing (bcrypt) | ✅ Complete | P0 |
| Session Management | ✅ Complete | P0 |
| Admin User Management (disable/unlock/delete/reset password) | ✅ Complete | P1 |
| Profile Photo Upload | ✅ Complete | P2 |
| Soft Delete (Data Retention) | ✅ Complete | P1 |
| Task Filtering & Sorting | ✅ Complete | P1 |
| 30-Day Activity Analytics | ✅ Complete | P1 |

### ❌ Out of Scope (Future Enhancements)

| Feature | Reason | Priority |
|---------|--------|----------|
| Database-Level AES-256 Encryption | Student project; bcrypt sufficient | P3 |
| Collaborative Task Sharing | Not in original requirements | P3 |
| Mobile App (native iOS/Android) | Web/desktop via Flet covers scope | P3 |
| Real-time Cloud Sync | Beyond scope; local-first design | P3 |
| Advanced ML Predictions | Would require significant data history | P3 |
| Offline Mode | Desktop/web covers scope | P3 |
| Dedicated Log Hours page route + UX polish | Time logging exists via Time It; standalone page is still placeholder-level | P3 |


---

## Architecture

### System Architecture Diagram
```
┌─────────────────────────────────────────────────────────────┐
│                    PRESENTATION LAYER                       │
│                   (Flet UI Components)                      │
├────────────┬──────────────┬──────────────┬──────────────────┤
│  Dashboard │    Tasks     │   Time It    │    Analytics     │
│   Page     │    Page      │    Page      │      Page        │
└────────────┴──────────────┴──────────────┴──────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                    STATE MANAGEMENT LAYER                   │
├────────────┬──────────────┬──────────────┬──────────────────┤
│  AuthMgr   │   TaskMgr    │  OnboardMgr  │   SessionMgr     │
│ (sessions) │ (CRUD ops)   │   (setup)    │ (time logs)      │
└────────────┴──────────────┴──────────────┴──────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                  BUSINESS LOGIC LAYER                       │
├──────────────────────────────────────────────────────-──────┤
│         AnalyticsEngine (calculations, AI hints)            │
│          User Model (bcrypt password hashing)               │
│          Task Model (status, time tracking)                 │
└───────-─────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                    DATA STORAGE LAYER                       │
├────────────────────────────────────────────-────────────────┤
│            SQLite Database (data/tymate.db)                 │
│                    - users / roles / sessions               │
│                    - tasks / task_sessions / task_events    │
│                    - audit_logs / time_logs / settings      │
└─────────────────────────────────────────────────-───────────┘
```

### Key Components
- **Flet**: Cross-platform UI framework (desktop & web)
- **SQLite**: Local relational database (no server required)
- **bcrypt**: Password hashing module
- **Analytics Engine**: Built-in recommendation system

### Project Structure
```
tymate/
├── main.py                 # Application entry point
├── requirements.txt        # Python dependencies
├── README.md              # Documentation
├── components/            # Reusable UI components
├── data/                  # Database storage
├── models/                # Data models (User, Task, Session)
├── services/              # Business logic (Analytics)
├── state/                 # State management (Auth, Task, Session, Onboarding)
├── storage/               # Database layer (SQLite)
├── tests/                 # Test suite
└── views/                 # UI pages (Dashboard, Tasks, Time It, Analytics, Settings, Admin)
```

---

## Data Model

### Entity Relationship Diagram
```
USERS (id, username, password_hash, email, ...)
  │
  ├─ id (PRIMARY KEY)
  ├─ username (UNIQUE)
  ├─ password_hash (bcrypt)
  ├─ role (admin, premium, user)
  ├─ sleep_hours, wake_time (time budget)
  ├─ created_at, updated_at (timestamps)
  └─ 1:N ──────────────────────────┐
                                   │
TASKS (id, user_id, title, ...)    │
  ├─ id (PRIMARY KEY)              │
  ├─ user_id (FOREIGN KEY) ────────┘
  ├─ title, source, category
  ├─ date_given, date_due
  ├─ estimated_time, status, completed_at
  ├─ is_recurring, recurrence_type, recurrence_interval, recurrence_until
  └─ is_deleted (soft delete flag)

TASK_SESSIONS (id, task_id, user_id, ...)
  ├─ id (PRIMARY KEY)
  ├─ task_id (FOREIGN KEY) ──────── references TASKS
  ├─ duration_minutes, logged_at, notes
  └─ is_deleted (soft delete flag)

TASK_EVENTS (id, task_id, user_id, ...)
  ├─ id (PRIMARY KEY)
  ├─ task_id (FOREIGN KEY) ──────── references TASKS
  ├─ event_type, message, metadata
  └─ created_at (timestamp)

AUDIT_LOGS (id, user_id, action, ...)
  ├─ id (PRIMARY KEY)
  ├─ user_id (FOREIGN KEY) ────── references USERS
  ├─ action (USER_REGISTERED, TASK_CREATED, etc.)
  ├─ table_name, record_id
  └─ created_at (timestamp)
```

### Key Fields
- **password_hash**: bcrypt format (never plaintext)
- **date_due, completed_at**: ISO 8601 timestamps
- **is_deleted**: Soft delete (retain data for analytics)
- **role**: Admin can view all analytics; User can only view own

---

## Emerging Technology

### AI-Powered Analytics Engine

**What it does:**
- Analyzes user task completion patterns over 30 days
- Generates personalized recommendations based on behavior
- Calculates procrastination score (0-100 scale)
- Estimates time accuracy for future planning

**Why chosen:**
- Provides value-added insights beyond basic task tracking
- Helps students improve time estimation and planning
- Demonstrates pattern recognition & data analysis skills
- Suitable for academic/personal projects without heavy ML infrastructure

**Implementation:**
- Built using Python's `statistics` module (mean, median, stdev)
- Heuristic-based rules (not deep learning)
- Runs locally; no external API calls
- Analyzes completion timing, category performance, and accuracy

**Limitations:**
- Requires historical data (30 days minimum for accurate insights)
- Cannot predict external factors (illness, emergencies)
- Limited to rule-based recommendations (not probabilistic ML)
- May be inaccurate with small sample sizes

**Code location:** [services/analytics_engine.py](services/analytics_engine.py)

---

## Setup & Run Instructions

### Prerequisites
- Python 3.8 or higher
- pip (Python package installer)
- Virtual environment (recommended)

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

### 3. Configure environment (optional)
Create a `.env` file in the project root to customize settings:
```env
# App view: 'web' for browser or 'desktop' for packaged app
FLET_APP_VIEW=web

# Session timeout (minutes)
TYMATE_SESSION_TIMEOUT_MINUTES=30
```

### 4. Run the app
```bash
# As a Desktop App
python main.py

# As a Web App (in browser)
flet run main.py --web
```

### Supported Platforms
- **Desktop**: Chrome, Edge, Firefox (Windows, Mac, Linux)
- **Mobile**: Safari (iOS), Chrome Mobile (Android)
- **Development**: Can run as standalone desktop app with PyInstaller

For detailed usage instructions, see [docs/USER_MANUAL.md](docs/USER_MANUAL.md).

---

## Testing Summary

### Test Coverage
```
✅ Unit Tests
   - test_unit_user_model.py: User password hashing & validation

✅ Integration Tests  
   - test_database.py: Database CRUD operations
   - test_auth.py: User login & registration flow
   - test_onboarding.py: Onboarding workflow
   - test_integration_auth_flow.py: End-to-end auth scenarios
   - test_schedule_manager.py: Schedule logic and time calculations
   - test_realtime_budget_edge_cases.py: Real-time budget edge cases
   - test_budget_verdict.py: Budget verdict and threshold behavior
   - test_edge_case_fix_validation.py: Regression coverage for onboarding/time edge cases

✅ Manual Testing
   - [Manual Test Checklist](docs/manual_test_checklist.md): UI feature verification
```

### How to Run Tests
```bash
# Remove existing database if needed
rm data/tymate.db        # Mac/Linux
del data\tymate.db       # Windows

# Run individual tests
python -m pytest tests/test_auth.py
python -m pytest tests/test_database.py
python -m pytest tests/test_onboarding.py
python -m pytest tests/test_unit_user_model.py
python -m pytest tests/test_integration_auth_flow.py
python -m pytest tests/test_schedule_manager.py
python -m pytest tests/test_realtime_budget_edge_cases.py
python -m pytest tests/test_budget_verdict.py
python -m pytest tests/test_edge_case_fix_validation.py

# Run all committed tests
python -m pytest tests/

# Generate sample database
python tests/generate_sample_db.py
python main.py           # Login with test credentials
```

### Test Data
Sample database includes:
- 3 pre-created users (admin, jessica, john)
- 20+ realistic sample tasks with various statuses
- Historical task data for analytics testing
- Audit log entries for system actions

### Coverage Notes
- Includes unit, integration, and targeted edge-case regression tests
- UI behavior is still primarily validated via manual test checklist (Flet limitation)
- Time-budget edge cases are explicitly covered by dedicated regression tests

---

## Team Roles & Contributions

**Jessica Lanuzo** — Sole Developer

This project was independently developed as part of academic coursework. All aspects including project planning, architecture design, backend/frontend implementation, testing, and documentation were completed individually.

---

---

## Risks & Constraints

### Technical Constraints
| Constraint | Impact | Mitigation |
|-----------|--------|------------|
| Flet UI Testing | Cannot automate test UI with pytest | Manual testing + comprehensive test data |
| SQLite Scalability | Single file database | Suitable for <100 users (academic project) |
| No Real-Time Sync | Local-first design only | Document as future enhancement |
| bcrypt vs AES-256 | No database-level encryption | bcrypt passwords sufficient for scope |

### Identified Risks
| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Password verification failure | Low | High | Implemented bcrypt sync in tests |
| Data loss (no backup) | Low | Medium | Soft deletes retain historical data |
| Session timeout edge cases | Low | Low | 30-min configurable timeout |
| Profile photo upload errors | Medium | Low | 5MB limit + format validation |
| Time calculation regressions | Low | Medium | Guarded by dedicated edge-case regression tests and schedule-manager tests |

**NOTE**: Check out **[Security Report](docs/SECURITY_REPORT.md)** for a more extensive discussion regarding app security.

### Future Enhancements
- ☐ SQLCipher for database encryption
- ☐ Cloud backup (Google Drive, Dropbox integration)
- ☐ Real-time notifications (when overdue)
- ☐ Improve recurring task UX (rule editor + occurrence preview)
- ☐ Dedicated Log Hours page flow (Time It is currently the primary logging path)
- ☐ Work Time and Schedule considerations
- ☐ Collaborative task sharing
- ☐ Mobile app (iOS/Android native)
- ☐ Advanced ML-based predictions
- ☐ Dark mode theme

---

## Reflections

### Jessica Lanuzo - Full Stack Developer

*So, Flet continued to prove to be a really good choice for developing apps; I only needed to be familiar with it (or just consult the documentation often), and I could do just about everything with my knowledge of coding in Python. And as I am still relatively new to developing on my own, references and bases are also really important in being able to build my own things efficiently.* 

*My circumstances led me to have an iterative workflow of (1) running through several of the software functionalities based on when it will appear or be used and (2) going back to the first uncommitted one and reviewing it before pushing into my GitHub repository. This, funnily, led to code conflicts even though I was working on my own because I did local version saving (can’t even call it ‘control’) before commits. But it was also somehow very fitting for my situation, because if I committed everything at once, I don’t think I would’ve reviewed them anymore later…* 

*Here, instead of my usual habit of overthinking the whole thing, I focused on the app flow and decided on things based on how I experienced it when doing the test runs.*



---

## 📝 License

This project is developed as part of academic coursework at University.

---

## 👥 Author

**Jessica Lanuzo**  
Bachelor of Science in Computer Science, Year 3  
Developed for the courses:

- CCCS 106 - Application Development and Emerging Technologies
- CS 319 - Information Assurance and Security
- CS 3110 - Software Engineering 1 and 2

April 2026

---

## 📚 References

- [Flet Documentation](https://flet.dev/)
- [Python bcrypt](https://pypi.org/project/bcrypt/)
- [SQLite Documentation](https://www.sqlite.org/)
- Time Management Research: Cal Newport's "Deep Work" principles
- Task Management UX: Inspired by Todoist, Google Tasks, Microsoft To Do