# Authentication & Permissions

This document describes how authentication and access control are implemented in the Workout API.

---

## Authentication Overview

The API uses **Django REST Framework Token Authentication**.

Users authenticate using their email and password to obtain a token, which is then used for all protected requests.

---

## Obtaining a Token

Endpoint:

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

---

## Using the Token

All authenticated requests must include the token in the header:

```
Authorization: Token <your_token>
```

Requests without a valid token will return:

```
401 Unauthorized
```

---

## User Model

The system uses a **custom user model** with:

* Email as the unique identifier (`USERNAME_FIELD = "email"`)
* Django’s authentication system (`AbstractBaseUser`, `PermissionsMixin`)

This enables:

* Email-based login
* Compatibility with Django’s permission framework

---

## Permission Model

The API enforces **strict user-level data ownership**.

### Core Principle

> A user can only access and modify their own data.

---

## Access Rules

### Workouts

* Users can only:

  * View their own workouts
  * Create workouts for themselves
  * Update/delete their own workouts

---

### Exercises

Exercises are split into two categories:

#### Public Exercises

* Accessible to all users
* Created by staff users

#### Private Exercises

* Owned by individual users
* Only accessible to the owner

---

### Workout Tags

* Fully user-scoped
* Users can only manage their own tags

---

### Exercise Tags

* System-defined tags (shared, read-only)
* User-created tags (editable only by owner)

---

## Implementation Details

Permissions are enforced using:

* **DRF Authentication**

  * `TokenAuthentication`

* **DRF Permission Classes**

  * `IsAuthenticated`

* **Queryset Filtering**

  * Data filtered by `request.user`
  * Prevents access to other users’ data

* **Validation Logic**

  * Serializer-level checks enforce ownership and constraints

---

## Security Considerations

### Token Security

* Tokens are required for all protected endpoints
* Tokens must be included in every request
* Invalid or missing tokens return `401 Unauthorized`

---

### Data Isolation

* All queries scoped to the authenticated user
* Prevents cross-user data access
* Enforced consistently across all endpoints

---

### Public vs Private Data

* Public exercises allow reuse across users
* Private exercises remain isolated
* Creation rules prevent non-admin users from creating public data

---

## Error Responses

Common permission-related responses:

* `401 Unauthorized` → Missing or invalid token
* `403 Forbidden` → Attempt to modify restricted resources
* `400 Bad Request` → Invalid input or authentication failure

---

## Design Decisions

### Token Authentication over JWT

* Simpler implementation
* Sufficient for this use case
* Reduces complexity in token management

---

### Queryset-Based Ownership Enforcement

* Ensures consistent data isolation
* Avoids reliance on client-side filtering
* Centralised control of access rules

---

### Public + Private Exercise Model

* Enables reuse of common exercises
* Maintains user-level customisation
* Balances flexibility with data isolation

---

## Summary

The authentication and permission system ensures:

* Secure access via token authentication
* Strict ownership of user data
* Controlled sharing of public resources
* Consistent enforcement across all endpoints

This design supports a scalable and secure backend for multi-user workout management.
## Authentication method
- token-based auth

## Authorisation rules
- user can only access own workouts
- public exercises readable by all
- private exercises scoped to owner
- no cross-user modification

## Enforcement approach
- queryset filtering by request.user
- permission classes if used

## Security considerations
- no user_id query exposure
- no trust in client-side filtering
