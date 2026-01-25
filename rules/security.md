# Security Requirements

These rules apply to ALL files in the project.

## OWASP Top 10 Prevention

### Injection (SQL, Command, XSS)
- Use Django ORM - never raw SQL with user input
- Use parameterized queries if raw SQL is necessary
- Escape user input in templates (Django auto-escapes)
- Sanitize HTML content with bleach or similar

### Broken Authentication
- Use django-allauth for authentication flows
- Implement rate limiting on auth endpoints
- Never log passwords or tokens

### Sensitive Data Exposure
- Never commit `.env` files or secrets
- Use environment variables for credentials
- Store API keys in settings, not code

### Security Misconfiguration
- Keep DEBUG=False in production
- Set proper CORS and CSRF settings
- Review django-security-check recommendations

## File Handling

### Sensitive Files - NEVER Read or Commit
- `.env`, `.env.*` - Environment secrets
- `**/secrets/**` - Secret files
- `**/credentials/**` - Credential files
- `*.pem`, `*.key` - Private keys
- `serviceAccountKey.json` - Service account keys

### Safe Alternatives
- Use `.env.example` for documentation
- Reference secrets by environment variable name
- Document required variables in README

## Code Review Checklist

Before completing any feature:
- [ ] No hardcoded secrets or API keys
- [ ] User input is validated and sanitized
- [ ] Database queries use ORM or parameterized queries
- [ ] Authentication/authorization checks are in place
- [ ] Rate limiting applied to sensitive endpoints
- [ ] Error messages don't leak sensitive information

## Django-Specific Security

```python
# Good: Use ORM
User.objects.filter(email=user_input)

# Bad: Raw SQL with user input
cursor.execute(f"SELECT * FROM users WHERE email = '{user_input}'")

# Good: Parameterized raw SQL (if necessary)
cursor.execute("SELECT * FROM users WHERE email = %s", [user_input])
```

## React-Specific Security

```javascript
// Good: React auto-escapes
<div>{userContent}</div>

// Bad: Bypasses escaping
<div dangerouslySetInnerHTML={{__html: userContent}} />

// If you must use dangerouslySetInnerHTML, sanitize first
import DOMPurify from 'dompurify';
<div dangerouslySetInnerHTML={{__html: DOMPurify.sanitize(userContent)}} />
```
