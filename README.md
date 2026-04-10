# Workout API Service

A backend API for managing workouts, exercises, and tagging, built with Django REST Framework.

The project focuses on authenticated, user-scoped data access, relational modelling, and API design. It includes filtering, tagging, and nested workout structures, with a Docker-based development and deployment setup.

---

## 🎯 Project Goal

This project explores how to design a backend system for structured workout planning, where:

- Users manage personalised workout routines
- Exercises are reusable across the system
- Workouts require ordered, configurable components

The focus is on backend architecture, data modelling, and API design.


## 🚀 Live Demo & API Usage

The application is containerised with Docker and deployed on AWS EC2.

- Docker Compose is used for local development
- The same containerised setup is used in production

**Deployed Swagger Docs:**
http://ec2-16-16-202-64.eu-north-1.compute.amazonaws.com/api/docs/

Use the live Swagger UI to explore the API.

### Authenticated demo flow

To access authenticated endpoints in Swagger:

#### 1. Create a user

Open:

`POST /api/user/create/`

Click **Try it out** and submit:

```json
{
  "email": "test@example.com",
  "password": "ExamplePass123!",
  "name": "Test User"
}
```

Example response:

```json
{
  "id": 1,
  "email": "test@example.com",
  "name": "Test User"
}
```

#### 2. Obtain an authentication token

Open:

`POST /api/user/token/`

Click **Try it out** and submit:

```json
{
  "email": "test@example.com",
  "password": "ExamplePass123!"
}
```

Copy the returned token.

#### 3. Authorise requests

Click the **Authorize** button in Swagger and enter:

```text
Token <your_token>
```

#### 4. Explore the API

You can then try endpoints such as:

- `GET /api/user/me/` — view your user profile
- `GET /api/workouts/` — view your workouts
- `POST /api/workouts/` — create a workout
- exercise and tag endpoints to test filtering and relationships

This demonstrates token authentication, user-scoped data access, and relational API behaviour.

---

## 🧠 Key Features

- Token-based authentication (DRF)
- User-scoped data access (users only access their own resources)
- Structured workout composition via a relational `WorkoutExercise` model
- Public and private exercises
- Tagging system for workouts and exercises
- Filtering by tags and exercise relationships
- Image upload support for exercises
- Docker-based setup with PostgreSQL
- API schema and interactive documentation via OpenAPI (Swagger)

---

## 🧩 Data Modelling

A key challenge in this project was modelling workouts composed of multiple exercises with additional metadata.

This is solved using an intermediate model:

`Workout → WorkoutExercise → Exercise`

This allows:

- Per-exercise configuration (sets, reps, rest, notes)
- Ordering of exercises within a workout
- Reusable exercise library across users

This structure enables flexible workout composition.

---

## 🔐 Authentication & Permissions

Authentication is handled using DRF `TokenAuthentication`.

Permissions are enforced using:

- `IsAuthenticated` for protected routes
- Querysets filtered by the authenticated user
- Ownership rules preventing access to other users’ data

---

## 🛠️ Custom Admin Interface

A custom back-office interface is implemented using Django Admin to manage relational workout data.

### Key Enhancements

- Inline editing of workout exercises
- Image previews for exercises
- Structured workout configuration (sets, reps, rest, notes)
- Clear organisation of relational data

---

### Exercise Management

Provides an overview of exercises, including difficulty, visibility, and image previews.

![Exercises Admin Interface](./docs/images/admin_exercise_list.png)

---

### Workout Builder

Inline editing enables construction of workouts with control over exercise order and configuration.

![Workout Admin Interface](./docs/images/admin_workout_inline.png)

---

## 📊 Architecture Overview

Client → API → Authentication → Business Logic → Database

The API is documented using OpenAPI (Swagger), providing an interface for exploring endpoints and request/response structures.

---

## ⚠️ Validation & Error Handling

- Invalid credentials return HTTP 400
- Unauthenticated requests return HTTP 401
- Unauthorized access returns HTTP 403
- Input validation is enforced via DRF serializers

---

## 🧱 Engineering Practices

- Automated testing covering API and model behaviour
- Feature branch workflow using pull requests
- Continuous Integration (GitHub Actions) running tests and linting
- Dockerised development environment
- Environment configuration via environment variables
- Code quality checks using flake8
- Modular Django app structure

---

## ⚠️ Known Limitations

- Uses DRF token authentication; JWT/OAuth flows are not implemented
- Designed as a portfolio backend service rather than a production-hardened application
- CI covers basic automated checks only
- No rate limiting or advanced observability tooling
- Some workout fields are simplified rather than fully derived
- Demo environment may be reset or changed without notice

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

```bash
docker-compose run --rm app sh -c "python manage.py createsuperuser"
```

### 5. Start Server

```bash
docker-compose run --rm app sh -c "python manage.py runserver"
```

### Accessing Admin

http://localhost:8000/admin/

---

### API Documentation

http://localhost:8000/api/docs/

---

## Testing & Linting

```bash
docker-compose run --rm app sh -c "python manage.py test && flake8"
```

---

## Notes for Reviewers

- Backend-focused project (no frontend)
- Admin interface is customised but not publicly exposed
- Demo data is reproducible locally via management commands
- Designed as a portfolio backend system
