# Hop & Barley - Django E-commerce

Hop & Barley is a Django-based e-commerce app for homebrewing supplies with web UI, REST API, and GraphQL analytics.

## Tech Stack

- Django
- Django REST Framework (DRF)
- PostgreSQL
- Docker / Docker Compose
- GraphQL (graphene-django)

## Quick Start

1. Start services:

```bash
docker compose up --build
```

2. Run migrations:

```bash
docker compose exec web python manage.py migrate
```

3. Seed demo data:

```bash
docker compose exec web python manage.py seed_products
```

App URL: http://localhost:8000

## API

- Swagger/OpenAPI docs: http://localhost:8000/api/docs/
- JWT obtain token: POST http://localhost:8000/api/token/
- JWT refresh token: POST http://localhost:8000/api/token/refresh/

Use JWT in protected endpoints:

```text
Authorization: Bearer <access_token>
```

## GraphQL

- Endpoint: http://localhost:8000/graphql/

Example query:

```graphql
query {
  totalOrders
  totalRevenue
  averageOrderValue
  topProducts {
    id
    name
    ordersCount
  }
}
```

## Testing

Run tests:

```bash
python manage.py test
```

Run tests with coverage:

```bash
coverage run manage.py test
coverage report
```

Current project coverage is around 90%+.

## License

This project is for educational purposes.
