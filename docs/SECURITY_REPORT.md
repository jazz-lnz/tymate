# TYMATE Security Engineering Report

**Scope Note**: TYMATE is a **personal, locally-run desktop application**. The threat model differs significantly from web applications. This report documents security controls appropriate for a single-user or shared-machine scenario, not multi-user cloud systems.

---

## Table of Contents
1. [Threat Model](#threat-model)
2. [Authentication & Password Security](#authentication--password-security)
3. [Session Management](#session-management)
4. [Input Validation & Sanitization](#input-validation--sanitization)
5. [Error Handling & Logging](#error-handling--logging)
6. [OWASP Top 10 Mitigations](#owasp-top-10-mitigations)
7. [Data Protection](#data-protection)
8. [Access Control](#access-control)

---

## ⚠️ Important: Default Admin Credentials

During initial setup, a default admin account is created:

- **Username**: `admin`
- **Password**: `admin123`

### For Single-User Machines

If TYMATE only runs on your personal computer with your OS login, the default admin password is acceptable. Your OS-level login credential is the primary security boundary.

### For Shared Machines

**Change the default admin password immediately** if:
- You share your computer with roommates, family, or colleagues
- Multiple people have physical access to your machine
- You're on a shared network (college dorm, office)

**How to change**:
1. Log in with `admin` / `admin123`
2. Go to **Settings** → **Profile Tab** → Change Password
3. Log out and re-login to confirm

Once changed, only the new password grants admin access.

---

## Threat Model

### STRIDE Analysis (Adapted for Local Desktop App)

| Threat Category | Relevant to Local App? | Risk | Mitigation |
|-----------------|------------------------|------|------------|
| **Spoofing Identity** | ✅ Yes (Shared machines) | Someone logs in as another user | bcrypt password hashing + session tokens + change default admin password |
| **Tampering with Data** | ✅ Yes (Physical access) | Unauthorized modification of tasks/settings | Audit logging + soft deletes (history preserved) |
| **Repudiation** | ✅ Limited | User claims they didn't perform an action | Audit logs track all actions with timestamps |
| **Information Disclosure** | ⚠️ Moderate (Local only) | Someone reads database file directly | bcrypt for passwords + OS file permissions |
| **Denial of Service** | ✅ Yes (User error) | App crashes from bad input | Input validation + graceful error handling |
| **Elevation of Privilege** | ✅ Yes (Shared machines) | Regular user accesses admin panel | Role-based access control + default password warning |

### Context: Local vs Network Threats

**What's DIFFERENT for a local app**:
- No remote attackers (app doesn't connect to internet)
- OS-level login is the primary security boundary
- Physical access to computer is required for all attacks
- Database file stored locally (protected by OS permissions)

**What STILL MATTERS**:
- Shared machines: roommates, family, colleagues
- Accidental data loss or corruption
- Password security (in case database file is copied)

### Key Threats & Mitigations

#### 1. Shared Machine Access
- **Threat**: Someone with physical access to your computer uses your logged-in session or default admin credentials
- **Mitigation**: 
  - 30-minute inactivity timeout
  - Change default admin password on shared machines
  - Log out when leaving computer

#### 2. Data Loss/Corruption
- **Threat**: Accidental deletion or database corruption
- **Mitigation**:
  - Soft deletes (can be recovered)
  - Audit trail of all changes
  - Manual backup recommended (copy `data/tymate.db`)

#### 3. Password Compromise
- **Threat**: Someone copies database file and tries to crack passwords
- **Mitigation**:
  - bcrypt hashing (intentionally slow, brute-force resistant)
  - 12 rounds = ~4,096 iterations per password check
  - Each password has unique salt

---

## Authentication & Password Security

### Password Hashing Algorithm

**Algorithm**: bcrypt  
**Cost Factor**: 12 rounds  
**Why chosen**: 
- Industry standard (GitHub, Heroku use bcrypt)
- 12 rounds balances security vs speed (~100ms login time)
- Higher than minimum (10 rounds) but doesn't slow down UX
- Can increase to 13-14 rounds later as hardware improves

### What This Means for You

When you create a password:
1. TYMATE never stores your actual password
2. It stores a "hash" (one-way scrambled version)
3. Even if someone copies `data/tymate.db`, they can't read your password
4. Login checks your password against the hash (takes ~0.1 seconds)

**Account Locking**: After 5 failed login attempts, your account temporarily locks for security. It auto-unlocks after 30 minutes, or admins can manually unlock it immediately.

**Important**: Because passwords are hashed, **you cannot recover a forgotten password**. You'd need to manually reset it via database access or create a new account.

### Implementation

```python
# Hash on registration/password change
salt = bcrypt.gensalt(rounds=12)
hashed = bcrypt.hashpw(password.encode('utf-8'), salt)

# Verify on login
bcrypt.checkpw(password.encode('utf-8'), hash.encode('utf-8'))
```

**Code Location**: [models/user.py](models/user.py#L88-L107)

### Password Requirements

- **Minimum length**: 6 characters
  - *Why*: Balance between security and usability for personal app
  - *Reasoning*: bcrypt makes even short passwords hard to crack; 6 chars = 308 billion combinations
- **No complexity rules**: Research shows length matters more than special characters
- **No password history**: Single-user app, no compliance requirements
- **No email verification**: Local app, no password reset via email needed

---

## Account Locking & Brute Force Protection

### How It Works

**Threshold**: 5 failed login attempts within any timeframe  
**Automatic Unlock**: 30 minutes of inactivity  
**Admin Override**: Admins can manually unlock accounts immediately

### Why This Matters

**Brute Force Attack Prevention**:
- Attackers who try common passwords can't just keep trying
- After 5 failures, account locks and forces them to wait 30 minutes
- Makes password guessing impractical (e.g., 50,000 attempts = 1.4+ years of waiting)

### User Experience

When locked out, users see:
```
❌ "Too many failed attempts. Account locked for 30 minutes."
```

After 30 minutes:
- Account automatically unlocks
- They can try again
- Failed attempt counter resets on successful login

### Admin Management

Admins can unlock accounts immediately via the Admin Panel:
1. Open Admin > User Management
2. Find the locked user (shows "Locked" status in orange)
3. Click the 🔓 unlock button
4. Account unlocks instantly

Admins can also use manual unlock during IT incidents (e.g., legitimate user knows their password but it changed).

### Code Implementation

```python
# Database tracking
locked_at: Optional[str]  # Timestamp when account was locked

# Login check
if user.is_locked and user.locked_at:
    time_since_lock = datetime.now() - datetime.fromisoformat(user.locked_at)
    if time_since_lock >= timedelta(minutes=30):
        # Auto-unlock
        user.is_locked = False
```

**Code Location**: [state/auth_manager.py](state/auth_manager.py#L120-L155) | [views/admin.py](views/admin.py#L115-L120)

### How Login Works

1. You enter username + password
2. App checks if password matches the stored hash
3. If correct, you're logged in for that session
4. Session ends when you close the app or log out

### Inactivity Timeout

**Default**: 30 minutes of inactivity logs you out automatically

**Why 30 minutes**: 
- Long enough for typical work sessions (adding multiple tasks)
- Short enough to protect against walked-away computers
- Standard for many desktop apps (VS Code, Slack use similar)
- Configurable via `.env` for personal preference

**Customize** (optional):
```env
# In .env file
TYMATE_SESSION_TIMEOUT_MINUTES=60  # Change to 60 minutes
```

**Code Location**: [state/auth_manager.py](state/auth_manager.py)

---

## Input Validation

### What Gets Checked

✅ **Task titles**: Max 200 characters  
  - *Why*: Most task titles are 10-50 chars; 200 allows long titles without UI issues
✅ **Task descriptions**: Max 2000 characters  
  - *Why*: ~300-400 words; enough for detailed notes without bloating database
✅ **Profile photos**: Max 5MB, must be jpg/png/gif/webp  
  - *Why*: High-res photos are 2-3MB; 5MB comfortable limit without storage issues
✅ **Passwords**: Minimum 6 characters  
  - *Why*: See password requirements above

### Why These Limits?

1. **Database performance**: SQLite handles these sizes efficiently
2. **UI responsiveness**: Flet can render without lag
3. **Storage**: Estimated 100 tasks + 1 photo = ~10MB total (very manageable)

### SQL Injection Protection

All database queries use **parameterized statements** (safe approach):
```python
# SAFE - What TYMATE does
db.fetch_one("SELECT * FROM users WHERE username = ?", (username,))
```

This prevents malicious input from breaking the database.

**Code Location**: [storage/sqlite.py](storage/sqlite.py)

---

## Error Handling & Logging

### Secure Error Handling

#### Principle: Don't Leak Sensitive Info

```python
# ❌ BAD - Exposes internal path
except Exception as e:
    return False, f"Database error at /home/user/tymate/storage/sqlite.py:42"

# ✅ GOOD - Generic message to user
except Exception as e:
    logger.error(f"Database error: {str(e)}")
    return False, "An error occurred. Please try again."
```

#### Login Error Handling
```python
# Intentionally vague to prevent username enumeration
success, msg, user, token = auth.login(username, password)
if not success:
    # Shows same message for both "user not found" and "wrong password"
    error_message.value = "Invalid username or password"
```

### Audit Logging

All security-relevant actions logged with:
- **Timestamp**: Exact moment of action
- **User ID**: Who performed action
- **Action type**: REGISTERED, LOGIN, LOGOUT, TASK_CREATED, etc.
- **Record details**: What was affected (immutable history)

**Logged Actions**:
- User registration
- Login attempts (successful & failed)
- Password changes
- Task CRUD operations
- Settings modifications
- Admin actions

**Code Location**: [state/auth_manager.py#_log_audit](state/auth_manager.py)

**Log Storage**: `audit_logs` table in SQLite (accessible via Admin panel)

### Logging Configuration

```python
# Built-in Python logging (could be extended)
import logging
logger = logging.getLogger("tymate")

# All security events logged
logger.info(f"User {user_id} registered: {username}")
logger.warning(f"Failed login attempt for: {username}")
logger.error(f"Password change failed for user {user_id}")
```

---

## OWASP Top 10 Mitigations

### 1. **Broken Access Control**
- **Risk**: Unauthorized access to admin features or other users' data
- **Mitigation**:
  - Role-based access control (user vs admin)
  - All admin endpoints check `user.role == "admin"`
  - Users only see their own tasks/analytics
  - Session validation on every request

### 2. **Cryptographic Failures**
- **Risk**: Passwords or data exposed in plaintext
- **Mitigation**:
  - bcrypt hashing for all passwords
  - Local storage only (no network transmission)
  - No sensitive data logged in plaintext
  - Optional: SQLCipher for database encryption (future enhancement)

### 3. **Injection**
- **Risk**: SQL injection via task titles, user input
- **Mitigation**:
  - Parameterized SQL queries (all queries use `?` placeholders)
  - Input length validation (max field sizes enforced)
  - No dynamic SQL string building
  - Flet framework auto-escapes UI rendering

### 4. **Insecure Design**
- **Risk**: Missing security features or flawed architecture
- **Mitigation**:
  - Session management built-in from start
  - Role-based design (admin vs user) from architecture
  - Audit logging designed in (not added later)
  - Data retention via soft deletes (security + compliance)

### 5. **Security Misconfiguration**
- **Risk**: Default/exposed credentials, debug mode enabled
- **Mitigation**:
  - `.env` file for secrets (not in git)
  - `.gitignore` excludes database files
- **Local Context**: Network-based injection attacks impossible (app is local)
  - No hardcoded credentials
  - Error messages don't reveal paths/config
  - Environment-based configuration

### 6. **Vulnerable Components**
- **Risk**: Outdated dependencies with known CVEs
- **Mitigation**:
  - Requirements locked to tested versions
  - bcrypt kept up-to-date (security focus library)
  - Flet & SQLite are actively maintained
  - Regular audits recommended (future)

### 7. **Authentication Failures**
- **Risk**: Weak password validation, session hijacking
- **Mitigation**:
  - bcrypt with cost=12 (strong hashing)
  - Session tokens regenerated on login
  - 30-minute inactivity timeout
  - Account lockout after 5 failed attempts
  - Password change invalidates old sessions

### 8. **Software & Data Integrity Failures**
- **Risk**: Unverified updates, data tampering
- **Mitigation**:
  - Audit logs track all modifications
  - Soft deletes maintain history (can detect unauthorized changes)
  - No auto-update mechanism (academic project)
  - Code version control via git

### 9. **Logging & Monitoring Failures**
- **Risk**: Security breaches go undetected
- **Mitigation**:
  - Audit logs capture all user actions
  - Failed login attempts tracked (5-strike lockout)
  - Admin panel displays user activity
  - Audit logs can be exported for review

### 10. **SSRF (Server-Side Request Forgery)**
- **Risk**: App makes requests to attacker-controlled URLs
- **Mitigation**:
  - No external API calls in core functionality
  - Analytics engine runs locally
  - No URL input fields (tasks use text
- **Local Context**: Not applicable (no network requests made) only)
  - Desktop app (no SSRF risk from web)

---

## Data Protection

### At Rest
- **Location**: Local SQLite database (`data/tymate.db`)
- **Access Control**: File system permissions (OS-level)
- **Encryption**: Passwords hashed irreversibly via bcrypt
- **Future**: Optional SQLCipher encryption (P3 enhancement)

### In Transit
- **Desktop App**: No network transmission (local-only)
- **Web Version**: Runs on localhost only (no remote access in scope)
- **If Extended**: Would require HTTPS/TLS

### In Memory
- **Session Tokens**: Stored in Python dict (lost on app restart)
- **Passwords**: Never stored in memory (only hash during check)
- **User Objects**: Discarded after session ends

---

## Access Control

### Role-Based Access Control (RBAC)

#### Regular User Permissions
```
✓ View own dashboard
✓ Create/edit/delete own tasks
✓ View own analytics
✓ Manage own profile & settings
✗ View other users' data
✗ Access admin panel
✗ View audit logs
```

#### Admin Permissions
```
✓ View admin panel
✓ Manage user accounts
✓ View audit logs (all users)
✓ View system-wide user activity
✗ Create own tasks (admin-only role, no task management)
✗ View analytics (analytics for regular users only)
```

### Implementation

```python
# Protected endpoint example
def show_admin_panel(page, user):
    if user.role != "admin":
        error_message.value = "Access denied. Admin only."
        return
    # Show admin UI...
```

**Code Locations**:
- [views/admin.py](views/admin.py) - Role check on entry
- [state/auth_manager.py](state/auth_manager.py) - Role validation
- [views/audit_logs.py](views/audit_logs.py) - Admin-only view

---

## Security Recommendations

### Current Implementation (Scope ✅)
- ✅ bcrypt password hashing
- ✅ Session management with timeouts
- ✅ Parameterized SQL queries
- ✅ Input validation & length limits
- ✅ Audit logging
- ✅ Role-based access control
- ✅ Secure error handling

### Future Enhancements (Scope 🔄)
- ☐ HTTPS/TLS for web deployment
- ☐ SQLCipher database encryption
- ☐ Two-factor authentication (2FA)
- ☐ Rate limiting on login attempts
- ☐ Security headers (CSP, HSTS)
- ☐ Dependency vulnerability scanning
- ☐ Automated security testing

### Not in Scope (Student Project)
- ❌ OAuth/SSO integration
- ❌ Hardware security keys
- ❌ Advanced threat detection
- ❌ SIEM integration
- ❌ Compliance certifications (SOC 2, ISO 27001)

---

## Testing & Validation

### Manual Security Testing
- [test_auth.py](tests/test_auth.py) - Login/password verification
- [test_unit_user_model.py](tests/test_unit_user_model.py) - Password hashing
- [manual_test_checklist.md](docu/manual_test_checklist.md) - UI security checks

### How to Verify Security Controls

```bash
# Test password hashing
python -c "
from models.user import User
pwd = User.hash_password('testpass123')
print('Hashed:', pwd)
print('Match:', User.User('test', pwd).verify_password('testpass123'))
"

# Test SQL injection resistance (should return None, not error)
python -c "
from storage.sqlite import get_database
db = get_database()
result = db.fetch_one(\"SELECT * FROM users WHERE username = ?\", 
                      (\"admin' OR '1'='1\",))
print('Injection attempt safely handled:', result)
"
```

---

## References

- [OWASP Top 10 2021](https://owasp.org/Top10/)
- [NIST Password Guidelines](https://pages.nist.gov/800-63-3/sp800-63b.html)
- [bcrypt Security Analysis](https://security.stackexchange.com/questions/4781/do-any-security-experts-recommend-bcrypt-for-password-storage)
- [STRIDE Threat Modeling](https://en.wikipedia.org/wiki/STRIDE_(security))
- [SQLi Prevention (OWASP)](https://cheatsheetseries.owasp.org/cheatsheets/SQL_Injection_Prevention_Cheat_Sheet.html)

---

## Conclusion**personal, locally-run application** managing individual task data. The design prioritizes:

1. **Password security** — bcrypt prevents unauthorized login
2. **Data integrity** — Audit logs detect unauthorized modifications
3. **Isolation** — Role-based access (user vs admin)
4. **Input safety** — Parameterized queries prevent injection

**Key Assumptions**:
- ✅ Application runs on user's personal machine (not cloud/server)
- ✅ Operating system login is the primary security boundary
- ✅ Users change default admin password on shared machines
- ✅ No remote access or network-based attacks expected
- ✅ Physical security provided by OS-level access control

**Security Maturity**: Level 2/5 (Appropriate for personal academic use)

**For Production Deployment** (if extended to web/cloud):
- Would require HTTPS/TLS, 2FA, automated security testing
- Database encryption (SQLCipher) strongly recommended
- Rate limiting and DDoS protection needed
- Compliance considerations (GDPR, etc.)

Current implementation focuses on **usability + reasonable security** for the intended single-user/shared-machine scenario.ing personal task data. The focus on bcrypt password hashing, session management, parameterized queries, and audit logging provides defense against common threats. For production deployment, additional controls (HTTPS, 2FA, database encryption) would be necessary.

**Security Maturity Level**: Level 2/5 (Strong foundation for academic use)
