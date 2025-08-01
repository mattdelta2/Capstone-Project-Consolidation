# News Application

## Description

This Django-based News Application enables role-based article management, newsletter subscriptions, and automatic email (and X) dispatch on publication. Readers can subscribe to publishers or individual journalists; editors approve and publish articles.

---

## Table of Contents

- [Features](#features)  
- [Tech Stack](#tech-stack)  
- [Prerequisites](#prerequisites)  
- [Installation & Setup](#installation--setup)  
- [Running the Application](#running-the-application)  
- [Running Tests](#running-tests)    
- [Common Issues](#common-issues)  
- [API Endpoints](#api-endpoints)  

---

## Features

- Custom user model with roles: Reader, Journalist, Editor  
- Group-based permissions enforcing CRUD by role  
- Reader subscriptions to publishers or journalists  
- Editor approval workflow with access control  
- Approved-article signals to email subscribers and post to X  
- RESTful API for third-party clients: serializers, views, URLs  
- Unit tests (pytest) covering API and core logic  
- MariaDB as the production database backend  

---

## Tech Stack

| Component         | Technology / Library          |
|-------------------|-------------------------------|
| Web Framework     | Django                        |
| REST API          | Django REST Framework         |
| Authentication    | DRF Token Authentication      |
| Email Dispatch    | Django’s built-in mailer      |
| Dispatch Signals  | Django signals                |
| Database          | MariaDB                       |
| Testing           | pytest                        |
| Markdown Editing  | Django-MarkdownX              |
| Tagging           | django-taggit                 |
| Frontend Styling  | Bootstrap                     |

---

## Prerequisites

- Python 3.10 or higher  
- MariaDB server  
- (Optional) API-client tool like Postman for testing  

---

## Installation & Setup



1. Create and activate a virtual environment:  
   ```bash
   python -m venv venv
   source venv/bin/activate   # on Windows use `venv\Scripts\activate`
   ```

2. Install dependencies:  
   ```bash
   pip install -r requirements.txt
   ```

3. Copy and configure environment variables:  
   ```bash
   cp .env.example .env
   # Edit .env with SECRET_KEY, DB_*, EMAIL_*, X_* values
   ```

4. Apply database migrations:  
   ```bash
   python manage.py migrate
   ```

5. Create a superuser:  
   ```bash
   python manage.py createsuperuser
   ```

---

## Running the Application

```bash
python manage.py runserver
```  

- Visit `http://localhost:8000/` for the site  
- Use `http://localhost:8000/admin/` for the admin interface  

---

## Running Tests

```bash
pytest
```  

- Aim for 100% coverage on API endpoints and core logic  

---



## Common Issues

- **MariaDB “Access denied”**: verify `DB_USER` and `DB_PASSWORD`.  
- **Token-auth returning 401**: ensure you’re POSTing to `/api-token-auth/` with JSON body.  
- **Missing migrations**: run `python manage.py makemigrations` then `migrate`.  

---

## API Endpoints

### Authentication

- `POST /api-token-auth/`  
  Request:  
  ```json
  { "username": "user", "password": "pass" }
  ```  
  Response:  
  ```json
  { "token": "abc123" }
  ```

### Articles

- `GET /api/articles/`  
  List approved articles for your subscriptions.  
  Query parameters:  
  - `publisher=<id>`  
  - `journalist=<id>`  
  - `tag=<name>`

- `GET /api/articles/<id>/`  
  Retrieve a single article by ID.

### Subscriptions

- `POST /api/newsletters/subscribe/`  
  ```json
  { "type": "publisher", "id": 4 }
  ```

- `DELETE /api/newsletters/unsubscribe/`  
  ```json
  { "type": "journalist", "id": 9 }
  ```