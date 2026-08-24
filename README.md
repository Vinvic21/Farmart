# Farmart
# Farmart Backend

Farmart is an e-commerce platform that lets farmers list and sell farm animals directly to buyers, cutting out middlemen. This is the Flask + PostgreSQL backend that powers the Farmart API.

## Tech Stack

- **Framework:** Flask 3.0
- **Database:** PostgreSQL
- **ORM:** Flask-SQLAlchemy
- **Migrations:** Flask-Migrate (Alembic)
- **Serialization:** Flask-Marshmallow / Marshmallow-SQLAlchemy
- **Auth:** Flask-JWT-Extended
- **Testing:** Pytest
- **Fake data:** Faker
- **Deployment:** Render / Railway
- **CI/CD:** GitHub Actions

## Project Structure

```
Farmart/
├── app.py                  # App entry point, blueprint registration
├── extensions.py           # Shared extension instances (db, ma, jwt)
├── seed.py                 # Faker-based database seeding script
├── requirements.txt
├── Procfile                # Deployment process config
├── controllers/            # Route handlers, grouped by resource (Blueprints)
│   ├── animals.py
│   ├── auth.py
│   ├── cart.py
│   ├── orders.py
│   └── payments.py
├── models/                 # SQLAlchemy models
│   ├── __init__.py         # Central model imports
│   ├── user.py
│   ├── profile.py
│   ├── animal.py
│   ├── cart.py
│   ├── cart_item.py
│   ├── order.py
│   ├── order_item.py
│   └── payment.py
├── schemas/                 # Marshmallow schemas for serialization
│   ├── user_schema.py
│   ├── profile_schema.py
│   ├── animal_schema.py
│   ├── cart_schema.py
│   ├── cart_item_schema.py
│   ├── order_schema.py
│   ├── order_item_schema.py
│   └── payment_schema.py
├── migrations/              # Alembic migration history
├── tests/                   # Pytest test suite
│   ├── test_animals.py
│   ├── test_auth.py
│   ├── test_cart.py
│   └── test_orders.py
└── .github/workflows/
    └── backend-ci.yml       # CI pipeline: install, migrate, test, health check
```

## Prerequisites

- Python 3.11+
- PostgreSQL (running locally or accessible remotely)
- pip / venv

## Local Setup

### 1. Clone and create a virtual environment

```bash
git clone <repo-url>
cd Farmart
python3 -m venv .venv
source .venv/bin/activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Set up PostgreSQL

Create a local database:

```bash
sudo -u postgres createdb farmart
```

Set a password for the `postgres` user if you haven't already:

```bash
sudo -u postgres psql -c "ALTER USER postgres PASSWORD 'yourpassword';"
```

### 4. Configure environment variables

Set `DATABASE_URL` in your shell (or a `.env` file if using `python-dotenv`):

```bash
export DATABASE_URL=postgresql://postgres:yourpassword@localhost:5432/farmart
```

> Note: if your password contains special characters (e.g. `@`), URL-encode them (`@` → `%40`) or the connection string will fail to parse correctly.

To make this persistent for your virtual environment, append it to the activate script:

```bash
echo 'export DATABASE_URL=postgresql://postgres:yourpassword@localhost:5432/farmart' >> .venv/bin/activate
```

### 5. Run database migrations

```bash
flask db upgrade
```

If this is your first time setting up migrations from scratch on a new machine:

```bash
flask db init
flask db migrate -m "initial models"
flask db upgrade
```

### 6. Seed the database (optional, recommended for local dev)

```bash
python seed.py
```

This creates sample farmers, buyers, profiles, and animals using Faker. All seeded users share the password `password123` for easy local testing.

> ⚠️ Running `seed.py` clears existing `User`, `Profile`, and `Animal` data before reseeding. Do not run this against a production database.

### 7. Run the development server

```bash
flask run
```

The API will be available at `http://127.0.0.1:5000`.

## Environment Variables

| Variable       | Description                                  | Default (fallback)         |
|----------------|-----------------------------------------------|-----------------------------|
| `DATABASE_URL` | PostgreSQL connection string                  | `sqlite:///farmart.db`      |
| `JWT_SECRET_KEY` | Secret key used to sign JWTs                | *(required for auth)*       |

## API Endpoints

### Health

| Method | Endpoint   | Description                     |
|--------|------------|----------------------------------|
| GET    | `/`        | Welcome message                  |
| GET    | `/status`  | Health check, returns `{"status": "ok"}` |

### Auth

| Method | Endpoint         | Description                          |
|--------|------------------|----------------------------------------|
| POST   | `/auth/register` | Register a new user (farmer or buyer) |
| POST   | `/auth/login`    | Log in, returns a JWT with role claim |

### Animals

| Method | Endpoint         | Access       | Description                              |
|--------|------------------|--------------|--------------------------------------------|
| GET    | `/animals`       | Public       | Paginated list, supports filters (see below) |
| GET    | `/animals/<id>`  | Public       | Single animal detail                     |
| POST   | `/animals`       | Farmer only  | Create a new animal listing              |
| PUT    | `/animals/<id>`  | Farmer only (owner) | Update an animal listing          |
| DELETE | `/animals/<id>`  | Farmer/Admin | Delete an animal listing                 |

**Query parameters for `GET /animals`:**

| Param        | Type  | Description                              |
|--------------|-------|--------------------------------------------|
| `type`       | str   | Filter by animal type (partial match)     |
| `breed`      | str   | Filter by breed (partial match)           |
| `status`     | str   | Filter by status; defaults to `available` |
| `min_price`  | float | Minimum price                             |
| `max_price`  | float | Maximum price                             |
| `min_age`    | int   | Minimum age                               |
| `max_age`    | int   | Maximum age                               |
| `page`       | int   | Page number, default `1`                  |
| `per_page`   | int   | Items per page, default `10`, capped at `50` |

### Cart

| Method | Endpoint            | Access      | Description                          |
|--------|---------------------|-------------|----------------------------------------|
| GET    | `/cart`             | Buyer only  | View current cart with nested animal info |
| POST   | `/cart/items`       | Buyer only  | Add an animal to the cart             |
| PATCH  | `/cart/items/<id>`  | Buyer only  | Update quantity of a cart item        |
| DELETE | `/cart/items/<id>`  | Buyer only  | Remove an item from the cart          |

### Orders

| Method | Endpoint                | Access      | Description                          |
|--------|--------------------------|-------------|----------------------------------------|
| POST   | `/orders/checkout`      | Buyer only  | Convert cart into an order            |
| GET    | `/orders`               | Buyer/Farmer | Role-filtered order list             |
| PATCH  | `/orders/<id>/confirm`  | Farmer only | Confirm an incoming order             |
| PATCH  | `/orders/<id>/reject`   | Farmer only | Reject an incoming order              |

### Payments

| Method | Endpoint                | Description                          |
|--------|--------------------------|----------------------------------------|
| POST   | `/payments/initiate`    | Create a payment record (stubbed gateway) |
| POST   | `/payments/webhook`     | Mark payment and order as paid        |

## Running Tests

Tests run against a separate database so your local dev data isn't affected:

```bash
sudo -u postgres createdb farmart_test
DATABASE_URL=postgresql://postgres:yourpassword@localhost:5432/farmart_test python -m pytest -v
```

## Continuous Integration

Every push and pull request to `main` and `develop` triggers `.github/workflows/backend-ci.yml`, which:

1. Spins up a Postgres service container
2. Installs dependencies from `requirements.txt`
3. Runs `flask db upgrade` to apply migrations
4. Runs the full pytest suite
5. Boots the app and checks `/status` responds correctly

## Deployment

The app is deployed via [Render / Railway] using the `Procfile`:

```
web: gunicorn app:app
```

`DATABASE_URL` and `JWT_SECRET_KEY` must be set as environment variables on the hosting platform.

## Git Workflow

This project follows **Gitflow** with **Conventional Commits**:

- `main` — production-ready code
- `develop` — integration branch, all feature branches merge here first
- `feature/*` — individual feature branches (e.g. `feature/models`, `feature/ci-and-tests`)

All PRs require review from another team member before merging to `develop`.

## Contributors

| Name              | Focus Area                                    |
|-------------------|------------------------------------------------|
| Victor Kipngeno   | Models, migrations, animals & cart endpoints, CI, deployment |
| Dennis Mwaura     | Auth, orders, schemas, validation             |
| Benvictor Gecure  | Frontend scaffold, animal detail/checkout UI  |
| Celestine         | Frontend auth, farmer dashboard               |
| Dario             | Frontend cart, payment UI, QA                 |