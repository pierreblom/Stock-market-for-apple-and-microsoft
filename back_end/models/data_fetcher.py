"""
Market data fetcher for retrieving stock data from external APIs.
"""

import finnhub
from alpha_vantage.timeseries import TimeSeries
import logging
from datetime import datetime
from typing import Dict, List, Optional, Union, Any, Tuple
from ..config import config
from ..utils.exceptions import ApiKeyNotConfiguredException, DataFetchException

# Type definitions
StockRecord = Dict[str, Union[str, float, int]]
CurrentData = Dict[str, Union[str, float]]
ApiResponse = Dict[str, Union[bool, List[StockRecord], CurrentData, str, None]]

# Ticker mapping to handle differences between APIs
TICKER_MAP: Dict[str, Dict[str, str]] = {
    'ASML.AS': {'alpha_vantage': 'ASML.AMS', 'finnhub': 'ASML.AS'}
}


def get_api_ticker(symbol: str, api_name: str) -> str:
    """
    Gets the correct ticker for the specified API, with a fallback for unknown symbols.
    
    Args:
        symbol: Stock symbol to map
        api_name: Name of the API ('alpha_vantage' or 'finnhub')
        
    Returns:
        Mapped ticker symbol for the specified API
    """
    if symbol in TICKER_MAP:
        return TICKER_MAP[symbol][api_name]
    logging.warning(f"No specific API ticker mapping for {symbol}. Using the symbol as is for {api_name}.")
    return symbol


class MarketDataFetcher:
    """Fetches market data from Finnhub and Alpha Vantage APIs."""
    
    def __init__(self) -> None:
        """Initialize API clients based on configured API keys."""
        if config.api.finnhub_api_key:
            self.finnhub_client: Optional[finnhub.Client] = finnhub.Client(api_key=config.api.finnhub_api_key)
            logging.info("Finnhub client initialized for current data.")
        else:
            self.finnhub_client = None
            logging.warning("Finnhub API key not configured. Will be unable to fetch current data.")

        if config.api.alpha_vantage_api_key:
            self.alpha_vantage_client: Optional[TimeSeries] = TimeSeries(
                key=config.api.alpha_vantage_api_key, 
                output_format='json'
            )
            logging.info("Alpha Vantage client initialized for historical data.")
        else:
            self.alpha_vantage_client = None
            logging.warning("Alpha Vantage API key not configured. Will be unable to fetch historical data.")

    def _parse_alpha_vantage_historical(self, data: Dict[str, Dict[str, str]]) -> List[StockRecord]:
        """
        Converts Alpha Vantage historical data to our standard format.
        
        Args:
            data: Raw Alpha Vantage API response data
            
        Returns:
            List of standardized stock records
        """
        records: List[StockRecord] = []
        for date, daily_data in data.items():
            records.append({
                'date': date,
                'open': float(daily_data['1. open']),
                'high': float(daily_data['2. high']),
                'low': float(daily_data['3. low']),
                'close': float(daily_data['4. close']),
                'volume': int(daily_data['5. volume'])
            })
        return records

    def get_historical_data(self, symbol: str, limit: Optional[int] = None) -> ApiResponse:
        """
        Gets historical stock data from Alpha Vantage.
        
        Args:
            symbol: Stock symbol to fetch data for
            limit: Maximum number of records to return (defaults to config limit)
            
        Returns:
            Dictionary containing success status, data, and message
            
        Raises:
            ApiKeyNotConfiguredException: If Alpha Vantage API key is not configured
            DataFetchException: If data fetching fails
        """
        if not self.alpha_vantage_client:
            raise ApiKeyNotConfiguredException("Alpha Vantage client not configured.")

        if limit is None:
            limit = config.api.historical_data_limit
        
        av_symbol = get_api_ticker(symbol, 'alpha_vantage')

        try:
            logging.info(f"Fetching historical data for {symbol} (using ticker {av_symbol}) from Alpha Vantage...")
            output_size = 'full' if limit > 100 else 'compact'
            data, _ = self.alpha_vantage_client.get_daily(symbol=av_symbol, outputsize=output_size)
            
            if not data:
                 raise DataFetchException(f"No data returned from Alpha Vantage API for {av_symbol}. The symbol may be invalid or not supported.")

            records = self._parse_alpha_vantage_historical(data)
            records = sorted(records, key=lambda x: x['date'], reverse=True)[:limit]
            
            logging.info(f"Successfully fetched {len(records)} records from Alpha Vantage for {symbol}")
            return {
                'success': True, 
                'data': records, 
                'message': f'Successfully fetched {len(records)} records from Alpha Vantage for {symbol}'
            }
        
        except Exception as e:
            message = f"Alpha Vantage historical fetch failed for {symbol}: {str(e)}"
            logging.error(message)
            raise DataFetchException(message)

    def get_current_data(self, symbol: str) -> ApiResponse:
        """
        Gets current stock data from Finnhub.
        
        Args:
            symbol: Stock symbol to fetch current data for
            
        Returns:
            Dictionary containing success status, data, and message
            
        Raises:
            ApiKeyNotConfiguredException: If Finnhub API key is not configured
            DataFetchException: If data fetching fails
        """
        if not self.finnhub_client:
            raise ApiKeyNotConfiguredException("Finnhub client not configured.")
            
        fh_symbol = get_api_ticker(symbol, 'finnhub')

        logging.info(f"Fetching current data for {symbol} (using ticker {fh_symbol}) from Finnhub...")
        try:
            quote = self.finnhub_client.quote(fh_symbol.upper())
            if quote and 'c' in quote and quote['c'] != 0:
                current_data: CurrentData = {
                    'symbol': symbol.upper(), 
                    'price': quote['c'], 
                    'open': quote['o'], 
                    'high': quote['h'],
                    'low': quote['l'], 
                    'previous_close': quote['pc'],
                    'change': quote['c'] - quote['pc'],
                    'change_percent': ((quote['c'] - quote['pc']) / quote['pc']) * 100 if quote['pc'] != 0 else 0,
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
                logging.info(f"Successfully fetched current data from Finnhub for {symbol}")
                return {
                    'success': True, 
                    'data': current_data, 
                    'message': f'Successfully fetched current data from Finnhub for {symbol}'
                }
            else:
                message = f"No current data available from Finnhub for {symbol}. The symbol may be incorrect or not supported."
                logging.warning(message)
                raise DataFetchException(message)
        except Exception as e:
            message = f"Finnhub current data fetch failed for {symbol}: {str(e)}"
            logging.error(message)
            raise DataFetchException(message) 