"""
Configuration management for the Gas Leak Detection System.
Handles all application settings including database, logging, and model parameters.
"""

import os
from datetime import timedelta
from pathlib import Path

# Project root directory
BASE_DIR = Path(__file__).resolve().parent

# Flask Configuration
class Config:
    """Base configuration"""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'gas_leak_detection_secret_key_2024'
    SECRET_KEY_BACKUP = 'backup_secret_key'
    
    # Flask-SocketIO
    SOCKETIO_CORS_ALLOWED_ORIGINS = os.environ.get('SOCKETIO_CORS', "*")
    
    # Database
    DATABASE_PATH = BASE_DIR / 'gas_monitoring.db'
    SQLALCHEMY_DATABASE_URI = f'sqlite:///{DATABASE_PATH}'
    
    # ML Model
    MODEL_PATH = BASE_DIR / 'gas_leak_model.pkl'
    TRAINING_DATA_PATH = BASE_DIR / 'synthetic_gas_leak.csv'
    
    # Logging
    LOG_DIR = BASE_DIR / 'logs'
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    LOG_FILE = LOG_DIR / 'app.log'
    DEBUG = True
    TESTING = False
    HOST = '0.0.0.0'
    PORT = 5001
    
    # Sensor Configuration
    SENSOR_UPDATE_INTERVAL = 2  # seconds
    SENSOR_CONFIG = {
        'mq4_normal_range': (120, 220),      # PPM - Methane
        'mq7_normal_range': (30, 70),        # PPM - Carbon Monoxide
        'mq135_normal_range': (80, 160),     # PPM - Air Quality
        'temperature_range': (25, 30),       # Celsius
        'mq4_alert_threshold': 500,          # High alert threshold
        'mq7_alert_threshold': 150,
        'mq135_alert_threshold': 400,
    }
    
    # Alert Configuration
    ALERT_CONFIG = {
        'low_threshold': 0.3,
        'medium_threshold': 0.7,
        'high_threshold': 0.85,
        'email_alerts_enabled': False,
        'sms_alerts_enabled': False,
        'max_alerts_per_hour': 10,
    }
    
    # ML Model Parameters
    MODEL_CONFIG = {
        'test_size': 0.2,
        'random_state': 42,
        'cv_folds': 5,
        'scoring_metric': 'roc_auc',
        'n_jobs': -1,  # Use all processors
    }
    
    # Feature Names
    FEATURE_NAMES = ["mq4_ppm", "mq7_ppm", "mq135_ppm", "temperature"]
    ENGINEERED_FEATURES = [
        "mq4_ppm", "mq7_ppm", "mq135_ppm", "temperature",
        "gas_ratio_1", "gas_ratio_2", "total_gas", "temp_normalized"
    ]
    
    # Application Settings
    TIME_ZONE = 'UTC'
    JSON_SORT_KEYS = False
    JSONIFY_PRETTYPRINT_REGULAR = True
    
    # Session Configuration
    PERMANENT_SESSION_LIFETIME = timedelta(hours=24)
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    
    # Performance
    JSON_RESPONSE_CACHE_TIMEOUT = 60  # seconds
    MAX_DATABASE_CONNECTIONS = 5


class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    TESTING = False
    SESSION_COOKIE_SECURE = False
    LOG_LEVEL = 'DEBUG'


class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    TESTING = False
    SESSION_COOKIE_SECURE = True
    LOG_LEVEL = 'INFO'


class TestingConfig(Config):
    """Testing configuration"""
    DEBUG = True
    TESTING = True
    DATABASE_PATH = BASE_DIR / 'test_gas_monitoring.db'
    LOG_LEVEL = 'DEBUG'


# Configuration dictionary
config_by_name = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}


def get_config(env: str = None) -> Config:
    """
    Get configuration object based on environment.
    
    Args:
        env: Environment name ('development', 'production', 'testing')
             If None, uses FLASK_ENV environment variable
    
    Returns:
        Configuration object
    """
    if env is None:
        env = os.environ.get('FLASK_ENV', 'development')
    
    return config_by_name.get(env.lower(), DevelopmentConfig)
