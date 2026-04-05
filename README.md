# Finance Data Processing API

A production-ready REST API for managing personal or organizational finances. Built with **FastAPI**, **PostgreSQL**, and **Redis** using **Clean Architecture** principles.

---

## Table of Contents

1. [Quick Start](#quick-start)
2. [Architecture](#architecture)
3. [System Design](#system-design)
4. [Roles and Permissions](#roles-and-permissions)
5. [API Reference](#api-reference)
   - [Authentication](#authentication)
   - [Users](#users)
   - [Financial Records](#financial-records)
   - [Categories](#categories)
   - [Dashboard](#dashboard)
   - [Health](#health)
6. [Request / Response Schemas](#request--response-schemas)
7. [Error Handling](#error-handling)
8. [Environment Variables](#environment-variables)

---

## Quick Start

### Prerequisites
- Docker Desktop

### Run the application

```bash
# Clone and enter the project
cd Finance_Data_Processing

# Start everything (database, redis, migrations, seed, api)
docker compose up --build
```

The API will be available at:
- **API base**: `http://localhost:8000/api/v1`
- **Interactive docs (Swagger)**: `http://localhost:8000/docs`
- **Alternative docs (ReDoc)**: `http://localhost:8000/redoc`

### Seed the database (permissions, roles, categories)

After the containers are running, run the seed script once manually:

```bash
docker exec finance_data_processing-api-1 python -m scripts.seed
```

This will create:
- 14 permissions (`records:create`, `users:read`, etc.)
- 3 roles (admin, analyst, viewer) with correct permission sets
- 13 system categories (Salary, Housing, Food & Dining, etc.)

### Create your first admin user

```bash
# 1. Register a user
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@example.com","password":"Admin123!","full_name":"Admin User"}'

# 2. Open a DB shell and assign the admin role
docker exec -it finance_data_processing-db-1 psql -U finance -d finance_db

# Inside psql:
INSERT INTO user_roles (user_id, role_id)
SELECT u.id, r.id FROM users u, roles r
WHERE u.email = 'admin@example.com' AND r.name = 'admin';
\q

# 3. Login
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@example.com","password":"Admin123!"}'
```

You will receive an `access_token`. Use it as a Bearer token in all subsequent requests:
```
Authorization: Bearer <access_token>
```

---

## Architecture

This project uses **Clean Architecture** — the code is split into four layers that only depend inward:

```
┌─────────────────────────────────────────┐
│           API / Interface Layer          │  ← HTTP routes, request/response schemas
│  app/api/  app/middleware/  app/main.py  │
├─────────────────────────────────────────┤
│           Application Layer             │  ← Business logic (use cases, DTOs)
│         app/application/                │
├─────────────────────────────────────────┤
│             Domain Layer                │  ← Core entities, value objects, rules
│           app/domain/                   │
├─────────────────────────────────────────┤
│         Infrastructure Layer            │  ← Database, Redis, JWT (concrete details)
│        app/infrastructure/              │
└─────────────────────────────────────────┘
```

**Key rule**: Each layer only imports from the layer directly below it. The domain layer never knows about the database. The application layer never knows about FastAPI.

### Folder Structure

```
app/
├── api/
│   ├── schemas/        # Pydantic request/response models
│   └── v1/             # Route handlers (auth, users, records, categories, roles, dashboard)
├── application/
│   └── use_cases/      # One file per business operation (login, create_record, etc.)
├── core/
│   ├── config.py       # Settings loaded from .env
│   ├── containers.py   # Dependency injection wiring
│   ├── dependencies.py # FastAPI auth dependencies
│   └── exceptions.py   # Custom error hierarchy
├── domain/
│   ├── entities/       # User, FinancialRecord, Category, Role, Permission, AuditLog
│   ├── value_objects/  # Email, Password, Money, DateRange
│   └── repositories/   # Abstract interfaces (no implementation)
├── infrastructure/
│   ├── database/       # SQLAlchemy models, session, Unit of Work
│   ├── repositories/   # Concrete DB implementations
│   ├── redis/          # Cache service (Redis)
│   └── security/       # JWT token service
├── middleware/
│   ├── request_id.py   # Injects X-Request-ID header
│   └── logging.py      # Structured JSON logging per request
└── main.py             # FastAPI app factory
```

---

## System Design

### Technology Stack

| Component | Technology |
|---|---|
| API Framework | FastAPI (async) |
| Database | PostgreSQL 16 |
| Cache / Token blacklist | Redis 7 |
| ORM | SQLAlchemy 2.x async |
| Migrations | Alembic |
| Authentication | JWT (HS256) — access + refresh tokens |
| Password hashing | bcrypt via passlib |
| Logging | structlog (JSON) |
| Server | Gunicorn + UvicornWorker (4 workers) |
| Containerization | Docker + Docker Compose |

### Authentication Flow

```
Client                          API
  │                              │
  │── POST /auth/login ─────────►│
  │                              │  Verify password
  │                              │  Issue access_token (15 min JWT)
  │                              │  Issue refresh_token (7 days, stored as hash in DB)
  │◄── { access_token, refresh_token } ──│
  │                              │
  │── GET /records ─────────────►│  Authorization: Bearer <access_token>
  │                              │  Decode JWT → check permissions
  │◄── records data ─────────────│
  │                              │
  │── POST /auth/refresh ────────►│  Send refresh_token
  │                              │  Rotate: revoke old, issue new pair
  │◄── { new access_token, new refresh_token } ──│
  │                              │
  │── POST /auth/logout ─────────►│  Blacklist access token JTI in Redis
  │                              │  Revoke refresh token in DB
  │◄── { message: "Logged out" } ─│
```

### Data Flow for a Request

```
HTTP Request
    │
    ▼
Middleware (Request ID → Logging)
    │
    ▼
Route Handler (app/api/v1/)
    │  validates input via Pydantic schema
    ▼
Use Case (app/application/use_cases/)
    │  pure business logic, no framework code
    ▼
Repository / Service (app/infrastructure/)
    │  talks to PostgreSQL or Redis
    ▼
Database / Cache
```

### Database Schema (simplified)

```
users
  id, email, hashed_password, full_name, status, is_active
  └── user_roles (user_id, role_id)
        └── roles (id, name, description)
              └── role_permissions (role_id, permission_id)
                    └── permissions (id, resource, action)

financial_records
  id, user_id, amount, record_type, category_id, record_date, notes
  └── categories (id, name, category_type, is_system)

refresh_tokens
  id, user_id, token_hash, expires_at, revoked

audit_logs
  id, actor_id, action, resource, resource_id, before, after, request_id, status
```

---

## Roles and Permissions


| Role | What they can do |
|---|---|
| **viewer** | Read records, categories, dashboard |
| **analyst** | viewer + create/update/delete their own records |
| **admin** | Full access — manage users, roles, categories, all records |

### Permission Codenames

| Codename | Description |
|---|---|
| `records:create` | Create financial records |
| `records:read` | View financial records |
| `records:update` | Edit financial records |
| `records:delete` | Delete financial records |
| `categories:create` | Create categories |
| `categories:read` | View categories |
| `categories:update` | Edit categories |
| `categories:delete` | Delete categories |
| `users:create` | Create users |
| `users:read` | View users |
| `users:update` | Update users / assign roles |
| `users:delete` | Delete users |
| `roles:create` | Create roles |
| `roles:read` | View roles |
| `roles:update` | Edit roles / assign permissions |
| `roles:delete` | Delete roles |
| `dashboard:read` | Access dashboard summaries |

---

## API Reference

All endpoints are prefixed with `/api/v1`. All protected endpoints require:
```
Authorization: Bearer <access_token>
```

---

### Authentication

#### Register
```
POST /api/v1/auth/register
```
Create a new user account. New users have no role by default — an admin must assign one.

**Request body:**
```json
{
  "email": "user@example.com",
  "password": "MyPassword123!",
  "full_name": "John Doe"
}
```

**Response (201):**
```json
{
  "id": "uuid",
  "email": "user@example.com",
  "full_name": "John Doe",
  "status": "active",
  "roles": [],
  "created_at": "2026-04-05T10:00:00Z"
}
```

---

#### Login
```
POST /api/v1/auth/login
```
Returns an access token and a refresh token.

**Request body:**
```json
{
  "email": "user@example.com",
  "password": "MyPassword123!"
}
```

**Response (200):**
```json
{
  "access_token": "eyJhbGci...",
  "refresh_token": "eyJhbGci...",
  "token_type": "bearer"
}
```

---

#### Refresh Token
```
POST /api/v1/auth/refresh
```
Exchange a refresh token for a new access token + refresh token pair. The old refresh token is invalidated.

**Request body:**
```json
{
  "refresh_token": "eyJhbGci..."
}
```

---

#### Logout
```
POST /api/v1/auth/logout
```
Requires: `Authorization: Bearer <access_token>`

Blacklists the current access token and revokes the refresh token.

**Request body:**
```json
{
  "refresh_token": "eyJhbGci..."
}
```

---

### Users

> Requires `users:read` / `users:create` / `users:update` / `users:delete` permissions (admin only by default)

#### List users
```
GET /api/v1/users?page=1&page_size=20&search=john&include_deleted=false
```

#### Get a user
```
GET /api/v1/users/{user_id}
```

#### Create a user
```
POST /api/v1/users
```
```json
{
  "email": "newuser@example.com",
  "password": "Password123!",
  "full_name": "New User",
  "role_names": ["analyst"]
}
```

#### Update a user
```
PATCH /api/v1/users/{user_id}
```
```json
{
  "full_name": "Updated Name"
}
```

#### Delete a user (soft delete)
```
DELETE /api/v1/users/{user_id}
```

#### Change user status (activate / deactivate)
```
PATCH /api/v1/users/{user_id}/status
```
```json
{
  "is_active": false
}
```

#### Assign a role to a user
```
POST /api/v1/users/{user_id}/roles
```
```json
{
  "role_id": "uuid-of-role"
}
```

#### Remove a role from a user
```
DELETE /api/v1/users/{user_id}/roles/{role_id}
```

---

### Financial Records

> `records:read` — viewer, analyst, admin
> `records:create` / `records:update` / `records:delete` — analyst, admin

#### List records (with filters)
```
GET /api/v1/records
```

Query parameters:

| Parameter | Type | Description |
|---|---|---|
| `page` | int | Page number (default: 1) |
| `page_size` | int | Items per page (default: 20) |
| `record_type` | string | `income` or `expense` |
| `category_id` | UUID | Filter by category |
| `date_from` | date | Start date (YYYY-MM-DD) |
| `date_to` | date | End date (YYYY-MM-DD) |
| `search` | string | Full-text search on notes |
| `user_id` | UUID | Filter by user (admin only) |

**Example:**
```
GET /api/v1/records?record_type=expense&date_from=2026-01-01&date_to=2026-03-31&page=1
```

#### Get a single record
```
GET /api/v1/records/{record_id}
```

#### Create a record
```
POST /api/v1/records
```
```json
{
  "amount": 1500.00,
  "record_type": "income",
  "category_id": "uuid-of-category",
  "record_date": "2026-04-05",
  "notes": "April salary"
}
```

**Response (201):**
```json
{
  "id": "uuid",
  "amount": 1500.00,
  "record_type": "income",
  "category_id": "uuid",
  "category_name": "Salary",
  "record_date": "2026-04-05",
  "notes": "April salary",
  "created_at": "2026-04-05T10:00:00Z"
}
```

#### Update a record
```
PATCH /api/v1/records/{record_id}
```
Send only the fields you want to change:
```json
{
  "amount": 1600.00,
  "notes": "April salary (updated)"
}
```

#### Delete a record (soft delete)
```
DELETE /api/v1/records/{record_id}
```

---

### Categories

> `categories:read` — all roles
> `categories:create` / `categories:update` / `categories:delete` — admin only

13 system categories are pre-seeded (Salary, Housing, Food & Dining, etc.). You can also create custom ones.

#### List categories
```
GET /api/v1/categories?category_type=expense&page=1&page_size=50
```

| Parameter | Values |
|---|---|
| `category_type` | `income`, `expense`, `both` |
| `include_inactive` | `true` / `false` |

#### Get a category
```
GET /api/v1/categories/{category_id}
```

#### Create a category
```
POST /api/v1/categories
```
```json
{
  "name": "Side Business",
  "category_type": "income",
  "description": "Income from side projects"
}
```

#### Update a category
```
PATCH /api/v1/categories/{category_id}
```
```json
{
  "name": "Freelance Work",
  "is_active": true
}
```

#### Delete a category
```
DELETE /api/v1/categories/{category_id}
```

---

### Dashboard

> Requires `dashboard:read` permission — viewer, analyst, admin

All dashboard endpoints accept optional filters:

| Parameter | Description |
|---|---|
| `user_id` | Filter data for a specific user (admin only) |
| `date_from` | Start date (YYYY-MM-DD) |
| `date_to` | End date (YYYY-MM-DD) |

#### Financial summary
```
GET /api/v1/dashboard/summary?date_from=2026-01-01&date_to=2026-03-31
```
**Response:**
```json
{
  "total_income": 4500.00,
  "total_expense": 2100.00,
  "net_balance": 2400.00,
  "total_records": 23,
  "cached": false
}
```

#### Category totals
```
GET /api/v1/dashboard/categories?date_from=2026-01-01
```
**Response:**
```json
[
  {
    "category_id": "uuid",
    "category_name": "Salary",
    "record_type": "income",
    "total": 3000.00,
    "count": 2
  },
  {
    "category_id": "uuid",
    "category_name": "Housing",
    "record_type": "expense",
    "total": 800.00,
    "count": 1
  }
]
```

#### Trends (monthly or weekly)
```
GET /api/v1/dashboard/trends?period=monthly&limit=6
```

| Parameter | Values | Default |
|---|---|---|
| `period` | `monthly`, `weekly` | `monthly` |
| `limit` | number | 12 |

**Response:**
```json
[
  { "period": "2026-03", "record_type": "income", "total": 1500.00, "count": 1 },
  { "period": "2026-03", "record_type": "expense", "total": 700.00, "count": 5 }
]
```

#### Recent activity
```
GET /api/v1/dashboard/recent?limit=10
```
Returns the most recent financial records.

---

### Health

#### Health check
```
GET /api/v1/health
```
No authentication required.

**Response (200):**
```json
{
  "status": "ok"
}
```

---

## Request / Response Schemas

### Paginated Response
All list endpoints return this structure:
```json
{
  "items": [...],
  "total": 100,
  "page": 1,
  "page_size": 20,
  "pages": 5
}
```

### Success Response
```json
{
  "message": "Operation successful"
}
```

### record_type values
| Value | Meaning |
|---|---|
| `income` | Money coming in |
| `expense` | Money going out |

### category_type values
| Value | Meaning |
|---|---|
| `income` | For income records only |
| `expense` | For expense records only |
| `both` | Can be used for either |

---

## Error Handling

All errors return a consistent JSON structure:

```json
{
  "detail": "Human readable error message"
}
```

### HTTP Status Codes

| Code | Meaning | When |
|---|---|---|
| `200` | OK | Successful GET / PATCH |
| `201` | Created | Successful POST |
| `400` | Bad Request | Invalid input |
| `401` | Unauthorized | Missing or invalid token |
| `403` | Forbidden | Token valid but insufficient permissions |
| `404` | Not Found | Resource does not exist |
| `409` | Conflict | Duplicate (e.g. email already registered) |
| `422` | Unprocessable | Pydantic validation failed (missing/wrong fields) |
| `500` | Server Error | Unexpected error |

### Example 422 (validation error)
```json
{
  "detail": [
    { "loc": ["body", "email"], "msg": "value is not a valid email address" },
    { "loc": ["body", "password"], "msg": "field required" }
  ]
}
```

---

## Environment Variables

Stored in `.env` (never committed to git):

| Variable | Description | Example |
|---|---|---|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql+asyncpg://finance:finance@db:5432/finance_db` |
| `REDIS_URL` | Redis connection string | `redis://redis:6379/0` |
| `JWT_SECRET_KEY` | Secret for signing JWTs | 64-char hex string |
| `JWT_ALGORITHM` | JWT algorithm | `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Access token lifetime | `15` |
| `REFRESH_TOKEN_EXPIRE_DAYS` | Refresh token lifetime | `7` |
| `POSTGRES_USER` | DB username | `finance` |
| `POSTGRES_PASSWORD` | DB password | `finance` |
| `POSTGRES_DB` | DB name | `finance_db` |
| `APP_ENV` | Environment name | `development` |
| `DEBUG` | Enable debug mode | `false` |

To generate a secure `JWT_SECRET_KEY`:
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```
