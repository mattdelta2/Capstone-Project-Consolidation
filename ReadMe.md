# News Application

[![Build Status](https://img.shields.io/github/actions/workflow/status/mattdelta2/Capstone-Project-Consolidation/ci.yml?branch=main)](https://github.com/mattdelta2/Capstone-Project-Consolidation/actions) [![Coverage](https://img.shields.io/codecov/c/github/mattdelta2/Capstone-Project-Consolidation)](https://codecov.io/gh/mattdelta2/Capstone-Project-Consolidation) [![Docker Pulls](https://img.shields.io/docker/pulls/mattdelta2/newsapp)](https://hub.docker.com/r/mattdelta2/newsapp)

A Django-based news management platform with role-based CR​UD, subscription newsletters, and automated email/X dispatch upon publication.

---

## Table of Contents

- [Features](#features)  
- [Tech Stack](#tech-stack)  
- [Prerequisites](#prerequisites)  
- [Installation & Setup](#installation--setup)  
  - [Local Development](#local-development)  
  - [Docker (Recommended)](#docker-recommended)  
- [Running the Application](#running-the-application)  
- [API Documentation](#api-documentation)  
- [Testing & Coverage](#testing--coverage)  
- [Common Issues](#common-issues)  
 

---

## Features

- Custom user model with roles: Reader, Journalist, Editor  
- Group-based permissions enforcing role-specific CRUD  
- Reader subscriptions to publishers or journalists  
- Editor approval workflow with access control  
- Signals to email subscribers and post to X on article publication  
- RESTful API (serializers, viewsets, routers)  
- Unit tests via pytest targeting 100% coverage  
- MariaDB as production-grade backend  

---

## Tech Stack

| Layer             | Technology / Library      |
|-------------------|---------------------------|
| Web Framework     | Django                    |
| API Toolkit       | Django REST Framework     |
| Auth              | DRF Token Authentication  |
| Database          | MariaDB                   |
| Email Dispatch    | Django Mailer            |
| Pub/Sub Signals   | Django Signals            |
| Frontend Styling  | Bootstrap                 |
| Markdown Editing  | Django-MarkdownX          |
| Tagging           | django-taggit             |
| Testing           | pytest, pytest-cov        |
| Containerization  | Docker, docker-compose    |

---

## Prerequisites

- Python 3.10+  
- MariaDB server (local or remote)  
- Docker & Docker Compose (for container setup)  
- [Postman](https://www.postman.com/) or similar (optional, for API testing)  

---

## Installation & Setup

### Local Development

1. Clone repo and enter directory:  
   ```bash
   git clone https://github.com/mattdelta2/Capstone-Project-Consolidation.git
   cd Capstone-Project-Consolidation
   ```

2. Create and activate a virtual environment:  
   ```bash
   python -m venv venv
   source venv/bin/activate   # Windows: venv\Scripts\activate
   ```

3. Install dependencies:  
   ```bash
   pip install -r requirements.txt
   ```

4. Copy and configure environment variables:  
   ```bash
   cp .env.example .env
   # Fill in SECRET_KEY, DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, EMAIL_*, X_* 
   ```

5. Apply migrations and create a superuser:  
   ```bash
   python manage.py migrate
   python manage.py createsuperuser
   ```

---

### Docker (Recommended)

1. Build and run containers:  
   ```bash
   docker compose up --build -d
   ```

2. Apply migrations inside the web container:  
   ```bash
   docker compose exec web python manage.py migrate
   docker compose exec web python manage.py createsuperuser
   ```

3. Access the app at `http://localhost:8000/` and admin at `http://localhost:8000/admin/`.

---

## Running the Application

If you’re not using Docker:

```bash
python manage.py runserver
```

Visit `http://localhost:8000/` for the website.

---

## API Documentation

Import `NewsPortal.postman_collection.json` into Postman to test endpoints manually.

---

## Testing & Coverage

Run automated tests with coverage reporting:

```bash
pytest --cov=news_portal --cov-report=html
```

Open `htmlcov/index.html` to review coverage details.

---

## Common Issues

- MariaDB “Access denied”: verify `DB_USER` & `DB_PASSWORD` in `.env`.  
- Token-auth 401: POST JSON to `/api-token-auth/` with correct credentials.  
- Static files missing: run `python manage.py collectstatic` when DEBUG=False.  
- Migration conflicts: delete conflicting migration files and re-run `makemigrations`.  

---
