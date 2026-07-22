# ARES Authentication

ARES uses a dual authentication system: JWT tokens for user sessions
and API keys for service-to-service communication.

## JWT Tokens

### Getting a Token

The API validates JWT Bearer tokens sent in the `Authorization` header.
Tokens are created by the admin and distributed to clients.

### Token Format

Tokens use the HS256 algorithm and contain these claims:

- `sub` — Subject (user identifier)
- `role` — User role (admin, user, reader)
- `permissions` — List of permission strings
- `iat` — Issued at timestamp
- `exp` — Expiration timestamp
- `type` — Token type (access or refresh)

### Using a Token

```bash
curl -H "Authorization: Bearer <token>" http://localhost:8000/api/v1/predict
```

## API Keys

API keys are long-lived credentials for automated clients.

```bash
curl -H "X-API-Key: <key>" http://localhost:8000/api/v1/predict
```

## Python SDK

```python
from ares.client import Client

# Using API key
client = Client(
    base_url="http://localhost:8000",
    api_key="ares_abc123.def456..."
)

# Using JWT token
client = Client(
    base_url="http://localhost:8000",
    token="eyJhbGciOiJIUzI1NiIs..."
)

result = client.predict(question1="Hello", question2="Hi")
```

## Security Best Practices

1. Rotate secret keys regularly
2. Use short-lived access tokens (15-30 minutes)
3. Store API keys securely (environment variables, vault)
4. Use HTTPS in production
5. Enable rate limiting
6. Restrict CORS origins in production
