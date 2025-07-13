"""
Automation service for handling automated download and scheduling operations.
"""

import logging
from typing import Dict

from ..config import AUTO_DOWNLOAD_ENABLED, DAILY_UPDATE_HOUR, DAILY_UPDATE_MINUTE, AUTO_DOWNLOAD_SYMBOLS, FINNHUB_API_KEY
from ..services.scheduler import automated_daily_download


class AutomationService:
    """Service for automation operations."""
    
    def get_automation_status(self) -> Dict:
        """Get status of automatic download configuration."""
        return {
            'success': True,
            'config': {
                'enabled': AUTO_DOWNLOAD_ENABLED,
                'hour': DAILY_UPDATE_HOUR,
                'minute': DAILY_UPDATE_MINUTE,
                'symbols': AUTO_DOWNLOAD_SYMBOLS,
                'api_key_configured': bool(FINNHUB_API_KEY)
            },
            'next_run': f"{DAILY_UPDATE_HOUR:02d}:{DAILY_UPDATE_MINUTE:02d} daily"
        }
    
    def trigger_automated_download(self) -> Dict:
        """Manually trigger the automated download process."""
        results = automated_daily_download()
        
        successful = sum(1 for r in results.values() if r['success'])
        total_symbols = len(results)
        total_records = sum(r['records'] for r in results.values())
        
        return {
            'success': True,
            'message': f'Download triggered successfully: {successful}/{total_symbols} symbols processed',
            'results': results,
            'summary': {
                'successful_symbols': successful,
                'total_symbols': total_symbols,
                'total_records': total_records
            }
        } 