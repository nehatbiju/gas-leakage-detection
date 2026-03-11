# Installation & Setup Guide

## Prerequisites

- **Python**: 3.8 or higher
- **pip**: Package manager for Python
- **Git** (optional): For version control
- **RAM**: Minimum 2GB
- **Disk Space**: 500MB available

## Quick Start (5 minutes)

### 1. Navigate to Project Directory
```bash
cd d:\aise
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Run the Application
```bash
python app.py
```

### 4. Access the Dashboard
Open your web browser and navigate to:
```
http://localhost:5001
```

Default credentials:
- **Username**: admin
- **Password**: admin123

---

## Detailed Installation Steps

### Step 1: Python Installation (if needed)

#### Windows
1. Download Python from [python.org](https://www.python.org/downloads/)
2. Run the installer
3. **Important**: Check "Add Python to PATH"
4. Click "Install Now"

Verify installation:
```bash
python --version
pip --version
```

### Step 2: Clone/Download Project

If using Git:
```bash
git clone <repository-url>
cd aise
```

Or manually download and extract the project folder.

### Step 3: Create Virtual Environment (Recommended)

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate
```

### Step 4: Install Dependencies

```bash
pip install -r requirements.txt
```

Expected output:
```
Successfully installed flask-2.3.3 flask-socketio-5.3.6 ...
```

### Step 5: Run the Application

```bash
python app.py
```

Expected output:
```
============================================================
Starting Gas Leak Detection System
============================================================
Database initialized successfully
ML model loaded successfully
Sensor simulation thread started
============================================================
Application running on 0.0.0.0:5001
Dashboard: http://localhost:5001
============================================================
```

### Step 6: Access Dashboard

1. Open web browser
2. Go to `http://localhost:5001`
3. See real-time sensor data and predictions

---

## Configuration

### Environment Variables

Create a `.env` file in the project root (optional):

```bash
FLASK_ENV=development
FLASK_DEBUG=True
LOG_LEVEL=DEBUG
SECRET_KEY=your-secret-key-here
```

### Configuration File

Edit `config.py` to customize:

```python
# Sensor thresholds
SENSOR_CONFIG = {
    'mq4_normal_range': (120, 220),
    'mq4_alert_threshold': 500,
}

# ML model parameters
MODEL_CONFIG = {
    'test_size': 0.2,
    'cv_folds': 5,
}

# Alert settings
ALERT_CONFIG = {
    'low_threshold': 0.3,
    'medium_threshold': 0.7,
}
```

---

## Project Structure

```
d:\aise\
├── app.py                      # Main Flask application
├── enhanced_ml_model.py        # ML model implementation
├── config.py                   # Configuration management
├── logger.py                   # Logging setup
├── database.py                 # Database manager
├── requirements.txt            # Python dependencies
├── synthetic_gas_leak.csv      # Training data
├── gas_leak_model.pkl         # Trained model (auto-generated)
├── gas_monitoring.db          # SQLite database (auto-generated)
├── logs/                      # Log files directory
│   └── app.log               # Application log
├── templates/                 # HTML templates
│   ├── base.html
│   ├── dashboard.html
│   ├── devices.html
│   ├── alerts.html
│   ├── analytics.html
│   └── settings.html
├── README.md                  # Project overview
├── ARCHITECTURE.md            # System design documentation
└── PROJECT_REPORT.md          # Detailed technical report
```

---

## Troubleshooting

### Issue: Module not found (ImportError)

**Solution**: Install missing dependencies
```bash
pip install -r requirements.txt
```

### Issue: Port 5001 is already in use

**Solution**: Change port in `app.py`
```python
socketio.run(app, host='0.0.0.0', port=5002)  # Use different port
```

### Issue: Database locked error

**Solution**: Close all instances and restart
```bash
# Kill all Python processes
# Windows:
taskkill /F /IM python.exe
# macOS/Linux:
pkill python
```

Then restart:
```bash
python app.py
```

### Issue: ML model file not found

**Solution**: Model will auto-train on first run. Wait for completion (2-3 minutes)
```bash
# Check logs
type logs\app.log  # Windows
cat logs/app.log   # macOS/Linux
```

### Issue: Dashboard not loading

**Solution**: 
1. Check if Flask is running: Look for "Serving Flask app"
2. Clear browser cache: Ctrl+Shift+Delete (or Cmd+Shift+Delete on Mac)
3. Try incognito mode: Ctrl+Shift+N (or Cmd+Shift+N on Mac)
4. Check browser console for errors: Press F12

---

## Database Setup

The database is automatically initialized on first run. To reset:

```bash
# Delete the database
del gas_monitoring.db  # Windows
rm gas_monitoring.db   # macOS/Linux

# Restart the application - it will recreate the database
python app.py
```

---

## ML Model Training

### First Time Training (Automatic)
- Takes 2-3 minutes
- Uses `synthetic_gas_leak.csv` as training data
- Saves model to `gas_leak_model.pkl`
- Performs hyperparameter tuning

### Retraining Model
```python
from enhanced_ml_model import EnhancedGasLeakDetector

detector = EnhancedGasLeakDetector()
X, y, df = detector.load_and_preprocess_data("synthetic_gas_leak.csv")
detector.train_models(X, y)
detector.evaluate_models()
detector.plot_results()
detector.save_model('gas_leak_model.pkl')
```

### Model Performance
```
Random Forest:   100% ROC-AUC
Gradient Boost:  ~98% ROC-AUC  
SVM:            ~95% ROC-AUC
```

---

## Running Tests

### Health Check
```bash
curl http://localhost:5001/api/health
```

Expected response:
```json
{
  "status": "healthy",
  "model_loaded": true,
  "simulation_running": true
}
```

### Get Current Readings
```bash
curl http://localhost:5001/api/current_readings
```

### Make a Prediction
```bash
curl -X POST http://localhost:5001/api/predict \
  -H "Content-Type: application/json" \
  -d '{"mq4_ppm": 150, "mq7_ppm": 45, "mq135_ppm": 120, "temperature": 27.5}'
```

---

## Performance Optimization

### For Production

1. **Disable Debug Mode**
   ```python
   app.config['DEBUG'] = False
   ```

2. **Use Production Server** (instead of Flask dev server)
   ```bash
   pip install gunicorn
   gunicorn --workers 4 app:app
   ```

3. **Enable HTTPS/SSL**
   Use a reverse proxy like Nginx

4. **Database Optimization**
   - Add connection pooling
   - Optimize queries with indices
   - Archive old sensor data

5. **ML Model Optimization**
   - Use GPU acceleration (CUDA)
   - Model compression for faster inference

---

## Logging

### View Logs
```bash
# Real-time log viewing
tail -f logs/app.log  # macOS/Linux
Get-Content logs\app.log -Tail 20 -Wait  # Windows

# View all logs
type logs\app.log  # Windows
cat logs/app.log   # macOS/Linux
```

### Log Levels
- **DEBUG**: Detailed diagnostic information
- **INFO**: General informational messages
- **WARNING**: Warning messages
- **ERROR**: Error messages
- **CRITICAL**: Critical failures

---

## Development Setup

### Install Development Dependencies
```bash
pip install -r requirements-dev.txt  # If available
pip install pytest black flake8  # Manual install
```

### Format Code
```bash
black *.py
```

### Run Lint
```bash
flake8 *.py
```

---

## Support & Documentation

- **API Documentation**: Check inline docstrings
- **Code Examples**: See function docstrings
- **Architecture Details**: See `ARCHITECTURE.md`
- **Technical Report**: See `PROJECT_REPORT.md`

---

## License

© 2024 Gas Leak Detection System. All rights reserved.
