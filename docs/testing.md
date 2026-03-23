# Testing Strategy and System Guarantees

This project uses automated tests to verify both isolated logic and full API behaviour.  

The test suite ensures that the backend enforces strict access control, correct domain logic, and consistent API responses.

## Test Layers

### Unit Tests
Unit tests validate isolated components such as:
- model methods and helpers
- serializer validation and transformation logic
- derived calculations (e.g. estimated duration)

These tests ensure internal logic behaves correctly in isolation.

### API / System Tests
API tests verify full request–response behaviour, including:
- authentication
- permissions and ownership
- database interaction
- response structure

These tests simulate real client usage via HTTP requests.

## System Guarantees

The following guarantees are enforced by application logic and verified by the automated test suite.

### Authentication

- Unauthenticated users cannot access protected endpoints (workouts, tags, exercises)
- All private API endpoints require valid authentication
- Authenticated users can access their own resources

### Ownership and Access Control

- Users can only access their own workouts
- Users cannot retrieve another user’s workout (returns 404)
- Users cannot update another user’s workout
- Users cannot delete another user’s workout

- Users can only access their own tags
- Users cannot modify another user’s tags

- Exercises and related entities are scoped to the authenticated user where applicable
- Public resources (if present) are read-only and cannot be modified by users

### Workout and Relationship Behaviour

- Workouts can be created, updated, and deleted by their owner
- Updating a workout does not allow reassignment of ownership
- Nested relationships (tags, exercises) are handled correctly during create and update

#### Tags
- New tags are created when provided in payloads
- Existing tags are reused (not duplicated)
- Updating tags replaces previous assignments
- Providing an empty list clears all tags from a workout

#### Exercises
- New exercises are created when provided in payloads
- Existing exercises are reused where possible
- Updating exercises replaces previous assignments
- Providing an empty list clears all exercises from a workout

### Validation and Data Integrity

- Invalid payloads are rejected with appropriate error responses
- Required fields must be provided when creating resources
- Invalid relationship data is not persisted
- Ownership constraints are enforced at all times
- Attempts to modify restricted fields (e.g. workout owner) are ignored

### API Response Behaviour

- List endpoints return only data belonging to the authenticated user
- Detail endpoints return complete and accurate resource representations
- Nested data (tags, exercises) is correctly serialized in responses
- Responses match expected serializer output

### Media Upload Handling

- Valid image uploads are accepted and stored correctly
- Uploaded images are associated with the correct workout
- Invalid image payloads are rejected with a 400 response
- File system state reflects successful uploads

## Continuous Verification

- All tests are automated and run via the standard Django test runner
- The full test suite is executed in CI on each change
- This ensures that all guarantees remain enforced as the code evolves

## Summary

The test suite verifies that the system:

- enforces strict user-level data isolation
- correctly manages relationships between workouts, tags, and exercises
- rejects invalid or inconsistent data
- provides reliable and predictable API responses
- safely handles file uploads

These guarantees ensure the backend behaves as a consistent, secure, and production-ready API.
