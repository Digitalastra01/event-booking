# Event Booking API

A robust FastAPI-based event booking system with Celery for background email processing.

## Features

-   **User Authentication**: JWT-based auth with role-based access control (Admin/User).
-   **Event Management**: Create, list, and manage events (Admin only).
-   **Booking System**: Users can book tickets for events.
    -   Capacity management.
    -   Guest details (Name, Email).
    -   Ticket counting.
-   **Email Notifications**: Asynchronous email confirmation using Celery and Redis.
-   **Database**: PostgreSQL with SQLAlchemy (Async).

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

## API Documentation

Visit `http://localhost:8000/docs` for the interactive Swagger UI.
