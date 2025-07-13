"""
API Documentation for Stock Market Dashboard.

This module provides comprehensive API documentation using OpenAPI/Swagger specification.
"""

from typing import Dict, Any, List
from datetime import datetime


def get_openapi_spec() -> Dict[str, Any]:
    """
    Generate OpenAPI 3.0 specification for the Stock Market Dashboard API.
    
    Returns:
        Complete OpenAPI specification dictionary
    """
    return {
        "openapi": "3.0.3",
        "info": {
            "title": "Stock Market Dashboard API",
            "description": """
            Comprehensive API for stock market data analysis and management.
            
            ## Features
            - Real-time and historical stock data retrieval
            - Market correlation and volatility analysis
            - Database management and automation
            - Price tracking and event detection
            
            ## Authentication
            Currently no authentication required. API keys for external services (Finnhub, Alpha Vantage) 
            should be configured via environment variables.
            
            ## Rate Limits
            - Finnhub: 60 calls/minute (free tier)
            - Alpha Vantage: 5 calls/minute, 500 calls/day (free tier)
            
            ## Data Sources
            - **Current Data**: Finnhub API
            - **Historical Data**: Alpha Vantage API
            - **Storage**: Local CSV files
            """,
            "version": "1.0.0",
            "contact": {
                "name": "Stock Market Dashboard",
                "url": "https://github.com/your-repo/stockmarket"
            },
            "license": {
                "name": "MIT",
                "url": "https://opensource.org/licenses/MIT"
            }
        },
        "servers": [
            {
                "url": "http://localhost:8001",
                "description": "Development server"
            }
        ],
        "paths": {
            "/api/health": {
                "get": {
                    "summary": "Health Check",
                    "description": "Check API health and configuration status",
                    "tags": ["System"],
                    "responses": {
                        "200": {
                            "description": "API is healthy",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "$ref": "#/components/schemas/HealthResponse"
                                    },
                                    "example": {
                                        "success": True,
                                        "data": {
                                            "status": "healthy",
                                            "timestamp": "2023-01-01T12:00:00Z",
                                            "config": {
                                                "api_keys_configured": True,
                                                "auto_download_enabled": True,
                                                "server_host": "localhost",
                                                "server_port": 8001
                                            }
                                        },
                                        "message": "API is healthy",
                                        "timestamp": "2023-01-01T12:00:00Z"
                                    }
                                }
                            }
                        }
                    }
                }
            },
            "/api/stock_data/{symbol}": {
                "get": {
                    "summary": "Get Stock Data",
                    "description": "Retrieve current and historical stock data for a symbol",
                    "tags": ["Stock Data"],
                    "parameters": [
                        {
                            "name": "symbol",
                            "in": "path",
                            "required": True,
                            "description": "Stock symbol (e.g., AAPL, MSFT)",
                            "schema": {
                                "type": "string",
                                "example": "AAPL"
                            }
                        },
                        {
                            "name": "period",
                            "in": "query",
                            "required": False,
                            "description": "Time period for historical data",
                            "schema": {
                                "type": "string",
                                "enum": ["1d", "5d", "1mo", "3mo", "6mo", "1y", "2y", "5y", "10y", "ytd", "max", "default"],
                                "default": "default"
                            }
                        }
                    ],
                    "responses": {
                        "200": {
                            "description": "Stock data retrieved successfully",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "$ref": "#/components/schemas/StockDataResponse"
                                    }
                                }
                            }
                        },
                        "400": {
                            "description": "Bad request - invalid symbol or API error",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "$ref": "#/components/schemas/ErrorResponse"
                                    }
                                }
                            }
                        }
                    }
                }
            },
            "/api/comparison_data": {
                "get": {
                    "summary": "Get Comparison Data",
                    "description": "Retrieve data for multiple symbols for comparison",
                    "tags": ["Stock Data"],
                    "parameters": [
                        {
                            "name": "symbols",
                            "in": "query",
                            "required": True,
                            "description": "Comma-separated list of stock symbols",
                            "schema": {
                                "type": "string",
                                "example": "AAPL,MSFT,GOOGL"
                            }
                        },
                        {
                            "name": "period",
                            "in": "query",
                            "required": False,
                            "description": "Time period for historical data",
                            "schema": {
                                "type": "string",
                                "enum": ["1d", "5d", "1mo", "3mo", "6mo", "1y", "2y", "5y", "10y", "ytd", "max", "default"],
                                "default": "default"
                            }
                        }
                    ],
                    "responses": {
                        "200": {
                            "description": "Comparison data retrieved successfully",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "$ref": "#/components/schemas/ComparisonDataResponse"
                                    }
                                }
                            }
                        }
                    }
                }
            },
            "/api/market/correlation": {
                "get": {
                    "summary": "Market Correlation Analysis",
                    "description": "Analyze correlation between multiple stocks",
                    "tags": ["Market Analysis"],
                    "parameters": [
                        {
                            "name": "symbols",
                            "in": "query",
                            "required": True,
                            "description": "Comma-separated list of stock symbols",
                            "schema": {
                                "type": "string",
                                "example": "AAPL,MSFT,GOOGL"
                            }
                        }
                    ],
                    "responses": {
                        "200": {
                            "description": "Correlation analysis completed",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "$ref": "#/components/schemas/CorrelationResponse"
                                    }
                                }
                            }
                        }
                    }
                }
            },
            "/api/market/events": {
                "get": {
                    "summary": "Market Events Detection",
                    "description": "Detect significant market events for a stock",
                    "tags": ["Market Analysis"],
                    "parameters": [
                        {
                            "name": "symbol",
                            "in": "query",
                            "required": True,
                            "description": "Stock symbol to analyze",
                            "schema": {
                                "type": "string",
                                "example": "AAPL"
                            }
                        },
                        {
                            "name": "threshold",
                            "in": "query",
                            "required": False,
                            "description": "Threshold for event detection (percentage)",
                            "schema": {
                                "type": "number",
                                "format": "float",
                                "default": 5.0,
                                "minimum": 0.1,
                                "maximum": 50.0
                            }
                        }
                    ],
                    "responses": {
                        "200": {
                            "description": "Market events detected",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "$ref": "#/components/schemas/MarketEventsResponse"
                                    }
                                }
                            }
                        }
                    }
                }
            },
            "/api/database/save/{symbol}": {
                "get": {
                    "summary": "Save Stock Data to Database",
                    "description": "Download and save historical stock data to local database",
                    "tags": ["Database Management"],
                    "parameters": [
                        {
                            "name": "symbol",
                            "in": "path",
                            "required": True,
                            "description": "Stock symbol to save",
                            "schema": {
                                "type": "string",
                                "example": "AAPL"
                            }
                        }
                    ],
                    "responses": {
                        "200": {
                            "description": "Data saved successfully",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "$ref": "#/components/schemas/DatabaseSaveResponse"
                                    }
                                }
                            }
                        }
                    }
                }
            },
            "/api/database/list": {
                "get": {
                    "summary": "List Database Files",
                    "description": "List all available database files with metadata",
                    "tags": ["Database Management"],
                    "responses": {
                        "200": {
                            "description": "Database files listed",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "$ref": "#/components/schemas/DatabaseListResponse"
                                    }
                                }
                            }
                        }
                    }
                }
            },
            "/api/database/update-all": {
                "get": {
                    "summary": "Update All Databases",
                    "description": "Update all configured stock databases with latest data",
                    "tags": ["Database Management"],
                    "responses": {
                        "200": {
                            "description": "All databases updated",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "$ref": "#/components/schemas/DatabaseUpdateResponse"
                                    }
                                }
                            }
                        }
                    }
                }
            },
            "/api/auto-download/status": {
                "get": {
                    "summary": "Get Automation Status",
                    "description": "Get current automation configuration and status",
                    "tags": ["Automation"],
                    "responses": {
                        "200": {
                            "description": "Automation status retrieved",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "$ref": "#/components/schemas/AutomationStatusResponse"
                                    }
                                }
                            }
                        }
                    }
                }
            },
            "/api/auto-download/trigger": {
                "get": {
                    "summary": "Trigger Automated Download",
                    "description": "Manually trigger the automated download process",
                    "tags": ["Automation"],
                    "responses": {
                        "200": {
                            "description": "Automated download triggered",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "$ref": "#/components/schemas/AutomationTriggerResponse"
                                    }
                                }
                            }
                        }
                    }
                }
            }
        },
        "components": {
            "schemas": {
                "HealthResponse": {
                    "type": "object",
                    "properties": {
                        "success": {"type": "boolean"},
                        "data": {
                            "type": "object",
                            "properties": {
                                "status": {"type": "string", "enum": ["healthy", "unhealthy"]},
                                "timestamp": {"type": "string", "format": "date-time"},
                                "config": {
                                    "type": "object",
                                    "properties": {
                                        "api_keys_configured": {"type": "boolean"},
                                        "auto_download_enabled": {"type": "boolean"},
                                        "server_host": {"type": "string"},
                                        "server_port": {"type": "integer"}
                                    }
                                }
                            }
                        },
                        "message": {"type": "string"},
                        "timestamp": {"type": "string", "format": "date-time"}
                    }
                },
                "StockDataResponse": {
                    "type": "object",
                    "properties": {
                        "success": {"type": "boolean"},
                        "data": {
                            "type": "object",
                            "properties": {
                                "symbol": {"type": "string"},
                                "dates": {"type": "array", "items": {"type": "string"}},
                                "prices": {"type": "array", "items": {"type": "number"}},
                                "volumes": {"type": "array", "items": {"type": "integer"}},
                                "current": {
                                    "type": "object",
                                    "properties": {
                                        "price": {"type": "number"},
                                        "change": {"type": "number"},
                                        "change_percent": {"type": "number"}
                                    }
                                },
                                "errors": {"type": "array", "items": {"type": "string"}},
                                "messages": {"type": "object"},
                                "granularity": {"type": "string"}
                            }
                        },
                        "message": {"type": "string"},
                        "timestamp": {"type": "string", "format": "date-time"}
                    }
                },
                "ComparisonDataResponse": {
                    "type": "object",
                    "properties": {
                        "success": {"type": "boolean"},
                        "data": {
                            "type": "object",
                            "additionalProperties": {
                                "$ref": "#/components/schemas/StockDataResponse"
                            }
                        },
                        "errors": {"type": "array", "items": {"type": "string"}},
                        "message": {"type": "string"},
                        "timestamp": {"type": "string", "format": "date-time"}
                    }
                },
                "CorrelationResponse": {
                    "type": "object",
                    "properties": {
                        "success": {"type": "boolean"},
                        "data": {
                            "type": "object",
                            "properties": {
                                "correlation_matrix": {
                                    "type": "object",
                                    "additionalProperties": {
                                        "type": "object",
                                        "additionalProperties": {"type": "number"}
                                    }
                                },
                                "market_volatility": {
                                    "type": "object",
                                    "additionalProperties": {"type": "number"}
                                },
                                "symbols": {"type": "array", "items": {"type": "string"}},
                                "analysis_date": {"type": "string", "format": "date-time"},
                                "message": {"type": "string"}
                            }
                        },
                        "message": {"type": "string"},
                        "timestamp": {"type": "string", "format": "date-time"}
                    }
                },
                "MarketEventsResponse": {
                    "type": "object",
                    "properties": {
                        "success": {"type": "boolean"},
                        "data": {
                            "type": "object",
                            "properties": {
                                "symbol": {"type": "string"},
                                "threshold": {"type": "number"},
                                "events": {
                                    "type": "array",
                                    "items": {
                                        "type": "object",
                                        "properties": {
                                            "date": {"type": "string"},
                                            "type": {"type": "string"},
                                            "magnitude": {"type": "string"},
                                            "return": {"type": "number"},
                                            "price_from": {"type": "number"},
                                            "price_to": {"type": "number"},
                                            "volume": {"type": "integer"}
                                        }
                                    }
                                },
                                "total_events": {"type": "integer"},
                                "analysis_date": {"type": "string", "format": "date-time"}
                            }
                        },
                        "message": {"type": "string"},
                        "timestamp": {"type": "string", "format": "date-time"}
                    }
                },
                "DatabaseSaveResponse": {
                    "type": "object",
                    "properties": {
                        "success": {"type": "boolean"},
                        "data": {
                            "type": "object",
                            "properties": {
                                "symbol": {"type": "string"},
                                "message": {"type": "string"},
                                "records_added": {"type": "integer"},
                                "total_records": {"type": "integer"},
                                "updated": {"type": "boolean"},
                                "filename": {"type": "string"}
                            }
                        },
                        "message": {"type": "string"},
                        "timestamp": {"type": "string", "format": "date-time"}
                    }
                },
                "DatabaseListResponse": {
                    "type": "object",
                    "properties": {
                        "success": {"type": "boolean"},
                        "data": {
                            "type": "object",
                            "properties": {
                                "databases": {
                                    "type": "array",
                                    "items": {
                                        "type": "object",
                                        "properties": {
                                            "symbol": {"type": "string"},
                                            "filename": {"type": "string"},
                                            "records": {"type": "integer"},
                                            "size_kb": {"type": "number"},
                                            "last_modified": {"type": "integer"},
                                            "date_range": {
                                                "type": "object",
                                                "properties": {
                                                    "earliest": {"type": "string"},
                                                    "latest": {"type": "string"}
                                                }
                                            }
                                        }
                                    }
                                },
                                "total_files": {"type": "integer"},
                                "message": {"type": "string"}
                            }
                        },
                        "message": {"type": "string"},
                        "timestamp": {"type": "string", "format": "date-time"}
                    }
                },
                "DatabaseUpdateResponse": {
                    "type": "object",
                    "properties": {
                        "success": {"type": "boolean"},
                        "data": {
                            "type": "object",
                            "properties": {
                                "results": {
                                    "type": "object",
                                    "additionalProperties": {
                                        "$ref": "#/components/schemas/DatabaseSaveResponse"
                                    }
                                },
                                "summary": {
                                    "type": "object",
                                    "properties": {
                                        "successful_symbols": {"type": "integer"},
                                        "total_symbols": {"type": "integer"},
                                        "total_records": {"type": "integer"}
                                    }
                                },
                                "message": {"type": "string"}
                            }
                        },
                        "message": {"type": "string"},
                        "timestamp": {"type": "string", "format": "date-time"}
                    }
                },
                "AutomationStatusResponse": {
                    "type": "object",
                    "properties": {
                        "success": {"type": "boolean"},
                        "data": {
                            "type": "object",
                            "properties": {
                                "config": {
                                    "type": "object",
                                    "properties": {
                                        "enabled": {"type": "boolean"},
                                        "hour": {"type": "integer"},
                                        "minute": {"type": "integer"},
                                        "symbols": {"type": "array", "items": {"type": "string"}},
                                        "api_key_configured": {"type": "boolean"}
                                    }
                                },
                                "next_run": {"type": "string"}
                            }
                        },
                        "message": {"type": "string"},
                        "timestamp": {"type": "string", "format": "date-time"}
                    }
                },
                "AutomationTriggerResponse": {
                    "type": "object",
                    "properties": {
                        "success": {"type": "boolean"},
                        "data": {
                            "type": "object",
                            "properties": {
                                "message": {"type": "string"},
                                "results": {
                                    "type": "object",
                                    "additionalProperties": {
                                        "type": "object",
                                        "properties": {
                                            "success": {"type": "boolean"},
                                            "records": {"type": "integer"}
                                        }
                                    }
                                },
                                "summary": {
                                    "type": "object",
                                    "properties": {
                                        "successful_symbols": {"type": "integer"},
                                        "total_symbols": {"type": "integer"},
                                        "total_records": {"type": "integer"}
                                    }
                                }
                            }
                        },
                        "message": {"type": "string"},
                        "timestamp": {"type": "string", "format": "date-time"}
                    }
                },
                "ErrorResponse": {
                    "type": "object",
                    "properties": {
                        "success": {"type": "boolean"},
                        "message": {"type": "string"},
                        "error_code": {"type": "string"},
                        "timestamp": {"type": "string", "format": "date-time"}
                    }
                }
            }
        },
        "tags": [
            {
                "name": "System",
                "description": "System health and status endpoints"
            },
            {
                "name": "Stock Data",
                "description": "Stock data retrieval and analysis"
            },
            {
                "name": "Market Analysis",
                "description": "Market correlation and event detection"
            },
            {
                "name": "Database Management",
                "description": "Database operations and file management"
            },
            {
                "name": "Automation",
                "description": "Automated data collection and scheduling"
            }
        ]
    }


def generate_markdown_docs() -> str:
    """
    Generate markdown documentation for the API.
    
    Returns:
        Markdown formatted API documentation
    """
    spec = get_openapi_spec()
    
    markdown = f"""# Stock Market Dashboard API Documentation

## Overview

{spec['info']['description']}

## Base URL

```
{spec['servers'][0]['url']}
```

## Authentication

Currently no authentication is required. API keys for external services should be configured via environment variables.

## Rate Limits

- **Finnhub**: 60 calls/minute (free tier)
- **Alpha Vantage**: 5 calls/minute, 500 calls/day (free tier)

## Endpoints

### System

#### Health Check

`GET /api/health`

Check API health and configuration status.

**Response:**
```json
{{
  "success": true,
  "data": {{
    "status": "healthy",
    "timestamp": "2023-01-01T12:00:00Z",
    "config": {{
      "api_keys_configured": true,
      "auto_download_enabled": true,
      "server_host": "localhost",
      "server_port": 8001
    }}
  }},
  "message": "API is healthy",
  "timestamp": "2023-01-01T12:00:00Z"
}}
```

### Stock Data

#### Get Stock Data

`GET /api/stock_data/{symbol}`

Retrieve current and historical stock data for a symbol.

**Parameters:**
- `symbol` (path, required): Stock symbol (e.g., AAPL, MSFT)
- `period` (query, optional): Time period for historical data
  - Options: `1d`, `5d`, `1mo`, `3mo`, `6mo`, `1y`, `2y`, `5y`, `10y`, `ytd`, `max`, `default`
  - Default: `default`

**Example:**
```
GET /api/stock_data/AAPL?period=1mo
```

#### Get Comparison Data

`GET /api/comparison_data`

Retrieve data for multiple symbols for comparison.

**Parameters:**
- `symbols` (query, required): Comma-separated list of stock symbols
- `period` (query, optional): Time period for historical data

**Example:**
```
GET /api/comparison_data?symbols=AAPL,MSFT,GOOGL&period=6mo
```

### Market Analysis

#### Market Correlation Analysis

`GET /api/market/correlation`

Analyze correlation between multiple stocks.

**Parameters:**
- `symbols` (query, required): Comma-separated list of stock symbols

**Example:**
```
GET /api/market/correlation?symbols=AAPL,MSFT,GOOGL
```

#### Market Events Detection

`GET /api/market/events`

Detect significant market events for a stock.

**Parameters:**
- `symbol` (query, required): Stock symbol to analyze
- `threshold` (query, optional): Threshold for event detection (percentage, default: 5.0)

**Example:**
```
GET /api/market/events?symbol=AAPL&threshold=3.0
```

### Database Management

#### Save Stock Data to Database

`GET /api/database/save/{symbol}`

Download and save historical stock data to local database.

**Parameters:**
- `symbol` (path, required): Stock symbol to save

**Example:**
```
GET /api/database/save/AAPL
```

#### List Database Files

`GET /api/database/list`

List all available database files with metadata.

**Example:**
```
GET /api/database/list
```

#### Update All Databases

`GET /api/database/update-all`

Update all configured stock databases with latest data.

**Example:**
```
GET /api/database/update-all
```

### Automation

#### Get Automation Status

`GET /api/auto-download/status`

Get current automation configuration and status.

**Example:**
```
GET /api/auto-download/status
```

#### Trigger Automated Download

`GET /api/auto-download/trigger`

Manually trigger the automated download process.

**Example:**
```
GET /api/auto-download/trigger
```

## Error Responses

All endpoints return consistent error responses:

```json
{{
  "success": false,
  "message": "Error description",
  "error_code": "ERROR_CODE",
  "timestamp": "2023-01-01T12:00:00Z"
}}
```

## Data Sources

- **Current Data**: Finnhub API
- **Historical Data**: Alpha Vantage API
- **Storage**: Local CSV files

## Configuration

The API can be configured using environment variables:

- `FINNHUB_API_KEY`: API key for Finnhub
- `ALPHA_VANTAGE_API_KEY`: API key for Alpha Vantage
- `FLASK_HOST`: Server host (default: 0.0.0.0)
- `FLASK_PORT`: Server port (default: 8001)
- `FLASK_DEBUG`: Debug mode (default: False)
- `EXPORT_DIR`: Directory for CSV files (default: ./data_exports)
- `LOG_LEVEL`: Logging level (default: INFO)

## Examples

### Python Example

```python
import requests

# Get stock data
response = requests.get('http://localhost:8001/api/stock_data/AAPL')
data = response.json()

# Get market correlation
response = requests.get('http://localhost:8001/api/market/correlation?symbols=AAPL,MSFT')
correlation = response.json()

# Save to database
response = requests.get('http://localhost:8001/api/database/save/AAPL')
result = response.json()
```

### JavaScript Example

```javascript
// Get stock data
fetch('http://localhost:8001/api/stock_data/AAPL')
  .then(response => response.json())
  .then(data => console.log(data));

// Get market correlation
fetch('http://localhost:8001/api/market/correlation?symbols=AAPL,MSFT')
  .then(response => response.json())
  .then(correlation => console.log(correlation));
```

## Support

For issues and questions, please refer to the project repository or create an issue.
"""
    
    return markdown


def get_api_summary() -> Dict[str, Any]:
    """
    Get a summary of all available API endpoints.
    
    Returns:
        Dictionary containing endpoint summary
    """
    spec = get_openapi_spec()
    
    summary = {
        "total_endpoints": len(spec["paths"]),
        "tags": {},
        "endpoints": []
    }
    
    for path, methods in spec["paths"].items():
        for method, details in methods.items():
            if method.upper() in ["GET", "POST", "PUT", "DELETE"]:
                endpoint = {
                    "path": path,
                    "method": method.upper(),
                    "summary": details.get("summary", ""),
                    "tags": details.get("tags", []),
                    "description": details.get("description", "")
                }
                summary["endpoints"].append(endpoint)
                
                # Count by tags
                for tag in endpoint["tags"]:
                    if tag not in summary["tags"]:
                        summary["tags"][tag] = 0
                    summary["tags"][tag] += 1
    
    return summary 