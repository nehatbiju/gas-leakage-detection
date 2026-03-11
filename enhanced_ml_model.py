"""
Enhanced Machine Learning Module for Gas Leak Detection.
Implements ensemble learning with multiple algorithms for robust leak detection.
"""

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split, GridSearchCV, cross_val_score
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.svm import SVC
from sklearn.preprocessing import StandardScaler, RobustScaler
from sklearn.metrics import classification_report, confusion_matrix, roc_auc_score, precision_recall_curve
from sklearn.pipeline import Pipeline
from sklearn.feature_selection import SelectKBest, f_classif
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
import seaborn as sns
import joblib
import warnings
from pathlib import Path
from typing import Dict, Tuple, Optional, Any
import logging

warnings.filterwarnings('ignore')

logger = logging.getLogger(__name__)


class EnhancedGasLeakDetector:
    """
    Enhanced Gas Leak Detector using ensemble machine learning.
    
    Attributes:
        models: Dictionary of trained model pipelines
        scalers: Dictionary of scaler objects
        feature_selector: SelectKBest feature selector
        best_model: Best performing model
        feature_names: List of original feature names
    """
    
    def __init__(self):
        """Initialize the detector with empty models"""
        self.models = {}
        self.scalers = {}
        self.feature_selector = None
        self.best_model = None
        self.best_model_name = None
        self.feature_names = ["mq4_ppm", "mq7_ppm", "mq135_ppm", "temperature"]
        logger.info("EnhancedGasLeakDetector initialized")
        
    def load_and_preprocess_data(self, filepath: str) -> Tuple[pd.DataFrame, pd.Series, pd.DataFrame]:
        """
        Load and preprocess the dataset with feature engineering.
        
        Args:
            filepath: Path to CSV file with sensor data
        
        Returns:
            Tuple of (features DataFrame, target Series, original DataFrame)
        
        Raises:
            FileNotFoundError: If data file not found
            ValueError: If required columns missing
        """
        try:
            if not Path(filepath).exists():
                raise FileNotFoundError(f"Data file not found: {filepath}")
            
            logger.info(f"Loading data from {filepath}")
            df = pd.read_csv(filepath)
            
            # Validate required columns
            required_cols = ["mq4_ppm", "mq7_ppm", "mq135_ppm", "temperature", "leak_status"]
            missing_cols = set(required_cols) - set(df.columns)
            if missing_cols:
                raise ValueError(f"Missing required columns: {missing_cols}")
            
            logger.info(f"Data loaded successfully. Shape: {df.shape}")
            
            # Feature engineering
            df['gas_ratio_1'] = df['mq4_ppm'] / (df['mq7_ppm'] + 1e-6)
            df['gas_ratio_2'] = df['mq135_ppm'] / (df['mq4_ppm'] + 1e-6)
            df['total_gas'] = df['mq4_ppm'] + df['mq7_ppm'] + df['mq135_ppm']
            df['temp_normalized'] = (df['temperature'] - df['temperature'].mean()) / df['temperature'].std()
            
            logger.debug("Feature engineering completed")
            
            # Define features and target
            feature_cols = ["mq4_ppm", "mq7_ppm", "mq135_ppm", "temperature", 
                           "gas_ratio_1", "gas_ratio_2", "total_gas", "temp_normalized"]
            X = df[feature_cols]
            y = df["leak_status"]
            
            logger.info(f"Preprocessing complete. Feature space: {len(feature_cols)} features")
            
            return X, y, df
            
        except FileNotFoundError as e:
            logger.error(f"File error: {e}")
            raise
        except ValueError as e:
            logger.error(f"Validation error: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error during preprocessing: {e}")
            raise
    
    def train_models(self, X: pd.DataFrame, y: pd.Series) -> Dict[str, Dict]:
        """
        Train multiple models with hyperparameter tuning using GridSearchCV.
        
        Args:
            X: Feature matrix
            y: Target vector
        
        Returns:
            Dictionary containing trained models and performance metrics
        
        Raises:
            ValueError: If training data is invalid
        """
        try:
            logger.info("Starting model training process")
            
            # Validate input data
            if X.empty or len(y) == 0:
                raise ValueError("Training data cannot be empty")
            
            if len(X) != len(y):
                raise ValueError("X and y must have same number of samples")
            
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, stratify=y, random_state=42
            )
            
            logger.info(f"Training set: {X_train.shape}, Test set: {X_test.shape}")
            
            # Feature selection
            self.feature_selector = SelectKBest(f_classif, k=6)
            X_train_selected = self.feature_selector.fit_transform(X_train, y_train)
            X_test_selected = self.feature_selector.transform(X_test)
            
            logger.debug(f"Selected {self.feature_selector.k} best features")
            
            # Model configurations
            models_config = {
                'RandomForest': {
                    'model': RandomForestClassifier(random_state=42, n_jobs=-1),
                    'params': {
                        'n_estimators': [100, 200],
                        'max_depth': [10, 20],
                        'min_samples_split': [2, 5],
                        'min_samples_leaf': [1, 2]
                    }
                },
                'GradientBoosting': {
                    'model': GradientBoostingClassifier(random_state=42),
                    'params': {
                        'n_estimators': [100, 200],
                        'learning_rate': [0.05, 0.1],
                        'max_depth': [3, 5]
                    }
                },
                'SVM': {
                    'model': SVC(probability=True, random_state=42),
                    'params': {
                        'C': [0.1, 1, 10],
                        'gamma': ['scale', 'auto'],
                        'kernel': ['rbf']
                    }
                }
            }
            
            best_score = 0
            results = {}
            
            for name, config in models_config.items():
                logger.info(f"Training {name}...")
                
                # Create pipeline with scaling
                scaler = StandardScaler() if name == 'SVM' else RobustScaler()
                
                pipeline = Pipeline([
                    ('scaler', scaler),
                    ('model', config['model'])
                ])
                
                # Grid search
                grid_search = GridSearchCV(
                    pipeline, 
                    {f'model__{k}': v for k, v in config['params'].items()},
                    cv=5, 
                    scoring='roc_auc',
                    n_jobs=-1,
                    verbose=0
                )
                
                grid_search.fit(X_train_selected, y_train)
                
                # Store results
                y_pred = grid_search.predict(X_test_selected)
                y_pred_proba = grid_search.predict_proba(X_test_selected)[:, 1]
                
                auc_score = roc_auc_score(y_test, y_pred_proba)
                results[name] = {
                    'model': grid_search.best_estimator_,
                    'score': auc_score,
                    'predictions': y_pred,
                    'probabilities': y_pred_proba,
                    'best_params': grid_search.best_params_
                }
                
                logger.info(f"{name} - ROC-AUC: {auc_score:.4f}")
                
                if auc_score > best_score:
                    best_score = auc_score
                    self.best_model = results[name]['model']
                    self.best_model_name = name
            
            self.models = results
            self.X_test = X_test_selected
            self.y_test = y_test
            
            logger.info(f"Best model: {self.best_model_name} (ROC-AUC: {best_score:.4f})")
            
            return results
            
        except ValueError as e:
            logger.error(f"Validation error during training: {e}")
            raise
        except Exception as e:
            logger.error(f"Error during model training: {e}")
            raise
    
    def evaluate_models(self) -> None:
        """
        Evaluate and print all trained models' performance metrics.
        
        Raises:
            ValueError: If no models have been trained
        """
        try:
            if not self.models:
                raise ValueError("No models trained yet!")
            
            logger.info("=" * 50)
            logger.info("Model Evaluation Results")
            logger.info("=" * 50)
            
            for name, result in self.models.items():
                logger.info(f"\n{name}:")
                logger.info(f"  ROC-AUC Score: {result['score']:.4f}")
                logger.info(f"  Best Parameters: {result['best_params']}")
                logger.debug(f"\nClassification Report:\n{classification_report(self.y_test, result['predictions'])}")
            
            logger.info(f"\n✓ Best Model: {self.best_model_name} (ROC-AUC: {self.models[self.best_model_name]['score']:.4f})")
            
        except ValueError as e:
            logger.error(f"Evaluation error: {e}")
            raise
        except Exception as e:
            logger.error(f"Error during model evaluation: {e}")
            raise
    
    def plot_results(self) -> None:
        """
        Generate and save visualization of model performance.
        
        Raises:
            ValueError: If models haven't been trained
        """
        try:
            if not self.models:
                raise ValueError("No models trained yet!")
            
            logger.info("Generating model evaluation plots")
            
            fig, axes = plt.subplots(2, 2, figsize=(15, 12))
            
            # Model comparison
            model_names = list(self.models.keys())
            scores = [self.models[name]['score'] for name in model_names]
            
            axes[0, 0].bar(model_names, scores, color=['skyblue', 'lightgreen', 'salmon'])
            axes[0, 0].set_title('Model Performance Comparison (ROC-AUC)', fontsize=12, fontweight='bold')
            axes[0, 0].set_ylabel('ROC-AUC Score')
            axes[0, 0].set_ylim(0.8, 1.0)
            
            # Feature importance
            if hasattr(self.best_model.named_steps['model'], 'feature_importances_'):
                selected_features = self.feature_selector.get_support()
                feature_names = np.array(["mq4_ppm", "mq7_ppm", "mq135_ppm", "temperature", 
                                        "gas_ratio_1", "gas_ratio_2", "total_gas", "temp_normalized"])
                selected_feature_names = feature_names[selected_features]
                
                importances = self.best_model.named_steps['model'].feature_importances_
                axes[0, 1].barh(selected_feature_names, importances, color='steelblue')
                axes[0, 1].set_title(f'Feature Importance ({self.best_model_name})', fontsize=12, fontweight='bold')
                axes[0, 1].set_xlabel('Importance')
            
            # Confusion matrix
            cm = confusion_matrix(self.y_test, self.models[self.best_model_name]['predictions'])
            sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', 
                       xticklabels=['Safe', 'Leak'], yticklabels=['Safe', 'Leak'], ax=axes[1, 0])
            axes[1, 0].set_title(f'Confusion Matrix ({self.best_model_name})', fontsize=12, fontweight='bold')
            
            # ROC Curves
            from sklearn.metrics import roc_curve
            for name, result in self.models.items():
                fpr, tpr, _ = roc_curve(self.y_test, result['probabilities'])
                axes[1, 1].plot(fpr, tpr, label=f'{name} (AUC = {result["score"]:.3f})', linewidth=2)
            
            axes[1, 1].plot([0, 1], [0, 1], 'k--', label='Random', linewidth=1)
            axes[1, 1].set_xlabel('False Positive Rate')
            axes[1, 1].set_ylabel('True Positive Rate')
            axes[1, 1].set_title('ROC Curves', fontsize=12, fontweight='bold')
            axes[1, 1].legend()
            axes[1, 1].grid(True, alpha=0.3)
            
            plt.tight_layout()
            plot_file = 'model_evaluation.png'
            plt.savefig(plot_file, dpi=300, bbox_inches='tight')
            logger.info(f"Plot saved to {plot_file}")
            plt.close()
            
        except ValueError as e:
            logger.error(f"Plot generation error: {e}")
            raise
        except Exception as e:
            logger.error(f"Error generating plots: {e}")
            raise
    
    def predict(self, sensor_data: Dict[str, float]) -> Dict[str, Any]:
        """
        Make prediction on new sensor data.
        
        Args:
            sensor_data: Dictionary with sensor readings (mq4_ppm, mq7_ppm, mq135_ppm, temperature)
        
        Returns:
            Dictionary with prediction, probability, and risk level
        
        Raises:
            ValueError: If model not trained or invalid sensor data
        """
        try:
            if self.best_model is None:
                logger.warning("Attempting to predict without trained model")
                raise ValueError("No model trained yet!")
            
            # Validate sensor data
            required_keys = {'mq4_ppm', 'mq7_ppm', 'mq135_ppm', 'temperature'}
            if not isinstance(sensor_data, dict):
                raise ValueError(f"sensor_data must be a dictionary, got {type(sensor_data)}")
            
            missing_keys = required_keys - set(sensor_data.keys())
            if missing_keys:
                raise ValueError(f"Missing required sensor data: {missing_keys}")
            
            # Convert dict to DataFrame
            df = pd.DataFrame([sensor_data])
            
            # Feature engineering (same as training)
            df['gas_ratio_1'] = df['mq4_ppm'] / (df['mq7_ppm'] + 1e-6)
            df['gas_ratio_2'] = df['mq135_ppm'] / (df['mq4_ppm'] + 1e-6)
            df['total_gas'] = df['mq4_ppm'] + df['mq7_ppm'] + df['mq135_ppm']
            df['temp_normalized'] = (df['temperature'] - 27.5) / 1.2
            
            feature_cols = ["mq4_ppm", "mq7_ppm", "mq135_ppm", "temperature", 
                           "gas_ratio_1", "gas_ratio_2", "total_gas", "temp_normalized"]
            X = df[feature_cols]
            
            # Apply feature selection
            X_selected = self.feature_selector.transform(X)
            
            # Make prediction
            prediction = self.best_model.predict(X_selected)[0]
            probability = self.best_model.predict_proba(X_selected)[0]
            
            result = {
                'prediction': int(prediction),
                'probability_safe': float(probability[0]),
                'probability_leak': float(probability[1]),
                'risk_level': self._get_risk_level(probability[1])
            }
            
            logger.debug(f"Prediction made: {result}")
            
            return result
            
        except ValueError as e:
            logger.error(f"Validation error during prediction: {e}")
            raise
        except Exception as e:
            logger.error(f"Error during prediction: {e}")
            raise
    
    def _get_risk_level(self, leak_prob: float) -> str:
        """
        Determine risk level based on leak probability.
        
        Args:
            leak_prob: Probability of gas leak (0-1)
        
        Returns:
            Risk level: 'LOW', 'MEDIUM', or 'HIGH'
        """
        if leak_prob < 0.3:
            return "LOW"
        elif leak_prob < 0.7:
            return "MEDIUM"
        else:
            return "HIGH"
    
    def save_model(self, filepath: str) -> bool:
        """
        Save the trained model to disk.
        
        Args:
            filepath: Path to save the model
        
        Returns:
            True if successful
        
        Raises:
            ValueError: If no model trained
        """
        try:
            if self.best_model is None:
                raise ValueError("No model trained yet!")
            
            model_data = {
                'best_model': self.best_model,
                'feature_selector': self.feature_selector,
                'best_model_name': self.best_model_name,
                'models': self.models
            }
            joblib.dump(model_data, filepath)
            logger.info(f"Model saved successfully to {filepath}")
            return True
            
        except ValueError as e:
            logger.error(f"Model save error: {e}")
            raise
        except Exception as e:
            logger.error(f"Error saving model: {e}")
            raise
    
    def load_model(self, filepath: str) -> bool:
        """
        Load a trained model from disk.
        
        Args:
            filepath: Path to saved model
        
        Returns:
            True if successful
        
        Raises:
            FileNotFoundError: If model file not found
        """
        try:
            if not Path(filepath).exists():
                raise FileNotFoundError(f"Model file not found: {filepath}")
            
            model_data = joblib.load(filepath)
            self.best_model = model_data['best_model']
            self.feature_selector = model_data['feature_selector']
            self.best_model_name = model_data['best_model_name']
            self.models = model_data['models']
            
            logger.info(f"Model loaded successfully from {filepath}")
            logger.info(f"Best model: {self.best_model_name}")
            
            return True
            
        except FileNotFoundError as e:
            logger.error(f"File not found: {e}")
            raise
        except Exception as e:
            logger.error(f"Error loading model: {e}")
            raise
    
    def load_model(self, filepath):
        """Load a trained model"""
        model_data = joblib.load(filepath)
        self.best_model = model_data['best_model']
        self.feature_selector = model_data['feature_selector']
        self.best_model_name = model_data['best_model_name']
        self.models = model_data['models']
        print(f"Model loaded from {filepath}")

def main():
    # Initialize detector
    detector = EnhancedGasLeakDetector()
    
    # Load and preprocess data
    print("Loading and preprocessing data...")
    X, y, df = detector.load_and_preprocess_data("synthetic_gas_leak.csv")
    
    # Train models
    print("Training models...")
    results = detector.train_models(X, y)
    
    # Evaluate models
    detector.evaluate_models()
    
    # Plot results
    detector.plot_results()
    
    # Save the best model
    detector.save_model("gas_leak_model.pkl")
    
    # Test prediction
    test_data = {
        'mq4_ppm': 850.0,
        'mq7_ppm': 280.0,
        'mq135_ppm': 750.0,
        'temperature': 27.5
    }
    
    prediction = detector.predict(test_data)
    print(f"\nTest Prediction: {prediction}")
    
    return detector

if __name__ == "__main__":
    detector = main()