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
