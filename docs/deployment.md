# Deployment

This project is deployed using Docker Compose with a reverse proxy and PostgreSQL database.

---

## Architecture Overview

![Deployment Diagram](./images/docker_compose_setup.png)

---

## Services

### App (Django)
- Runs the API via uWSGI
- Handles business logic and requests

### Database (PostgreSQL)
- Stores application data
- Persisted via Docker volumes

### Proxy (Nginx)
- Handles incoming requests
- Serves static/media files
- Routes API traffic to Django app

---

## Data Persistence

Docker volumes are used to store:

- PostgreSQL data (`postgres-data`)
- Static/media files (`static-data`)

This ensures data is preserved across container restarts.

---

## Request Flow

1. User sends request to Nginx  
2. Nginx routes API requests to Django app  
3. Django interacts with PostgreSQL  
4. Response returned via Nginx  

---

## Running in Production Mode

The application can be run using Docker Compose:
```
docker-compose up --build
```

Environment variables control:
- database credentials
- secret keys
- debug mode

---

## Notes

- Static and media files are served via Nginx  
- Database and file storage persist via volumes  
- Architecture mirrors a typical production Django setup  

