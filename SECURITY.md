# Security Policy

## Reporting Security Vulnerabilities

If you discover a security vulnerability in Aurex, please report it responsibly:

1. **Do not** open a public GitHub issue
2. Email the security team at: security@aurex.local (or contact system administrator)
3. Include:
   - Description of the vulnerability
   - Steps to reproduce
   - Potential impact
   - Suggested fix (if available)

We will acknowledge receipt within 48 hours and provide a timeline for resolution.

## Security Updates

### 2026-04-10: Dependency Security Patches (Updated)

**Status**: ✅ FIXED

#### Vulnerabilities Addressed

1. **FastAPI ReDoS Vulnerability (CVE-2024-24762)**
   - **Package**: fastapi
   - **Affected Version**: ≤ 0.109.0
   - **Fixed Version**: 0.110.0
   - **Severity**: Medium
   - **Impact**: Content-Type header Regular Expression Denial of Service (ReDoS)
   - **Resolution**: Updated from 0.104.1 to 0.110.0

2. **Pillow Out-of-Bounds Write in PSD Loading**
   - **Package**: Pillow
   - **Affected Version**: ≥ 10.3.0, < 12.1.1
   - **Fixed Version**: 12.1.1
   - **Severity**: Critical
   - **Impact**: Out-of-bounds write vulnerability when loading PSD (Photoshop) images
   - **Resolution**: Updated from 10.3.0 to 12.1.1
   - **Note**: Also fixes previous buffer overflow vulnerability from version 10.1.0

3. **python-jose Algorithm Confusion**
   - **Package**: python-jose
   - **Affected Version**: < 3.4.0
   - **Fixed Version**: 3.4.0
   - **Severity**: High
   - **Impact**: Algorithm confusion with OpenSSH ECDSA keys
   - **Resolution**: Updated from 3.3.0 to 3.4.0

4. **python-multipart Multiple Vulnerabilities**
   - **Package**: python-multipart
   - **Affected Version**: ≤ 0.0.6
   - **Fixed Version**: 0.0.22
   - **Severity**: High
   - **Issues**:
     - Arbitrary file write via non-default configuration
     - Denial of Service (DoS) via malformed multipart/form-data boundary
     - Content-Type header ReDoS
   - **Resolution**: Updated from 0.0.6 to 0.0.22

#### Action Taken

Updated `python-backend/requirements.txt` with patched versions. All installations from this point forward will use secure versions.

#### Deployment Impact

**For New Deployments**: No action needed, will use patched versions automatically.

**For Existing Deployments**: Update dependencies immediately:

```bash
cd /opt/aurex/python-backend
source venv/bin/activate
pip install --upgrade -r requirements.txt
sudo systemctl restart aurex-api
sudo systemctl restart aurex-celery-worker
```

#### Verification

After updating, verify versions:

```bash
pip list | grep -E "fastapi|Pillow|python-jose|python-multipart"
```

Expected output:
```
fastapi                   0.110.0
Pillow                    12.1.1
python-jose               3.4.0
python-multipart          0.0.22
```

## Security Best Practices

### 1. Dependency Management

- **Regular Updates**: Check for security updates monthly
- **Automated Scanning**: Use `pip-audit` or GitHub Dependabot
- **Pin Versions**: Use exact versions in requirements.txt (as we do)
- **Test Updates**: Test in staging before production

### 2. Environment Security

- **Never commit .env files** with real secrets
- **Use strong random keys** (32+ characters)
- **Rotate secrets** quarterly or after team member departures
- **Restrict file permissions**: `chmod 600 .env`

### 3. Network Security

- **Firewall Rules**: Only allow necessary ports
- **Internal APIs**: FastAPI should not be publicly accessible
- **HTTPS**: Use TLS/SSL in production (configure when ready)
- **VPN/Private Network**: Keep infrastructure on private network

### 4. Database Security

- **Separate Credentials**: Different passwords for app vs admin
- **Connection Restrictions**: PostgreSQL only accepts app server
- **Parameterized Queries**: All database access uses PDO/SQLAlchemy (never string concatenation)
- **Regular Backups**: Automated daily backups with retention policy

### 5. Authentication Security

- **Keycloak SSO**: Centralized authentication
- **Session Management**: Secure cookies, HttpOnly flag
- **CSRF Protection**: Token validation on state-changing requests
- **Role-Based Access**: Enforce permissions at both PHP and Python layers

### 6. Input Validation

- **File Uploads**: Validate type, size, content
- **API Requests**: Pydantic validation in FastAPI
- **SQL Injection**: Use parameterized queries (PDO, SQLAlchemy)
- **XSS Protection**: Escape output in templates

### 7. Monitoring & Logging

- **Audit Logs**: Track sensitive actions (logins, downloads, deletions)
- **Error Logging**: Capture and review errors regularly
- **Security Events**: Monitor for suspicious patterns
- **Log Retention**: Keep audit logs for compliance requirements

## Secure Development Guidelines

### For Python Backend

```python
# ✅ Good: Use Pydantic for validation
from pydantic import BaseModel, validator

class UploadRequest(BaseModel):
    filename: str
    
    @validator('filename')
    def validate_filename(cls, v):
        if '..' in v or '/' in v:
            raise ValueError('Invalid filename')
        return v

# ❌ Bad: No validation
filename = request.get('filename')  # Could be ../../etc/passwd
```

### For PHP Frontend

```php
// ✅ Good: Parameterized queries
$stmt = $pdo->prepare("SELECT * FROM users WHERE email = ?");
$stmt->execute([$email]);

// ❌ Bad: String concatenation
$result = $pdo->query("SELECT * FROM users WHERE email = '$email'");

// ✅ Good: Escape output
echo htmlspecialchars($userInput, ENT_QUOTES, 'UTF-8');

// ❌ Bad: Direct output
echo $userInput;
```

## Known Security Considerations

### Current State (Pre-Production)

- **HTTP Only**: System not configured for HTTPS yet (planned for production)
- **Internal Network**: Assumes servers on trusted internal network (192.168.1.x)
- **No Rate Limiting**: Not implemented yet (planned enhancement)
- **No WAF**: No Web Application Firewall (consider for production)

### Planned Security Enhancements

- [ ] Enable HTTPS with Let's Encrypt or commercial certificate
- [ ] Implement API rate limiting
- [ ] Add Web Application Firewall (WAF)
- [ ] Set up intrusion detection
- [ ] Implement security headers (HSTS, CSP)
- [ ] Add automated vulnerability scanning
- [ ] Set up security alerting

## Security Checklist for Deployment

Before going to production:

- [ ] All dependencies updated to patched versions
- [ ] Strong unique passwords for all services
- [ ] .env files secured with correct permissions
- [ ] Firewall rules configured
- [ ] PostgreSQL restricted to app server only
- [ ] HTTPS enabled (or scheduled)
- [ ] Keycloak using strong password policy
- [ ] Session timeout configured appropriately
- [ ] Audit logging enabled
- [ ] Backup procedures tested
- [ ] Security monitoring in place
- [ ] Incident response plan documented

## Compliance Considerations

Depending on your use case, you may need to consider:

- **GDPR**: If processing EU citizen data
- **PCI DSS**: If handling payment card data
- **SOC 2**: If providing service to enterprises
- **Industry-Specific**: Banking regulations, HIPAA, etc.

Consult with your legal/compliance team for specific requirements.

## Regular Security Tasks

### Monthly
- [ ] Check for dependency security updates
- [ ] Review audit logs for anomalies
- [ ] Verify backup procedures working

### Quarterly
- [ ] Rotate secrets and passwords
- [ ] Review user access and remove inactive accounts
- [ ] Update security documentation

### Annually
- [ ] Security audit/penetration testing
- [ ] Review and update security policies
- [ ] Security training for team

## Contact

For security-related questions:
- Security Team: security@aurex.local
- System Administrator: admin@aurex.local
- Emergency: [Contact information]

## Acknowledgments

We thank the security researchers and community members who responsibly disclose vulnerabilities:
- GitHub Security Advisory Database
- Python Package Index (PyPI) security team
- FastAPI, Pillow, python-jose, and python-multipart maintainers
