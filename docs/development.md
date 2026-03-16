# Development Setup
This project is developed and run inside Docker containers. The goal is to keep the development environment consistent and avoid having to install Python, PostgreSQL, or other dependencies directly on the host machine.

Using Docker means the application and database always run with the same versions and configuration. This helps avoid common setup issues such as mismatched Python versions, missing system libraries, or differences between local development environments.

Another advantage is that the same container setup can be used when deploying the application. This helps keep development and production environments aligned, reducing the risk of problems caused by configuration differences between environments.

## Requirements

- Docker
- Docker Compose

Install instructions:
https://docs.docker.com/get-docker/

## Start the project

`docker-compose up`
This starts the Django application and the PostgreSQL database.

Once running, the API is available at:

http://localhost:8000

## Running Django Commands

Management commands should be run inside the app container.

### Run migrations

`docker-compose run --rm app python manage.py migrate`

### Create a superuser

`docker-compose run --rm app python manage.py createsuperuser`

### Run tests

`docker-compose run --rm app python manage.py test`

### Stopping the Environment

`docker-compose down`

