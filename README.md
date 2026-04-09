# Workout API Service

A production-style backend API for managing workouts, exercises, and user-specific training data.

This project demonstrates real-world backend engineering practices including authentication, permissions, relational data modelling, testing, and containerised deployment.

---

## Live Demo

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

You can now access endpoints.

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
* Object-level permission checks enforced

---

## Architecture Overview

Client → API → Auth → Services → Database

More detailed documentation available in `/docs`.

---

## Demo Preview

*(Add screenshots or GIFs here)*

Suggested:

* Swagger usage
* Admin dashboard
* Workout creation flow

---

## Summary

This project demonstrates:

* Real-world API design
* Authentication & security practices
* Relational modelling beyond CRUD
* Testing, validation, and CI workflows
* Containerised development environment
