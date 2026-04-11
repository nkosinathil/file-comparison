# Aurex API Documentation

## Base URL

```
Production: https://aurex.example.com/api
Development: http://localhost:8000/api
```

## Authentication

All API endpoints require an API key in the header:

```
X-API-Key: your_api_key_here
```

## Endpoints

### Health Check

```http
GET /health
```

**Response**:
```json
{
  "status": "healthy",
  "service": "aurex-backend"
}
```

---

## Cases

### List Cases

```http
GET /api/cases
```

**Query Parameters**:
- `skip` (int): Pagination offset (default: 0)
- `limit` (int): Results per page (default: 100, max: 1000)
- `status` (string): Filter by status (pending, processing, completed, error, cancelled)

**Response**:
```json
[
  {
    "id": "CASE001_20260410_120000",
    "case_name": "FNB Analysis Q1",
    "evidence_number": "EV-2026-001",
    "timezone": "Africa/Johannesburg",
    "status": "completed",
    "processed_files": 25,
    "total_files": 25,
    "total_transactions": 1247,
    "date_range": "2026-01-01 to 2026-03-31",
    "created_at": "2026-04-10T12:00:00Z",
    "updated_at": "2026-04-10T14:30:00Z"
  }
]
```

### Create Case

```http
POST /api/cases
```

**Request Body**:
```json
{
  "case_name": "FNB Analysis Q1",
  "evidence_number": "EV-2026-001",
  "timezone": "Africa/Johannesburg",
  "input_folder": "/path/to/pdfs",
  "output_folder": "/path/to/output"
}
```

**Response** (201 Created):
```json
{
  "id": "CASE001_20260410_120000",
  "case_name": "FNB Analysis Q1",
  "status": "pending",
  "created_at": "2026-04-10T12:00:00Z"
}
```

### Get Case

```http
GET /api/cases/{case_id}
```

**Response**:
```json
{
  "id": "CASE001_20260410_120000",
  "case_name": "FNB Analysis Q1",
  "evidence_number": "EV-2026-001",
  "status": "completed",
  "processed_files": 25,
  "total_files": 25,
  "total_transactions": 1247
}
```

### Delete Case

```http
DELETE /api/cases/{case_id}
```

**Response** (204 No Content)

---

## Processing

### Start Processing

```http
POST /api/processing/{case_id}/start
```

**Response**:
```json
{
  "case_id": "CASE001_20260410_120000",
  "status": "queued",
  "message": "Processing started"
}
```

### Get Processing Status

```http
GET /api/processing/{case_id}/status
```

**Response**:
```json
{
  "case_id": "CASE001_20260410_120000",
  "status": "processing",
  "progress": 0.45,
  "current_file": "62275063536_20240420.pdf",
  "message": "Processing file 12 of 25"
}
```

**Status Values**:
- `pending` - Not started
- `queued` - In queue
- `processing` - Currently processing
- `completed` - Finished successfully
- `error` - Failed with error
- `cancelled` - Cancelled by user

### Cancel Processing

```http
POST /api/processing/{case_id}/cancel
```

**Response**:
```json
{
  "case_id": "CASE001_20260410_120000",
  "status": "cancelled",
  "message": "Processing cancelled"
}
```

---

## Analysis

### Get Insights

```http
GET /api/analysis/{case_id}/insights
```

**Response**:
```json
{
  "total_transactions": 1247,
  "total_debit": -125430.50,
  "total_credit": 180250.00,
  "date_range": {
    "min": "2026-01-01",
    "max": "2026-03-31"
  },
  "categories": {
    "Groceries": 15420.30,
    "Fuel": 8750.00,
    "Entertainment": 3210.50,
    "Insurance": 2500.00
  },
  "monthly_trend": {
    "2026-01": 42150.20,
    "2026-02": 38920.10,
    "2026-03": 44360.20
  },
  "top_counterparties": [
    {
      "name": "WOOLWORTHS",
      "count": 45,
      "total": 8750.30
    }
  ]
}
```

### Get Network Data

```http
GET /api/analysis/{case_id}/network
```

**Response**:
```json
{
  "nodes": [
    {
      "id": "ACC_62275063536",
      "label": "Account ***3536",
      "group": "account"
    },
    {
      "id": "PARTY_WOOLWORTHS",
      "label": "WOOLWORTHS",
      "group": "counterparty"
    }
  ],
  "edges": [
    {
      "from": "ACC_62275063536",
      "to": "PARTY_WOOLWORTHS",
      "amount": 8750.30,
      "count": 45
    }
  ]
}
```

### Get Transactions

```http
GET /api/analysis/{case_id}/transactions
```

**Query Parameters**:
- `skip` (int): Pagination offset
- `limit` (int): Results per page
- `category` (string): Filter by category

**Response**:
```json
{
  "transactions": [
    {
      "id": 1,
      "account_number": "62275063536",
      "transaction_date": "2026-01-15T10:30:00Z",
      "description": "WOOLWORTHS HYDE PARK",
      "amount": -245.50,
      "balance": 12450.30,
      "transaction_type": "debit",
      "category": "Groceries",
      "counterparty": "WOOLWORTHS"
    }
  ],
  "total": 1247,
  "page": 1
}
```

---

## Chat

### Ask Question

```http
POST /api/chat/{case_id}/ask
```

**Request Body**:
```json
{
  "question": "What were the top 5 expenses in January?"
}
```

**Response**:
```json
{
  "question": "What were the top 5 expenses in January?",
  "answer": "Based on the transactions in January 2026, the top 5 expenses were:\n1. Groceries - R 15,420.30\n2. Fuel - R 8,750.00\n3. Entertainment - R 3,210.50\n4. Insurance - R 2,500.00\n5. Utilities - R 1,850.20",
  "model": "llama2",
  "timestamp": "2026-04-10T12:30:00Z"
}
```

### Get Chat History

```http
GET /api/chat/{case_id}/history
```

**Query Parameters**:
- `limit` (int): Number of messages to return (default: 50)

**Response**:
```json
{
  "case_id": "CASE001_20260410_120000",
  "messages": [
    {
      "id": 1,
      "timestamp": "2026-04-10T12:30:00Z",
      "question": "What were the top 5 expenses?",
      "answer": "Based on the data...",
      "model": "llama2"
    }
  ]
}
```

---

## Error Responses

All endpoints may return the following error responses:

### 400 Bad Request
```json
{
  "error": "Invalid request",
  "detail": "case_name is required"
}
```

### 401 Unauthorized
```json
{
  "error": "Unauthorized",
  "detail": "Invalid or missing API key"
}
```

### 404 Not Found
```json
{
  "error": "Not Found",
  "detail": "Case not found"
}
```

### 500 Internal Server Error
```json
{
  "error": "Internal Server Error",
  "detail": "An unexpected error occurred"
}
```

### 503 Service Unavailable
```json
{
  "error": "Service Unavailable",
  "detail": "Database connection failed"
}
```

---

## Rate Limiting

API requests are rate limited to:
- 100 requests per minute per API key
- 1000 requests per hour per API key

Rate limit headers are included in responses:
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1712761800
```

---

## Webhooks (Future)

Webhooks for processing events will be available in a future release:
- `processing.started`
- `processing.progress`
- `processing.completed`
- `processing.failed`

---

## SDKs

Official SDKs are planned for:
- Python
- PHP
- JavaScript/TypeScript
- Java

---

## Support

For API support, contact: api-support@example.com
