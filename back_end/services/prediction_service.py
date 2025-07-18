"""
Prediction service for machine learning-based stock price forecasting.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import pickle
import os
from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import mean_squared_error, mean_absolute_error
import warnings
warnings.filterwarnings('ignore')

from sklearn.linear_model import LinearRegression

from ..utils.logger import get_logger
from ..utils.exceptions import DataFetchException


class SimpleModel:
    def __init__(self):
        self.model = LinearRegression()
        self.is_trained = False
    def fit(self, X, y):
        X_reshaped = X.reshape(X.shape[0], -1)
        self.model.fit(X_reshaped, y)
        self.is_trained = True
    def predict(self, X):
        if not self.is_trained:
            raise ValueError("Model not trained")
        X_reshaped = X.reshape(X.shape[0], -1)
        return self.model.predict(X_reshaped)


class PredictionService:
    """Service for machine learning-based price predictions."""
    
    def __init__(self):
        self.logger = get_logger(__name__)
        self.models_dir = "back_end/models/saved_models"
        self.scalers_dir = "back_end/models/scalers"
        
        # Create directories if they don't exist
        os.makedirs(self.models_dir, exist_ok=True)
        os.makedirs(self.scalers_dir, exist_ok=True)
        
        # Initialize scaler
        self.scaler = MinMaxScaler(feature_range=(0, 1))
        
    def preprocess_data(self, historical_data: List[Dict]) -> np.ndarray:
        """
        Preprocess historical data for LSTM model.
        
        Args:
            historical_data: List of stock records with OHLCV data
            
        Returns:
            Scaled data array ready for LSTM input
        """
        if not historical_data:
            raise DataFetchException("No historical data provided for preprocessing")
        
        # Extract close prices
        close_prices = [float(record['close']) for record in historical_data]
        
        # Convert to numpy array and reshape for scaler
        data = np.array(close_prices).reshape(-1, 1)
        
        # Scale the data
        scaled_data = self.scaler.fit_transform(data)
        
        return scaled_data
    
    def create_sequences(self, data: np.ndarray, lookback_days: int = 60) -> Tuple[np.ndarray, np.ndarray]:
        """
        Create sequences for LSTM model training.
        
        Args:
            data: Scaled price data
            lookback_days: Number of days to look back for prediction
            
        Returns:
            Tuple of (X, y) arrays for training
        """
        X, y = [], []
        
        for i in range(lookback_days, len(data)):
            X.append(data[i-lookback_days:i, 0])
            y.append(data[i, 0])
        
        return np.array(X), np.array(y)
    
    def build_lstm_model(self, input_shape: Tuple[int, int]) -> object:
        """
        Build LSTM model architecture.
        
        Args:
            input_shape: Shape of input data (samples, timesteps)
            
        Returns:
            Compiled LSTM model
        """
        try:
            # Try to import TensorFlow/Keras
            from tensorflow.keras.models import Sequential
            from tensorflow.keras.layers import LSTM, Dense, Dropout
            from tensorflow.keras.optimizers import Adam
            
            model = Sequential([
                LSTM(50, return_sequences=True, input_shape=input_shape),
                Dropout(0.2),
                LSTM(50, return_sequences=False),
                Dropout(0.2),
                Dense(25),
                Dense(1)
            ])
            
            model.compile(optimizer=Adam(learning_rate=0.001), loss='mean_squared_error')
            
            return model
            
        except ImportError:
            # Fallback to simple linear model if TensorFlow not available
            self.logger.warning("TensorFlow not available, using simple linear model")
            return self._build_simple_model(input_shape)
    
    def _build_simple_model(self, input_shape: Tuple[int, int]) -> object:
        """
        Build a simple linear model as fallback.
        
        Args:
            input_shape: Shape of input data
            
        Returns:
            Simple linear model
        """
        return SimpleModel()
    
    def train_model(self, X_train: np.ndarray, y_train: np.ndarray, 
                   epochs: int = 100, batch_size: int = 32) -> object:
        """
        Train the LSTM model.
        
        Args:
            X_train: Training features
            y_train: Training targets
            epochs: Number of training epochs
            batch_size: Batch size for training
            
        Returns:
            Trained model
        """
        self.logger.info(f"Training model with {len(X_train)} samples")
        
        # Build model
        model = self.build_lstm_model((X_train.shape[1], 1))
        
        # Train model
        if hasattr(model, 'fit') and hasattr(model, 'compile'):
            # Keras model
            model.fit(X_train, y_train, epochs=epochs, batch_size=batch_size, verbose=0)
        else:
            # Simple model
            model.fit(X_train, y_train)
        
        self.logger.info("Model training completed")
        return model
    
    def predict_future_prices(self, model: object, recent_data: np.ndarray, 
                            days_ahead: int = 30) -> List[float]:
        """
        Predict future prices using trained model.
        
        Args:
            model: Trained model
            recent_data: Recent scaled price data
            days_ahead: Number of days to predict
            
        Returns:
            List of predicted prices
        """
        predictions = []
        current_sequence = recent_data[-60:].flatten()  # Use last 60 days
        
        for _ in range(days_ahead):
            # Reshape for prediction
            X_pred = current_sequence.reshape(1, -1, 1)
            
            # Make prediction
            if hasattr(model, 'predict') and hasattr(model, 'compile'):
                # Keras model
                pred = model.predict(X_pred, verbose=0)[0, 0]
            else:
                # Simple model
                pred = model.predict(X_pred.reshape(1, -1))[0]
            
            predictions.append(pred)
            
            # Update sequence for next prediction
            current_sequence = np.append(current_sequence[1:], pred)
        
        # Inverse transform predictions
        predictions_reshaped = np.array(predictions).reshape(-1, 1)
        predictions_unscaled = self.scaler.inverse_transform(predictions_reshaped)
        
        return predictions_unscaled.flatten().tolist()
    
    def evaluate_model(self, model: object, X_test: np.ndarray, y_test: np.ndarray) -> Dict:
        """
        Evaluate model performance.
        
        Args:
            model: Trained model
            X_test: Test features
            y_test: Test targets
            
        Returns:
            Dictionary with evaluation metrics
        """
        # Make predictions
        if hasattr(model, 'predict') and hasattr(model, 'compile'):
            # Keras model
            y_pred = model.predict(X_test, verbose=0)
        else:
            # Simple model
            y_pred = model.predict(X_test.reshape(X_test.shape[0], -1))
        
        # Calculate metrics
        mse = mean_squared_error(y_test, y_pred)
        mae = mean_absolute_error(y_test, y_pred)
        rmse = np.sqrt(mse)
        
        # Calculate accuracy (percentage of correct direction predictions)
        direction_accuracy = self._calculate_direction_accuracy(y_test, y_pred)
        
        return {
            'mse': mse,
            'mae': mae,
            'rmse': rmse,
            'direction_accuracy': direction_accuracy,
            'predictions_count': len(y_pred)
        }
    
    def _calculate_direction_accuracy(self, y_true: np.ndarray, y_pred: np.ndarray) -> float:
        """
        Calculate accuracy of price direction predictions.
        
        Args:
            y_true: True values
            y_pred: Predicted values
            
        Returns:
            Direction accuracy percentage
        """
        if len(y_true) < 2:
            return 0.0
        
        # Calculate direction changes
        true_directions = np.diff(y_true) > 0
        pred_directions = np.diff(y_pred) > 0
        
        # Calculate accuracy
        correct_directions = np.sum(true_directions == pred_directions)
        total_directions = len(true_directions)
        
        return (correct_directions / total_directions) * 100 if total_directions > 0 else 0.0
    
    def save_model(self, model: object, symbol: str, version: str = "latest") -> str:
        """
        Save trained model to disk.
        
        Args:
            model: Trained model
            symbol: Stock symbol
            version: Model version
            
        Returns:
            Path to saved model
        """
        filename = f"{symbol}_{version}.pkl"
        filepath = os.path.join(self.models_dir, filename)
        
        # Save model
        with open(filepath, 'wb') as f:
            pickle.dump(model, f)
        
        # Save scaler
        scaler_filename = f"{symbol}_{version}_scaler.pkl"
        scaler_filepath = os.path.join(self.scalers_dir, scaler_filename)
        
        with open(scaler_filepath, 'wb') as f:
            pickle.dump(self.scaler, f)
        
        self.logger.info(f"Model saved to {filepath}")
        return filepath
    
    def load_model(self, symbol: str, version: str = "latest") -> Optional[object]:
        """
        Load trained model from disk.
        
        Args:
            symbol: Stock symbol
            version: Model version
            
        Returns:
            Loaded model or None if not found
        """
        filename = f"{symbol}_{version}.pkl"
        filepath = os.path.join(self.models_dir, filename)
        
        if not os.path.exists(filepath):
            return None
        
        # Load model
        with open(filepath, 'rb') as f:
            model = pickle.load(f)
        
        # Load scaler
        scaler_filename = f"{symbol}_{version}_scaler.pkl"
        scaler_filepath = os.path.join(self.scalers_dir, scaler_filename)
        
        if os.path.exists(scaler_filepath):
            with open(scaler_filepath, 'rb') as f:
                self.scaler = pickle.load(f)
        
        self.logger.info(f"Model loaded from {filepath}")
        return model
    
    def generate_predictions(self, symbol: str, historical_data: List[Dict], 
                           days_ahead: int = 30, retrain: bool = False) -> Dict:
        """
        Generate price predictions for a symbol.
        
        Args:
            symbol: Stock symbol
            historical_data: Historical price data
            days_ahead: Number of days to predict
            retrain: Whether to retrain the model
            
        Returns:
            Dictionary with predictions and metrics
        """
        self.logger.info(f"Generating predictions for {symbol} ({days_ahead} days ahead)")
        
        try:
            # Check if we have enough data
            if len(historical_data) < 100:
                return {
                    'success': False,
                    'message': f'Insufficient data for {symbol}. Need at least 100 data points, got {len(historical_data)}',
                    'predictions': [],
                    'metrics': {}
                }
            
            # Load existing model if not retraining
            model = None
            if not retrain:
                model = self.load_model(symbol)
            
            # Train new model if needed
            if model is None or retrain:
                # Preprocess data
                scaled_data = self.preprocess_data(historical_data)
                
                # Create sequences
                lookback_days = 60
                X, y = self.create_sequences(scaled_data, lookback_days)
                
                # Split data (80% train, 20% test)
                split_index = int(len(X) * 0.8)
                X_train, X_test = X[:split_index], X[split_index:]
                y_train, y_test = y[:split_index], y[split_index:]
                
                # Train model
                model = self.train_model(X_train, y_train)
                
                # Evaluate model
                metrics = self.evaluate_model(model, X_test, y_test)
                
                # Save model
                self.save_model(model, symbol)
            else:
                # Use existing model, create minimal metrics
                metrics = {
                    'mse': 0.0,
                    'mae': 0.0,
                    'rmse': 0.0,
                    'direction_accuracy': 0.0,
                    'predictions_count': 0,
                    'note': 'Using pre-trained model'
                }
            
            # Generate predictions
            scaled_data = self.preprocess_data(historical_data)
            predictions = self.predict_future_prices(model, scaled_data, days_ahead)
            
            # Generate prediction dates
            last_date = datetime.strptime(historical_data[-1]['date'].split('T')[0], '%Y-%m-%d')
            prediction_dates = []
            for i in range(1, days_ahead + 1):
                pred_date = last_date + timedelta(days=i)
                prediction_dates.append(pred_date.strftime('%Y-%m-%d'))
            
            # Prepare response
            result = {
                'success': True,
                'symbol': symbol,
                'predictions': [
                    {
                        'date': date,
                        'price': float(price),
                        'confidence': self._calculate_prediction_confidence(i, days_ahead)
                    }
                    for i, (date, price) in enumerate(zip(prediction_dates, predictions))
                ],
                'metrics': metrics,
                'model_info': {
                    'trained_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'data_points_used': len(historical_data),
                    'days_ahead': days_ahead
                }
            }
            
            self.logger.info(f"Predictions generated for {symbol}: {len(predictions)} days ahead")
            return result
            
        except Exception as e:
            self.logger.error(f"Error generating predictions for {symbol}: {str(e)}")
            return {
                'success': False,
                'message': f'Prediction failed: {str(e)}',
                'predictions': [],
                'metrics': {}
            }
    
    def _calculate_prediction_confidence(self, day_index: int, total_days: int) -> float:
        """
        Calculate confidence level for predictions (decreases over time).
        
        Args:
            day_index: Current prediction day index
            total_days: Total number of prediction days
            
        Returns:
            Confidence percentage
        """
        # Confidence decreases linearly from 90% to 50%
        base_confidence = 90.0
        min_confidence = 50.0
        
        if total_days <= 1:
            return base_confidence
        
        confidence_decline = (base_confidence - min_confidence) / (total_days - 1)
        confidence = base_confidence - (day_index * confidence_decline)
        
        return max(min_confidence, confidence) 