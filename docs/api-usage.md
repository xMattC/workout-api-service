# API Usage Guide

This document explains how to interact with the Workout API, including authentication, common workflows, and example requests.

---

## Base URL

Local:

```
http://localhost:8000/
```

Production:

```
http://ec2-16-16-202-64.eu-north-1.compute.amazonaws.com/
```

---

## Authentication

The API uses **Token Authentication**.

### Obtain Token

Endpoint:

```
POST /api/user/token/
```

Request:

```json
{
  "email": "api_demo@workoutapp.com",
  "password": "DemoPassword123$"
}
```

Response:

```json
{
  "token": "your_token_here"
}
```

---

### Using the Token

Include the token in the request header:

```
Authorization: Token <your_token>
```

---

## Demo Account

Use the seeded demo account for testing:

* **Email:** [api_demo@workoutapp.com](mailto:api_demo@workoutapp.com)
* **Password:** DemoPassword123$

---

## Common Workflows

### 1. Retrieve Current User

```
GET /api/user/me/
```

Response:

```json
{
  "id": 1,
  "email": "api_demo@workoutapp.com",
  "name": "Demo User"
}
```

---

### 2. Create a Workout

```
POST /api/workout/
```

Request:

```json
{
  "title": "Upper Body Push",
  "description": "Chest and triceps workout",
  "duration_minutes": 45
}
```

---

### 3. List Workouts

```
GET /api/workout/
```

Returns all workouts belonging to the authenticated user.

---

### 4. Add Exercises to a Workout

Exercises are added via the **WorkoutExercise** relationship.

Example request (structure may vary depending on serializer):

```json
{
  "exercise": 1,
  "order": 1,
  "sets": 3,
  "reps": 12,
  "rest_seconds": 60,
  "user_notes": "Focus on form"
}
```

---

### 5. View Exercises

```
GET /api/exercise/
```

Returns:

* Public exercises
* User-created exercises

---

## Swagger Usage

The API is fully documented using Swagger:

```
/api/docs/
```

### Steps:

1. Open Swagger
2. Call `POST /api/user/token/`
3. Copy the returned token
4. Click **Authorize**
5. Enter:

```
Token <your_token>
```

You can now interact with all protected endpoints.

---

## Error Handling

Common responses:

* **400 Bad Request** → Invalid input or credentials
* **401 Unauthorized** → Missing or invalid token
* **403 Forbidden** → Accessing another user’s data

---

## Permissions Summary

* All endpoints (except user creation and token) require authentication
* Users can only access their own workouts
* Exercises are:

  * Public (accessible to all)
  * Private (owned by user)

---

## Notes

* All requests and responses are JSON
* Authentication is required for most operations
* The API structure reflects the underlying relational model
* Use Swagger for easiest exploration and testing

---

## Summary

This API supports:

* User authentication via token
* Workout creation and management
* Flexible exercise composition
* Strict user-level data isolation

It is designed to provide a clean and scalable backend for structured workout planning.
