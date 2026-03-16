# User API Architecture

This document describes the architecture and request flow for the User
API within the Django REST backend.

The user module currently provides endpoints for:

-   creating a user account
-   obtaining an authentication token
-   retrieving and updating the authenticated user's profile

These endpoints are exposed under: `/api/user/`

------------------------------------------------------------------------

# User API Request Flow

The following diagram illustrates how requests flow through the Django
REST framework stack when interacting with the user endpoints.

``` mermaid
flowchart TD

Client["Client / Browser"] --> Router["Django URL Router (app/urls.py)"]

Router --> UserRouter["User Router (user/urls.py)"]

UserRouter --> CreateUser["CreateUserView"]
UserRouter --> Token["CreateTokenView"]
UserRouter --> ManageUser["ManageUserView"]

CreateUser --> Serializer["UserSerializer"]
ManageUser --> Serializer

Serializer --> Model["Custom User Model"]
Model --> DB["PostgreSQL Database"]
```

The core processing pipeline:

1.  An HTTP request arrives from a client.
2.  Django routes the request using the root URL configuration.
3.  The request is dispatched to the user application router.
4.  A Django REST Framework view handles the request.
5.  A serializer validates and converts incoming data.
6.  The custom user model persists the data via the Django ORM.
7.  The data is stored in PostgreSQL.

------------------------------------------------------------------------

# URL Routing

The root router is defined in: `app/urls.py`

Requests beginning with `/api/user/` are delegated to the user
application router: `path("api/user/", include("user.urls"))`

The user router (`user/urls.py`) maps specific endpoints to views.

  |Endpoint              |Method              |View
  |--------------------- |------------------- |-------------------
  |`/api/user/create/`   |POST                |`CreateUserView`
  |`/api/user/token/`    |POST                |`CreateTokenView`
  |`/api/user/me/`       |GET / PUT / PATCH   |`ManageUserView`

------------------------------------------------------------------------

# View Layer

The API uses Django REST Framework generic views, which provide
built-in request handling.

### CreateUserView

`CreateAPIView`

Responsible for creating new user accounts.

`Request → Serializer validation → User creation → Response`

------------------------------------------------------------------------

### CreateTokenView

`ObtainAuthToken`

Authenticates a user and returns a token.

`Request credentials → authenticate() → token returned`

------------------------------------------------------------------------

### ManageUserView

`RetrieveUpdateAPIView`

Allows an authenticated user to retrieve or update their profile.

Supported methods:

-   GET
-   PUT
-   PATCH

Authentication is handled using: `TokenAuthentication`

------------------------------------------------------------------------

# Serializer Layer

Serializers perform validation and translation between JSON and
Django models.

The main serializer used by the user API is:

`UserSerializer`

Responsibilities include:

-   validating incoming user data
-   enforcing password rules
-   converting JSON payloads to model instances
-   hashing passwords before storage

------------------------------------------------------------------------

# Model Layer

The project uses a custom user model configured in Django settings:

`AUTH_USER_MODEL = "core.User"`

This model:

-   extends `AbstractBaseUser`
-   uses email as the username
-   integrates with Django authentication
-   stores user credentials securely using hashed passwords

User creation logic is handled by a custom user manager.

------------------------------------------------------------------------

# Database

All user data is persisted via the Django ORM to a PostgreSQL
database.

Database configuration is defined in:

`settings.py`

The backend connects to PostgreSQL using environment variables supplied
by Docker.
