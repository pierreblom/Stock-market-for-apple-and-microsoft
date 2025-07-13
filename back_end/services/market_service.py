"""
Market service for handling market analysis business logic.
"""

import logging
import numpy as np
from datetime import datetime
from typing import Dict, List

from ..models.data_fetcher import MarketDataFetcher
from ..utils.exceptions import DataFetchException


class MarketService:
    """Service for market analysis operations."""
    
    def __init__(self):
        self.fetcher = MarketDataFetcher()
    
    def get_market_correlation(self, symbols: List[str], period: str = 'default') -> Dict:
        """Get market correlation analysis for multiple symbols."""
        correlation_data = {}
        stock_returns = {}
        
        # Get data for all symbols (limit to 10 for performance)
        for symbol in symbols[:10]:
            symbol = symbol.strip().upper()
            result = self.fetcher.get_historical_data(symbol, 60)
            
            if result['success'] and result['data']:
                prices = [float(record['close']) for record in result['data']]
                # Calculate daily returns
                returns = [(prices[i] - prices[i+1]) / prices[i+1] for i in range(len(prices)-1)]
                stock_returns[symbol] = returns
        
        # Calculate correlation matrix
        correlation_matrix = {}
        symbols_list = list(stock_returns.keys())
        
        for i, symbol1 in enumerate(symbols_list):
            correlation_matrix[symbol1] = {}
            for j, symbol2 in enumerate(symbols_list):
                if len(stock_returns[symbol1]) > 0 and len(stock_returns[symbol2]) > 0:
                    min_length = min(len(stock_returns[symbol1]), len(stock_returns[symbol2]))
                    returns1 = stock_returns[symbol1][:min_length]
                    returns2 = stock_returns[symbol2][:min_length]
                    
                    if len(returns1) > 1:
                        correlation = np.corrcoef(returns1, returns2)[0, 1]
                        correlation_matrix[symbol1][symbol2] = round(float(correlation), 3)
                    else:
                        correlation_matrix[symbol1][symbol2] = 0.0
                else:
                    correlation_matrix[symbol1][symbol2] = 0.0
        
        # Calculate market metrics
        market_volatility = {}
        for symbol in symbols_list:
            if len(stock_returns[symbol]) > 0:
                volatility = np.std(stock_returns[symbol]) * (252**0.5)  # Annualized
                market_volatility[symbol] = round(float(volatility), 3)
        
        return {
            'success': True,
            'correlation_matrix': correlation_matrix,
            'market_volatility': market_volatility,
            'symbols': symbols_list,
            'analysis_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'message': f'Correlation analysis complete for {len(symbols_list)} symbols'
        }
    
    def get_market_events(self, symbol: str, threshold: float = 0.05) -> Dict:
        """Detect significant market events from price movements."""
        symbol = symbol.upper()
        result = self.fetcher.get_historical_data(symbol, 60)
        
        if not result['success'] or not result['data']:
            raise DataFetchException(f'No data available for {symbol}')
        
        events = []
        data = result['data']
        
        for i in range(1, len(data)):
            prev_close = float(data[i-1]['close'])
            curr_close = float(data[i]['close'])
            daily_return = (curr_close - prev_close) / prev_close
            
            if abs(daily_return) >= threshold:
                event_type = "Large Move Up" if daily_return > 0 else "Large Move Down"
                magnitude = "Extreme" if abs(daily_return) > threshold * 2 else "Significant"
                
                events.append({
                    'date': data[i]['date'],
                    'type': event_type,
                    'magnitude': magnitude,
                    'return': round(daily_return * 100, 2),
                    'price_from': round(prev_close, 2),
                    'price_to': round(curr_close, 2),
                    'volume': data[i]['volume']
                })
        
        # Sort by date (most recent first)
        events.sort(key=lambda x: x['date'], reverse=True)
        
        return {
            'success': True,
            'symbol': symbol,
            'threshold': threshold * 100,
            'events': events[:20],  # Return most recent 20 events
            'total_events': len(events),
            'analysis_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        } 