# RESTful API

## Overview

Minarca Server provides a RESTful API that allows users to interact with the application programmatically. The API is accessible via the `/api` endpoint, and different endpoints provide access to various functionalities, including retrieving application information, managing user settings, working with access tokens, SSH keys, and repository settings.

## Authentication

The REST API endpoints (`/api`) supports two modes of authentication:

1. **Username and Password:** The same credentials used for authenticating via the web interface.
2. **Username and Access Token:** Access tokens act as passwords, and their scope may limit access to specific API endpoints. When Multi-Factor Authentication (MFA) is enabled, this mode is supported.

## Input Payloads

The Minarca Server RESTful API supports input payloads in two commonly used formats: `application/json` and `application/x-www-form-urlencoded`. This flexibility allows users to choose the payload format that best suits their needs when interacting with the API.

- **`application/json`**: Use this format for JSON-encoded data. The payload should be a valid JSON object sent in the request body.

- **`application/x-www-form-urlencoded`**: This format is suitable for URL-encoded data, typically used in HTML forms. Key-value pairs are sent in the request body with a `Content-Type` header set to `application/x-www-form-urlencoded`.

Please ensure that the appropriate `Content-Type` header is set in your API requests to match the payload format being used.

## Rate limits

REST API requests are subject to rate limit settings. These settings reduce the risk of Minarca Server instance being overloaded.

Minarca Server returns HTTP status code 429 for 1 hour, if 20 failed authentication requests were received in the same period of time from a single IP address. The same limit also applied to most POST method in the RESTful API.

This limit is configurable through the `rate-limit` settings.

### Example using cURL

Here's an example of using cURL to make a request to the Minarca Server API with a JSON payload:

```bash
# Example using application/json payload
curl -u admin:admin123 -X POST -H "Content-Type: application/json" -d '{"fullname": "John Doe", "email": "john@example.com", "lang": "en", "report_time_range": "30"}' https://example.com/api/currentuser
```

And for a request with `application/x-www-form-urlencoded` payload:

```bash
# Example using application/x-www-form-urlencoded payload
curl -u admin:admin123 -X POST -H "Content-Type: application/x-www-form-urlencoded" -d 'fullname=John%20Doe&email=john@example.com&lang=en&report_time_range=30' https://example.com/api/currentuser
```

Adjust the payload data and endpoint URL accordingly based on your specific use case.

---

All available endpoints are documented using the OpenAPI (Swagger) specification, accessible from your Minarca Server server at `https://example.com/api/openapi.json`. Access to the URL requires authentication.

```{toctree}
---
maxdepth: 3
---
endpoints
```

