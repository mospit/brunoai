# Bruno AI Server - Security Features

This document outlines the comprehensive security and rate-limiting features implemented in the Bruno AI Server.

## 🔒 Security Features Implemented

### 1. Enhanced Rate Limiting

#### Authentication Rate Limiting (5 attempts/15 min per IP)
- **Strict Auth Limits**: 5 failed authentication attempts per 15 minutes per IP address
- **General Rate Limits**: 60 requests per minute for general endpoints
- **Auth Endpoint Limits**: 10 requests per minute for authentication endpoints
- **Automatic Reset**: Rate limits automatically reset after the time window expires
- **Security Logging**: All rate limit violations are logged with client details

#### Rate Limiting Headers
```
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 45
X-RateLimit-Reset: 1640995200
X-RateLimit-Type: auth (for authentication endpoints)
```

### 2. CSRF Protection

#### CSRF Token Management
- **Secure Token Generation**: HMAC-SHA256 based tokens with session IDs
- **1-Hour Token Lifetime**: Tokens expire automatically for security
- **Cookie-Based Distribution**: CSRF tokens delivered via secure cookies
- **Header Validation**: Requires `X-CSRF-Token` header for state-changing requests

#### CSRF Endpoints
- `GET /auth/csrf-token` - Get CSRF token for session
- Automatic validation for POST, PUT, PATCH, DELETE requests

#### CSRF Exemptions
- Bearer token authentication (considered sufficient CSRF protection)
- Safe HTTP methods (GET, HEAD, OPTIONS)
- Authentication endpoints (login, register, refresh)

### 3. Secure Cookie Handling

#### HttpOnly Cookies with HTTPS Enforcement
- **HttpOnly Cookies**: Authentication cookies cannot be accessed via JavaScript
- **Secure Flag**: Cookies only sent over HTTPS in production
- **SameSite=Strict**: Maximum CSRF protection
- **Path Restrictions**: Refresh tokens restricted to `/auth/refresh` path

#### Cookie Types
```javascript
brunoai_access_token    // 15-minute expiration, HttpOnly
brunoai_refresh_token   // 7-day expiration, HttpOnly, path-restricted
brunoai_csrf_token      // 15-minute expiration, accessible to JS
brunoai_session         // 7-day expiration, HttpOnly
```

### 4. Enhanced Input Sanitization

#### Comprehensive Input Validation
- **SQL Injection Protection**: Pattern-based detection and blocking
- **XSS Prevention**: HTML tag stripping and dangerous pattern detection
- **Control Character Removal**: Null bytes and control characters filtered
- **Length Validation**: Configurable maximum lengths per field type
- **URL Scheme Validation**: Only safe URL schemes allowed

#### Sanitization Features
- Email format validation and normalization
- HTML tag removal (with safe tag allowlist option)
- Unicode normalization
- Whitespace trimming and normalization

### 5. Security Logging & Monitoring

#### Structured Security Events
- **Authentication Attempts**: Success/failure with client details
- **Rate Limit Violations**: IP, user agent, and endpoint information
- **CSRF Violations**: Token validation failures
- **Suspicious Activity**: Malicious input attempts and security errors

#### Log Format
```json
{
  "event": "auth_attempt",
  "success": false,
  "email": "user@example.com",
  "client_ip": "192.168.1.100",
  "user_agent": "Mozilla/5.0...",
  "timestamp": "2024-01-15T10:30:00Z",
  "reason": "invalid_password"
}
```

#### Password Security
- **Never Logged**: Passwords are never written to logs or debug output
- **Secure Hashing**: bcrypt with 12 rounds for password storage
- **Validation Without Logging**: Password requirements checked without exposure

### 6. Comprehensive Security Headers

#### Production Security Headers
```
Strict-Transport-Security: max-age=31536000; includeSubDomains; preload
Content-Security-Policy: default-src 'self'; script-src 'self'; ...
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
X-XSS-Protection: 1; mode=block
Referrer-Policy: strict-origin-when-cross-origin
Cross-Origin-Embedder-Policy: require-corp
Cross-Origin-Opener-Policy: same-origin
Cross-Origin-Resource-Policy: same-origin
Permissions-Policy: camera=(), microphone=(), geolocation=(), ...
```

#### Development vs Production
- **Development**: Relaxed CSP for debugging tools
- **Production**: Strict CSP and HSTS headers
- **Environment Detection**: Automatic configuration based on settings

### 7. Token Security

#### JWT Token Management
- **Short-Lived Access Tokens**: 15-minute expiration
- **Longer Refresh Tokens**: 7-day expiration with revocation capability
- **Secure Storage**: Refresh tokens stored in database with revocation tracking
- **Automatic Cleanup**: Expired tokens automatically purged

#### Token Revocation
- **Individual Revocation**: Single refresh token invalidation
- **Bulk Revocation**: All user tokens on password change/security events
- **Logout Cleanup**: All tokens revoked on explicit logout

## 🛡️ Security Middleware Stack

### Middleware Order (Execution Order)
1. **CORSMiddleware** - Handle cross-origin requests
2. **SecurityHeadersMiddleware** - Add security headers
3. **AuthenticationMiddleware** - Handle auth and rate limiting
4. **Application Routes** - Your API endpoints

### Middleware Configuration
```python
# Security headers with environment-specific CSP
app.add_middleware(SecurityHeadersMiddleware)

# Authentication with rate limiting
app.add_middleware(AuthenticationMiddleware)
```

## 📝 Usage Examples

### Client Implementation

#### Getting CSRF Token
```javascript
// Get CSRF token
const response = await fetch('/auth/csrf-token');
const { csrf_token } = await response.json();

// Use in subsequent requests
await fetch('/api/protected-endpoint', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'X-CSRF-Token': csrf_token
  },
  body: JSON.stringify(data)
});
```

#### Cookie-Based Authentication
```javascript
// Login (sets secure cookies automatically)
const response = await fetch('/auth/login', {
  method: 'POST',
  credentials: 'include', // Important for cookies
  headers: {
    'Content-Type': 'application/json',
    'X-CSRF-Token': csrf_token
  },
  body: JSON.stringify({ email, password })
});

// Subsequent requests automatically include cookies
await fetch('/api/protected-endpoint', {
  credentials: 'include'
});
```

#### Bearer Token Authentication
```javascript
// Login and store tokens
const { access_token, refresh_token } = await response.json();

// Use bearer token (no CSRF required)
await fetch('/api/protected-endpoint', {
  headers: {
    'Authorization': `Bearer ${access_token}`
  }
});
```

### Server-Side Security

#### Input Sanitization
```python
from bruno_ai_server.services.security_service import security_service

# Automatic sanitization
sanitized_data = security_service.sanitize_request_data({
    "email": user_input.email,
    "name": user_input.name,
    "url": user_input.website
})
```

#### Security Logging
```python
# Log authentication attempt
security_service.logger.log_auth_attempt(
    request, email, success=False, reason="invalid_password"
)

# Log suspicious activity
security_service.logger.log_suspicious_activity(
    request, "malicious_input", {"pattern": "detected_pattern"}
)
```

## ⚠️ Security Considerations

### Production Deployment
1. **HTTPS Required**: All security features assume HTTPS in production
2. **Environment Variables**: Ensure `ENVIRONMENT=production` is set
3. **Secret Management**: Use strong, randomly generated secrets
4. **Database Security**: Secure database connections and access
5. **Network Security**: Proper firewall and network segmentation

### Rate Limiting Notes
- Rate limits are per-IP address and stored in memory
- Consider Redis for distributed deployments
- Monitor rate limit logs for potential DDoS attempts
- Adjust limits based on legitimate usage patterns

### CSRF Protection
- Required for cookie-based authentication only
- Bearer token requests are exempt (tokens provide CSRF protection)
- Ensure CSRF tokens are included in AJAX requests
- Mobile apps typically use Bearer tokens (no CSRF needed)

## 🔧 Configuration

### Environment Variables
```bash
# Required for security
APP_SECRET_KEY=your-super-secret-key-here
JWT_SECRET=your-jwt-secret-here
ENVIRONMENT=production  # Enables strict security

# Optional security settings
ENABLE_CSRF=true
RATE_LIMIT_ENABLED=true
```

### Security Service Configuration
```python
# Customize rate limits
DEFAULT_RATE_LIMIT = 60      # requests per minute
AUTH_RATE_LIMIT = 10         # auth requests per minute
AUTH_ATTEMPT_LIMIT = 5       # failed attempts per 15 minutes

# Token lifetimes
ACCESS_TOKEN_EXPIRE_MINUTES = 15
REFRESH_TOKEN_EXPIRE_DAYS = 7

# Password requirements
MIN_PASSWORD_LENGTH = 8
MAX_PASSWORD_LENGTH = 128
```

## 🚨 Security Monitoring

### Key Metrics to Monitor
- Authentication failure rates per IP
- Rate limit violations
- CSRF token validation failures
- Suspicious input patterns
- Token usage and expiration patterns

### Alerting Recommendations
- Alert on > 5 failed logins from single IP in 5 minutes
- Alert on repeated CSRF violations
- Alert on potential injection attempts
- Monitor for unusual token usage patterns

## 📚 Security Standards Compliance

### Standards Addressed
- **OWASP Top 10**: Injection, Broken Authentication, XSS, etc.
- **NIST Cybersecurity Framework**: Protect, Detect, Respond
- **Industry Best Practices**: Secure coding, defense in depth

### Security Features Summary
✅ Rate limiting (5 attempts/15 min per IP)  
✅ CSRF protection for cookie-based auth  
✅ Comprehensive input sanitization  
✅ Passwords never logged  
✅ Secure HttpOnly cookies  
✅ HTTPS enforcement in production  
✅ Security headers (HSTS, CSP, etc.)  
✅ Structured security logging  
✅ Token management and revocation  
✅ SQL injection protection  
✅ XSS prevention  
✅ Secure session management  

This implementation provides enterprise-grade security suitable for production deployment while maintaining developer-friendly APIs and comprehensive monitoring capabilities.
