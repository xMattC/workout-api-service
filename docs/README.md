# Documentation

This directory contains supporting documentation for the Workout API.

The goal of these documents is to explain how the system is used, how core backend behaviour is implemented, and how the main domain models are structured.

---

## Contents

### API Usage

- [API Usage Guide](./api-usage.md)  
  Practical guide for authenticating, exploring endpoints, and working with common API flows.

- [Authentication & Permissions](./auth-and-permissions.md)  
  Explains token authentication, ownership rules, and how access control is enforced across the API.

---

### Architecture

- [Workout API Architecture](./workout-api-architecture.md)  
  Describes the core workout domain model, including workouts, exercises, tags, and the `WorkoutExercise` intermediate model.

- [User API Architecture](./user-api-architecture.md)  
  Explains the user system, including the custom user model, serializers, views, and request flow for authentication and profile management.

---

### Quality & Testing

- [Testing](./testing.md)  
  Overview of the testing strategy, including validation, ownership rules, nested relationships, and API behaviour.

---

## Notes

- The main project overview is available in the repository root `README.md`
- Swagger/OpenAPI documentation is available from the running application
  
