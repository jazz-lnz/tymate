#  Tymate — A Time Budgeting App

Tymate is a time‑aware activity tracker designed for working students and regular students in academic settings. It helps users create and organize tasks, assign estimated time values, and monitor how their time is distributed throughout the day or week. 

The system supports basic task management, time budgeting, and progress tracking to help users stay aware of their workload.

## Core Concept
Just like a bank account or budgeting app shows:
- **Balance**: How much money you have left
- **Deposits**: Money coming in
- **Withdrawals**: Money going out

TYMATE shows:
- **Balance**: How many free hours you have left today
- **Budget**: Your total available time

- **Spent**: Hours you've logged to tasks

##  Getting Started

### 1. Create and activate a virtual environment
```
python -m venv .venv

# Mac/Linux
source .venv/bin/activate

## Windows
# .venv\Scripts\activate
```

### 2. Install dependencies
``` 
pip install -r requirements.txt
```

### 3. Run the app
```
# As a Desktop App
python main.py

## As a Web App
# flet run main.py --web
```

## Running Tests

#### Remove existing database (if needed)
```
# del data\tymate.db
```

### Database Test
```
python -m tests.test_database
```
### Onboarding Feature Test
```
python -m tests.test_onboarding
```
### Authentication Test
```
python -m tests.test_auth
```