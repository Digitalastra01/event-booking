# Event Booking API

A robust FastAPI-based event booking system with Celery for background email processing.

## Features

-   **User Authentication**: JWT-based auth with role-based access control (Organizer/User).
-   **Event Management**: Organizers can create, list, and manage events.
-   **Booking System**: Users can book tickets for events.
    -   Capacity management.
    -   Guest details (Name, Email).
    -   Ticket counting.
-   **Email Notifications**: Asynchronous email confirmation using Celery and Redis.
-   **Database**: PostgreSQL with SQLAlchemy (Async).
-   **Observability**: Structured logging across API endpoints for better auditing.

## Tech Stack

-   **Framework**: FastAPI
-   **Database**: PostgreSQL, SQLAlchemy (Async), Alembic
-   **Background Tasks**: Celery, Redis
-   **Runtime**: Python 3.14 (managed by `uv`)

## Setup

1.  **Install Dependencies**:
    ```bash
    uv sync
    ```

2.  **Environment Variables**:
    Create a `.env` file with the following:
    ```env
    DATABASE_URL=postgresql+asyncpg://user:password@localhost/dbname
    SECRET_KEY=your_secret_key
    REDIS_URL=redis://localhost:6379/0
    MAIL_USERNAME=your_email@gmail.com
    MAIL_PASSWORD=your_app_password
    MAIL_FROM=your_email@gmail.com
    MAIL_PORT=587
    MAIL_SERVER=smtp.gmail.com
    SUPPRESS_SEND=0
    ```

3.  **Run Migrations**:
    ```bash
    uv run alembic upgrade head
    ```

4.  **Start Application**:
    ```bash
    uv run uvicorn app.main:app --reload
    ```

5.  **Start Celery Worker**:
    ```bash
    celery -A app.core.celery_app worker --loglevel=info
    ```

## Usage

-   **Create an account** (`/api/v1/auth/signup`): set `is_organizer` to `true` for organizer access.
-   **Obtain a token** (`/api/v1/auth/login`): use the returned bearer token in subsequent requests.
-   **List events** (`/api/v1/events/all`): organizers and users can fetch full event listings.
-   **Manage events** (`/api/v1/events/{id}`): organizers create, update, delete events; authorization enforced.
-   **Manage bookings** (`/api/v1/bookings/`): users can create, view, update, and cancel their bookings.
-   **Manage users** (`/api/v1/users/`): organizers can invite or modify other users and organizers.

## API Documentation

Visit `http://localhost:8000/docs` for the interactive Swagger UI.

## Role-based Access Control

-   **Organizers** can create, update, and delete events, and manage users through the `/api/v1/users` endpoints.
-   **Users** can browse events and manage their own bookings.
-   **Registration**: When calling `/api/v1/auth/signup`, include `"is_organizer": true` in the payload to create an organizer; omit or set it to `false` to create a regular user.

## Developer Notes

-   **Migrations**: Use Alembic to evolve the schema. Create new revisions with `uv run alembic revision --autogenerate -m "description"`.
-   **Legacy role cleanup**: If upgrading from an older schema with `ADMIN` roles, run the migration script in `scripts/migrate_admin_roles.py` to map them to `organizer` or `user`.
-   **Testing**: Execute `uv run pytest` to verify API flows and ensure bookings/events logic remains intact.
-   **Logging**: Endpoint handlers emit structured logs via `app/utils/logger.py`. Tail your console or configure log aggregation for production deployments.
