# Security Policy

ExamForge AI contains synthetic demo data only and intentionally excludes the operational question database and historical audit exports.

- Keep SECRET_KEY, GEMINI_API_KEY, database credentials and e-mail credentials outside Git.
- AI output is untrusted draft content: validate structure and require human review.
- Never auto-approve AI-generated items.
- Use authenticated access, CSRF protection and HTTPS in production.
- Do not publish real question banks, exams, faculty identifiers, student data or audit exports.
- Rotate any credential that has ever been committed to a public repository.

Report vulnerabilities privately through GitHub Security Advisories / Private Vulnerability Reporting.
