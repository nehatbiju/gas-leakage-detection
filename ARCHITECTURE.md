# Gas Leak Detection System - Architecture Documentation

## Overview
This document describes the system architecture, design patterns, and technical decisions for the AI-Powered Gas Leak Detection System.

## System Architecture

```
┌────────────────────────────────────────────────────────────────────┐
│                        Frontend (Web Dashboard)                    │
│                   (HTML5, CSS3, JavaScript, Charts.js)             │
└────────────────────────────────────────────────────────────────────┘
                              ▲ ▼ (WebSocket)
┌────────────────────────────────────────────────────────────────────┐
│                      Flask Web Application                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────────┐ │
│  │   Routes &   │  │   Socket.io  │  │   API Endpoints          │ │
│  │   Templates  │  │   Real-time  │  │   (RESTful JSON APIs)    │ │
│  └──────────────┘  └──────────────┘  └──────────────────────────┘ │
└────────────────────────────────────────────────────────────────────┘
         ▲ ▼                          ▲ ▼
┌──────────────────────┐    ┌──────────────────────────┐
│  Database Manager    │    │  ML Model Pipeline       │
│  (SQLite with)       │    │  ┌──────────────────┐    │
│  Connection Pooling  │    │  │ Feature Pipeline │    │
│  & Transactions      │    │  │ Ensemble Models  │    │
└──────────────────────┘    │  │ Prediction Srv.  │    │
                            └──────────────────────┘
                                    ▲ ▼
┌────────────────────────────────────────────────────────────┐
│                  Sensor Simulation Layer                   │
│         (Real-time Data Generation & Preprocessing)        │
└────────────────────────────────────────────────────────────┘
```

## Component Breakdown

### 1. **Frontend Layer**
- **Technology**: HTML5, CSS3, JavaScript
- **Framework**: Bootstrap 4 for responsive design
- **Charting**: Chart.js for real-time data visualization
- **Communication**: WebSocket (Flask-SocketIO) for live updates

**Pages:**
- `dashboard.html` - Real-time monitoring with live gauges and alerts
- `devices.html` - Sensor device management
- `alerts.html` - Alert history and management
- `analytics.html` - Analytics and predictive insights
- `settings.html` - System configuration

### 2. **Flask Application** (`app.py`)
**Responsibilities:**
- HTTP routing and view rendering
- REST API endpoints for data access
- WebSocket event handling
- Request validation and error handling
- Logging and monitoring

**Key Modules:**
```python
- Routes (Web Pages)
  ├── Dashboard, Devices, Alerts, Analytics, Settings
  
- API Endpoints (REST JSON)
  ├── /api/current_readings - Get latest sensor data
  ├── /api/historical_data - Query time-series data
  ├── /api/alerts - Get active alerts
  ├── /api/predict - Make ML predictions
  ├── /api/health - System health check
  └── /api/toggle_shutoff - Control gas valve
  
- WebSocket Events
  ├── connect - New client connection
  ├── disconnect - Client disconnection
  └── sensor_update (broadcast) - Real-time data push
```

### 3. **ML Model Pipeline** (`enhanced_ml_model.py`)

**Architecture:**
```
Raw Sensor Data
        ▼
Feature Engineering (8 features)
        ▼
Feature Selection (SelectKBest)
        ▼
Ensemble Learning (3 models)
     ├─ Random Forest (Best: 100% ROC-AUC)
     ├─ Gradient Boosting
     └─ Support Vector Machine
        ▼
Prediction & Confidence Scoring
        ▼
Risk Level Classification (LOW/MEDIUM/HIGH)
```

**Models Trained:**
1. **Random Forest Classifier**
   - 100+ decision trees
   - Robust to outliers
   - Feature importance rankings
   - Best overall performer

2. **Gradient Boosting Classifier**
   - Sequential ensemble learning
   - High precision for leak detection
   - Excellent for imbalanced data

3. **Support Vector Machine (SVM)**
   - Non-linear kernel (RBF)
   - Effective for high-dimensional data
   - Strong generalization

**Feature Engineering:**
- `mq4_ppm` - Methane concentration
- `mq7_ppm` - Carbon monoxide concentration
- `mq135_ppm` - Air quality index
- `temperature` - Environmental temperature
- `gas_ratio_1` - MQ4/MQ7 ratio
- `gas_ratio_2` - MQ135/MQ4 ratio
- `total_gas` - Combined gas reading
- `temp_normalized` - Temperature z-score

### 4. **Database Manager** (`database.py`)

**Database Schema:**

```sql
sensor_readings
├── id (PK)
├── timestamp
├── mq4_ppm (REAL)
├── mq7_ppm (REAL)
├── mq135_ppm (REAL)
├── temperature (REAL)
├── prediction (INTEGER 0/1)
├── probability_leak (REAL)
└── risk_level (TEXT)

alerts
├── id (PK)
├── timestamp
├── alert_type
├── severity (LOW/MEDIUM/HIGH)
├── message
└── resolved (BOOLEAN)

devices
├── id (PK)
├── device_name
├── location
├── status
└── last_seen

users
├── id (PK)
├── username (UNIQUE)
├── password
├── role
└── email
```

**Features:**
- Context manager for safe connections
- Automatic transaction handling
- Connection pooling
- Index optimization
- Error handling with logging

### 5. **Configuration Management** (`config.py`)

**Configuration Classes:**
- `Config` - Base configuration
- `DevelopmentConfig` - Debug enabled, verbose logging
- `ProductionConfig` - Optimized for production
- `TestingConfig` - For unit testing

**Manageable Settings:**
- Database paths
- Model parameters
- Sensor configuration
- Alert thresholds
- Logging levels
- Security settings

### 6. **Logging System** (`logger.py`)

**Features:**
- Rotating file handler (10MB max, 5 backups)
- Console output with formatting
- Structured logging with timestamps
- Log levels: DEBUG, INFO, WARNING, ERROR, CRITICAL

**Log File:** `logs/app.log`

## Data Flow

### 1. **Real-Time Sensor Monitoring**
```
Sensor Simulation
      ▼
Current Readings Update
      ▼
ML Prediction
      ▼
Database Storage
      ▼
Alert Evaluation
      ├─ If Leak Detected
      │  └─ Create Alert & Broadcast
      │
      └─ WebSocket Broadcast to Clients
```

### 2. **User Dashboard Update**
```
Client Connects (WebSocket)
      ▼
Send Current Readings
      ▼
Receive Real-time Updates Every 2 seconds
      ▼
Update Chart & Gauges
      ▼
Display Alerts as they occur
```

### 3. **Historical Data Query**
```
Client Request (/api/historical_data?hours=24)
      ▼
Database Query with time filter
      ▼
JSON Response with series data
      ▼
Client renders analytics chart
```

## Design Patterns Used

### 1. **Singleton Pattern**
- `DatabaseManager` - Single database instance
- `EnhancedGasLeakDetector` - Single model instance

### 2. **Observer Pattern**
- WebSocket for real-time event broadcasting
- Alert system for event notifications

### 3. **Context Manager Pattern**
- Database connection management
- Resource cleanup guarantee

### 4. **Pipeline Pattern**
- ML feature engineering → selection → prediction

### 5. **Factory Pattern**
- Configuration creation based on environment

## Error Handling Strategy

**Layers:**
```
API Route (Try-Catch)
        ▼
Validation & Type Checking
        ▼
Business Logic Execution
        ▼
Database Operation (with rollback)
        ▼
JSON Error Response with HTTP Status
```

**HTTP Status Codes:**
- `200 OK` - Success
- `400 Bad Request` - Invalid input
- `404 Not Found` - Resource not found
- `500 Internal Error` - Server error
- `503 Service Unavailable` - Model not loaded

## Security Considerations

1. **Input Validation**
   - Type checking on API parameters
   - Range validation for sensor data

2. **Database Security**
   - Parameterized queries (SQL injection prevention)
   - Session isolation

3. **Secret Management**
   - Environment variables for sensitive data
   - No hardcoded credentials in code

4. **CORS Configuration**
   - Controlled origin access
   - SocketIO CORS restrictions

## Performance Optimizations

1. **Database**
   - Indices on frequently queried columns
   - Query optimization with time filters
   - Connection pooling

2. **ML Model**
   - Feature selection (reduce dimensionality)
   - Pickle serialization for fast loading
   - Efficient prediction pipeline

3. **Frontend**
   - WebSocket for efficient real-time updates
   - Chart.js with optimized rendering
   - Responsive design for mobile

## Monitoring & Observability

**Logging:**
- Application events in rotating files
- Debug information for troubleshooting
- Alert triggers logged

**Health Check Endpoint:**
- `/api/health` - System status
- Model loaded status
- Simulation running status

**Metrics Tracked:**
- Alert counts with rate limiting
- Prediction confidence scores
- Response times
