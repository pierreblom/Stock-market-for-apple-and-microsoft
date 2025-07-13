"""
Response wrapper for consistent API responses.
"""

import time
from typing import Any, Dict, Optional, Union
from flask import jsonify, request
from .exceptions import StockDashboardException
from .logger import get_logger


class ApiResponse:
    """Standardized API response wrapper."""
    
    @staticmethod
    def success(
        data: Any = None, 
        message: str = "", 
        status_code: int = 200, 
        metadata: Optional[Dict] = None,
        **kwargs
    ):
        """Create a successful response."""
        response = {
            'success': True,
            'message': message,
            'timestamp': time.time(),
            'status_code': status_code,
            **kwargs
        }
        
        if data is not None:
            response['data'] = data
        
        if metadata:
            response['metadata'] = metadata
            
        return jsonify(response), status_code
    
    @staticmethod
    def error(
        message: str, 
        status_code: int = 400, 
        error_type: Optional[str] = None,
        error_code: Optional[str] = None,
        details: Optional[Dict] = None,
        **kwargs
    ):
        """Create an error response."""
        response = {
            'success': False,
            'message': message,
            'timestamp': time.time(),
            'status_code': status_code,
            **kwargs
        }
        
        if error_type:
            response['error_type'] = error_type
        
        if error_code:
            response['error_code'] = error_code
            
        if details:
            response['details'] = details
            
        return jsonify(response), status_code
    
    @staticmethod
    def from_exception(exception: Exception, status_code: int = 500):
        """Create an error response from an exception."""
        if isinstance(exception, StockDashboardException):
            return ApiResponse.error(
                message=str(exception),
                status_code=status_code,
                error_type=exception.__class__.__name__,
                error_code=getattr(exception, 'error_code', None)
            )
        else:
            return ApiResponse.error(
                message=f"Internal server error: {str(exception)}",
                status_code=status_code,
                error_type="InternalError",
                error_code="INTERNAL_ERROR"
            )
    
    @staticmethod
    def paginated(
        data: list,
        page: int,
        per_page: int,
        total: int,
        message: str = "",
        **kwargs
    ):
        """Create a paginated response."""
        total_pages = (total + per_page - 1) // per_page
        
        metadata = {
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': total,
                'total_pages': total_pages,
                'has_next': page < total_pages,
                'has_prev': page > 1
            }
        }
        
        return ApiResponse.success(
            data=data,
            message=message,
            metadata=metadata,
            **kwargs
        )
    
    @staticmethod
    def list_response(
        data: list,
        message: str = "",
        count: Optional[int] = None,
        **kwargs
    ):
        """Create a list response with count information."""
        metadata = {
            'count': count if count is not None else len(data)
        }
        
        return ApiResponse.success(
            data=data,
            message=message,
            metadata=metadata,
            **kwargs
        )


def handle_exceptions(func):
    """Decorator to handle exceptions and return consistent responses."""
    def wrapper(*args, **kwargs):
        logger = get_logger(func.__module__)
        start_time = time.time()
        
        try:
            # Log request
            if request:
                logger.info(f"API Request: {request.method} {request.endpoint}", extra={
                    'extra_fields': {
                        'api_request': {
                            'method': request.method,
                            'endpoint': request.endpoint,
                            'args': request.args.to_dict(),
                            'path_params': request.view_args or {}
                        }
                    }
                })
            
            result = func(*args, **kwargs)
            
            # Log successful response
            response_time = time.time() - start_time
            logger.info(f"API Response: 200 {request.endpoint if request else 'unknown'} ({response_time:.3f}s)", extra={
                'extra_fields': {
                    'api_response': {
                        'endpoint': request.endpoint if request else 'unknown',
                        'status_code': 200,
                        'response_time': response_time
                    }
                }
            })
            
            return result
            
        except StockDashboardException as e:
            response_time = time.time() - start_time
            logger.warning(f"API Error: 400 {request.endpoint if request else 'unknown'} ({response_time:.3f}s) - {str(e)}", extra={
                'extra_fields': {
                    'api_response': {
                        'endpoint': request.endpoint if request else 'unknown',
                        'status_code': 400,
                        'response_time': response_time,
                        'error_type': type(e).__name__
                    }
                }
            })
            return ApiResponse.from_exception(e, status_code=400)
            
        except Exception as e:
            response_time = time.time() - start_time
            logger.error(f"API Error: 500 {request.endpoint if request else 'unknown'} ({response_time:.3f}s) - {str(e)}", extra={
                'extra_fields': {
                    'api_response': {
                        'endpoint': request.endpoint if request else 'unknown',
                        'status_code': 500,
                        'response_time': response_time,
                        'error_type': type(e).__name__
                    }
                }
            }, exc_info=True)
            return ApiResponse.from_exception(e, status_code=500)
    
    wrapper.__name__ = func.__name__
    return wrapper 