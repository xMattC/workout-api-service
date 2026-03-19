## Test categories

- auth tests

- ownership tests

- validation tests

- API tests

## Critical guarantees

- cross-user access blocked

- invalid data rejected

- nested responses correct

## How to run tests

- "Do not describe every test. Describe what is proven."


# SYSTMES TESTS: 
## 1. Authentication system tests

Prove:

protected endpoints reject unauthenticated requests

token auth works

invalid token or missing token fails

## 2. Ownership system tests

Prove:

- user A cannot access user B’s workouts

- user A cannot edit user B’s exercises

- user A cannot delete user B’s workout-exercise rows

- These are among the most important tests in your project.

## 3. Validation system tests

Prove:

- negative sets rejected

- zero reps rejected

- duplicate order in same workout rejected

- invalid image rejected

- These should go through the API, not only serializer unit tests.

## 4. API contract tests

Prove:

- workout detail returns nested workout exercises

- filtered endpoint returns correct subset

- paginated endpoint returns expected structure

- This is about response usefulness and consistency.

## 5. Media system tests

Prove:

- valid image upload succeeds

- image is attached to the correct exercise

- bad file is rejected
