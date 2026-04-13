# Password Manager
This is a web-based password manager built with Flask.
The main goal of this project is to practice secure programming principles, especially in areas like authentication, encryption and handling sensitive data.

This project was developed as part of the course COMP.SEC.300.

## Features
- User registration and login
- Add, view and delete credentials

## Technologies
- Python (Flask)
- PostgreSQL (Flask-SQLAlchemy)
- Docker & Docker Compose
- GitHub Actions (CI/CD security pipeline)
    - SonarCloud (SAST)
    - Snyk (SCA) 
    - Trivy (container & filesystem scanning)
    - CycloneDX (SBOM generation)

## Setup Instructions
1. Clone the repository
2. Create a `.env` file:
    - POSTGRES_USER=myuser
    - POSTGRES_PASSWORD=password
    - POSTGRES_DB=mydb
    - DATABASE_URL=postgresql://myuser:password@db:5432/mydb
    - SECRET_KEY=secret_key
3. Build and start the containers:
    - docker compose build
    - docker compose up -d
4. Open the application:
    - http://localhost:5000


## Security Features
- Passwords hashed using Argon2id
- Credentials encrypted using AES-256-GCM
- CSRF protection enabled on all forms
- Secure session cookie configuration
- Access control enforced on all routes
- Session timeout after inactivity

## Most important limitations
- No 2FA or rate limiting
- No HTTPS -> secure cookie flag not enabled
- No unit/integration tests implemented
- Some vulnerabilities from base Docker image remain
- No autofill support (cannot be used across other applications)

## Notes
This project focuses on demonstrating secure programming practices rather than building a full production-ready password manager. Some features and improvements are intentionally left out due to scope and time constraints.