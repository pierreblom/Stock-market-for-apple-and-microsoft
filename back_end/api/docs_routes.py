"""
API documentation routes for serving OpenAPI specification and documentation.
"""

from flask import Blueprint, jsonify, render_template_string
from ..utils.api_docs import get_openapi_spec, generate_markdown_docs, get_api_summary
from ..utils.response_wrapper import ApiResponse

# Create blueprint
docs_bp = Blueprint('docs', __name__)


@docs_bp.route('/openapi.json')
def openapi_spec():
    """Serve OpenAPI 3.0 specification."""
    spec = get_openapi_spec()
    return jsonify(spec)


@docs_bp.route('/swagger')
def swagger_ui():
    """Serve Swagger UI for API documentation."""
    html_template = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="utf-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <meta name="description" content="Stock Market Dashboard API Documentation" />
        <title>Stock Market Dashboard API - Swagger UI</title>
        <link rel="stylesheet" type="text/css" href="https://unpkg.com/swagger-ui-dist@5.9.0/swagger-ui.css" />
        <style>
            html { box-sizing: border-box; overflow: -moz-scrollbars-vertical; overflow-y: scroll; }
            *, *:before, *:after { box-sizing: inherit; }
            body { margin:0; background: #fafafa; }
        </style>
    </head>
    <body>
        <div id="swagger-ui"></div>
        <script src="https://unpkg.com/swagger-ui-dist@5.9.0/swagger-ui-bundle.js" crossorigin></script>
        <script src="https://unpkg.com/swagger-ui-dist@5.9.0/swagger-ui-standalone-preset.js" crossorigin></script>
        <script>
            window.onload = () => {
                window.ui = SwaggerUIBundle({
                    url: '/api/docs/openapi.json',
                    dom_id: '#swagger-ui',
                    deepLinking: true,
                    presets: [
                        SwaggerUIBundle.presets.apis,
                        SwaggerUIStandalonePreset
                    ],
                    plugins: [
                        SwaggerUIBundle.plugins.DownloadUrl
                    ],
                    layout: "StandaloneLayout"
                });
            };
        </script>
    </body>
    </html>
    """
    return html_template


@docs_bp.route('/markdown')
def markdown_docs():
    """Serve markdown documentation."""
    markdown = generate_markdown_docs()
    
    html_template = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="utf-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <title>Stock Market Dashboard API Documentation</title>
        <script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
        <style>
            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                line-height: 1.6;
                max-width: 1200px;
                margin: 0 auto;
                padding: 20px;
                background: #f8f9fa;
            }
            .container {
                background: white;
                padding: 40px;
                border-radius: 8px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }
            h1 { color: #2c3e50; border-bottom: 3px solid #3498db; padding-bottom: 10px; }
            h2 { color: #34495e; margin-top: 30px; }
            h3 { color: #7f8c8d; }
            code { background: #f1f2f6; padding: 2px 6px; border-radius: 3px; font-family: 'Monaco', 'Menlo', monospace; }
            pre { background: #2c3e50; color: #ecf0f1; padding: 15px; border-radius: 5px; overflow-x: auto; }
            pre code { background: none; padding: 0; }
            .endpoint { background: #f8f9fa; border-left: 4px solid #3498db; padding: 15px; margin: 15px 0; }
            .method { font-weight: bold; color: #e74c3c; }
            .path { font-family: monospace; color: #2980b9; }
            table { border-collapse: collapse; width: 100%; margin: 15px 0; }
            th, td { border: 1px solid #ddd; padding: 8px 12px; text-align: left; }
            th { background: #f8f9fa; font-weight: bold; }
            .nav { background: #2c3e50; color: white; padding: 15px; border-radius: 5px; margin-bottom: 20px; }
            .nav a { color: #3498db; text-decoration: none; }
            .nav a:hover { text-decoration: underline; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="nav">
                <strong>Stock Market Dashboard API</strong> | 
                <a href="/api/docs/swagger">Swagger UI</a> | 
                <a href="/api/health">Health Check</a> |
                <a href="/">Dashboard</a>
            </div>
            <div id="content"></div>
        </div>
        <script>
            document.getElementById('content').innerHTML = marked.parse(`{{ markdown_content }}`);
            
            // Add syntax highlighting for code blocks
            document.querySelectorAll('pre code').forEach(block => {
                block.style.display = 'block';
                block.style.whiteSpace = 'pre-wrap';
            });
            
            // Style endpoints
            document.querySelectorAll('h3').forEach(h3 => {
                if (h3.textContent.includes('GET') || h3.textContent.includes('POST') || 
                    h3.textContent.includes('PUT') || h3.textContent.includes('DELETE')) {
                    h3.parentElement.classList.add('endpoint');
                }
            });
        </script>
    </body>
    </html>
    """
    
    return render_template_string(html_template, markdown_content=markdown)


@docs_bp.route('/summary')
def api_summary():
    """Get API endpoint summary."""
    summary = get_api_summary()
    return ApiResponse.success(
        data=summary,
        message="API summary retrieved successfully"
    )


@docs_bp.route('/')
def docs_index():
    """API documentation index page."""
    summary = get_api_summary()
    
    html_template = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="utf-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <title>Stock Market Dashboard API Documentation</title>
        <style>
            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                line-height: 1.6;
                max-width: 1200px;
                margin: 0 auto;
                padding: 20px;
                background: #f8f9fa;
            }
            .container {
                background: white;
                padding: 40px;
                border-radius: 8px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }
            h1 { color: #2c3e50; border-bottom: 3px solid #3498db; padding-bottom: 10px; }
            h2 { color: #34495e; margin-top: 30px; }
            .card {
                background: #f8f9fa;
                border: 1px solid #e9ecef;
                border-radius: 8px;
                padding: 20px;
                margin: 15px 0;
                transition: transform 0.2s;
            }
            .card:hover {
                transform: translateY(-2px);
                box-shadow: 0 4px 15px rgba(0,0,0,0.1);
            }
            .card h3 { margin-top: 0; color: #495057; }
            .card p { color: #6c757d; margin-bottom: 15px; }
            .btn {
                display: inline-block;
                padding: 10px 20px;
                background: #3498db;
                color: white;
                text-decoration: none;
                border-radius: 5px;
                margin: 5px;
                transition: background 0.2s;
            }
            .btn:hover {
                background: #2980b9;
            }
            .btn-secondary {
                background: #6c757d;
            }
            .btn-secondary:hover {
                background: #5a6268;
            }
            .stats {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 20px;
                margin: 30px 0;
            }
            .stat-card {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 20px;
                border-radius: 8px;
                text-align: center;
            }
            .stat-number {
                font-size: 2.5em;
                font-weight: bold;
                margin-bottom: 5px;
            }
            .stat-label {
                font-size: 0.9em;
                opacity: 0.9;
            }
            .endpoints {
                margin-top: 30px;
            }
            .endpoint-item {
                background: #f8f9fa;
                border-left: 4px solid #3498db;
                padding: 15px;
                margin: 10px 0;
                border-radius: 0 5px 5px 0;
            }
            .method {
                font-weight: bold;
                color: #e74c3c;
                margin-right: 10px;
            }
            .path {
                font-family: monospace;
                color: #2980b9;
            }
            .summary {
                color: #6c757d;
                font-size: 0.9em;
                margin-top: 5px;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>📊 Stock Market Dashboard API</h1>
            <p>A comprehensive API for stock market data analysis and management.</p>
            
            <div class="stats">
                <div class="stat-card">
                    <div class="stat-number">{{ summary.total_endpoints }}</div>
                    <div class="stat-label">Total Endpoints</div>
                </div>
                {% for tag, count in summary.tags.items() %}
                <div class="stat-card">
                    <div class="stat-number">{{ count }}</div>
                    <div class="stat-label">{{ tag }} Endpoints</div>
                </div>
                {% endfor %}
            </div>
            
            <div style="text-align: center; margin: 30px 0;">
                <a href="/api/docs/swagger" class="btn">🔍 Swagger UI</a>
                <a href="/api/docs/markdown" class="btn">📖 Markdown Docs</a>
                <a href="/api/docs/summary" class="btn btn-secondary">📊 API Summary</a>
                <a href="/api/health" class="btn btn-secondary">❤️ Health Check</a>
                <a href="/" class="btn btn-secondary">🏠 Dashboard</a>
            </div>
            
            <div class="endpoints">
                <h2>Available Endpoints</h2>
                {% for endpoint in summary.endpoints %}
                <div class="endpoint-item">
                    <div>
                        <span class="method">{{ endpoint.method }}</span>
                        <span class="path">{{ endpoint.path }}</span>
                    </div>
                    <div class="summary">{{ endpoint.summary }}</div>
                    {% if endpoint.tags %}
                    <div style="margin-top: 5px;">
                        {% for tag in endpoint.tags %}
                        <span style="background: #e9ecef; padding: 2px 8px; border-radius: 12px; font-size: 0.8em; margin-right: 5px;">{{ tag }}</span>
                        {% endfor %}
                    </div>
                    {% endif %}
                </div>
                {% endfor %}
            </div>
            
            <div style="margin-top: 40px; padding: 20px; background: #e8f4fd; border-radius: 8px;">
                <h3>🚀 Quick Start</h3>
                <p><strong>Base URL:</strong> <code>http://localhost:8001</code></p>
                <p><strong>Health Check:</strong> <code>GET /api/health</code></p>
                <p><strong>Get Stock Data:</strong> <code>GET /api/stock_data/AAPL</code></p>
                <p><strong>Market Analysis:</strong> <code>GET /api/market/correlation?symbols=AAPL,MSFT</code></p>
            </div>
        </div>
    </body>
    </html>
    """
    
    return render_template_string(html_template, summary=summary) 