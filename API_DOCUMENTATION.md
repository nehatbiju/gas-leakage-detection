# API Documentation

## Overview
REST API endpoints for the Gas Leak Detection System. All responses are JSON format.

## Base URL
```
http://localhost:5001/api
```

---

## Authentication
Currently, the API has no authentication. In production, implement:
- JWT tokens
- API keys
- OAuth 2.0

---

## Endpoints

### 1. Get Current Sensor Readings
**Endpoint**: `GET /api/current_readings`

**Description**: Get the latest sensor readings and ML prediction

**Parameters**: None

**Response Success (200)**:
```json
{
  "mq4_ppm": 156.23,
  "mq7_ppm": 48.12,
  "mq135_ppm": 125.45,
  "temperature": 27.8,
  "timestamp": "2024-03-11T10:30:45.123456",
  "prediction": 0,
  "probability_safe": 0.987,
  "probability_leak": 0.013,
  "risk_level": "LOW"
}
```

**Example**:
```bash
curl http://localhost:5001/api/current_readings
```

---

### 2. Get Historical Sensor Data
**Endpoint**: `GET /api/historical_data`

**Description**: Query historical sensor readings with optional time window

**Parameters**:
| Name | Type | Default | Description |
|------|------|---------|-------------|
| hours | integer | 24 | Hours of historical data to retrieve (1-8760) |

**Response Success (200)**:
```json
[
  {
    "timestamp": "2024-03-11T10:30:00",
    "mq4_ppm": 156.23,
    "mq7_ppm": 48.12,
    "mq135_ppm": 125.45,
    "temperature": 27.8,
    "prediction": 0,
    "probability_leak": 0.013,
    "risk_level": "LOW"
  },
  ...
]
```

**Examples**:
```bash
# Last 24 hours (default)
curl http://localhost:5001/api/historical_data

# Last 7 days
curl http://localhost:5001/api/historical_data?hours=168

# Last 1 hour
curl http://localhost:5001/api/historical_data?hours=1
```

---

### 3. Get Active Alerts
**Endpoint**: `GET /api/alerts`

**Description**: Get all unresolved alerts

**Parameters**: None

**Response Success (200)**:
```json
[
  {
    "id": 1,
    "timestamp": "2024-03-11T10:25:30",
    "type": "Gas Leak Detected",
    "severity": "HIGH",
    "message": "Gas leak detected with 87.23% confidence",
    "resolved": false
  },
  ...
]
```

**Example**:
```bash
curl http://localhost:5001/api/alerts
```

---

### 4. Resolve Alert
**Endpoint**: `POST /api/resolve_alert/<alert_id>`

**Description**: Mark an alert as resolved

**Parameters**:
| Name | Type | Location | Description |
|------|------|----------|-------------|
| alert_id | integer | URL path | ID of alert to resolve |

**Request Body**: None

**Response Success (200)**:
```json
{
  "success": true
}
```

**Response Error (500)**:
```json
{
  "error": "Failed to resolve alert"
}
```

**Example**:
```bash
curl -X POST http://localhost:5001/api/resolve_alert/1
```

---

### 5. Make ML Prediction
**Endpoint**: `POST /api/predict`

**Description**: Make a gas leak prediction based on sensor readings

**Request Headers**:
```
Content-Type: application/json
```

**Request Body**:
```json
{
  "mq4_ppm": 150.0,
  "mq7_ppm": 45.0,
  "mq135_ppm": 120.0,
  "temperature": 27.5
}
```

**Response Success (200)**:
```json
{
  "prediction": 0,
  "probability_safe": 0.98,
  "probability_leak": 0.02,
  "risk_level": "LOW"
}
```

**Response Error (400)**:
```json
{
  "error": "Missing required sensor data: {...}"
}
```

**Response Error (503)**:
```json
{
  "error": "Model not loaded"
}
```

**Example**:
```bash
curl -X POST http://localhost:5001/api/predict \
  -H "Content-Type: application/json" \
  -d '{"mq4_ppm": 150, "mq7_ppm": 45, "mq135_ppm": 120, "temperature": 27.5}'
```

---

### 6. Toggle Gas Shutoff Valve
**Endpoint**: `POST /api/toggle_shutoff`

**Description**: Control the emergency gas shutoff valve

**Request Headers**:
```
Content-Type: application/json
```

**Request Body**:
```json
{
  "action": "on"
}
```

**Valid Actions**: `"on"` or `"off"`

**Response Success (200)**:
```json
{
  "success": true,
  "action": "on"
}
```

**Response Error (400)**:
```json
{
  "error": "Invalid action"
}
```

**Examples**:
```bash
# Turn off the valve
curl -X POST http://localhost:5001/api/toggle_shutoff \
  -H "Content-Type: application/json" \
  -d '{"action": "off"}'

# Turn on the valve
curl -X POST http://localhost:5001/api/toggle_shutoff \
  -H "Content-Type: application/json" \
  -d '{"action": "on"}'
```

---

### 7. System Health Check
**Endpoint**: `GET /api/health`

**Description**: Check system status and health

**Parameters**: None

**Response Success (200)**:
```json
{
  "status": "healthy",
  "timestamp": "2024-03-11T10:30:45.123456",
  "model_loaded": true,
  "simulation_running": true
}
```

**Response Error (503)**:
```json
{
  "status": "unhealthy",
  "error": "Model initialization failed"
}
```

**Example**:
```bash
curl http://localhost:5001/api/health
```

---

## Response Codes

| Code | Meaning | Common Causes |
|------|---------|---------------|
| 200 | OK | Request successful |
| 400 | Bad Request | Invalid parameters or input |
| 404 | Not Found | Endpoint doesn't exist |
| 500 | Internal Error | Server error, check logs |
| 503 | Service Unavailable | Model not loaded or database issue |

---

## Data Types

### SensorReading
```json
{
  "mq4_ppm": 150.0,        // Methane concentration (ppm)
  "mq7_ppm": 45.0,         // Carbon monoxide (ppm)
  "mq135_ppm": 120.0,      // Air quality (ppm)
  "temperature": 27.5,     // Temperature (celsius)
  "timestamp": "ISO-8601"  // Timestamp
}
```

### Prediction
```json
{
  "prediction": 0,           // 0=Safe, 1=Leak
  "probability_safe": 0.98,  // Confidence of safety (0-1)
  "probability_leak": 0.02, // Confidence of leak (0-1)
  "risk_level": "LOW"        // LOW, MEDIUM, or HIGH
}
```

### Alert
```json
{
  "id": 1,
  "timestamp": "ISO-8601",
  "type": "Gas Leak Detected",
  "severity": "HIGH",     // HIGH, MEDIUM, LOW
  "message": "...",
  "resolved": false
}
```

---

## Risk Levels

| Level | Probability | Action |
|-------|-------------|--------|
| LOW | < 30% | Monitor |
| MEDIUM | 30-70% | Alert & Log |
| HIGH | > 70% | Alert & Shutoff |

---

## Error Handling

All errors follow this format:
```json
{
  "error": "Human-readable error message"
}
```

### Common Errors

**Missing Parameters**:
```json
{
  "error": "Missing required sensor data: {'mq4_ppm', 'temperature'}"
}
```

**Invalid Data Type**:
```json
{
  "error": "Temperature must be a number"
}
```

**Model Not Ready**:
```json
{
  "error": "Model not loaded"
}
```

---

## Rate Limiting

Current implementation has no rate limiting. For production:
- Implement 100 requests/minute per IP
- Cache frequently accessed endpoints
- Use CDN for static assets

---

## CORS Configuration

WebSocket cross-origin access is allowed from all origins (`"*"`). In production:
```python
socketio = SocketIO(app, cors_allowed_origins=[
    "https://yourdomain.com",
    "https://app.yourdomain.com"
])
```

---

## WebSocket Events

### Events Emitted by Server

**sensor_update**: Sent every 2 seconds
```json
{
  "mq4_ppm": 150.0,
  "mq7_ppm": 45.0,
  "mq135_ppm": 120.0,
  "temperature": 27.5,
  "prediction": 0,
  "probability_leak": 0.013,
  "risk_level": "LOW",
  "timestamp": "2024-03-11T10:30:45"
}
```

**alert**: Sent when alert is triggered
```json
{
  "type": "Gas Leak Detected",
  "severity": "HIGH",
  "message": "Gas leak detected with 87% confidence",
  "timestamp": "2024-03-11T10:30:45"
}
```

---

## Example Workflow

### 1. Start System
```bash
python app.py
```

### 2. Check Health
```bash
curl http://localhost:5001/api/health
```

### 3. Get Current Readings
```bash
curl http://localhost:5001/api/current_readings
```

### 4. Query Last Hour of Data
```bash
curl http://localhost:5001/api/historical_data?hours=1
```

### 5. Get Alerts
```bash
curl http://localhost:5001/api/alerts
```

### 6. Resolve Alert
```bash
curl -X POST http://localhost:5001/api/resolve_alert/1
```

### 7. Trigger Manual Prediction
```bash
curl -X POST http://localhost:5001/api/predict \
  -H "Content-Type: application/json" \
  -d '{"mq4_ppm": 850, "mq7_ppm": 300, "mq135_ppm": 750, "temperature": 28}'
```

---

## Performance Tips

1. **Batch Requests**: Combine multiple queries into one
2. **Caching**: Cache `current_readings` for 10 seconds
3. **Compression**: Enable gzip compression on responses
4. **Pagination**: For large datasets, implement pagination

---

## Security Notes

- All endpoints should use HTTPS in production
- Implement authentication for write operations
- Validate and sanitize all inputs
- Implement rate limiting
- Log all API access

---

## Changelog

**v2.0** (Current)
- Added comprehensive error handling
- Added health check endpoint
- Improved logging throughout
- Added environment configuration

**v1.0**
- Initial release
