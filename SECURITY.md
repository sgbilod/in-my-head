# Security Policy

## 🔒 Security at In My Head

We take the security of "In My Head" seriously. This document outlines our security policy and how to report vulnerabilities.

## 🛡️ Our Commitment

- **Privacy First**: All data processing happens locally by default
- **No Telemetry**: No tracking without explicit user consent
- **Open Source**: Complete transparency through open-source code
- **Regular Audits**: Periodic security reviews and updates
- **Dependency Management**: Automated vulnerability scanning

## 📊 Supported Versions

We actively support the following versions with security updates:

| Version | Supported          |
| ------- | ------------------ |
| 0.1.x   | :white_check_mark: |
| < 0.1   | :x:                |

## 🚨 Reporting a Vulnerability

If you discover a security vulnerability, please help us protect our users by following these steps:

### 1. **Do Not** Disclose Publicly

Please do not create a public GitHub issue for security vulnerabilities.

### 2. Report Privately

Send your report to: **security@inmyhead.ai**

Include in your report:

- Description of the vulnerability
- Steps to reproduce the issue
- Potential impact
- Suggested fix (if any)
- Your contact information

### 3. Response Timeline

- **24 hours**: We will acknowledge receipt of your report
- **7 days**: We will provide an initial assessment
- **30 days**: We aim to release a fix or mitigation
- **90 days**: We will publicly disclose the vulnerability (after fix)

### 4. Recognition

We value security researchers and will:

- Credit you in our security advisory (unless you prefer to remain anonymous)
- Add you to our Security Hall of Fame
- Consider bug bounties for critical vulnerabilities (when program is active)

## 🔐 Security Best Practices for Users

### For Developers

1. **Never commit secrets**:

   - Use `.env` files (add to `.gitignore`)
   - Use environment variables
   - Use secure vaults for API keys

2. **Keep dependencies updated**:

   ```bash
   npm audit fix
   pip-audit --fix
   ```

3. **Run security scans**:

   ```bash
   npm audit
   docker scan <image>
   ```

4. **Use strong authentication**:
   - Enable 2FA on all accounts
   - Use SSH keys for Git operations
   - Rotate API keys regularly

### For End Users

1. **Keep the application updated**:

   - Install updates promptly
   - Enable automatic updates if available

2. **Protect your data**:

   - Use strong passwords
   - Enable encryption features
   - Regular backups

3. **Be cautious with plugins**:

   - Only install plugins from trusted sources
   - Review permissions before installation
   - Keep plugins updated

4. **Use secure networks**:
   - Avoid public Wi-Fi for sensitive operations
   - Use VPN when necessary
   - Verify HTTPS connections

## 🛠️ Security Features

### Built-in Security

- **Local-First Architecture**: Data stays on your device
- **Optional Encryption**: End-to-end encryption for cloud sync
- **Audit Logs**: Track all data access
- **Secure APIs**: Rate limiting, authentication, authorization
- **Input Validation**: All user inputs sanitized
- **HTTPS Only**: Encrypted communication

### Security Scanning

We use the following tools:

- **Dependabot**: Automated dependency updates
- **Trivy**: Container vulnerability scanning
- **npm audit**: Node.js dependency security
- **Safety**: Python dependency security
- **OWASP ZAP**: Web application security testing

## 📋 Security Checklist

Before each release, we verify:

- [ ] All dependencies updated
- [ ] Security scans passed
- [ ] No hardcoded secrets
- [ ] Input validation implemented
- [ ] Authentication/authorization working
- [ ] Encryption enabled where needed
- [ ] Audit logs functioning
- [ ] Rate limiting configured
- [ ] HTTPS enforced
- [ ] Security headers set
- [ ] Error messages don't leak sensitive info
- [ ] Backups tested

## 🎓 Security Resources

### For Learning

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [OWASP Cheat Sheets](https://cheatsheetseries.owasp.org/)
- [Docker Security Best Practices](https://docs.docker.com/develop/security-best-practices/)
- [Node.js Security Best Practices](https://nodejs.org/en/docs/guides/security/)
- [Python Security](https://python.readthedocs.io/en/stable/library/security_warnings.html)

### Our Security Guides

- [Development Security Guide](docs/development/security-guide.md)
- [Deployment Security](docs/architecture/security-model.md)
- [API Security](docs/api/security.md)

## 📜 Compliance

We strive for compliance with:

- **GDPR**: General Data Protection Regulation (EU)
- **CCPA**: California Consumer Privacy Act (US)
- **OWASP**: Open Web Application Security Project standards
- **CWE**: Common Weakness Enumeration
- **CVE**: Common Vulnerabilities and Exposures

## 🏆 Security Hall of Fame

We thank the following security researchers for their responsible disclosure:

(List will be updated as vulnerabilities are reported and fixed)

## 📞 Contact

For security-related questions or concerns:

- **Email**: security@inmyhead.ai
- **PGP Key**: [Available on request]
- **Security Page**: https://inmyhead.ai/security

---

**Remember**: Security is everyone's responsibility. If you see something, say something!

_Last Updated: October 4, 2025_
