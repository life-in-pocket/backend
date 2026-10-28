# Pocket Backend

REST API for Pocket, a personal task and time-tracking app. Built with FastAPI, SQLAlchemy (async), and JWT authentication. Users register with email, verify their address via a link, and then manage their tasks and statistics.

## Features

- User registration with email verification
- JWT-based login (blocked until the email is verified)
- Transactional emails with Jinja2 templates (verification and welcome emails)
- Task management with per-day tracking
- Statistics: weekly, monthly and yearly aggregates

## Tech Stack

- Python 3.13
- FastAPI
- SQLAlchemy 2.x (async)
- Pydantic v2 and pydantic-settings
- fastapi-mail (SMTP)
- Jinja2 for email templates
- Uvicorn

### 📁 Project Structure

```text
backend/
├── app/
│   ├── core/                  # Core configurations, security utils (JWT, hashing), mail client
│   ├── task/                  # Task domain: models, schemas, endpoints, business logic
│   ├── user/                  # User domain: models, schemas, auth/2FA routes, service layer
│   ├── templates/             # Jinja2 email templates for 2FA verification & alerts
│   ├── database.py            # SQLAlchemy async/sync engine, sessionmaker, Base model
│   ├── dependencies.py        # Shared FastAPI dependencies (auth guards, DB sessions)
│   └── main.py                # FastAPI application factory, middleware, router aggregation
├── .env.example               # Environment variables template
└── requirements.txt           # Project dependencies
```

## Getting Started

### Prerequisites

- Python 3.13+
- A PostgreSQL (or your configured) database
- An SMTP provider for development, such as [Mailtrap](https://mailtrap.io)

### Installation

```bash
cd backend
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Configuration

Copy the example file and fill in your values:

```bash
cp .env.example .env
```

| Variable | Description |
|---|---|
| `DATABASE_URL` | Database connection string |
| `SECRET_KEY` | Key used to sign JWT tokens |
| `FRONTEND_URL` | Frontend origin, used in email links |
| `MAIL_SERVER` | SMTP host |
| `MAIL_PORT` | SMTP port (587 with STARTTLS, 2525 for Mailtrap) |
| `MAIL_USERNAME` | SMTP username |
| `MAIL_PASSWORD` | SMTP password |
| `MAIL_FROM` | Sender address |
| `MAIL_FROM_NAME` | Sender display name |

### Running

```bash
uvicorn app.main:app --reload
```

The API is available at `http://localhost:8000`. Interactive docs are at `http://localhost:8000/docs`.

## API Overview

| Method | Endpoint | Description |
|---|---|---|
| POST | `/auth/register` | Create an account and send a verification email |
| POST | `/auth/verify` | Verify email with a token from the link |
| POST | `/auth/login` | Get an access token (requires verified email) |

## Email Verification Flow

1. The user registers. A random token is generated, its SHA-256 hash is stored, and the plain token is sent by email.
2. The user opens the link, which points to the frontend. The frontend sends the token to `POST /auth/verify`.
3. The backend matches the hash, checks expiry, marks the user as verified, and clears the token.
4. A welcome email is sent in the background.

Tokens are single-use and expire after 24 hours.

## Testing Emails Locally

Use a Mailtrap sandbox during development so no real address receives test mail. Set the SMTP credentials from your sandbox inbox in `.env`.