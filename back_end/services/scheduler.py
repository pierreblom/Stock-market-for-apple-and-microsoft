from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
import logging
import atexit
from ..config import (
    AUTO_DOWNLOAD_ENABLED, 
    DAILY_UPDATE_HOUR, 
    DAILY_UPDATE_MINUTE, 
    AUTO_DOWNLOAD_SYMBOLS, 
    FINNHUB_API_KEY
)
from ..models.data_fetcher import MarketDataFetcher
from ..models.database import save_to_database_csv


# Configure logging for scheduler
logging.basicConfig(level=logging.INFO)
scheduler_logger = logging.getLogger('apscheduler')
scheduler_logger.setLevel(logging.INFO)

# Initialize scheduler
scheduler = BackgroundScheduler()
scheduler.start()

# Register shutdown handler
atexit.register(lambda: scheduler.shutdown())


def automated_daily_download():
    """Automated function to download stock data daily"""
    try:
        logging.info("🤖 Starting automated daily download...")
        
        # This function now relies on the MarketDataFetcher, which requires at least Alpha Vantage key.
        # The fetcher itself will handle which API to use.
        
        fetcher = MarketDataFetcher()
        results = {}
        
        for symbol in AUTO_DOWNLOAD_SYMBOLS:
            try:
                logging.info(f"📈 Fetching data for {symbol}...")
                
                # Get historical data (last 30 days to ensure we have recent data)
                historical_result = fetcher.get_historical_data(symbol, 30)
                
                if historical_result['success'] and historical_result['data']:
                    # Save to daily CSV
                    csv_result = save_to_database_csv(historical_result['data'], symbol)
                    
                    if csv_result and csv_result['success']:
                        results[symbol] = {
                            'success': True,
                            'records': csv_result['records'],
                            'message': csv_result['message']
                        }
                        logging.info(f"✅ {symbol}: {csv_result['message']}")
                    else:
                        results[symbol] = {
                            'success': False,
                            'records': 0,
                            'message': f"Failed to save CSV: {csv_result['message'] if csv_result else 'Unknown error'}"
                        }
                        logging.error(f"❌ {symbol}: Failed to save CSV")
                else:
                    results[symbol] = {
                        'success': False,
                        'records': 0,
                        'message': f"Failed to fetch data: {historical_result['message']}"
                    }
                    logging.error(f"❌ {symbol}: {historical_result['message']}")
                    
            except Exception as e:
                results[symbol] = {
                    'success': False,
                    'records': 0,
                    'message': f"Error: {str(e)}"
                }
                logging.error(f"❌ {symbol}: {str(e)}")
        
        # Log summary
        successful = sum(1 for r in results.values() if r['success'])
        total_records = sum(r['records'] for r in results.values())
        
        logging.info(f"🎯 Automated download complete: {successful}/{len(AUTO_DOWNLOAD_SYMBOLS)} symbols successful, {total_records} total records saved")
        
        return results
        
    except Exception as e:
        logging.error(f"❌ Automated download failed: {str(e)}")
        return {}


def setup_scheduler():
    """Setup the automated download scheduler"""
    if AUTO_DOWNLOAD_ENABLED and FINNHUB_API_KEY:
        try:
            # Schedule daily download
            scheduler.add_job(
                func=automated_daily_download,
                trigger=CronTrigger(hour=DAILY_UPDATE_HOUR, minute=DAILY_UPDATE_MINUTE),
                id='daily_stock_download',
                name='Daily Stock Data Download',
                replace_existing=True
            )
            
            logging.info(f"⏰ Scheduled daily download at {DAILY_UPDATE_HOUR:02d}:{DAILY_UPDATE_MINUTE:02d}")
            logging.info(f"📈 Auto-download symbols: {', '.join(AUTO_DOWNLOAD_SYMBOLS)}")
            
        except Exception as e:
            logging.error(f"❌ Failed to setup scheduler: {str(e)}")
    else:
        if not AUTO_DOWNLOAD_ENABLED:
            logging.info("⏸️  Auto-download is disabled")
        if not FINNHUB_API_KEY:
            logging.warning("⚠️  API key not configured - auto-download disabled") 