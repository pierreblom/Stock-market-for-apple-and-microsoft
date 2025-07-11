import finnhub
from alpha_vantage.timeseries import TimeSeries
import logging
from datetime import datetime
from ..config import FINNHUB_API_KEY, ALPHA_VANTAGE_API_KEY, HISTORICAL_DATA_LIMIT

# Ticker mapping to handle differences between APIs
TICKER_MAP = {
    'ASML.AS': {'alpha_vantage': 'ASML.AMS', 'finnhub': 'ASML.AS'}

}

def get_api_ticker(symbol, api_name):
    """Gets the correct ticker for the specified API, with a fallback for unknown symbols."""
    if symbol in TICKER_MAP:
        return TICKER_MAP[symbol][api_name]
    logging.warning(f"No specific API ticker mapping for {symbol}. Using the symbol as is for {api_name}.")
    return symbol

class MarketDataFetcher:
    def __init__(self):
        if FINNHUB_API_KEY:
            self.finnhub_client = finnhub.Client(api_key=FINNHUB_API_KEY)
            logging.info("Finnhub client initialized for current data.")
        else:
            logging.warning("Finnhub API key not configured. Will be unable to fetch current data.")

        if ALPHA_VANTAGE_API_KEY:
            self.alpha_vantage_client = TimeSeries(key=ALPHA_VANTAGE_API_KEY, output_format='json')
            logging.info("Alpha Vantage client initialized for historical data.")
        else:
            logging.warning("Alpha Vantage API key not configured. Will be unable to fetch historical data.")

    def _parse_alpha_vantage_historical(self, data):
        """Converts Alpha Vantage historical data to our standard format."""
        records = []
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

    def get_historical_data(self, symbol, limit=None):
        """Gets historical stock data from Alpha Vantage."""
        if not self.alpha_vantage_client:
            return {'success': False, 'data': [], 'message': "Alpha Vantage client not configured."}

        if limit is None:
            limit = HISTORICAL_DATA_LIMIT
        
        av_symbol = get_api_ticker(symbol, 'alpha_vantage')

        try:
            logging.info(f"Fetching historical data for {symbol} (using ticker {av_symbol}) from Alpha Vantage...")
            output_size = 'full' if limit > 100 else 'compact'
            data, _ = self.alpha_vantage_client.get_daily(symbol=av_symbol, outputsize=output_size)
            
            if not data:
                 raise ValueError(f"No data returned from Alpha Vantage API for {av_symbol}. The symbol may be invalid or not supported.")

            records = self._parse_alpha_vantage_historical(data)
            records = sorted(records, key=lambda x: x['date'], reverse=True)[:limit]
            
            logging.info(f"Successfully fetched {len(records)} records from Alpha Vantage for {symbol}")
            return {'success': True, 'data': records, 'message': f'Successfully fetched {len(records)} records from Alpha Vantage for {symbol}'}
        
        except Exception as e:
            message = f"Alpha Vantage historical fetch failed for {symbol}: {str(e)}"
            logging.error(message)
            return {'success': False, 'data': [], 'message': message}

    def get_current_data(self, symbol):
        """Gets current stock data from Finnhub."""
        if not self.finnhub_client:
            return {'success': False, 'data': None, 'message': "Finnhub client not configured."}
            
        fh_symbol = get_api_ticker(symbol, 'finnhub')

        logging.info(f"Fetching current data for {symbol} (using ticker {fh_symbol}) from Finnhub...")
        try:
            quote = self.finnhub_client.quote(fh_symbol.upper())
            if quote and 'c' in quote and quote['c'] != 0:
                current_data = {
                    'symbol': symbol.upper(), 'price': quote['c'], 'open': quote['o'], 'high': quote['h'],
                    'low': quote['l'], 'previous_close': quote['pc'],
                    'change': quote['c'] - quote['pc'],
                    'change_percent': ((quote['c'] - quote['pc']) / quote['pc']) * 100 if quote['pc'] != 0 else 0,
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
                logging.info(f"Successfully fetched current data from Finnhub for {symbol}")
                return {'success': True, 'data': current_data, 'message': f'Successfully fetched current data from Finnhub for {symbol}'}
            else:
                message = f"No current data available from Finnhub for {symbol}. The symbol may be incorrect or not supported."
                logging.warning(message)
                return {'success': False, 'data': None, 'message': message}
        except Exception as e:
            message = f"Finnhub current data fetch failed for {symbol}: {str(e)}"
            logging.error(message)
            return {'success': False, 'data': None, 'message': message} 