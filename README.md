# JSONPlaceholder User Fetcher

A production-ready Python application to fetch user information from the [JSONPlaceholder API](https://jsonplaceholder.typicode.com/users), following clean architecture and industry best practices. 

---

## Features

- Connects to the JSONPlaceholder API and retrieves all user records from `/users`
- Clean, modular, and testable codebase (controller → service → domain → repository)
- Environment configuration via `.env`
- Logging and error propagation
- Ready for further extension

---

## Project Structure

```
src/
  config/           # Configuration and environment variable loader
    config.py
  data/             # Repository layer for API access
    user_repository.py
  domain/           # Domain models
    models.py
  services/         # Business logic layer
    user_service.py
  main.py           # Application entrypoint
.env                # Environment variables
requirements.txt    # Python dependencies
.gitignore
README.md
```

---

## Setup & Usage

### 1. Clone the repository

```bash
git clone <your-repo-url>
cd <repo-directory>
```

### 2. Create and activate a virtual environment (recommended)

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

Edit the `.env` file if you need to override the default API base URL or endpoint.

### 5. Run the application

```bash
python src/main.py
```

---

## Configuration

All environment variables are managed in the `.env` file:

```
JSONPLACEHOLDER_BASE_URL=https://jsonplaceholder.typicode.com
JSONPLACEHOLDER_USERS_ENDPOINT=/users
```

---

## Linting & Style

- Follows [PEP8](https://peps.python.org/pep-0008/) and industry standards.
- Use `flake8` or `black` for linting/formatting (optional).

---

## Notes

- No authentication or special headers are required for the API.
- No data is persisted or transformed.
- The code is ready for further processing or integration.
