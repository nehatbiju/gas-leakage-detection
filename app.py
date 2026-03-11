"""
AI-Powered Gas Leak Detection System
Flask web application for real-time gas monitoring with machine learning predictions.

Author: Development Team
Version: 2.0
Last Updated: 2024
"""

from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from flask_socketio import SocketIO, emit
import pandas as pd
import numpy as np
import json
from datetime import datetime, timedelta
import threading
import time
import random
import logging
from functools import wraps
from pathlib import Path
from typing import Dict, Any

from enhanced_ml_model import EnhancedGasLeakDetector
from config import get_config, DevelopmentConfig
from logger import LoggerSetup, get_logger
from database import DatabaseManager


class SimpleGasDetector:
    """Fallback rule-based detector when ML model is unavailable"""
    
    def predict(self, sensor_data: Dict[str, float]) -> Dict[str, Any]:
        """
        Make rule-based prediction on sensor data.
        
        Args:
            sensor_data: Dictionary with sensor readings
        
        Returns:
            Dictionary with prediction and risk level
        """
        mq4 = sensor_data.get('mq4_ppm', 0)
        mq7 = sensor_data.get('mq7_ppm', 0)
        mq135 = sensor_data.get('mq135_ppm', 0)
        temp = sensor_data.get('temperature', 25)
        
        # Rule-based risk score
        risk_score = 0
        
        # MQ-4 (Methane) detection
        if mq4 > 800:
            risk_score += 0.6
        elif mq4 > 500:
            risk_score += 0.3
        elif mq4 > 300:
            risk_score += 0.1
        
        # MQ-7 (CO/Carbon Monoxide) detection
        if mq7 > 300:
            risk_score += 0.5
        elif mq7 > 150:
            risk_score += 0.2
        elif mq7 > 100:
            risk_score += 0.1
        
        # MQ-135 (Air Quality) detection
        if mq135 > 700:
            risk_score += 0.4
        elif mq135 > 400:
            risk_score += 0.2
        elif mq135 > 250:
            risk_score += 0.1
        
        # Temperature anomaly detection
        if temp > 35 or temp < 15:
            risk_score += 0.1
        
        # Normalize and determine prediction
        leak_probability = min(risk_score, 0.95)
        prediction = 1 if leak_probability > 0.7 else 0
        
        if leak_probability > 0.7:
            risk_level = 'HIGH'
        elif leak_probability > 0.3:
            risk_level = 'MEDIUM'
        else:
            risk_level = 'LOW'
        
        return {
            'prediction': prediction,
            'probability_safe': 1.0 - leak_probability,
            'probability_leak': leak_probability,
            'risk_level': risk_level
        }

# Initialize Flask app
app = Flask(__name__)
config = get_config()
app.config.from_object(config)

# Initialize logger
LoggerSetup.setup_logger(app.config)
logger = get_logger(__name__)

# Initialize SocketIO
socketio = SocketIO(app, cors_allowed_origins=app.config['SOCKETIO_CORS_ALLOWED_ORIGINS'])

# Initialize database
db_manager = DatabaseManager(str(app.config['DATABASE_PATH']))

# Global variables
detector = None
fallback_detector = SimpleGasDetector()  # Always available fallback
current_readings = {
    'mq4_ppm': 150.0,
    'mq7_ppm': 45.0,
    'mq135_ppm': 120.0,
    'temperature': 27.5,
    'timestamp': datetime.now().isoformat()
}
simulation_running = False
using_fallback_model = False

logger.info(f"Application initialized with {app.config.__class__.__name__} configuration")


# Utility functions for Model Management
def load_ml_model() -> bool:
    """
    Load or train the ML model with fallback to rule-based detection.
    
    Returns:
        True if model loaded/trained successfully
    """
    global detector, using_fallback_model
    try:
        detector = EnhancedGasLeakDetector()
        model_path = app.config['MODEL_PATH']
        
        if Path(model_path).exists():
            detector.load_model(str(model_path))
            logger.info("ML Model loaded successfully from disk")
            using_fallback_model = False
            return True
        else:
            logger.info("Model not found, attempting to train new model...")
            training_data = app.config['TRAINING_DATA_PATH']
            
            if not Path(training_data).exists():
                logger.warning(f"Training data not found: {training_data}")
                logger.warning("Using fallback rule-based detector")
                using_fallback_model = True
                return True
            
            try:
                X, y, df = detector.load_and_preprocess_data(str(training_data))
                detector.train_models(X, y)
                detector.evaluate_models()
                detector.plot_results()
                detector.save_model(str(model_path))
                logger.info("New model trained and saved successfully")
                using_fallback_model = False
                return True
            except Exception as train_error:
                logger.warning(f"Model training failed: {train_error}")
                logger.warning("Using fallback rule-based detector")
                using_fallback_model = True
                return True
            
    except Exception as e:
        logger.warning(f"Error setting up ML model: {e}")
        logger.warning("Using fallback rule-based detector")
        using_fallback_model = True
        return True


def simulate_sensor_data() -> None:
    """
    Simulate sensor data and make predictions periodically.
    Runs in a background thread.
    """
    global current_readings, simulation_running
    
    logger.info("Sensor simulation started")
    simulation_running = True
    alert_count = 0
    last_hour_reset = datetime.now()
    
    while simulation_running:
        try:
            # Reset alert count every hour
            if (datetime.now() - last_hour_reset).total_seconds() > 3600:
                alert_count = 0
                last_hour_reset = datetime.now()
            
            # Simulate normal readings with occasional spikes
            if random.random() < 0.05:  # 5% chance of leak simulation
                current_readings = {
                    'mq4_ppm': random.uniform(800, 1000),
                    'mq7_ppm': random.uniform(250, 350),
                    'mq135_ppm': random.uniform(700, 900),
                    'temperature': random.uniform(26, 30),
                    'timestamp': datetime.now().isoformat()
                }
                logger.debug("High-level readings simulated (potential leak scenario)")
            else:
                current_readings = {
                    'mq4_ppm': random.uniform(120, 220),
                    'mq7_ppm': random.uniform(30, 70),
                    'mq135_ppm': random.uniform(80, 160),
                    'temperature': random.uniform(25, 30),
                    'timestamp': datetime.now().isoformat()
                }
            
            # Make prediction (with fallback)
            try:
                if detector and not using_fallback_model:
                    prediction = detector.predict(current_readings)
                else:
                    # Use fallback detector
                    prediction = fallback_detector.predict(current_readings)
                
                current_readings.update(prediction)
                
                # Store in database
                db_manager.insert_sensor_reading(current_readings)
                
                # Check for alerts (with rate limiting)
                if prediction['prediction'] == 1 and alert_count < app.config['ALERT_CONFIG']['max_alerts_per_hour']:
                    alert_count += 1
                    detector_type = "Rule-based" if using_fallback_model else "ML"
                    create_alert(
                        'Gas Leak Detected',
                        prediction['risk_level'],
                        f"[{detector_type}] Gas leak detected with {prediction['probability_leak']:.2%} confidence"
                    )
                
                # Emit to connected clients
                socketio.emit('sensor_update', current_readings)
                
            except Exception as e:
                logger.error(f"Error making prediction: {e}")
            
            time.sleep(app.config['SENSOR_UPDATE_INTERVAL'])
            
        except Exception as e:
            logger.error(f"Error in sensor simulation loop: {e}")
            time.sleep(1)
    
    logger.info("Sensor simulation stopped")


def create_alert(alert_type: str, severity: str, message: str) -> bool:
    """
    Create and broadcast an alert.
    
    Args:
        alert_type: Type of alert
        severity: Severity level (LOW, MEDIUM, HIGH)
        message: Alert message
    
    Returns:
        True if alert created successfully
    """
    try:
        if db_manager.insert_alert(alert_type, severity, message):
            alert_data = {
                'type': alert_type,
                'severity': severity,
                'message': message,
                'timestamp': datetime.now().isoformat()
            }
            socketio.emit('alert', alert_data)
            logger.warning(f"Alert created: {alert_type} - {severity}")
            return True
        return False
    except Exception as e:
        logger.error(f"Error creating alert: {e}")
        return False

# Web Routes
@app.route('/')
def index():
    """Redirect to dashboard"""
    return redirect(url_for('dashboard'))


@app.route('/dashboard')
def dashboard():
    """Display main dashboard"""
    try:
        return render_template('dashboard.html')
    except Exception as e:
        logger.error(f"Error loading dashboard: {e}")
        return jsonify({'error': 'Failed to load dashboard'}), 500


@app.route('/devices')
def devices():
    """Display devices management page"""
    try:
        devices_data = db_manager.get_devices()
        return render_template('devices.html', devices=devices_data)
    except Exception as e:
        logger.error(f"Error loading devices page: {e}")
        return jsonify({'error': 'Failed to load devices'}), 500


@app.route('/alerts')
def alerts():
    """Display alerts page"""
    try:
        alerts_data = db_manager.get_alerts(limit=100)
        return render_template('alerts.html', alerts=alerts_data)
    except Exception as e:
        logger.error(f"Error loading alerts page: {e}")
        return jsonify({'error': 'Failed to load alerts'}), 500


@app.route('/analytics')
def analytics():
    """Display analytics page"""
    try:
        return render_template('analytics.html')
    except Exception as e:
        logger.error(f"Error loading analytics page: {e}")
        return jsonify({'error': 'Failed to load analytics'}), 500


@app.route('/settings')
def settings():
    """Display settings page"""
    try:
        return render_template('settings.html')
    except Exception as e:
        logger.error(f"Error loading settings page: {e}")
        return jsonify({'error': 'Failed to load settings'}), 500


# API Endpoints
@app.route('/api/current_readings', methods=['GET'])
def api_current_readings():
    """Get current sensor readings"""
    try:
        return jsonify(current_readings)
    except Exception as e:
        logger.error(f"Error fetching current readings: {e}")
        return jsonify({'error': 'Failed to get readings'}), 500


@app.route('/api/historical_data', methods=['GET'])
def api_historical_data():
    """Get historical sensor data with optional time range"""
    try:
        hours = request.args.get('hours', 24, type=int)
        
        if hours < 1 or hours > 8760:  # Max 1 year
            hours = 24
        
        data = db_manager.get_sensor_readings(hours=hours)
        return jsonify(data)
        
    except Exception as e:
        logger.error(f"Error fetching historical data: {e}")
        return jsonify({'error': 'Failed to get historical data'}), 500


@app.route('/api/alerts', methods=['GET'])
def api_alerts():
    """Get unresolved alerts"""
    try:
        alerts_data = db_manager.get_alerts(unresolved_only=True)
        return jsonify(alerts_data)
    except Exception as e:
        logger.error(f"Error fetching alerts: {e}")
        return jsonify({'error': 'Failed to get alerts'}), 500


@app.route('/api/resolve_alert/<int:alert_id>', methods=['POST'])
def resolve_alert(alert_id):
    """Resolve an alert by ID"""
    try:
        if db_manager.resolve_alert(alert_id):
            logger.info(f"Alert {alert_id} resolved")
            return jsonify({'success': True})
        else:
            return jsonify({'error': 'Failed to resolve alert'}), 500
    except Exception as e:
        logger.error(f"Error resolving alert: {e}")
        return jsonify({'error': 'Failed to resolve alert'}), 500


@app.route('/api/toggle_shutoff', methods=['POST'])
def toggle_shutoff():
    """Toggle gas shutoff valve"""
    try:
        data = request.get_json() or {}
        action = data.get('action', 'unknown')
        
        if action not in ['on', 'off']:
            return jsonify({'error': 'Invalid action'}), 400
        
        create_alert('System Control', 'INFO', f'Gas shutoff valve turned {action}')
        logger.info(f"Gas shutoff valve {action}")
        
        return jsonify({'success': True, 'action': action})
    except Exception as e:
        logger.error(f"Error toggling shutoff: {e}")
        return jsonify({'error': 'Failed to control shutoff'}), 500


@app.route('/api/predict', methods=['POST'])
def api_predict():
    """Make prediction on sensor data"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        if not detector:
            return jsonify({'error': 'Model not loaded'}), 503
        
        prediction = detector.predict(data)
        return jsonify(prediction)
        
    except ValueError as e:
        logger.warning(f"Prediction validation error: {e}")
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Error making prediction: {e}")
        return jsonify({'error': 'Failed to make prediction'}), 500


@app.route('/api/health', methods=['GET'])
def health_check():
    """System health check endpoint"""
    try:
        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'model_loaded': detector is not None,
            'using_fallback': using_fallback_model,
            'simulation_running': simulation_running
        })
    except Exception as e:
        logger.error(f"Health check error: {e}")
        return jsonify({'status': 'unhealthy', 'error': str(e)}), 503


def main():
    """Main application entry point"""
    global simulation_running, using_fallback_model
    try:
        logger.info("=" * 60)
        logger.info("Starting Gas Leak Detection System v2.0")
        logger.info("=" * 60)
        
        # Initialize database
        if not db_manager.init_database():
            logger.error("Failed to init database")
            return
        
        logger.info("✓ Database initialized")
        
        # Load ML model (with fallback)
        if load_ml_model():
            if using_fallback_model:
                logger.info("✓ Using FALLBACK rule-based detector")
            else:
                logger.info("✓ ML model loaded successfully")
        else:
            logger.warning("! System will use fallback detector")
        
        # Start sensor simulation
        sensor_thread = threading.Thread(target=simulate_sensor_data, daemon=True)
        sensor_thread.start()
        logger.info("✓ Sensor simulation started")
        
        logger.info("=" * 60)
        logger.info("Dashboard available at: http://localhost:5001")
        logger.info("API Health Check: http://localhost:5001/api/health")
        logger.info("=" * 60)
        
        socketio.run(app, host='0.0.0.0', port=5001, debug=False)
        
    except KeyboardInterrupt:
        logger.info("Application interrupted by user")
        simulation_running = False
    except Exception as e:
        logger.critical(f"Critical Error: {e}")


# Socket events
@socketio.on('connect')
def handle_connect():
    logger.info(f"Client connected: {request.sid}")
    emit('sensor_update', current_readings)

@socketio.on('disconnect')
def handle_disconnect():
    logger.info(f"Client disconnected: {request.sid}")


if __name__ == '__main__':
    main()