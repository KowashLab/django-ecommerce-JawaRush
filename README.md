# Hop & Barley — Homebrewing Supply Store

An e-commerce web application for homebrewing supplies built with Django.

## Tech Stack

- **Backend:** Django 5.2, Django REST Framework
- **Database:** PostgreSQL 15
- **Admin UI:** Django Jazzmin
- **Containerization:** Docker & Docker Compose
- **Language:** Python 3.12

## Features

- **Product Catalog** — browsable product listings with categories, detail pages, and slug-based URLs
- **Shopping Cart** — session-based cart with add, remove, and quantity update
- **Checkout & Orders** — order placement with shipping details, payment method selection, and email notifications
- **User Authentication** — registration, login, logout (CSRF-protected POST), and account page with order history
- **Admin Panel** — Jazzmin-powered admin interface for managing products, categories, and orders

## Getting Started

### Prerequisites

- [Docker](https://docs.docker.com/get-docker/) and Docker Compose

### Run the Project

```bash
docker compose up --build
```

The application will be available at **http://localhost:8000**.

### Create a Superuser

With the containers running, open a shell in the web container:

```bash
docker compose exec web python manage.py createsuperuser
```

Follow the prompts to set a username, email, and password.

### Access the Admin Panel

Navigate to **http://localhost:8000/admin/** and log in with the superuser credentials created above.

## Project Structure

```
core/           — Django project settings and root URL configuration
products/       — Product and Category models, views, admin
orders/         — Order and OrderItem models, cart, checkout, payment views
users/          — Registration, login, logout, account views
reviews/        — Product reviews (app scaffold)
templates/      — Django HTML templates
static/         — CSS, JavaScript, and images
```

## Environment Variables

The following variables are configured via `compose.yaml`:

| Variable      | Default                              | Description          |
|---------------|--------------------------------------|----------------------|
| `DB_ENGINE`   | `django.db.backends.postgresql`      | Database backend     |
| `DB_NAME`     | `mydb`                               | Database name        |
| `DB_USER`     | `postgres`                           | Database user        |
| `DB_PASSWORD` | `password`                           | Database password    |
| `DB_HOST`     | `db`                                 | Database host        |
| `DB_PORT`     | `5432`                               | Database port        |

## License

This project is for educational purposes.
