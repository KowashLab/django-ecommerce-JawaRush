# Hop & Barley — Django E-commerce

Full-featured e-commerce platform for homebrewing supplies built with Django.

Includes:

* Web application (Django templates + sessions)
* REST API (DRF + JWT authentication)
* GraphQL analytics layer
* Dockerized infrastructure with PostgreSQL
* High test coverage and CI-ready setup

---

## Tech Stack

* Django
* Django REST Framework (DRF)
* GraphQL (graphene-django)
* PostgreSQL
* Docker / Docker Compose
* Coverage (testing)
* Flake8 (linting)

---

## Quick Start

```bash
docker compose up --build
docker compose exec web python manage.py migrate
docker compose exec web python manage.py seed_products
```

App: http://localhost:8000

---

## Authentication (JWT)

Obtain token:

```bash
POST /api/token/
```

Refresh token:

```bash
POST /api/token/refresh/
```

Use in requests:

```text
Authorization: Bearer <access_token>
```

---

## REST API

Swagger docs:

```
http://localhost:8000/api/docs/
```

Main endpoints:

* `/api/products/`
* `/api/categories/`
* `/api/orders/`
* `/api/cart/`
* `/api/products/{id}/reviews/`

---

## GraphQL Analytics

Endpoint:

```
http://localhost:8000/graphql/
```

Example:

```graphql
{
  totalOrders
  totalRevenue
  averageOrderValue
  revenueByDay {
    date
    revenue
  }
  topProducts {
    id
    name
    ordersCount
  }
}
```

---

## Testing

Run tests:

```bash
python manage.py test
```

Coverage:

```bash
coverage run manage.py test
coverage report
```

Coverage: **90%+**

---

## Infrastructure

* PostgreSQL database
* Docker Compose setup
* Environment-based configuration

---

## Project Structure

* `products/` — catalog logic
* `orders/` — cart and checkout
* `users/` — authentication and profiles
* `reviews/` — product reviews
* `api/` — REST API layer
* `analytics/` — GraphQL schema
* `templates/`, `static/` — frontend

---

## Notes

* Orders store price snapshots (OrderItem)
* Reviews allowed only after purchase
* Cart stored in session
* GraphQL used for analytics only (read-only)

---

## License

Educational project

---

## Author

* Name: Oleg Covas

---

## Checklist

* [x] Catalog with filters, search, pagination
* [x] Product page with reviews
* [x] Cart functionality
* [x] Checkout with email
* [x] User account and orders
* [x] REST API with JWT
* [x] Admin panel with analytics
* [x] Swagger documentation
* [x] Tests (90%+ coverage)
* [x] Docker setup
* [x] GraphQL analytics
