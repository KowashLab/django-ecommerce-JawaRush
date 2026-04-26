# JWT Authentication Testing Guide

## API Endpoints

- **Obtain Token**: `POST /api/token/`
- **Refresh Token**: `POST /api/token/refresh/`
- **Products**: `GET /api/products/` (no auth required)
- **Categories**: `GET /api/categories/` (no auth required)
- **Orders**: `GET /api/orders/` (requires JWT authentication)

## Testing with curl

### 1. Obtain JWT Token

Replace `username` and `password` with actual credentials:

```bash
curl -X POST http://localhost:8000/api/token/ \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser","password":"testpass"}'
```

Response example:
```json
{
  "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

Copy the `access` token for the next requests.

### 2. Access Protected Orders Endpoint

Replace `YOUR_ACCESS_TOKEN` with the token from step 1:

```bash
curl -X GET http://localhost:8000/api/orders/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### 3. Refresh Token

Use the `refresh` token to get a new `access` token:

```bash
curl -X POST http://localhost:8000/api/token/refresh/ \
  -H "Content-Type: application/json" \
  -d '{"refresh":"YOUR_REFRESH_TOKEN"}'
```

Response:
```json
{
  "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

## Testing with Postman

1. **Obtain Token**:
   - Method: POST
   - URL: `http://localhost:8000/api/token/`
   - Body (JSON): `{"username":"testuser","password":"testpass"}`
   - Click Send

2. **Set Authorization Header**:
   - In the response, copy the `access` token value
   - Go to the "Authorization" tab
   - Select "Bearer Token" from the "Type" dropdown
   - Paste the token in the "Token" field

3. **Access Orders**:
   - Method: GET
   - URL: `http://localhost:8000/api/orders/`
   - Click Send (Postman will automatically add the Bearer token)

## Architecture

- **Website Authentication**: Uses Django sessions (unchanged)
- **API Authentication**: Uses JWT tokens (new)
- **Session Auth Still Works**: The API also accepts session cookies for development
- **OrderViewSet**: Protected by `IsAuthenticated` permission
  - Only authenticated users can access their own orders
  - Anonymous users get 401 Unauthorized

## Token Details

- **Access Token Lifetime**: 1 hour
- **Refresh Token Lifetime**: 7 days
- **Algorithm**: HS256 (HMAC SHA-256)
- **Stored Secret**: Uses Django SECRET_KEY

## Security Notes

1. Tokens are signed with your Django SECRET_KEY
2. Keep tokens safe; treat like passwords
3. Access tokens expire after 1 hour; use refresh token to get new one
4. Never hardcode tokens in code; use environment variables or secure storage
5. In production, serve API over HTTPS only
