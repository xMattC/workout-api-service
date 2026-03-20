
### System overview
- what the backend models
- how users interact with it

### Entities and relationships
- clear explanation of:
    - Exercise (public/private)
    - Workout
    - WorkoutExercise
    - program

### Why WorkoutExercise exists
-  not a simple join
- contains business fields (sets, reps, rest, order)

### Ownership model
- how user scoping works
- how public resources differ

### Data flow

- create workout
- add exercises
- retrieve workout with nested data

### Derived logic
- how estimated duration is calculated
- why it is approximate

### API design choices
- why nested responses are used
- why filtering/pagination is included
