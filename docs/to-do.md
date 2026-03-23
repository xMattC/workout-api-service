# Backend App API – Final TODO List

## Phase 1: Core Domain Improvements
- Implement WorkoutExercise model:
  - Fields: workout, exercise, order, sets, reps, rest_seconds, optional notes
  - Validation:
    - sets > 0
    - reps > 0
    - order > 0
    - order unique per workout

- Move image handling to Exercise model:
  - Add image field
  - Add upload endpoint
  - Validate file type and size

---

## Phase 2: Public & Private Data Model
- Add public seeded exercises:
  - is_public = True
  - created_by = null

- Add private exercises:
  - is_public = False
  - created_by = user

- Enforce rules:
  - Public exercises are read-only
  - Users can only edit their own exercises
  - Prevent duplicate exercise names per user

---

## Phase 3: API Maturity
- Add filtering:
  - exercises by name/category
  - workouts by name/date

- Add search:
  - name-based search

- Add ordering:
  - name, created date

- Add pagination:
  - default page size
  - page navigation

---

## Phase 4: Derived Logic
- Add estimated duration:
  - based on sets, reps, rest
  - use default seconds per rep
  - expose:
    - per exercise duration
    - total workout duration

---

## Phase 5: Ownership Enforcement
- Ensure all querysets filter by request.user

- Add tests:
  - user cannot access other users’ workouts
  - user cannot modify other users’ data
  - public resources cannot be modified

---

## Phase 6: Validation & Rules
- Add serializer/model validation:
  - positive sets/reps
  - valid image uploads
  - no invalid relationships
  - enforce ownership on relations

---

## Phase 7: API Enhancements
- Nested workout detail:
  - include workout exercises + exercise data

- Add one summary endpoint:
  - total workout duration or stats

---

## Phase 8: Testing
- Auth tests
- Ownership tests
- Validation tests
- API response tests
- Media upload tests

---

## Phase 9: Documentation
- Rewrite README:
  - project overview
  - features
  - ownership rules
  - API examples
  - deployment info

- Add docs:
  - workout-api-architecture.md
  - auth-and-permissions.md
  - api-usage.md (optional)

---

## Phase 10: Deployment
- Deploy API publicly:
  - production settings
  - PostgreSQL
  - HTTPS

- Add to README:
  - live API URL
  - Swagger URL

---

## Phase 11: Presentation
- Add screenshots:
  - Swagger UI
  - workout detail response
  - filtering example

---

## Final Condition
- Live deployed API
- Clear README
- Strong domain model
- Tests proving rules
- Swagger usable externally
