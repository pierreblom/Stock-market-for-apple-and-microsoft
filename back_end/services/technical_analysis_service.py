"""
Technical analysis service for calculating indicators and generating trading signals.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from datetime import datetime

from ..utils.logger import get_logger
from ..utils.exceptions import DataFetchException


class TechnicalAnalysisService:
    """Service for technical analysis calculations and signal generation."""
    
    def __init__(self):
        self.logger = get_logger(__name__)
    
    def calculate_sma(self, data: List[Dict], period: int = 20) -> List[float]:
        """
        Calculate Simple Moving Average.
        
        Args:
            data: List of stock records with 'close' prices
            period: Period for SMA calculation (default: 20)
            
        Returns:
            List of SMA values (same length as input data, NaN for insufficient data)
        """
        if not data or len(data) < period:
            return [np.nan] * len(data) if data else []
        
        # Extract close prices
        close_prices = [float(record['close']) for record in data]
        
        # Calculate SMA using pandas
        df = pd.DataFrame({'close': close_prices})
        sma = df['close'].rolling(window=period).mean().tolist()
        
        return sma
    
    def calculate_ema(self, data: List[Dict], period: int = 20) -> List[float]:
        """
        Calculate Exponential Moving Average.
        
        Args:
            data: List of stock records with 'close' prices
            period: Period for EMA calculation (default: 20)
            
        Returns:
            List of EMA values (same length as input data, NaN for insufficient data)
        """
        if not data or len(data) < period:
            return [np.nan] * len(data) if data else []
        
        # Extract close prices
        close_prices = [float(record['close']) for record in data]
        
        # Calculate EMA using pandas
        df = pd.DataFrame({'close': close_prices})
        ema = df['close'].ewm(span=period).mean().tolist()
        
        return ema
    
    def calculate_rsi(self, data: List[Dict], period: int = 14) -> List[float]:
        """
        Calculate Relative Strength Index.
        
        Args:
            data: List of stock records with 'close' prices
            period: Period for RSI calculation (default: 14)
            
        Returns:
            List of RSI values (same length as input data, NaN for insufficient data)
        """
        if not data or len(data) < period + 1:
            return [np.nan] * len(data) if data else []
        
        # Extract close prices
        close_prices = [float(record['close']) for record in data]
        
        # Calculate price changes
        price_changes = pd.Series(close_prices).diff()
        
        # Separate gains and losses
        gains = price_changes.where(price_changes > 0, 0)
        losses = -price_changes.where(price_changes < 0, 0)
        
        # Calculate average gains and losses
        avg_gains = gains.rolling(window=period).mean()
        avg_losses = losses.rolling(window=period).mean()
        
        # Calculate RS and RSI
        rs = avg_gains / avg_losses
        rsi = 100 - (100 / (1 + rs))
        
        return rsi.tolist()
    
    def calculate_macd(self, data: List[Dict], fast: int = 12, slow: int = 26, signal: int = 9) -> Dict[str, List[float]]:
        """
        Calculate MACD (Moving Average Convergence Divergence).
        
        Args:
            data: List of stock records with 'close' prices
            fast: Fast EMA period (default: 12)
            slow: Slow EMA period (default: 26)
            signal: Signal line period (default: 9)
            
        Returns:
            Dictionary with 'macd_line', 'signal_line', and 'histogram' lists
        """
        if not data or len(data) < slow:
            empty_list = [np.nan] * len(data) if data else []
            return {
                'macd_line': empty_list,
                'signal_line': empty_list,
                'histogram': empty_list
            }
        
        # Extract close prices
        close_prices = [float(record['close']) for record in data]
        
        # Calculate fast and slow EMAs
        df = pd.DataFrame({'close': close_prices})
        ema_fast = df['close'].ewm(span=fast).mean()
        ema_slow = df['close'].ewm(span=slow).mean()
        
        # Calculate MACD line
        macd_line = ema_fast - ema_slow
        
        # Calculate signal line (EMA of MACD line)
        signal_line = macd_line.ewm(span=signal).mean()
        
        # Calculate histogram
        histogram = macd_line - signal_line
        
        return {
            'macd_line': macd_line.tolist(),
            'signal_line': signal_line.tolist(),
            'histogram': histogram.tolist()
        }
    
    def detect_golden_cross(self, sma_short: List[float], sma_long: List[float]) -> Optional[int]:
        """
        Detect golden cross (short SMA crosses above long SMA).
        
        Args:
            sma_short: List of short-term SMA values
            sma_long: List of long-term SMA values
            
        Returns:
            Index where golden cross occurred, or None if no cross detected
        """
        if len(sma_short) < 2 or len(sma_long) < 2:
            return None
        
        # Check for golden cross (short SMA crosses above long SMA)
        for i in range(1, len(sma_short)):
            if (sma_short[i-1] <= sma_long[i-1] and 
                sma_short[i] > sma_long[i] and 
                not pd.isna(sma_short[i]) and 
                not pd.isna(sma_long[i])):
                return i
        
        return None
    
    def detect_death_cross(self, sma_short: List[float], sma_long: List[float]) -> Optional[int]:
        """
        Detect death cross (short SMA crosses below long SMA).
        
        Args:
            sma_short: List of short-term SMA values
            sma_long: List of long-term SMA values
            
        Returns:
            Index where death cross occurred, or None if no cross detected
        """
        if len(sma_short) < 2 or len(sma_long) < 2:
            return None
        
        # Check for death cross (short SMA crosses below long SMA)
        for i in range(1, len(sma_short)):
            if (sma_short[i-1] >= sma_long[i-1] and 
                sma_short[i] < sma_long[i] and 
                not pd.isna(sma_short[i]) and 
                not pd.isna(sma_long[i])):
                return i
        
        return None
    
    def generate_signals(self, historical_data: List[Dict]) -> Dict:
        """
        Generate comprehensive trading signals based on technical indicators.
        
        Args:
            historical_data: List of stock records with OHLCV data
            
        Returns:
            Dictionary containing all indicators and signals
        """
        if not historical_data:
            raise DataFetchException("No historical data provided for analysis")
        
        self.logger.info(f"Generating technical analysis signals for {len(historical_data)} data points")
        
        try:
            # Calculate all indicators
            sma_20 = self.calculate_sma(historical_data, 20)
            sma_50 = self.calculate_sma(historical_data, 50)
            sma_200 = self.calculate_sma(historical_data, 200)
            ema_12 = self.calculate_ema(historical_data, 12)
            ema_26 = self.calculate_ema(historical_data, 26)
            rsi_14 = self.calculate_rsi(historical_data, 14)
            macd_data = self.calculate_macd(historical_data)
            
            # Get latest values for signal generation
            latest_index = len(historical_data) - 1
            
            # Initialize signals
            signals = {
                'sma_signals': [],
                'rsi_signals': [],
                'macd_signals': [],
                'overall_signal': 'HOLD',
                'confidence': 0,
                'reasons': []
            }
            
            # SMA Cross Signals (Golden/Death Cross)
            golden_cross_20_50 = self.detect_golden_cross(sma_20, sma_50)
            death_cross_20_50 = self.detect_death_cross(sma_20, sma_50)
            golden_cross_50_200 = self.detect_golden_cross(sma_50, sma_200)
            death_cross_50_200 = self.detect_death_cross(sma_50, sma_200)
            
            # Check for recent crosses (last 5 days)
            recent_threshold = max(0, latest_index - 5)
            
            if golden_cross_20_50 and golden_cross_20_50 >= recent_threshold:
                signals['sma_signals'].append('BUY')
                signals['reasons'].append('Golden Cross (20/50 SMA) detected')
            elif death_cross_20_50 and death_cross_20_50 >= recent_threshold:
                signals['sma_signals'].append('SELL')
                signals['reasons'].append('Death Cross (20/50 SMA) detected')
            
            if golden_cross_50_200 and golden_cross_50_200 >= recent_threshold:
                signals['sma_signals'].append('BUY')
                signals['reasons'].append('Golden Cross (50/200 SMA) detected')
            elif death_cross_50_200 and death_cross_50_200 >= recent_threshold:
                signals['sma_signals'].append('SELL')
                signals['reasons'].append('Death Cross (50/200 SMA) detected')
            
            # RSI Signals
            if latest_index >= 0 and not pd.isna(rsi_14[latest_index]):
                current_rsi = rsi_14[latest_index]
                if current_rsi < 30:
                    signals['rsi_signals'].append('BUY')
                    signals['reasons'].append(f'RSI oversold ({current_rsi:.1f})')
                elif current_rsi > 70:
                    signals['rsi_signals'].append('SELL')
                    signals['reasons'].append(f'RSI overbought ({current_rsi:.1f})')
            
            # MACD Signals
            if (latest_index >= 0 and 
                not pd.isna(macd_data['macd_line'][latest_index]) and 
                not pd.isna(macd_data['signal_line'][latest_index])):
                
                current_macd = macd_data['macd_line'][latest_index]
                current_signal = macd_data['signal_line'][latest_index]
                
                # Check for MACD crossover
                if latest_index > 0:
                    prev_macd = macd_data['macd_line'][latest_index - 1]
                    prev_signal = macd_data['signal_line'][latest_index - 1]
                    
                    if prev_macd <= prev_signal and current_macd > current_signal:
                        signals['macd_signals'].append('BUY')
                        signals['reasons'].append('MACD bullish crossover')
                    elif prev_macd >= prev_signal and current_macd < current_signal:
                        signals['macd_signals'].append('SELL')
                        signals['reasons'].append('MACD bearish crossover')
            
            # Determine overall signal
            buy_signals = (signals['sma_signals'].count('BUY') + 
                          signals['rsi_signals'].count('BUY') + 
                          signals['macd_signals'].count('BUY'))
            
            sell_signals = (signals['sma_signals'].count('SELL') + 
                           signals['rsi_signals'].count('SELL') + 
                           signals['macd_signals'].count('SELL'))
            
            total_signals = buy_signals + sell_signals
            
            if total_signals > 0:
                if buy_signals > sell_signals:
                    signals['overall_signal'] = 'BUY'
                    signals['confidence'] = min(100, (buy_signals / total_signals) * 100)
                elif sell_signals > buy_signals:
                    signals['overall_signal'] = 'SELL'
                    signals['confidence'] = min(100, (sell_signals / total_signals) * 100)
                else:
                    signals['overall_signal'] = 'HOLD'
                    signals['confidence'] = 50
            
            # Prepare response
            result = {
                'success': True,
                'indicators': {
                    'sma_20': sma_20,
                    'sma_50': sma_50,
                    'sma_200': sma_200,
                    'ema_12': ema_12,
                    'ema_26': ema_26,
                    'rsi_14': rsi_14,
                    'macd': macd_data
                },
                'signals': signals,
                'latest_values': {
                    'sma_20': sma_20[latest_index] if latest_index >= 0 and not pd.isna(sma_20[latest_index]) else None,
                    'sma_50': sma_50[latest_index] if latest_index >= 0 and not pd.isna(sma_50[latest_index]) else None,
                    'sma_200': sma_200[latest_index] if latest_index >= 0 and not pd.isna(sma_200[latest_index]) else None,
                    'rsi_14': rsi_14[latest_index] if latest_index >= 0 and not pd.isna(rsi_14[latest_index]) else None,
                    'macd_line': macd_data['macd_line'][latest_index] if latest_index >= 0 and not pd.isna(macd_data['macd_line'][latest_index]) else None,
                    'macd_signal': macd_data['signal_line'][latest_index] if latest_index >= 0 and not pd.isna(macd_data['signal_line'][latest_index]) else None
                },
                'analysis_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'data_points': len(historical_data)
            }
            
            self.logger.info(f"Technical analysis complete: {signals['overall_signal']} signal with {signals['confidence']:.1f}% confidence")
            return result
            
        except Exception as e:
            self.logger.error(f"Error generating technical analysis: {str(e)}")
            raise DataFetchException(f"Technical analysis failed: {str(e)}")
    
    def get_technical_analysis(self, symbol: str, historical_data: List[Dict]) -> Dict:
        """
        Get comprehensive technical analysis for a symbol.
        
        Args:
            symbol: Stock symbol
            historical_data: List of stock records
            
        Returns:
            Complete technical analysis with indicators and signals
        """
        self.logger.info(f"Performing technical analysis for {symbol}")
        
        # Generate signals
        analysis = self.generate_signals(historical_data)
        
        # Add symbol information
        analysis['symbol'] = symbol.upper()
        
        return analysis 