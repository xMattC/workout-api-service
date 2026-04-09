# API Usage Guide

This document explains how to interact with the Workout API, including authentication, common workflows, and example requests.

---

## Base URL

Local:
`http://localhost:8000/`

Production:
`http://ec2-16-16-202-64.eu-north-1.compute.amazonaws.com/`

---

## Authentication

The API uses DRF Token Authentication.

### Obtain Token

`POST /api/user/token/`

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

### Using the Token

Include the token in the request header:

```
Authorization: Token <your_token>
```

---

## Demo Account

Use the seeded demo account for testing:

* **Email:** `api_demo@workoutapp.com`
* **Password:** `DemoPassword123$`

---

## Common Workflows

### 1. Retrieve Current User

`GET /api/user/me/`

Example response:

```json
{
  "email": "api_demo@workoutapp.com",
  "name": "Demo User"
}
```

---

### 2. List Workouts

`GET /api/workout/workouts/`

Optional filters:

* `?exercises=1,2`
* `?wo_tags=1,2`

Examples:

```
GET /api/workout/workouts/?exercises=1,2
GET /api/workout/workouts/?wo_tags=3
GET /api/workout/workouts/?exercises=1,2&wo_tags=3
```

Returns workouts owned by the authenticated user.

---

### 3. Create a Workout

`POST /api/workout/workouts/`

Request:

```json
{
  "title": "Upper Body Push",
  "description": "Chest and triceps workout",
  "duration_minutes": 45,
  "wo_tags": [
    { "name": "Push Day" }
  ],
  "workout_exercises": [
    {
      "exercise": 1,
      "order": 1,
      "sets": 4,
      "reps": 10,
      "rest_seconds": 90
    }
  ]
}
```

Notes:

* `wo_tags` is optional
* `workout_exercises` is optional
* Nested relationships are replaced on update, not merged

---

### 4. Retrieve a Workout in Detail

`GET /api/workout/workouts/{id}/`

Returns a fully expanded workout including nested exercise data.

---

### 5. List Exercises

`GET /api/workout/exercises/`

Returns:

* Public exercises
* User-created exercises

Optional filters:

* `?assigned_only=1`
* `?ex_tags=1,2`

Examples:

```
GET /api/workout/exercises/?assigned_only=1
GET /api/workout/exercises/?ex_tags=1,2
```

---

### 6. Create an Exercise

`POST /api/workout/exercises/`

Request:

```json
{
  "name": "Incline Dumbbell Press",
  "difficulty": "intermediate",
  "ex_tags": [
    { "name": "Dumbbell", "type": "equipment" },
    { "name": "Chest", "type": "primary_muscle" }
  ]
}
```

Notes:

* Normal users create private exercises
* Only staff users may create public exercises

---

### 7. Upload Exercise Images

`POST /api/workout/exercises/{id}/upload-image/`

Accepted fields:

* `image_1`
* `image_2`

Supports partial updates.

---

### 8. Workout Tags

`GET /api/workout/workouts-tags/`
`POST /api/workout/workouts-tags/`

Optional filter:

* `?assigned_only=1`

---

### 9. Exercise Tags

`GET /api/workout/exercises-tags/`
`POST /api/workout/exercises-tags/`

Optional filter:

* `?assigned_only=1`

System tags and user-created tags are returned.
Only user-owned custom tags can be modified.

---

## Swagger Usage

Swagger is available at:

`/api/docs/`

Steps:

1. Open Swagger
2. Call `POST /api/user/token/`
3. Copy the returned token
4. Click **Authorize**
5. Enter:

```
Token <your_token>
```

---

## Error Handling

Common responses:

* `400 Bad Request` → Invalid input or credentials
* `401 Unauthorized` → Missing or invalid token
* `403 Forbidden` → Attempting to modify restricted resources

---

## Permissions Summary

* `POST /api/user/create/` and `POST /api/user/token/` are public
* All other endpoints require authentication
* Users can only access their own workouts and workout tags
* Exercises include public + user-owned private exercises
* System exercise tags are read-only for non-admin users

---
