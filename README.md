# Workout API Backend

A Django REST API for managing exercises and workouts, featuring user-scoped data access, public and private resources, structured workout composition, and derived metrics such as estimated workout duration.

---

## Overview

This project models a workout planning system where users can:

- Create and manage workouts
- Compose workouts from exercises with sets, reps, and rest
- Use a shared library of public exercises
- Create private custom exercises
- Upload and manage exercise images
- Retrieve structured workout data with derived metrics

The system enforces strict ownership rules and provides a clean, queryable API.

The API is deployed and available for live interaction via Swagger documentation.
---

## Core Features

- Token-based authentication
- User-scoped workouts and private data
- Public (seeded) and private exercises
- Workout composition via `WorkoutExercise`
- Estimated workout duration calculation
- Filtering, search, ordering, pagination
- Image upload for exercises
- OpenAPI / Swagger documentation
- Automated tests and CI
- Dockerised setup with PostgreSQL

---

## Key Concepts

### User-Scoped Access Control
All workouts and private exercises are owned by a user. Users cannot access or modify other users’ data.

### Public vs Private Resources
- Public exercises are system-provided and read-only
- Private exercises are user-created and editable only by their owner

### Enriched Join Model
`WorkoutExercise` is a first-class entity linking workouts and exercises, containing:
- order
- sets
- reps
- rest time
- optional notes

### Derived Metrics
Workout duration is estimated based on:
- sets
- reps
- rest time
- assumed seconds per rep

---

## Data Model

- User
- Exercise (public/private)
- Workout
- WorkoutExercise

---

## Ownership Rules

- Users can only access their own workouts
- Public exercises are readable but not editable
- Private exercises are only accessible to their creator
- WorkoutExercise entries inherit workout ownership

---

## API Highlights

### Authentication
- Create user
- Obtain token
- Manage profile

### Exercises
- List (public + private)
- Create private exercise
- Upload image

### Workouts
- Create workout
- Add exercises to workout
- Retrieve nested workout details

---

## Example Requests

### Create Workout
POST /api/workouts/

### Add Exercise to Workout
POST /api/workout-exercises/

### Filter Exercises
GET /api/exercises/?search=push

---

## Tech Stack

- Django
- Django REST Framework
- PostgreSQL
- Docker
- drf-spectacular

---

## Local Setup

```bash
git clone <repo>
cd backend-app-api
docker-compose up
```

---

## Running Tests

```bash
docker-compose run app python manage.py test
```

---

## Documentation

Swagger UI available at:
```
http://localhost:8000/api/docs/
```

---

## Deployment

The API is deployed and publicly accessible.

Base URL:
https://<your-domain>

Interactive API documentation:
https://<your-domain>/api/docs/

## Live API Usage

### Example: List Exercises
GET https://<your-domain>/api/exercises/

### Example: Create Workout (Authenticated)
POST https://<your-domain>/api/workouts/

Authorization:
Token <your-token>

### Production Setup

- Django running in production mode (DEBUG=False)
- PostgreSQL database
- Environment variables for secrets and configuration
- Static and media files handled via configured storage
- HTTPS enabled

### Notes

- Public endpoints are available for testing via Swagger
- Authentication is required for protected routes

---

## Screenshots

- Swagger UI (live deployed API)
- Workout detail response with nested exercises
- Exercise list with filtering

---

## Future Improvements

- Program (multi-workout) support
- Expanded filtering options
- Additional derived metrics
