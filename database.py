"""
Database management for the Gas Leak Detection System.
Handles all database operations with connection pooling and error handling.
"""

import sqlite3
from pathlib import Path
from contextlib import contextmanager
from datetime import datetime
from typing import List, Dict, Tuple, Optional
import logging

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Manages SQLite database connections and operations"""
    
    def __init__(self, db_path: str):
        """
        Initialize database manager.
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
    
    @contextmanager
    def get_connection(self):
        """
        Context manager for database connections.
        Ensures proper connection closing and error handling.
        """
        conn = None
        try:
            conn = sqlite3.connect(str(self.db_path))
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA foreign_keys = ON")
            yield conn
            conn.commit()
        except sqlite3.OperationalError as e:
            logger.error(f"Database operational error: {e}")
            if conn:
                conn.rollback()
            raise
        except Exception as e:
            logger.error(f"Unexpected database error: {e}")
            if conn:
                conn.rollback()
            raise
        finally:
            if conn:
                conn.close()
    
    def init_database(self) -> bool:
        """
        Initialize database with required tables.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Create tables
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS sensor_readings (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                        mq4_ppm REAL NOT NULL,
                        mq7_ppm REAL NOT NULL,
                        mq135_ppm REAL NOT NULL,
                        temperature REAL NOT NULL,
                        prediction INTEGER,
                        probability_leak REAL,
                        risk_level TEXT,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS alerts (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                        alert_type TEXT NOT NULL,
                        severity TEXT NOT NULL,
                        message TEXT NOT NULL,
                        resolved BOOLEAN DEFAULT FALSE,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS devices (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        device_name TEXT NOT NULL,
                        location TEXT NOT NULL,
                        status TEXT DEFAULT 'active',
                        last_seen DATETIME,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS users (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        username TEXT UNIQUE NOT NULL,
                        password TEXT NOT NULL,
                        role TEXT DEFAULT 'Operator',
                        email TEXT,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # Insert default data
                self._insert_default_data(cursor)
                
                # Create indices for performance
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_timestamp ON sensor_readings(timestamp)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_alert_timestamp ON alerts(timestamp)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_device_status ON devices(status)')
                
                logger.info("Database initialized successfully")
                return True
                
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            return False
    
    def _insert_default_data(self, cursor) -> None:
        """Insert default data into database"""
        try:
            # Insert default devices
            cursor.execute('''
                INSERT OR IGNORE INTO devices (device_name, location, status, last_seen)
                VALUES 
                (?, ?, ?, ?),
                (?, ?, ?, ?),
                (?, ?, ?, ?)
            ''', (
                'Kitchen Sensor', 'Kitchen', 'active', datetime.now(),
                'Garage Sensor', 'Garage', 'active', datetime.now(),
                'Basement Sensor', 'Basement', 'inactive', datetime.now()
            ))
            
            # Insert default user
            cursor.execute('''
                INSERT OR IGNORE INTO users (username, password, role, email)
                VALUES (?, ?, ?, ?)
            ''', ('admin', 'admin123', 'Admin', 'admin@gasmonitor.com'))
            
            logger.debug("Default data inserted successfully")
        except Exception as e:
            logger.warning(f"Could not insert default data: {e}")
    
    def insert_sensor_reading(self, data: Dict) -> bool:
        """
        Insert sensor reading into database.
        
        Args:
            data: Dictionary with sensor readings
        
        Returns:
            True if successful, False otherwise
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO sensor_readings 
                    (timestamp, mq4_ppm, mq7_ppm, mq135_ppm, temperature, prediction, probability_leak, risk_level)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    datetime.now(),
                    data.get('mq4_ppm', 0),
                    data.get('mq7_ppm', 0),
                    data.get('mq135_ppm', 0),
                    data.get('temperature', 0),
                    data.get('prediction', 0),
                    data.get('probability_leak', 0),
                    data.get('risk_level', 'LOW')
                ))
                return True
        except Exception as e:
            logger.error(f"Failed to insert sensor reading: {e}")
            return False
    
    def insert_alert(self, alert_type: str, severity: str, message: str) -> bool:
        """
        Insert alert into database.
        
        Args:
            alert_type: Type of alert
            severity: Severity level
            message: Alert message
        
        Returns:
            True if successful, False otherwise
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO alerts (timestamp, alert_type, severity, message)
                    VALUES (?, ?, ?, ?)
                ''', (datetime.now(), alert_type, severity, message))
                return True
        except Exception as e:
            logger.error(f"Failed to insert alert: {e}")
            return False
    
    def get_alerts(self, limit: int = 100, unresolved_only: bool = False) -> List[Dict]:
        """Get alerts from database"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                query = 'SELECT * FROM alerts'
                params = []
                
                if unresolved_only:
                    query += ' WHERE resolved = FALSE'
                
                query += ' ORDER BY timestamp DESC LIMIT ?'
                params.append(limit)
                
                cursor.execute(query, params)
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Failed to retrieve alerts: {e}")
            return []
    
    def resolve_alert(self, alert_id: int) -> bool:
        """Resolve an alert"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('UPDATE alerts SET resolved = TRUE WHERE id = ?', (alert_id,))
                return True
        except Exception as e:
            logger.error(f"Failed to resolve alert: {e}")
            return False
    
    def get_sensor_readings(self, hours: int = 24) -> List[Dict]:
        """Get historical sensor readings"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                query = '''
                    SELECT timestamp, mq4_ppm, mq7_ppm, mq135_ppm, temperature, 
                           prediction, probability_leak, risk_level
                    FROM sensor_readings 
                    WHERE timestamp > datetime('now', ? || ' hours')
                    ORDER BY timestamp ASC
                '''
                cursor.execute(query, (f'-{hours}',))
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Failed to retrieve sensor readings: {e}")
            return []
    
    def get_devices(self) -> List[Dict]:
        """Get all registered devices"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM devices')
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Failed to retrieve devices: {e}")
            return []
    
    def update_device_status(self, device_id: int, status: str) -> bool:
        """Update device status"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    'UPDATE devices SET status = ?, last_seen = ? WHERE id = ?',
                    (status, datetime.now(), device_id)
                )
                return True
        except Exception as e:
            logger.error(f"Failed to update device status: {e}")
            return False
