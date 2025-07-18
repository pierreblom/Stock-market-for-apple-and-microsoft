#!/usr/bin/env python3
"""
Test suite for Technical Analysis Service.
"""

import sys
import os
import unittest
import pandas as pd
from datetime import datetime

# Add project root to path for imports
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from back_end.services.technical_analysis_service import TechnicalAnalysisService


class TestTechnicalAnalysisService(unittest.TestCase):
    """Test cases for TechnicalAnalysisService."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.service = TechnicalAnalysisService()
        
        # Sample test data (simplified stock data)
        self.test_data = [
            {'date': '2025-01-01', 'open': 100.0, 'high': 105.0, 'low': 98.0, 'close': 102.0, 'volume': 1000000},
            {'date': '2025-01-02', 'open': 102.0, 'high': 108.0, 'low': 101.0, 'close': 106.0, 'volume': 1200000},
            {'date': '2025-01-03', 'open': 106.0, 'high': 110.0, 'low': 104.0, 'close': 108.0, 'volume': 1100000},
            {'date': '2025-01-04', 'open': 108.0, 'high': 112.0, 'low': 106.0, 'close': 110.0, 'volume': 1300000},
            {'date': '2025-01-05', 'open': 110.0, 'high': 115.0, 'low': 108.0, 'close': 113.0, 'volume': 1400000},
            {'date': '2025-01-06', 'open': 113.0, 'high': 116.0, 'low': 110.0, 'close': 114.0, 'volume': 1250000},
            {'date': '2025-01-07', 'open': 114.0, 'high': 118.0, 'low': 112.0, 'close': 116.0, 'volume': 1350000},
            {'date': '2025-01-08', 'open': 116.0, 'high': 120.0, 'low': 114.0, 'close': 118.0, 'volume': 1450000},
            {'date': '2025-01-09', 'open': 118.0, 'high': 122.0, 'low': 116.0, 'close': 120.0, 'volume': 1500000},
            {'date': '2025-01-10', 'open': 120.0, 'high': 124.0, 'low': 118.0, 'close': 122.0, 'volume': 1600000},
        ]
    
    def test_calculate_sma(self):
        """Test SMA calculation."""
        sma_5 = self.service.calculate_sma(self.test_data, 5)
        
        # Should have NaN values for first 4 entries, then valid SMA
        self.assertEqual(len(sma_5), len(self.test_data))
        self.assertTrue(all(pd.isna(x) for x in sma_5[:4]))  # First 4 should be NaN
        
        # Check that we get valid SMA values
        valid_smas = [x for x in sma_5 if not pd.isna(x)]
        self.assertGreater(len(valid_smas), 0)
        self.assertTrue(all(isinstance(x, (int, float)) for x in valid_smas))
    
    def test_calculate_ema(self):
        """Test EMA calculation."""
        ema_5 = self.service.calculate_ema(self.test_data, 5)
        
        # Should have valid EMA values
        self.assertEqual(len(ema_5), len(self.test_data))
        
        # Check that we get valid EMA values
        valid_emas = [x for x in ema_5 if not pd.isna(x)]
        self.assertGreater(len(valid_emas), 0)
        self.assertTrue(all(isinstance(x, (int, float)) for x in valid_emas))
    
    def test_calculate_rsi(self):
        """Test RSI calculation."""
        # Need more data for RSI calculation (at least 15 points for 14-period RSI)
        extended_data = self.test_data * 2  # 20 data points
        
        rsi_14 = self.service.calculate_rsi(extended_data, 14)
        
        # Should have NaN values for first 14 entries, then valid RSI
        self.assertEqual(len(rsi_14), len(extended_data))
        
        # Check that we get valid RSI values (between 0 and 100)
        valid_rsis = [x for x in rsi_14 if not pd.isna(x)]
        self.assertGreater(len(valid_rsis), 0)
        self.assertTrue(all(0 <= x <= 100 for x in valid_rsis))
    
    def test_calculate_macd(self):
        """Test MACD calculation."""
        macd_data = self.service.calculate_macd(self.test_data)
        
        # Should have MACD line, signal line, and histogram
        self.assertIn('macd_line', macd_data)
        self.assertIn('signal_line', macd_data)
        self.assertIn('histogram', macd_data)
        
        # All should have same length as input data
        self.assertEqual(len(macd_data['macd_line']), len(self.test_data))
        self.assertEqual(len(macd_data['signal_line']), len(self.test_data))
        self.assertEqual(len(macd_data['histogram']), len(self.test_data))
    
    def test_detect_golden_cross(self):
        """Test golden cross detection."""
        # Create data where short SMA crosses above long SMA
        sma_short = [10, 11, 12, 13, 14]  # Rising
        sma_long = [15, 14, 13, 12, 11]   # Falling
        
        cross_index = self.service.detect_golden_cross(sma_short, sma_long)
        self.assertIsNotNone(cross_index)
        self.assertGreaterEqual(cross_index, 0)
        self.assertLess(cross_index, len(sma_short))
    
    def test_detect_death_cross(self):
        """Test death cross detection."""
        # Create data where short SMA crosses below long SMA
        sma_short = [15, 14, 13, 12, 11]  # Falling
        sma_long = [10, 11, 12, 13, 14]   # Rising
        
        cross_index = self.service.detect_death_cross(sma_short, sma_long)
        self.assertIsNotNone(cross_index)
        self.assertGreaterEqual(cross_index, 0)
        self.assertLess(cross_index, len(sma_short))
    
    def test_generate_signals(self):
        """Test signal generation."""
        # Need more data for meaningful signal generation
        extended_data = self.test_data * 3  # 30 data points
        
        result = self.service.generate_signals(extended_data)
        
        # Check structure
        self.assertIn('success', result)
        self.assertIn('indicators', result)
        self.assertIn('signals', result)
        self.assertIn('latest_values', result)
        
        # Check signals structure
        signals = result['signals']
        self.assertIn('overall_signal', signals)
        self.assertIn('confidence', signals)
        self.assertIn('reasons', signals)
        
        # Check that signal is one of the expected values
        self.assertIn(signals['overall_signal'], ['BUY', 'SELL', 'HOLD'])
        
        # Check confidence is between 0 and 100
        self.assertGreaterEqual(signals['confidence'], 0)
        self.assertLessEqual(signals['confidence'], 100)
    
    def test_get_technical_analysis(self):
        """Test complete technical analysis."""
        result = self.service.get_technical_analysis('TEST', self.test_data)
        
        # Check structure
        self.assertIn('success', result)
        self.assertIn('symbol', result)
        self.assertIn('indicators', result)
        self.assertIn('signals', result)
        
        # Check symbol
        self.assertEqual(result['symbol'], 'TEST')
        
        # Check that analysis was successful
        self.assertTrue(result['success'])


if __name__ == '__main__':
    # Import pandas for NaN checks
    # Run tests
    unittest.main(verbosity=2) 