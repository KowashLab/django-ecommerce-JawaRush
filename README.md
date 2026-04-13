# Hop & Barley — Homebrewing Supply Store

An e-commerce web application for homebrewing supplies built with Django.

## Tech Stack

- **Backend:** Django 5.2
- **Database:** PostgreSQL 15
- **Admin UI:** Django Jazzmin
- **Containerization:** Docker & Docker Compose
- **Language:** Python 3.12

## Features

- **Product Catalog** — browsable product listings with categories, filtering, search, sorting, and pagination
- **Shopping Cart** — session-based cart with add, remove, and quantity update
- **Checkout & Orders** — order placement with shipping details, payment method selection, and email notifications
- **User Authentication** — registration, login, logout (CSRF-protected POST), password change, and profile editing
- **Account** — order history with status filtering
- **Admin Panel** — Jazzmin-powered admin with order analytics (total orders, revenue)

## Getting Started

### Prerequisites

- [Docker](https://docs.docker.com/get-docker/) and Docker Compose

### Run the Project

```bash
git clone https://github.com/KowashLab/WebApp-JavaRush.git
cd WebApp-JavaRush
docker compose up --build
```

Open: **http://localhost:8000**

### Create a Superuser

```bash
docker compose exec web python manage.py createsuperuser
```

### Seed Products

```bash
docker compose exec web python manage.py seed_products
```

### Admin Panel

Navigate to **http://localhost:8000/admin/** and log in with the superuser credentials.

## Environment Variables

The project works out of the box with default values. To customize, copy `.env.example` to `.env`:

```bash
cp .env.example .env
```

| Variable      | Default      | Description        |
|---------------|--------------|--------------------|
| `SECRET_KEY`  | dev fallback | Django secret key  |
| `DEBUG`       | `True`       | Debug mode         |
| `DB_NAME`     | `postgres`   | Database name      |
| `DB_USER`     | `postgres`   | Database user      |
| `DB_PASSWORD` | `postgres`   | Database password  |
| `DB_HOST`     | `db`         | Database host      |
| `DB_PORT`     | `5432`       | Database port      |

## Project Structure

```
core/           — Django project settings and root URL configuration
products/       — Product and Category models, views, admin, seed command
orders/         — Order and OrderItem models, cart, checkout, payment views
users/          — Registration, login, logout, account, profile views
reviews/        — Product reviews model and admin
templates/      — Django HTML templates
static/         — CSS, JavaScript, and images
```

## License

This project is for educational purposes.
