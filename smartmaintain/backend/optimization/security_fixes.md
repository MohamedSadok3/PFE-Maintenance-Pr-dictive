# Security Fixes - SmartMaintain

## ⚠️ CRITICAL - Apply Immediately

### 1. Fix Hardcoded SECRET_KEY

**Current Issue**: JWT secret is hardcoded in code
```python
# backend/shared/auth.py
SECRET_KEY = "dev-secret-key-change-in-production"
```

**Solution**:

1. Generate secure secret:
```bash
# On Linux/Mac
openssl rand -hex 32

# On Windows PowerShell
$bytes = New-Object byte[] 32
[System.Security.Cryptography.RandomNumberGenerator]::Create().GetBytes($bytes)
[System.BitConverter]::ToString($bytes).Replace("-","").ToLower()
```

2. Add to `.env`:
```bash
JWT_SECRET_KEY=<generated_secret_here>
```

3. Update `backend/shared/auth.py`:
```python
from shared.config import get_env

SECRET_KEY = get_env("JWT_SECRET_KEY")
if not SECRET_KEY:
    raise RuntimeError("JWT_SECRET_KEY must be set in environment")
```

4. Restart all services:
```bash
docker-compose restart
```

---

### 2. Add Rate Limiting

**Current Issue**: No protection against brute force attacks

**Solution**: Add Flask-Limiter

1. Install dependency:
```bash
# Add to backend/auth/requirements.txt
Flask-Limiter==3.5.0
```

2. Update `backend/auth/app.py`:
```python
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

app = Flask(__name__)

limiter = Limiter(
    app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="redis://redis:6379/1"
)

@app.route("/api/auth/login", methods=["POST"])
@limiter.limit("5 per minute")
def login():
    ...

@app.route("/api/auth/register-plant", methods=["POST"])
@limiter.limit("3 per hour")
def register_plant():
    ...
```

---

### 3. Improve Email Validation

**Current Issue**: Basic regex validation

**Solution**:

1. Install dependency:
```bash
# Add to backend/auth/requirements.txt
email-validator==2.1.0
```

2. Update `backend/auth/services/auth_service.py`:
```python
from email_validator import validate_email, EmailNotValidError

def login(email: str, password: str):
    try:
        # Validate email format
        valid = validate_email(email, check_deliverability=False)
        email = valid.normalized
    except EmailNotValidError as e:
        raise ValueError(f"Invalid email: {e}")
    
    # ... rest of login logic
```

---

### 4. Add CORS Whitelist Validation

**Current Issue**: CORS origins from environment without validation

**Solution** - Update `backend/gateway/app.py`:
```python
import re

ALLOWED_ORIGIN_PATTERNS = [
    r'^http://localhost:\d+$',
    r'^https://.*\.smartmaintain\.com$',
    r'^https://smartmaintain\.com$',
]

def validate_origin(origin):
    """Validate origin against whitelist patterns."""
    for pattern in ALLOWED_ORIGIN_PATTERNS:
        if re.match(pattern, origin):
            return True
    return False

# Use in CORS
CORS(app, 
     origins=lambda origin: validate_origin(origin),
     supports_credentials=True)
```

---

### 5. Add HTTPS Redirect (Production)

**Solution** - Add to `backend/gateway/app.py`:
```python
from flask import redirect, request

@app.before_request
def redirect_to_https():
    if not app.debug and request.url.startswith('http://'):
        url = request.url.replace('http://', 'https://', 1)
        return redirect(url, code=301)
```

---

### 6. Secure Cookie Settings

**Solution** - Update `backend/auth/services/auth_service.py`:
```python
def create_token(user_id, role):
    # ... existing code ...
    
    return {
        'token': token,
        'cookie_settings': {
            'httponly': True,      # Prevent XSS access
            'secure': True,        # HTTPS only
            'samesite': 'Strict',  # CSRF protection
            'max_age': 86400       # 24 hours
        }
    }
```

---

### 7. Add SQL Injection Protection

**Current Status**: ✅ Already protected (using parameterized queries)

**Verify**:
```python
# ✅ Good - Parameterized
cursor.execute(
    "SELECT * FROM users WHERE email = %s",
    (email,)
)

# ❌ Bad - String interpolation (NOT USED, but check)
cursor.execute(f"SELECT * FROM users WHERE email = '{email}'")
```

---

### 8. Add XSS Protection Headers

**Solution** - Add to `backend/gateway/app.py`:
```python
@app.after_request
def set_security_headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Content-Security-Policy'] = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline'; "
        "style-src 'self' 'unsafe-inline'; "
        "img-src 'self' data: https:; "
        "connect-src 'self' ws: wss:;"
    )
    return response
```

---

### 9. Password Policy Enforcement

**Solution** - Update `backend/auth/services/registration_service.py`:
```python
import re

def validate_password_strength(password):
    """Enforce strong password policy."""
    if len(password) < 12:
        raise ValueError("Password must be at least 12 characters")
    
    if not re.search(r'[A-Z]', password):
        raise ValueError("Password must contain uppercase letter")
    
    if not re.search(r'[a-z]', password):
        raise ValueError("Password must contain lowercase letter")
    
    if not re.search(r'[0-9]', password):
        raise ValueError("Password must contain number")
    
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        raise ValueError("Password must contain special character")
    
    return True

def register_plant(form_data):
    # ... existing code ...
    validate_password_strength(form_data['owner_password'])
    # ... rest of registration
```

---

### 10. Add Audit Logging

**Solution** - Create `backend/shared/audit_log.py`:
```python
import logging
from datetime import datetime
from typing import Optional

audit_logger = logging.getLogger('audit')

def log_auth_event(
    event_type: str,
    user_id: Optional[int],
    email: str,
    success: bool,
    ip_address: str,
    details: dict = None
):
    """Log authentication events for security audit."""
    audit_logger.info({
        'timestamp': datetime.utcnow().isoformat(),
        'event_type': event_type,
        'user_id': user_id,
        'email': email,
        'success': success,
        'ip_address': ip_address,
        'details': details or {}
    })

# Usage in login endpoint
from shared.audit_log import log_auth_event

def login(email, password):
    try:
        user = # ... authenticate ...
        log_auth_event('login', user['id'], email, True, request.remote_addr)
        return user
    except Exception as e:
        log_auth_event('login', None, email, False, request.remote_addr, {'error': str(e)})
        raise
```

---

## Security Checklist

### Critical (Do Now)
- [ ] Generate and set JWT_SECRET_KEY
- [ ] Add rate limiting to auth endpoints
- [ ] Improve email validation
- [ ] Add security headers

### Important (This Week)
- [ ] CORS whitelist validation
- [ ] Secure cookie settings
- [ ] Password policy enforcement
- [ ] Audit logging

### Recommended (This Month)
- [ ] HTTPS redirect in production
- [ ] Security penetration testing
- [ ] Dependency vulnerability scanning
- [ ] Regular security audits

---

## Testing Security Fixes

### 1. Test Rate Limiting
```bash
# Should block after 5 attempts in 1 minute
for i in {1..10}; do
  curl -X POST http://localhost:5000/api/auth/login \
    -H "Content-Type: application/json" \
    -d '{"email":"test@test.com","password":"wrong"}'
  sleep 2
done
```

### 2. Test JWT Secret
```bash
# Verify token uses new secret
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@smartmaintain.com","password":"admin123"}' \
  | jq -r '.token' \
  | cut -d. -f2 \
  | base64 -d \
  | jq
```

### 3. Test Security Headers
```bash
curl -I http://localhost:5000/health
# Should see X-Content-Type-Options, X-Frame-Options, etc.
```

---

## Monitoring Security

### Log Files to Monitor
```bash
# Authentication failures
tail -f logs/audit.log | grep '"success":false'

# Rate limit hits
tail -f logs/gateway.log | grep '429'

# Unusual access patterns
tail -f logs/auth.log | grep -E '(401|403)'
```

### Alerts to Configure
1. **5+ failed logins** from same IP in 5 minutes
2. **Rate limit exceeded** 10+ times in 1 hour
3. **New admin user created**
4. **JWT secret changed**
5. **Database password changed**

---

## Resources

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [Flask Security Best Practices](https://flask.palletsprojects.com/en/latest/security/)
- [JWT Best Practices](https://datatracker.ietf.org/doc/html/rfc8725)
