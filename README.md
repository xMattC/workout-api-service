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
## 🚀 Live Demo & API Usage

**Swagger Docs:**
http://ec2-16-16-202-64.eu-north-1.compute.amazonaws.com/api/docs/

---

### Demo Access

Use the seeded demo account to explore authenticated endpoints with preloaded data:

* **Email:** [api_demo@workoutapp.com](mailto:api_demo@workoutapp.com)
* **Password:** DemoPassword123$

---

### Step-by-Step Demo Flow

#### 1. Obtain Authentication Token

In Swagger, open:

`POST /api/user/token/`

Click **"Try it out"**, then enter:

```json
{
  "email": "api_demo@workoutapp.com",
  "password": "DemoPassword123$"
}
```

Click **Execute**, then copy the returned token.

---

#### 2. Authorise Requests

Click the **Authorize** button in Swagger and enter:

```
Token <your_token>
```

---

#### 3. Explore the API

Try the following endpoints:

* `GET /api/user/me/` → View your user profile
* `GET /api/workout/` → View existing workouts
* `POST /api/workout/` → Create a new workout
* Add exercises to a workout

This demonstrates authentication, permissions, and relational data handling.

Example: `POST /api/user/create/`

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

This is solved using an intermediate model: `Workout → WorkoutExercise → Exercise`

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

### 4. Create Superuser
```
docker-compose run --rm app sh -c "python manage.py createsuperuser"
```
Follow the prompts to set:
- Email
- Password


### 5. Start Server
```
docker-compose run --rm app sh -c "python manage.py runserver"
```

### Accessing the Admin Interface

Once the server is running, open:

http://localhost:8000/admin/

Log in using the **superuser credentials** you created in the previous step.

After logging in, you can:
- Manage users  
- View and edit workouts  
- Explore exercises and relationships  
- Use the custom admin interface for structured workout management  

---

### API Documentation

Swagger docs available at:

http://localhost:8000/api/docs/

---

## Testing & Linting

```bash
docker-compose run --rm app sh -c "python manage.py test && flake8"
```

---

## Development Utilities

```bash
docker-compose run --rm app sh -c "python manage.py shell"
```

---

## Notes for Reviewers

* Backend-focused project (no frontend)
* Admin interface is customised but not publicly exposed
* Demo data is reproducible locally via management commands
* Designed to reflect production-style backend patterns
