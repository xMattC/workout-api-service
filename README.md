# Workout API Service

A backend API for building and managing structured workout programmes, supporting user-specific data, reusable exercise libraries, and complex workout composition.

---

## 🎯 Project Goal

This project explores how to design a backend system for structured workout planning, where:

* Users manage personalised workout routines
* Exercises are reusable across the system
* Workouts require ordered, configurable components

The focus is on backend architecture, data modelling, and API design.

---

## 🚀 Live Demo

* **Swagger Docs:** https://workout-api-service.onrender.com/swagger/

---

### Demo Access

Use the seeded demo account to explore authenticated endpoints with preloaded data:

* **Email:** [api_demo@workoutapp.com](mailto:api_demo@workoutapp.com)
* **Password:** DemoPassword123$

---

### Suggested Demo Flow

1. Log in via `POST /api/user/token/`
2. Authorise in Swagger using `Token <your_token>`
3. Retrieve your user profile (`/api/user/me/`)
4. View existing workouts
5. Create a new workout
6. Add exercises to the workout

---

### Example API Usage

#### Create User

POST `/api/user/create/`

Request:

```json
{
  "email": "test@example.com",
  "password": "test123",
  "name": "Test User"
}
```

Response:

```json
{
  "id": 1,
  "email": "test@example.com",
  "name": "Test User"
}
```

---

## 🧠 Key Features

* Token-based authentication
* User-scoped data permissions
* Structured workout composition
* Fully documented API (Swagger/OpenAPI)
* Dockerised development environment

---

## 🧩 Data Modelling

A key challenge in this project was modelling workouts composed of multiple exercises with additional metadata.

This is solved using an intermediate model:

Workout → WorkoutExercise → Exercise

This allows:

* Per-exercise configuration (sets, reps, rest, notes)
* Ordering of exercises within a workout
* Reusable exercise library across users

This structure enables flexible and scalable workout composition.

---

## 🔐 Authentication & Permissions

Authentication is handled using DRF TokenAuthentication.

Permissions are enforced using:

* `IsAuthenticated` for protected routes
* Querysets filtered by the authenticated user
* Strict ownership rules preventing access to other users’ data

---

## 🛠️ Custom Admin Interface

A custom back-office system has been built using Django Admin to manage complex relational workout data efficiently.

### Key Enhancements

* Inline editing of workout exercises
* Image previews for exercise visualisation
* Structured workout configuration (sets, reps, rest, notes)
* Clear organisation of relational data

---

### Exercise Management

Provides a clear overview of all exercises, including difficulty, visibility, and image previews.

![Exercises Admin Interface](./docs/images/admin_exercise_list.png)

---

### Workout Builder

Custom inline editing enables efficient construction of workouts with full control over exercise order and configuration.

![Workout Admin Interface](./docs/images/admin_workout_inline.png)

---

## 📊 Architecture Overview

Client → API → Authentication → Business Logic → Database

The API is fully documented using Swagger/OpenAPI, providing an interactive interface for exploring endpoints and request/response structures.

---

## ⚠️ Validation & Error Handling

* Invalid credentials return HTTP 400
* Unauthenticated requests return HTTP 401
* Unauthorized access returns HTTP 403
* Input validation enforced via DRF serializers

---

## 🧱 Engineering Practices

Development follows a structured workflow ensuring code quality and reliability:

* **Test-Driven Development (TDD)** – Core functionality built with tests first
* **Feature Branch Workflow** – Isolated development via pull requests
* **Continuous Integration (CI)** – GitHub Actions running tests and linting
* **Dockerised Environment** – Consistent development setup
* **Environment Configuration** – Managed via environment variables
* **Code Quality Enforcement** – Linting with flake8
* **Modular Architecture** – Clear separation of Django apps

---

## 📦 Running Locally

### 1. Clone Repository

```bash
git clone https://github.com/xMattC/workout-api-service.git
cd workout-api-service
```

### 2. Run Migrations

```bash
docker-compose run --rm app sh -c "python manage.py migrate"
```

### 3. Seed Demo Data

```bash
docker-compose run --rm app sh -c "python manage.py seed_users"
docker-compose run --rm app sh -c "python manage.py seed_exercises"
```

### 4. Start Server

```bash
docker-compose run --rm app sh -c "python manage.py runserver"
```

Open: http://localhost:8000/swagger/

---

## 🧪 Testing & Linting

```bash
docker-compose run --rm app sh -c "python manage.py test && flake8"
```

---

## 🛠️ Development Utilities

```bash
docker-compose run --rm app sh -c "python manage.py shell"
```

---

## 📌 Notes for Reviewers

* Backend-focused project (no frontend)
* Admin interface is customised but not publicly exposed
* Demo data is reproducible locally via management commands
* Designed to reflect production-style backend patterns

---

## 📬 Contact

For admin demo access or questions, feel free to reach out.
