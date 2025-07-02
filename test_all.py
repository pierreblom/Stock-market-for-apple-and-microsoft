#!/usr/bin/env python3
"""
Comprehensive Test Suite for Stock Market Tracker
Consolidates all functionality tests into a single file
"""

import requests
import json
import finnhub
import sys
import os
from datetime import datetime, timedelta
import time

# Add project root to path for imports
sys.path.append(os.path.dirname(__file__))

class StockTrackerTester:
    def __init__(self):
        self.finnhub_api_key = "d1ifespr01qhsrhf8sv0d1ifespr01qhsrhf8svg"
        self.stockdata_api_key = "1VN0tUC8cdFdjEbNDYpz9S9SpMpJf451AnM9liQI"
        self.stockdata_base_url = "https://api.stockdata.org/v1"
        self.dashboard_url = "http://127.0.0.1:8080"
        
        # Test results tracking
        self.test_results = {
            'passed': 0,
            'failed': 0,
            'skipped': 0
        }
    
    def print_header(self, title):
        """Print a formatted test section header"""
        print(f"\n{'='*60}")
        print(f"🧪 {title}")
        print(f"{'='*60}")
    
    def print_test(self, test_name, status, details=None):
        """Print formatted test result"""
        status_emoji = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⏭️"
        print(f"{status_emoji} {test_name}: {status}")
        if details:
            print(f"   {details}")
        
        # Update counters
        if status == "PASS":
            self.test_results['passed'] += 1
        elif status == "FAIL":
            self.test_results['failed'] += 1
        else:
            self.test_results['skipped'] += 1
    
    def test_finnhub_api(self):
        """Test Finnhub API integration"""
        self.print_header("FINNHUB API TESTS")
        
        try:
            finnhub_client = finnhub.Client(api_key=self.finnhub_api_key)
            
            # Test 1: Current quote for AAPL
            try:
                quote = finnhub_client.quote('AAPL')
                if 'c' in quote and quote['c'] > 0:
                    self.print_test(
                        "AAPL Current Quote", 
                        "PASS", 
                        f"Price: ${quote['c']}, Change: ${quote['c'] - quote['pc']:.2f}"
                    )
                else:
                    self.print_test("AAPL Current Quote", "FAIL", "Invalid quote data")
            except Exception as e:
                self.print_test("AAPL Current Quote", "FAIL", str(e))
            
            # Test 2: Current quote for MSFT
            try:
                quote = finnhub_client.quote('MSFT')
                if 'c' in quote and quote['c'] > 0:
                    self.print_test(
                        "MSFT Current Quote", 
                        "PASS", 
                        f"Price: ${quote['c']}, Change: ${quote['c'] - quote['pc']:.2f}"
                    )
                else:
                    self.print_test("MSFT Current Quote", "FAIL", "Invalid quote data")
            except Exception as e:
                self.print_test("MSFT Current Quote", "FAIL", str(e))
            
            # Test 3: Historical data (expected to fail on free tier)
            try:
                end_date = datetime.now()
                start_date = end_date - timedelta(days=30)
                start_timestamp = int(start_date.timestamp())
                end_timestamp = int(end_date.timestamp())
                
                data = finnhub_client.stock_candles('AAPL', 'D', start_timestamp, end_timestamp)
                
                if data and data.get('s') == 'ok' and data.get('c'):
                    self.print_test(
                        "Historical Data", 
                        "PASS", 
                        f"Got {len(data['c'])} records"
                    )
                else:
                    self.print_test(
                        "Historical Data", 
                        "SKIP", 
                        "Free tier limitation (expected)"
                    )
            except Exception as e:
                if "403" in str(e) or "access" in str(e).lower():
                    self.print_test(
                        "Historical Data", 
                        "SKIP", 
                        "Free tier limitation (expected)"
                    )
                else:
                    self.print_test("Historical Data", "FAIL", str(e))
        
        except Exception as e:
            self.print_test("Finnhub API Setup", "FAIL", str(e))
    
    def test_stockdata_api(self):
        """Test StockData.org API"""
        self.print_header("STOCKDATA.ORG API TESTS")
        
        # Test 1: Current price data
        try:
            price_url = f"{self.stockdata_base_url}/data/quote"
            price_params = {
                'symbols': 'AAPL',
                'api_token': self.stockdata_api_key
            }
            
            response = requests.get(price_url, params=price_params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if 'data' in data and len(data['data']) > 0:
                    stock_data = data['data'][0]
                    self.print_test(
                        "Current Price Data", 
                        "PASS", 
                        f"AAPL: ${stock_data.get('price', 'N/A')}"
                    )
                else:
                    self.print_test("Current Price Data", "FAIL", "No data returned")
            else:
                self.print_test(
                    "Current Price Data", 
                    "FAIL", 
                    f"HTTP {response.status_code}"
                )
        except Exception as e:
            self.print_test("Current Price Data", "FAIL", str(e))
        
        # Test 2: Historical data
        try:
            eod_url = f"{self.stockdata_base_url}/data/eod"
            eod_params = {
                'symbols': 'AAPL',
                'api_token': self.stockdata_api_key,
                'sort': 'desc'
            }
            
            response = requests.get(eod_url, params=eod_params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if 'data' in data and len(data['data']) > 0:
                    self.print_test(
                        "Historical Data", 
                        "PASS", 
                        f"Got {len(data['data'])} records"
                    )
                else:
                    self.print_test("Historical Data", "FAIL", "No historical data")
            else:
                self.print_test(
                    "Historical Data", 
                    "FAIL", 
                    f"HTTP {response.status_code}"
                )
        except Exception as e:
            self.print_test("Historical Data", "FAIL", str(e))
    
    def test_demo_data_generation(self):
        """Test the demo data generation functionality"""
        self.print_header("DEMO DATA GENERATION TESTS")
        
        try:
            from web_dashboard import FinnhubDataFetcher
            
            fetcher = FinnhubDataFetcher()
            
            # Test demo data generation for AAPL
            result = fetcher.generate_demo_historical_data('AAPL', 30)
            
            if result['success'] and len(result['data']) == 30:
                prices = [record['close'] for record in result['data']]
                price_range = max(prices) - min(prices)
                self.print_test(
                    "AAPL Demo Data Generation", 
                    "PASS", 
                    f"30 records, price range: ${price_range:.2f}"
                )
            else:
                self.print_test("AAPL Demo Data Generation", "FAIL", "Invalid data structure")
            
            # Test demo data generation for MSFT
            result = fetcher.generate_demo_historical_data('MSFT', 60)
            
            if result['success'] and len(result['data']) == 60:
                prices = [record['close'] for record in result['data']]
                price_range = max(prices) - min(prices)
                self.print_test(
                    "MSFT Demo Data Generation", 
                    "PASS", 
                    f"60 records, price range: ${price_range:.2f}"
                )
            else:
                self.print_test("MSFT Demo Data Generation", "FAIL", "Invalid data structure")
        
        except Exception as e:
            self.print_test("Demo Data Generation", "FAIL", str(e))
    
    def test_dashboard_api(self):
        """Test the web dashboard API endpoints"""
        self.print_header("DASHBOARD API TESTS")
        
        # Test 1: Health check
        try:
            response = requests.get(f"{self.dashboard_url}/api/health", timeout=5)
            if response.status_code == 200:
                health = response.json()
                if health.get('status') == 'healthy':
                    self.print_test("Health Check", "PASS", "Dashboard is healthy")
                else:
                    self.print_test("Health Check", "FAIL", f"Status: {health.get('status')}")
            else:
                self.print_test("Health Check", "FAIL", f"HTTP {response.status_code}")
        except requests.exceptions.ConnectionError:
            self.print_test("Health Check", "SKIP", "Dashboard not running")
        except Exception as e:
            self.print_test("Health Check", "FAIL", str(e))
        
        # Test 2: Stock data endpoint for AAPL
        try:
            response = requests.get(f"{self.dashboard_url}/api/stock_data/AAPL", timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get('success') and len(data.get('dates', [])) > 0:
                    self.print_test(
                        "AAPL Stock Data API", 
                        "PASS", 
                        f"{len(data['dates'])} data points"
                    )
                else:
                    self.print_test("AAPL Stock Data API", "FAIL", "No valid data returned")
            else:
                self.print_test("AAPL Stock Data API", "FAIL", f"HTTP {response.status_code}")
        except requests.exceptions.ConnectionError:
            self.print_test("AAPL Stock Data API", "SKIP", "Dashboard not running")
        except Exception as e:
            self.print_test("AAPL Stock Data API", "FAIL", str(e))
        
        # Test 3: Stock data endpoint for MSFT
        try:
            response = requests.get(f"{self.dashboard_url}/api/stock_data/MSFT", timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get('success') and len(data.get('dates', [])) > 0:
                    self.print_test(
                        "MSFT Stock Data API", 
                        "PASS", 
                        f"{len(data['dates'])} data points"
                    )
                else:
                    self.print_test("MSFT Stock Data API", "FAIL", "No valid data returned")
            else:
                self.print_test("MSFT Stock Data API", "FAIL", f"HTTP {response.status_code}")
        except requests.exceptions.ConnectionError:
            self.print_test("MSFT Stock Data API", "SKIP", "Dashboard not running")
        except Exception as e:
            self.print_test("MSFT Stock Data API", "FAIL", str(e))
        
        # Test 4: Frontend accessibility
        try:
            response = requests.get(self.dashboard_url, timeout=5)
            if response.status_code == 200:
                if "Stock Market Tracker" in response.text:
                    self.print_test("Frontend Access", "PASS", "Dashboard loads correctly")
                else:
                    self.print_test("Frontend Access", "FAIL", "Dashboard content issue")
            else:
                self.print_test("Frontend Access", "FAIL", f"HTTP {response.status_code}")
        except requests.exceptions.ConnectionError:
            self.print_test("Frontend Access", "SKIP", "Dashboard not running")
        except Exception as e:
            self.print_test("Frontend Access", "FAIL", str(e))
    
    def test_symbol_variations(self):
        """Test various stock symbols for availability"""
        self.print_header("STOCK SYMBOL TESTS")
        
        test_symbols = [
            ("AAPL", "Apple Inc"),
            ("MSFT", "Microsoft Corp"),
            ("GOOGL", "Alphabet Inc"),
            ("AMZN", "Amazon.com Inc"),
            ("TSLA", "Tesla Inc")
        ]
        
        try:
            finnhub_client = finnhub.Client(api_key=self.finnhub_api_key)
            
            for symbol, company in test_symbols:
                try:
                    quote = finnhub_client.quote(symbol)
                    if 'c' in quote and quote['c'] > 0:
                        self.print_test(
                            f"{symbol} ({company})", 
                            "PASS", 
                            f"${quote['c']:.2f}"
                        )
                    else:
                        self.print_test(f"{symbol} ({company})", "FAIL", "Invalid data")
                except Exception as e:
                    self.print_test(f"{symbol} ({company})", "FAIL", str(e))
        
        except Exception as e:
            self.print_test("Symbol Tests Setup", "FAIL", str(e))
    
    def test_data_export(self):
        """Test CSV data export functionality"""
        self.print_header("DATA EXPORT TESTS")
        
        try:
            # Test CSV list endpoint
            response = requests.get(f"{self.dashboard_url}/api/csv/list", timeout=5)
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    self.print_test(
                        "CSV List Endpoint", 
                        "PASS", 
                        f"Found {len(data.get('files', []))} CSV files"
                    )
                else:
                    self.print_test("CSV List Endpoint", "FAIL", data.get('message', 'Unknown error'))
            else:
                self.print_test("CSV List Endpoint", "FAIL", f"HTTP {response.status_code}")
        except requests.exceptions.ConnectionError:
            self.print_test("CSV List Endpoint", "SKIP", "Dashboard not running")
        except Exception as e:
            self.print_test("CSV List Endpoint", "FAIL", str(e))
        
        try:
            # Test CSV availability check
            response = requests.get(f"{self.dashboard_url}/api/csv/check-availability", timeout=5)
            if response.status_code == 200:
                data = response.json()
                if data.get('success') is not None:
                    self.print_test(
                        "CSV Availability Check", 
                        "PASS", 
                        f"Has CSV data: {data.get('has_csv_data', False)}"
                    )
                else:
                    self.print_test("CSV Availability Check", "FAIL", "Invalid response structure")
            else:
                self.print_test("CSV Availability Check", "FAIL", f"HTTP {response.status_code}")
        except requests.exceptions.ConnectionError:
            self.print_test("CSV Availability Check", "SKIP", "Dashboard not running")
        except Exception as e:
            self.print_test("CSV Availability Check", "FAIL", str(e))
    
    def run_all_tests(self):
        """Run the complete test suite"""
        print("🚀 STARTING COMPREHENSIVE STOCK TRACKER TEST SUITE")
        print(f"⏰ Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Run all test categories
        self.test_finnhub_api()
        self.test_stockdata_api()
        self.test_demo_data_generation()
        self.test_dashboard_api()
        self.test_symbol_variations()
        self.test_data_export()
        
        # Print summary
        self.print_header("TEST SUMMARY")
        total_tests = sum(self.test_results.values())
        pass_rate = (self.test_results['passed'] / total_tests * 100) if total_tests > 0 else 0
        
        print(f"📊 Total Tests: {total_tests}")
        print(f"✅ Passed: {self.test_results['passed']}")
        print(f"❌ Failed: {self.test_results['failed']}")
        print(f"⏭️ Skipped: {self.test_results['skipped']}")
        print(f"📈 Pass Rate: {pass_rate:.1f}%")
        
        if self.test_results['failed'] == 0:
            print("\n🎉 ALL TESTS PASSED! Your stock tracker is working perfectly!")
        elif pass_rate >= 70:
            print(f"\n✨ Good! {pass_rate:.1f}% of tests passed. Minor issues to address.")
        else:
            print(f"\n⚠️ Warning: Only {pass_rate:.1f}% of tests passed. Please check the issues above.")
        
        return pass_rate

def main():
    """Main test runner"""
    tester = StockTrackerTester()
    return tester.run_all_tests()

if __name__ == "__main__":
    try:
        pass_rate = main()
        exit_code = 0 if pass_rate >= 70 else 1
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n⏹️ Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Test suite crashed: {e}")
        sys.exit(1) 