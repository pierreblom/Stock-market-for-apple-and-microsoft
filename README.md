# Stock Market AI Analysis Tool

This project combines StockData.org stock market data with ShuttleAI's artificial intelligence to provide intelligent stock analysis.

## Features

- Fetch real-time and historical stock data from StockData.org
- AI-powered analysis using ShuttleAI
- Multiple analysis types: General, Technical, and Sentiment analysis
- Simple command-line interface
- **100 requests per DAY** (4x more than Alpha Vantage!)

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Get API Keys

#### StockData.org API Key
1. Go to [StockData.org](https://www.stockdata.org/)
2. Click "Sign Up" (no credit card required!)
3. Get instant access to **100 requests per day**
4. Find your API token on your dashboard

#### ShuttleAI API Key
1. Go to [ShuttleAI](https://shuttleai.com/)
2. Sign up for a free account
3. Get your API key from the dashboard

### 3. Configure API Keys

Edit `main.py` and replace the placeholder API keys:

```python
SHUTTLEAI_API_KEY = "your_actual_shuttleai_api_key"
STOCKDATA_API_KEY = "your_actual_stockdata_api_key"
```

## Usage

Run the program:

```bash
python main.py
```

Follow the prompts to:
1. Enter a stock symbol (e.g., AAPL, TSLA, MSFT)
2. Choose an analysis type:
   - **General Analysis**: Overall performance insights and trends
   - **Technical Analysis**: Price movement patterns and trading insights
   - **Sentiment Analysis**: Market sentiment based on recent price movements

## Example

```
=== Stock Market AI Analysis Tool ===
This tool combines StockData.org stock data with ShuttleAI analysis
✅ 100 requests per DAY (4x more than Alpha Vantage!)

Enter a stock symbol (e.g., AAPL, TSLA, MSFT): AAPL

Analysis types available:
1. General Analysis
2. Technical Analysis
3. Sentiment Analysis

Select analysis type (1-3): 1

--- General Analysis for AAPL ---
Fetching current price for AAPL...
Fetching historical data for AAPL...
Analyzing with AI...
[AI analysis results will appear here]
```

## API Rate Limits

- **StockData.org Free Tier**: **100 requests per day** (much better than Alpha Vantage's 25!)
- **ShuttleAI Free Tier**: Check their current free tier limits on their website

## Why StockData.org?

We switched from Alpha Vantage to StockData.org because:
- ✅ **4x more daily requests** (100 vs 25)
- ✅ **No credit card required** for signup
- ✅ **Real-time stock prices** and historical data
- ✅ **Extended hours data** included
- ✅ **6+ years of historical data**
- ✅ **Market news** with sentiment analysis

## Data Sources

- **Current Prices**: Real-time US stock prices from IEX
- **Historical Data**: End-of-day historical data
- **Company Info**: Stock names, exchanges, and metadata
- **AI Analysis**: Powered by ShuttleAI's advanced language models

## Troubleshooting

1. **"Error fetching stock data"**: Check your StockData.org API key and internet connection
2. **"Error with AI analysis"**: Verify your ShuttleAI API key and account status
3. **Rate limit errors**: You may have exceeded the daily limit, wait and try again tomorrow

## Next Steps

You can extend this project by:
- Adding more analysis types
- Implementing data visualization
- Creating a web interface
- Adding portfolio tracking
- Implementing alerts and notifications
- Adding news sentiment analysis using StockData.org's news API 