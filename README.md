# Workout API Service

A backend API for building and managing structured workout programmes, supporting user-specific data, reusable exercise libraries, and complex workout composition.

This project was built to explore how to design a backend system for structured workout planning, where:

- Users manage personalised workout routines
- Exercises are reusable across the system
- Workouts require ordered, configurable components

The focus is on backend architecture, data modelling, and API design.

---

## Live Demo
The API is fully documented using Swagger/OpenAPI, providing an interactive interface for exploring endpoints, authentication, and request/response structures.

**Swagger Docs:** (http://ec2-16-16-202-64.eu-north-1.compute.amazonaws.com/api/docs/#/)

**Demo Access**
Use the demo account below to test authenticated endpoints:

* **Email:** [api_demo@workoutapp.com](mailto:api_demo@workoutapp.com)
* **Password:** DemoPassword123$

**How to Authenticate**

1. POST `/api/user/token/`
2. Copy the returned access token
3. Click **Authorize** in Swagger
4. Enter: `Token <your_token>`

 **Suggested Demo Flow**

1. Log in using the demo account
2. View workouts
3. Create a new workout
4. Add exercises to the workout

This demonstrates authentication, permissions, and relational data handling.

**Example API Usage**

Create User:
```
POST /api/user/create/
```
Request:
```
{
  "email": "test@example.com",
  "password": "test123",
  "name": "Test User"
}
```
Response:
```
{
  "id": 1,
  "email": "test@example.com",
  "name": "Test User"
}
```
---

## Key Features

* Token-based authentication
* Object-level permissions (user-scoped data)
* Public vs private exercise system
* Workout → Exercise join model
* Derived workout data (e.g. duration)
* Fully documented API (Swagger/OpenAPI)
* Dockerised setup (PostgreSQL + Django)
* Automated testing + linting

---

## Tech Stack

* Python / Django
* Django REST Framework
* PostgreSQL
* Docker & Docker Compose
* Swagger (drf-yasg)

---

## Engineering Practices

- **Test-Driven Development (TDD)** – Core functionality developed with tests written prior to implementation
- **Feature Branch Workflow** – Isolated development using feature branches with pull request reviews
- **Continuous Integration (CI)** – GitHub Actions pipeline running tests and linting on each pull request
- **Dockerised Environment** – Consistent development and execution using Docker Compose
- **Environment Configuration** – Settings managed via environment variables
- **Code Quality Enforcement** – Linting with flake8
- **Modular Architecture** – Structured Django apps with clear separation of concerns
- 
## Custom Admin Interface

Built a custom back-office system using Django Admin to efficiently manage complex relational workout data.

Key improvements include:

- Inline workout exercise editing
- Image previews for exercises
- Structured workout configuration (sets, reps, rest, notes)
- Clear visual grouping of workout components

This enables efficient management of complex workout structures directly within the admin interface.

![Exercises Admin Interface](./docs/images/admin_exercise_list.png)
![Workout Admin Interface](./docs/images/admin_workout_inline.png)
---

## Data Modelling

A key challenge in this project was modelling workouts composed of multiple exercises with additional metadata.

This is solved using an intermediate model:

Workout ↔ WorkoutExercise ↔ Exercise

This allows:

- Per-exercise configuration (sets, reps, rest, notes)
- Ordering of exercises within a workout
- Reusable exercise library across users

This structure enables flexible and scalable workout composition.

## Validation & Error Handling

- Invalid credentials return HTTP 400
- Unauthorized access returns HTTP 401
- Users cannot access other users’ data (403)
- Input validation enforced via serializers
  
## Running Locally

### 1. Clone Repository

```
git clone https://github.com/xMattC/workout-api-service.git
cd workout-api-service
```

### 2. Start Development Server & Apply Migrations

```
docker-compose run --rm app sh -c "python manage.py runserver"
docker-compose run --rm app sh -c "python manage.py makemigrations"
docker-compose run --rm app sh -c "python manage.py migrate"
```

### 4. Seed Demo Data

Custom management commands are included to populate realistic data.

```
docker-compose run --rm app sh -c "python manage.py seed_exercise_data"
docker-compose run --rm app sh -c "python manage.py seed_user_workout_data"
```

### 5. Testing & Linting

```
docker-compose run --rm app sh -c "python manage.py test && flake8"
```

### 6. Create Superuser

```
docker-compose run --rm app sh -c "python manage.py createsuperuser"
```

### 7. Accessing the Admin Interface

Once you have created a superuser, you can log into the Django admin panel:
```
docker-compose run --rm app sh -c "python manage.py runserver"
```
* **Admin URL:** http://localhost:8000/admin/
* Use the credentials you created via `createsuperuser`
* Full admin access

You can:
  
  * Manage users
  * View/edit workouts
  * Inspect exercise relationships
  * Explore join model data (`WorkoutExercise`)

---

## Design Highlights

### Ownership Model

* Users can only access their own workouts
* Exercises can be public or user-owned

### Join Model

Workouts and exercises are linked via:

`WorkoutExercise`

This enables:

* Ordered workouts
* Per-exercise metadata
* Flexible composition

### Permissions

* Auth required for protected routes
* Permissions are enforced using DRF TokenAuthentication and IsAuthenticated, with querysets filtered by the authenticated user to ensure strict data ownership.

---

## Architecture Overview

Client → API → Auth → Services → Database

More detailed documentation available in `/docs`.

---

## Summary

This project demonstrates:

* Real-world API design
* Authentication & security practices
* Relational modelling beyond CRUD
* Testing, validation, and CI workflows
* Containerised development environment
